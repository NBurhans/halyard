#!/usr/bin/env python3
"""
audit.py — schema-agnostic profiler and integrity checker for Pokemon ROM hack data.

Run this on every file before analysis. It does not know your schema; it reports
what is there and flags the structural problems that silently corrupt aggregates.

Usage:
  python audit.py profile <file> [--sheet NAME]
      Column inventory, dtypes, nulls, ranges, placeholder scan.

  python audit.py ids <file> --col ID_COLUMN
      Duplicate IDs, gaps in the index range, zero-slot contents.

  python audit.py range <file> --col COLUMN --min 1 --max 255
      Values outside a legal range.

  python audit.py refs <child.csv> --col MOVE_ID <parent.csv> --parent-col ID
      Orphan references from child into parent (referential integrity).

  python audit.py stats <file> --cols hp,atk,def,spa,spd,spe [--total-col BST]
      Stat-block specific checks: identical-stat dummy rows, BST arithmetic,
      range violations, distribution shape.

Reads .csv, .tsv, .json, .xlsx. Exit code is 0 always; findings go to stdout.
"""

import argparse
import json
import math
import os
import re
import sys

try:
    import pandas as pd
except ImportError:
    sys.exit("pandas required: pip install pandas --break-system-packages")

PLACEHOLDER_PATTERNS = [
    r"^\?+$", r"^-+$", r"^_+$", r"^$",
    r"^missingno$", r"^dummy$", r"^none$", r"^null$", r"^n/?a$",
    r"^unused\d*$", r"^placeholder$", r"^temp$", r"^tbd$", r"^xxx+$",
    r"^species_none$", r"^move_none$", r"^item_none$",
]
PLACEHOLDER_RE = re.compile("|".join(PLACEHOLDER_PATTERNS), re.IGNORECASE)


# ---------- loading ----------

def load(path, sheet=None):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".csv",):
        return pd.read_csv(path, encoding_errors="replace")
    if ext in (".tsv", ".tab"):
        return pd.read_csv(path, sep="\t", encoding_errors="replace")
    if ext in (".xlsx", ".xlsm", ".xls"):
        xl = pd.ExcelFile(path)
        if sheet is None and len(xl.sheet_names) > 1:
            print(f"NOTE: workbook has {len(xl.sheet_names)} sheets: "
                  f"{xl.sheet_names}. Profiling '{xl.sheet_names[0]}'. "
                  f"Use --sheet to pick another; check the others too.\n")
        return xl.parse(sheet or 0)
    if ext == ".json":
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, dict):
            print(f"NOTE: JSON top-level keys: {list(data.keys())[:20]}")
            for v in data.values():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    return pd.json_normalize(v)
            return pd.json_normalize(data)
        return pd.json_normalize(data)
    sys.exit(f"Unsupported extension: {ext}")


def is_text(s):
    """Text-column test that works across pandas versions.

    pandas <3 gives text columns dtype 'object'; pandas 3 gives them 'str'.
    Checking for 'object' alone silently skips every text column on pandas 3,
    which makes the placeholder and whitespace scans report a false all-clear.
    """
    return not (pd.api.types.is_numeric_dtype(s)
                or pd.api.types.is_datetime64_any_dtype(s)
                or pd.api.types.is_bool_dtype(s))


def rule(title):
    print(f"\n{'=' * 62}\n{title}\n{'=' * 62}")


# ---------- commands ----------

def cmd_profile(args):
    df = load(args.file, args.sheet)
    rule(f"PROFILE  {os.path.basename(args.file)}")
    print(f"rows: {len(df)}    columns: {len(df.columns)}")

    print(f"\n{'column':<28}{'dtype':<10}{'nulls':>7}{'unique':>8}  range / sample")
    print("-" * 96)
    for c in df.columns:
        s = df[c]
        nulls = int(s.isna().sum())
        uniq = int(s.nunique(dropna=True))
        if pd.api.types.is_numeric_dtype(s) and s.notna().any():
            detail = f"min={s.min():g}  max={s.max():g}  mean={s.mean():.2f}"
        else:
            vals = s.dropna().astype(str).unique()[:3]
            detail = ", ".join(v[:18] for v in vals)
        print(f"{str(c)[:27]:<28}{str(s.dtype):<10}{nulls:>7}{uniq:>8}  {detail}")

    # placeholder scan
    hits = []
    for c in df.columns:
        if is_text(df[c]):
            mask = df[c].astype(str).str.strip().apply(
                lambda v: bool(PLACEHOLDER_RE.match(v)))
            if mask.any():
                hits.append((c, int(mask.sum()),
                             df.loc[mask, c].astype(str).unique()[:4].tolist()))
    rule("PLACEHOLDER SCAN")
    if hits:
        for c, n, examples in hits:
            print(f"  [FLAG] {c}: {n} placeholder-like values  e.g. {examples}")
        print("\n  These are likely unused slots, not design decisions.")
        print("  Decide explicitly whether to exclude them, and record it.")
    else:
        print("  clean: no placeholder-pattern values found")

    # fully duplicated rows
    dupes = int(df.duplicated().sum())
    rule("DUPLICATE ROWS")
    print(f"  {'[FLAG] ' if dupes else 'clean: '}{dupes} fully duplicated rows")

    # whitespace contamination
    ws = [c for c in df.columns if is_text(df[c])
          and df[c].astype(str).str.contains(r"^\s|\s$", regex=True, na=False).any()]
    rule("WHITESPACE")
    print(f"  {'[FLAG] leading/trailing whitespace in: ' + ', '.join(ws) if ws else 'clean'}")


def cmd_ids(args):
    df = load(args.file, args.sheet)
    col = args.col
    if col not in df.columns:
        sys.exit(f"column '{col}' not found. available: {list(df.columns)}")
    rule(f"ID AUDIT  {os.path.basename(args.file)} :: {col}")

    s = df[col]
    dupes = s[s.duplicated(keep=False)].sort_values()
    if len(dupes):
        print(f"  [FLAG] {s.duplicated().sum()} duplicate IDs "
              f"({dupes.nunique()} distinct values affected)")
        for v in dupes.unique()[:15]:
            print(f"      id {v}: rows {df.index[s == v].tolist()}")
    else:
        print("  clean: no duplicate IDs")

    if pd.api.types.is_numeric_dtype(s):
        lo, hi = int(s.min()), int(s.max())
        missing = sorted(set(range(lo, hi + 1)) - set(s.dropna().astype(int)))
        print(f"\n  range: {lo}..{hi}   present: {s.nunique()}   "
              f"expected if contiguous: {hi - lo + 1}")
        if missing:
            print(f"  [FLAG] {len(missing)} gaps in the ID range")
            print(f"      {missing[:25]}{' ...' if len(missing) > 25 else ''}")
            print("      Check the source: intentional removal or parse loss?")
        else:
            print("  clean: ID range is contiguous")

        if (s == 0).any():
            rule("ZERO SLOT")
            print(df[s == 0].to_string())
            print("\n  Slot 0 is often a null/dummy entry. Confirm before including"
                  "\n  it in any aggregate — it drags means toward zero.")


def cmd_range(args):
    df = load(args.file, args.sheet)
    col = args.col
    rule(f"RANGE CHECK  {col} ∈ [{args.min}, {args.max}]")
    s = pd.to_numeric(df[col], errors="coerce")
    bad = df[(s < args.min) | (s > args.max)]
    coerced = int(s.isna().sum() - df[col].isna().sum())
    if coerced:
        print(f"  [FLAG] {coerced} values could not be read as numbers")
    if len(bad):
        print(f"  [FLAG] {len(bad)} values outside legal range")
        print(bad.to_string()[:3000])
    else:
        print("  clean: all values in range")


def cmd_refs(args):
    child = load(args.child, args.sheet)
    parent = load(args.parent)
    rule(f"REFERENTIAL INTEGRITY\n  {os.path.basename(args.child)}.{args.col}"
         f"  ->  {os.path.basename(args.parent)}.{args.parent_col}")

    cvals = child[args.col].dropna()
    pvals = set(parent[args.parent_col].dropna())
    orphan_mask = ~cvals.isin(pvals)
    orphans = cvals[orphan_mask]

    if len(orphans):
        print(f"  [FLAG] {len(orphans)} orphan references "
              f"({orphans.nunique()} distinct undefined targets)")
        vc = orphans.value_counts()
        for val, n in vc.head(20).items():
            rows = child.index[child[args.col] == val].tolist()[:6]
            print(f"      {val!r}  referenced {n}x  (rows {rows}"
                  f"{' ...' if n > 6 else ''})")
        print("\n  Each of these is a dangling pointer in the hack — likely a")
        print("  real bug worth reporting to the author, not just a data issue.")
    else:
        print(f"  clean: all {len(cvals)} references resolve")

    unused = pvals - set(cvals)
    print(f"\n  unreferenced parent entries: {len(unused)}"
          f"{' — check for unobtainable/unused content' if unused else ''}")


def cmd_stats(args):
    df = load(args.file, args.sheet)
    cols = [c.strip() for c in args.cols.split(",")]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        sys.exit(f"columns not found: {missing}\navailable: {list(df.columns)}")

    rule(f"STAT BLOCK AUDIT  ({', '.join(cols)})")
    block = df[cols].apply(pd.to_numeric, errors="coerce")

    # range
    bad = block[(block < 1) | (block > 255)].dropna(how="all")
    if len(bad):
        print(f"  [FLAG] {len(bad)} rows with stats outside 1..255 "
              f"(values >255 wrap when written to ROM)")
        print(bad.head(15).to_string())
    else:
        print("  clean: all stats within legal 1..255")

    # identical-stat dummy rows
    identical = block[block.nunique(axis=1) == 1].dropna(how="all")
    print()
    if len(identical):
        print(f"  [FLAG] {len(identical)} rows where all six stats are identical")
        print("      Strong signal of unused/dummy slots. Inspect before including:")
        print(identical.head(15).to_string())
    else:
        print("  clean: no all-identical stat rows")

    bst = block.sum(axis=1)
    if args.total_col and args.total_col in df.columns:
        stated = pd.to_numeric(df[args.total_col], errors="coerce")
        mism = df[(bst - stated).abs() > 0.5]
        print()
        if len(mism):
            print(f"  [FLAG] {len(mism)} rows where stated total != sum of stats")
            print("      Usually a stale total left after an edit.")
            print(mism.head(15).to_string()[:2000])
        else:
            print("  clean: stated totals match computed sums")

    rule("BST DISTRIBUTION")
    q = bst.describe(percentiles=[.1, .25, .5, .75, .9])
    print(q.to_string())
    # crude bimodality signal
    hist, edges = pd.cut(bst, bins=12, retbins=True)
    counts = hist.value_counts().sort_index()
    print("\n  histogram:")
    peak = counts.max()
    for interval, n in counts.items():
        bar = "#" * max(1, int(28 * n / peak)) if n else ""
        print(f"    {interval.left:6.0f}-{interval.right:<6.0f} {n:>4}  {bar}")
    # Multimodality proxy. Pad with zeros so the first and last bins can
    # register as modes — a legendary/pseudo tier lands in the top bin almost
    # every time, and an unpadded scan would miss precisely the case that
    # matters most for ROM hack rosters.
    vals = [0] + counts.tolist() + [0]
    peaks = sum(1 for i in range(1, len(vals) - 1)
                if vals[i] >= vals[i - 1] and vals[i] >= vals[i + 1]
                and vals[i] > peak * 0.25)
    if peaks > 1:
        print(f"\n  [FLAG] distribution appears multimodal ({peaks} local peaks).")
        print("      A single mean is misleading here — report the modes separately.")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("profile"); pr.add_argument("file")
    pr.add_argument("--sheet"); pr.set_defaults(func=cmd_profile)

    pi = sub.add_parser("ids"); pi.add_argument("file")
    pi.add_argument("--col", required=True); pi.add_argument("--sheet")
    pi.set_defaults(func=cmd_ids)

    pg = sub.add_parser("range"); pg.add_argument("file")
    pg.add_argument("--col", required=True)
    pg.add_argument("--min", type=float, default=1)
    pg.add_argument("--max", type=float, default=255)
    pg.add_argument("--sheet"); pg.set_defaults(func=cmd_range)

    pf = sub.add_parser("refs"); pf.add_argument("child"); pf.add_argument("parent")
    pf.add_argument("--col", required=True)
    pf.add_argument("--parent-col", required=True)
    pf.add_argument("--sheet"); pf.set_defaults(func=cmd_refs)

    ps = sub.add_parser("stats"); ps.add_argument("file")
    ps.add_argument("--cols", required=True)
    ps.add_argument("--total-col"); ps.add_argument("--sheet")
    ps.set_defaults(func=cmd_stats)

    args = p.parse_args()
    args.func(args)
    print()


if __name__ == "__main__":
    main()
