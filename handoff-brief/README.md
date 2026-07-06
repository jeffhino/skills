# handoff-brief

A Claude Code skill that parks and resumes session context so work survives
interruptions. **Park** distills the live session — goal, decisions with
reasoning, files touched, commands that worked, open threads, and one exact next
step — into a dated brief filed at `<repo>/.claude/handoffs/`, auto-superseding
older briefs on the same topic. **Resume** finds the newest brief for a topic,
loads it, and reconciles against real git state before acting.

## Optional: non-repo handoffs

For work outside a git repo, set `HANDOFF_VAULT_DIR` to a directory where
non-repo briefs should be stored (e.g. a notes folder):

```bash
export HANDOFF_VAULT_DIR="$HOME/Documents/Handoffs"
```

If it's unset, non-repo parking is disabled and the skill uses only the
repo-scoped `.claude/handoffs/` path.

## Install

```bash
cp -r handoff-brief ~/.claude/skills/
```
