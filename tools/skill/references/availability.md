# Availability, Milestones and Routes

An S-tier build that needs a TM found after the fight it would win is worth nothing. Availability is not a filter applied at the end — it is a dimension of every score.

Contents:
1. The milestone list
2. The progression graph
3. Species channels
4. Item and TM availability
5. Level caps and evolution feasibility
6. Route scoring
7. Missables
8. Checklist state
9. What to do when the source doesn't encode ordering

---

## 1. The milestone list

A milestone is a named progression checkpoint with a gate: a badge, a story flag, a map that becomes reachable, a boss.

Each milestone carries:

| Field | Source |
|---|---|
| `id`, `order` | Adapter config |
| `gate` | The flag, badge count or map that opens it — Measured where the source encodes it |
| `level_cap` | Measured from the hack's cap implementation, or `none` |
| `bosses` | The trainer entries that count as bosses here |
| `maps_opened` | Which maps become reachable |

Milestone ordering is the single most common **Inferred** field in the whole model, because decomp sources encode gates but rarely encode a canonical order. Label it Inferred, state the assumption, and cross-check against the hack's own walkthrough or wiki — that ordering is legitimately what secondary sources are *for*.

---

## 2. The progression graph

Maps are nodes, gated by milestone. Each node carries encounters (with slot rates), ground items, hidden items, TMs, trainers, NPCs, shops, and one-time events.

Two things routinely go wrong here:

- **A map is reachable earlier than its "story" milestone**, via surf, a back entrance, or a sequence break. Assigning it to the wrong milestone makes everything on it appear later than it is, which understates early options. Where reachability is uncertain, assign the *later* milestone and flag it — the cost of a too-late assignment is a missed opportunity; the cost of a too-early one is a recommendation the player cannot act on.
- **A map's contents are gated separately from the map.** An item behind Rock Smash, Surf or a key item is gated by that HM, not by the map. Track the gate on the item, not just the node.

---

## 3. Species channels

A species has an **arrival milestone** or it is out of pool. Every channel must be parsed, because difficulty hacks distribute heavily through non-wild channels and a wild-encounter-only parse produces a badly wrong pool.

| Channel | Where it lives | Notes |
|---|---|---|
| Wild encounters | `wild_encounters.json` or `.inc` tables | Sum slot rates when a species occupies multiple slots |
| Starters | The starter species table in source | Hacks frequently change these; never assume the base game's trio |
| Gifts | `giveMon` / script events in map scripts | Usually one-time and missable |
| Eggs | Script events | Gated on whether breeding is available yet |
| In-game trades | Trade data tables and scripts | Costs a species — a mutual-exclusivity constraint |
| Static encounters | Script-triggered battles | Often one attempt only |
| Boss rewards | Post-battle scripts | Easy to miss in a parse |
| Fossils / choice events | Scripts | Mutually exclusive; record the exclusivity |

Record for each: the channel, the map, the level, the milestone, the copy count, whether it's one-time, and whether it's exclusive with something else.

**Report the species that end up unavailable.** A species present in the data but in no encounter table, no trainer party, no gift and no egg is either planned content or an author oversight, and it's worth telling the user which you think it is.

---

## 4. Item and TM availability

Parse placement from *every* source the codebase uses. In the the base decomp family that means at least:

- **Ground and hidden items** — in `data/maps/*/map.json`, as object events. Parsing only the scripts misses these entirely, and it is a large miss: coverage TMs are commonly ground items.
- **Script gifts** — `giveitem` / `giveitemfast` in `data/maps/*/scripts.inc` and `data/scripts/*.inc`.
- **Mart inventories** — item lists under a `Pokemart` label. Mart stock is effectively unlimited; everything else is a finite count.
- **Battle and NPC rewards** — post-battle scripts.

**Copy counts are literal.** `giveitemfast ITEM_X, 10` grants ten. Do not infer scarcity from how rare an item feels in other games.

Then classify supply:

- **Open** — purchasable, or ≥ 3 copies. Can be assumed in any build.
- **Scarce** — 2 copies.
- **Singleton** — exactly one in the entire game. Exactly one team member can hold it for the whole run.

This classification feeds the item dependence metric in `builds.md` and invariant I5.

For TMs, check whether the hack makes them **reusable**. Modern expansion builds usually do; older ones consume on use. It changes whether TM copy count is a real constraint or a non-issue, and it's a one-line check in the config headers.

---

## 5. Level caps and evolution feasibility

Many difficulty hacks enforce a level cap per badge, and it is usually implemented in a dedicated source file. **Read it; do not assume.** The cap determines:

- Which level-up moves are available at that milestone
- Which evolutions have happened
- The level at which every matchup is computed

Evolution feasibility gates on more than level:

| Method | Feasible when |
|---|---|
| Level | Level ≤ cap at that milestone |
| Item | The evolution item is obtainable by then, with copy count respected |
| Trade | Only if the hack replaced trade evolutions with another method — a trade evolution with no trade partner is **not feasible** in a single-player run. Check the config; expansion hacks very often patch this. |
| Friendship / time / location | The condition is reachable by that milestone |

An unevolved species held back by an infeasible evolution should still be scored — as itself, in its unevolved form, with the blocked evolution noted. Silently scoring it as its evolved form is a wrong answer the player will act on.

---

## 6. Route scoring

Each location gets a grade with a stated reason, built from four terms:

| Term | Question it answers |
|---|---|
| **Immediate value** | Does anything here improve the team for the *next* boss? |
| **Lineage value** | Does anything here become a top answer for a *later* boss, and is the investment cost worth it? |
| **Scarcity** | Is anything here unavailable or much harder to get elsewhere? |
| **Missability** | Is anything here permanently lost if the player walks past it? |

**Weight scarcity and missability hardest**, because they're the only irreversible terms. Immediate value can be obtained again later; a one-time gift cannot. A route full of good-but-common encounters is a B; a route with one one-time gift that becomes a top-5 answer at the Elite Four is an A regardless of what else it holds.

**Lineage is scored forward, not backward.** A weak species that becomes a top-3 answer two milestones later is an *investment*. Report it as:

> `Species X — investment. Payoff at milestone M (top-3 Special Wall). Cost: N levels under the cap, evolution item Y (open supply).`

Payoff milestone and cost, both stated. This is what makes a catch-priority list useful rather than a list of what's strong right now — and it's the main thing a player cannot work out for themselves mid-session.

### Per-route breakdown

For each location, produce:

- Encounter table with slot rates, level ranges, and each species' **current and projected** role ranks
- A **catch priority** ordering with one line of reasoning each
- Items and TMs, flagged with which species they unlock a build for
- Trainers worth fighting for a specific reason (a reward, a level-cap push, a rare item)
- An explicit **missable list** with the gate after which each is lost
- A **"safe to skip" verdict** when that's the honest answer. A route guide that grades everything as important is a route guide nobody reads.

---

## 7. Missables

The system's second success criterion is that nothing one-time and high-value is missed. Missability detection is therefore a first-class check, not a nicety.

Classify each one-time thing by **what closes it**:

| Closure type | Example |
|---|---|
| Hard gate | A map that becomes permanently inaccessible after a story event |
| Soft gate | An NPC who moves or stops offering something after a flag |
| Exclusive choice | Starters, fossils, either/or gifts — taking one forecloses the other |
| Consumed resource | A trade that costs a species; an item used on the wrong recipient |
| Level-window | An encounter or evolution only reachable below a cap that will rise |

For each, record the **last milestone at which it can still be obtained**. That field is what powers the "what have I passed that I shouldn't have?" query, and it's the one field most likely to be Inferred rather than Measured — flag it accordingly, and spot-check a sample against the hack's walkthrough before publishing.

When missable data is incomplete, say so explicitly and scope the claim: "missables verified for milestones 1–5; later milestones not yet audited" is honest and usable. Silence implies completeness that isn't there.

---

## 8. Checklist state

The route view is stateful for a single run: caught / obtained / skipped, plus the ability to ask what's been passed.

**Run state is INTERNAL, always.** It's personal, it changes daily, and it has no business in a shared repo. Keep it in a single local file with a documented shape, keep it separate from the derived datasets, and never fold it into an EXTERNAL export. See `deliverables.md`.

---

## 9. When the source doesn't encode ordering

Decomp sources encode gates and flags; they rarely encode "this is badge 4." Some of the milestone graph will always be Inferred. Handle it explicitly:

1. **Anchor on what is Measured** — level caps keyed to badge count, flag names that contain a badge or story reference, mart stock that changes at a known point.
2. **Fill the gaps from the hack's own walkthrough or wiki**, and label those fields **Asserted**.
3. **Cross-check the two.** Where the site and the source disagree, use the source and log the disagreement as a finding.
4. **Ask the user.** They're playing it. For an ordering question that costs an hour to derive and ten seconds to answer, ask — then record the answer as Asserted with the user as the source.
