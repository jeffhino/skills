# Drill Ledger format & scheduling reference

Read this only when you need to explain the scheduling to the user, hand-fix a
malformed line, or debug the parser. Normal drills never need it — the script
owns all of this.

Ledger file: set via `LANGUAGE_LEDGER_PATH` / `--ledger` (default `drill-ledger.md`
beside the vocab log).
Script: `~/.claude/skills/language-drill/scripts/ledger.py`

## Item line grammar

```
- [LANG] term | meaning | first=YYYY-MM-DD | box=1-5 | last=YYYY-MM-DD|never | ok=N | miss=N
```

| Field | Meaning |
|---|---|
| `LANG` | Two uppercase letters: `JP` Japanese, `TG` Tagalog, `XX` any other — any language works |
| `term` | Word/phrase, usually with reading in parens: `水 (mizu)`. Grammar patterns keep the `pattern: ` prefix |
| `meaning` | Free text; may be empty; may legally contain `\|` (parser anchors on ` \| first=`) |
| `first` | Date first captured in the vocab log (or seed date). Never changes |
| `box` | Leitner box 1-5. New items start at 1 |
| `last` | Date last drilled, or `never` |
| `ok` / `miss` | Lifetime counts of `pass` and `miss` grades (`partial` increments neither) |

Dedup key = language + term with any trailing `(reading)` stripped, casefolded.
So `水 (mizu)` and `水` are the same item — the first-captured spelling wins.

Lines that don't match the grammar are counted as `MALFORMED_LEDGER_LINES` and
ignored (not deleted) — but note the ledger is fully rewritten on `--write`,
so a malformed line WILL be dropped then. If sync reports malformed lines,
read the ledger, quote the bad lines to the user, and fix format before `--write`.

## Leitner constants (in ledger.py — change there, not here)

| Box | Interval | Rationale |
|---|---|---|
| 1 | 1 day | New or just-missed: drill daily |
| 2 | 3 days | |
| 3 | 7 days | Roughly doubling ladder |
| 4 | 14 days | |
| 5 | 30 days | Mastered: monthly maintenance |

An item is due when `today - last >= interval(box)`, or `last=never`.
Session size: 10-15 (MIN_ITEMS/MAX_ITEMS). Most-overdue first; if fewer than
10 due, least-recently-drilled items backfill; if the whole ledger is under
10 items, you get them all plus `small_sample: true` — report that honestly.

## Grade → box transitions

| Grade | Box | Counters |
|---|---|---|
| `pass` | +1 (cap 5) | ok+1 |
| `partial` | unchanged (retry at same interval) | none |
| `miss` | reset to 1 | miss+1 |

All three set `last=today`, so a partial still counts as a drill exposure.

## Source format being parsed (read-only)

The vocab log is a plain markdown file — any editor or notes app can produce it.
Point the skill at it with `LANGUAGE_LOG_PATH` / `--log`. Expected shape:

```
## YYYY-MM-DD
- [JP] 諦める (akirameru) — to give up. Heard "akiramenaide" on a train.
- [TG] kahit ano — whatever / anything.
```

Parser accepts `—`, `–`, or ` - ` as the term/meaning separator; a bullet with
no separator becomes a term with empty meaning (still drillable for usage).
Bullets before any date header get `first=unknown`.
