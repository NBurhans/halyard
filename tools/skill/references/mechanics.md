# Mechanics and Formulas

Formulas are given for Gen 3, the base for the overwhelming majority of ROM hacks. Hacks built on the base decomp often backport later-generation mechanics — **verify against the hack's own source before applying any of these**, and mark results as *Inferred* whenever a formula is assumed rather than confirmed from the data.

---

## 1. Stat calculation

Non-HP stats:

```
Stat = floor( ( floor( (2*Base + IV + floor(EV/4)) * Level / 100 ) + 5 ) * NatureMod )
```

HP:

```
HP = floor( (2*Base + IV + floor(EV/4)) * Level / 100 ) + Level + 10
```

NatureMod is 1.1, 1.0, or 0.9. Shedinja is hardcoded to 1 HP.

For cross-species comparison at a fixed level, hold IV=31, EV=0, Nature=1.0 and say so. Level 50 and level 100 rank species identically for non-HP stats but not for HP, because of the flat `+ Level + 10` term — at low levels HP differences compress. If the analysis concerns early-game balance, compute at the actual level, not level 50.

---

## 2. Damage

```
Base = floor( floor( floor(2*Level/5 + 2) * Power * A / 50 ) / D ) + 2
Damage = Base * STAB * TypeEffectiveness * Random
```

- `A`/`D` are Attack/Defense for physical moves, Sp.Atk/Sp.Def for special.
- STAB = 1.5 when the move's type matches one of the user's types.
- Random is uniform over 85/100 … 100/100.
- Other multipliers (weather, items, Burn halving physical Attack, screens) apply in a defined order; if the analysis is sensitive to that order, consult the hack's `CalculateBaseDamage` implementation directly.

**Gen 3 physical/special split is by type, not by move.** This matters constantly in hack analysis:

- **Physical types:** Normal, Fighting, Flying, Poison, Ground, Rock, Bug, Ghost, Steel
- **Special types:** Fire, Water, Grass, Electric, Psychic, Ice, Dragon, Dark

A hack may have moved to the Gen 4 per-move split. Check for a `.split` or `.category` field in the move table — its presence is the tell.

---

## 3. Type effectiveness

Effectiveness is the product across the defender's types: 0, 0.25, 0.5, 1, 2, or 4. Gen 3 stores the chart as a flat list of `(attackType, defendType, multiplier)` triples with multipliers encoded as 0/5/10/20 (i.e. ×10). Immunities are handled separately from the main table in some builds.

**Load the hack's chart.** Type chart edits are one of the most common hack modifications, and every coverage claim depends on it.

Useful derived metrics:
- **Offensive coverage:** the count of defensive type combinations (of the ~171 real ones in the hack's roster) hit for ≥2× by at least one move in a given movepool.
- **Defensive profile:** counts of 4×, 2×, 1×, 0.5×, 0.25×, 0× incoming per type. Report weaknesses and resistances as counts, not lists, when comparing many species.

---

## 4. Catch rate

```
a = floor( floor( (3*HPmax - 2*HPcurrent) * CatchRate * BallBonus / (3*HPmax) ) * StatusBonus )
```

If `a ≥ 255`, the catch succeeds. Otherwise:

```
b = 1048560 / sqrt( sqrt( 16711680 / a ) )
```

and four shake checks each succeed with probability `b / 65536`. Overall capture probability is `(b/65536)^4`.

StatusBonus: 2 for sleep or freeze, 1.5 for paralysis, poison, or burn, 1 otherwise. For comparing catch difficulty across a roster, a full-HP, no-status, standard-ball baseline is the fair comparison — state the assumption.

---

## 5. Experience and growth

EXP from a defeated Pokémon:

```
EXP = floor( BaseExpYield * FaintedLevel / 7 ) / Participants
```

Multiply by 1.5 for trainer battles and 1.5 for traded Pokémon (Gen 3 applies Lucky Egg only in later gens).

Total EXP to reach level `n`:

| Growth rate | Formula |
|---|---|
| Fast | `4n³/5` |
| Medium Fast | `n³` |
| Medium Slow | `6n³/5 − 15n² + 100n − 140` |
| Slow | `5n³/4` |
| Erratic / Fluctuating | Piecewise; implement from the decomp table rather than a closed form |

Growth rate is a real balance lever hack authors adjust. When analyzing progression pacing, compare EXP-to-level-50 across the roster, not just base stats — a 600 BST species on Slow growth is a different design object than the same stats on Medium Fast.

---

## 6. Encounter slots

Gen 3 default slot probabilities:

| Method | Slot rates (%) |
|---|---|
| Land (12 slots) | 20, 20, 10, 10, 10, 10, 5, 5, 4, 4, 1, 1 |
| Surfing (5 slots) | 60, 30, 5, 4, 1 |
| Old Rod (2) | 70, 30 |
| Good Rod (3) | 60, 20, 20 |
| Super Rod (5) | 40, 40, 15, 4, 1 |

Rock Smash and Headbutt tables vary by base game. These are *slot* probabilities, conditional on an encounter triggering; the encounter rate itself is a separate per-area value.

When a species occupies multiple slots in one table, sum its slot probabilities — a species in slots 1 and 2 has 40% presence, not 20%. This is a frequent source of undercounted availability.

For "how long to find X" questions: expected encounters to first sighting is `1/p`; the probability of at least one sighting in `k` encounters is `1 − (1−p)^k`.

---

## 7. Derived metrics worth computing

Define these explicitly in the workbook so the user can adjust them:

- **BST** — sum of six base stats. Crude but the standard axis.
- **Physical bulk** = `HP × Def`; **Special bulk** = `HP × SpD`. Products, not sums, because damage scales inversely with defense.
- **Offensive index** — for Gen 3, `max(Atk, SpA)` weighted by whether the species' STAB types fall on the matching side of the type split. A species with high Attack and only special-type STAB is misrepresented by raw Attack.
- **Speed tier** — rank rather than raw value; what matters is what a species outspeeds within the hack's actual roster and trainer parties.
- **Availability level** — the earliest level at which the species is obtainable, from encounter and gift data. Pair with BST to find power-vs-progression outliers.
- **Movepool depth** — count of distinct damaging types available, and separately the count of moves with power ≥ 80. Raw learnset length overstates weak movepools.

---

## 8. Multiplier order, hazards and speed — what the matrix needs

Sections 1–8 give the formulas. The matchup matrix in `matchups.md` needs the parts the formulas leave implicit, and these are where a cell most often comes out wrong.

### Multiplier order

Damage multipliers do not commute under integer truncation. Applying burn after a screen gives a different integer than applying it before, and a cell decided by one HP is decided by the order. Where the analysis is sensitive to it — and near-KO cells always are — **read the hack's own damage implementation** rather than applying multipliers in whatever order is convenient. The usual chain is: base damage → spread → weather → crit → random → STAB → type → burn → other (screens, items, abilities), but expansion versions reorder pieces of it.

### Hazards

Chip on entry, applied before the first move:

| Hazard | Chip |
|---|---|
| Stealth Rock | Fraction of max HP scaled by the Rock type effectiveness against the entrant (1/32 at 0.25× up to 1/2 at 4×) |
| Spikes | 1/8, 1/6, 1/4 of max HP at 1, 2, 3 layers; grounded targets only |
| Toxic Spikes | Poison or badly poison on entry; absorbed by a grounded Poison type |
| Sticky Web | Speed drop on entry, grounded targets only — changes speed order, not HP |

Heavy-Duty Boots and Magic Guard negate the relevant parts; check whether the hack implements them before modelling either. Hazard chip is what makes the "chipped state" verdict differ from the full-HP verdict, so a matrix computed without hazards understates how often a build actually loses.

### Speed order

Compute in this order, and stop at the first thing that decides it:

1. Priority bracket, including ability-granted priority (Prankster, Gale Wings) and whether the target's type blocks it (Dark versus Prankster status, in hacks that implement it)
2. Trick Room, which inverts the comparison
3. Effective Speed = base Speed stat × item × ability × status × field
   - Choice Scarf ×1.5, Iron Ball and similar ×0.5
   - Paralysis: ×0.5 in Gen 7+, ×0.25 before — a config-dependent value, check it
   - Tailwind ×2; weather-speed abilities (Swift Swim, Chlorophyll, Sand Rush) ×2
4. Speed ties — resolved randomly, so a tie is a **Marginal** verdict, never a win

A cell computed with the wrong speed order is wrong in both directions at once, which is why speed is worth verifying before damage.

### Turns to KO

```
ttk = ceil( target_HP / damage_per_turn )
```

Compute it at both roll ends, not at the average. `ttk_lo` and `ttk_hi` differing by one turn is exactly the "wins on rolls" case that a mean would hide. Fold in per-turn residuals — Leftovers recovery, poison or burn damage, sand or hail chip, Rocky Helmet and Rough Skin contact damage — because over three or four turns they routinely change the integer.

### Accuracy

Model accuracy explicitly for moves below roughly 90%. A 4-turn KO on an 80% accurate move fails outright about a third of the time, and calling that a win is the kind of confident wrong answer that costs a nuzlocke run. Above 90%, note it as unmodelled variance rather than pretending it's absent.

---

## 9. Reading the mechanics config before applying any of this

Expansion-based hacks backport later-generation mechanics selectively, per switch. Before applying a single formula from this file, parse `include/config/*.h` and record what it says. The switches that most often change an answer:

| Switch | Changes |
|---|---|
| Physical/special split | Every offensive role score. Presence of a `.category` or `.split` field on moves is the tell. |
| Critical hit rate and multiplier | Damage variance; Gen 6+ crits are ×1.5, earlier are ×2 |
| Burn damage fraction and Attack reduction | Wall viability |
| Paralysis speed multiplier | Speed order in a large fraction of cells |
| Reusable TMs | Whether TM copy count is a real constraint |
| Hidden ability obtainability | Which builds exist at all |
| Trade evolutions patched | Which species are in the pool |
| Terrain and weather durations, extender items | Weather and terrain setter role scores |
| Exp share behaviour and level cap | Party levels at every milestone |

Record the parsed config with the analysis, as a Measured artifact. When a later result looks surprising, this table is the first place to check, and reconstructing it after the fact is far more work than saving it.

---

## 10. When the hack disagrees with these formulas

If computed values contradict something observable in the data (e.g. an `expYield` field that produces absurd level curves), stop and check the source implementation before publishing the number. Report the discrepancy as *Unresolved* rather than picking whichever formula makes the output look reasonable.
