# language-drill

A Claude Code skill that runs a spaced-repetition (Leitner) language practice
session in chat from a plain markdown vocab log — any language works (Japanese
and Tagalog are just examples). A bundled deterministic script parses your log
into a drill ledger, picks 10-15 due items, and Claude quizzes you recall-then-usage
with gentle grading, writing results back to the ledger.

**Vocab log format:** a markdown file with `## YYYY-MM-DD` date headers and bullets
`- [XX] term (reading) — meaning` (`XX` = a two-letter language tag; reading and
meaning optional). Point the skill at it with the `LANGUAGE_LOG_PATH` env var (or
the `--log` flag); the ledger is written to `LANGUAGE_LEDGER_PATH` / `--ledger`,
defaulting to `drill-ledger.md` beside the log.

**Install:** `cp -r language-drill ~/.claude/skills/`
