# Claude Skills

A collection of [Claude Code](https://claude.com/claude-code) skills by Jeff Hinojosa.

Skills are self-contained capabilities Claude can invoke by name — each one bundles
instructions, and optionally scripts and reference material, into a folder Claude loads
on demand. Drop one into `~/.claude/skills/` and Claude picks it up.

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
