#!/usr/bin/env python3
"""handoff.py — deterministic filing engine for the handoff-brief skill.

Subcommands:
  park   --topic "<topic>" --content-file <path> [--repo <repo-root>]
         Files a brief written by Claude. Creates the handoffs dir if missing,
         supersedes older briefs for the same topic, updates INDEX.md.
         Scope: --repo <root> -> <root>/.claude/handoffs/ ;
                no --repo -> external folder from HANDOFF_VAULT_DIR.
  resume --topic "<topic>" [--repo <repo-root>]
         Finds the newest brief for the topic (repo dir if given, plus the
         external folder), prints metadata + full content. Never fails hard:
         if nothing matches, lists what IS available.
  list   [--repo <repo-root>]
         Lists all briefs (repo dir if given, plus external folder) with status.

Storage:
  Repo-scoped briefs live in <repo>/.claude/handoffs/. Non-repo briefs live in
  the directory named by the HANDOFF_VAULT_DIR environment variable. If
  HANDOFF_VAULT_DIR is unset, the non-repo fallback is disabled and only the
  repo-scoped path is used.

Exit codes: 0 = ok (including "no brief found" — that is a valid answer),
            non-zero = caller error (bad paths, empty content file) with an
            ERROR: line on stderr saying exactly what to fix.
"""

import argparse
import datetime
import os
import re
import sys
from pathlib import Path

INDEX_NAME = "INDEX.md"
INDEX_HEADER = "# Handoff index — newest brief per topic"
SUPERSEDED_MARK = "SUPERSEDED"
# Filename pattern: YYYY-MM-DD-<slug>.md
BRIEF_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)\.md$")


def vault_handoffs() -> Path | None:
    """Optional external handoff folder for non-repo work.

    Read from the HANDOFF_VAULT_DIR environment variable. Returns None when the
    var is unset or empty, which cleanly disables the non-repo fallback.
    """
    raw = os.environ.get("HANDOFF_VAULT_DIR", "").strip()
    if not raw:
        return None
    return Path(raw).expanduser()


def slugify(topic: str) -> str:
    """Lowercase, non-alphanumerics -> single hyphens, trimmed."""
    slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    return slug


def handoff_dir(repo: str | None) -> Path:
    if repo:
        root = Path(repo).expanduser().resolve()
        if not root.is_dir():
            sys.exit(f"ERROR: --repo path does not exist: {root}")
        return root / ".claude" / "handoffs"
    vault = vault_handoffs()
    if vault is None:
        sys.exit(
            "ERROR: no --repo given and HANDOFF_VAULT_DIR is not set.\n"
            "Either run inside a git repo and pass --repo <root>, or set "
            "HANDOFF_VAULT_DIR to a directory for non-repo handoffs."
        )
    return vault


def scan_dir(d: Path) -> list[dict]:
    """Return brief records in d, newest first. Empty list if dir missing."""
    if not d.is_dir():
        return []
    out = []
    for f in sorted(d.iterdir(), reverse=True):
        m = BRIEF_RE.match(f.name)
        if not m:
            continue
        try:
            first = f.read_text(encoding="utf-8").splitlines()
            superseded = bool(first) and SUPERSEDED_MARK in first[0]
        except OSError:
            superseded = False
        out.append(
            {"path": f, "date": m.group(1), "slug": m.group(2),
             "superseded": superseded}
        )
    return out


def update_index(d: Path, slug: str, filename: str) -> None:
    """Rewrite INDEX.md so `slug: filename` points at the newest brief."""
    index = d / INDEX_NAME
    entries: dict[str, str] = {}
    if index.is_file():
        for line in index.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^([a-z0-9-]+): (\S+)$", line.strip())
            if m:
                entries[m.group(1)] = m.group(2)
    entries[slug] = filename
    body = INDEX_HEADER + "\n\n" + "".join(
        f"{k}: {v}\n" for k, v in sorted(entries.items())
    )
    index.write_text(body, encoding="utf-8")


def mark_superseded(rec: dict, new_filename: str, today: str) -> None:
    """Prepend a SUPERSEDED callout. Idempotent (skips if already marked)."""
    if rec["superseded"]:
        return
    text = rec["path"].read_text(encoding="utf-8")
    header = f"> [!warning] SUPERSEDED by {new_filename} on {today}\n\n"
    rec["path"].write_text(header + text, encoding="utf-8")


def cmd_park(args) -> None:
    slug = slugify(args.topic)
    if not slug:
        sys.exit("ERROR: topic slugified to empty string; pass a real topic.")
    src = Path(args.content_file)
    if not src.is_file():
        sys.exit(f"ERROR: content file not found: {src}\n"
                 "Write the brief body to a file first, then re-run park.")
    content = src.read_text(encoding="utf-8")
    if not content.strip():
        sys.exit(f"ERROR: content file is empty: {src}\n"
                 "Refusing to file an empty brief.")

    d = handoff_dir(args.repo)
    d.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    filename = f"{today}-{slug}.md"
    target = d / filename
    replaced_same_day = target.exists()

    # Supersede every older brief for this exact topic slug.
    superseded = []
    for rec in scan_dir(d):
        if rec["slug"] == slug and rec["path"].name != filename:
            mark_superseded(rec, filename, today)
            superseded.append(rec["path"].name)

    target.write_text(content, encoding="utf-8")
    update_index(d, slug, filename)

    print(f"PARKED: {target}")
    if replaced_same_day:
        print("NOTE: replaced an existing same-day brief for this topic.")
    if superseded:
        print(f"SUPERSEDED ({len(superseded)}): " + ", ".join(superseded))
    print(f"INDEX updated: {d / INDEX_NAME}")


def gather(repo: str | None) -> list[dict]:
    """All briefs from repo dir (if given) plus the external folder (if set)."""
    recs = []
    if repo:
        recs.extend(scan_dir(handoff_dir(repo)))
    vault = vault_handoffs()
    if vault:
        recs.extend(scan_dir(vault))
    return recs


def cmd_resume(args) -> None:
    slug = slugify(args.topic)
    recs = gather(args.repo)
    if not recs:
        print("NO BRIEFS EXIST YET in the searched locations:")
        if args.repo:
            print(f"  repo:  {handoff_dir(args.repo)}")
        vault = vault_handoffs()
        if vault:
            print(f"  external: {vault}")
        else:
            print("  external: (HANDOFF_VAULT_DIR not set)")
        return

    exact = [r for r in recs if r["slug"] == slug]
    fuzzy = [r for r in recs if slug in r["slug"] or r["slug"] in slug]
    pool = exact or fuzzy
    if not pool:
        print(f"NO BRIEF FOUND for topic '{slug}'.")
        print("AVAILABLE TOPICS (newest first):")
        seen = set()
        for r in recs:
            if r["slug"] not in seen:
                seen.add(r["slug"])
                flag = " (superseded)" if r["superseded"] else ""
                print(f"  {r['slug']}  — {r['path'].name}{flag}")
        return

    # Newest first; prefer a current (non-superseded) brief over a newer-named
    # superseded one only if dates tie — normally the current one IS newest.
    pool.sort(key=lambda r: (r["date"], not r["superseded"]), reverse=True)
    best = next((r for r in pool if not r["superseded"]), pool[0])
    age = (datetime.date.today()
           - datetime.date.fromisoformat(best["date"])).days
    match_kind = "exact" if exact else f"fuzzy (matched slug '{best['slug']}')"

    print("BRIEF FOUND")
    print(f"path: {best['path']}")
    print(f"date: {best['date']}  (age: {age} day{'s' if age != 1 else ''})")
    print(f"status: {'SUPERSEDED — no current brief for this topic' if best['superseded'] else 'current'}")
    print(f"match: {match_kind}")
    if len(pool) > 1:
        print(f"older briefs for this topic: {len(pool) - 1}")
    print("--- CONTENT ---")
    print(best["path"].read_text(encoding="utf-8"))


def cmd_list(args) -> None:
    locations = []
    if args.repo:
        locations.append(("repo", handoff_dir(args.repo)))
    vault = vault_handoffs()
    if vault:
        locations.append(("external", vault))
    if not locations:
        print("No locations to search: pass --repo <root> or set "
              "HANDOFF_VAULT_DIR.")
        return
    any_found = False
    for label, d in locations:
        recs = scan_dir(d)
        print(f"[{label}] {d}")
        if not recs:
            print("  (no briefs)" if d.is_dir() else "  (directory does not exist yet)")
            continue
        any_found = True
        for r in recs:
            flag = "superseded" if r["superseded"] else "CURRENT"
            print(f"  {r['date']}  {r['slug']:<30}  {flag}  {r['path'].name}")
    if not any_found:
        print("SUMMARY: zero briefs anywhere — nothing has been parked yet.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    pk = sub.add_parser("park")
    pk.add_argument("--topic", required=True)
    pk.add_argument("--content-file", required=True)
    pk.add_argument("--repo", default=None,
                    help="repo root; omit for the HANDOFF_VAULT_DIR folder")

    rs = sub.add_parser("resume")
    rs.add_argument("--topic", required=True)
    rs.add_argument("--repo", default=None)

    ls = sub.add_parser("list")
    ls.add_argument("--repo", default=None)

    args = p.parse_args()
    {"park": cmd_park, "resume": cmd_resume, "list": cmd_list}[args.cmd](args)


if __name__ == "__main__":
    main()
