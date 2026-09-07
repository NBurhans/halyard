# Integrity Checks

Failure modes specific to ROM hack data, ordered roughly by how often they silently corrupt an analysis. Run these before drawing conclusions; report findings in the Data Integrity Log regardless of whether they change the headline result.

---

## A. Identity and indexing

### A1. Internal index vs. Pokédex number
The most damaging and most common error. Gen 3 stores species in an internal order where the Hoenn Pokémon occupy indices 277+ and the National Dex order is a separate mapping. Randomizer and editor exports disagree about which they report. Symptoms: type distributions that look wrong, a "Bulbasaur" with 100 base Speed, evolution chains pointing at unrelated species.

**Check:** pick 5 unmodified-looking species and verify name↔stat pairs against a known baseline. If a hack claims to be unmodified for early-route Pokémon and your parse says otherwise, suspect the mapping before suspecting the hack.

### A2. Duplicate IDs
Two rows sharing a species/move/item ID. Usually an editor writing over a slot without clearing the old row, or a merge artifact in a design spreadsheet. Silently doubles that entry's weight in every aggregate.

### A3. Index gaps
Missing IDs in an otherwise contiguous range. Sometimes intentional (removed content), sometimes a parse failure. Distinguish by checking whether the source file has the entry at all.

### A4. Off-by-one on the zero slot
Many tables reserve index 0 for a null/dummy entry. Including it drags every mean toward zero. Excluding it when the hack actually uses slot 0 loses a real species. Check what's in slot 0 before deciding.

---

## B. Placeholder and dummy content

### B1. Unused species slots
Gen 3 has a block of unused slots (the `SPECIES_UNOWN_B` through `SPECIES_EGG` region, roughly indices 252–276 in the base game) filled with dummy data — often all-stat-1 or all-stat-0 entries named `??????`, `-----`, `MISSINGNO`, or `DUMMY`. These are not design decisions. Including them in a BST distribution produces a phantom low-tier cluster.

**Check:** flag any row where all six base stats are identical, or where the name matches a placeholder pattern, or where BST is implausibly low (<100) or the catch rate is 0 alongside zero stats.

### B2. Partially implemented custom species
Hacks that add species often leave some fields unfilled. A row with real stats but `TYPE_NONE`, an empty learnset, or ability slot 0 is likely work-in-progress. Report these separately from finished content — a "the hack has 14 species with no moves" finding is usually a bug report the author wants.

### B3. Sentinel values
`255`, `0`, `-1`, and `65535` often mean "none" rather than a real quantity. A catch rate of 0 means uncatchable, not "very hard." Confirm the sentinel convention per column before computing statistics on it.

---

## C. Referential integrity

Cross-file checks. Each of these is a real bug in the hack if it fires, and worth surfacing prominently.

| Check | Detects |
|---|---|
| Learnset move IDs ∈ move table | Moves taught that don't exist |
| Evolution target ∈ species table | Evolutions into nothing (freeze/crash risk) |
| Encounter species ∈ species table | Unimplemented species in the wild |
| Trainer party species ∈ species table | Broken trainer battles |
| Trainer party moves ∈ that species' legal pool | Illegal movesets (may be intentional) |
| TM compatibility flags ↔ TM list length | Flags for TMs beyond the defined set |
| Held item IDs ∈ item table | Phantom items |
| Ability IDs ∈ ability table | Undefined abilities |
| Egg group ↔ evolution family consistency | Breeding chain breaks |

Report orphans by name and count. "3 orphan move references in learnsets: species #0412 references MOVE_0891 (undefined) at levels 12, 24, 39" is actionable; "some references are broken" is not.

---

## D. Value range violations

- **Base stats:** legal range 1–255. Values above 255 will wrap when written to the ROM. A 300 base Attack in a design spreadsheet is a bug the author needs to know about before it becomes a 44.
- **BST arithmetic:** if the source has both individual stats and a total column, verify the total equals the sum. Mismatches mean a stale total after an edit.
- **Catch rate:** 0–255. **EV yields:** 0–3 per stat, and Gen 3 caps total EV yield at 255 per stat over a run.
- **Levels:** encounter and trainer levels should be 1–100. Level 0 entries are parse artifacts.
- **Encounter rates:** slot probabilities per table should sum to 100% (or to the platform's slot count). A table summing to 97% or 103% is either a rounding display or a real bug.
- **Type IDs:** must exist in the type chart. Hacks that add types (Fairy backported to Gen 3, Sound, Light) shift every downstream ID.

---

## E. Semantic and design-level inconsistencies

These aren't corruption — they're places where the data is internally valid but tells a confusing story. Report as observations, not errors.

- **Evolution level exceeds availability.** A species evolving at level 55 that only appears in a level 8 wild encounter and nowhere later.
- **Dead-end stat lines.** A species whose only high stat is in an attack category with no usable moves in its pool (a physical attacker with a special-only learnset). In Gen 3 the physical/special split is by *type*, not by move, so this is a real and frequent problem in hacks that changed movesets without changing types.
- **Unobtainable content.** Species in the data that appear in no encounter table, no trainer party, no gift, no egg. Distinguish "designed for a later update" from "the author forgot to place it."
- **Type chart edits with downstream effects.** If the hack modified type effectiveness, every coverage and matchup analysis must use the hack's chart. Load it; never assume the vanilla chart.
- **Difficulty curve inversions.** Trainer party average level or BST that dips between sequential story milestones.


---

## F. Statistical hygiene

- **Report n on every statistic.** Species counts vary between hacks; a claim about "Water types" over n=19 needs that n visible.
- **Bimodality.** BST distributions in hacks are frequently bimodal (a designed tier and a legendary tier). A single mean across both is misleading — check the shape before reporting central tendency.
- **Selection effects in encounter data.** Rare-slot species are undersampled in play but equally weighted in a raw table average. Decide and state whether the analysis weights by encounter probability.
- **Small-sample correlations.** With fewer than ~30 observations, report the scatter alongside any correlation coefficient and avoid p-values entirely unless the user asks.

---

## G. Availability and gating integrity

These checks exist because the availability model in `availability.md` is derived from several separate parses, and a silent gap in any one of them produces a ranking that looks fine and recommends things the player cannot obtain. Run all of them before publishing any milestone-gated output.

### G1. Species with no arrival milestone
Every obtainable species should resolve to an arrival milestone. Species that don't fall into three groups, and the difference matters: unobtainable in this hack (a finding for the author), obtainable through a channel you didn't parse (a bug in your ingest), or gated behind something the milestone graph doesn't model. Report the count and name a sample before assuming the first.

### G2. Item placements found by only one source
Cross-tabulate item locations by source — ground (`map.json`), script, mart, reward. An item class that appears in exactly one source is suspicious: if every TM you found came from scripts and none from `map.json`, you missed the ground items. Report the by-source counts, not just the total.

### G3. Copy counts of 1 across the board
If every item in your table has exactly one copy, you parsed presence rather than count — bulk `giveitemfast ITEM_X, 10` calls were read as single grants. The signature is a suspiciously flat supply distribution in a hack that clearly has an item tier.

### G4. TMs referenced in learnsets but never placed
Teachable moves with no obtainable TM. Some are genuine (the hack defines compatibility for a TM it never places); most are a parse gap. Distinguish by grepping the item constant across the whole repo before calling it unobtainable.

### G5. Level cap versus level-up learnsets
A milestone whose level cap sits below the level at which a species learns the move a role gate depends on. Not an error — but if a species passes a gate at a milestone where its gating move isn't learnable yet, the cap isn't being applied.

### G6. Evolutions above the cap
Species scored in an evolved form that the level cap makes impossible at that milestone. Check the evolution level against the cap for every species in every milestone's pool. This one silently inflates early-game rankings.

### G7. Infeasible evolution methods
Trade evolutions in a single-player run, item evolutions whose item isn't obtainable yet, friendship evolutions with no mechanism. Check the config headers first — expansion hacks very often patch trade evolutions to a level or item method, and assuming they didn't removes real species from the pool.

### G8. Encounter slot rates that don't sum
Slot probabilities per table should sum to 100% or to the platform's slot count. A table summing to 97% is either a rounding display or a real bug; either way, note which.

### G9. Mutually exclusive acquisitions not recorded
Starters, fossils, either/or gifts, and trades that cost a species. If the availability table records these as independently obtainable, team feasibility (invariant I5) cannot catch an impossible recommendation. Check that at least the starter set is flagged exclusive — if it isn't, the exclusivity parse isn't running at all.

### G10. Milestone ordering unverified
The ordering is usually Inferred. Confirm it against the hack's own walkthrough or the user, and record which milestones are Measured (anchored to a cap or flag) versus Inferred. An ordering error shifts every gate downstream of it.

---

## Writing the Data Integrity Log

Structure it as a table with columns: Check, Result, Severity, Affected rows, Effect on analysis. Severity tiers:

- **Blocking** — the analysis cannot proceed correctly until resolved (e.g. ambiguous ID mapping).
- **Material** — the analysis proceeds but a stated number changes if resolved.
- **Cosmetic** — noted for the author's benefit, no effect on findings.

Include passed checks. A log that only lists problems doesn't tell the user what was verified.
