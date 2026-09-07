#!/usr/bin/env python3
"""
Transcode the HALYARD dataset into the reference app's payload schema.

The app is data-driven against a fixed 13-table shape documented by its own
`build_app_data.py`. This emits that exact shape from HALYARD's TSVs, so the UI
code is untouched and only the numbers underneath change.

Field maps, from the app itself:

  F = idx,name,form,ftype,stage,dex,t1,t2,st,ab,lvl,tm,from,into,av,flags
  K = t,v,vf,vo,roi,ic,n,nf,S,T,Y,n2,n2f,n3,n3f,ec,cv,cf,cvo,cn,ci,cnat,cab,
      fab,cevs,lv,ldw,sus,kit,depth,hasRec,hasScr,nHaz,heal,hazChip,csus,ckit,
      cspread,modal,cm,fr,ed,conf,ab,rmean,np

Values are integers scaled x10000. Per-checkpoint arrays run from the species'
earliest checkpoint through 19 — NOT all 19 slots — which is how the app indexes
them.

Deliberately blank, because HALYARD does not compute them and inventing numbers
to fill a UI slot would be worse than an em dash:
  roi, ic          investment cost and return
  lv, ldw          lineage value and dead-weight penalty
  cspread          per-checkpoint offensive/defensive EV spread

Move ids are row order in 01b_moves.tsv, which coincides with the reference's
ids (both derive from source order: id 1 is Pound in each).
"""
import csv, gzip, json, base64, collections, statistics, re, os

OUT = "/home/claude/out"
WORK = "/home/claude/work"
NA = ("NONE", "NA", "UNK", "")

def tsv(p, gz=False):
    op = gzip.open if gz else open
    with op(f"{OUT}/{p}", "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))

def i4(x):
    """4dp float -> int x 10000, matching the reference scaling."""
    if x is None or x in NA:
        return None
    try: return int(round(float(x) * 10000))
    except (ValueError, TypeError): return None

TY = lambda s: s.replace("TYPE_", "").capitalize() if s not in NA else ""

# What core/model/matrix.js actually ran per track. The app previously showed
# "252 / 252 / 4" with no stat names, which is unusable — the whole point of a
# spread is which stat it goes into.
EV_SPREAD = {
    "physical": "252 Atk / 252 Spe / 6 HP",
    "special":  "252 SpA / 252 Spe / 6 HP",
    "mixed":    "252 Atk / 252 SpA / 6 Spe",
    "support":  "252 HP / 252 Def / 6 SpD",
    "floor":    "no EVs",
}
CAT = {"PHYSICAL": "P", "SPECIAL": "S", "STATUS": "-"}


def main():
    species = tsv("01_species.tsv")
    moves   = tsv("01b_moves.tsv")
    avail   = {a["species_const"]: a for a in tsv("01c_availability.tsv")}
    world   = tsv("02_world.tsv")
    trainers= tsv("03_trainers.tsv")
    cps     = tsv("03b_checkpoints.tsv")
    val     = tsv("05_valuation.tsv")
    roles   = tsv("05_roles.tsv")
    sustain = json.load(open(f"{WORK}/sustain.json"))
    names   = json.load(open(f"{WORK}/species_names.json"))
    resolved= json.load(open(f"{WORK}/boss_resolved.json"))
    chart   = json.load(open(f"{WORK}/typechart.json"))

    by_const = {s["species_const"]: s for s in species}
    idx_of  = {s["species_const"]: int(s["internal_index"]) for s in species}
    by_idx  = {int(s["internal_index"]): s for s in species}
    mv_id   = {m["move_const"]: i for i, m in enumerate(moves)}
    mv_name = {m["move_name"]: i for i, m in enumerate(moves) if m["move_name"] not in NA}

    # ---------- mv, ty, ch
    MOVES = {}
    for i, m in enumerate(moves):
        if m["move_name"] in NA: continue
        try: bp = int(m["power"])
        except ValueError: bp = 0
        MOVES[str(i)] = [m["move_name"], TY(m["type"]), CAT.get(m["category"], "-"), bp]
    TYPES = [t for t in chart.keys() if t not in ("???", "Stellar")][:18]
    CHART = [[chart[a]["eff"].get(d, 1) for d in TYPES] for a in TYPES]

    # ---------- cp: order, label, cap, anchor trainer ids, pool size
    pool_at = collections.Counter()
    for a in avail.values():
        if a["in_pool"] == "TRUE" and a["earliest_cp"] != "UNK":
            for c in range(int(a["earliest_cp"]), 20):
                pool_at[c] += 1
    anchors = collections.defaultdict(list)
    TRS, tid_of = [], {}
    for t in trainers:
        if t["role"] == "route" or t["checkpoint"] == "DYNAMIC":
            continue
        tid = f"{t['role']}:{t['trainer_label']}:{t['trainer_id']}"
        tid_of[t["trainer_id"]] = tid
        anchors[int(t["checkpoint"])].append(tid)
        ivs, evs = t["ivs"].split("|"), t["evs"].split("|")
        roster = []
        for i, slot in enumerate(t["roster"].split("|")):
            p = slot.split(":")
            if len(p) < 5: continue
            roster.append([resolved.get(p[0], p[0]), p[1], p[3] if p[3] not in NA else "",
                           p[2] if p[2] not in NA else "",
                           [m for m in (p[5].split(",") if len(p) > 5 else []) if m not in NA],
                           1 if "MEGA" in p[0].upper() else 0])
        TRS.append([tid, t["trainer_label"], t["role"], "fixed",
                    t["min_level"], t["max_level"], roster])
    LABEL = {1:"Pre Roxanne",2:"Pre Rustboro Rival",3:"Pre Brawly",4:"Pre Aqua Museum",
             5:"Pre Route110 Rival",6:"Pre Wattson",7:"Pre MtChimney",8:"Pre Flannery",
             9:"Pre TrickHouse",10:"Pre Norman",11:"Pre Fly",12:"Pre Winona",
             13:"Pre Lilycove Rival",14:"Pre Submarine",15:"Pre Tate and Liza",
             16:"Pre Seafloor",17:"Pre Juan",18:"Pre Victory Road",19:"Champion"}
    CPS = [[int(c["order"]), LABEL.get(int(c["order"]), f"Checkpoint {c['order']}"),
            int(c["level_cap"]), anchors.get(int(c["order"]), []),
            pool_at.get(int(c["order"]), 0)] for c in cps]

    # ---------- tm gates, evolution items
    TMGATE, EVOITEM = {}, {}
    for w in world:
        if w["earliest_gate"] not in NA and w["item_const"].startswith("ITEM_TM"):
            m = re.match(r"^(\d+)", w["earliest_gate"])
            if m:
                mid = mv_name.get(w["item_name"].replace("TM", "").strip())
                if mid: TMGATE[str(mid)] = min(int(m.group(1)), TMGATE.get(str(mid), 99))
        if w["item_const"] not in NA and w["item_name"] not in NA:
            EVOITEM[w["item_const"]] = w["item_name"]

    # ---------- niches and items, index spaces
    NICHES = sorted({r["primary_role"] for r in val} |
                    {r["hybrid_role"] for r in val if r["hybrid_role"] != "NA"} | {"NONE"})
    NI = {n: i for i, n in enumerate(NICHES)}
    ITEMS = sorted({r["item"].replace("ITEM_", "").replace("_", " ").title() for r in val})
    II = {n: i for i, n in enumerate(ITEMS)}

    # ---------- per-species, per-checkpoint valuation, keyed by species then cp
    per = collections.defaultdict(dict)
    for r in val:
        per[r["species_const"]][int(r["checkpoint"])] = r
    # third role fit comes from the roles table's top3 string
    top3 = {}
    for r in roles:
        if r["anchor"] != "candidate": continue
        k = (r["species_const"], int(r["checkpoint"]))
        if k not in top3 or float(r["primary_fit"]) > float(top3[k][0]):
            top3[k] = (float(r["primary_fit"]), r["top3"])

    # ---------- pk: which moves the ceiling used, how many slots each answered,
    #            and which the floor used
    PICKS = collections.defaultdict(dict)
    for cp in range(1, 20):
        p = f"{OUT}/04_matchups_cp{cp}.tsv.gz"
        if not os.path.exists(p): continue
        counts = collections.defaultdict(collections.Counter)
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                if r["anchor"] != "candidate": continue
                counts[r["species_const"]][r["my_best_move"]] += 1
        for sc, cnt in counts.items():
            v = per.get(sc, {}).get(cp)
            if not v: continue
            ceil_moves = [m for m in v["moves"].split(",") if m in mv_name]
            ids   = [mv_name[m] for m in ceil_moves]
            slots = [cnt.get(m, 0) for m in ceil_moves]
            fl    = [mv_name[m] for m in (v.get("floor_moves", "") or "").split(",")
                     if m in mv_name]
            PICKS[str(idx_of[sc])][str(cp)] = [ids, slots, fl]
        print(f"  pk cp{cp:>2}: {len(counts)} species")

    # ---------- val
    VAL = {}
    for sc, bycp in per.items():
        ii = idx_of.get(sc)
        if ii is None: continue
        ec = min(bycp)
        run = [bycp[c] for c in range(ec, 20) if c in bycp]
        if not run: continue
        rated = [r for r in run if r["tier"] != "NR"]
        mean = lambda f: statistics.mean(float(r[f]) for r in rated) if rated else None
        last = run[-1]
        t3 = top3.get((sc, int(last["checkpoint"])), (0, ""))[1].split(";")
        def nth(i):
            if len(t3) > i and ":" in t3[i]:
                role, fit = t3[i].rsplit(":", 1)
                return NI.get(role, NI["NONE"]), i4(fit)
            return NI["NONE"], None
        n2, n2f = nth(1); n3, n3f = nth(2)
        sus = (sustain.get(sc) or {})
        slast = sus.get(str(last["checkpoint"])) or {}
        modal = collections.Counter(r["primary_role"] for r in run).most_common(1)[0][0]
        vorps = [float(r["vorp"]) for r in rated] if rated else []
        VAL[str(ii)] = [
            last["tier"], i4(mean("ceiling_fit")), i4(mean("floor_fit")),
            i4(statistics.mean(vorps)) if vorps else None,
            None, None,                                    # roi, ic — not computed
            NI.get(last["primary_role"], NI["NONE"]), i4(last["ceiling_fit"]),
            i4(last["S"]), i4(last["T"]), i4(last["Y"]),
            n2, n2f, n3, n3f, ec,
            [i4(r["ceiling_fit"]) for r in run],
            [i4(r["floor_fit"]) for r in run],
            [i4(r["vorp"]) if r["tier"] != "NR" else None for r in run],
            [NI.get(r["primary_role"], NI["NONE"]) for r in run],
            [II.get(r["item"].replace("ITEM_", "").replace("_", " ").title(), 0) for r in run],
            last["nature"], last["ability"].replace("ABILITY_", "").replace("_", " ").title(),
            # floor ability: the more common one, which is what a zero-investment
            # build gets without an ability capsule
            (by_const[sc]["ability_1"].replace("ABILITY_", "").replace("_", " ").title()
             if by_const.get(sc, {}).get("ability_1") not in NA else ""),
            # the spread the matrix actually ran for this track, named per stat
            # rather than as three bare numbers
            EV_SPREAD.get(last["track"], "31 IVs, no EVs"),
            None, None,                                    # lv, ldw — not computed
            i4(slast.get("sustain")), i4(slast.get("sustain_kit")),
            int(slast.get("sweep_depth", 0)),
            slast.get("has_recovery", 0), slast.get("has_screens", 0),
            slast.get("n_hazards", 0), i4(slast.get("heal_per_turn")), 0,
            [i4((sus.get(str(r["checkpoint"])) or {}).get("sustain")) for r in run],
            [i4((sus.get(str(r["checkpoint"])) or {}).get("sustain_kit")) for r in run],
            [None for _ in run],                           # cspread — not computed
            modal,
            1 if last.get("cant_miss") == "TRUE" else 0, 0, None,
            last["availability_confidence"], last["entry_reason"],
            i4(statistics.mean(float(r["replacement_fit"]) for r in rated
                               if r["replacement_fit"] != "UNDEFINED")) if rated else None,
            len([x for x in t3 if x]),
        ]

    # ---------- sp
    evolves_from = {}
    for s in species:
        if s["evolutions"] in NA: continue
        for br in s["evolutions"].split("|"):
            p = br.split(":")
            if len(p) >= 3 and p[2] in idx_of:
                evolves_from[p[2]] = idx_of[s["species_const"]]
    def stage(sc, seen=None):
        seen = seen or set()
        if sc in seen or sc not in evolves_from: return 1
        seen.add(sc)
        prev = by_idx.get(evolves_from[sc])
        return 1 + (stage(prev["species_const"], seen) if prev else 0)

    SP = []
    for s in species:
        sc, ii = s["species_const"], int(s["internal_index"])
        lvl = []
        for tok in s["levelup_moves"].split(","):
            if ":" not in tok: continue
            mc, lv = tok.rsplit(":", 1)
            if mc in mv_id and lv.isdigit(): lvl.append([mv_id[mc], int(lv)])
        tm = [mv_id[m.strip()] for m in s["teachable_moves"].split(",")
              if m.strip() in mv_id] if s["teachable_moves"] not in NA else []
        into = []
        if s["evolutions"] not in NA:
            for br in s["evolutions"].split("|"):
                p = br.split(":")
                if len(p) >= 3 and p[2] in idx_of:
                    into.append([p[0], idx_of[p[2]], p[1]])
        av = [x.split(":")[:4] for x in s["wild_availability"].split("|")] \
             if s["wild_availability"] not in NA else []
        a = avail.get(sc, {})
        flags = (1 if s.get("is_starter") == "TRUE" else 0) | \
                (2 if a.get("entry_reason", "").startswith("evolution") is False
                     and "wild" not in a.get("entry_reason", "") else 0)
        full = names.get(sc, s["species_name"])
        form = full[len(s["species_name"]):].lstrip("-") if full != s["species_name"] else ""
        SP.append([ii, s["species_name"], form, s["form_type"], stage(sc),
                   int(s["natdex_num"]) if s["natdex_num"].isdigit() else 0,
                   TY(s["type_1"]), TY(s["type_2"]),
                   [int(s[f"base_{k}"]) for k in ("hp","atk","def","spa","spd","spe")],
                   [s["ability_1"].replace("ABILITY_","").replace("_"," ").title()
                    if s["ability_1"] not in NA else "",
                    s["ability_2"].replace("ABILITY_","").replace("_"," ").title()
                    if s["ability_2"] not in NA else "",
                    s["ability_hidden"].replace("ABILITY_","").replace("_"," ").title()
                    if s["ability_hidden"] not in NA else ""],
                   lvl, tm, evolves_from.get(sc, 0), into, av, flags])

    # ---------- tier thresholds, recut against THIS VORP distribution
    means = sorted(v[3] for v in VAL.values() if v[3] is not None)
    q = lambda p: means[min(len(means)-1, int(len(means)*p))] / 100.0
    TH = [["S+", round(q(.97),2)], ["S", round(q(.92),2)], ["A", round(q(.82),2)],
          ["B", round(q(.65),2)], ["C", round(q(.40),2)], ["D", round(q(.15),2)],
          ["F", -99900]]

    # ---------- rt: read-only route listing. map -> [[speciesIdx, method,
    # levels, rate]], which is exactly what 01_species already encodes.
    routes = collections.defaultdict(list)
    for s_ in species:
        if s_["wild_availability"] in NA: continue
        ii = int(s_["internal_index"])
        for rec in s_["wild_availability"].split("|"):
            p_ = rec.split(":")
            if len(p_) < 2: continue
            mp = p_[0].replace("MAP_", "").replace("_", " ").title()
            routes[mp].append([ii, p_[1] if len(p_) > 1 else "",
                               p_[2] if len(p_) > 2 else "",
                               p_[3] if len(p_) > 3 else ""])
    RT = [[m, sorted(v)] for m, v in sorted(routes.items())]
    print(f"routes: {len(RT)} maps, {sum(len(r[1]) for r in RT)} encounter records")

    D = dict(rt=RT, pk=PICKS, sp=SP, val=VAL, mv=MOVES, ty=TYPES, ch=CHART, cp=CPS,
             tr=TRS, tm=TMGATE, ei=EVOITEM, ni=NICHES, it=ITEMS, th=TH)
    raw = json.dumps(D, separators=(",", ":"), ensure_ascii=False).encode()
    gz = gzip.compress(raw, 9)
    b64 = base64.b64encode(gz).decode()
    open(f"{WORK}/data.b64", "w").write(b64)
    print()
    print(f"species {len(SP)} · valued {len(VAL)} · moves {len(MOVES)} · "
          f"trainers {len(TRS)} · checkpoints {len(CPS)} · niches {len(NICHES)} · items {len(ITEMS)}")
    print(f"tier cuts recut on this VORP distribution: {TH[:6]}")
    print(f"json {len(raw)/1e6:.2f} MB -> gzip {len(gz)/1e3:.0f} KB -> base64 {len(b64)/1e3:.0f} KB")

if __name__ == "__main__":
    main()
