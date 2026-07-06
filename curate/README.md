# curate

A Claude Code skill that triages and prioritizes your [Things 3](https://culturedcode.com/things/)
tasks — batched inbox triage, overdue flagging, Today-list curation, stale-item
surfacing, and duplicate merging. Every action is proposed and approval-gated;
the skill never mutates your task list without your say-so. Reads and status
changes go through the `clings` CLI; moves and scheduling go through AppleScript,
with hard-won workarounds baked in for several clings 0.3.0 date bugs.

**Audience:** this skill is only useful if you run Things 3 with the `clings` CLI.

## Prerequisites

- **Things 3** on macOS.
- **`clings`** — a Things 3 CLI — on your `PATH` (verify with `clings doctor`).

## Install

```bash
cp -r curate ~/.claude/skills/
```
