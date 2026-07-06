#!/usr/bin/env python3
"""Inventory Strudel techniques used in a folder of saved pattern files.

Usage:
    python3 inventory.py [folder]

Folder resolution (first match wins):
    1. the [folder] command-line argument, if given
    2. the STRUDEL_PATTERNS_DIR environment variable, if set
    3. ./strudel-patterns relative to the current directory

Output: JSON on stdout. Always exits 0 unless the folder argument is
unusable in a way that makes the whole session pointless (exit 1 with a
JSON error object) -- callers should parse stdout either way.

Detection is regex-based over raw pattern text. Patterns are expected as raw
Strudel/JS code in .md files (no frontmatter, no code fences) so they stay
paste-able into strudel.cc. The script also accepts .js and .txt.
"""

import json
import os
import re
import sys
from pathlib import Path

DEFAULT_FOLDER = os.environ.get("STRUDEL_PATTERNS_DIR", "strudel-patterns")

# Files below this count make gap analysis weak evidence, not proof.
# 5 chosen because with <5 patterns, absence of a technique is more likely
# "hasn't written many patterns yet" than "doesn't know the technique".
SMALL_SAMPLE_THRESHOLD = 5

# --- Technique detectors -----------------------------------------------
# key -> (category, regex over WHOLE file text)
# Names must stay in sync with references/techniques.md.
CODE_DETECTORS = {
    # rhythm & time
    "euclid":        ("rhythm", r"\.euclid(Rot|Legato|Off)?\s*\("),
    "off":           ("rhythm", r"\.off\s*\("),
    "swing":         ("rhythm", r"\.swing(By)?\s*\("),
    "ply":           ("rhythm", r"\.ply\s*\("),
    "rev":           ("rhythm", r"\.rev\s*\("),
    "iter":          ("rhythm", r"\.iter\s*\("),
    "palindrome":    ("rhythm", r"\.palindrome\s*\("),
    "late_early":    ("rhythm", r"\.(late|early)\s*\("),
    "fast_slow":     ("rhythm", r"\.(fast|slow)\s*\("),
    # randomness & conditional logic
    "sometimes":     ("random", r"\.(sometimes(By)?|often|rarely|almost(Never|Always)|someCycles)\s*\("),
    "degrade":       ("random", r"\.degrade(By)?\s*\("),
    "choose":        ("random", r"\b(w?choose(Cycles)?)\s*\("),
    "perlin":        ("random", r"\bperlin\b"),
    "rand":          ("random", r"\b(i?rand)\b"),
    "shuffle_scramble": ("random", r"\.(shuffle|scramble)\s*\("),
    "every":         ("random", r"\.every\s*\("),
    "when":          ("random", r"\.when(mod)?\s*\("),
    "chunk":         ("random", r"\.chunk\s*\("),
    "mask_struct":   ("random", r"\.(mask|struct)\s*\("),
    # melody & harmony
    "scale":         ("melody", r"\.scale\s*\("),
    "chords":        ("melody", r"\bchord\s*\(|note\s*\(\s*[\"'`][^\"'`]*,"),
    "arp":           ("melody", r"\.arp\s*\("),
    "transpose_add": ("melody", r"\.(transpose|add)\s*\("),
    "voicing":       ("melody", r"\.voicings?\s*\("),
    # synthesis
    "adsr":          ("synthesis", r"\.(attack|decay|sustain|release|adsr)\s*\("),
    "waveform_synth": ("synthesis", r"[\"'`](sine|sawtooth|square|triangle)[\"'`]"),
    "fm":            ("synthesis", r"\.fm(h|attack|decay|env)?\s*\("),
    "vibrato":       ("synthesis", r"\.vib(mod)?\s*\("),
    "detune":        ("synthesis", r"\.detune\s*\("),
    "superimpose_layer": ("synthesis", r"\.(superimpose|layer)\s*\("),
    "noise":         ("synthesis", r"[\"'`](white|pink|brown)\b"),
    # effects
    "filters":       ("effects", r"\.(lpf|hpf|bpf|cutoff|lpq|resonance)\s*\("),
    "filter_env":    ("effects", r"\.(lpenv|lpattack|lpdecay|lpsustain|lprelease|ftype)\s*\("),
    "delay":         ("effects", r"\.delay(time|feedback)?\s*\("),
    "reverb":        ("effects", r"\.(room|roomsize|size)\s*\("),
    "distortion":    ("effects", r"\.(shape|distort|crush|coarse)\s*\("),
    "pan":           ("effects", r"\.pan\s*\("),
    "jux":           ("effects", r"\.jux(By)?\s*\("),
    "phaser":        ("effects", r"\.phaser\s*\("),
    "compressor":    ("effects", r"\.compressor\s*\("),
    # samples
    "bank":          ("samples", r"\.bank\s*\("),
    "chop_slice":    ("samples", r"\.(chop|slice|splice|striate)\s*\("),
    "sample_speed":  ("samples", r"\.speed\s*\("),
    "begin_end":     ("samples", r"\.(begin|end)\s*\("),
    "loopat_fit":    ("samples", r"\.(loopAt|fit)\s*\("),
    "cut":           ("samples", r"\.cut\s*\("),
    "custom_samples": ("samples", r"\bsamples\s*\("),
    # modulation & structure
    "signal_range":  ("modulation", r"\.range\s*\("),
    "segment":       ("modulation", r"\.segment\s*\("),
    "stack":         ("structure", r"\bstack\s*\("),
    "cat_seq":       ("structure", r"\b(cat|seq|fastcat|slowcat)\s*\("),
    "arrange":       ("structure", r"\barrange\s*\("),
}

# key -> (category, regex over quoted mini-notation strings only)
MININOTATION_DETECTORS = {
    "mn_rest":         ("mininotation", r"~"),
    "mn_subdivision":  ("mininotation", r"\["),
    "mn_alternation":  ("mininotation", r"<"),
    "mn_polymeter":    ("mininotation", r"\{"),
    "mn_chance":       ("mininotation", r"\?"),
    "mn_replicate_elongate": ("mininotation", r"[!@]"),
    "mn_speed":        ("mininotation", r"\*"),
    "mn_euclid":       ("mininotation", r"\(\s*\d+\s*,\s*\d+"),
}

# Gap ordering: pedagogical priority for a jam session. Earlier = teach
# first (high musical payoff, builds on what a sample/synth user already
# does). Gaps not listed here get appended alphabetically at the end.
GAP_PRIORITY = [
    "euclid", "mn_euclid", "jux", "off", "chop_slice", "every", "arp",
    "degrade", "mn_alternation", "mn_chance", "swing", "mask_struct",
    "ply", "chords", "fm", "filter_env", "chunk", "mn_polymeter",
    "iter", "phaser", "shuffle_scramble", "segment", "when", "voicing",
    "begin_end", "loopat_fit", "cut", "palindrome", "compressor",
]

QUOTED = re.compile(r'"([^"]*)"|\'([^\']*)\'|`([^`]*)`')


def quoted_strings(text):
    return ["".join(m.groups(default="")) for m in QUOTED.finditer(text)]


def analyze_file(path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return {"file": path.name, "error": str(e), "techniques": []}
    found = []
    for key, (_cat, rx) in CODE_DETECTORS.items():
        if re.search(rx, text):
            found.append(key)
    strings = quoted_strings(text)
    for key, (_cat, rx) in MININOTATION_DETECTORS.items():
        if any(re.search(rx, s) for s in strings):
            found.append(key)
    return {"file": path.name, "chars": len(text), "techniques": sorted(found)}


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(DEFAULT_FOLDER)
    if not folder.is_dir():
        print(json.dumps({
            "error": f"Folder not found: {folder}",
            "hint": "Pass the pattern folder as an argument or set STRUDEL_PATTERNS_DIR, then re-run.",
            "file_count": 0,
        }, indent=2))
        sys.exit(1)

    files = sorted(p for p in folder.iterdir()
                   if p.is_file() and p.suffix in (".md", ".js", ".txt")
                   and not p.name.startswith("."))
    per_file = [analyze_file(p) for p in files]

    all_keys = list(CODE_DETECTORS) + list(MININOTATION_DETECTORS)
    usage = {k: 0 for k in all_keys}
    for f in per_file:
        for t in f.get("techniques", []):
            usage[t] += 1

    used = {k: v for k, v in usage.items() if v > 0}
    gaps = [k for k in all_keys if usage[k] == 0]
    prioritized = [k for k in GAP_PRIORITY if k in gaps]
    prioritized += sorted(k for k in gaps if k not in GAP_PRIORITY)

    n = len(files)
    warnings = []
    if n == 0:
        warnings.append("Folder is EMPTY: no pattern files found. Gap analysis "
                        "is meaningless -- every technique is 'unused'. Run a "
                        "foundations session instead of a gap session.")
    elif n < SMALL_SAMPLE_THRESHOLD:
        warnings.append(f"SMALL SAMPLE: only {n} pattern file(s). A technique "
                        "missing here may just mean few patterns saved, not a "
                        "skill gap. Present gaps as suggestions, not diagnosis.")

    print(json.dumps({
        "folder": str(folder),
        "file_count": n,
        "files": per_file,
        "techniques_used": used,
        "gaps_prioritized": prioritized,
        "small_sample": n < SMALL_SAMPLE_THRESHOLD,
        "warnings": warnings,
    }, indent=2))


if __name__ == "__main__":
    main()
