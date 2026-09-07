# app

`index.html` is built by swapping a HALYARD payload into the reference survey UI
and adding a Routes tab.

```
python3 sustain.py       # the sustain axis, from the matchup matrices
python3 transcode.py     # HALYARD TSVs -> the app's 14-table schema -> data.b64
python3 build_app.py     # payload swap + Routes tab -> index.html
```

## Why a transcode rather than a rewrite

The reference app is data-driven against a fixed schema documented by its own
builder. Emitting that schema means the UI code is untouched, so everything that
already worked keeps working. `transcode.py` carries the field maps.

## EV spreads

`cevs` names the stat each 252 goes into, taken from the spread the matrix
actually ran for that track — physical `252 Atk / 252 Spe / 6 HP`, support
`252 HP / 252 Def / 6 SpD`, and so on. It was briefly a hardcoded
`252 / 252 / 4` with no stat names, which is unusable: the whole point of a
spread is which stat it goes into.

## The About tab

Rewritten to describe this pipeline. The reference app's prose was left in place
at first, so the page whose job is to say what to trust was the page carrying the
wrong generation, the wrong form counts, and a stale "move priority is absent".
It now states the real figures and the real limits, including the priority one.

## Deliberately blank

Three fields HALYARD does not compute are sent as null and render as em dashes
rather than being filled with invented numbers:

| field | what it drove |
|---|---|
| `roi`, `ic` | investment cost and return |
| `lv`, `ldw` | lineage value and dead-weight penalty |
| `cspread` | per-checkpoint offensive/defensive EV spread |

## Routes

One row per species, not per encounter slot — a species commonly appears three or
four times on one map across surf, old rod and super rod. Rates are **not summed**:
5% on the surf table and 30% on a fishing table are probabilities in different
tables, so each method keeps its own rate and the level band spans the merged slots.
Rows sort by value, so the best option on a map is first.

## Sustain

Ported from the reference `score.js`, not reinvented — the axis has to keep
meaning the same thing for the UI around it to stay honest. Its design notes are
preserved in `sustain.py`: sequential lifebar, reset at trainer boundaries,
roster order as presented, published as the kit delta.

The one legitimate difference: turns-to-KO and incoming damage are read off
HALYARD's measured matrix cells rather than recomputed.
