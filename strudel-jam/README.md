# strudel-jam

A Claude Code skill that runs a focused [Strudel](https://strudel.cc) live-coding practice session: it inventories the techniques across your saved pattern files with a deterministic script, picks ONE technique you haven't used yet, and turns it into a constraint-based exercise with a paste-ready starter pattern. It then offers (propose-then-confirm) to save the session's pattern back to your folder.

## Prerequisites
- A folder of Strudel pattern files saved as raw Strudel/JS code in `.md` files (no frontmatter, no code fences), so they stay paste-able into strudel.cc. Point the skill at it via the `STRUDEL_PATTERNS_DIR` environment variable, or pass the folder as an argument to `scripts/inventory.py`. An empty or tiny folder is handled honestly.
- [strudel.cc](https://strudel.cc) to run and hear the patterns (Python 3 to run the inventory script).

## Install
```
cp -r strudel-jam ~/.claude/skills/
```
