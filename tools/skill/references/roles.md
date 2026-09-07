# Roles and Role Scoring

*(This file replaces the earlier `archetypes.md`. The taxonomy and the gates-before-scores method carry over; what's new is that every role is now scored against the boss rosters at a milestone rather than against an abstract rubric.)*

The purpose is to answer "what is this build *for*, in this fight" rather than "how good is this Pokémon." Those are different questions, and conflating them is how analysis ends up re-deriving the BST ranking with extra steps.

A build with a mediocre stat total can be the best available answer to a specific problem — a slow bulky Ghost with reliable recovery and Will-O-Wisp is a first-rate physical wall regardless of its 480 BST, *if the boss it's being scored against actually attacks physically*. The framework exists to surface exactly those cases. If the output doesn't surface any, something is wrong with it.

Contents:
1. Gates before scores
2. Roles are relative to the roster
3. Role taxonomy
4. The toolkit component
5. The typing component
6. Per-role scoring notes
7. Reporting

---

## 1. Gates before scores

A wall without recovery is not a wall. A sweeper that cannot boost and cannot outspeed anything is not a sweeper. Additive scoring hides this: a species with enormous HP and Defense but zero recovery and zero utility will still land near the top of a "physical wall" ranking if bulk is 60% of the weight.

Every role has two parts:

- **Gates** — binary requirements. Fail one and the build is disqualified from that role, regardless of stats. Gates encode what the role actually *requires* to function.
- **Score** — a continuous 0–1 fit measure, computed only for builds that pass the gates.

```
role_fit = 0                                              if any gate fails
role_fit = w_stat·S + w_tool·T + w_type·Y + w_fight·F     otherwise
```

`S` stat fit, `T` toolkit fit, `Y` typing fit, `F` **fight fit** — the boss-relative term, which is what distinguishes this from a generic tier list. Weights sum to 1. Report all four components alongside the total; a single opaque number is not usable for team-building.

**Percentile-normalize, don't min-max.** Rank each stat within the *obtainable pool at that milestone* and use the percentile. Min-max scaling lets a handful of legendary outliers compress everyone else into the bottom third, reintroducing exactly the BST bias the framework is meant to avoid.

Gates evaluate against the build's **available** moves and abilities at that milestone, not its full lifetime pool. A wall whose recovery move is learned at level 52 under a level-40 cap does not pass the recovery gate yet. This is the single most common source of a role ranking that looks right and is useless.

---

## 2. Roles are relative to the roster

**A role's score is only meaningful relative to the boss rosters at that milestone.** This is the central change from a generic archetype rating.

A hazard setter is near-worthless against a three-Pokémon gym and excellent against a six-Pokémon Elite Four member with three Stealth Rock weaknesses. A physical wall is a top pick against a boss with four physical attackers and a liability against the same boss's special-leaning successor. Scoring either one on an abstract utility rubric produces a number that is stable, defensible, and wrong.

The `F` term is computed from the milestone's boss rosters, per role:

| Role family | `F` is a function of |
|---|---|
| Offense | How many roster members this build beats 1v1, weighted by how threatening they are (from `matchups.md` §4) |
| Defense | Turns survived against that roster's actual win conditions, and how many of its attackers it walls outright |
| Utility — hazards | How many switches the roster forces × how many members take meaningful chip |
| Utility — removal | Whether the boss sets hazards at all, and how much they cost the intended team |
| Utility — status | How many roster members are crippled by the status this build applies, and whether any absorbs it |
| Utility — phazing | Whether the roster has a setup sweeper worth forcing out |
| Enabler | What it enables *on that team, in that fight* — zero in isolation |

Where a role's `F` is zero for a milestone, say so. "No hazard setter is worth a slot against this gym" is a real and useful finding; ranking hazard setters against each other for a fight where none of them matter is not.

---

## 3. Role taxonomy

A starting vocabulary, not a fixed schema. Hacks vary. If a hack's mechanics create a role this list doesn't name, add it and say so; if the hack can't support a role — no Trick Room move means no Trick Room role — drop it and report that you did.

### Offense

| Role | Core stats | Gates | Typical enablers |
|---|---|---|---|
| **Wallbreaker (physical)** | Atk | ≥2 physical moves ≥90 BP available; ≥3 attacking types in the available pool | Sheer Force, Guts, Huge Power, Choice Band |
| **Wallbreaker (special)** | SpA | ≥2 special moves ≥90 BP; ≥3 attacking types | Sheer Force, Solar Power, Choice Specs |
| **Setup Sweeper** | Atk or SpA, Spe | ≥1 setup move raising the relevant offense or Speed; ≥1 STAB ≥75 BP on the matching side | Speed Boost, Moxie, Adaptability, boosting items |
| **Revenge Killer** | Spe, Atk or SpA | ≥1 priority move OR top-quartile Speed in the milestone pool | Prankster, Gale Wings, Choice Scarf |
| **Trick Room Attacker** | Atk or SpA, *inverted* Spe | Bottom-quartile Speed; above-median offense; Trick Room exists and is obtainable | Brave/Quiet nature, bulk |
| **Priority Abuser** | Atk or SpA | ≥1 priority move with usable power and STAB or coverage relevance | Technician, Adaptability |
| **Mixed Attacker** | Atk and SpA both above median | Usable STAB on *both* sides | Adaptability, Protean/Libero |

### Defense

| Role | Core stats | Gates | Typical enablers |
|---|---|---|---|
| **Physical Wall** | HP×Def | Reliable recovery available; ≥1 physical-attack answer (burn, Intimidate, phazing) | Regenerator, Intimidate, Fur Coat |
| **Special Wall** | HP×SpD | Reliable recovery; ≥1 special answer or status | Regenerator, Ice Scales, Natural Cure |
| **Mixed Wall** | HP×min(Def,SpD) | Recovery; both defenses above median | Unaware, Magic Guard |
| **Regenerator Pivot** | HP, Def or SpD | Pivot move (U-turn/Volt Switch/Teleport/Flip Turn) available | Regenerator above all |
| **Tank** | HP + bulk + offense | Above-median bulk *and* above-median offense; no setup required | Assault Vest, Rocky Helmet |

### Utility

| Role | Gates | Typical enablers |
|---|---|---|
| **Hazard Setter** | Knows an obtainable hazard move | Sturdy, Prankster, Focus Sash |
| **Hazard Remover** | Rapid Spin / Defog / Mortal Spin available | Regenerator |
| **Cleric / Status Absorber** | Wish / Heal Bell / Aromatherapy / Healing Wish, or a status immunity that matters | Natural Cure, Guts |
| **Phazer** | Whirlwind / Roar / Dragon Tail / Circle Throw | Bulk, hazards already up |
| **Screens Setter** | Reflect + Light Screen, or Aurora Veil | Prankster, Light Clay |
| **Trapper** | Trapping ability or trapping move | Arena Trap, Shadow Tag, Magnet Pull |
| **Weather / Terrain Setter** | Setter ability OR the setting move | Drought, Drizzle, Sand Stream, the Surges |
| **Status Spreader** | ≥1 of Will-O-Wisp / Thunder Wave / Toxic / Spore / Glare | Prankster, No Guard + Spore |
| **Speed Control** | Tailwind / Trick Room / Sticky Web / Thunder Wave | Prankster |

### Enabler

| Role | Gates | Notes |
|---|---|---|
| **Sacrificial Pivot** | Memento / Healing Wish / Explosion, or Sturdy + suicide-lead kit | Scores only in a team context |
| **Redirection** | Follow Me / Rage Powder | Usually near-zero in single battles; drop the role if the hack has no doubles bosses |
| **Baton Passer** | Baton Pass + a setup move | Scores only against rosters slow enough to allow the pass |

Enabler roles are the clearest case where a standalone score is meaningless. Score them at the team layer or not at all, and say which you did.

---

## 4. The toolkit component

`T` measures whether the build has the moves and abilities the role wants, over and above the gates it already passed.

**Build move-category lists by scanning the hack's own move table**, not by hardcoding names. Hacks add, rename, and re-power moves constantly.

- **Recovery**: moves healing a fraction of max HP. Detect via the healing property or flag where the data exposes one; fall back to a name list only when it doesn't.
- **Setup**: moves whose self-effect raises Atk, SpA, Def, SpD, or Spe.
- **Hazards / removal / pivots / screens / status**: small curated lists, each verified to exist in this hack's move table before use.

Score `T` as the fraction of the role's *bonus* tools present, capped at 1. Weight abilities into `T` rather than giving them a separate term — an ability that enables a role (Regenerator on a pivot) is worth more than a marginal extra move, so give enabling abilities a heavier contribution.

**Check the physical/special split convention first.** In Gen 3 the split is by type; from Gen 4 it's per move. Getting this backwards makes every offensive role wrong. See `mechanics.md`.

**Gate on availability, score on the pool.** The gates use what's obtainable at this milestone. `T` may look ahead — a build one TM away from a much better toolkit is worth flagging as an investment — but only if the lookahead is labelled, with the milestone the TM arrives.

---

## 5. The typing component

For **defensive** roles, `Y` derives from the resistance profile: resistances and immunities against weaknesses, using **the hack's own type chart**. Weight by which attacking types are actually common in the milestone's boss rosters — a Fire resistance is worth more against a Fire gym than against the pool at large. This is where `Y` and `F` overlap; keep the split clean by making `Y` about the type profile in the abstract and `F` about this specific roster.

For **offensive** roles, `Y` is STAB quality: does the build have a same-type attacking move on the side its higher attacking stat sits on, and how much of the milestone's opposition does that STAB hit neutrally or better. A high-Attack species whose only strong STAB is special is a mismatch, and that mismatch should visibly depress its offensive role scores.

---

## 6. Per-role scoring notes

These are the places where a naive score goes wrong most often.

**Walls.** Score turns survived against the roster's win conditions, not raw bulk. A wall that survives twelve turns against a threat that isn't the fight's problem has done nothing. Recovery PP is a real constraint in long fights — if the boss out-PPs the wall, the wall loses eventually.

**Hazard setters.** Value = switches forced × chip landed. A boss with three Stealth Rock weaknesses and an AI that switches is a hazard setter's dream; a three-Pokémon gym that never switches is worth zero. Also check whether the boss removes hazards — a Defogger on the roster halves the term.

**Revenge killers.** The gate is speed *relative to this roster*, not a global speed tier. Compute what it actually outspeeds after the boss's items and abilities. Priority is a partial substitute, weighted by whether the roster's threats survive a priority hit.

**Setup sweepers.** Score the setup opportunity, not just the post-setup power. If nothing on the roster gives a free turn, the setup move is a dead slot and the build should score as a plain attacker. Phazing and status on the boss's side kill setup entirely — check for both.

**Cleric / status absorber.** Scores near zero against a roster that inflicts no status, and highly against one built around Toxic or Will-O-Wisp. This is a role whose value swings more between milestones than almost any other.

**Trappers.** Value is entirely about whether the roster has something worth removing that the trapper beats 1v1. Compute that intersection explicitly.

**Weather / terrain setters.** Score the whole-team effect, not the setter's own performance, and check whether the boss sets competing weather — a setter that gets overwritten every switch is worse than nothing.

---

## 7. Reporting

**Report the top three role fits per build, not just the winner.** Many builds are genuinely hybrid, and forcing a single label discards information. Call the top one `primary_role`; where the runner-up is within ~0.05, mark it hybrid and name both.

**Some builds fail every gate.** That's a finding, not a bug — it means that build has no functional role against this milestone's opposition. Report the count and name a few. Do not invent a "generalist" bucket to absorb them; that hides the result.

**Publish per role, per milestone.** A single global ordered list is a BST ranking with extra steps, and it buries the specialists.

**Run the invariants before publishing.** `invariants.md` — especially I3 (BST correlation in band), I4 (role depth), and diagnostics D1 (low-BST representation) and D2 (gate bite). A ladder published without them is an opinion.
