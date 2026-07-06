#!/usr/bin/env python3
"""Language drill ledger tool — deterministic parse / select / record / seed.

Subcommands:
  sync    Parse the vocab log into the canonical drill ledger (merge-safe).
  select  Leitner-style pick of due drill items (JSON to stdout).
  record  Apply drill results (JSON file of grades) to the ledger.
  seed    Create ledger items from a JSON file when no log exists yet.

Paths (no assumptions about any particular notes app):
  --log / LANGUAGE_LOG_PATH    Source vocab log markdown file (READ-ONLY).
                               Default: ./language-log.md
  --ledger / LANGUAGE_LEDGER_PATH  Drill ledger file this tool writes.
                               Default: drill-ledger.md beside the log.

Design rules:
  - The source vocab log is NEVER written, only read.
  - Only the drill ledger is written, and only with --write.
    Without --write, proposed content goes to stdout (propose->confirm flow).
  - Missing/empty inputs are reported via STATUS lines, never a stack trace.
  - Small sample sizes are reported honestly (SMALL_SAMPLE flag / NOTE lines).

Stdlib only (argparse/re/json/datetime). No network. Python 3.9+.
"""

import argparse
import datetime
import json
import os
import re
import sys

DEFAULT_LOG = "language-log.md"
DEFAULT_LEDGER_NAME = "drill-ledger.md"

# --- Leitner constants (documented, do not tweak casually) -------------------
# Days between drills per box. Box 1 = new or recently missed (drill daily);
# roughly doubling ladder so mastered items settle into monthly maintenance.
INTERVALS = {1: 1, 2: 3, 3: 7, 4: 14, 5: 30}
MAX_BOX = 5
MIN_ITEMS = 10  # target session floor: fewer than this makes for too thin a drill
MAX_ITEMS = 15  # cap: keeps a chat drill session around 10-15 minutes

# Log bullet: "- [JP] term (reading) — meaning. context"
LOG_LINE_RE = re.compile(r"^[-*]\s+\[([A-Za-z]{2})\]\s+(.+)$")
DATE_HEADER_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s*$")
# Meaning separators, tried in order: em dash, en dash, spaced hyphen.
SEPARATORS = [" — ", " – ", " - "]

# Meaning is (.*?) not (.+?): captures with no meaning ("- [TG] salamat po")
# render an empty meaning field and must still round-trip on re-parse.
LEDGER_LINE_RE = re.compile(
    r"^- \[([A-Z]{2})\] (.+?) \| (.*?) \| first=(\S+) \| box=([1-5]) "
    r"\| last=(\S+) \| ok=(\d+) \| miss=(\d+)\s*$")

LEDGER_HEADER = """# Language Drill Ledger

Machine-maintained by the language-drill skill (scripts/ledger.py).
Hand-adding a line is fine if the exact format below is kept; do not
reorder fields. Source of truth for drill scheduling.

Format: `- [LANG] term | meaning | first=YYYY-MM-DD | box=1-5 | last=YYYY-MM-DD|never | ok=N | miss=N`

"""


def resolve_log_path(args):
    """Source vocab log path: --log, then LANGUAGE_LOG_PATH, then default."""
    p = args.log or os.environ.get("LANGUAGE_LOG_PATH") or DEFAULT_LOG
    return os.path.expanduser(p)


def resolve_ledger_path(args):
    """Ledger path: --ledger, then LANGUAGE_LEDGER_PATH, else beside the log."""
    p = args.ledger or os.environ.get("LANGUAGE_LEDGER_PATH")
    if p:
        return os.path.expanduser(p)
    log = resolve_log_path(args)
    return os.path.join(os.path.dirname(os.path.abspath(log)), DEFAULT_LEDGER_NAME)


def norm_key(lang, term):
    """Dedup key: language + term with any trailing (reading) stripped."""
    t = re.sub(r"\s*\([^)]*\)\s*$", "", term).strip().casefold()
    return (lang.upper(), t)


def parse_log(path):
    """Parse the vocab log. Returns (items, skipped_count).

    items: list of dicts {lang, term, meaning, first}. First occurrence wins
    (earliest date in file order) so first-seen dates are preserved.
    """
    items, seen, skipped = [], {}, 0
    current_date = None
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            m = DATE_HEADER_RE.match(line)
            if m:
                current_date = m.group(1)
                continue
            m = LOG_LINE_RE.match(line.strip())
            if not m:
                if line.strip().startswith(("-", "*")) and line.strip("-* "):
                    skipped += 1  # bullet that didn't match [XX] format
                continue
            lang, rest = m.group(1).upper(), m.group(2).strip()
            term, meaning = rest, ""
            for sep in SEPARATORS:
                if sep in rest:
                    term, meaning = rest.split(sep, 1)
                    break
            term, meaning = term.strip(), meaning.strip()
            if not term:
                skipped += 1
                continue
            key = norm_key(lang, term)
            if key in seen:
                continue  # duplicate capture; earliest first-seen wins
            item = {"lang": lang, "term": term, "meaning": meaning,
                    "first": current_date or "unknown"}
            seen[key] = item
            items.append(item)
    return items, skipped


def parse_ledger(path):
    """Parse the drill ledger. Returns (entries_dict_by_key, malformed_count)."""
    entries, malformed = {}, 0
    if not os.path.isfile(path):
        return entries, malformed
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.startswith("- ["):
                continue
            m = LEDGER_LINE_RE.match(line)
            if not m:
                malformed += 1
                continue
            e = {"lang": m.group(1), "term": m.group(2),
                 "meaning": m.group(3), "first": m.group(4),
                 "box": int(m.group(5)), "last": m.group(6),
                 "ok": int(m.group(7)), "miss": int(m.group(8))}
            entries[norm_key(e["lang"], e["term"])] = e
    return entries, malformed


def render_ledger(entries):
    """Render ledger note text. Sorted by first-seen then term: deterministic."""
    lines = [LEDGER_HEADER.rstrip("\n"), ""]
    for e in sorted(entries.values(), key=lambda x: (x["first"], x["lang"], x["term"])):
        lines.append(
            "- [{lang}] {term} | {meaning} | first={first} | box={box} "
            "| last={last} | ok={ok} | miss={miss}".format(**e))
    return "\n".join(lines) + "\n"


def write_ledger(path, content):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def cmd_sync(args):
    log_path = resolve_log_path(args)
    ledger_path = resolve_ledger_path(args)
    entries, malformed = parse_ledger(ledger_path)
    if not os.path.isfile(log_path):
        if not entries:
            print("STATUS: NO_SOURCE")
            print(f"DETAIL: {log_path} does not exist and no ledger exists. "
                  "Zero vocab-log entries so far. Offer to seed the "
                  "ledger from conversation (seed subcommand).")
            return 0
        print("STATUS: OK_NO_SOURCE")
        print(f"DETAIL: {log_path} missing, but ledger has {len(entries)} "
              "items (seeded). Nothing to sync.")
        print(f"TOTAL: {len(entries)}")
        return 0
    source_items, skipped = parse_log(log_path)
    new = 0
    for it in source_items:
        key = norm_key(it["lang"], it["term"])
        if key not in entries:
            entries[key] = {**it, "box": 1, "last": "never", "ok": 0, "miss": 0}
            new += 1
    content = render_ledger(entries)
    print("STATUS: OK")
    print(f"SOURCE_ITEMS: {len(source_items)}")
    print(f"SKIPPED_LINES: {skipped}")
    print(f"MALFORMED_LEDGER_LINES: {malformed}")
    print(f"NEW: {new}")
    print(f"TOTAL: {len(entries)}")
    if len(entries) < MIN_ITEMS:
        print(f"NOTE: SMALL_SAMPLE - only {len(entries)} items total; a full "
              f"{MIN_ITEMS}-{MAX_ITEMS} item drill is not possible yet.")
    if args.write:
        write_ledger(ledger_path, content)
        print(f"WROTE: {ledger_path}")
    else:
        print("--- PROPOSED LEDGER CONTENT (not written; re-run with --write) ---")
        print(content, end="")
    return 0


def cmd_select(args):
    ledger_path = resolve_ledger_path(args)
    entries, malformed = parse_ledger(ledger_path)
    today = datetime.date.fromisoformat(args.date)
    if not entries:
        print(json.dumps({"status": "EMPTY_LEDGER", "total": 0, "items": [],
                          "detail": f"{ledger_path} missing or has no items. "
                                    "Run sync, or seed from conversation."}))
        return 0

    def overdue_days(e):
        if e["last"] == "never":
            return 9999  # never drilled = maximally due
        last = datetime.date.fromisoformat(e["last"])
        return (today - last).days - INTERVALS[e["box"]]

    due = [e for e in entries.values() if overdue_days(e) >= 0]
    due.sort(key=lambda e: (-overdue_days(e), e["first"], e["term"]))
    picked = due[:MAX_ITEMS]
    if len(picked) < MIN_ITEMS:  # backfill with least-recently-drilled rest
        rest = [e for e in entries.values() if e not in picked]
        rest.sort(key=lambda e: ("0000" if e["last"] == "never" else e["last"],
                                 e["first"], e["term"]))
        picked += rest[:MIN_ITEMS - len(picked)]
    out = {"status": "OK", "date": args.date, "total": len(entries),
           "due_count": len(due), "selected": len(picked),
           "small_sample": len(entries) < MIN_ITEMS,
           "malformed_ledger_lines": malformed,
           "items": [{k: e[k] for k in
                      ("lang", "term", "meaning", "first", "box", "last")}
                     for e in picked]}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


# Grade -> box transition. pass: promote (learning works); miss: back to box 1
# (classic Leitner reset); partial: hold box, gets retried at same interval.
def apply_grade(e, grade, date):
    if grade == "pass":
        e["box"] = min(e["box"] + 1, MAX_BOX)
        e["ok"] += 1
    elif grade == "miss":
        e["box"] = 1
        e["miss"] += 1
    elif grade != "partial":
        return False
    e["last"] = date
    return True


def cmd_record(args):
    ledger_path = resolve_ledger_path(args)
    entries, _ = parse_ledger(ledger_path)
    if not entries:
        print("STATUS: EMPTY_LEDGER")
        print(f"DETAIL: {ledger_path} missing or empty; nothing to record against.")
        return 1
    try:
        with open(args.results, encoding="utf-8") as f:
            results = json.load(f)
        assert isinstance(results, list)
    except (OSError, ValueError, AssertionError) as exc:
        print("STATUS: BAD_RESULTS_FILE")
        print(f"DETAIL: {exc}")
        return 1
    applied, unmatched, bad_grade = 0, [], []
    for r in results:
        key = norm_key(str(r.get("lang", "")), str(r.get("term", "")))
        e = entries.get(key)
        if e is None:
            unmatched.append(r.get("term", "?"))
            continue
        if apply_grade(e, r.get("grade", ""), args.date):
            applied += 1
        else:
            bad_grade.append(r.get("term", "?"))
    print("STATUS: OK")
    print(f"APPLIED: {applied}")
    if unmatched:
        print(f"UNMATCHED: {', '.join(unmatched)}")
    if bad_grade:
        print(f"BAD_GRADE (must be pass|partial|miss): {', '.join(bad_grade)}")
    if args.write:
        write_ledger(ledger_path, render_ledger(entries))
        print(f"WROTE: {ledger_path}")
    else:
        print("DRY_RUN: re-run with --write to apply.")
    return 0


def cmd_seed(args):
    ledger_path = resolve_ledger_path(args)
    entries, _ = parse_ledger(ledger_path)
    try:
        with open(args.items, encoding="utf-8") as f:
            items = json.load(f)
        assert isinstance(items, list) and items
    except (OSError, ValueError, AssertionError) as exc:
        print("STATUS: BAD_ITEMS_FILE")
        print(f"DETAIL: expected non-empty JSON list "
              f'[{{"lang","term","meaning"}}]; got: {exc}')
        return 1
    added, skipped_dup, invalid = 0, 0, 0
    for it in items:
        lang = str(it.get("lang", "")).upper()
        term = str(it.get("term", "")).strip()
        if not re.fullmatch(r"[A-Z]{2}", lang) or not term:
            invalid += 1
            continue
        key = norm_key(lang, term)
        if key in entries:
            skipped_dup += 1
            continue
        entries[key] = {"lang": lang, "term": term,
                        "meaning": str(it.get("meaning", "")).strip(),
                        "first": args.date, "box": 1, "last": "never",
                        "ok": 0, "miss": 0}
        added += 1
    print("STATUS: OK")
    print(f"ADDED: {added}  DUPLICATES_SKIPPED: {skipped_dup}  INVALID: {invalid}")
    print(f"TOTAL: {len(entries)}")
    if len(entries) < MIN_ITEMS:
        print(f"NOTE: SMALL_SAMPLE - {len(entries)} items total.")
    content = render_ledger(entries)
    if args.write:
        write_ledger(ledger_path, content)
        print(f"WROTE: {ledger_path}")
    else:
        print("--- PROPOSED LEDGER CONTENT (not written; re-run with --write) ---")
        print(content, end="")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log",
                   help="Source vocab log markdown file, READ-ONLY "
                        "(env: LANGUAGE_LOG_PATH; default: ./language-log.md)")
    p.add_argument("--ledger",
                   help="Drill ledger file this tool writes "
                        "(env: LANGUAGE_LEDGER_PATH; default: drill-ledger.md "
                        "beside the log)")
    p.add_argument("--date", default=datetime.date.today().isoformat(),
                   help="Override 'today' (YYYY-MM-DD) for testing")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("sync")
    sp.add_argument("--write", action="store_true")
    sub.add_parser("select")
    rp = sub.add_parser("record")
    rp.add_argument("--results", required=True, help="JSON results file")
    rp.add_argument("--write", action="store_true")
    dp = sub.add_parser("seed")
    dp.add_argument("--items", required=True, help="JSON items file")
    dp.add_argument("--write", action="store_true")
    args = p.parse_args()
    try:
        datetime.date.fromisoformat(args.date)
    except ValueError:
        print(f"STATUS: BAD_DATE\nDETAIL: --date must be YYYY-MM-DD, got {args.date}")
        return 1
    return {"sync": cmd_sync, "select": cmd_select,
            "record": cmd_record, "seed": cmd_seed}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
