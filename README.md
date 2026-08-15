# Mericanii S(13) Sorting-Network Laboratory

This folder is the standalone experiment for the first Mericanii open-problem
programme:

> Determine whether a 13-input sorting network needs 44 or 45 comparators.

The initial execution is deliberately limited to building a trustworthy
baseline laboratory. It must reproduce known construction and proof baselines
before any Mericanii learned search or attempt at 44 comparators begins.

## Start here

1. Read `PROJECT_CONTRACT.md` completely.
2. Read `GOAL_STATE.md`.
3. Paste `CODEX_BASELINE_PROMPT.md` into a Codex task opened from this folder.

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

The baseline contract is complete. No novel 44-comparator experiment or later
Mericanii method is authorized without a new user-approved, frozen contract.

The frozen interface begins with `make setup`, `make verify`, and the serial
`make baseline-b0` through `make baseline-b4` gates. `make evidence-check`
validates every preserved scored run.

## Repository boundary

This project is independent of:

- `/Users/yugendren/defense`
- `/Users/yugendren/experiments/deletion_code`
- `/Users/yugendren/experiments/mericanii_knowledge`

Do not modify those folders while executing this experiment.
