# Report JSON — field reference

Output of `scripts/mine_claude_usage.py` (one JSON object on stdout).

## Top level

| Field | Meaning |
|---|---|
| `ok` | `false` means a fatal setup problem; see `error`. Non-fatal issues never flip this. |
| `window_days` | Trailing window used. |
| `generated_at` | Local timestamp of the run. |
| `file_errors` | Present only if individual files were unreadable (list of `path: error`). |

## `volume`

| Field | Meaning |
|---|---|
| `files_scanned` | Top-level session `.jsonl` files streamed. |
| `files_skipped_older_than_window` | Files whose mtime predates the window (append-only files, so safe to skip). |
| `files_skipped_excluded` | Files inside a project dir matching an `--exclude` substring — never read at all. |
| `bytes_read` | Total bytes streamed (honest volume figure for the retro). |
| `malformed_lines_skipped` | JSON lines that failed to parse. |
| `projects_with_activity` | Project dir names that produced at least one ask/skill/command in window. |

## `sample`

| Field | Meaning |
|---|---|
| `sessions_in_window` | Distinct sessions with at least one user ask in window. |
| `typed_asks_in_window` | Total user asks in window. |
| `warning` | Non-null string when below 5 sessions or 10 asks — lead the retro with it verbatim. |

## Skills

| Field | Meaning |
|---|---|
| `installed_skills` | `{name, description (first sentence), source: user\|project}` — globbed from `~/.claude/skills/*/SKILL.md` plus `.claude/skills/*/SKILL.md` under every cwd seen in transcripts. |
| `skill_usage` | Per installed skill: Skill-tool invocations + matching slash-command uses in window. |
| `skills_never_fired` | Installed skills with 0 fires in window. |
| `skill_calls_not_matching_installed` | Skill-tool calls whose name isn't an installed skill dir — built-ins/plugins (e.g. deep-research, loop). |
| `builtin_or_other_command_usage` | Slash commands that aren't installed skills (`/model`, `/clear`, ...). |

## Asks

| Field | Meaning |
|---|---|
| `first_asks` | First ask of each session (truncated to 200 chars): "what the user opened Claude to do". Always present. |
| `asks` | Every ask — present only with `--full`. |
| `recurring_ask_groups` | Deterministic clusters: union-find over token-Jaccard >= 0.5, stopworded, asks with <3 content tokens excluded. Each group: `count`, `shared_keywords` (tokens in >= half the members), `sample_asks` (3, 120-char, PRIVATE — categorize, never quote), `sessions` (8-char session prefixes). |

## What counts as "an ask" (parser rules, verified)

- Record `type == "user"` in a top-level session file; subdirectories
  (subagent transcripts) are never read.
- `promptSource` in `{"typed", "queued"}` counts ("queued" = typed while the
  agent was busy). `sdk`/`system`/absent-with-toolUseResult are machine
  records and excluded.
- Older CLI versions (<= ~2.1.14x) wrote no `promptSource`; fallback: a user
  record with no `toolUseResult`, not `isMeta`, with real text, that is not a
  `<command-*>` invocation, `<local-command-*>` output, or an
  `[Request interrupted by user...]` marker.
- Slash commands are recognized by `<command-name>/x</command-name>` inside
  user-record text and counted separately from asks.
- Skill invocations are `tool_use` blocks named `Skill` in assistant records;
  the skill name is `input.skill`.

## Transcript locations

- Sessions: `~/.claude/projects/<flattened-cwd>/<session-uuid>.jsonl`
  (path flattening: `/Users/you/my-project` → `-Users-you-my-project`).
- A dir named `-` holds sessions launched from `/`.
- Line types seen in real files: `user`, `assistant`, `system`, `attachment`,
  `queue-operation`, `ai-title`, `custom-title`, `last-prompt`, `mode`,
  `permission-mode`, `file-history-snapshot`, `agent-name`, `agent-color`.
  Only `user` and `assistant` matter to the miner.
