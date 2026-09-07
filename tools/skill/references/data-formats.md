# ROM Hack Data Formats

Contents:
1. Decomp C sources (the base decomp / pokefirered / pokecrystal family)
2. Pokémon Essentials PBS text files
3. Universal Pokémon Randomizer logs
4. GUI editor exports (PGE, G3T, HexManiac, PokeFinder)
5. Spreadsheet and JSON exports
6. Save file and inventory dumps
7. General parsing advice
8. Placement and progression data in expansion-era repos

---

## 1. Decomp C sources

**Tells:** `.h`, `.inc`, `.c` extensions; C struct initializer syntax; `SPECIES_`, `MOVE_`, `ITEM_`, `ABILITY_`, `TYPE_` constant prefixes.

Base stats live in `src/data/pokemon/base_stats.h` as struct initializers. **In recent the base decomp versions this file no longer exists** — species data moved to `src/data/pokemon/species_info/gen_N_families.h`, one file per generation, with learnsets, evolutions, and form data folded into the same struct. Check both layouts before concluding the data is missing; a parse that finds zero species usually means the wrong path, not an empty repo.

```c
[SPECIES_BULBASAUR] =
{
    .baseHP        = 45,
    .baseAttack    = 49,
    .baseDefense   = 49,
    .baseSpeed     = 45,
    .baseSpAttack  = 65,
    .baseSpDefense = 70,
    .type1 = TYPE_GRASS,
    .type2 = TYPE_POISON,
    .catchRate = 45,
    .expYield = 64,
    .growthRate = GROWTH_MEDIUM_SLOW,
    .abilities = {ABILITY_OVERGROW, ABILITY_NONE},
},
```

Parse with a regex over `\[SPECIES_(\w+)\]\s*=\s*\{(.*?)\n\};?` in DOTALL, then key-value pairs on `\.(\w+)\s*=\s*([^,]+),`. Field names vary across decomp forks and across expansion versions — do not hardcode a field list, discover it from the file and report which fields are present.

Other files worth knowing:
- `level_up_learnsets.h` — learnsets, often as `LEVEL_UP_MOVE(level, MOVE_X)` macros.
- `tmhm_learnsets.h` — bitfield or macro lists of TM compatibility.
- `evolution.h` — `{EVO_LEVEL, 16, SPECIES_IVYSAUR}` triples; the middle parameter's meaning depends on the evolution method constant.
- `wild_encounters.json` (modern the base decomp) or `.inc` tables (older) — encounter slots.
- `trainers.h` + `trainer_parties.h` — trainer definitions and their rosters, linked by party pointer name.
- `type_effectiveness` tables — Gen 3 stores these as flat triples terminated by a sentinel; a modified chart is a common hack feature and must be parsed, not assumed.

**Critical:** hacks built on the the base decomp frequently add fields (`.isLegendary`, `.eggGroups`, hidden ability slots) and change enum ordering. Treat the constants file (`include/constants/species.h`) as authoritative for the ID↔name mapping and load it explicitly rather than assuming National Dex order.

---

## 2. Pokémon Essentials PBS files

**Tells:** `.txt` files named `pokemon.txt`, `moves.txt`, `trainers.txt`, `encounters.txt`, `items.txt`, `abilities.txt`; INI-like sections.

Modern (v19+) format:

```
[BULBASAUR]
Name = Bulbasaur
Types = GRASS,POISON
BaseStats = 45,49,49,45,65,70
Moves = 1,TACKLE,3,GROWL,7,LEECH_SEED
```

Older versions use numeric section headers (`[1]`) with an `InternalName` field. `BaseStats` order is **HP, Attack, Defense, Speed, Sp.Atk, Sp.Def** — note Speed sits fourth, not last. Getting this wrong silently swaps Speed and Sp.Atk across the entire dataset, which is the single most common parse bug in Essentials analysis. Sanity check it: if your parsed "Speed" distribution has a suspicious number of 20s and the "Sp.Atk" column looks fast, you swapped them.

`moves.txt` uses comma-positional fields whose order changed between Essentials versions. Confirm the version from `Game.rxdata` metadata or ask the user before trusting positional parsing.

---

## 3. Universal Pokémon Randomizer logs

**Tells:** plaintext `.log`, header naming the randomizer version and seed, sections separated by blank lines and headings like `--Pokemon Base Stats & Types--`, `--Wild Pokemon--`, `--Trainers Pokemon--`.

Fixed-width-ish columns that are not reliably delimited. Split on runs of 2+ spaces rather than single spaces. The log records the *randomized* result, not the hack author's deliberate design — say so when interpreting, since "the designer intended" claims are meaningless for randomized data.

Randomizer logs also frequently truncate long move lists with ellipses. Check for `...` before treating a movepool count as complete.

---

## 4. GUI editor exports

- **PokéGen / G3T (Gen 3 Tools):** CSV exports with editor-specific column headers. Usually clean, but IDs are internal indices, not Pokédex numbers.
- **HexManiac Advance:** exports tables as CSV with the internal table name as the filename. Preserves index order faithfully — a good source of truth for ID mapping.
- **PokeFinder / encounter tools:** encounter slot tables with rates as percentages or as raw slot counts. Confirm which; a "rate" column summing to 100 is percentages, one summing to 12 or 10 is slot counts.

---

## 5. Spreadsheet and JSON exports

Hand-maintained design spreadsheets are common and are the most likely source to contain human error: merged cells, notes in numeric columns, trailing whitespace in species names, two rows for one species after an edit. Read every sheet in the workbook, not just the first, and check for a hidden or `_old` sheet that may be the real data.

For JSON, dump the top-level key structure before parsing so the user can confirm you found the right node.

---

## 6. Save file and inventory dumps

Occasionally the data is a playthrough state rather than game internals — party, box, bag. These describe one player's run and generalize poorly. Treat them as a sample of size one and say so before drawing any conclusion about the hack's design.

---

## 7. General parsing advice

- **Save the intermediate.** Write the parsed dataframe to CSV in the working directory and mention the path. The user should be able to audit the parse independently of the analysis.
- **Report parse loss.** If the source has 411 species entries and your dataframe has 386, that gap is a finding, not a rounding error. Locate it before continuing.
- **Never assume the ID mapping.** See `integrity-checks.md` § index offsets.
- **Encoding:** decomp files are UTF-8; older editor exports are often Latin-1 or Shift-JIS. A `UnicodeDecodeError` on a Pokémon name usually means a special character in a custom species name — recover it rather than dropping the row.

---

## 8. Placement and progression data in expansion-era repos

Base stats and learnsets are the easy half. The availability model in `availability.md` needs to know *where* everything is, and expansion-era repos scatter that across at least five places with different formats. A parse that reads only one of them looks successful and is badly incomplete.

### Ground and hidden items — `data/maps/<Map>/map.json`

Items lying on the ground are **object events in `map.json`**, not script commands. They are commonly encoded with the item constant in a field that looks unrelated to items — in the base decomp the item ID rides in `trainer_sight_or_berry_tree_id` on an item-ball object event.

This is the single easiest miss in the whole ingest, and it is a large one: coverage TMs are very often ground items. If your TM location table is missing obvious moves — Earth Power, Superpower, X-Scissor, Iron Tail — you parsed scripts only. Check `map.json` before concluding a TM is unobtainable.

### Script gifts — `data/maps/<Map>/scripts.inc` and `data/scripts/*.inc`

`giveitem` and `giveitemfast` calls, with a literal count argument. **The count is real.** `giveitemfast ITEM_TOXIC_ORB, 10` grants ten copies, and difficulty hacks use bulk dispensers like this deliberately to make a whole item tier freely available. Parse the count, don't assume 1.

Species gifts (`givemon`), eggs, and static encounters live in the same files. So do post-battle rewards.

### Mart inventories

Item lists under a label matching `*Pokemart*`, usually as `.2byte ITEM_*` lines terminated by a sentinel. Mart stock is effectively **unlimited supply**; everything else is a finite copy count. This distinction drives the open/scarce/singleton classification in `builds.md` §5, so parse marts separately rather than folding them into placement counts.

### Trainers and rosters — `trainers.h` / `trainers.party` / `trainer_parties.h`

Linked to rosters by party pointer name in older layouts; newer expansion versions use a `.party` text format that's easier to parse but structured differently. Boss rosters must be Measured from here — level, species, item, ability, nature and moves — because the whole matchup layer rests on them. A roster taken from a wiki is Asserted at best and frequently stale.

### Level caps and mechanics config

Difficulty hacks that enforce a level cap usually implement it in a dedicated source file (commonly `src/caps.c` or similar) keyed to badge count or a flag. Read it. Do not assume the presence or absence of a cap.

`include/config/*.h` holds the generation switches — `#define X GEN_N` and `TRUE`/`FALSE` toggles — that determine which mechanics apply: the physical/special split, crit rates, ability behaviour, whether TMs are reusable, whether hidden abilities are obtainable, whether trade evolutions were patched to another method. Parse this file early; almost every formula in `mechanics.md` depends on something in it.

### Encounters — `src/data/wild_encounters.json`

Modern layouts use JSON keyed by map, with separate land/water/rock-smash/fishing tables and an encounter rate per table. Older layouts use `.inc` tables. When a species occupies multiple slots in one table, **sum its slot probabilities** — a species in slots 1 and 2 has 40% presence, not 20%. This is a frequent source of undercounted availability.

### A parse checklist for this layer

Before treating the availability model as complete, confirm you have read: `map.json` object events, `scripts.inc` give-calls with counts, mart tables, trainer parties, the level cap file, the config headers, and the encounter JSON. Report the count found from each source. A source that yielded zero results is either genuinely absent from this hack or a path you got wrong, and the difference matters.
