#!/usr/bin/env python3
"""Mine Claude Code transcript JSONL for retro analysis.

Streams every top-level session transcript under ~/.claude/projects/*/ for a
trailing window (default 30 days) and emits ONE JSON report to stdout:
  - typed user asks (first-per-session flagged), truncated for privacy
  - Skill tool invocations + slash-command invocations, counted per name
  - installed skills (user-level + project-level) with fired/never status
  - deterministic recurring-ask groups (token Jaccard clustering)
  - honest volume + sample-size metadata

PRIVACY: pass --exclude <substring> (repeatable) to skip any project dir whose
name contains that substring — useful for confidential projects. No directory
is excluded by default. Ask text is truncated to 200 chars and this report is
local-only; the consuming skill summarizes categories, never verbatim text.

Usage: python3 mine_claude_usage.py [--days 30] [--projects-dir PATH]
                                    [--exclude SUBSTRING ...]
Exit code is always 0 with a JSON body; errors are reported in the JSON
("ok": false) so the caller never has to parse a traceback.
"""

import argparse
import glob
import json
import os
import re
import sys
import time
from collections import Counter

# 200 chars is enough to categorize an ask without storing whole messages.
ASK_TRUNCATE = 200

# Jaccard >= 0.5 on content tokens means the asks share most of their
# vocabulary — a conservative "same ask again" signal, few false positives.
JACCARD_THRESHOLD = 0.5

# Below these counts, any "pattern" is anecdote, not signal.
MIN_SESSIONS_FOR_CONFIDENCE = 5
MIN_ASKS_FOR_CONFIDENCE = 10

STOPWORDS = set(
    "a an and are as at be but by can could do does for from has have how i in is it its "
    "me my of on or our so that the them then there these they this to want was we what "
    "when where which will with would you your please help make new want".split()
)

COMMAND_NAME_RE = re.compile(r"<command-name>([^<]+)</command-name>")


def tokenize(text):
    """Lowercase content tokens (len>2, non-stopword) for similarity grouping."""
    words = re.findall(r"[a-z0-9']+", text.lower())
    return frozenset(w for w in words if len(w) > 2 and w not in STOPWORDS)


def extract_text(content):
    """Return the human text of a user message's content (str or block list)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [b.get("text", "") for b in content
                 if isinstance(b, dict) and b.get("type") == "text"]
        return "\n".join(p for p in parts if p)
    return ""


def parse_ts(record):
    """ISO timestamp -> epoch seconds, or None."""
    ts = record.get("timestamp")
    if not ts:
        return None
    try:
        # e.g. 2026-07-03T01:22:59.207Z
        from datetime import datetime, timezone
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except (ValueError, TypeError):
        return None


def scan_session(path, cutoff_epoch, project):
    """Stream one session JSONL. Returns (asks, skills, commands, cwds, bytes, bad_lines)."""
    asks, skill_invocations, command_uses, cwds = [], [], [], set()
    bytes_read = 0
    bad_lines = 0
    first_seen = False
    session_id = os.path.basename(path).replace(".jsonl", "")

    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:  # streaming — never slurp; largest files are multi-MB
            bytes_read += len(line)
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                bad_lines += 1
                continue
            if not isinstance(rec, dict) or rec.get("isSidechain"):
                continue

            epoch = parse_ts(rec)
            rtype = rec.get("type")

            if rtype == "user":
                if rec.get("cwd"):
                    cwds.add(rec["cwd"])
                msg = rec.get("message") or {}
                text = extract_text(msg.get("content"))
                if not text:
                    continue
                # Slash-command invocations (count even outside typed asks)
                m = COMMAND_NAME_RE.search(text)
                if m:
                    if epoch is None or epoch >= cutoff_epoch:
                        command_uses.append(m.group(1).lstrip("/").strip())
                    continue
                # Only genuinely human prompts count as "asks". "typed" is a
                # normal prompt; "queued" is one the user typed while the agent
                # was busy (verified in real transcripts) — both are their words.
                # None/"sdk"/"system" are tool results and machine prompts.
                # FALLBACK (verified): CLI versions <= ~2.1.14x never wrote
                # promptSource, so on those records a human ask is one with
                # no promptSource key, no toolUseResult, not isMeta, and real
                # text — otherwise whole older projects vanish from the retro.
                if "promptSource" in rec:
                    if rec["promptSource"] not in ("typed", "queued"):
                        continue
                elif "toolUseResult" in rec or rec.get("isMeta"):
                    continue
                # Harness-inserted records, not asks: <local-command-stdout>,
                # <local-command-caveat>, interrupt markers (all verified in
                # real transcripts on records that lack promptSource).
                if text.startswith(("<local-command-",
                                    "[Request interrupted by user")):
                    continue
                if epoch is not None and epoch < cutoff_epoch:
                    first_seen = True  # session started before window
                    continue
                asks.append({
                    "project": project,
                    "session": session_id,
                    "ts": rec.get("timestamp"),
                    "first_in_session": not first_seen,
                    "text": text[:ASK_TRUNCATE],
                })
                first_seen = True

            elif rtype == "assistant":
                msg = rec.get("message") or {}
                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if (isinstance(block, dict)
                            and block.get("type") == "tool_use"
                            and block.get("name") == "Skill"):
                        name = (block.get("input") or {}).get("skill")
                        if name and (epoch is None or epoch >= cutoff_epoch):
                            skill_invocations.append(name)

    return asks, skill_invocations, command_uses, cwds, bytes_read, bad_lines


def read_frontmatter(skill_md_path):
    """Parse name + description from SKILL.md YAML frontmatter (handles '>' folds)."""
    name, desc_lines, in_desc = None, [], False
    try:
        with open(skill_md_path, "r", encoding="utf-8", errors="replace") as fh:
            first = fh.readline()
            if first.strip() != "---":
                return None, ""
            for line in fh:
                if line.strip() == "---":
                    break
                if in_desc:
                    if line.startswith((" ", "\t")):
                        desc_lines.append(line.strip())
                        continue
                    in_desc = False
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip()
                elif line.startswith("description:"):
                    rest = line.split(":", 1)[1].strip()
                    if rest in (">", "|", ">-", "|-"):
                        in_desc = True
                    else:
                        desc_lines.append(rest)
    except OSError:
        return None, ""
    desc = " ".join(desc_lines)
    # First sentence is enough for gap comparison
    return name, desc.split(". ")[0][:200]


def collect_installed_skills(cwds):
    """User-level skills + project skills discovered via transcript cwd fields."""
    skills = {}
    patterns = [os.path.expanduser("~/.claude/skills/*/SKILL.md")]
    for cwd in sorted(cwds):
        patterns.append(os.path.join(cwd, ".claude", "skills", "*", "SKILL.md"))
    seen_paths = set()
    for pat in patterns:
        for path in sorted(glob.glob(pat)):
            real = os.path.realpath(path)
            if real in seen_paths:
                continue
            seen_paths.add(real)
            name, desc = read_frontmatter(path)
            if not name:
                name = os.path.basename(os.path.dirname(path))
            source = "user" if path.startswith(os.path.expanduser("~/.claude/")) else "project"
            skills[name] = {"name": name, "description": desc, "source": source}
    return skills


def group_recurring_asks(asks):
    """Union-find grouping of asks by token Jaccard similarity (deterministic)."""
    # Asks with <3 content tokens ("yes", "run it", "continue") are mid-session
    # follow-ups with no clustering signal — exclude them from grouping.
    asks = [a for a in asks if len(tokenize(a["text"])) >= 3]
    toks = [tokenize(a["text"]) for a in asks]
    parent = list(range(len(asks)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(asks)):
        if not toks[i]:
            continue
        for j in range(i + 1, len(asks)):
            if not toks[j]:
                continue
            inter = len(toks[i] & toks[j])
            union = len(toks[i] | toks[j])
            if union and inter / union >= JACCARD_THRESHOLD:
                parent[find(j)] = find(i)

    groups = {}
    for i in range(len(asks)):
        groups.setdefault(find(i), []).append(i)

    out = []
    for members in groups.values():
        if len(members) < 2:
            continue
        # Keywords present in at least half the members — strict intersection
        # of a chained cluster is often empty and tells the reader nothing.
        tok_counts = Counter(t for m in members for t in toks[m])
        majority = [t for t, c in tok_counts.most_common() if c * 2 >= len(members)]
        out.append({
            "count": len(members),
            "shared_keywords": majority[:12],
            "sample_asks": [asks[m]["text"][:120] for m in members[:3]],
            "sessions": sorted({asks[m]["session"][:8] for m in members}),
        })
    out.sort(key=lambda g: -g["count"])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="trailing window in days (default 30)")
    ap.add_argument("--projects-dir",
                    default=os.path.expanduser("~/.claude/projects"),
                    help="Claude Code projects dir")
    ap.add_argument("--full", action="store_true",
                    help="include every ask in output (default: only "
                         "first-in-session asks, keeps the report readable)")
    ap.add_argument("--exclude", action="append", default=[], metavar="SUBSTRING",
                    help="skip any project dir whose name contains this "
                         "substring (repeatable; default: exclude nothing)")
    args = ap.parse_args()
    exclude_substrings = [s.lower() for s in args.exclude if s]

    report = {"ok": True, "window_days": args.days, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}

    if not os.path.isdir(args.projects_dir):
        report.update(ok=False, error=f"projects dir not found: {args.projects_dir}",
                      asks=[], skill_usage={}, installed_skills=[])
        print(json.dumps(report, indent=2))
        return

    cutoff_epoch = time.time() - args.days * 86400
    all_asks, all_skills, all_commands, all_cwds = [], Counter(), Counter(), set()
    files_scanned = files_skipped_old = files_skipped_excluded = 0
    total_bytes = total_bad_lines = 0
    projects_seen = set()

    for proj_dir in sorted(glob.glob(os.path.join(args.projects_dir, "*"))):
        if not os.path.isdir(proj_dir):
            continue
        proj_name = os.path.basename(proj_dir)
        # Optional privacy skip: any project dir whose name contains a
        # user-supplied --exclude substring is never read (e.g. a confidential
        # project). No exclusions by default.
        if any(sub in proj_name.lower() for sub in exclude_substrings):
            files_skipped_excluded += len(glob.glob(os.path.join(proj_dir, "*.jsonl")))
            continue
        # Only top-level *.jsonl = main sessions. Subdirs hold subagent
        # transcripts (machine-generated prompts, not the user's asks) — skip.
        for path in sorted(glob.glob(os.path.join(proj_dir, "*.jsonl"))):
            try:
                if os.path.getmtime(path) < cutoff_epoch:
                    files_skipped_old += 1  # append-only files: old mtime => no in-window lines
                    continue
                asks, skills, commands, cwds, nbytes, bad = scan_session(
                    path, cutoff_epoch, proj_name)
            except OSError as e:
                total_bad_lines += 1
                report.setdefault("file_errors", []).append(f"{path}: {e}")
                continue
            files_scanned += 1
            total_bytes += nbytes
            total_bad_lines += bad
            if asks or skills or commands:
                projects_seen.add(proj_name)
            all_asks.extend(asks)
            all_skills.update(skills)
            all_commands.update(commands)
            all_cwds.update(cwds)

    installed = collect_installed_skills(all_cwds)
    # A skill counts as "fired" whether invoked via the Skill tool or typed
    # as a slash command (/morning-digest) — both are real usage.
    skill_usage = {name: all_skills.get(name, 0) + all_commands.get(name, 0)
                   for name in sorted(installed)}
    unknown_skill_calls = {k: v for k, v in all_skills.items() if k not in installed}
    other_commands = {k: v for k, v in all_commands.most_common() if k not in installed}
    never_fired = sorted(n for n, c in skill_usage.items() if c == 0)

    sessions_in_window = len({a["session"] for a in all_asks})
    n_asks = len(all_asks)

    report.update({
        "volume": {
            "files_scanned": files_scanned,
            "files_skipped_older_than_window": files_skipped_old,
            "files_skipped_excluded": files_skipped_excluded,
            "bytes_read": total_bytes,
            "malformed_lines_skipped": total_bad_lines,
            "projects_with_activity": sorted(projects_seen),
        },
        "sample": {
            "sessions_in_window": sessions_in_window,
            "typed_asks_in_window": n_asks,
            "warning": (
                f"SMALL SAMPLE: only {sessions_in_window} sessions / {n_asks} typed asks "
                f"in the last {args.days} days — treat any pattern below as tentative, "
                "not a trend."
            ) if (sessions_in_window < MIN_SESSIONS_FOR_CONFIDENCE
                  or n_asks < MIN_ASKS_FOR_CONFIDENCE) else None,
        },
        "installed_skills": sorted(installed.values(), key=lambda s: s["name"]),
        "skill_usage": skill_usage,
        "skills_never_fired": never_fired,
        "skill_calls_not_matching_installed": unknown_skill_calls,
        "builtin_or_other_command_usage": other_commands,
        "recurring_ask_groups": group_recurring_asks(all_asks),
        # First ask per session = "what the user opened Claude to do" — always
        # included. The full ask list is large; opt in with --full.
        "first_asks": sorted((a for a in all_asks if a["first_in_session"]),
                             key=lambda a: a["ts"] or ""),
    })
    if args.full:
        report["asks"] = sorted(all_asks, key=lambda a: a["ts"] or "")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
