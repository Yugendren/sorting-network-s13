# Mericanii S(13) Sorting-Network Laboratory

The completed B0--B4 baseline remains frozen at commit
`f4829768b9de2db170e4234d6c3d774b312eb318`. The active, separately versioned
goal evaluates one learned SENSO truncation ranker under
`METHOD_EXPERIMENT_CONTRACT_V1.md`; it does not alter or regenerate baseline
evidence.

This folder is the standalone experiment for the first Mericanii open-problem
programme:

> Determine whether a 13-input sorting network needs 44 or 45 comparators.

The trustworthy baseline has completed. The active method experiment keeps the
44 target out of learning and matched evaluation; a bounded frontier attempt is
allowed only if the frozen method passes.

## Start here

1. Read `METHOD_EXPERIMENT_CONTRACT_V1.md` completely.
2. Read `GOAL_STATE.md`.
3. Use `make verify`, then execute only the active serial gate in the ledger.

The execution prompt ends at `BASELINE_READY`. That verdict does **not** mean
the open problem is solved. It authorizes a later, separately frozen experiment
on Mericanii's builder/refuter and learned-ranking method.

## Current research snapshot

As of 2026-08-15:

\[
44 \le S(13) \le 45.
\]

A public 45-comparator witness exists. Either a valid 44-comparator witness or a
checked proof that no such witness exists would settle the case. The live
status must be re-audited when execution begins.

## Baseline execution status

B0 through B4 passed on 2026-08-15. The current-status audit did not find the
target stale; two independent verifiers accepted the public witness; seed 18
of the frozen 20-seed SENSO batch locally reproduced a verified 45-comparator
network; the official n=9 workflow returned `Just (9,25)`; and the exact
published n=11 certificate replay returned `Just (11,35)`. The canonical
terminal decision and complete evidence ledger are in
`evidence/b4/b4-20260815T014232Z/baseline-report.md`.

The baseline contract is complete and immutable. The user-approved method-v1
contract is now the sole authority for E0--E5.

The frozen interface begins with `make setup`, `make verify`, and the serial
`make baseline-b0` through `make baseline-b4` gates. `make evidence-check`
validates every preserved scored run.

The active method interface is serial: `make method-e0`,
`make setup-method-instrumented`, `make method-e1`, `make method-e2-train`,
`make setup-method-v1`, and then the single-use `make method-e2-validate`.
Later gates are intentionally unavailable until the validation decision has
been frozen and committed.

## Repository boundary

This project is independent of:

- `/Users/yugendren/defense`
- `/Users/yugendren/experiments/deletion_code`
- `/Users/yugendren/experiments/mericanii_knowledge`

Do not modify those folders while executing this experiment.
