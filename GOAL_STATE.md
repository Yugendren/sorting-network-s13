# Goal state

Keep this file below 120 lines. Replace stale facts; do not append a diary.

## Active contract

- Goal: definitively settle S(13) ∈ {44, 45} via dual-track programme —
  Track A (LLM-outer-loop evolution hunt for a 44) and Track B (proof
  engineering: make the n=13 lower-bound computation feasible).
- Authority: `METHOD_EXPERIMENT_CONTRACT_V3.md`. Contract SHA-256:
  `2462f25f78c427a50d929d31bca9c789e8a8602d437104b64d5fb0897b86d098`.
- Branch: `main`.
- Anchors: `SOLUTION_STRATEGY.md`, `docs/research-programme.md` (M0–M5),
  `docs/sota-survey.md`, `docs/evolution-harness-design.md`,
  approved plan 2026-08-17.
- Budget: local-first (M4 16GB/10c; 3060 box A 48GB; 3060 box B 32GB);
  AWS ≤ $500 credits, RunPod ≤ 40 SGD, per-run estimates required,
  >$50/run needs explicit user approval.

## Predecessor facts (immutable)

- B0–B4 baseline complete (2026-08-15); evidence immutable.
- goal/s13-method-v1: terminal verdict `METHOD_REJECTED`.
- goal/s13-feature-eng-v1-omp: **PARKED at gate F0** (committed at
  `2b976a0`, inactive; superseded by v3 programme; revivable).
- Frozen Python verifier SHA-256:
  `b420583606173d9f892e48e5656580792d2a4a2aa27a39f9a599ff5770e9ab2e`.
- Frozen Go verifier SHA-256:
  `a07336fb4d4d1b8c7b275fd00fe65173df3fd8cb4f9ebd017cc90e1ecea1ee2f`.
- Frozen SENSO binary SHA-256:
  `1d6fe20b547fa0e9dd9c899e34b608ac157104f63fd845d858e6e4ae9c0e6cc6`.
- sortnetopt pin: `0b5d09c47446096f9e3a0812b35afc72b7f2a718`.
- SENSO matched-compute baseline: 2/60 seeds at ≤45, 50,200 evals/seed.
- Research snapshot (surveyed 2026-08-17): `44 <= S(13) <= 45`; 44 bound
  is 2025 folklore (van Voorhis two-channel + S(11)=35), never published;
  45 witness is Juillé 1995, unimproved.

## Measured anchors (evidence/b2, evidence/b3)

- n=9 full search: ~0.80 s real (prior 15.4 s figure included a 10 s
  stats-logger sleep floor + checker); n=10: ~0.92 s, ~86 MB (local).
- n=10 memo mass: k=7,8 (n-3, n-2) hold 85.7% of packed bytes;
  get:insert 17:1; 87.6% of table created in final bound iteration.
- n=11 certificate replay: 5149 s, 4.06 GB (M4, passes).
- n=11 original full search: 4h51m, 178 GB (Harder's 24-core box).
- Harder's n=13 direct estimate: >20,000 TB RAM; known waste headroom
  ~195× (12.7M certificate steps vs 2.46B explored sets at n=11).

## Current truth

- State: `ACTIVE` — P0 governance in progress (contract committed with
  this file's update).
- Active milestones: Track A gate = harness produces valid sorters and
  reaches 45; Track B gate = M0 (sortnetopt archaeology + n=9/n=10
  local profiling with waste breakdown).

## Gate ledger

| Gate | Track | State | Falsifiable outcome |
|---|---|---|---|
| P0 governance | — | IN PROGRESS | v3 contract + this file committed on main |
| P1 harness build | A | NOT STARTED | Evaluator + pool + ledger; gen-0 smoke run; valid sorter found |
| A-45 | A | NOT STARTED | Evolved program reaches 45 comparators |
| A-beat-SENSO | A | NOT STARTED | >2/60 at ≤45 matched compute |
| M0 archaeology+profile | B | **COMPLETE** | internals doc + instrumentation patch + memo-mass histogram (evidence/v3/m0) |
| M1 scaling law | B | NOT STARTED | Cost model + one AWS n=11 replication (~$15) |
| M2 memory attack | B | NOT STARTED | Full n=11 search on 48GB box, bit-identical, checker-verified |
| M3 ML+GPU | B | NOT STARTED | Node reduction with bit-identical certificates |
| M4 restricted classes | B | NOT STARTED | Class exhaustion certificates |
| M5 n=13 campaign | B | NOT STARTED | Go/no-go strictly from M1–M3 numbers |
| Side quest | — | NOT STARTED | docs/s13-lower-bound-note.md (44 bound write-up) |

## Immediate next action

Finish P0 (commit governance), then run P1 (Track A harness build) and
M0 (Opus lead archaeology of sortnetopt) in parallel.
