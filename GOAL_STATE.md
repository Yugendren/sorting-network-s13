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

- State: `COMPLETE`.
- Current milestone: B4 complete -- stopped before any novel experiment.
- Repository state: branch `goal/s13-baseline`; supplied snapshot commit
  `fa0fc41e0bc2841a38aed55418602db6049c89b8`; final B0 gate source commit
  `19bd4efadddf75182caa8012981917c0938aa2ed`; B1 gate source commit
  `48bd3e136545095b807f6d68f7f13b7a27af5524`; B2 gate source commit
  `a91a1710201d4f1c4b1f13e6473930ce8ec13184`; B3 gate source commit
  `5d44ca23742cd86b490ba366ad568b5322e4f21f`; B4 gate source commit
  `307198dceb6a832e65725f8e84ef9423f1abb451`.
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
- Construction truth: B1 PASS. Python direct enumeration and the independent Go
  bit-parallel verifier agreed on 267 cases and both accepted the public
  45-comparator witness with artifact SHA-256
  `35ddd10b0869a8d589559cdca71fc2d3bd619411988017167e4e40e71992bb83`.
- Constructive reproduction: B2 PASS. All 20 SENSO seeds completed; seed 18
  produced the sole 45-comparator result, accepted by both verifiers. The size
  distribution was 45:1, 46:16, 47:3. Greedy best was 47 and random best 148.
- Exact/certificate reproduction: B3 PASS. The official n=9 workflow returned
  `Just (9,25)`, a well-formed corrupted proof returned `Nothing`, and the
  exact published n=11 certificate returned `Just (11,35)`. Its 3,068,651,498
  byte SHA-256 remained
  `7fe9f5cd694714bf83da0bcab162a290eb076ad4257265507a74cea8fab85b7e`
  before and after the 5,148.689796-second replay. Total scored wall time
  through B3 is 5,618.423088 seconds.
- Aggregate and stop: B4 PASS. It validated four accepted gate identities and
  all ten preserved B0--B3 scored attempts, generated the 12-section report,
  and confirmed that no novel experiment started. The report SHA-256 is
  `d2cb721147ba442004bb3018db07a3cdf7d2626264f2aabe1a3d2cacae48abb7`.
- Terminal verdict: issued once in
  `evidence/b4/b4-20260815T014232Z/baseline-report.md`.

## Baseline acceptance gates

| Gate | State | Evidence |
|---|---|---|
| B0 source and protocol freeze | PASS | `evidence/b0/b0-20260814T230315Z` |
| B1 independent construction truth | PASS | `evidence/b1/b1-20260814T231402Z` |
| B2 20-seed constructive baseline | PASS | `evidence/b2/b2-20260814T232833Z` |
| B3 exact/certificate baseline | PASS | `evidence/b3/b3-20260815T000708Z` |
| B4 aggregate report and verdict | PASS | `evidence/b4/b4-20260815T014232Z` |

## Stop condition

No further action is authorized by this contract. Before any later experiment,
the user must approve and freeze a new versioned contract that begins with a
fresh S(13) status audit. Do not draft or execute it implicitly.
