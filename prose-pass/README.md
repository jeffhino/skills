# prose-pass

A draft-editing skill with two axes: William Strunk Jr.'s *The Elements of
Style* (1920 edition, public domain) with modern usage verdicts baked in —
enforcing the parts that held up, refusing the parts that didn't — and an
**AI destyler** that strips the documented writing habits of current-generation
language models.

## What it does

Point it at a draft (email, doc, README, essay) and it runs two passes:

1. **Mechanical** — a bundled deterministic script (`scripts/prose_check.py`,
   stdlib-only Python) flags ~35 near-certain patterns with line numbers:
   Rule 13 padding ("owing to the fact that" → since), glossary survivors
   ("of a hostile nature", "such as … etc.", "as good or better than",
   *literally* propping up hyperbole), empty frames ("he is a man who…"),
   its/it's, affect/effect, and more. Markdown code blocks, inline code, and
   URLs are masked before matching.
2. **Judgment** — the model reviews against 16 context-dependent rules
   (danglers, comma splices, parallelism, concrete language, end-emphasis,
   active voice *as Strunk actually stated it* — topic-focus test, not a
   passive ban), each encoded with its original exceptions.

Findings cite the rule and propose a recast. Nothing is rewritten without
confirmation.

## The AI destyler

Built from the 2024–2026 evidence base (Wikipedia's "Signs of AI writing"
editor catalog, the Reinhart and Kobak corpus studies, GPTZero corpus
multipliers, platform slop-suppression data) rather than 2023 folklore — so
it weights the durable tells (constructions, formatting, rhythm) over the
fading word blacklist:

- **Regex tells** — chatbot artifacts ("As an AI language model",
  `utm_source=chatgpt.com`), stock openers ("In today's fast-paced world"),
  significance inflation ("stands as a testament to", "plays a crucial role
  in"), the "it's not just X — it's Y" antithesis, "No X. No Y. Just Z.",
  reveal bridges ("The best part?"), trailing "-ing" significance clauses,
  weasel attribution ("experts agree"), bold-term bullet scaffolding, emoji
  formatting, copula avoidance ("serves as" for "is").
- **Density signals** (doc-level, saturation-triggered): buzzword cluster
  rate, em-dash rate, signpost chains (Moreover/Furthermore/Additionally),
  "not only" repetition, mechanical boldface, and sentence-rhythm uniformity
  (coefficient of variation of sentence lengths).
- **Judgment tells** (model layer): genericness — the #1 reason readers gloss
  over — stance-free both-sidesing, triad saturation, conclusion recaps,
  synonym cycling, unearned profundity.

It also carries explicit **do-not-accuse guardrails** from the false-positive
literature: em dashes, polished prose, and formal/ESL register are never
treated as tells, and no single instance of anything is. Density and
co-occurrence are the signal. Use `--no-ai` to run the Strunk pass alone.

## What it refuses to do

A hard do-not-enforce list covers the famous folklore rules modern usage has
overturned: singular *they* (now endorsed by Chicago/AP/APA), split
infinitives, sentence-initial *However*, blanket passive-voice bans, the
that/which distinction-as-grammar, singular-only *none*, *shall/will*. About a
third of the 1920 book is dead or reversed; this skill knows which third.

## Register modes

`formal` / `standard` (default) / `punchy` — because most "softened" Strunk
rules are really register rules. Punchy mode leaves fragments, hedges, and
informal idiom alone; they're voice, not errors.

## Try the checker standalone

```
python3 scripts/prose_check.py draft.md --register standard
python3 scripts/prose_check.py draft.md --json
```

## Provenance

The 1920 Strunk text is public domain and vendored at
`references/elements-of-style-1920.txt` (source: Project Gutenberg #37134,
boilerplate stripped). Everything E.B. White added from 1959 onward remains
copyrighted and is not reproduced — where his additions survive as good
advice, the rule set restates the idea in its own words. The modern verdicts
draw on Chicago, AP, Garner, and Geoffrey Pullum's "50 Years of Stupid
Grammar Advice" (2009).
