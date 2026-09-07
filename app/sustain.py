#!/usr/bin/env python3
"""
HALYARD — the sustain axis.

Ported from the reference app's own model (`score.js`, SUSTAIN section), because
the point of this exercise is to keep that app's behaviour and swap the numbers
underneath. Reimplementing it differently would change what the UI means.

Their reasoning, which the port preserves:

  - A per-slot version saturates: almost everything beats one individual slot,
    so the axis reads 0.82-0.99 for a wall and a glass cannon alike.
  - So the roster is walked SEQUENTIALLY on a single lifebar. Damage taken
    accumulates; healing pays it back per turn. How deep the species gets before
    fainting is what separates a wall from an attacker that survives one hit.
  - The lifebar RESETS at every trainer boundary, because the player heals
    between fights. Carrying damage across a whole checkpoint scored everything
    1-3 and discriminated nothing — the mirror of the saturation problem.
  - Roster order as the fight presents it. Sorting hardest-first is a worst-case
    ordering that zeroes genuine walls on their first slot; the player does not
    choose to lead into the ace.
  - The published axis is the KIT DELTA — this species minus the identical
    species with no kit — because raw depth correlated 0.809 with BST and so
    measured size rather than kit.

What differs, and why it is legitimate: their `tk` and `inPerTurn` come from
their own scoring pass. Mine come from the HALYARD matrix, which already stores
turns-to-KO both directions, raw incoming, and incoming after utility. So the
"with kit" and "bare" arms are read straight off measured cells rather than
recomputed.
"""
import csv, gzip, json, collections, statistics, os, re

OUT = "/home/claude/out"
WORK = "/home/claude/work"

# heal per turn as a fraction of max HP, exactly as the reference model sets it
HEAL_RECOVERY = 0.25     # reliable recovery restores ~50% but costs the turn
HEAL_REGEN    = 0.11     # a third of max HP per switch, amortised
HEAL_LEFTOVER = 0.0625

RECOVERY_TAG = "recovery"
SCREEN_TAG   = "screens"


def heal_per_turn(tags, item, ability):
    h = 0.0
    if RECOVERY_TAG in tags:
        h += HEAL_RECOVERY
    if "regenerator" in (ability or "").lower():
        h += HEAL_REGEN
    if "LEFTOVERS" in (item or "") or "BERRY_JUICE" in (item or ""):
        h += HEAL_LEFTOVER
    return h


def walk(seq, heal):
    """Sequential lifebar walk. seq entries are (trainer, tk, incoming).
    Returns how many slots deep the species gets before fainting, with the bar
    resetting at each trainer boundary."""
    hp, dep, cur = 1.0, 0, None
    for trainer, tk, inc in seq:
        if trainer != cur:
            cur = trainer
            hp = 1.0
        loss = max(0.0, tk * inc - tk * heal)
        if hp - loss <= 0:
            continue                    # faints here; next trainer is a fresh bar
        hp -= loss
        dep += 1
    return dep


def main():
    # ceiling build per (species, checkpoint), to know item/ability/tags
    ceil = {}
    for r in csv.DictReader(open(f"{OUT}/05_valuation.tsv"), delimiter="\t"):
        ceil[(r["species_const"], int(r["checkpoint"]))] = r

    out = {}
    for cp in range(1, 20):
        p = f"{OUT}/04_matchups_cp{cp}.tsv.gz"
        if not os.path.exists(p):
            continue
        # per (species, anchor) sequence of slots in roster order
        seqs = collections.defaultdict(list)
        meta = {}
        with gzip.open(p, "rt", encoding="utf-8") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                if r["anchor"] != "candidate":
                    continue
                key = (r["species_const"], r["ability"], r["nature"], r["item"], r["moves"])
                try:
                    tk = min(float(r["my_turns_to_ko"]), 20.0)
                    inc_kit = float(r["incoming_after_utility"])
                    inc_bare = float(r["their_dmg_frac"])
                except ValueError:
                    continue
                seqs[key].append((r["boss_trainer_id"], int(r["boss_slot"]),
                                  tk, inc_kit, inc_bare))
                meta[key] = r["utility_tags"]

        for key, rows in seqs.items():
            sc, ability, nature, item, moves = key
            c = ceil.get((sc, cp))
            # only the published ceiling build carries the axis
            if not c or c["ability"] != ability or c["nature"] != nature \
               or c["item"] != item or c["moves"] != moves:
                continue
            rows.sort(key=lambda t: (t[0], t[1]))     # roster order as presented
            tags = meta.get(key, "")
            h = heal_per_turn(tags, item, ability)
            kit  = walk([(t[0], t[2], t[3]) for t in rows], h)
            bare = walk([(t[0], t[2], t[4]) for t in rows], 0.0)
            n = max(1, len(rows))
            sus, sus_bare = kit / n, bare / n
            haz = 0.0
            m = re.search(r"hazard:([a-z+]+)", tags)
            n_haz = len(m.group(1).split("+")) if m else 0
            try:
                haz = statistics.mean(float(x) for x in [rows and "0"] ) if False else 0.0
            except Exception:
                haz = 0.0
            out.setdefault(sc, {})[cp] = {
                "sustain": round(sus, 4),
                "sustain_bare": round(sus_bare, 4),
                "sustain_kit": round(sus - sus_bare, 4),
                "sweep_depth": kit,
                "n_slots": n,
                "has_recovery": 1 if RECOVERY_TAG in tags else 0,
                "has_screens": 1 if SCREEN_TAG in tags else 0,
                "n_hazards": n_haz,
                "heal_per_turn": round(h, 4),
            }
        print(f"  cp{cp:>2} {len(out) and sum(1 for s in out if cp in out[s]):>5} species")

    json.dump(out, open(f"{WORK}/sustain.json", "w"))
    # sanity: does the kit delta actually discriminate, and is it decorrelated
    # from BST the way the reference model intended?
    sp = {r["species_const"]: r for r in
          csv.DictReader(open(f"{OUT}/01_species.tsv"), delimiter="\t")}
    xs, ys, raw = [], [], []
    for sc, d in out.items():
        if 19 not in d:
            continue
        xs.append(d[19]["sustain_kit"]); raw.append(d[19]["sustain"])
        ys.append(int(sp[sc]["bst"]))
    def corr(a, b):
        ma, mb = statistics.mean(a), statistics.mean(b)
        num = sum((x-ma)*(y-mb) for x, y in zip(a, b))
        den = (sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))**0.5
        return num/den if den else 0
    print()
    print(f"species with a sustain value : {len(out)}")
    print(f"kit delta  mean {statistics.mean(xs):.3f}  range {min(xs):.3f}..{max(xs):.3f}")
    print(f"r(raw sustain, BST) = {corr(raw, ys):+.3f}   <- reference measured 0.809, which is why")
    print(f"r(kit delta,   BST) = {corr(xs, ys):+.3f}   <- the published axis is the delta")


if __name__ == "__main__":
    main()
