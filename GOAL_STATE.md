# Goal state

Keep this file below 120 lines. Replace stale facts; do not append a diary.

## Active contract

- Goal: build and evaluate the first Mericanii learned completion-value ranker
  for S(13); run one bounded 44-comparator campaign only if the method passes.
- Authority: `METHOD_EXPERIMENT_CONTRACT_V1.md`.
- Contract SHA-256:
  `6d8e9c3d0c4719bbd4c28bf55bc068ead10407e4a5928978afc55be338e503e6`.
- User objective SHA-256:
  `50adee208bbefcc871e4b5987d181fc5156b81841f015d28cb72fe6788691921`.
- Scope: E0--E5, at most two method versions, exactly one terminal report.
- Branch: `goal/s13-method-v1` based at frozen baseline commit
  `f4829768b9de2db170e4234d6c3d774b312eb318`.
- Prohibited: target 44 during learning or matched exams; RL, diffusion, MCTS,
  LLM inner-loop search, SAT lower-bound work, version 3, paid compute,
  publication, or external contact.

## Current truth

- State: `ACTIVE`.
- Active milestone: single-use E4 V2 matched exam. Version 1 failed E2;
  neither frozen matched-exam holdout has been run.
- Frozen predecessor report:
  `evidence/b4/b4-20260815T014232Z/baseline-report.md`.
- Predecessor report SHA-256:
  `d2cb721147ba442004bb3018db07a3cdf7d2626264f2aabe1a3d2cacae48abb7`.
- Predecessor verdict: `BASELINE_READY`.
- Research snapshot rechecked 2026-08-15: comparator-count bounds remain
  `44 <= S(13) <= 45`; depth 9 is context only.
- B0--B4 evidence inventory replay: PASS at method-branch creation. It is
  immutable and must not be regenerated.
- Frozen Python verifier SHA-256:
  `b420583606173d9f892e48e5656580792d2a4a2aa27a39f9a599ff5770e9ab2e`.
- Frozen Go verifier SHA-256:
  `a07336fb4d4d1b8c7b275fd00fe65173df3fd8cb4f9ebd017cc90e1ecea1ee2f`.
- Frozen SENSO binary SHA-256:
  `1d6fe20b547fa0e9dd9c899e34b608ac157104f63fd845d858e6e4ae9c0e6cc6`.
- Development n=13 seeds: predecessor B2 seeds 1--20 only.
- E3 requirement: frozen SENSO and Mericanii, 60 paired untouched seeds,
  exactly 50,200 candidate evaluations per method per seed.
- Method-v1 intervention: rank SENSO truncation-point proposals with a small
  completion classifier; reconstruction, mutation, fitness, and budgets remain
  otherwise frozen.
- Local host: Apple M4, 10 logical cores, 16 GiB RAM; CPU search and inference.
- Training host: authorized GeForce RTX 3060, 12 GiB; no paid compute.
- No matched exam or 44-comparator search has begun.
- E0 PASS: `evidence/e0/e0-20260815T021424Z`, tested source commit
  `da9301bf1c41378bdb6930388d8ac36f86f5d89c`, manifest SHA-256
  `a38832f101d24fbc5430ce8c25b5a343cbbcd8fcedf66c723f8383a588499754`,
  and frozen-config aggregate
  `5c22a3ce05504045ceaa7359a7b25d318cc0a923163b162779c32975c2533465`.
- E0 preserved one prior tooling FAIL at `evidence/e0/e0-20260815T021347Z`;
  it created no score and motivated the baseline-only inventory preflight.
- E1 PASS: `evidence/e1/e1-20260815T022353Z`, tested source commit
  `7d4c13de2328d21c10683242e83a05875978fea5`, manifest SHA-256
  `af6e1fb05a4fcf984f71d0a3ab4f40d39e4288d7fb68c2daae2b32c61f3236b5`.
  Logging-off, logging-on, and frozen B2 trajectories agree; all 20 seeds and
  1,004,000 rows passed. The compressed dataset SHA-256 is
  `5628fd5187772bd66ff630bc3889f1973ca8cfefae468b189e586cc83f6be994`.
- E1 labels: 1,216 <=45 rows, all from calibration seed 18, comprising 413
  unique 45-comparator candidates accepted by both verifiers. Training seeds
  1--16 contain zero positives; this frozen limitation must be handled without
  moving seed 18 or changing the version-1 objective.
- E2 training subgate PASS: `evidence/e2/e2-train-20260815T023758Z`, tested
  source commit `a6d531b7d89a6353d9920f1c3d2bd8bd3262f6a0`, manifest SHA-256
  `2ff8fc719428d62b87aa3c50b785f4a2b42581be780f93fd675065ff3f893074`.
  Both RTX replays selected epoch 26 and exported byte-identical weights. The
  model export SHA-256 is
  `eb606f4f6712a1eaa53bde8d36c0c8280c635c73453d22a861112ccf356babb7`;
  calibration AP was 0.003119165.
- Frozen V1 integration build PASS:
  `.build/senso-mericanii-v1/attempt-20260815T024633Z`, binary SHA-256
  `cbdfb957ecca9aa67b2effb6b05889ba2bcff7a97099246e36bee9a85a2d34dc`,
  integration-patch SHA-256
  `f2d8fd259f1ceab62e2e41f826f0573feb1d05cdbd4e17f5cf82df9960f1a132`.
  Compiled float32 inference matched all 32 fixture rows exactly.
- E2 single-use validation materialization completed all 20 seeds and 1,004,000
  rows at `evidence/e2/e2-validation-20260815T030452Z`; aggregate dataset
  SHA-256 is
  `7bca7bec0cfda5573d4640eb6f9a3af697025dbedf3342242c330eb70dfbbfd9`.
  It contains 2,079 <=45 rows and no <=44 row. The preserved gate failed
  mechanically before scoring because its wrapper rejected the evidence CWD;
  no seed trajectory was rerun or replaced.
- E2 V1 valid FAIL: `evidence/e2/e2-validation-resume-20260815T031541Z`,
  manifest SHA-256
  `d7a06923e0fea0ef1dadca0fcfb72436fd0f26f313eea24e976a7e4a86cc406e`.
  The exact frozen model scored micro concordance 0.446355505360 and macro
  0.446364583942 over 19,499,483,815 within-seed pairs; every one of 20 seed
  scores was below 0.5. Integration remained operational at exactly 50,200
  evaluations/rank calls and produced a dual-verified size-46 network. V1 may
  not enter E3.
- E4 freeze: change learning objective only; 85 features and truncation
  integration remain fixed. The revealed 60-seed E4 manifest reproduces compact
  commitment `02436e65...d57c4f` and is disjoint from all earlier partitions.
- E4 V2 training PASS: `evidence/e4/e4-train-20260815T032452Z`, source
  `a2da1a4`, manifest `0128da00...b1f95f`. Both RTX replays selected epoch 5;
  calibration concordance was 0.805550041740 and byte-identical model export
  SHA-256 was `7c7ec61f...79e9e6a`.
- Frozen V2 integration PASS: patch `f2d8fd25...1a132`; binary `382e4a29...7fdf`.

## Gate ledger

| Gate | State | Next falsifiable outcome |
|---|---|---|
| Authority freeze | COMPLETE | Commit `3c876d6`; no preceding scores |
| E0 experiment freeze | COMPLETE | PASS evidence `e0-20260815T021424Z` |
| E1 dataset | COMPLETE | PASS evidence `e1-20260815T022353Z` |
| E2 method v1 | COMPLETE / FAIL | Concordance 0.446355505360 < 0.5 |
| E3 matched exam | NOT RUN FOR V1 | E2 prerequisite failed; seeds remain sealed |
| E4 one repair | ACTIVE | Run the frozen 60-pair exam and integrity replay once |
| E5 frontier | CONDITIONAL | Only after pass; 100M eval / seven-day maximum |
| Terminal report | PENDING | One allowed verdict, then stop |

## Immediate next action

Commit the verified exam protocol, then execute the single paired E4 exam once.
