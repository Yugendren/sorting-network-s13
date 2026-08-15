# E0 experiment freeze

Falsifiable outcome: E0 passes only if the baseline ancestry and B0--B4 tree
remain exact, the live maintained sources retain the comparator-count interval
44--45, all experiment configs hash correctly, seed partitions reproduce and
remain disjoint, the two verifiers and frozen SENSO artifact are unchanged, and
both authorized hosts satisfy the frozen resource boundary.

Run from the repository root on a clean `goal/s13-method-v1` commit:

```sh
make method-e0
make evidence-check
```

`tools/e0_method_gate.py` records the source commit, repository/worktree state,
baseline inventory replay, source heads, source/cache hashes, SENSO pins, exact
configuration aggregate, seed derivation/commitment, local host, RTX training
host, tool versions, and a complete evidence inventory under `evidence/e0/`.

E0 produces no dataset row, model score, checkpoint, matched-exam result, or
frontier candidate. A PASS only authorizes E1.
