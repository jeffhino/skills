# The prose-pass rule set

Derived from William Strunk Jr., *The Elements of Style* (1920 edition, public
domain — vendored in this folder as `elements-of-style-1920.txt`), with every
rule filtered through modern usage verdicts (Chicago, AP, Garner, and the
linguistics critiques of the book, principally Pullum 2009). Rule numbers are
the 1920 edition's; later "Strunk & White" editions renumbered everything.

Two layers. The **mechanical layer** lives in `scripts/prose_check.py` — never
re-derive those checks by hand. This file is the **judgment layer**: what the
reviewing model looks for itself, each rule stated with its exceptions, because
the exceptions are what keep this from becoming the strawman version of Strunk.

---

## Judgment rules — apply these when reviewing

**J1. Danglers (Rule 7).** An opening participial phrase (or appositive, or
adjective phrase) must refer to the grammatical subject. "On arriving in
Chicago, his friends met him" — his friends didn't arrive. Still an unambiguous
error in every modern guide. Exception: fossilized sentence adverbs
("speaking of…", "considering…", "given…") are fine.

**J2. Comma splices (Rule 5).** Independent clauses joined by a comma need a
semicolon, a period, or a conjunction — and a conjunctive adverb (*however,
therefore, then*) does not rescue the comma. Exceptions Strunk himself allowed,
still valid: very short parallel clauses ("Man proposes, God disposes") and
deliberate splices in dialogue or informal registers.

**J3. Accidental fragments (Rule 6).** A stranded phrase punctuated as a
sentence is an error when it reads as a blunder; a deliberate fragment for
emphasis is a legitimate device ("Again and again he called out. No reply.") —
Strunk permitted it in 1920. In punchy register, don't flag fragments at all.

**J4. Paired commas (Rule 3).** A parenthetic interruption takes a comma on
both sides or neither — never one. Non-restrictive clauses take commas;
restrictive ones don't. (Whether the pronoun is *which* or *that* is house
style, not grammar — see the do-not-enforce list.)

**J5. Active voice, as Strunk actually wrote it (Rule 10).** The active is the
default because it is more direct and concise — but Strunk called the passive
"frequently convenient and sometimes necessary." The test is topic focus: if
the paragraph is about the receiver of the action, the passive is *correct*
("The dramatists of the Restoration are little esteemed to-day" in a paragraph
about the dramatists). Flag only: (a) passives that bury or drop an agent the
reader needs; (b) a passive depending on another passive; (c) an action-noun
subject leaving the verb nothing to do ("A survey of this region was made" →
"This region was surveyed").

**J6. Positive form (Rule 11).** Cast statements positively: *did not
remember* → *forgot*; *not honest* → *dishonest*; *did not pay attention to* →
*ignored*. Evasive negation is usually vague as well as weak. Exceptions:
genuine denial, and deliberate antithesis ("Not that I loved Caesar less…").

**J7. Definite, specific, concrete (Rule 12).** The surest way to hold
attention: "A period of unfavorable weather set in" → "It rained every day for
a week." Flag abstractions that a concrete detail would replace. Caveat:
technical and legal prose sometimes needs deliberate abstraction for scope.

**J8. Every word tells (Rule 13, beyond the script's patterns).** The script
catches the stock padding; the model catches structural dilution — an idea
doled out across several limp sentences that one sentence would carry.
Conciseness does NOT mean all-short sentences; the standard is that every word
does work.

**J9. Sentence variety (Rule 14).** A run of loose two-clause sentences
(*…and…*, *…while…*) reads sing-song. Flag the pattern, not individual
sentences; suggest recasting a few as simple, semicolon-joined, or periodic.

**J10. Parallelism (Rule 15).** Co-ordinate ideas take the same form. An
article or preposition governing a series appears before the first term only,
or before every term. Correlatives (*both/and, not only/but also, either/or,
first/second*) must be followed by matching constructions. Uncontested then
and now — applies to lists and headings too.

**J11. Related words together (Rule 16).** Keep subject near verb, relative
near antecedent, modifier next to what it modifies — flag only where the
separation actually misleads ("He wrote three articles about his adventures,
which were published in Harper's"). Modern usage fully tolerates "He only
found two mistakes" when unambiguous; don't police *only*-placement for sport.

**J12. Steady tense in summaries (Rule 17).** Summaries of works take the
literary present, held throughout; unmotivated tense-shifting is still an
error.

**J13. End-emphasis (Rule 18).** The end of the sentence is the stress
position; put the new or emphatic element there ("Because of its hardness,
this steel is used for making razors" beats the reverse). Confirmed by modern
information-structure linguistics. The sentence opening is the second-best
slot. Scales up: sentences in a paragraph, paragraphs in a piece.

**J14. Topic sentences (Rule 9).** In expository or business prose, a
paragraph should announce its topic early and develop it. Skip for narrative.
Ignore Strunk's "end in conformity with the beginning" closing formula.

**J15. Glossary judgment entries.** Still-live entries needing context to
apply: *effect/affect* beyond the script's patterns; *fact* reserved for
verifiables, not judgments; *less/fewer* (with Strunk's own round-number
exception: "less than a hundred" is fine); *like* vs *as* before clauses
(formal register only); *whom* hypercorrection — "the man who he thought was
his friend" is correct, the parenthetical "he thought" doesn't make *who* an
object; concessive *while* only where no ambiguity with the temporal sense;
*etc.* never after "such as"; empty announcement openers (*interesting*,
*one of the most*).

**J16. When a hackneyed formula appears, recast the sentence** — don't swap a
synonym into the same dead frame. This is Strunk's own meta-advice and the
single best editing move in the book.

---

## DO NOT ENFORCE — modern verdicts that override the 1920 text

These are in Strunk (or attributed to the book) and are wrong today. Flagging
any of these is a bug in the review:

1. **Singular *they*** — Strunk prescribed generic *he*; fully reversed.
   Chicago, AP, and APA all endorse singular *they*. Never "correct" it.
2. **Blanket passive-voice bans** — the folklore version, not Strunk's text.
   Pullum (2009) showed 3 of the 4 famous examples aren't even passives.
   Apply J5's narrow tests only.
3. **Split infinitives** — always grammatical; even Strunk framed the
   avoidance as taste. Flag only a genuinely awkward pile-up.
4. **Sentence-initial *However,*** — fully standard; the comma disambiguates.
5. ***That/which* for restrictive clauses** — White's 1959 addition, not
   Strunk; house style, not grammar (restrictive *which* is standard British).
   Comma placement (J4) is the real rule.
6. **Singular-only *none*** — plural *none* has centuries of precedent.
7. ***Shall/will* and first-person *should*** — dead in American English.
8. **Now-standard words** Strunk rejected: *proven, gotten, due to*
   (adverbial), *data is, fix, folks, dependable, claim* (= assert),
   *nearby, viewpoint, worthwhile, student body, oftentimes, anyone/everyone/
   someone* as single words, *different than* (informal), *cannot help but*,
   intensifier *so* (informal), *feature* as a verb, *contact* as a verb.
9. **Archaic spelling conventions** — *to-day*, "one hundred and one"
   (American style now omits *and*), etymological hyphenation.

## Register modes

- **formal** — everything: all judgment rules plus the script's `formal` tier
  (hedges, *different than*, *stated*, *kind of/sort of*).
- **standard** (default) — J1–J16 with register-tolerant exceptions honored;
  script `always` + `style` tiers.
- **punchy** — errors and clarity only: J1, J2 (splices that misread), J5–J8,
  J10, J13, J16; script `always` tier. Fragments, hedged rhythm, and informal
  idiom are the writer's voice — leave them alone.

## Provenance note

The 1920 Strunk text is public domain. Everything E.B. White added from 1959
on (the intro, "An Approach to Style," the that/which rule, ~50 glossary
entries) remains copyrighted and is not reproduced here — where his additions
survive as good advice, this rule set states the idea in its own words.
