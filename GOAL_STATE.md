# Goal state

Keep this file below 120 lines. Replace stale facts; do not append a diary.

## Active contract

- Goal: enrich the Mericanii feature set and training-data diversity to improve
  the learned completion-value ranker for S(13).
- Authority: `METHOD_EXPERIMENT_CONTRACT_V2.md`.
- Contract SHA-256:
  `df2f52281db6114821eb63487b5c1ad873834a60a8b2634d0c0047d09fe2620f`.
- Scope: F0–F5, at most two ranker versions, exactly one terminal report.
- Branch: `goal/s13-feature-eng-v1-omp` based at terminal commit of
  `goal/s13-method-v1` (`d72cedf`).
- Prohibited: target 44 during learning or matched exams; RL, diffusion, MCTS,
  LLM inner-loop oracles, SAT lower-bound work, version 3 after F4, paid
  compute, publication, or external contact.

## Predecessor facts (immutable)

- Terminal predecessor verdict: `METHOD_REJECTED`.
- Canonical predecessor report:
  `evidence/final/final-20260815T044410Z/canonical-terminal-report.md`.
- B0–B4 evidence: immutable; never alter, delete, or regenerate.
- Frozen Python verifier SHA-256:
  `b420583606173d9f892e48e5656580792d2a4a2aa27a39f9a599ff5770e9ab2e`.
- Frozen Go verifier SHA-256:
  `a07336fb4d4d1b8c7b275fd00fe65173df3fd8cb4f9ebd017cc90e1ecea1ee2f`.
- Frozen SENSO binary SHA-256:
  `1d6fe20b547fa0e9dd9c899e34b608ac157104f63fd845d858e6e4ae9c0e6cc6`.
- V1 training positive rows: 1,216; all from calibration seed 18 only;
  training seeds 1–16 produced zero positives.
- V1 validation concordance: 0.446355505360 (< 0.5, failed gate).
- V2 (objective-repair) exam: SENSO 2/60 successes; Mericanii 0/60.
- Research snapshot (rechecked 2026-08-15): `44 <= S(13) <= 45`.

## Current truth

- State: `ACTIVE` — gate F0 not yet complete.
- Next falsifiable gate: F0 experiment freeze.

## Diagnosed weaknesses to address

1. All positive training labels came from seed 18; seeds 1–16 had zero
   positives — the model saw no successful completion pattern during training.
2. The 85-feature v1 set lacked structural completability signals: output-set
   entropy, channel-pair coverage, symmetry indicators, progress velocity.
3. Normalisation was fitted on the zero-positive training seeds (1–16),
   creating a domain mismatch at validation time.

## Gate ledger

| Gate | State | Next falsifiable outcome |
|---|---|---|
| F0 experiment freeze | PENDING | Feature schema v2 committed; seeds declared |
| F1 dataset | NOT STARTED | All declared seeds instrumented; trajectory sentinel pass |
| F2 ranker training | NOT STARTED | Concordance > 0.5 on frozen validation |
| F3 matched exam | NOT STARTED | Six frozen criteria on 60 paired seeds |
| F4 one repair | NOT STARTED | Only if F3 fails validly |
| F5 frontier | NOT STARTED | Only if F3 or F4 passes; 44-comparator campaign |
| Terminal report | NOT STARTED | Single terminal verdict |

## Immediate next action

Complete F0: finalise and commit `config/experiment-v2/features-v2.json`
(feature groups A–E selections), `config/experiment-v2/dataset-v2.json`
(seed manifest including any Group-E extra seeds), and
`config/experiment-v2/model-v2.json`. Then generate the F0 freeze manifest
and commit with SHA-256 recorded here.
