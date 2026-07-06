---
name: curate
version: 2.0.0
description: >
  Prioritizes and sorts Things 3 tasks using the clings CLI for reads
  and status changes, and AppleScript for moves/scheduling. Triages the inbox
  in approved batches, flags overdue tasks, curates the Today list, surfaces
  stale Anytime items, and merges duplicates. Conversational and batched —
  you approve every action before execution. Triggers — "curate", "triage
  my inbox", "clean up Things", "plan my day", "plan my week", "what's
  overdue", "Things 3", "clings".
---

# Curate

Collaborative triage of your Things 3 lists. You recommend, the user decides —
never execute an action they haven't approved.

## Prerequisites

- **Things 3** on macOS (this skill drives it via AppleScript and the clings CLI).
- **`clings`** — a Things 3 CLI — must be on your `PATH`. Verify with
  `clings doctor`. The bug notes below were verified against **clings 0.3.0**;
  re-test them before trusting a newer version.

## Hard rules

1. Reach the CLI as bare **`clings`** (it must be on `PATH`).
2. **Reads, complete, cancel, and property updates** go through clings.
   **Moves between lists, scheduling, and project assignment** go through the
   AppleScript recipes below — never anything else.
3. **Never cancel+re-add a task to move it.** AppleScript moves preserve the
   task's ID, creation date, notes, and checklist.
4. **Never use `delete`** unless the user explicitly says "delete" — `cancel`
   is recoverable, delete goes to trash.
5. Do NOT use `clings update --when` or `--heading` — they need a
   URL-scheme auth token that is not configured by default (re-check with
   `clings doctor` only if the user says they added one).

## Known clings 0.3.0 bugs (re-test before trusting a newer version)

**Dates are +31 years.** `creationDate`/`modificationDate` in all JSON output
are exactly 31 years in the future (Cocoa epoch bug — a task created today
shows 31 years ahead). Rules:
- Never show a raw date or an age computed from a raw date.
- To compute age: subtract exactly 31 years, then diff against today.
- Relative ordering is unaffected — "sort oldest first" on raw values is safe.

**Due dates are unusable on the read side.** `dueDate` in JSON is garbage
(a task due 2026-07-20 reads back as 2005-03-18), and `filter "due < today"`
wrongly matches future-due tasks. Therefore:
- NEVER read or filter due dates through clings. Use the AppleScript overdue
  query in step 3.
- WRITING a due date with `clings update <id> --due YYYY-MM-DD` works
  correctly (verified against Things ground truth).

## JSON shapes

All list commands (`inbox`, `today`, `anytime`, `someday`, `upcoming`,
`filter`, `search`) with `--json` return:

```json
{ "count": 31, "items": [ { "id": "K99iKmr2...", "name": "...", "notes": "",
  "status": "open", "tags": [], "project": null, "area": null, "dueDate": null,
  "creationDate": "2057-06-15T15:58:54Z", "modificationDate": "...",
  "checklistItems": [] } ] }
```

Exception: `focus --json` returns `{ "items": [ { "score": 5, "reasons":
["Unassigned"], "todo": { ...same item shape... } } ] }` — no `count`, and the
task fields sit one level down under `todo`.

## AppleScript recipes (the only sanctioned mutations outside clings)

| Intent | Command |
|---|---|
| Move to Today | `osascript -e 'tell application "Things3" to move to do id "<id>" to list "Today"'` |
| Move to Anytime | same, `list "Anytime"` |
| Move to Someday | same, `list "Someday"` |
| Schedule for a date | date-builder recipe below |
| Assign to project | `osascript -e 'tell application "Things3" to set project of to do id "<id>" to project "<name>"'` |

**Schedule for a specific date** (e.g. "this week" → pick the day):

```bash
osascript -e 'set d to (current date)' -e 'set time of d to 0' \
  -e 'set day of d to 1' -e 'set year of d to 2026' -e 'set month of d to 7' \
  -e 'set day of d to 10' -e 'tell application "Things3" to schedule to do id "<id>" for d'
```

Why this shape (all verified against Things 3):
- `set activation date of to do ...` is READ-ONLY in the scripting dictionary
  — it errors at runtime (-10006). Never use it.
- `date "2026-07-10"` string coercion silently produces **year 12178**. Never
  build AppleScript dates from "YYYY-MM-DD" strings — always the builder above.
- `set day of d to 1` comes before setting year/month to avoid month-rollover
  (e.g. day 31 + "set month to February" would roll into March).
- Do NOT use `move ... to project "<name>"` — move's target is typed as a
  built-in list; `set project of` is the writable path.

## Workflow

Copy this checklist and work through it in order:

- [ ] 1. Gather state
- [ ] 2. Triage inbox (batched, approval-gated)
- [ ] 3. Flag overdue (AppleScript query)
- [ ] 4. Curate Today
- [ ] 5. Surface stale Anytime items
- [ ] 6. Summarize

### 1. Gather state — run in parallel

```bash
clings inbox --json
clings today --json
clings anytime --json
clings projects --json
```

### 2. Triage inbox

Present inbox items in batches of 5–8 as a table — Age computed per the
+31-year rule, never raw:

```
| # | Task | Age | Recommendation | Reasoning |
```

Wait for the user to approve, override, or skip each batch before executing
anything. For each item recommend exactly one of:

| Disposition | How to execute |
|---|---|
| Today | AppleScript move to `list "Today"` |
| This week | AppleScript schedule recipe for a specific date |
| Anytime | AppleScript move to `list "Anytime"` |
| Someday | AppleScript move to `list "Someday"` |
| Assign to project | AppleScript `set project of to do id ...` |
| Complete | `clings complete <id>` |
| Cancel | `clings cancel <id>` |
| Merge (dupe) | `clings cancel <dupe-id>`, then fold anything worth keeping into the survivor: `clings update <survivor-id> --notes "..."` (other flags: `--name`, `--tags`, `--due`) |

### 3. Flag overdue

Do NOT use `clings filter "due < today"` (broken — see bugs box). Run:

```bash
osascript -e 'tell application "Things3"
set out to ""
repeat with t in (to dos whose status is open and due date < (current date))
	set d to due date of t
	set out to out & (id of t) & " | " & (name of t) & " | " & (short date string of d) & linefeed
end repeat
return out
end tell'
```

Empty output = nothing overdue; say so plainly. Otherwise propose per task:
reschedule (AppleScript schedule recipe), new deadline (`clings update
<id> --due YYYY-MM-DD` — the write side works), complete, or cancel.

### 4. Curate Today

Run `clings focus --limit 15 --json` (shape in JSON section — tasks are
under `todo`). Cross-check its ranked queue against the Today list plus what
step 2 just moved there. If Today exceeds ~7 items, propose deferring the
lowest-priority ones (AppleScript move to Anytime, or schedule for a specific
day). A good Today list is ambitious but completable: 5–7 focused tasks.

### 5. Surface stale Anytime items

From the step-1 `anytime` pull, sort by raw `creationDate` ascending (ordering
is safe) and take the oldest 15–20 with no project — target items older than
~90 days (age per the +31-year rule); don't try to process all 300+. Propose in batches, same table + approval gate as step 2:
- Still relevant → assign a project or schedule
- Stale → Someday or cancel

### 6. Summarize

- Today's curated list (final state — re-pull `clings today --json`)
- Actions taken: moved / scheduled / completed / canceled counts
- Items flagged for next time

## Bulk operations — plan, preview, execute

When one disposition applies to many items, use `clings bulk`
(subcommands: `complete`, `cancel`, `tag`, `move --to "<project>"`). Three
non-negotiable rules:

1. **`--list` defaults to `today`** — pass it explicitly on EVERY bulk call
   (`--list inbox`, `--list anytime`, even `--list today` when intended), or
   you will act on the wrong list.
2. **`--dry-run` first, always.** Show the user the preview.
3. Only after the user approves the preview, re-run the identical command with
   `-y` in place of `--dry-run` (without `-y` the confirmation prompt hangs a
   non-interactive shell).

```bash
# preview
clings bulk cancel --list inbox --where "name CONTAINS 'newsletter'" --dry-run
# after approval
clings bulk cancel --list inbox --where "name CONTAINS 'newsletter'" -y
```

"No todos match the criteria" on the dry run is a clean no-op, not an error.
Note: bulk cannot move items between built-in lists (`move` targets a
project) — batches of AppleScript `move` commands are the way for that.

## Principles

- **Bias toward action**: a quick task (<5 min) sitting in inbox for days →
  suggest Today.
- **Respect the user's energy**: 5–7 focused tasks beats 15 scattered ones.
- **Spot duplicates**: fast capture sometimes records the same intent twice
  with different wording. Flag likely dupes for the Merge flow.
- **Cancel over delete**, always, unless the user says delete.
- **Conversational, not automated**: batched proposals, explicit approval, the
  user has the final call on every action.
