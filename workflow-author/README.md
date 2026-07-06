# workflow-author

A Claude Code skill that authors **Workflow scripts** (`.claude/workflows/*.js`) — plain-JS orchestration files that fan work out to subagents while keeping the deterministic core in code. It interviews you for goal/stages/shape, drafts the file against a verified harness API reference, lints it with a bundled static checker, and walks you through a dry-run design trace. It only authors — it never executes the workflow it writes.

## Prerequisites

- Node.js (for the bundled `scripts/lint_workflow.mjs` static checker).
- Optional: the official `claude-plugins-official` marketplace installed, for a real workflow exemplar to skim. The skill works without it.

## Install

```
cp -r workflow-author ~/.claude/skills/
```
