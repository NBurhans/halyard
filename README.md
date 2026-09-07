# halyard

A data-driven planning framework for turn-based RPG progression.

All 1,523 species forms scored by role against every boss roster at each of
nineteen checkpoints, from **4,248,276 damage-calculated matchups**.

**[Open the survey →](https://YOUR_GITHUB_USERNAME.github.io/halyard/)**

## What is here

| | |
|---|---|
| **`index.html`** | The survey — dex, rankings, roles, bosses, routes, party. Self-contained |
| **`data/`** | Analysis output as TSVs. `05_valuation.tsv` is the headline: 19,215 scored rows |
| **`pipeline/`** | Every script, numbered in dependency order |
| **`app/`** | The payload transcoder and app builder |
| **`tools/`** | Verification suite — calc reproducibility, integrity audit, sensitivity test |
| **`docs/`** | Phase gate reports, the integrity record, publishing guide |

## How a build is scored

Roles first, gates before scores. A wall without recovery is not a wall at any
bulk. Every build is scored inside a role, never on one global ladder — a single
list collapses into a base-stat sort, which is measurably what happens if you try.

`role_fit = w_stat·S + w_tool·T + w_type·Y + w_fight·F`, all four reported.

**Floor** is zero investment. **Ceiling** is the best build using only reliably
obtainable items. **VORP** subtracts the third-best *floor* build in the same role.

**Sustain** is the turn dimension the damage axes cannot see: the roster walked
sequentially on one lifebar, the bar resetting at each trainer boundary, with
per-turn recovery counted. The published figure is the **kit delta** — this
species minus the identical species with no kit — because raw sweep depth
measures size rather than kit. Raw depth correlates +0.37 with BST here; the
delta correlates **−0.17**.

## What is trustworthy and what is not

Every damage figure is **Derived**, never Measured — generation 8 mechanics are
pinned and every cell inherits that. The engine was checked against an
independent reimplementation of the damage formula: **99.7% agreement over 600
cells spanning 18 move types**.

Availability timing is mostly **Asserted** — 120 of 127 encounter maps are dated
from a secondary progression source, because the target's files encode which flag
gates each checkpoint but not which map is reachable when.

**Four of seven invariants fail.** I3 (rank is not a base-stat sort) passes at
0.502 against a 0.60 ceiling; I6 (stats drive the build) at 0.856 against a 0.20
floor; I7 at 0.129. I1, I2, I4 and I5 do not pass. `docs/INTEGRITY_RECORD.md`
lists eleven defects found and fixed, every one silent, plus four process failures.

Tier cuts are recut against this VORP distribution rather than inherited, so they
are not comparable to any earlier run's badges.

## Credits

The survey interface is the Emerald Imperium analysis app by the same author,
reused wholesale — its layout, dossier, party and boss views are unchanged. Only
the data underneath is swapped, and a Routes tab added. Sprite art is the bundle
that ships with it, from ydarissep/JwowSquared.github.io; 99.9% of forms match.

Damage engine: [RadicalRedShowdown/damage-calc](https://github.com/RadicalRedShowdown/damage-calc),
used as a **mechanics engine only** — its bundled data layer is never used.

No ROM, save file or game asset is redistributed here. Derived tables only.
