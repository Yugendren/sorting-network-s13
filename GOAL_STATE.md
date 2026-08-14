# Goal state

Keep this file below 120 lines. Replace stale facts; do not append a diary.

## Contract

- Goal: build and verify the S(13) baseline laboratory, issue a terminal
  baseline verdict, and stop before novel experiments.
- Authority: `PROJECT_CONTRACT.md`.
- Contract SHA-256:
  `6f345adb8c2037c28d4f08bf04cdbba6205de8848768b52c4bc9f09f737e1d61`.
- Execution prompt SHA-256:
  `f1f99ff05de9baab68ef0056458a3932094f3b0cc2d7fde55db28b3edad52ad9`.
- Scope: Milestones B0--B4 only.
- Excluded: 44-comparator frontier search, nonexistence search, ML/RL training,
  LLM search, diffusion, GPU rental, publication, and external claims.

## Current truth

- State: `ACTIVE`.
- Current milestone: B0 -- inspect, audit, and freeze.
- Repository state: branch `goal/s13-baseline`; supplied snapshot commit
  `fa0fc41e0bc2841a38aed55418602db6049c89b8`; frozen B0 implementation commit
  `744826ddff0884e53ba3d94db05773fcb669b86f`.
- Research snapshot: live audit on 2026-08-15 found maintained bounds
  `44 <= S(13) <= 45`; no primary/current source in the audit settled S(13).
- Known construction: public 45-comparator, 10-layer network.
- Known certified precedent: `S(11)=35`, with `S(12)=39` derived in Harder's
  work; published certificate/checker available.
- Local machine: Apple M4 Mac mini, 10 CPU cores, 16 GiB RAM.
- RTX 3060 server: available but prohibited for the baseline unless the
  contract is versioned by the user.
- Verified implementation/evidence: source cache, protocol freeze, dependency
  lock, and portability patch pass narrow tests. The first B0 run failed safely
  on an incorrect Stack lock path; the corrected run passed. Evidence-validator
  hardening changed the frozen B0 aggregate, so one final clean B0 rerun is
  required before advancing.
- Terminal verdict: `PENDING`.

## Baseline acceptance gates

| Gate | State | Evidence |
|---|---|---|
| B0 source and protocol freeze | PASS SUPERSEDED; RETRY REQUIRED | `evidence/b0/b0-20260814T230128Z` |
| B1 independent construction truth | NOT RUN | -- |
| B2 20-seed constructive baseline | NOT RUN | -- |
| B3 exact/certificate baseline | NOT RUN | -- |
| B4 aggregate report and verdict | NOT RUN | -- |

## Next smallest action

1. Commit the corrected PASS evidence and hardened evidence validator.
2. Rerun B0 from the resulting clean commit; do not start B1 unless it passes.
