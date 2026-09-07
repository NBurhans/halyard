# HALYARD / target SABLE — Phase 4 gate report (rev 2)

Supersedes rev 1. Three approved changes implemented: continuous-margin scoring, utility in the 1v1 primitive, and the full item catalogue. All 19 checkpoints re-run.

**Headline: two of the three changes did what they were meant to. The third did not, and the reason is that my rev-1 diagnosis was measured on the wrong population. §3 is the correction, and it matters more than anything else here.**

---

## 1. What changed

### 1.1 Item catalogue — 13 items to 182

Derived from the `hold_effect` codes in `02_world.tsv` rather than written by hand, so an item added to the hack appears automatically.

| class | items | reliable |
|---|---|---|
| mega | 70 | 13 |
| **type_boost** | **20** | **19** |
| **resist_berry** | **18** | **18** |
| species_locked | 9 | 3 |
| utility_misc | 8 | 3 |
| status_cure | 6 | 6 |
| longevity / weather_ext / terrain_seed | 4 each | 4 |
| 18 further classes | 1 each | — |

The complete set of 18 type-boost items and 18 resist berries had never entered the generator. Only 12 held items remain uncatalogued, each explicitly classed as having no build effect — nothing dropped silently.

Effect on the enumerated set: top item share fell from **25% to 13.6%**, and item dependence collapsed from 5,015 affected ceilings to **294** (mean gap 0.178 → 0.048), because reliable items now genuinely compete.

### 1.2 Utility in the primitive

Rather than bolting a bonus onto the score, hazards, status, recovery and screens act on the same turns-to-KO race as damage, so the two are commensurable:

- **chip** — Stealth Rock scaled by the defender's Rock matchup; Spikes only against grounded targets
- **denial** — sleep 1.5 turns, paralysis 0.75, poison/leech/phaze 0.5; paralysis also halves opponent speed and can flip speed order
- **longevity** — recovery subtracts from incoming damage per turn; screens ×0.66; burn cuts physical damage 25%

Each is stored in its own column (`utility_tags`, `hazard_chip`, `denial_turns`, `incoming_after_utility`) so a verdict traces back to its cause. Worked example: Pidgey with Reflect + Roost vs Rhyhorn — incoming fraction 0.5686 → 0.1253, flipping the matchup to a win.

**Support-track mean score rose from 0.115 to 0.245.** The gap to attacking tracks narrowed from ~4× to ~1.7×.

### 1.3 Continuous-margin scoring

`weighted_score` now uses the squashed, boss-weighted margin the matrix already computed. The verdict is retained as `verdict_score`.

**Resolution improved sharply: checkpoint 1 went from 26 distinct scores across 1,035 species to 142.**

### 1.4 Scale

| | rev 1 | rev 2 |
|---|---|---|
| Candidate builds to the matrix | 52,965 | 119,472 |
| Matrix cells | 1,471,929 | **1,562,981** |
| Distinct items appearing as a ceiling | 3 | 22 |

Candidates are bucketed by item **class** — up to three per track — so the matrix, not the pre-matrix heuristic, chooses the published ceiling's item.

---

## 2. Invariants after the changes

| Invariant | Result |
|---|---|
| I1 item ≤ 25% | **FAIL** — Life Orb 61.4% (was Leftovers 47.6%) |
| I2 nature ≤ 20% | **FAIL** — Adamant 57.3%, Modest 38.4% |
| I3 \|r\| ≤ 0.60 | **FAIL 17/19**, mean r = 0.751 (was 18/19, mean 0.788) |

I1 and I2 got **worse**, not better, despite the catalogue expanding 14×.

---

## 3. Correction: my rev-1 diagnosis was wrong

Rev 1 §5.2 claimed the verdict discretization was collapsing the ladder onto BST, citing r = 0.850 for the verdict against r = 0.306 for the margin.

**That comparison was invalid.** The 0.306 measured raw `mean_margin` — unsquashed, unweighted turns-difference. The score built from it is squashed and boss-weighted: a different quantity. Measured correctly, on the same population:

| basis, all cp19 candidate builds | r vs BST |
|---|---|
| verdict score | 0.850 |
| **margin score, as implemented** | **0.824** |

The discretization was worth ~0.03, not ~0.54. I over-read a number from a population that did not match the one the score is computed on, and recommended a change on that basis. The change was still worth making — resolution went 26 → 142, and it is the right primitive — but not for the reason I gave.

### 3.1 The actual cause

Splitting by role does not decorrelate either. Within-track correlation at checkpoint 19:

| track | n | r vs BST |
|---|---|---|
| physical | 627 | +0.864 |
| special | 394 | +0.893 |

Nature is **100% Adamant** within physical ceilings and **100% Modest** within special ones. The speed-tier rule generates Jolly and Timid correctly; the matrix then rejects them every time, because a damage race rewards the damage nature.

The structural point: **any score measuring "wins 1v1 damage races against boss rosters" is monotone in stats, so it will correlate with BST — and in a difficulty hack it arguably should.** Percentile-normalizing cannot help, since a rank-preserving transform leaves correlation intact.

Decorrelation must come from terms that are *not* monotone in stats. VISION §4.5 already specifies them: `role_fit = w_stat·S + w_tool·T + w_type·Y + w_fight·F`. The matrix produces essentially S and Y. **T (movepool tools) and the binary role gates do not exist yet — they are Phase 5.**

I3, I1 and I2 are all **Phase 5 gates**. Phase 4's own gate passes.

---

## 4. Phase 4 gate criteria

| Criterion | Result |
|---|---|
| Build count / cell count | 2.4M builds enumerated, 119,472 candidates, **1,562,981 cells** |
| Pruning rules stated | `builds.md` s1–s6, per-species trace in `INT_build_trace.json` |
| ≥10 calcs hand-reproduced, discrepancy rate reported | **600 cells, 0.3%, 18 move types** |
| Custom-layer additions / unsupported count | 464 species + 103 moves added; **0 unsupported at calc time** |

Reproducibility used an independent Python reimplementation of the Gen 8 formula; it does not call the calculator. Both discrepancies are checker limitations (Xerneas's Fairy Aura; one rounding-order case) — **zero attributable to the engine**.

---

## 5. Recommended next step

Build the Phase 5 role layer — gates first, then `role_fit` with all four components — and test I1–I5 and I7 there. The three things that should break BST monotonicity:

1. **Binary role gates.** A wall without recovery is not a wall at any bulk. Disqualification is not monotone in stats.
2. **The tool term T.** Movepool quality independent of stat totals — what lets a 480-BST utility species outrank a 600-BST one.
3. **VORP against replacement level, per role per checkpoint.** A strong species in a crowded role is worth less than a mediocre one in an empty role.

If I1 and I2 still fail after that, the honest reading is that the item and nature *rules* are too permissive, not the catalogue too small. Life Orb at 61% means the `allout` exploitability predicate admits nearly every attacking build — a rule to tighten, not a distribution to pad.

---

## 6. Gaps unchanged from rev 1

- **647 of 1,044 in-pool forms carry `earliest_cp = UNK`** — only 11 of 127 encounter maps have a gated world row
- **153 DYNAMIC rival slots excluded — 23% of all boss content**
- 9 target-custom boss forms absent from Phase 1 (`Infernape-Mega` ×7, `Luxray-Mega`, `Slaking-Mega`, `Empoleon-Mega-O/D`, `Torterra-Mega`, `Dusknoir-Mega`, `Dialga-Primal`, `Palkia-Primal`)
- Gift Pokémon and in-game trades absent from `02_world.tsv`
- 58 mega forms inherit base-form timing; stone placement unresolved
