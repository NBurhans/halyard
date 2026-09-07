# Manifest

Raw file URLs follow the pattern:

```
https://raw.githubusercontent.com/<username>/halyard/main/<path>
```

`CHECKSUMS.txt` carries a sha256 and byte count for every file.

## data/

| file | rows | bytes | what it is |
|---|---:|---:|---|
| `01_species.tsv` | 1,523 | 1,786,312 | species-form master: identity, typing, stats, movepools, breeding, availability |
| `01b_moves.tsv` | 938 | 166,062 | the move table as the target defines it, not as the base game defines it |
| `01c_availability.tsv` | 1,523 | 99,537 | earliest checkpoint each form can be in hand, with confidence and reason |
| `01d_map_gates.tsv` | 127 | 7,877 | which checkpoint opens each encounter map, and where that claim came from |
| `02_world.tsv` | 1,128 | 201,743 | items, TMs, vendors, placements, literal quantities |
| `03_trainers.tsv` | 859 | 403,558 | trainers and rosters, encoded per slot |
| `03b_checkpoints.tsv` | 19 | 744 | progression gates and level caps |
| `04a_candidates.tsv.gz` | 152,865 | 1,779,091 | the builds the matrix actually scored |
| `04b_matchup_summary.tsv` | 19,665 | 7,068,605 | per (species, checkpoint) floor and ceiling |
| `05_roles.tsv.gz` | 152,865 | 3,821,012 | role fits with S, T, Y and F reported separately |
| `05_valuation.tsv` | 19,215 | 6,189,726 | **the headline** — VORP, tier, build, availability |
| `checkpoints.yaml` | 19 | — | progression gates, level caps, boss set |
| `mechanics.yaml` | — | — | pinned generation, engine binding, QoL switches, move aliases |
| `item_catalog.json` | 182 items | 29,117 | held items derived from world hold-effect codes |
| `typechart.json` | 19 types | 4,147 | type effectiveness, from the mechanics engine |

### Not committed

The raw per-checkpoint matrices (`04_matchups_cp1..19.tsv`, 4,248,276 cells, ~1.5 GB)
and the full enumerated build set (`04_builds.tsv`, 429 MB). Both regenerate from
`pipeline/`. See `.gitignore`.

## Conventions

| convention | format |
|---|---|
| list | comma-separated |
| key:value | `33:1,45:3` |
| grouped records | pipe-separated records, colon-separated fields |
| not applicable | `NA` |
| empty but valid | `NONE` |
| unknown, absent from source | `UNK` |

`NA`, `NONE` and `UNK` mean three different things and never collapse. `NONE` is a
measurement. `UNK` is a gap. `NA` is a category error.

Every published field carries a confidence tier. The tier says **how we know**, never
**whether we know** — gaps are carried by `UNK` and the integrity log.

| tier | meaning | count in the ladder |
|---|---:|
| Measured | parsed directly from source | 1,303 |
| Derived | computed from measured inputs by a stated formula | 7,399 |
| Inferred | reasoned from context | 1,915 |
| Asserted | from a secondary source without source confirmation | 8,598 |

## pipeline/

Numbered in dependency order. Steps 01–04 need the target's source tree; their output
is already in `data/`, so a rebuild can start at 05.

| script | produces |
|---|---|
| `01_parse_species.py` | `01_species.tsv` |
| `02_parse_moves.py` | `01b_moves.tsv` |
| `03_parse_world.py` | `02_world.tsv` |
| `04_parse_trainers.py` | `03_trainers.tsv` |
| `05_map_gates.py` | `01d_map_gates.tsv` |
| `06_availability.py` | `01c_availability.tsv` |
| `07_item_catalog.py` | `item_catalog.json` |
| `08_build_data_layer.js` | custom calc data layer |
| `09_build_generator.py` | `04a_candidates.tsv` |
| `10_matrix.js` | `04_matchups_cp*.tsv` |
| `11_summarize.py` | `04b_matchup_summary.tsv` |
| `12_roles.py` | `05_roles.tsv` |
| `13_valuation.py` | `05_valuation.tsv` |

Supporting modules, imported rather than run: `resolve.py` (form-aware name
resolution), `species_key.py` (unique form keys), `sable_gen.js` and
`sable_abilities.js` (calc bindings).

## tools/

| file | what it does |
|---|---|
| `verify_calcs.py` | reimplements the damage formula independently and compares |
| `audit_integrity.py` | round-trip, cross-phase referential integrity, UNK sweep |
| `sensitivity_i6.py` | perturbs base stats and re-runs generation |
| `skill/` | the analysis skill and its nine reference documents |

## docs/

| file | what it covers |
|---|---|
| `INTEGRITY_RECORD.md` | all eleven defects, cause and resolution, plus four process failures |
| `PHASE4_GATE.md` | build generation and the matchup matrix |
| `PHASE5_GATE.md` | roles, VORP, tiers, the invariant results |
| `PHASE6_GATE.md` | round-trip, referential integrity, sensitivity |
| `PHASE6_REGEN.md` | the regeneration pass after the move-alias fix |
| `PHASE7_NOTES.md` | the companion app |
| `AVAILABILITY_NOTE.md` | how progression ordering closed the timing gap |
| `PUBLISHING.md` | how to put the survey on GitHub Pages |
| `VISION.md` | scope, classification, naming policy |
| `RUNBOOK.md` | the working prompt template, target block empty |
| `CONTRIBUTING.md` | the four rules, and how the silent defects were caught |

## app/

| file | what it is |
|---|---|
| `app_template.html` | the survey with a `__PAYLOAD__` placeholder |
| `build_index.py` | builds the payload from `data/` and writes `index.html` |
