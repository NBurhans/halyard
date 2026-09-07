#!/usr/bin/env python3
"""
export_bundle.py — write a whole database as a compact, self-describing TSV bundle.

WHY TSV AND NOT JSON
`export_dataset.py` is right for a single analysis output. It is wrong for a
whole database, because JSON records repeat every key name on every row. A
92,000-row movepool table spends most of its bytes re-writing the string
"move_id". The same content as TSV puts column names on one header line and
routinely comes out 8-12x smaller, while staying trivially parseable:

    import pandas as pd
    df = pd.read_csv('01_species.tsv', sep='\t')

Use this when the deliverable is "here is the dataset" rather than "here is a
result": consolidating a project, handing files to a future session, or any time
the JSON exports have accumulated into more volume than the person wants to
carry around.

FOLD ONE-TO-MANY RELATIONS INTO THE PARENT
The second big saving is structural. Three tables keyed on species — level-up
moves, TM moves, egg moves — repeat the species key ~92,000 times between them.
Encoded as columns on the species row they cost a fraction of that:

    levelup   move_id:level,move_id:level,...
    tm, egg   comma-separated ids
    evo       method:target:param;...

`encode_pairs` and `encode_list` below do this. Document the encoding in the
README, because a column of "33:1,45:3" is unreadable without it.

WHAT THE BUNDLE MUST CONTAIN
A bundle is not a folder of tables. It is tables plus the context needed to
trust them:
  - numbered files, so reading order is obvious;
  - a `00_README.md` carrying provenance, parse gotchas, the confidence split,
    validation numbers, corrections made, and what is stale;
  - an explicit list of superseded files that were dropped, with reasons.
A bundle that silently omits a superseded version looks like data loss.

Usage:
    from export_bundle import Bundle, encode_pairs, encode_list
    b = Bundle("/mnt/user-data/outputs/<codename>")
    b.add("01_species.tsv", species_df, "movepools folded in; see README")
    b.add("07_scores.tsv", scores_df, "headline results")
    b.readme(title="...", files_note="...", gotchas=[...], confidence={...},
             validation=val_df, corrections=[...], stale=[...], superseded=[...])
    b.verify({"01_species.tsv": 1534, "07_scores.tsv": 1026})
"""

import os, glob, math
try:
    import pandas as pd
except ImportError:
    raise SystemExit("pandas required: pip install pandas --break-system-packages")


def encode_pairs(seq, sep=",", inner=":"):
    """[(33,1),(45,3)] or flat [33,1,45,3] -> '33:1,45:3'"""
    if seq is None: return ""
    s = list(seq)
    if s and not isinstance(s[0], (list, tuple)):
        s = [(s[i], s[i + 1]) for i in range(0, len(s) - 1, 2)]
    return sep.join(f"{a}{inner}{b}" for a, b in s)


def encode_list(seq, sep=","):
    """[4,7,12] -> '4,7,12'"""
    return "" if seq is None else sep.join(str(x) for x in seq)


def decode_pairs(s, sep=",", inner=":"):
    if not isinstance(s, str) or not s: return []
    return [tuple(p.split(inner)) for p in s.split(sep)]


def decode_list(s, sep=",", cast=int):
    if not isinstance(s, str) or not s: return []
    return [cast(x) for x in s.split(sep)]


class Bundle:
    def __init__(self, outdir):
        self.dir = outdir
        os.makedirs(outdir, exist_ok=True)
        self.files = []

    def add(self, name, df, note=""):
        """Write one TSV. Numbered names keep reading order obvious."""
        path = os.path.join(self.dir, name)
        df.to_csv(path, sep="\t", index=False, float_format="%.4g", na_rep="")
        kb = os.path.getsize(path) / 1024
        self.files.append(dict(name=name, rows=len(df), cols=len(df.columns),
                               kb=round(kb, 1), note=note))
        print(f"  {name:28s} {len(df):7d} rows {kb:9.1f} KB  {note}")
        return path

    def readme(self, title, intro="", gotchas=(), confidence=None, validation=None,
               corrections=(), stale=(), superseded=(), assumptions="",
               classification="EXTERNAL", source=None, invariants=None):
        """Write 00_README.md. Every argument here exists because a bundle
        without it is a pile of numbers nobody should trust.

        classification  Bundles are EXTERNAL by construction — self-describing
                        and usable without the source tree. If a bundle would
                        contain run state or anything that needs the target's
                        source present, split it rather than marking it INTERNAL.
        source          Repo and commit/branch the data was parsed from.
        invariants      Markdown table from invariants.report(), where the
                        bundle carries a ranking.
        """
        if classification not in ("INTERNAL", "EXTERNAL"):
            raise ValueError("classification must be INTERNAL or EXTERNAL")
        L = [f"# {title}", "", f"**Classification:** {classification}"]
        if source:
            L.append(f"**Source:** {source}")
        L.append("")
        if intro: L += [intro, ""]
        L += [f"{len(self.files)} tab-separated files plus this README. First line is the header;",
              "read any of them with a split on tab.", "",
              "```python",
              "import pandas as pd",
              f"df = pd.read_csv('{self.files[0]['name'] if self.files else '01_table.tsv'}', sep='\\t')",
              "```", "", "## Files", "",
              "| File | Rows | What it holds |", "|---|---|---|"]
        for f in self.files:
            L.append(f"| `{f['name']}` | {f['rows']:,} | {f['note']} |")
        if gotchas:
            L += ["", "## Parse gotchas — verify each, do not assume", ""]
            L += [f"{i}. {g}" for i, g in enumerate(gotchas, 1)]
        if confidence:
            L += ["", "## Confidence", ""]
            for tier, what in confidence.items():
                L.append(f"- **{tier}** — {what}")
        if validation is not None:
            L += ["", "## Validation", "", validation.to_markdown(index=False)]
        if invariants:
            L += ["", "## Invariants", "", invariants]
        if corrections:
            L += ["", "## Corrections made along the way", ""]
            L += [f"- {c}" for c in corrections]
        if assumptions:
            L += ["", "## Model assumptions", "", assumptions]
        if stale:
            L += ["", "## What is stale", ""]
            L += [f"- {s}" for s in stale]
        if superseded:
            L += ["", "## Superseded files, dropped deliberately", "",
                  "Replaced by later corrected versions; no unique information lost.", ""]
            L += [f"- {s}" for s in superseded]
        p = os.path.join(self.dir, "00_README.md")
        open(p, "w", encoding="utf-8").write("\n".join(L) + "\n")
        print(f"  00_README.md written")
        return p

    def verify(self, expected=None, spot_checks=()):
        """Re-read every file and confirm it round-trips. Never ship unverified."""
        print("\nverification:")
        bad = []
        for f in self.files:
            df = pd.read_csv(os.path.join(self.dir, f["name"]), sep="\t")
            if len(df) != f["rows"]:
                bad.append((f["name"], f["rows"], len(df)))
            if expected and f["name"] in expected and len(df) != expected[f["name"]]:
                bad.append((f["name"], expected[f["name"]], len(df)))
        print(f"  row counts round-trip: {not bad}" + (f"  MISMATCHES {bad}" if bad else ""))
        for label, fn in spot_checks:
            try:
                print(f"  {label}: {fn(self.dir)}")
            except Exception as e:
                print(f"  {label}: FAILED {e}")
        total = sum(os.path.getsize(p) for p in glob.glob(os.path.join(self.dir, "*")))
        print(f"  {len(glob.glob(os.path.join(self.dir,'*')))} files, {total/1048576:.2f} MB total")
        return not bad
