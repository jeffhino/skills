---
name: strudel-jam
description: Runs a Strudel live-coding practice session. Inventories the techniques used across your saved patterns in a folder of Strudel pattern files with a deterministic script, picks ONE technique you haven't used yet, and turns it into a constraint-based exercise with a paste-ready starter pattern for strudel.cc. Offers (propose-then-confirm) to save the session's pattern and notes back to the pattern folder. Handles an empty or tiny pattern folder honestly instead of inventing gaps. Triggers — "strudel practice", "jam session", "new strudel idea".
version: 1.0.0
---

# Strudel Jam

Last verified: 2026-07-03

One session = one technique. Inventory what you already use, pick one gap,
build a constrained exercise around it, hand you a starter pattern you can paste
straight into https://strudel.cc, then offer to save the results.

**Pattern folder:** point the skill at a folder of saved Strudel pattern files
via the `STRUDEL_PATTERNS_DIR` environment variable (or pass the folder as a CLI
arg to the inventory script). Patterns are stored as RAW Strudel/JS code in
`.md` files — no frontmatter, no code fences — so they stay paste-able into
strudel.cc. Keep every file you save paste-able as-is: code only, notes as
`//` comments. Never add markdown headers or fences to a pattern file.

## Hard rules
- ONE technique per session. Do not bundle two gaps "for efficiency".
- Never write to the pattern folder without showing the exact filename + full
  content and getting an explicit yes (propose → confirm → execute).
- Never overwrite an existing pattern file. If the proposed name exists, append
  `-2`, `-3`, ...
- Starter patterns: write valid Strudel syntax, double-check every function
  name against `references/techniques.md`. You cannot execute Strudel, so
  label the pattern **"untested — if strudel.cc errors, tell me the message"**.
- If the inventory reports `small_sample: true` or `file_count: 0`, say so
  plainly. Frame gaps as "not in your saved patterns yet", never as "you
  clearly don't know X".

## Session steps

Copy this checklist and work it top to bottom:
- [ ] 1. Run inventory
- [ ] 2. Report inventory honestly (incl. sample-size caveat)
- [ ] 3. Pick ONE technique
- [ ] 4. Build exercise: constraints + starter pattern
- [ ] 5. Jam happens (your side) — offer help iterating
- [ ] 6. Offer to save (propose → confirm → execute)

### 1. Run inventory
```
STRUDEL_PATTERNS_DIR=/path/to/your/patterns python3 scripts/inventory.py
```
(Or pass the folder as an argument: `python3 scripts/inventory.py /path/to/your/patterns`.)
The script resolves the pattern folder from the argument, then `STRUDEL_PATTERNS_DIR`,
then `./strudel-patterns`, and prints JSON: `file_count`, per-file `techniques`,
`techniques_used`, `gaps_prioritized` (pedagogically ordered), `small_sample`,
`warnings`.

| Script result | Action |
|---|---|
| `error` key present (folder missing) | Confirm the pattern folder path (set `STRUDEL_PATTERNS_DIR` or pass it as an arg), then re-run. If truly gone, say so and stop. |
| `file_count: 0` | Skip gap-picking. Run a **foundations session**: mini-notation basics + `stack` + one effect, from `references/techniques.md`. Say the folder is empty so this is a starting point, not gap analysis. |
| `file_count` 1–4 | Proceed, but lead with the small-sample warning verbatim in spirit: gaps are suggestions, not diagnosis. |
| `file_count` ≥ 5 | Proceed normally. |

### 2. Report
Give a 3-line read: how many patterns, top 3–5 technique families you
already lean on (plain names, not detector keys), and the first three items
of `gaps_prioritized`.

### 3. Pick ONE technique
Default: the FIRST entry of `gaps_prioritized`. Offer entries 2 and 3 as
alternates in the same breath ("today: euclid rhythms — or say 'jux' /
'chop' if you'd rather"). If you name any technique, that wins. Then read
that technique's row in `references/techniques.md` before writing anything.

### 4. Build the exercise
Produce exactly this structure:
1. **Technique** — 2–3 sentences on what it does musically (plain terms).
2. **Constraints** — exactly 3, e.g.: max 3 voices; the technique must appear
   in every rhythmic voice; 10-minute timebox. Constraints force the
   technique to be load-bearing, not decorative.
3. **Starter pattern** — a complete, paste-ready snippet (roughly 10–25
   lines) that already runs the technique once, with `//` comments marking
   the 2–3 places to mutate live. Use generic, reliable Strudel sounds
   (TR808 bank drums, `sine`/`triangle`/`sawtooth` synths, `hh bd sd cp rim`)
   so the only new element is the technique itself. Mark it untested.
4. **Stretch goal** — one line, optional.

### 5. During the jam
If you paste back an error or a pattern that sounds wrong, debug against
`references/techniques.md` first; if the reference seems stale vs. what
strudel.cc accepts, trust strudel.cc's live behavior and note the staleness.

### 6. Offer to save
Propose, then wait for confirmation before writing:
- **Pattern file** → `<pattern folder>/jam-YYYY-MM-DD-<technique>.md`.
  Confirm the naming convention on the first save. Content = final Strudel
  code, with a short `//` comment block at top: date, technique practiced,
  one-line note on what worked. Code only — must stay paste-able.
- Write with the Write tool to the file path (more reliable than editor
  integrations for multi-line code). After writing, `ls` the file to
  confirm it landed.
If declined, drop it — no nagging, no draft files anywhere.

## Files
- `scripts/inventory.py` — run it (don't re-derive its logic by reading files
  manually). Exits 0 with JSON even for empty folders.
- `references/techniques.md` — technique checklist keyed to the script's
  detector names; syntax skeletons per technique. Authored from strudel.cc
  docs knowledge; update against strudel.cc docs when stale.
