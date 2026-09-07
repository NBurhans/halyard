# Build Generation

A species is not the unit of analysis. A build is:

> **build = (ability, nature, held item, four moves, EV/level assumption)**

scored at a milestone. A species with two abilities, two plausible natures and two viable items is really eight different Pokémon, and the difference between the best and worst of them is often larger than the difference between two adjacent species.

This file covers how builds get generated, and the one rule that keeps the whole system from degenerating.

Contents:
1. The generation rule
2. Ability enumeration
3. Nature enumeration
4. Move slot filling
5. Held items and scarcity
6. Item dependence
7. EV/IV assumptions
8. Pruning — keeping the space computable
9. Anti-degeneracy failure signatures

---

## 1. The generation rule

**The species fills the build slots. The role never fills them uniformly.**

This is the single most important rule in the framework, and the reason the stated requirement — *no one item, nature, or moveset should ever be the dominant recommendation* — is achievable rather than aspirational.

The failure mode it prevents: deciding that Wallbreakers want Choice Band and Adamant, then handing Choice Band and Adamant to every Wallbreaker candidate. Every candidate shifts by the same multiplier, no ordering changes, and the output is a list where 60% of builds share an item. The item term did no work; it was decoration.

Generation is therefore *conditional on the stat spread and the ability set*:

| Species property | Consequence for generation |
|---|---|
| Atk ≫ SpA | No special build is generated at all. Not a low-scoring one — none. |
| SpA ≫ Atk | Symmetrically, no physical build. |
| Atk ≈ SpA, both above median | Mixed builds enter the space |
| Bottom-quartile Speed + high offense | Trick Room build generated; Brave/Quiet natures enter |
| Top-quartile Speed | Scarf and priority-revenge builds enter |
| Unevolved with real bulk | Eviolite build generated |
| No recovery move in pool | Assault Vest and Leftovers builds considered; "wall" gates likely fail |
| Recovery in pool | Defensive builds generated; passive-damage items rise |
| Poison typing | Black Sludge |
| Ability that wants status (Guts, Poison Heal, Quick Feet) | Flame Orb / Toxic Orb builds |
| Multi-hit move in pool | Loaded Dice |
| Stealth Rock weakness ≥ 2× | Heavy-Duty Boots build |

Treat that table as a starting vocabulary. The generalisation: **each item, nature and move slot has a precondition expressed in terms of the species' own numbers and toolkit.** If a slot value has no precondition, it will spread everywhere and it is a bug.

Derive the thresholds (`≫`, "above median", "top quartile") from the hack's own obtainable roster, not from absolute numbers. A 110 Attack is top-decile in one hack and unremarkable in another.

---

## 2. Ability enumeration

**Ability is part of the build, never averaged.** Averaging across ability slots is how Regenerator, Huge Power, and Prankster get diluted into invisibility.

Enumerate every ability the species can actually have, and check the hack's own configuration for whether hidden abilities are obtainable — many expansion hacks make them universally available, some gate them, some don't implement them. That's a source question, not a guess. If a hidden ability is unobtainable, its builds don't exist.

Where an ability is the whole reason a build works, say so in the build's stated reasoning. "Best build of X" that silently depends on an ability slot the player can't roll is a wrong answer.

---

## 3. Nature enumeration

Enumerate and score natures; don't assume the "obviously correct" one. The assumption is usually right for pure attackers and usually wrong everywhere else — for walls, for Trick Room builds, for anything with a speed tier that only matters at one threshold.

Score natures against the milestone's actual opposition, because nature value is threshold-shaped rather than linear:

- A +Speed nature is worth a great deal if it crosses a boss Pokémon's speed tier and nearly nothing if it doesn't. Compute the crossing, don't assume the boost helps.
- A −Attack nature costs nothing on a pure special attacker but changes confusion and Foul Play damage; note it only where it's material.
- A defensive nature's value is turns survived against that boss's win conditions, which is a step function around the roll that would otherwise KO.

The invariant on nature spread is **I2 ≤ 20%**. If one nature is on more than a fifth of recommended builds, either the speed-tier computation isn't running or natures are being applied by role rather than by species.

---

## 4. Move slot filling

Four slots, filled from the species' *legal and available* pool at that milestone. Availability, not legality, is the binding constraint — see `availability.md`.

The pool sources:

- **Level-up**, gated by the level the species is actually at that milestone. A move learned at 48 is not available under a level-40 cap.
- **TM/HM**, gated by whether that TM is obtainable by that milestone *and* by copy count if the hack consumes TMs. Modern expansion builds usually make TMs reusable; check, because it changes everything about scarcity.
- **Egg moves**, gated by whether the parent chain is obtainable and by whether breeding is available yet.
- **Tutors**, where they exist. Some hacks have none and hand out TMs from an NPC instead — verify rather than assuming a tutor list exists.

Slot-filling principles:

- **Obligatory STAB is not a signal.** If every Fire type runs the same Fire move because it's the only good one, that's the hack's move table, not a modelling failure. Report obligatory STAB fillers separately from the I7 move-diversity check, or I7 fires on something you can't fix.
- **Coverage is measured against the milestone's boss rosters**, not against the whole type chart. A coverage move that hits nothing on the next three bosses is a wasted slot regardless of how good it looks in the abstract.
- **A utility slot competes with a coverage slot.** Score the four-move set as a set, not as four independent picks — the marginal value of a third attacking move is often lower than a first status move, and additive slot scoring never discovers that.

---

## 5. Held items and scarcity

Items are gated twice.

**Gate one — can the species exploit it?** Eviolite needs an unevolved species. Black Sludge needs a Poison type. Toxic Orb needs an ability that wants status. Assault Vest needs a species with no recovery to lose. Throat Spray needs a sound move. Booster Energy needs a Paradox ability. An item that fails its precondition doesn't get generated.

**Gate two — can the player rely on having it?** Item supply in difficulty hacks is sharply two-tiered, and the tiers behave completely differently:

- **Open items** — purchasable, or present in ≥ 3 copies. These can be assumed. Leftovers at three copies, a bulk dispenser handing out ten Flame Orbs, anything in a mart.
- **Singleton items** — one copy in the entire game. Life Orb, the Choice items, Focus Sash, Eviolite and Assault Vest are commonly singletons. Exactly one team member can hold each, for the whole run.

**Score the build with the best *open* item.** Track the best item overall separately. Never let a build's headline score quietly rest on a singleton — that repeats, at the item layer, exactly the mistake that ungated TMs make at the move layer.

Copy counts are **literal and Measured**. A script that grants ten copies grants ten. Parse them from placement data; do not infer scarcity from how rare the item feels in other games.

---

## 6. Item dependence

For each build, publish:

```
item_dependence = score(best_item_overall) − score(best_open_item)
```

This is one of the most decision-relevant numbers the framework produces, because it converts an abstract ranking into a budget. A build with item dependence 0.00 can be fielded without limit. A build with high item dependence is competing with every other high-dependence build for the same single item.

The aggregate form is worth reporting per role: **the open supply of a role** — how many members of that role can be simultaneously equipped with a reliable item. A role whose open supply is zero has no reliable item at all, and the practical consequence is a hard cap on how many of them the player can field well. That is a headline finding, not a footnote.

---

## 7. EV/IV assumptions

State the assumption explicitly and hold it constant across every build, or comparisons are meaningless.

| Model | Argument for | Argument against |
|---|---|---|
| Flat neutral (IV 31, EV 0) | Cleanest; isolates species differences | Understates trainable species and any hack with generous EV items |
| Player-achievable | Most realistic | Requires a judgement about what "achievable" means, which drifts |
| Fully optimised (252/252) | Matches competitive intuition | Wrong for most single-playthrough runs |

Default to **flat neutral, stated**, and offer the alternative when the user's run makes it wrong. If the hack ships EV-training facilities early, that's a reason to revisit — note it rather than silently switching.

Level assumption follows the milestone's level cap where one exists, and the realistic party level otherwise. Compute HP at the actual level, not at 50 — the flat `+ Level + 10` term compresses HP differences at low levels, and early-game analysis done at level 50 misrepresents which walls actually hold.

---

## 8. Pruning — keeping the space computable

Full enumeration is (abilities × natures × items × move combinations). The move-combination term explodes first. Practical pruning, in order of what to try:

1. **Precondition gates first.** They're free and they cut hardest — most items and half the natures never generate for a given species.
2. **Dominated-set elimination on moves.** Within a species' pool, a move strictly dominated by another (same type, same category, lower power, no extra effect, no accuracy advantage) never appears in an optimal set. Remove it before combining.
3. **Cap coverage slots.** Enumerate the best k coverage options by damage against the milestone's actual boss rosters, then combine, rather than combining all pool moves.
4. **Score the STAB slot greedily, the rest combinatorially.** The best STAB is nearly always determined; the interesting choices are slots 2–4.

Report how much you pruned. "Enumerated 1,240 builds from a raw space of ~40,000 after gates and dominated-move elimination" is auditable; a bare build count is not.

---

## 9. Anti-degeneracy failure signatures

When the invariants in `invariants.md` fail, the cause is nearly always one of these. Check them in this order:

| Symptom | Likely cause |
|---|---|
| One item on >25% of builds (I1 fails) | Item applied by role instead of by species precondition, or the scarcity gate isn't running |
| One nature on >20% (I2 fails) | Speed-tier crossing isn't computed; natures scored linearly instead of at thresholds |
| BST correlation >0.6 (I3 fails) | Gates aren't biting; stat magnitude is weighted too heavily relative to toolkit and typing |
| BST correlation <0.3 | Gates are mis-specified and disqualifying good species, or scoring is dominated by noise |
| A role has <3 viable species (I4 fails) | Gates reference a move or ability that barely exists in this hack — verify against the hack's move table |
| Recommended team not equippable (I5 fails) | Singleton items being credited to multiple builds; the open-item rule isn't applied |
| Stat perturbation changes nothing (I6 fails) | Build generation is reading the role, not the species. This is the serious one. |
| One move on >30% (I7 fails) | Either obligatory STAB isn't being excluded and reported separately, or the coverage pool is too narrowly pruned |

I6 deserves the most attention. If scrambling a species' base stats leaves its recommended build unchanged, the generator is not reading the spread, and every claim about builds being species-specific is false regardless of how good the output looks.
