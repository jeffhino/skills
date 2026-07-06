---
name: handoff-brief
description: Parks and resumes session context so work survives interruptions. Park mode distills the live session — goal, decisions with reasoning, files touched (absolute paths), commands that worked, open threads, and one exact next step — into a dated brief filed at <repo>/.claude/handoffs/ for repo work or an optional external handoffs folder for non-repo work, auto-superseding older briefs on the same topic via a bundled filing script. Resume mode locates the newest brief for a topic, loads it, then verifies real state (git branch/status/log may have moved) and reconciles before acting. Cheap to invoke at interrupt time; briefs are never deleted, only marked SUPERSEDED. Triggers — "write a handoff", "brief the next session", "park this", "park this session", "resume <topic>", "pick up <topic> where we left off", "handoff brief", "what was I doing on <topic>".
version: 1.0.0
---

# handoff-brief

Park or resume session context. Speed is the point — park in under a minute,
resume with verified (not assumed) state. All filing mechanics live in
`scripts/handoff.py`; do not hand-roll paths, index updates, or supersede
headers.

The script lives alongside this file; invoke it by its path relative to the
skill directory (shown below as `scripts/handoff.py`).

## Storage locations

- **Repo work** — briefs go to `<repo-root>/.claude/handoffs/`. The repo root is
  derived dynamically via `git rev-parse --show-toplevel`.
- **Non-repo work** — briefs go to the directory named by the optional
  `HANDOFF_VAULT_DIR` environment variable (e.g. a notes folder). If
  `HANDOFF_VAULT_DIR` is unset, non-repo parking is disabled and the skill uses
  only the repo-scoped path. To enable it, export the var, e.g.:
  ```bash
  export HANDOFF_VAULT_DIR="$HOME/Documents/Handoffs"
  ```

## Pick the mode

| The user says | Mode |
|---|---|
| "park this", "write a handoff", "brief the next session" | Park |
| "resume X", "pick up X", "what was I doing on X" | Resume |
| "what handoffs exist", "list handoffs" | Run `python3 scripts/handoff.py list [--repo <root>]` and show the output |

## Park mode

1. **Topic**: take the user's wording if they named one; otherwise infer a 2–4
   word topic from the session and state it ("Parking as `finance-parity`").
   Do not stall to ask — they're interrupting, keep it fast.
2. **Scope**: run `git rev-parse --show-toplevel 2>/dev/null` in the session's
   working directory.

   | Result | Scope | Action |
   |---|---|---|
   | Prints a path | repo | Remember the root; pass `--repo <root>` in step 4 |
   | Fails / not a repo | non-repo (external folder) | Omit `--repo` (requires `HANDOFF_VAULT_DIR`) |

3. **Write the brief** to a scratchpad file (e.g. `<scratchpad>/brief.md`)
   following `references/brief-template.md` exactly. For repo scope, capture
   real values first: `git branch --show-current`, `git rev-parse --short
   HEAD`, `git status --porcelain | wc -l`. Distill from the ACTUAL session:
   real decisions with their why, absolute paths, commands verbatim, exactly
   ONE next step.
4. **File it**:
   ```bash
   python3 scripts/handoff.py park \
     --topic "<topic>" --content-file <scratchpad>/brief.md [--repo <root>]
   ```
   The script creates the handoffs dir if missing, marks older same-topic
   briefs SUPERSEDED (never deletes), and updates `INDEX.md` so the newest
   brief per topic is findable in one line.
5. **Confirm** in one line: parked path + the NEXT STEP you recorded. Done.
   No summary essay.

## Resume mode

1. **Locate**: determine repo root as in Park step 2, then:
   ```bash
   python3 scripts/handoff.py resume \
     --topic "<topic>" [--repo <root>]
   ```
   The script searches the repo handoffs dir and the external folder (if
   `HANDOFF_VAULT_DIR` is set), prints the newest matching brief with its age
   and status, or lists available topics if nothing matches.
2. **Handle the result**:

   | Script output | Action |
   |---|---|
   | `BRIEF FOUND` + `status: current` | Continue to step 3 |
   | `status: SUPERSEDED — no current brief` | Tell the user only a superseded brief exists; ask before trusting it |
   | `NO BRIEF FOUND` + topic list | Show the user the available topics; do not guess |
   | `NO BRIEFS EXIST YET` | Say so plainly; offer to start fresh |

3. **Verify state before acting** — the brief is a snapshot; the world moved.
   For repo-scoped briefs run, from the repo root:
   ```bash
   git branch --show-current
   git status --porcelain
   git log --oneline -10
   ```
   Compare against the brief's "State at park" section:

   | Check | If it differs |
   |---|---|
   | Branch matches brief's branch | Report the actual branch; ask before switching — never `git checkout` on your own |
   | HEAD sha matches | New commits landed — read `git log <brief-sha>..HEAD --oneline`, summarize what changed |
   | Files listed under "Files touched" still exist (`ls` each) | Flag missing/renamed files before touching anything |
   | Brief age > 7 days | Say so explicitly; treat "Commands that worked" as possibly stale |

   For non-repo briefs: `ls` any absolute paths named in the brief and flag
   missing ones. Skip the git checks.
4. **Reconcile, then act**: give the user a 3–5 line readback — goal, what (if
   anything) drifted since park, and the recorded NEXT STEP. If nothing
   drifted, proceed with the next step. If state drifted, present the delta and
   let the user decide — do not assume the old next step still applies.

## Hard rules

- Never delete a brief. Expiry = SUPERSEDED header, which `park` applies
  automatically.
- Briefs go ONLY to `<repo>/.claude/handoffs/` or the `HANDOFF_VAULT_DIR`
  folder — nowhere else.
- Resume never mutates anything (no checkout, no stash, no edits) until the
  reconciliation readback is on screen.
- Keep invocation cheap: no extra research, no re-reading the whole repo. The
  brief captures the session that just happened, nothing more.
