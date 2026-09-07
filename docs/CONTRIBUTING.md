# Working on this

## The four rules that matter

1. **Every number is computed, not recalled.** Memory of base stats, movepools
   or type charts is a hypothesis. Load the file, run the code, show the
   arithmetic. Difficulty hacks exist precisely to break the assumptions you
   would otherwise import.
2. **No information is dropped, ever.** If the source has it, the dataset has
   it. If a field is empty, encode the sentinel — do not omit the column. If a
   row is excluded from an aggregate, name it and the reason.
3. **Ambiguity gets named, not smoothed.** Two files disagreeing is a
   deliverable. A clean answer resting on a silent assumption is a defect.
4. **Verify before presenting.** Re-read every file written, confirm row counts
   round-trip, and decode encoded cells back to something recognisable.

## Before you trust a result

Most defects in this project were silent — nothing errored, the numbers just
came out wrong. The ones that got caught were caught by a check written to fail,
or by a result that failed a smell test. Two habits earned their keep:

- **Check that the pipeline stages are the same vintage.** A stale intermediate
  once caused invariant results to be reported on one current checkpoint and
  eighteen old ones. `core/invariants/phase6a.py` now blocks on this.
- **Distrust a suspiciously clean number.** A sensitivity test returning exactly
  0.0% was comparing a file against itself. A ladder putting a 280-BST
  unevolved species at the top of the wall rankings was measuring against an
  empty baseline.

`docs/INTEGRITY_RECORD.md` lists all eleven defects with cause and resolution.

## Commit messages

No franchise-identifying words. Describe the change in terms of the framework:
"fix map gate merge order", not the target's name.

## Classification

Classify every artifact INTERNAL or EXTERNAL at creation, not at publication.
The test: can this be used by someone who does not have the target's source
tree? If yes, EXTERNAL. When something fits neither, ask — an over-cautious
INTERNAL classification costs nothing but a conversation.
