# Matchups and Team Construction

The 1v1 matchup is the primitive. Team value is derived from it.

The reason is computability. Every candidate build against every Pokémon on every boss roster is a finite, exhaustively enumerable set — tens of thousands of cells, each one a measured number. Teams of six drawn from a pool of two hundred is a space of ~10¹² and cannot be enumerated at all. Building the team layer on top of a complete 1v1 matrix gives both layers, and keeps the heuristic layer honest because it rests on measured cells rather than on estimates of estimates.

Contents:
1. What a matrix cell contains
2. Computing the cell
3. Verdicts and margins
4. From cells to a boss threat sheet
5. The team layer
6. Simultaneous feasibility
7. What this model does not capture

---

## 1. What a matrix cell contains

One cell = one (build, opposing Pokémon, context) triple. Context is the milestone plus the field state — weather, terrain, hazards, screens — because a Fire attacker under the boss's own rain is a different object.

Each cell records:

| Field | Notes |
|---|---|
| `dmg_out_lo` / `dmg_out_hi` | Damage roll range dealt, as a fraction of the opponent's HP |
| `dmg_in_lo` / `dmg_in_hi` | Damage roll range taken from the opponent's best move |
| `speed_order` | Faster / slower / tied, after items, abilities, and field effects |
| `priority_edge` | Whether either side has usable priority that changes the order |
| `ttk_out` / `ttk_in` | Turns to KO in each direction, integer, from full HP |
| `outcome_full` | Verdict from full HP |
| `outcome_chipped` | Verdict from a realistic partial HP state |
| `margin` | How comfortable the verdict is (see §3) |
| `decided_by` | The one factor that flips the cell — a roll, a speed tie, a status, an ability |

`decided_by` is what makes the matrix explicable. A user asking "why does the system think this beats that" should get a one-line answer from this field, not a re-derivation.

---

## 2. Computing the cell

Use `mechanics.md` for the formulas, and **read them from the hack's own implementation where the analysis is sensitive to ordering** — multiplier order, burn application, and screen interactions differ between generations and between expansion versions.

Things that must be in the computation, in rough order of how often omitting them produces a wrong verdict:

1. **Ability effects, both sides.** Intimidate, Levitate, Regenerator, weather setters, damage-reduction abilities, and immunity abilities routinely flip cells outright.
2. **Held items, both sides.** Boss Pokémon in difficulty hacks carry items that matter — parse the trainer party data rather than assuming bare.
3. **Speed order after modifiers**, including Choice Scarf, Tailwind, paralysis, and Trick Room. A cell computed with the wrong speed order is wrong in both directions at once.
4. **Type effectiveness from the hack's own chart.** Never the vanilla chart. Chart edits are among the most common hack modifications.
5. **STAB, weather, terrain, and hazard chip.**
6. **Priority**, including ability-granted priority.
7. **Status and setup**, where they change the outcome rather than merely decorating it.

The **chipped state** matters more than it looks. In a real boss fight the player's Pokémon rarely arrives at full HP, and a build whose verdict collapses at 70% HP is materially worse than one that doesn't. Model a realistic partial state (a defensible default is entry after one round of hazard chip plus one average hit) and report both verdicts. Where they disagree, that disagreement *is* the advice.

---

## 3. Verdicts and margins

Emit a verdict plus a margin, never a bare binary. The margin is what turns a matrix into usable advice.

| Verdict | Meaning |
|---|---|
| **Wins** | Beats it across the full damage roll range, both orders |
| **Wins on rolls** | Beats it on most rolls; loses on unfavourable ones. Name the roll. |
| **Marginal** | The outcome is decided by something the player doesn't control — a speed tie, a secondary effect, a crit |
| **Loses on rolls** | Usually loses; wins on favourable ones |
| **Loses** | Loses across the range |
| **Loses hard** | Loses without meaningfully damaging it — worth flagging separately, because it identifies a threat with no answer |

"Wins on rolls" and "Marginal" are the cells a player most needs to see, because they're where preparation changes the outcome. Never round them into "Wins" for a cleaner-looking table.

---

## 4. From cells to a boss threat sheet

For each boss, the sheet the player actually wants:

- **The roster**, with each member's level, item, ability, and moves as parsed — Measured, from trainer party data.
- **Threats ranked** by how many current-pool builds lose to them and how badly. A Pokémon that beats 90% of the available pool is the fight's real problem, whatever its stat line says.
- **Answers per threat**, drawn from the current pool, with the verdict and the margin.
- **Threats with no answer.** This is the most valuable row on the sheet and the one most likely to be quietly omitted. If nothing in the pool beats it, say so and pivot to what mitigates it — chip, status, sacrifice, hazards.
- **The fight's shape**: does it force switches, does it have a setup sweeper, does it have a wall that stalls a whole team out. Fight shape is what determines whether a hazard setter or a phazer is worth a slot, and it comes from the roster's structure rather than from any individual cell.

---

## 5. The team layer

Team fit against a boss = **coverage of that boss's threat set, weighted by how badly each unanswered threat loses the fight.**

Search: beam search over teams of six drawn from the milestone's available pool. Full enumeration is impossible; beam search over a measured matrix is defensible if you report the beam width and the seed. Greedy construction alone is not enough — it locks in an early pick and never discovers complementary pairs.

A build's **team score** is a marginal contribution measure, not a standalone rating:

```
appearance_rate  = fraction of the top-N teams containing this build
marginal_value   = best_team_score − best_team_score_without_this_build
```

Report both. They diverge in an informative way: a high appearance rate with low marginal value means the build is a good generic pick with many substitutes; low appearance rate with high marginal value means it's the unique answer to something, which is exactly the specialist the framework exists to surface.

**This construction is what enforces recommendation diversity structurally.** Six copies of the same wallbreaker cover one threat six times and leave five uncovered, so the search selects complements without any diversity rule being imposed. If the output is still homogeneous after the team layer runs, the problem is upstream in build generation, not here.

---

## 6. Simultaneous feasibility

**A recommended team must be a team the player could actually assemble.** Check, at minimum:

- **Item copy counts.** Two members cannot both hold the game's single Choice Scarf. This is invariant I5 and it fails silently unless explicitly checked.
- **Species uniqueness**, unless the hack genuinely permits duplicates.
- **Availability at that milestone** for every member, including evolution feasibility under the level cap.
- **TM copy counts**, if the hack consumes TMs on use.
- **Mutually exclusive acquisitions** — a starter choice, a fossil choice, an in-game trade that costs a species, an either/or gift. These are one of the commonest sources of an infeasible "optimal" team, and they only appear if the availability parse recorded the exclusivity.

When a team fails feasibility, don't discard it silently. Report the best feasible team *and* the infeasible ideal with the constraint that separates them — "this team is one Choice Scarf short" is genuinely useful information about the run.

---

## 7. What this model does not capture

State these limitations wherever the matrix is published. They bound the claims honestly, and a user who knows the bounds trusts the rest more.

- **Switching and momentum.** The matrix is 1v1; real fights involve switch chains, and a build that loses every 1v1 can still earn its slot as a pivot. The team layer partially compensates; it doesn't fully.
- **Multi-turn resource attrition** across a whole fight — PP, healing item usage, the boss's own item usage.
- **AI behaviour.** Difficulty hacks often ship smarter trainer AI that switches, predicts, and preserves win conditions. The matrix assumes a fixed opposing move choice, which is optimistic for the player.
- **Player skill and item use.** A player who can afford to use healing items in-fight has a materially different matchup set.
- **RNG beyond damage rolls** — crits, secondary effect procs, accuracy checks. Model accuracy where a move is below ~90%; note the rest as unmodelled variance rather than pretending it's absent.

None of these is a reason to skip the matrix. All of them are reasons to publish margins rather than binaries.
