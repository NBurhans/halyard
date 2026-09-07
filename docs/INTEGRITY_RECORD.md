# Consolidated integrity record

Every defect found across the build, with its consequence and resolution. All
were silent — none raised an error; each was caught by a targeted assertion or
by a result that failed a smell test.

| # | Defect | Consequence | Resolution |
|---|---|---|---|
| 1 | Species tables encode maps as `MAP_ROUTE101`, world tables as `Route101` | 0 of 127 encounter maps joined; every wild species fell through to "no known gate" | Normalised both sides |
| 2 | `species_name` is the base name for every form | Boss rosters resolved every regional and mega to its **base form** — Alolan Ninetales scored as a Fire type | Constant-keyed resolver; slot resolution 73% to 95.8% |
| 3 | Data layer key derived from `form_type` | **81 collisions.** Deoxys-Attack/Defense/Speed and ~78 others overwrote each other; 344 of 1,523 rows lost | Key derived from the constant; layer 1,179 to 1,523. Matrix fully re-run |
| 4 | Air Balloon predicate was `lambda c: True` | 25% item share on a meaningless rule | Gated to Ground-weak forms |
| 5 | Item catalogue hand-written, 13 items | Leftovers and Life Orb took 90% of ceilings; 18 type-boost items and 18 resist berries never entered the generator | Derived from hold-effect codes; 182 items |
| 6 | Ceiling picker ignored the scarcity rule `builds.md` already stated | Life Orb on 55% of published ceilings | Reliable-item preference enforced; 11,756 ceilings demoted; I1 passed |
| 7 | Candidates bucketed by item class only | Jolly and Timid reached the matrix **zero times** despite being generated | 2x2 factorial over item class and nature |
| 8 | Cells with zero floor occupants missed the `undefined` set | Fell through to a silent replacement of 0.0; Slakoth (BST 280) ranked S+ physical wall | Explicit undefined marking; S+ rows 1,193 to 622 |
| 9 | Replacement drawn only from floors whose *primary* role matched | Baseline too thin for tool-gated roles | Read each floor's fit in that specific role |
| 10 | Species and move parsers disagree on three move constants | 106 level-up references silently dropped from movepools | Alias map registered; 167 published ceilings affected |
| 11 | Source and walkthrough map gates merged with "source wins" | Petalburg City dated to checkpoint 10 when reachable at 1 | Item gates bound obtainability, not reachability; take the earlier |

## Process failures worth recording

- **Mixed-vintage data.** A single-checkpoint test run overwrote the candidate
  file; matrix batches for checkpoints 2-19 then matched zero candidates, wrote
  nothing, and left the previous run's files in place. Invariant results were
  reported on one current checkpoint and eighteen stale ones. A consistency
  check now runs first and blocks the pipeline.
- **A test that could not fail.** The first I6 run returned exactly 0.0%,
  because both the true and perturbed species tables were written to the same
  temp path — the test compared the perturbed file against itself.
- **A diagnosis measured on the wrong population.** The claim that verdict
  discretization caused the BST collapse rested on comparing two different
  quantities. Measured correctly the difference was 0.03, not 0.54.
- **An impact estimate that overstated itself.** The move-alias defect was
  argued as flipping orientation verdicts, from a level-up-only comparison. With
  teachable moves included — which the generator always used — no verdict
  flipped. True impact was 167 ceilings, 81% of them in the bottom two tiers.
