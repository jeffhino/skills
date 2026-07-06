---
name: claude-retro
description: >-
  Mines your local Claude Code transcripts (~/.claude/projects/*/) for a
  trailing window (default 30 days) to find the next automation worth building.
  A bundled streaming parser extracts your typed asks and Skill invocations,
  clusters recurring asks, and compares them against every installed skill.
  Renders a local-only retro: per-skill usage (fired vs never fired), recurring
  asks with no skill behind them, friction signals, and 2-3 concrete
  skill/automation candidates with draft trigger phrases. Privacy-first — an
  optional --exclude flag hard-skips confidential projects, the report never
  leaves the machine, and the retro summarizes ask CATEGORIES, never verbatim
  message text. Triggers — "claude retro", "what did I ask Claude this month",
  "what should be a skill", "skill gap analysis", "claude usage review".
version: 1.0.0
---

# Claude Retro

Mine what you actually asked Claude recently, measure which skills earn their
keep, and propose the next automation. Everything runs local; nothing is sent
anywhere.

## Privacy rules (hard, no exceptions)

1. To keep a confidential project out of the retro, pass `--exclude <substring>`
   to the miner (repeatable). Any project dir whose name contains the substring
   is never read. Nothing is excluded by default — decide per run whether any
   directory should be off-limits, and never bypass an agreed exclusion with a
   manual read of that dir.
2. NEVER quote the user's message text verbatim in the rendered retro — not even
   the `sample_asks` snippets. Describe each recurring ask as a CATEGORY
   ("drum-programming iterations in a live-coding tool", "hotel comparison for a
   trip"), backed by counts. Shared keywords from the report may be shown as-is.
3. The report JSON stays on disk locally. Do not paste raw JSON into chat, and
   never feed it to any network tool (WebSearch/WebFetch/email/anything).

## Workflow

Copy this checklist and work through it:

- [ ] Step 1: Run the miner
- [ ] Step 2: Gate on `ok` and the sample-size warning
- [ ] Step 3: Render skill usage
- [ ] Step 4: Render recurring asks and friction
- [ ] Step 5: Propose 2-3 candidates
- [ ] Step 6: Offer follow-ups

### Step 1 — Run the miner

```bash
python3 ~/.claude/skills/claude-retro/scripts/mine_claude_usage.py --days 30 > /tmp/claude-retro-report.json
```

- Different window if the user asked for one ("this quarter" → `--days 90`).
- To keep a confidential project out of the scan, add `--exclude <substring>`
  (repeatable) — e.g. `--exclude secret-project`. Nothing is excluded by default.
- Stdlib-only Python 3; no packages to install. Exit code is always 0 — all
  errors are inside the JSON.
- Add `--full` ONLY if the user explicitly wants every ask listed; default output
  keeps first-in-session asks + clusters, which is enough for the retro.

Then `Read /tmp/claude-retro-report.json` (typically ~20 KB). Field meanings:
see `references/report-fields.md`.

### Step 2 — Gate on data quality

| Condition in JSON | Action |
|---|---|
| `ok` is `false` | Report the `error` string to the user and stop. |
| `sample.warning` is non-null | Lead the retro with that warning verbatim; label every finding "tentative". |
| `volume.malformed_lines_skipped` > 0 | Mention the count in one line; continue. |
| `volume.files_skipped_excluded` > 0 | Note "N sessions excluded via --exclude". |

Always state the volume honestly: files scanned, bytes read, sessions and
typed asks in window. Never imply more data than exists.

### Step 3 — Skill usage

Render a table from `skill_usage` + `skills_never_fired`:

| Skill | Fires (30d) | Verdict |
|---|---|---|
| morning-digest | 2 | active |
| strudel-jam | 0 | never fired |

Rules:
- "Fires" counts Skill-tool invocations plus matching slash commands — that is
  what the script measures. Skills a session merely *read* are not counted.
- For never-fired skills, do NOT recommend deletion. Just list them and note
  possible reasons (new skill, seasonal, triggers too narrow).
- `skill_calls_not_matching_installed` = built-in/plugin skills (deep-research,
  loop, ...). Report separately as "built-in usage", not as gaps.

### Step 4 — Recurring asks and friction

From `recurring_ask_groups` (already deterministically clustered by the
script — do not re-cluster by feel):

| Group property | Interpretation |
|---|---|
| `count` >= 3 AND `sessions` >= 2 | Real recurring ask → candidate material (Step 5) if no installed skill's description covers its keywords. |
| `count` >= 3 AND `sessions` == 1 | Intra-session iteration loop → friction signal only, not a skill gap. |
| `count` == 2 | Mention only if it clearly matches another signal; otherwise skip. |
| Keywords match an installed skill's description | Skill exists but the user typed the ask manually → trigger-phrase problem; suggest widening that skill's triggers instead of a new skill. |

Friction signals to call out (categories, never quotes):
- Groups spanning 2+ sessions = the user re-explaining the same context; a skill
  or CLAUDE.md note would absorb it.
- Heavy `builtin_or_other_command_usage` on the same command (e.g. `/model`
  12x) = harness friction worth a settings fix.
- Many "resume/where were we" style asks = handoff-brief is under-triggered.

### Step 5 — Candidates

Propose exactly 2-3 concrete skill/automation candidates. For each:

- **Name** (kebab-case) and one-line job.
- **Evidence**: counts from the report ("asked 4x across 3 sessions").
- **Draft trigger phrases**: 3-5, in the style `"phrase one", "phrase two"`.
- **Shape**: new skill / widen an existing skill's triggers / settings-hook
  (route the last one through the `update-config` skill).

If the data honestly supports fewer than 2 candidates, say so — never pad
with inventions. Rank by evidence count, descending.

### Step 6 — Offer follow-ups

Ask the user (propose → confirm, never do silently):
- Draft any chosen candidate as a real skill now?
- Delete `/tmp/claude-retro-report.json`, or keep it for comparison?

## Known limits (state these when relevant)

- Only local Claude Code CLI transcripts are mined — claude.ai web/mobile
  sessions are invisible to this retro.
- Subagent transcripts (subdirs of each project dir) are intentionally
  excluded: their prompts are machine-generated, not the user's asks.
- Transcripts from CLI versions <= ~2.1.14x lack the `promptSource` field;
  the script uses a verified fallback heuristic for those, which can rarely
  misclassify an odd harness record as an ask.
