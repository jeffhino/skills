# claude-retro

A local-only Claude Code skill that mines your own CLI transcripts
(`~/.claude/projects/*/`) over a trailing window to find the next automation
worth building. A bundled stdlib-only Python parser extracts your typed asks and
Skill invocations, clusters recurring asks, and compares them against every
installed skill, then Claude renders a retro: per-skill usage, recurring asks
with no skill behind them, friction signals, and 2-3 concrete skill candidates.
Nothing ever leaves your machine.

## Prerequisites

- Claude Code with existing transcripts under `~/.claude/projects/`.
- Python 3 (standard library only — no packages to install).

## Privacy

The report stays on disk (`/tmp/claude-retro-report.json`) and is never sent
anywhere. To keep a confidential project out of the scan, pass
`--exclude <substring>` to the miner (repeatable); nothing is excluded by
default.

## Install

```bash
cp -r claude-retro ~/.claude/skills/
```
