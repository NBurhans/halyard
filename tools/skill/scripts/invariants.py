#!/usr/bin/env python3
"""
invariants.py — the release-blocking checks on a recommended-build set.

The requirement that no single item, nature or move should dominate the
recommendations is a hard constraint, not an aspiration. These are its
falsifiable tests. See references/invariants.md for what each one means and
what to do when it fails.

Use as a module:

    from invariants import run_invariants, report
    res = run_invariants(builds, teams=teams, item_copies=copies,
                         perturbation_churn=0.34,
                         obligatory_stab={"MOVE_FLAMETHROWER"})
    print(report(res))

Expected `builds` columns (rename yours or pass a column map):

    species        species identifier
    milestone      milestone identifier
    role           primary role
    score          final rank score for the recommended build
    bst            base stat total
    item           held item of the recommended build ("" or None for none)
    nature         nature of the recommended build
    moves          list/tuple of move identifiers, or a comma-separated string

I6 cannot be computed from a finished table — it requires regenerating builds
against perturbed stats. Compute the churn fraction in the pipeline and pass it
in as `perturbation_churn`; if omitted, I6 is reported as NOT RUN, which is not
the same as a pass and must not be presented as one.

CLI:

    python invariants.py builds.csv --teams teams.csv --item-copies items.csv
"""

import argparse
import json
import math

try:
    import pandas as pd
except ImportError:
    raise SystemExit("pandas required: pip install pandas --break-system-packages")


# Defaults tuned against a roster of roughly 400 obtainable species.
# Overriding a threshold to make a failing check pass is not a fix — record
# any change and its reason in the target config and in the report.
THRESHOLDS = {
    "I1_item_max": 0.25,
    "I2_nature_max": 0.20,
    "I3_bst_corr_min": 0.30,
    "I3_bst_corr_max": 0.60,
    "I4_role_depth_min": 3,
    "I4_within_frac": 0.10,
    "I6_churn_min": 0.20,
    "I7_move_max": 0.30,
}


def _frac_top(series):
    """Return (value, fraction) for the most common non-null entry."""
    s = series.dropna()
    s = s[s.astype(str).str.len() > 0]
    if len(s) == 0:
        return None, 0.0
    counts = s.value_counts()
    return counts.index[0], float(counts.iloc[0]) / len(s)


def _as_move_list(v):
    if isinstance(v, (list, tuple, set)):
        return list(v)
    if isinstance(v, str):
        return [m.strip() for m in v.split(",") if m.strip()]
    return []


def i1_item_concentration(builds, thresholds):
    item, frac = _frac_top(builds["item"])
    return {
        "id": "I1", "name": "item concentration",
        "value": round(frac, 4), "detail": item,
        "threshold": f"<= {thresholds['I1_item_max']}",
        "passed": frac <= thresholds["I1_item_max"],
        "note": "Builds with no item are excluded from the denominator.",
    }


def i2_nature_concentration(builds, thresholds):
    nature, frac = _frac_top(builds["nature"])
    return {
        "id": "I2", "name": "nature concentration",
        "value": round(frac, 4), "detail": nature,
        "threshold": f"<= {thresholds['I2_nature_max']}",
        "passed": frac <= thresholds["I2_nature_max"],
        "note": "",
    }


def i3_bst_correlation(builds, thresholds):
    d = builds[["score", "bst"]].dropna()
    n = len(d)
    if n < 3:
        return {"id": "I3", "name": "BST correlation", "value": None,
                "detail": f"n={n}", "threshold": "insufficient data",
                "passed": None, "note": "Too few rows to correlate."}
    r = float(d["score"].corr(d["bst"]))
    lo, hi = thresholds["I3_bst_corr_min"], thresholds["I3_bst_corr_max"]
    ok = (not math.isnan(r)) and lo <= abs(r) <= hi
    if math.isnan(r):
        note = "Correlation undefined — one column is constant."
    elif abs(r) > hi:
        note = "Too high: gates are not biting; stat magnitude over-weighted."
    elif abs(r) < lo:
        note = "Too low: gates likely mis-specified, or the score is noise-dominated."
    else:
        note = "In band."
    return {
        "id": "I3", "name": "BST correlation",
        "value": None if math.isnan(r) else round(r, 4), "detail": f"n={n}",
        "threshold": f"{lo}-{hi} (absolute)", "passed": ok, "note": note,
    }


def i4_role_depth(builds, thresholds):
    """Every (role, milestone) needs >= N species within X% of the leader."""
    worst = None
    frac = thresholds["I4_within_frac"]
    rows = []
    for (ms, role), grp in builds.groupby(["milestone", "role"]):
        leader = grp["score"].max()
        if not (leader > 0):
            depth = 0
        else:
            depth = int((grp["score"] >= leader * (1 - frac)).sum())
        rows.append((ms, role, depth))
        if worst is None or depth < worst[2]:
            worst = (ms, role, depth)
    passed = worst is not None and worst[2] >= thresholds["I4_role_depth_min"]
    detail = "no roles found" if worst is None else f"{worst[1]} @ {worst[0]}"
    return {
        "id": "I4", "name": "role depth",
        "value": None if worst is None else worst[2], "detail": detail,
        "threshold": f">= {thresholds['I4_role_depth_min']} within {int(frac*100)}% of leader",
        "passed": passed,
        "note": f"{sum(1 for r in rows if r[2] < thresholds['I4_role_depth_min'])}"
                f" of {len(rows)} role-milestone pairs below threshold.",
    }


def i5_team_feasibility(teams, item_copies):
    """Every recommended team must be simultaneously equippable.

    teams: DataFrame with columns team_id, species, item (one row per member).
    item_copies: dict {item: copies} or DataFrame with columns item, copies.
                 Missing items are treated as unlimited, which is permissive —
                 an incomplete copy-count parse makes this check weaker, not
                 stronger, so verify the parse before trusting a pass.
    """
    if teams is None:
        return {"id": "I5", "name": "team feasibility", "value": None,
                "detail": "no teams supplied", "threshold": "100%",
                "passed": None, "note": "NOT RUN."}
    if isinstance(item_copies, pd.DataFrame):
        copies = dict(zip(item_copies["item"], item_copies["copies"]))
    else:
        copies = dict(item_copies or {})

    bad = []
    for tid, grp in teams.groupby("team_id"):
        used = grp["item"].dropna()
        used = used[used.astype(str).str.len() > 0].value_counts()
        for item, n in used.items():
            avail = copies.get(item, math.inf)
            if n > avail:
                bad.append(f"team {tid}: {n}x {item} (have {avail})")
        if grp["species"].duplicated().any():
            bad.append(f"team {tid}: duplicate species")

    total = teams["team_id"].nunique()
    n_bad = len({b.split(':')[0] for b in bad})
    rate = 1.0 if total == 0 else (total - n_bad) / total
    return {
        "id": "I5", "name": "team feasibility",
        "value": round(rate, 4), "detail": f"{total} teams checked",
        "threshold": "100%", "passed": rate == 1.0,
        "note": "; ".join(bad[:5]) + (" …" if len(bad) > 5 else ""),
    }


def i6_stat_sensitivity(perturbation_churn, thresholds):
    if perturbation_churn is None:
        return {"id": "I6", "name": "stat sensitivity", "value": None,
                "detail": "", "threshold": f">= {thresholds['I6_churn_min']}",
                "passed": None,
                "note": "NOT RUN. Regenerate builds against perturbed stats and "
                        "pass the churn fraction in. A missing I6 is not a pass."}
    return {
        "id": "I6", "name": "stat sensitivity",
        "value": round(float(perturbation_churn), 4), "detail": "",
        "threshold": f">= {thresholds['I6_churn_min']}",
        "passed": float(perturbation_churn) >= thresholds["I6_churn_min"],
        "note": "Direct test that build generation reads the stat spread.",
    }


def i7_move_concentration(builds, thresholds, obligatory_stab=None):
    obligatory = set(obligatory_stab or ())
    rows = []
    for mv in builds["moves"]:
        rows.extend(m for m in _as_move_list(mv) if m not in obligatory)
    if not rows:
        return {"id": "I7", "name": "move concentration", "value": None,
                "detail": "", "threshold": f"<= {thresholds['I7_move_max']}",
                "passed": None, "note": "No movesets supplied."}
    counts = pd.Series(rows).value_counts()
    n_builds = len(builds)
    top_move = counts.index[0]
    frac = float(counts.iloc[0]) / n_builds     # share of builds, not of slots
    return {
        "id": "I7", "name": "move concentration",
        "value": round(frac, 4), "detail": top_move,
        "threshold": f"<= {thresholds['I7_move_max']}",
        "passed": frac <= thresholds["I7_move_max"],
        "note": f"{len(obligatory)} obligatory STAB filler(s) excluded"
                + (f": {sorted(obligatory)}" if obligatory else "")
                + ". Publish that list alongside this result.",
    }


def run_invariants(builds, teams=None, item_copies=None,
                   perturbation_churn=None, obligatory_stab=None,
                   thresholds=None):
    """Run I1-I7. Returns a list of result dicts."""
    t = dict(THRESHOLDS)
    t.update(thresholds or {})

    required = {"species", "milestone", "role", "score", "bst"}
    missing = required - set(builds.columns)
    if missing:
        raise ValueError(f"builds is missing columns: {sorted(missing)}")
    for col in ("item", "nature", "moves"):
        if col not in builds.columns:
            builds = builds.assign(**{col: None})

    return [
        i1_item_concentration(builds, t),
        i2_nature_concentration(builds, t),
        i3_bst_correlation(builds, t),
        i4_role_depth(builds, t),
        i5_team_feasibility(teams, item_copies),
        i6_stat_sensitivity(perturbation_churn, t),
        i7_move_concentration(builds, t, obligatory_stab),
    ]


def blocking_failures(results):
    """Checks that failed outright. A None (NOT RUN) is not a failure, but it
    is also not a pass — see `not_run`."""
    return [r for r in results if r["passed"] is False]


def not_run(results):
    return [r for r in results if r["passed"] is None]


def report(results, fmt="md"):
    """Render the results table that ships with every published ladder."""
    if fmt == "json":
        return json.dumps(results, indent=1)
    lines = ["| Check | Value | Threshold | Status | Note |",
             "|---|---|---|---|---|"]
    for r in results:
        status = {True: "Pass", False: "**FAIL**", None: "NOT RUN"}[r["passed"]]
        val = "—" if r["value"] is None else r["value"]
        det = f" ({r['detail']})" if r.get("detail") else ""
        lines.append(f"| {r['id']} {r['name']} | {val}{det} | "
                     f"{r['threshold']} | {status} | {r.get('note','')} |")
    fails = blocking_failures(results)
    skipped = not_run(results)
    lines.append("")
    if fails:
        lines.append(f"**{len(fails)} blocking failure(s): "
                     f"{', '.join(r['id'] for r in fails)}.** Diagnose before "
                     "publishing — see references/builds.md §9 for the failure "
                     "signatures, and do not tune thresholds to make a check pass.")
    else:
        lines.append("No blocking failures.")
    if skipped:
        lines.append(f"Not run: {', '.join(r['id'] for r in skipped)}. "
                     "State this explicitly wherever the ladder is published; "
                     "an unrun check is not a passed check.")
    return "\n".join(lines)


def _read(path):
    if path is None:
        return None
    if path.endswith((".tsv", ".tab")):
        return pd.read_csv(path, sep="\t")
    if path.endswith((".xlsx", ".xlsm")):
        return pd.read_excel(path)
    return pd.read_csv(path)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("builds", help="recommended builds table (csv/tsv/xlsx)")
    p.add_argument("--teams", default=None, help="team_id, species, item")
    p.add_argument("--item-copies", default=None, help="item, copies")
    p.add_argument("--churn", type=float, default=None,
                   help="I6 perturbation churn fraction, computed in the pipeline")
    p.add_argument("--obligatory-stab", nargs="*", default=None,
                   help="moves excluded from I7, reported separately")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    res = run_invariants(_read(a.builds), teams=_read(a.teams),
                         item_copies=_read(a.item_copies),
                         perturbation_churn=a.churn,
                         obligatory_stab=a.obligatory_stab)
    print(report(res, fmt="json" if a.json else "md"))
    raise SystemExit(1 if blocking_failures(res) else 0)


if __name__ == "__main__":
    main()
