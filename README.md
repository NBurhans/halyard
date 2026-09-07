# halyard

A data-driven planning framework for turn-based RPG progression.

HALYARD answers three questions at any point in a playthrough: what should I be
building, what is it good against, and when can I actually get it. It answers them
from the target's own source data rather than from community consensus or from what
a language model remembers.

Underneath it computes an exhaustive one-on-one matchup matrix — **4,248,276 cells**
for the current target. On the surface it publishes replacement-relative value, per
role, with a floor, a ceiling, and the cost of getting from one to the other.

**[Open the survey →](https://YOUR_GITHUB_USERNAME.github.io/halyard/)**

## What is here

| | |
|---|---|
| **`index.html`** | The survey — dex, rankings, roles, bosses, routes. Self-contained, opens offline |
| **`data/`** | Analysis output as TSVs. `05_valuation.tsv` is the headline: 19,215 scored rows with VORP, roles and tiers |
| **`pipeline/`** | Every script, numbered in dependency order. The whole thing rebuilds from `data/` plus the damage calc |
| **`tools/`** | The verification suite — calc reproducibility, integrity audit, sensitivity test — and the analysis skill |
| **`docs/`** | Phase gate reports, the integrity record, the vision and runbook |
| **`MANIFEST.md`** | Full file index with row counts |

## How a build is scored

Roles first, gates before scores. A wall without recovery is not a wall at any bulk,
and no amount of stats lets additive scoring pretend otherwise. Every build is scored
inside a role, never on one global ladder — a single list collapses into a base-stat
sort, which is measurably what happens if you try it.

`role_fit = w_stat·S + w_tool·T + w_type·Y + w_fight·F`, all four reported separately.

| term | what it measures |
|---|---|
| **S** | stat percentile within the obtainable pool at that checkpoint |
| **T** | movepool tools the role actually requires |
| **Y** | typing against *that boss's* attacking and defending types |
| **F** | boss-relative performance, from the matchup matrix |

**Floor** is zero investment: neutral nature, 0 EVs, more common ability, no item,
level-up moves only. **Ceiling** is the best build using only reliably obtainable
items. **VORP** subtracts the third-best *floor* build in the same role, so a species
is measured against what you would otherwise field, not against the whole roster.

Utility is scored inside the 1v1 primitive rather than bolted on afterwards: hazard
chip, status turn-denial, recovery and screens all act on the same turns-to-KO race
as damage, so a wall and a wallbreaker are commensurable.

## What is trustworthy and what is not

Every damage figure is **Derived**, never Measured — the mechanics generation is
pinned and every cell inherits that assumption. The engine was checked against an
independent Python reimplementation of the damage formula: **99.7% agreement over 600
cells spanning 18 move types**, with both discrepancies traced to the checker's own
limits rather than the engine.

Availability timing is mostly **Asserted** — 120 of 127 encounter maps are dated from
a secondary source, because the target's files encode which flag gates each checkpoint
but not which map is reachable when. The confidence rides with the number everywhere
it is shown, in amber.

**Four of seven invariants fail**, and the app says so on its About tab:

| check | result |
|---|---|
| I3 rank is not just a base-stat sort | **pass** — 0.502 against a 0.60 ceiling |
| I6 stats actually drive the build | **pass** — 85.6% against a 20% floor |
| I7 no move on more than 30% of sets | **pass** — 0.129 |
| I1 no item on more than a quarter | fail — 0.277 |
| I2 no nature on more than a fifth | fail — 0.281 |
| I4 every role has real competition | fail — 117 cells, mostly genuine role scarcity |
| I5 teams can all hold their items | fail — one item-copy conflict |

`docs/INTEGRITY_RECORD.md` is the adversarial record: eleven defects found and fixed,
every one of them silent, plus four process failures worth knowing about. Read it
before trusting any single number.

Other known limits, all stated in the app: 153 level-scaled rival slots are excluded
because they carry no fixed roster; nine target-custom boss forms are absent from the
species table; gift creatures and in-game trades were never parsed into the world data;
58 alternate forms inherit their base form's timing.

**`pipeline/` and `data/` are not separated behind an adapter.** Portability to a
second target was dropped by decision, so the ingest scripts read this target's layout
directly. The portability claim in `docs/VISION.md` section 8 has never been tested —
do not read this repo as evidence it holds.

## Rebuilding

```
cd pipeline
git clone --depth 1 https://github.com/RadicalRedShowdown/damage-calc calc
cd calc/calc && npm install && npx tsc -p . && cd ../..

python3 05_map_gates.py && python3 06_availability.py
python3 07_item_catalog.py && node 08_build_data_layer.js
python3 09_build_generator.py                    # ~150k candidate builds
node --max-old-space-size=4096 10_matrix.js      # ~70 min, 4.2M cells
python3 11_summarize.py && python3 12_roles.py && python3 13_valuation.py
cd ../app && python3 build_index.py              # rebuilds index.html
```

Steps 01–04 parse the target's source tree; the TSVs they produce are already in
`data/`, so a rebuild can start at 05.

## Naming

The target is referred to by codename only. Its public name, source repository and
website live in the **INTERNAL** target configuration block in `docs/RUNBOOK.md`
section 0, which ships empty and is never committed. See `docs/VISION.md` section 1.

Creature and move names appear inside `data/`. That is unavoidable and acceptable —
the goal is that this repo is not findable by someone searching for the target, not
that its contents are obfuscated.

No ROM, save file or game asset is redistributed here. Derived numeric tables only.

## Credits

Damage engine: [RadicalRedShowdown/damage-calc](https://github.com/RadicalRedShowdown/damage-calc),
used as a **mechanics engine only** — its bundled data layer is never used; every
calculation runs against a custom layer built from the target's own species table.
Sprites from [PokeAPI/sprites](https://github.com/PokeAPI/sprites) over the network.
