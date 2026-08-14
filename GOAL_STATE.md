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
- Current milestone: B1 -- establish independent construction truth.
- Repository state: branch `goal/s13-baseline`; supplied snapshot commit
  `fa0fc41e0bc2841a38aed55418602db6049c89b8`; final B0 gate source commit
  `19bd4efadddf75182caa8012981917c0938aa2ed`.
- Research snapshot: live audit on 2026-08-15 found maintained bounds
  `44 <= S(13) <= 45`; no primary/current source in the audit settled S(13).
- Known construction: public 45-comparator, 10-layer network.
- Known certified precedent: `S(11)=35`, with `S(12)=39` derived in Harder's
  work; published certificate/checker available.
- Local machine: Apple M4 Mac mini, 10 CPU cores, 16 GiB RAM.
- RTX 3060 server: available but prohibited for the baseline unless the
  contract is versioned by the user.
- Verified implementation/evidence: B0 PASS. The source/status audit, protocol,
  20 seeds, dependency lock, budgets, portability patch, and immutable evidence
  policy are frozen at aggregate SHA-256
  `9efccb2d1b3fcafef9385ddb562a5e202136bc31c64cfc64bdc3c9bdea60b67c`.
- Terminal verdict: `PENDING`.

## Baseline acceptance gates

| Gate | State | Evidence |
|---|---|---|
| B0 source and protocol freeze | PASS | `evidence/b0/b0-20260814T230315Z` |
| B1 independent construction truth | NOT RUN | -- |
| B2 20-seed constructive baseline | NOT RUN | -- |
| B3 exact/certificate baseline | NOT RUN | -- |
| B4 aggregate report and verdict | NOT RUN | -- |

## Next smallest action

1. Build Verifier A and Verifier B without shared parsing or execution logic.
2. Establish the full B1 fixture, differential, metamorphic, mutation, and
   deterministic-replay gate before starting B2.
