---
name: prose-pass
description: Reviews a prose draft (email, doc, README, post, essay) on two axes. Axis 1 — Strunk's Elements of Style (1920, public domain) filtered through modern usage verdicts plus plain-language packs (wordy formulas, nominalization chains, hedge stacks, corporate jargon, redundant pairs, legalese, stock application phrases, urgency hype) — ~60 deterministic patterns — and judgment rules (danglers, splices, parallelism, concreteness, end-emphasis) with Strunk's own exceptions honored. Axis 2 — an AI destyler: ~25 regex tells (stock openers, significance inflation, not-just-X-but-Y antithesis, -ing significance trailers, weasel attribution, reveal bridges, engagement bait, bold-bullet scaffolding, chatbot artifacts) plus density signals (buzzword clusters, em-dash rate, signposts, triads, adverb/nominalization/ALL-CAPS saturation, metronomic sentence rhythm) and judgment tells (genericness, stance-free hedging), with documented false-positive guardrails so em dashes, polish, and formal/ESL register are never treated as tells. Eval-tested against real ChatGPT output, Sonnet fiction, bureaucratese/purple-prose/infomercial controls, and public-domain classics. Advisory, never auto-rewrites: findings cite the rule, propose a recast, edits happen only on confirmation. Three register modes (formal / standard / punchy). Triggers — "prose pass", "edit this draft", "copy edit", "tighten this up", "Strunk check", "review my writing", "de-AI this", "destyle", "make it sound human", "does this sound like AI", "AI tells".
version: 1.2.0
---

# Prose Pass

A draft-editing pass with two axes: Strunk's *The Elements of Style* (1920)
with modern verdicts baked in, and an AI destyler that strips the documented
writing habits of current-generation models. Each axis has two layers: a
deterministic script finds the mechanical problems; you (the model) find the
judgment ones. You cite rules, propose recasts, and touch nothing without
confirmation.

## Paths

- Checker (run it, never reimplement its patterns):
  `~/.claude/skills/prose-pass/scripts/prose_check.py`
- Strunk judgment rules + do-not-enforce list (READ before reviewing):
  `~/.claude/skills/prose-pass/references/rules.md`
- AI-tell judgment layer + false-positive guardrails (READ before reviewing):
  `~/.claude/skills/prose-pass/references/ai-tells.md`
- Source text for citation lookups (optional):
  `~/.claude/skills/prose-pass/references/elements-of-style-1920.txt`

## Workflow — follow in order

### Step 1: Get the draft and pick a register

- If the user gave a file path, use it. If they pasted text, write it verbatim
  to a scratch file first (the checker needs a file).
- Infer the register from the document's evident purpose and voice — cover
  letter or legal/academic prose → `formal`; business doc, email, README →
  `standard`; marketing copy, personal essay with an intentional voice →
  `punchy`. State your choice in one line ("Reviewing as standard register —
  say 'formal' or 'punchy' to rerun differently."). Don't interrogate the user
  about it; the register is cheap to change.

### Step 2: Run the mechanical checker

```
python3 ~/.claude/skills/prose-pass/scripts/prose_check.py DRAFT --register REGISTER --json
```

Trust its output. Do not add your own regex-style pattern hunting on top —
anything mechanical that it doesn't flag was either judged too noisy or is on
the do-not-enforce list. A draft with zero flags is a clean mechanical pass;
say so rather than inventing findings.

AI-tell checks (tier `ai`) run in every register — AI-pattern is not a
formality question. They include doc-level density signals reported as line-0
flags (em-dash rate, buzzword cluster, signpost chain, sentence-rhythm CV);
these are saturation signals, honest about weak single hits. If the user only
wants the Strunk pass, add `--no-ai`; if they only asked to de-AI the text,
still run the full checker but lead the report with the AI section.

### Step 3: Read `references/rules.md` and `references/ai-tells.md`, then do the judgment pass

Read the draft in full and apply judgment rules J1–J16 **at the chosen
register** (the Register modes section of rules.md says which rules are
active) and AI-tell judgment rules A1.1–A1.8 (genericness, stance-free
hedging, triad saturation, conclusion recaps, synonym cycling, unearned
profundity, transition-glued non-arguments, verbosity).
Hard constraints:

- Honor every stated exception. Strunk's escape hatches (deliberate fragments,
  topic-focused passives, short parallel splices) are part of the rules.
- Never flag anything on the do-not-enforce list. If you catch yourself about
  to "fix" singular *they*, a split infinitive, sentence-initial *However*, or
  a topic-appropriate passive — that is the failure mode this skill exists to
  avoid.
- Honor the A2 do-not-accuse guardrails: em dashes, polished prose, formal or
  ESL register, and any single instance of a pattern are not AI tells.
  Density and co-occurrence are the signal; say so when a hit is weak.
- Judgment findings need a defensible reader-facing reason (misleads, dilutes,
  buries the point, reads as slop), not "Strunk says so."

### Step 4: Render the report

One report, two sections, findings numbered continuously:

```
## Prose pass — DRAFT (N words, REGISTER register)

### Mechanical (script)
1. L12 — "owing to the fact that" → "since"  [Rule 13]
2. L15 — "of a hostile nature" → "hostile acts"  [glossary: Nature]

### AI tells
3. L3 — "It's not just about convenience — it's about…" → state the claim
   once, directly  [AI: antithesis]
4. doc — buzzword cluster (leverage×2, robust×2, crucial×1) → thin to plain
   register  [AI: density]

### Judgment
5. L4 — dangler: "Walking through the data, the anomaly appeared…" — the
   anomaly isn't walking. → "Walking through the data, I noticed…"  [Rule 7]
6. L20–24 — four consecutive "…, and…" sentences read sing-song; recast one
   or two as periodic.  [Rule 14]

### Verdict
One or two sentences: overall health, the single highest-value fix, and
anything you deliberately did NOT flag (e.g. "left your fragments alone —
they're doing voice work").
```

- Quote the smallest offending span, cite the rule, propose a concrete recast.
- Report intensifier density from the script stats only if it's notable.
- If the draft is long and flag-dense, cap the report at the ~15 highest-value
  findings and say how many minor ones you're holding back.

### Step 5: Apply fixes only on request

If the user says fix it (all, or by finding number), edit the file with
minimal diffs — change flagged spans only, never silently "improve" untouched
sentences. For AI-tell fixes follow the A3 priority order in ai-tells.md
(artifacts and openers first; end by adding a specific, a number, or a stance —
deletions alone only stop the bleeding). After applying, rerun the checker to
confirm the flags cleared and report the before/after word count. Density
flags (rhythm, buzzword cluster) may take more than one iteration; report
the metric moving, not just flag counts.

## Honesty rules

- Zero findings is a real result — report a clean pass plainly.
- If a finding is a register call rather than an error, label it as such.
- Never present a do-not-enforce item as an error, even if the user's own
  style guide disagrees — note the conflict instead and follow the user.
