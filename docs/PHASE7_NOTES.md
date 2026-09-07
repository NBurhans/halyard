# HALYARD / target SABLE — Phase 7 companion app

**Deliverable:** `halyard_sable.html` — 2.01 MB, single file, opens offline.

## Self-containment

| requirement | result |
|---|---|
| external network references | **0** |
| `localStorage` / `sessionStorage` | **0** |
| build step | none — open the file |
| payload | embedded, 1.98 MB interned JSON |

Everything is interned into string tables and emitted as arrays; an object-per-row payload of 19,215 valuation rows would have cost several megabytes in repeated key names.

## Verification

Not just "the file is well-formed" — the payload was re-parsed out of the finished HTML and every view exercised headlessly against it:

| check | result |
|---|---|
| payload parses from the shipped file | yes |
| dangling species references in valuation | **0** |
| dangling species references in routes | **0** |
| app JavaScript syntax | clean |
| rankings / dex / fights / routes / method | **all render** |
| species card | renders |

## Scope decision — no availability filtering

Two different columns in this dataset both get called "checkpoint", and only one is trustworthy:

| column | meaning | UNK | shipped |
|---|---|---|---|
| `earliest_cp` | when the player can obtain the form | **61.8%** | **no** |
| `checkpoint` | which boss roster the build was scored against | 0% | yes |

The app offers no availability filter and no availability column, because that data would look authoritative and be wrong. Boss-fight views are kept — those rosters are parsed from real trainer data with nothing unresolved. The Method tab states this in plain language rather than hiding it.

## Views

- **Rankings** — value over replacement, filtered by role and boss fight, sortable. Scarce items and one-time availability are flagged inline. Top 300 shown with a stated count.
- **Dex** — searchable, filterable by type and tier, 1,523 species-forms.
- **Species card** — stats with bars, typing, abilities, evolutions, the best build across fights with all four fit components, and a per-fight ceiling sparkline. Opens from any table row.
- **Boss fights** — 90 fights across 17 checkpoints with full rosters and level caps.
- **Routes** — 127 maps, 2,197 encounter records: which Pokémon appear where, with method, levels, rate and best tier. Read-only, as specified — no missable tracking, no completion state.
- **Method** — what the numbers are, the four failing checks named rather than buried, tier thresholds, and the availability exclusion.

## Design

Cool instrument palette (pale blue-grey, deep slate ink, single deep-cyan signal, amber only for flags), one sans family throughout with tabular numerals rather than a monospace face, and the tier ramp as the one place colour does real work. The data is the hero — the app opens straight into the ranking table, with no marketing header.

Quality floor: responsive to mobile, visible keyboard focus, `Enter` opens any row, `Escape` closes the panel, reduced motion respected, empty states that say what to do next.

## Known limits carried into the app

- 61.8% of rows have unknown obtainment timing — surfaced in Method, not filtered on
- 153 level-scaled rival slots excluded from all scoring
- 9 target-custom boss forms absent from Phase 1
- I1, I2, I4, I5 fail; each is named on the Method tab with its cause
