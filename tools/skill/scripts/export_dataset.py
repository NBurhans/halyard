#!/usr/bin/env python3
"""
export_dataset.py — write every dataset twice: a readable form and a JSON form.

The JSON is meant to be re-uploaded to the project so a later session can load
it directly instead of re-deriving it. That only works if the file is
self-describing, so each export carries a metadata block recording where the
data came from, how confident it is, and what the columns mean.

Use as a module:

    from export_dataset import export
    export(df, "species_archetypes",
           title="Archetype fit scores per species",
           sources=["speciesData_json.txt", "moveData_json.txt"],
           confidence="Derived",
           classification="EXTERNAL",
           notes="Gates applied before scoring; see roles.md",
           column_docs={"primary_niche": "Highest-scoring archetype after gates"})

Or from the CLI to convert an existing CSV:

    python export_dataset.py in.csv species_archetypes --title "..." --confidence Measured

Outputs into <outdir> (default /mnt/user-data/outputs/datasets):
    <name>.json   machine-readable, with metadata + records
    <name>.csv    readable, opens anywhere
    manifest.json index of every dataset exported this session
"""

import argparse, json, os, datetime, math

try:
    import pandas as pd
except ImportError:
    raise SystemExit("pandas required: pip install pandas --break-system-packages")

DEFAULT_OUT = "/mnt/user-data/outputs/datasets"
CONFIDENCE = {"Measured", "Derived", "Inferred", "Asserted", "Unresolved", "Mixed"}
CLASSIFICATION = {"INTERNAL", "EXTERNAL"}


def _clean(v):
    """JSON has no NaN/Infinity. Emit null so the file stays valid and loadable."""
    if v is None:
        return None
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    if isinstance(v, (bool, int, str)):
        return v
    if hasattr(v, "item"):          # numpy scalar
        try:
            return _clean(v.item())
        except Exception:
            pass
    if pd.isna(v):
        return None
    return str(v)


def export(df, name, title="", sources=None, confidence="Measured", notes="",
           column_docs=None, outdir=DEFAULT_OUT, readable="csv", manifest=True,
           classification="EXTERNAL", milestone=None, invariants=None):
    """Write df as both JSON and a readable file. Returns the paths written.

    classification  INTERNAL (local only, needs the source tree or is run state)
                    or EXTERNAL (self-contained, ships to the repo).
    milestone       Optional milestone id this dataset is gated at. Anything
                    milestone-dependent that omits it is ambiguous later.
    invariants      Optional dict of invariant results (see invariants.py).
    """
    if confidence not in CONFIDENCE:
        raise ValueError(f"confidence must be one of {sorted(CONFIDENCE)}")
    if classification not in CLASSIFICATION:
        raise ValueError(f"classification must be one of {sorted(CLASSIFICATION)}")
    os.makedirs(outdir, exist_ok=True)

    records = [{k: _clean(v) for k, v in row.items()}
               for row in df.to_dict(orient="records")]

    payload = {
        "metadata": {
            "name": name,
            "title": title,
            "generated": datetime.date.today().isoformat(),
            "source_files": sources or [],
            "confidence": confidence,
            "notes": notes,
            "row_count": len(df),
            "columns": list(map(str, df.columns)),
            "column_docs": column_docs or {},
            "classification": classification,
            "milestone": milestone,
            "invariants": invariants or {},
            "schema_version": 2,
        },
        "records": records,
    }

    jpath = os.path.join(outdir, f"{name}.json")
    with open(jpath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    if readable == "csv":
        rpath = os.path.join(outdir, f"{name}.csv")
        df.to_csv(rpath, index=False)
    elif readable == "md":
        rpath = os.path.join(outdir, f"{name}.md")
        with open(rpath, "w", encoding="utf-8") as f:
            f.write(f"# {title or name}\n\n")
            f.write(f"Source: {', '.join(sources or []) or 'n/a'}  \n")
            f.write(f"Confidence: {confidence}  \nClassification: {classification}  \n")
            if milestone is not None:
                f.write(f"Milestone: {milestone}  \n")
            f.write(f"Rows: {len(df)}\n\n")
            if notes:
                f.write(notes + "\n\n")
            f.write(df.to_markdown(index=False))
    else:
        raise ValueError("readable must be 'csv' or 'md'")

    if manifest:
        mpath = os.path.join(outdir, "manifest.json")
        try:
            with open(mpath, encoding="utf-8") as f:
                man = json.load(f)
        except Exception:
            man = {"datasets": []}
        man["datasets"] = [d for d in man["datasets"] if d.get("name") != name]
        man["datasets"].append({
            "name": name, "title": title, "rows": len(df),
            "confidence": confidence, "classification": classification,
            "milestone": milestone, "json": f"{name}.json",
            "readable": os.path.basename(rpath),
            "generated": payload["metadata"]["generated"],
        })
        man["datasets"].sort(key=lambda d: d["name"])
        man["updated"] = datetime.datetime.now().isoformat(timespec="seconds")
        with open(mpath, "w", encoding="utf-8") as f:
            json.dump(man, f, ensure_ascii=False, indent=1)

    print(f"exported {name}: {len(df)} rows -> {jpath} + {rpath}")
    return jpath, rpath


def load(name, outdir=DEFAULT_OUT):
    """Read back a previously exported dataset as (DataFrame, metadata)."""
    path = name if name.endswith(".json") else os.path.join(outdir, f"{name}.json")
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    return pd.DataFrame(payload["records"]), payload["metadata"]


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("infile", help="CSV/TSV/XLSX to convert")
    p.add_argument("name", help="dataset name (no extension)")
    p.add_argument("--title", default="")
    p.add_argument("--sources", nargs="*", default=[])
    p.add_argument("--confidence", default="Measured", choices=sorted(CONFIDENCE))
    p.add_argument("--classification", default="EXTERNAL", choices=sorted(CLASSIFICATION))
    p.add_argument("--milestone", default=None)
    p.add_argument("--notes", default="")
    p.add_argument("--outdir", default=DEFAULT_OUT)
    p.add_argument("--readable", default="csv", choices=["csv", "md"])
    a = p.parse_args()

    ext = os.path.splitext(a.infile)[1].lower()
    if ext in (".xlsx", ".xlsm"):
        df = pd.read_excel(a.infile)
    elif ext in (".tsv", ".tab"):
        df = pd.read_csv(a.infile, sep="\t")
    else:
        df = pd.read_csv(a.infile)

    export(df, a.name, title=a.title, sources=a.sources, confidence=a.confidence,
           notes=a.notes, outdir=a.outdir, readable=a.readable,
           classification=a.classification, milestone=a.milestone)


if __name__ == "__main__":
    main()
