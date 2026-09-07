# Invariants

The requirement that *no one item, nature, or moveset should ever be the dominant recommendation* is treated as a hard constraint with falsifiable tests, not an aspiration. These checks run against the recommended-build set before any ladder is published, and a failure blocks publication.

Run `scripts/invariants.py` to compute them. Report the results **with** the deliverable — they are the evidence that the ranking means something, and a ladder published without them is an opinion.

Contents:
1. The invariant table
2. Notes on the load-bearing ones
3. Diagnostic checks (report, don't block)
4. What to do when one fails
5. Reporting format

---

## 1. The invariant table

Computed over the set of **recommended builds** — one primary build per (species, milestone) that passed the gates and appears in the published output.

| # | Invariant | Threshold | Blocks release |
|---|---|---|---|
| **I1** | No single held item appears in more than 25% of recommended builds | ≤ 0.25 | Yes |
| **I2** | No single nature appears in more than 20% of recommended builds | ≤ 0.20 | Yes |
| **I3** | Correlation between final rank score and BST | 0.30 ≤ \|r\| ≤ 0.60 | Yes |
| **I4** | Every role at every milestone has ≥ 3 species within 10% of the leader | ≥ 3 | Yes |
| **I5** | Recommended teams are simultaneously equippable given copy counts | 100% | Yes |
| **I6** | Perturbing base stats by ±15 changes the recommended build for ≥ 20% of species | ≥ 0.20 | Yes |
| **I7** | No move appears in more than 30% of recommended movesets, excluding obligatory STAB fillers | ≤ 0.30 | Yes |

Thresholds are defaults, tuned against a Hoenn-scale roster of roughly 400 obtainable species. They are configurable per target, but **changing a threshold to make a failing check pass is not a fix** — record any change, with a reason, in the target's config and in the report.

---

## 2. Notes on the load-bearing ones

### I3 — the band matters more than the direction

Correlation with BST should be **moderate, not zero**. Strong Pokémon really are strong, and a model that denies it is wrong in an obvious way.

- **r near 1.0** — the model is an expensive way to sort by BST. Gates aren't biting; stat magnitude is over-weighted relative to toolkit and typing.
- **r near 0.0** — the model is broken. Usually gates are mis-specified and disqualifying strong species for spurious reasons, or the score is dominated by a noisy term.
- **r ≈ 0.3–0.6** — the model has found real specialists without pretending base stats are irrelevant.

Report r alongside n and a scatter plot. A correlation without its scatter hides bimodality, and hack rosters are frequently bimodal.

### I6 — the only direct test of the core claim

The claim is that base stats determine the build. I6 tests it directly: perturb each species' base stats by ±15 across the spread, regenerate builds, and measure how many species change their recommended build.

If scrambling the spread leaves recommendations unchanged, **the build generator is reading the role rather than the species**, and every claim about species-specific builds is false regardless of how plausible the output looks. This is the most serious failure in the set and it cannot be patched by reweighting — it means the generation preconditions in `builds.md` §1 aren't wired to real numbers.

Perturbation should preserve BST where practical (shift stats against each other rather than inflating the total), so the test measures sensitivity to *spread shape* rather than to raw power.

### I5 — the check that fails silently

Nothing in the scoring pipeline naturally notices that two recommended teammates both want the game's only Focus Sash. I5 is the only place it surfaces. It also catches mutually exclusive acquisitions — starters, fossils, either/or gifts — which is why the availability parse has to record exclusivity rather than just presence.

### I7 — exclude obligatory STAB, and say what you excluded

If a hack's move table gives every Fire type exactly one good Fire move, that move will appear on nearly every Fire build and there is nothing wrong with the model. Report obligatory STAB fillers as a separate table with their frequencies, and run I7 on the remaining slots. An excluded set that's never published is a loophole; an excluded set that's published is a finding about the hack's move design.

---

## 3. Diagnostic checks — report, don't block

These don't gate release, but they belong in the audit depth of every publication.

**D1 — Low-BST representation.** Every role's top 10 should contain at least one species from the bottom half of the BST distribution. If a role's top 10 is entirely high-BST, either the role is genuinely stat-hungry (sweepers often are — say so) or its gates aren't doing their job.

**D2 — Gate bite.** Report how many species each gate eliminates. A gate that removes nothing isn't encoding a real requirement. A gate that removes 99% is probably mis-specified or referencing a move that doesn't exist in this hack — verify against the hack's own move table before trusting it.

**D3 — Weight sensitivity.** Shift the component weights by ±0.1 and measure how many primary roles churn. Heavy churn means the labels are arbitrary and should be presented as soft rankings rather than hard categories. Mild churn is expected and healthy.

**D4 — Intuition spot-check.** Pick five species whose roles are well understood and confirm the classifier agrees. When it disagrees, work out which is wrong — sometimes the hack really did change something, and that's a finding. Report disagreements either way rather than quietly tuning until they vanish.

**D5 — Open supply per role.** How many members of each role can be simultaneously equipped with a reliable item (see `builds.md` §6). A role with open supply near zero has a hard practical cap on how many the player can field well. This is usually one of the most decision-relevant numbers in the whole analysis.

**D6 — Coverage of the boss set.** For each boss, how many roster members have at least one "Wins" answer in the current pool. A boss with threats that nothing answers is the headline, not a footnote.

---

## 4. What to do when one fails

Do not tune until it passes. Diagnose first — `builds.md` §9 maps each failure signature to its likely cause. Then, in order of preference:

1. **Fix the generation precondition or the gate** that's actually wrong. This is the real fix in most cases.
2. **Fix the input parse.** A surprising number of invariant failures are parse bugs — an unread ability column, a missed ground-item source, a level cap not applied.
3. **Reweight**, only after 1 and 2 are ruled out, and only with the before/after reported.
4. **Change the threshold**, only when the target genuinely differs from the default assumptions — a small roster legitimately can't satisfy I4 at ≥ 3. Record the change and the reason in the target config.

If a check cannot be satisfied, **publish anyway with the failure stated prominently** rather than suppressing the ladder — but say what the failure means for how the output should be used. "I1 fails at 0.31 because this hack has one dominant item tier; treat item recommendations as weaker than the species recommendations" is a usable caveat.

---

## 5. Reporting format

Ship this table with every published ladder, in the audit depth and summarised at the working depth:

| Check | Value | Threshold | Status | Note |
|---|---|---|---|---|
| I1 item concentration | 0.18 (Leftovers) | ≤ 0.25 | Pass | |
| I2 nature concentration | 0.14 (Adamant) | ≤ 0.20 | Pass | |
| I3 BST correlation | 0.46 (n=402) | 0.30–0.60 | Pass | Scatter in audit sheet |
| I4 role depth | min 3 (Cleric @ M2) | ≥ 3 | Pass | Tightest at early milestones |
| I5 team feasibility | 100% | 100% | Pass | 40 teams checked |
| I6 stat sensitivity | 0.34 | ≥ 0.20 | Pass | ±15, BST-preserving |
| I7 move concentration | 0.22 | ≤ 0.30 | Pass | 6 obligatory STAB fillers excluded, listed separately |

Include passed checks. A report that lists only failures doesn't tell the user what was verified.
