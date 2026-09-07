# Deliverables, Classification and Presentation

Every artifact gets classified at creation and presented at three depths. Both rules exist for the same reason: the person has to be able to *use* the output and *trust* it, and those need different things.

Contents:
1. INTERNAL vs EXTERNAL
2. The classification test, and its one exception
3. Naming and repo policy
4. Three depths
5. Dual-format data
6. Workbooks and dashboards
7. Confidence on every field

---

## 1. INTERNAL vs EXTERNAL

Classify at creation, not at publication. Retrofitting a classification onto a folder of files is how private run state ends up in a public repo.

### INTERNAL — local disk only

- Cloned hack source, raw dumps, any copy of the game's data files
- Snapshots of scraped wiki or website pages
- Intermediate parse artifacts — pickles, working dataframes, scratch CSVs
- Weight-tuning worksheets and calibration notes
- **Personal run state** — the actual team, checklist progress, house rules, save data
- Anything that only makes sense with the target's source tree present

Naming: `INT_<topic>_<version>.<ext>`, in a local project folder.

### EXTERNAL — ships to the repo

- The engine, parsers, adapters, and this skill
- Processed, self-describing datasets — TSV bundles with README, CSV/JSON exports with metadata
- Rendered dashboards and checklists
- Documentation, including the vision document
- Integrity logs, invariant reports, validation results

Naming: `EXT_<topic>_<version>.<ext>`, or conventional repo names once the layout is established.

**Never commit** ROM files, save files, or game assets — sprites, audio, tilesets, music. Derived numeric tables only.

---

## 2. The classification test, and its one exception

The test: **can this artifact be used by someone who doesn't have the source tree?** If yes, EXTERNAL. If no, INTERNAL.

The exception, deliberately taken: **parsers and the engine are EXTERNAL even though they consume source.** The strict test would push them INTERNAL, but the reusable engine *is* the product, and needing a target to run against is the whole point of the portability goal. Raw source stays INTERNAL; code that reads it ships.

When something genuinely doesn't fit either bucket, say so and ask rather than guessing. The cost of a wrong guess is asymmetric — an over-cautious INTERNAL classification costs nothing but a conversation.

---

## 3. Naming and repo policy

The repo is meant to be hard to find by chance. That's a discoverability goal, not an obfuscation goal — the contents are readable, the metadata just isn't searchable.

1. **No franchise-identifying words** in the repo name, description, topics, README title, or commit messages.
2. **Codenames for targets** in folder names, never a hack's public name.
3. Species, move and map names inside data files are unavoidable and acceptable.
4. No repo topics or tags. No links to the repo from forums, Discord, or wikis.

Note the tension this creates with this skill's own description, which needs franchise terms to trigger reliably. Skill descriptions are functional configuration inside the repo, not repo metadata, so they're out of scope for rules 1–2 — but keep the README and commit messages clean regardless.

---

## 4. Three depths

Always all three, never only one. A verdict without a drill-down is unfalsifiable; a spreadsheet without a verdict is homework.

| Depth | Form | Purpose | Test of success |
|---|---|---|---|
| **Glance** | One screen. A verdict and three bullets. | Mid-session, in-game decisions | Readable on a phone between battles |
| **Working** | Sortable tables, workbook, filterable dashboard, charts | Planning between sessions | Every recommendation can be compared against its alternatives |
| **Audit** | Full derivation, source file and line references, integrity log, invariant results | Trusting the above | Any single number can be traced to the file it came from |

The Glance layer is the one most often skipped and the one the user actually reads most. Write it last, from the finished analysis, and make it commit to a recommendation. "It depends" is not a Glance answer; "lead with X, your weak slot is Y, don't skip the gift on Route 116" is.

**Charts serve a decision.** No chart exists to demonstrate that charts can be made. If you can't name the decision a chart informs, cut it. For chart construction and design principles, borrow from the `data` skill family — `data:create-viz` and `data:data-visualization` for chart selection and publication quality, `data:build-dashboard` for the self-contained HTML pattern.

---

## 5. Dual-format data

Every dataset ships **twice**: once for a human to read, once as JSON or TSV for a machine to reload. These are not alternatives. The readable form is how the person checks the work; the machine form is how a later session picks it up without re-deriving anything — the difference between analysis that compounds and analysis that restarts every conversation.

**Single result** — use `scripts/export_dataset.py`:

```python
from export_dataset import export
export(df, "role_ladder_m04",
       title="Role ladders at milestone 4",
       sources=["src/data/pokemon/species_info/*.h", "data/maps/*/map.json"],
       confidence="Derived",
       classification="EXTERNAL",
       notes="Level cap 35 applied; open items only. See builds.md §5",
       column_docs={"item_dependence": "score(best item) − score(best open item)"})
```

That writes `<name>.json` (metadata block + records), `<name>.csv`, and updates `manifest.json`. The metadata block matters: a JSON file that reaches a future session without its provenance, confidence tier and classification is a pile of numbers nobody should trust.

**Whole database** — use `scripts/export_bundle.py` for a TSV bundle. JSON repeats every key on every row; a 92,000-row movepool table spends most of its bytes rewriting the string `move_id`, and the same content as TSV is routinely 8–12× smaller and no harder to read.

Two rules separate a bundle from a folder of files:

- **Fold one-to-many relations into the parent row.** Level-up, TM and egg move tables each repeat the species key tens of thousands of times. Encoded as columns they cost a fraction of that. Document the encoding in the README — a column reading `33:1,45:3` is meaningless without it.
- **Ship `00_README.md` alongside**: provenance, parse gotchas with the consequence of getting each wrong, the confidence split, validation numbers, every correction made, what is stale, and an explicit list of superseded files with reasons. A bundle that quietly omits a superseded version looks like data loss; one that lists it and says why is a record.

Always call `verify()` before presenting. Re-read every file, confirm the row counts round-trip, and spot-check that an encoded column decodes back to something recognisable — a stat line matching vanilla, an evolution resolving to the right species. Never present a bundle you have not re-read.

Bundles are EXTERNAL by construction. If a bundle would contain run state, split it.

---

## 6. Workbooks and dashboards

**The primary human-readable deliverable for a modelling pass is an .xlsx workbook that shows the work.** Read `/mnt/skills/public/xlsx/SKILL.md` before building it. Not a table of final answers:

- A `README` sheet: source files, commit or branch, row counts, parse date, the Data Integrity Log, and the invariant report.
- One sheet per analysis with **intermediate columns visible** — if you computed an effective-bulk index, HP, Def and the formula's components sit next to it, and the cell holds a real Excel formula rather than a hardcoded value wherever practical. The person should be able to change a weight and watch the ladder move.
- Charts on their own sheet or anchored beside the data they describe, as native Excel charts so they stay live.

**Dashboards must be self-contained**: a single HTML file that opens offline, with no build step and no CDN dependency. Read `/mnt/skills/public/frontend-design/SKILL.md` before building one. A dashboard that needs a network connection is useless in the situation it was built for.

For a quick read in chat, an inline chart alongside the headline finding is welcome. It supplements the workbook; it doesn't replace it.

---

## 7. Confidence on every field

Every displayed number carries a confidence tier — Measured, Derived, Inferred, Asserted, or Unresolved. **A number without one is a bug.**

In tables, that's a column or a suffix. In prose, it's a clause. In a workbook, it's a header note or a legend on the README sheet. In a Glance card, it's acceptable to state the tier once for the whole card if every number on it shares one — and to say which numbers don't.

The tiers exist so the user can accept your measurements and reject your interpretation independently. That only works if the seam is visible everywhere, not just in the audit layer.
