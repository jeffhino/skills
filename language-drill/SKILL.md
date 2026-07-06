---
name: language-drill
description: Runs a spaced-repetition language practice session from a plain markdown vocab log (any language — Japanese and Tagalog are just examples). A bundled deterministic script parses the log into a canonical drill ledger with first-seen dates and Leitner boxes, selects 10-15 due items, then Claude runs an interactive recall-then-usage drill in chat with gentle grading and writes results back to the ledger. Handles the empty case honestly — if no vocab log exists yet, it says so plainly and offers to seed the ledger from conversation instead. Triggers — "language drill", "quiz me", "practice session".
version: 1.0.0
---

# Language Drill

Spaced practice from a plain markdown vocab log. All parsing, item selection,
and scheduling math is done by ONE bundled script — never do this math yourself.

## Paths and configuration

- Script (run it, don't reimplement): `~/.claude/skills/language-drill/scripts/ledger.py`
- **Source vocab log** (READ-ONLY, never edit): set via the `LANGUAGE_LOG_PATH`
  environment variable or the `--log` flag. Defaults to `./language-log.md`.
  This is any plain markdown file with `## YYYY-MM-DD` date headers and vocab
  bullets in the format `- [XX] term (reading) — meaning` (see below).
- **Ledger** (the ONLY file this skill writes): set via `LANGUAGE_LEDGER_PATH`
  or `--ledger`. Defaults to `drill-ledger.md` in the same directory as the log.
- Results scratch file: write drill results JSON to a temporary/scratch dir, not
  next to the log.

The vocab log is a generic, app-agnostic format — nothing about it assumes any
particular notes app. To point the skill at your log, either export
`LANGUAGE_LOG_PATH=/path/to/your/log.md` once, or pass `--log /path/to/your/log.md`
on every invocation.

### Vocab log format (documented generic format)

```
## YYYY-MM-DD
- [JP] 諦める (akirameru) — to give up. Heard "akiramenaide" on a train.
- [TG] kahit ano — whatever / anything.
```

- `## YYYY-MM-DD` headers group entries by first-seen date.
- Each vocab bullet is `- [XX] term (reading) — meaning`, where `XX` is a
  two-letter language tag (`JP`, `TG`, or any ISO-ish code — any language works).
- The `(reading)` is optional; the separator may be `—`, `–`, or ` - `; a bullet
  with no separator becomes a term with an empty meaning (still drillable).

Full ledger line format and Leitner constants: see
`~/.claude/skills/language-drill/references/ledger-format.md` (read only if you
need to hand-fix a line or explain the scheduling).

## Workflow — follow in order

### Step 1: Sync the ledger from the vocab log

```bash
python3 ~/.claude/skills/language-drill/scripts/ledger.py sync
```

(Set `LANGUAGE_LOG_PATH` first, or add `--log <path>`.)

| Script output | Action |
|---|---|
| `STATUS: NO_SOURCE` | Tell the user plainly: no vocab log exists yet, so there is nothing to drill from. Offer to seed the ledger from conversation (Step 1b). Do not invent items. |
| `STATUS: OK` but `TOTAL: 0` | The log exists but has no parseable items. Treat like NO_SOURCE: do NOT `--write` an empty ledger; offer Step 1b, and mention `SKIPPED_LINES` if nonzero (bullets that didn't match the `- [XX]` format). |
| `MALFORMED_LEDGER_LINES` > 0 | STOP before any `--write` (a rewrite drops malformed lines). Read the ledger, show the user the bad lines, fix format per `references/ledger-format.md`, re-run sync. |
| `STATUS: OK_NO_SOURCE` | Ledger was previously seeded; skip to Step 2. |
| `STATUS: OK` + ledger file does NOT exist yet | FIRST CREATION — show the user the proposed ledger content the script printed, wait for an explicit yes, then re-run with `--write`. |
| `STATUS: OK` + ledger file already exists | Auto-update is pre-approved: re-run with `--write` without asking. Say "synced N new items" so the user sees it happened. |
| `NOTE: SMALL_SAMPLE` | Repeat the honest count to the user ("only N items so far — this will be a short drill, not the full 10-15"). Never pad the session or fake a bigger set. |

Check for the ledger by listing the ledger path (default `drill-ledger.md`
beside the log, or wherever `LANGUAGE_LEDGER_PATH`/`--ledger` points).

### Step 1b: Seed from conversation (only when NO_SOURCE / EMPTY_LEDGER)

1. Ask the user for words/phrases they're learning (any language).
2. Write them to a scratch `seed.json` as
   `[{"lang":"JP","term":"水 (mizu)","meaning":"water"}, ...]`
   (`lang` = 2 letters: JP, TG, or any other ISO-ish code).
3. Dry-run: `python3 ~/.claude/skills/language-drill/scripts/ledger.py seed --items <scratch>/seed.json`
4. Show the user the proposed ledger; on explicit yes, re-run with `--write`.
   This is a first creation, so propose→confirm is mandatory here.
5. Continue to Step 2.

### Step 2: Select drill items

```bash
python3 ~/.claude/skills/language-drill/scripts/ledger.py select
```

Returns JSON. Use its `items` list verbatim and in order — do not reorder,
add, or drop items. If `"small_sample": true`, tell the user the real counts
(`selected` of `total`) before starting. If `status` is `EMPTY_LEDGER`, go to
Step 1b.

### Step 3: Run the drill (interactive, one item at a time)

For each item, two phases:

1. **Recall** — give the meaning and language, ask for the term. Example:
   "1/12 — [JP] What's the word for *to give up*?" Do NOT show the term yet.
2. **Usage** — reveal the correct term (with reading), then ask the user to use
   it in a sentence. For `pattern:` items, ask for a sentence using the pattern.

Grade each item with exactly one of:

| Grade | Rule |
|---|---|
| `pass` | Recall essentially right (minor romaji/spelling slips are fine) AND sentence uses it plausibly |
| `partial` | Recalled wrong but recognized it once revealed, or the sentence was shaky |
| `miss` | Couldn't recall and couldn't use it |

Tone: gentle. Never scold; on partial/miss give the correct form plus one
short example sentence, then move on. Keep pace brisk — one exchange per
phase, no lectures.

Track results as you go: `[{"lang":"JP","term":"<exact term from select JSON>","grade":"pass"}, ...]`.
Use the term string EXACTLY as it appeared in the select JSON, or record will
report it UNMATCHED.

### Step 4: Record results

1. Write the results array to a scratch `drill-results.json`.
2. Dry-run: `python3 ~/.claude/skills/language-drill/scripts/ledger.py record --results <scratch>/drill-results.json`
3. If `APPLIED` equals the number of items drilled and no `UNMATCHED`/`BAD_GRADE`
   lines: re-run with `--write` (auto-append pre-approved, ledger already exists).
4. If `UNMATCHED` or `BAD_GRADE` appears: fix the JSON (exact term strings;
   grades only pass/partial/miss) and retry the dry-run. Never hand-edit the
   ledger to force it.
5. Close with an honest summary: X pass / Y partial / Z miss, which items
   moved up a box, which reset to box 1, and when the next batch comes due.

## Hard rules

- The vocab log is read-only. Only the ledger file is ever written, and only
  via the script's `--write` flag.
- First creation of the ledger (sync or seed): propose→confirm→execute.
  After it exists: `--write` runs without asking — that standing approval is
  by design, state it if the user seems surprised.
- Never fabricate vocabulary, counts, or confidence. Small n gets reported
  as small n.
- No network, no email, no calendar, no tasks — this skill only reads the
  vocab log, runs the script, and chats.
