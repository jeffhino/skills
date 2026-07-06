# Brief template

Copy this structure exactly. Every section is required — write "none" rather
than omitting a heading. All file paths must be ABSOLUTE.

```markdown
# Handoff: <topic in plain words>

Parked: YYYY-MM-DD HH:MM
Scope: repo <absolute repo root> | non-repo (external folder)

## Goal
One or two sentences: what this work is trying to achieve, in your own terms.

## State at park
- Branch: <output of `git branch --show-current`, or "n/a (not a repo)">
- HEAD: <output of `git rev-parse --short HEAD`, or "n/a">
- Dirty files: <count from `git status --porcelain | wc -l`, or "n/a">

## Decisions made (and why)
- <decision> — because <reasoning, one line>
- ...

## Files touched
- /absolute/path/one — <what changed, half a line>
- ...

## Commands that worked
```bash
<exact commands, verbatim, copy-pasteable>
```

## Open threads
- <anything unresolved, questions pending, things still owed an answer>

## NEXT STEP (exact)
<ONE concrete action, specific enough to execute without re-deriving context.
Bad: "continue the refactor". Good: "Edit /abs/path/to/FinanceCard.swift —
replace the hardcoded month label at line ~140 with the formatter added in
BudgetEngine, then run the build">
```

## Quality bar

- Decisions WITH reasoning — a decision without its "why" is half a decision.
- Commands verbatim: flags, paths, everything. Copy from the session, do not
  reconstruct from memory.
- Exactly one NEXT STEP. If two things are pending, the second one is an open
  thread.
- Do not pad. A good brief is 30–60 lines. The next session pays for every
  line you write.
