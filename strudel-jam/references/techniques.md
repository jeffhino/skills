# Strudel technique checklist

Authored 2026-07-03 from Strudel (strudel.cc) docs knowledge, NOT fetched live.
**Update against strudel.cc docs when stale** — function names and defaults drift
between Strudel releases. If a starter pattern errors in strudel.cc, check the
live docs/REPL autocomplete before blaming your browser.

Keys below match `scripts/inventory.py` detector keys exactly. Each entry:
what it is → constraint idea for an exercise → syntax skeleton.
All skeletons are hand-written and untested unless a session verified them.

## Contents
- [Rhythm & time](#rhythm--time)
- [Mini-notation](#mini-notation)
- [Randomness & conditionals](#randomness--conditionals)
- [Melody & harmony](#melody--harmony)
- [Synthesis](#synthesis)
- [Effects](#effects)
- [Samples](#samples)
- [Modulation & structure](#modulation--structure)

## Rhythm & time
| Key | What | Exercise constraint | Skeleton |
|---|---|---|---|
| `euclid` | Euclidean rhythm: spread N hits over M steps | Every rhythmic voice must use `.euclid`; no hand-written drum strings | `sound("bd").euclid(3,8)`; variants `.euclidRot(3,8,2)`, `.euclidLegato(3,8)` |
| `off` | Offset a copy of the pattern in time, transform it | Build a groove where every melodic layer is `.off` copies of ONE seed line | `n("0 2 4").off(1/8, x=>x.add(7).gain(.5))` |
| `swing` | Shuffle feel | Take a straight 16th-note hat line, make 3 swing intensities | `sound("hh*8").swingBy(1/3, 4)` |
| `ply` | Repeat each event N times (subdivide) | One drum line, pattern the ply amount | `sound("bd sd").ply("<1 2 3>")` |
| `rev` | Reverse each cycle | — | `n("0 2 4 7").rev()` |
| `iter` | Rotate start point each cycle | — | `n("0 2 4 7").iter(4)` |
| `palindrome` | Forward, then backward, alternating cycles | — | `n("0 2 4 7").palindrome()` |
| `late_early` | Nudge timing (humanize) | — | `.late(.02)` |
| `fast_slow` | Tempo multiply/divide | — | `.fast(2)`, `.slow(1.5)` |

## Mini-notation
(Detected inside quoted pattern strings.)
| Key | What | Skeleton |
|---|---|---|
| `mn_euclid` | Euclid inside the string | `sound("bd(3,8) hh(5,8,1)")` — third arg is rotation |
| `mn_alternation` | `<a b c>` cycles one value per cycle | `note("c3 <e3 g3 b3>")` |
| `mn_polymeter` | `{a b c, d e}` layers different lengths | `sound("{bd sd, hh hh hh}")`; `%4` sets steps-per-cycle: `{bd sd cp}%4` |
| `mn_chance` | `?` = 50% drop; `?0.3` = 30% drop | `sound("hh*8?")` |
| `mn_replicate_elongate` | `!` repeat event, `@` stretch its length | `sound("bd!2 sd@3")` |
| `mn_rest` / `mn_subdivision` / `mn_speed` | `~`, `[a b]`, `*` | `sound("bd [sd sd] ~ bd*2")` |

## Randomness & conditionals
| Key | What | Skeleton |
|---|---|---|
| `every` | Apply fn every Nth cycle | `.every(4, x=>x.rev())` |
| `degrade` | Randomly drop events | `.degradeBy(.3)` |
| `sometimes` | Randomly transform some events (`sometimesBy`, `often`, `rarely`) | `.sometimesBy(.4, x=>x.speed(2))` |
| `choose` | Random pick from list per event | `s(choose("bd","sd","cp"))` — verify exact call form in docs |
| `shuffle_scramble` | `shuffle(n)` reorders subdivisions without repeats; `scramble(n)` with repeats | `n("0 2 4 7").shuffle(4)` |
| `mask_struct` | `struct` imposes a boolean rhythm on values; `mask` silences by boolean pattern | `note("c3").struct("t f t t")` |
| `when` / `chunk` | Conditional per cycle / transform a rotating chunk | `.chunk(4, x=>x.hpf(2000))` |
| `perlin` / `rand` | Continuous noise/random signals | `.gain(perlin.range(.6,.9))` |

## Melody & harmony
| Key | What | Skeleton |
|---|---|---|
| `arp` | Arpeggiate chords into sequences | `chord("<Am F C E>").arp("0 [0,2] 1 [0,2]")` — verify arg forms in docs |
| `chords` | Simultaneous notes (comma) or `chord()` names | `note("a3,c4,e4")` |
| `voicing` | Auto voice-leading for chord symbols | `chord("<C^7 A7b13>").voicing()` |
| `scale` | Map `n` degrees onto a scale | `n("0 2 4 6").scale("A:minor:pentatonic")` |
| `transpose_add` | Shift pitch; `.add` can be patterned | `.add("<0 5 7>")` |

## Synthesis
| Key | What | Skeleton |
|---|---|---|
| `fm` | FM synthesis: `fm` = modulation index, `fmh` = harmonic ratio | `note("a2").s("sine").fm(4).fmh("<1 2 1.5>")` |
| `adsr` | Envelope | `.attack(.01).decay(.1).sustain(.5).release(.3)` |
| `waveform_synth` | `s("sine\|sawtooth\|square\|triangle")` | — |
| `vibrato` / `detune` / `noise` | `.vib(5).vibmod(.2)`; `.detune(.1)`; `s("white")` | — |
| `superimpose_layer` | Stack a transformed copy on itself | `.superimpose(x=>x.detune(.15))` |

## Effects
| Key | What | Skeleton |
|---|---|---|
| `jux` | Original in left ear, transformed copy in right | `.jux(x=>x.rev())`, `.juxBy(.5, x=>x.fast(2))` |
| `filter_env` | Filter envelope on top of lpf | `.lpf(400).lpenv(4).lpattack(.01).lpdecay(.2)` |
| `phaser` | Sweeping notch | `.phaser(2)` |
| `filters` / `delay` / `reverb` / `distortion` / `pan` / `compressor` | `.lpf .hpf .delay .delaytime .delayfeedback .room .size .shape .crush .coarse .pan .compressor` | — |

## Samples
| Key | What | Skeleton |
|---|---|---|
| `chop_slice` | `chop(n)` grain-chops each sample; `slice`/`splice` re-sequence slices; `striate` interleaves | `s("breaks165").chop(8).rev()` — sample name must exist in loaded banks |
| `begin_end` | Play only part of a sample | `.begin(.25).end(.75)` |
| `loopat_fit` | Stretch sample to N cycles | `s("breaks125").loopAt(2)` |
| `cut` | Choke group (open/closed hat behavior) | `.cut(1)` |
| `custom_samples` | Load your own via `samples({...}, baseUrl)` | see strudel.cc "samples" docs |
| `bank` / `sample_speed` | `.bank("RolandTR808")`; `.speed(2)` (negative = reverse) | — |

## Modulation & structure
| Key | What | Skeleton |
|---|---|---|
| `segment` | Sample a continuous signal into N discrete events | `n(sine.segment(8).range(0,7)).scale("C:minor")` |
| `signal_range` | Continuous LFOs: `sine.range(200,2000).slow(4)` | — |
| `stack` / `cat_seq` / `arrange` | Layer / sequence / song structure | `arrange([4, a], [8, b])` |
