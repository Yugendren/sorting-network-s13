# Version-1 failure analysis

Frozen before any version-2 implementation or E4 seed materialization.

## Decision

Version 1 failed validly at E2 and did not enter E3. Its exact deployed model
obtained micro within-seed concordance 0.446355505360 and macro concordance
0.446364583942 on the single-use 20-seed validation set. Every individual seed
scored below the constant-ranker reference of 0.5. The integration audit was
operational: it completed exactly 50,200 evaluations and 50,200 rank calls,
returned a 46-comparator network accepted by both frozen verifiers, and used
the frozen truncation proposal and tie-break policy.

This is a ranking-quality failure, not a verifier, budget, inference,
integration, or reproducibility failure. E3 remained sealed because the E2
prerequisite failed; therefore no E3 outcome exists to use in this analysis or
in repair design.

## Evidence

- ARTIFACT_VERIFIED E1 dataset: 1,004,000 rows. Training seeds 1--16 contain
  zero positive `final_count <= 45` labels. The 1,216 development positives all
  occur in calibration seed 18.
- MEASURED V1 selected-checkpoint calibration average precision:
  0.003119164559, below the calibration positive prevalence of approximately
  0.00606.
- ARTIFACT_VERIFIED validation aggregate SHA-256:
  `7bca7bec0cfda5573d4640eb6f9a3af697025dbedf3342242c330eb70dfbbfd9`.
  It contains 1,004,000 rows, 2,079 size-45 rows, no size-44 row, and
  19,499,483,815 comparable within-seed pairs.
- MEASURED V1 validation metric SHA-256:
  `1e2e83b60e49f2f52cfd316ac51ade95f5f85b4812d729fd500108a3fcb8fff6`.
- ARTIFACT_VERIFIED E2 resume manifest SHA-256:
  `d7a06923e0fea0ef1dadca0fcfb72436fd0f26f313eea24e976a7e4a86cc406e`.

## Causal diagnosis

The binary completion event is absent from the frozen training split, so the
V1 BCE objective cannot learn positive completion value from training rows.
Calibration-only positives cannot repair a model whose gradient training saw
only the negative class. The consistently sub-0.5 validation ranking is the
predicted failure mode of that objective. The evidence does not isolate a
defect in the 85-feature representation or in the truncation integration, and
changing either would confound the repair.

## Exactly one major repair

Version 2 changes the **learning objective only**:

- replace binary `final_count <= 45` BCE with float32 regression to standardized
  negative final comparator count, so higher score means a better completion;
- use mean squared error for gradient training;
- select checkpoints by highest calibration within-seed concordance, then
  lowest calibration MSE, then earliest epoch.

The target is derived only from `final_count`; target 44 is not represented,
weighted, rewarded, or selected. Training and calibration remain development
seeds 1--16 and 17--20 respectively.

The representation remains the exact 85 V1 features with the exact V1 feature
normalization. The architecture, parameter count, optimizer, learning rate,
batch size, epoch/patience limits, deterministic seed, export format, compiled
float32 inference, eight truncation proposals, tie break, single base RNG draw,
reconstruction, mutation, fitness, population, evaluation budget, and two
verifiers remain frozen. No second major change and no version 3 are permitted.

## Information boundary

E3 seeds have not been executed. E4 seeds have not yet been materialized or
executed. Neither partition may be used for training, normalization,
checkpoint selection, repair choice, or debugging. Version-1 validation data
was inspected only for this aggregate diagnosis and will not be added to V2
gradient training.
