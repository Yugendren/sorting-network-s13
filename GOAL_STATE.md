# Goal state

Keep this file below 120 lines. Replace stale facts; do not append a diary.

## Contract

- Goal: build and verify the S(13) baseline laboratory, issue a terminal
  baseline verdict, and stop before novel experiments.
- Authority: `PROJECT_CONTRACT.md`.
- Contract SHA-256: `UNKNOWN` until the execution run freezes it.
- Execution prompt SHA-256: `UNKNOWN` until the execution run freezes it.
- Scope: Milestones B0--B4 only.
- Excluded: 44-comparator frontier search, nonexistence search, ML/RL training,
  LLM search, diffusion, GPU rental, publication, and external claims.

## Current truth

- State: `NOT_STARTED`.
- Current milestone: B0 -- inspect, audit, and freeze.
- Repository state: folder created; Git status `UNKNOWN` until inspected.
- Research snapshot: as of 2026-08-15, maintained bounds are
  `44 <= S(13) <= 45`.
- Known construction: public 45-comparator, 10-layer network.
- Known certified precedent: `S(11)=35`, with `S(12)=39` derived in Harder's
  work; published certificate/checker available.
- Local machine: Apple M4 Mac mini, 10 CPU cores, 16 GiB RAM.
- RTX 3060 server: available but prohibited for the baseline unless the
  contract is versioned by the user.
- Verified implementation/evidence: none.
- Terminal verdict: `PENDING`.

## Baseline acceptance gates

| Gate | State | Evidence |
|---|---|---|
| B0 source and protocol freeze | NOT RUN | -- |
| B1 independent construction truth | NOT RUN | -- |
| B2 20-seed constructive baseline | NOT RUN | -- |
| B3 exact/certificate baseline | NOT RUN | -- |
| B4 aggregate report and verdict | NOT RUN | -- |

## Next smallest action

1. Read `PROJECT_CONTRACT.md` completely.
2. Inspect Git and initialize the standalone repository if needed.
3. Re-audit the live S(13) status and pin all source/artifact versions.
4. Freeze the B0 manifest before scored execution.

