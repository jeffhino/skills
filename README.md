# Claude Skills

A collection of [Claude Code](https://claude.com/claude-code) skills by Jeff Hinojosa.

Skills are self-contained capabilities Claude can invoke by name — each one bundles
instructions, and optionally scripts and reference material, into a folder Claude loads
on demand. Drop one into `~/.claude/skills/` and Claude picks it up.

## Skills

| Skill | What it does |
|---|---|
| [handoff-brief](handoff-brief/) | Park and resume session context across interruptions — distills a session into a dated brief, verifies real git state on resume. |
| [workflow-author](workflow-author/) | Author Claude Code workflow scripts (`.claude/workflows/*.js`) against the real harness API, with a bundled static linter. |
| [claude-retro](claude-retro/) | Mine your local Claude Code transcripts to find which skills never fire and what you keep asking for manually. |
| [strudel-jam](strudel-jam/) | Run a [Strudel](https://strudel.cc) live-coding practice session — finds a technique gap in your saved patterns and sets an exercise. |
| [language-drill](language-drill/) | Spaced-repetition (Leitner) vocab drill from a plain-markdown log — quizzes recall-then-usage and tracks progress. |
| [curate](curate/) | Triage and prioritize [Things 3](https://culturedcode.com/things/) tasks via the `clings` CLI (macOS). |
| [prose-pass](prose-pass/) | Copy-edit a draft against Strunk's *Elements of Style* (1920, public domain) with modern verdicts baked in, plus an AI destyler that strips current-generation model tells — deterministic checker + density signals + judgment pass, three register modes. |

## Layout

Each skill lives in its own directory:

```
skills/
  <skill-name>/
    SKILL.md          # trigger, description, and instructions
    scripts/          # optional bundled scripts
    references/       # optional reference material
```

## Install a skill

Copy the skill's folder into your Claude skills directory:

```
cp -r <skill-name> ~/.claude/skills/
```

Then invoke it in Claude Code with `/<skill-name>` or let it trigger on its description.

## License

MIT — see [LICENSE](LICENSE).
