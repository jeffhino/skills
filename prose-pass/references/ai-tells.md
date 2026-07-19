# The AI destyler — judgment layer

Companion to `rules.md`. The script (`prose_check.py`) handles the regex-able
AI tells and the density signals; this file is what the reviewing model checks
itself, plus the guardrails that keep de-styling from becoming witch-hunting.

Evidence base (2024–2026): the Wikipedia "Signs of AI writing" editor catalog;
Reinhart et al. (arXiv 2410.16107 — trailing participial clauses at 2–5x human
rates); Kobak et al., *Science Advances* 2025 (excess-vocabulary corpus study);
GPTZero corpus multipliers; platform data (LinkedIn slop suppression, Wikipedia
speedy-deletion criterion G15); and the false-positive literature (Stanford
HAI on ESL misclassification; the em-dash backlash coverage).

## The core insight: density and co-occurrence, not presence

Every AI tell is also a legitimate human rhetorical device. One antithesis is
rhetoric; three in 400 words plus bold-bullet scaffolding plus metronomic
paragraphs is near-conclusive. One instance of anything proves nothing —
flag patterns, and say so honestly when a hit is weak signal.

Word-level tells are also **decaying**: the famous 2023 cluster (delve,
tapestry, testament) faded as vendors updated models. The durable tells are
constructions, formatting, and rhythm. Weight accordingly.

## A1 — Judgment tells (the script can't see these)

**A1.1 Genericness — the #1 reason readers gloss over.** No named people,
companies, numbers, dates, or places; claims the median writer would also
make; could-have-been-written-by-anyone. Readers report deciding within two
sentences and switching to skim mode. This is Strunk's Rule 12 failure in
modern dress, and word-swaps don't fix it. The fix: at least one verifiable
specific per section, and one claim a generic writer wouldn't risk.

**A1.2 Stance-free both-sidesing.** Symmetric hedges that exist only for
balance ("While challenges remain, the opportunities are immense"), templated
"Despite its challenges, X continues to thrive" pivots, refusal to commit.
Fix: take one defensible position, name the single most serious objection
concretely, and say which way the evidence leans.

**A1.3 Triad saturation.** Rule-of-three everywhere — "faster, smarter, and
more efficient," three bullets, three examples. One tricolon per piece is
rhetoric; wall-to-wall triads fake comprehensiveness. Fix: keep the one item
that carries information, or use two, or four.

**A1.4 Conclusion recaps.** A final section that restates every prior point
and adds nothing. (Humans are taught this too — high false-positive risk;
judge whether it adds anything, don't reflex-flag.) Fix: end on the last
substantive point.

**A1.5 Elegant variation / synonym cycling.** Rotating through synonyms for
the same referent to avoid repetition. Fix: repeat the ordinary word for the
ordinary thing. (Caveat: some school traditions teach this to humans.)

**A1.6 Unearned profundity beats.** One-line drama without support:
"Something shifted." "And that changes everything." Fix: supply the evidence
or cut the beat.

**A1.7 Transition-glued non-arguments.** Locally fluent sentences whose
sequence doesn't argue anything; Moreover/Furthermore stitching unrelated
points. Fix: make each paragraph earn its position; use transitions that
state the logical relation ("This fails because…").

**A1.8 Verbosity without density.** Every point restated; length the content
doesn't earn. Fix: delete every sentence that restates rather than advances.

## A2 — Do-not-accuse guardrails (documented false positives)

De-styling means removing patterns that cost the writing readers. It does NOT
mean scrubbing anything a detector might dislike. Never treat these as tells:

1. **Em dashes per se.** Human writers use them heavily and always have;
   detectors' em-dash folklore has produced widely covered false accusations.
   Only extreme density (the script's threshold) warrants a note, and the fix
   is capping, not purging.
2. **Polished, error-free prose.** "Too clean" is not a tell; punishing
   quality is the failure mode. Nothing to fix.
3. **Formal or ESL register.** Detectors misclassified more than half of
   non-native-speaker essays as AI in the Stanford study. Earnest formal
   vocabulary ("delve" is ordinary Nigerian English) is not a tell — only
   cluster density is.
4. **A single anything.** One triad, one antithesis, one "crucial," one
   rhetorical question — normal writing. Flag accumulation.
5. **Domain-legitimate structure.** Bold-term bullets in a README or spec,
   headings in documentation — humans genuinely write these. The tell is the
   pattern imported where it doesn't belong (essays, emails, articles).

## A3 — Rewriting guidance for the destyle pass

When applying fixes, in priority order:

1. Strip machine artifacts and stock openers/closers outright (zero loss).
2. Deflate significance inflation into facts: what happened, when, how
   measured. If nothing justifies the claim, the sentence goes.
3. Collapse antitheses and reveal-bridges into direct statements.
4. Cut trailing "-ing" significance clauses; end sentences on the fact.
5. Replace weasel attribution with a named source or delete the claim.
6. Thin buzzword clusters into plain register (use, solid, important, improve).
7. Convert listicle scaffolding back into prose where prose belongs.
8. Break the rhythm: vary sentence and paragraph lengths, allow a fragment,
   an aside, an uneven list.
9. Add what AI can't: a named specific, a number, a first-hand observation,
   a real stance. This is the step that restores reader trust — the deletions
   only stop the bleeding.

Note the interplay with the Strunk layer: destyling and Strunk agree almost
everywhere (concrete language, omit needless words, end-emphasis), with one
tension — Strunk's love of parallel structure can reinforce AI-ish rhythm.
Parallelism within a sentence: keep. Identical architecture across every
sentence and paragraph: break.
