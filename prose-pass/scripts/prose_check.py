#!/usr/bin/env python3
"""prose_check.py — deterministic prose checks derived from Strunk's The Elements
of Style (1920, public domain), filtered through modern usage verdicts.

Flags only patterns that are near-certain wins to fix. It deliberately contains
NO checks for passive voice, singular they, split infinitives, or
sentence-initial "However" — modern usage accepts all four, and enforcing them
is the classic Elements-of-Style failure mode. Judgment-level review (danglers,
parallelism, concreteness) is the calling model's job, not this script's.

Usage:
  prose_check.py FILE [FILE...] [--register standard|formal|punchy] [--json]

Registers: punchy runs only always-on error checks; standard (default) adds
style-tier checks; formal adds formal-register checks.
"""

import argparse
import json
import re
import sys

# Each check: id, tier ('always' | 'style' | 'formal'), citation, compiled
# pattern, suggestion. Order matters: more specific patterns come first, and a
# span already claimed by an earlier check is not re-flagged.
# Literal spaces in patterns are compiled as \s+ so phrases match across a
# hard line wrap in the source text.
_C = lambda p: re.compile(p.replace(" ", r"\s+"), re.IGNORECASE)

CHECKS = [
    # --- Rule 13: omit needless words (always) ---
    ("padding", "always", "Rule 13", _C(r"\bthe question as to whether\b"), "whether"),
    ("padding", "always", "Rule 13", _C(r"\bas to whether\b"), "whether"),
    ("padding", "always", "Rule 13", _C(r"\bthere (?:is|was) no doubt but that\b"), "doubtless / no doubt that"),
    ("padding", "always", "Rule 13 / 'But'", _C(r"\bdoubt but that\b"), "doubt that"),
    ("padding", "always", "Rule 13", _C(r"\bowing to the fact that\b"), "since"),
    ("padding", "always", "Rule 13", _C(r"\b(?:due to|because of|in view of) the fact that\b"), "because"),
    ("padding", "always", "Rule 13", _C(r"\b(?:in spite of|despite) the fact that\b"), "although"),
    ("padding", "always", "Rule 13", _C(r"\bcall (?:your|his|her|their|the reader's) attention to the fact that\b"), "remind / point out that"),
    ("the-fact-that", "always", "Rule 13", _C(r"\bthe fact that\b"), "recast the sentence — Strunk: revise 'the fact that' out of every sentence it appears in"),
    ("in-a-manner", "style", "Rule 13", _C(r"\bin a (\w+) manner\b"), "use the adverb: 'in a hasty manner' → 'hastily'"),
    ("for-purposes", "style", "Rule 13", _C(r"\bfor (\w+) purposes\b"), "trim: 'used for fuel purposes' → 'used for fuel'"),
    ("empty-frame", "always", "Rule 13 / glossary", _C(r"\bis a (?:man|woman|person|writer|leader|country|city|place|company|topic|subject|question|problem) (?:who|which|that)\b"), "collapse the frame: 'He is a man who is ambitious' → 'He is ambitious'"),
    ("who-which-cuttable", "style", "Rule 13", _C(r", (?:who|which) (?:is|was|are|were) "), "often cuttable: 'Trafalgar, which was Nelson's last battle' → 'Trafalgar, Nelson's last battle'"),

    # --- Glossary entries with intact modern verdicts ---
    ("of-a-nature", "always", "'Character' / 'Nature'", _C(r"\bof an? \w+ (?:nature|character)\b"), "use the plain adjective: 'acts of a hostile nature' → 'hostile acts'"),
    ("such-as-etc", "always", "'Etc.'", _C(r"\b(?:such as|for example|for instance|e\.g\.,?|including)\b[^.\n]{0,90}?,? etc\.?"), "drop 'etc.' — the introduction already signals an incomplete list"),
    ("as-good-or-better", "always", "'As good or better than'", _C(r"\bas (\w+) or (?:better|worse|more|less|higher|lower) than\b"), "complete both comparisons: 'as good as his, or better'"),
    ("case-padding", "style", "'Case'", _C(r"\bin (?:many|most|some|numerous|all|the majority of) cases\b"), "recast directly: 'In many cases, the rooms were poorly ventilated' → 'Many of the rooms were poorly ventilated'"),
    ("case-padding", "style", "'Case'", _C(r"\bit (?:has|had) (?:\w+ )?been the case that\b"), "recast directly: state the thing itself"),
    ("factor", "style", "'Factor'", _C(r"\b(?:a|an|the) (?:major|important|key|big|great|deciding|significant|crucial) factor in\b"), "recast around a concrete verb: 'training was the great factor in his winning' → 'he won by being better trained'"),
    ("interesting-announce", "style", "'Interesting'", _C(r"\bit is interesting to (?:note|recall|observe|consider)(?: that)?\b"), "cut the preamble — make it interesting instead of announcing it"),
    ("interesting-announce", "style", "'Interesting'", _C(r"\ban interesting (?:\w+ ){0,2}(?:is|was) "), "cut the preamble and tell the thing itself"),
    ("along-lines", "style", "'Line, along these lines'", _C(r"\balong (?:these|those|the same|similar) lines\b"), "'to the same effect', or name the actual subject"),
    ("literal-hyperbole", "always", "'Literal, literally'", _C(r"\ba literal \w+ of\b"), "drop 'literal' — it props up the metaphor it contradicts"),
    ("literally", "style", "'Literal, literally'", _C(r"\bliterally\b"), "if hyperbole, cut it; if factual, it is usually unneeded"),
    ("one-of-the-most", "style", "'One of the most'", _C(r"(?m)^[#>*\-\d.\x20\t]{0,8}One of the most\b"), "threadbare opener — start with the subject itself"),
    ("one-of-agreement", "style", "'One of the most'", _C(r"\bone of the \w+(?:es|s) (?:that|who) (?:is|was|has|does|seems|makes|gets|goes)\b"), "verb should be plural — the antecedent is the plural noun: 'one of the ablest men that HAVE attacked'"),
    ("thanks-in-advance", "style", "'Thanking You in Advance'", _C(r"\bthank(?:s|ing)?(?: you)? in advance\b"), "make the request directly ('Will you please…') and thank them after"),
    ("possess", "style", "'Possess'", _C(r"\bpossess(?:es|ed)?\b"), "'have' or 'own' — plainer and stronger"),
    ("stated", "formal", "'State'", _C(r"\bstated that\b"), "'said' — reserve 'state' for full or formal declarations"),
    ("most-everybody", "always", "'Most'", _C(r"\bmost (?:everybody|everyone|anybody|anyone|all of)\b"), "'almost everybody' etc. — 'most' is not 'almost'"),
    ("different-than", "formal", "'Different than'", _C(r"\bdifferent than\b"), "'different from' in formal prose (accepted informally)"),
    ("cannot-help-but", "formal", "'Help'", _C(r"\b(?:can|could)(?: ?not|n't) help but (\w+)\b"), "'could not help seeing' — now accepted idiom, but the short form is cleaner"),
    ("kind-sort-hedge", "formal", "'Kind of'", _C(r"\b(?:kind|sort) of\b"), "as a hedge, use 'rather' or cut; the literal classifying sense ('a kind of resin') is fine"),
    ("hedge-very", "style", "'Very'", _C(r"\b(?:very|really|extremely|incredibly|definitely|certainly)\b"), "prefer a word that is strong in itself"),
    ("less-count", "style", "'Less'", _C(r"\bless (?!than\b)(\w+s)\b"), "'fewer' if countable ('fewer men'); fine for quantities and round numbers"),

    # --- Rule 10's tame openers (style) ---
    ("there-opener", "style", "Rule 10", _C(r"(?:(?m:^)[\x20\t]*|(?<=[.!?])\s{1,3})There (?:is|are|was|were)\b"), "consider a concrete subject and verb: 'There were dead leaves on the ground' → 'Dead leaves covered the ground'"),

    # --- Always-wrong mechanics ---
    ("its-error", "always", "Rule 1", _C(r"\bit's (?:own|way into|way out of)\b"), "'its' — possessive pronouns take no apostrophe"),
    ("affect-noun", "style", "'Effect'", _C(r"\b(?:an|the|its|their|his|her|any) affect\b"), "probably 'effect' (result); 'affect' as a noun is a psychology term"),

    # --- AI tells (tier 'ai', active in every register; see references/ai-tells.md) ---
    # Machine artifacts: near-zero human base rate, effectively diagnostic.
    ("ai-artifact", "ai", "AI: artifact", _C(r"\bas an ai(?: language)? model\b|\bas of my last (?:knowledge )?update\b|\bi hope this (?:helps|email finds you well)\b|\bwould you like me to\b|\bcertainly! here\b|\bgreat question\b|contentReference|oaicite|turn\d+search\d+|grok_card|\[cite: ?\d+\]|utm_source=chatgpt\.com"), "chatbot chrome / machine artifact — delete it; it destroys reader trust on sight"),
    # Stock scene-setting openers: readers report bailing at these.
    ("ai-opener", "ai", "AI: stock opener", _C(r"\bin today's (?:fast-paced|digital|modern|ever-changing|rapidly evolving)[\w-]* (?:world|age|era|landscape|environment)\b|\bin th(?:is|e) (?:day and age|ever-evolving)\b|\bin the (?:ever-evolving|rapidly (?:evolving|changing)) (?:landscape|world|realm|field) of\b|\bas technology continues to (?:evolve|advance)\b|\bin a world where\b|\bgone are the days\b|\blook no further\b"), "delete the opener and start with the most specific true thing you have"),
    # Significance inflation / puffery — active across all model eras.
    ("ai-puffery", "ai", "AI: significance inflation", _C(r"\b(?:stands|serves) as a testament to\b|\ba (?:true )?testament to\b|\bplays? a (?:crucial|vital|key|significant|pivotal|central) role in\b|\bunderscor(?:es|ing) the (?:importance|need|significance)\b|\bleft an indelible mark\b|\benduring legacy\b|\bcontinues to captivate\b|\b(?:solidif|cement)(?:ied|ying|ing) (?:his|her|its|their) (?:place|legacy|position)\b|\bmarks a pivotal moment\b|\bsetting the stage for\b|\bpaving the way for\b|\ba beacon of\b|\brich (?:tapestry|cultural heritage)\b|\bnestled in the heart of\b|\bdeeply rooted in\b|\breflects broader\b|\bcannot be overstated\b"), "replace the significance claim with the concrete fact that would justify it, or cut"),
    # Stock metaphor kit.
    ("ai-metaphor", "ai", "AI: stock metaphor", _C(r"\bnavigat(?:e|ing) the (?:complexities|landscape|waters|challenges) of\b|\bunlock(?:ing)? the (?:potential|power|secrets?) of\b|\bunleash(?:ing)? the power\b|\bharness(?:ing)? the power\b|\bembark(?:ing|ed)? on a journey\b|\b(?:let's )?(?:take a )?(?:deep |)dive in(?:to)?\b|\bin the realm of\b|\belevate your\b|\bgame[- ]changer\b|\ba (?:diverse|wide|vast) array of\b|\ba myriad of\b|\ba plethora of\b|\btreasure trove\b|\ba tapestry of\b"), "say the plain thing: name the actual components, actions, or stakes"),
    # Throat-clearing.
    ("ai-throat-clear", "ai", "AI: throat-clearing", _C(r"\bit(?:'s| is) (?:important|worth|crucial) (?:to note|noting|to mention|mentioning)(?: that)?\b|\bit should be noted that\b|\bit(?:'s| is) worth mentioning\b"), "cut the preamble — the sentence works without it"),
    # Negative-parallelism antithesis: the signature current-generation construction.
    ("ai-antithesis", "ai", "AI: not-X-but-Y antithesis", _C(r"\b(?:it|this|that)(?:'s| is)? ?n[o']t (?:just|only|merely|simply|about) [^.!?\n]{2,60}?[—;,.-]+ ?(?:it(?:'s| is)|this is|but) (?:about )?"), "state the positive claim once, directly; keep negation only when the misconception is real and named"),
    ("ai-no-no-just", "ai", "AI: staccato triplet", _C(r"\bno \w[^.!?\n]{0,40}[.!?] no \w[^.!?\n]{0,40}[.!?] (?:just|only)\b"), "emphasis dressed as content — replace with the one specific claim"),
    # Reveal bridges and staged rhetorical questions.
    ("ai-reveal-bridge", "ai", "AI: reveal bridge", _C(r"\bthe (?:result|best part|kicker|catch|bottom line)\?|\b(?:but )?here'?s the (?:thing|kicker|catch)[:.]"), "answer in the same breath, as a declarative sentence"),
    # Copula avoidance.
    ("ai-copula-avoid", "ai", "AI: copula avoidance", _C(r"\b(?:serves?|stands?|functions?) as an? \b"), "usually just 'is' — reserve 'serves as' for when function differs from identity"),
    ("ai-boasts", "ai", "AI: copula avoidance", _C(r"\bboast(?:s|ing|ed)? (?:a|an|the|over|more)\b"), "'has' — plain copula"),
    # Vague authority.
    ("ai-weasel", "ai", "AI: weasel attribution", _C(r"\bexperts (?:agree|argue|say|believe|note|suggest)\b|\bstudies (?:show|suggest|have shown|indicate)\b|\bresearch (?:shows|suggests|indicates)\b|\bindustry reports\b|\bobservers have (?:noted|cited)\b|\bmany (?:believe|argue|experts)\b|\bwidely (?:regarded|considered|seen) as\b|\bsome critics (?:argue|say|contend)\b"), "name the source and date, or delete the claim"),
    # Trailing present-participle significance clauses (2-5x human rate; strongest quantified tell).
    ("ai-ing-trailer", "ai", "AI: -ing significance trailer", _C(r", (?:highlighting|underscoring|emphasizing|reflecting|demonstrating|signaling|showcasing|solidifying|cementing|marking|underlining|illustrating) "), "end the sentence at the fact; if the implication matters, give it its own sentence with an agent and evidence"),
    # Chat-UI formatting bleed.
    ("ai-bold-bullet", "ai", "AI: bold-term bullet", _C(r"(?m)^[\x20\t]*[-*+•][\x20\t]+\*\*[^*\n]{1,50}\*\*:?"), "convert the listicle to sentences, or drop the bolded label-colon scaffold"),
    ("ai-emoji-format", "ai", "AI: emoji formatting", _C(r"(?m)^[\x20\t]*(?:#{1,6}[\x20\t]*)?[✅❌🚀💡📊🔥⚡🎯✨📈🌟💪🧵👇]"), "strip decorative emoji from headers and bullets"),
    # Legacy-era vocabulary — faded from frontier defaults but still emitted by older/cheaper models.
    ("ai-vocab", "ai", "AI: era vocabulary", _C(r"\bdelv(?:e|es|ing)\b|\btapestry\b|\bgarner(?:ed|ing)?\b|\bmultifaceted\b|\bintricacies\b|\bintricate interplay\b|\bever-evolving\b|\bseamlessly\b|\bshowcas(?:e|es|ing)\b"), "plain register: examine, mix, earn, complex, smoothly, show — one hit is weak signal; two or more warrants a pass"),
    ("ai-whether-youre", "ai", "AI: audience hedge", _C(r"\bwhether you'?re an? [^.!?\n]{2,40} or an? \b"), "pick your actual reader and write to them"),
    ("ai-first-foremost", "ai", "AI: signposting", _C(r"\bfirst and foremost\b"), "'first' — or just make the point"),
]

# AI buzzword cluster: no single word is a tell (many are fine human words, so
# they are NOT per-hit checks) — the aggregate density is the signal.
AI_BUZZWORDS = {
    "crucial", "pivotal", "robust", "comprehensive", "seamless", "vibrant",
    "leverage", "leverages", "leveraging", "utilize", "utilizes", "utilizing",
    "foster", "fosters", "fostering", "holistic", "synergy", "paradigm",
    "transformative", "groundbreaking", "revolutionary", "meticulous",
    "meticulously", "intricate", "myriad", "plethora", "elevate", "empower",
    "empowering", "streamline", "streamlined", "enhance", "enhances",
    "enhancing", "moreover", "furthermore", "additionally", "notably",
    "ultimately", "genuinely", "incredibly", "cutting-edge", "state-of-the-art",
}

SIGNPOST_RX = re.compile(
    r"(?:^|[.!?]\s+)(Moreover|Furthermore|Additionally|Firstly|Secondly|"
    r"Thirdly|Lastly|In essence|Ultimately|Importantly|Notably|In conclusion|"
    r"In summary|Overall),", re.MULTILINE)


def density_flags(text, masked, words):
    """Doc-level AI-pattern density signals. Thresholds are deliberately
    conservative — these fire on saturation, never on normal human use."""
    n = len(words) or 1
    flags = []

    def add(check, count, detail, suggest):
        flags.append({"line": 0, "tier": "ai", "check": check,
                      "cite": "AI: density", "match": detail,
                      "suggest": suggest, "context": f"doc-level signal ({count} occurrences, {len(words)} words)"})

    dashes = len(re.findall(r"—|--", masked))
    if dashes >= 4 and dashes * 1000 / n > 6:
        add("ai-emdash-density", dashes,
            f"{dashes} em dashes ({round(dashes * 1000 / n, 1)}/1000w)",
            "cap near 1 per 300 words and never two in a sentence; convert splices to periods or commas. Do NOT purge them all — em dashes are also a mark of pro editing")

    buzz = [w for w in words if w.lower() in AI_BUZZWORDS]
    if len(buzz) >= 5 and len(buzz) * 1000 / n > 10:
        from collections import Counter
        top = ", ".join(f"{w}×{c}" for w, c in Counter(x.lower() for x in buzz).most_common(5))
        add("ai-buzzword-density", len(buzz), f"buzzword cluster: {top}",
            "swap for plain register (leverage→use, robust→solid, crucial→important or cut) until the cluster thins")

    posts = SIGNPOST_RX.findall(masked)
    if len(posts) >= 3:
        add("ai-signpost-density", len(posts),
            "signpost chain: " + ", ".join(sorted(set(posts))),
            "delete most transitions — order and content should carry the sequence")

    notonly = len(re.findall(r"\bnot only\b", masked, re.IGNORECASE))
    if notonly >= 2:
        add("ai-notonly-density", notonly, f"'not only … but' ×{notonly}",
            "one correlative contrast per piece; state the rest as plain claims")

    sentences = [s for s in re.split(r"[.!?]+\s", masked) if len(s.split()) >= 3]
    if len(sentences) >= 12:
        lens = [len(s.split()) for s in sentences]
        mean = sum(lens) / len(lens)
        cv = (sum((x - mean) ** 2 for x in lens) / len(lens)) ** 0.5 / mean
        if cv < 0.35:
            add("ai-metronome", len(sentences),
                f"uniform sentence rhythm (length CV {round(cv, 2)}; human prose usually >0.45)",
                "vary deliberately — set a 5-word sentence against a 30-word one; allow a fragment or an aside")

    bolds = len(re.findall(r"\*\*[^*\n]{1,60}\*\*", masked))
    if bolds >= 6:
        add("ai-bold-density", bolds, f"{bolds} bold spans",
            "mechanical boldface — if everything is bold, nothing is; bold at most one thing")

    return flags


# 'less' before these s-final mass/singular nouns is fine — do not flag.
LESS_STOPLIST = {
    "news", "means", "progress", "physics", "mathematics", "politics",
    "economics", "series", "species", "kudos", "chaos", "analysis", "stress",
    "success", "business", "access", "awareness", "gas", "glass", "grass",
}

MASK_PATTERNS = [
    re.compile(r"```.*?```", re.DOTALL),          # fenced code blocks
    re.compile(r"`[^`\n]+`"),                     # inline code
    re.compile(r"https?://\S+"),                  # URLs
    re.compile(r"\S+@\S+\.\S+"),                  # emails
]


def mask(text):
    """Blank out code/URLs with spaces so offsets and line numbers survive."""
    def blank(m):
        return re.sub(r"\S", " ", m.group(0))
    for pat in MASK_PATTERNS:
        text = pat.sub(blank, text)
    return text


def check_text(text, register, ai=True):
    tiers = {"punchy": {"always"},
             "standard": {"always", "style"},
             "formal": {"always", "style", "formal"}}[register]
    if ai:
        tiers = tiers | {"ai"}
    masked = mask(text)
    line_starts = [0]
    for m in re.finditer(r"\n", masked):
        line_starts.append(m.end())

    def line_of(pos):
        lo, hi = 0, len(line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_starts[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    flags, claimed = [], []
    for cid, tier, cite, pat, suggest in CHECKS:
        if tier not in tiers:
            continue
        for m in pat.finditer(masked):
            span = (m.start(), m.end())
            if any(s < span[1] and span[0] < e for s, e in claimed):
                continue
            if cid == "less-count" and m.group(1).lower() in LESS_STOPLIST:
                continue
            claimed.append(span)
            ln = line_of(m.start())
            src_line = text[line_starts[ln - 1]:
                            line_starts[ln] - 1 if ln < len(line_starts) else len(text)]
            flags.append({
                "line": ln,
                "tier": tier,
                "check": cid,
                "cite": cite,
                "match": " ".join(m.group(0).split()),
                "suggest": suggest,
                "context": src_line.strip()[:160],
            })
    flags.sort(key=lambda f: f["line"])
    if ai:
        words = re.findall(r"[A-Za-z''-]+", masked)
        flags += density_flags(text, masked, words)
    return flags


def stats(text):
    words = re.findall(r"[A-Za-z''-]+", mask(text))
    intens = sum(1 for w in words if w.lower() in
                 {"very", "really", "extremely", "certainly", "definitely", "incredibly"})
    return {"words": len(words),
            "intensifiers": intens,
            "intensifiers_per_1000": round(1000 * intens / len(words), 1) if words else 0}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--register", choices=["punchy", "standard", "formal"],
                    default="standard")
    ap.add_argument("--no-ai", action="store_true",
                    help="skip the AI-tell checks and density signals")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    out = []
    for path in args.files:
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        out.append({"file": path, "register": args.register,
                    "stats": stats(text),
                    "flags": check_text(text, args.register, ai=not args.no_ai)})

    if args.json:
        json.dump(out, sys.stdout, indent=1)
        print()
        return 0

    for r in out:
        s = r["stats"]
        print(f"\n== {r['file']} — {s['words']} words, register={r['register']}, "
              f"{len(r['flags'])} flags, intensifiers {s['intensifiers']} "
              f"({s['intensifiers_per_1000']}/1000w)")
        for f in r["flags"]:
            print(f"  L{f['line']:>4} [{f['tier']:<6}] {f['cite']}: \"{f['match']}\" → {f['suggest']}")
            print(f"        | {f['context']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
