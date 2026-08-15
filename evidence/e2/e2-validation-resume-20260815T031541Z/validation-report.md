# Mericanii method V1 validation report

Run: `e2-validation-resume-20260815T031541Z`  
Tested commit: `2fd9c5155479a3227d0ec05abc26b55c9ddbd812`  
Gate decision: `E2_FAIL`

This is an E2 gate decision, not a terminal goal verdict.

## Frozen identities

- ARTIFACT_VERIFIED contract SHA-256: `6d8e9c3d0c4719bbd4c28bf55bc068ead10407e4a5928978afc55be338e503e6`.
- ARTIFACT_VERIFIED model export SHA-256: `eb606f4f6712a1eaa53bde8d36c0c8280c635c73453d22a861112ccf356babb7`.
- ARTIFACT_VERIFIED model checkpoint SHA-256: `ad736315f79493ffccaee6418a4d95624282374bb6e844d0001346dd88d617ab`.
- ASSUMED primary aggregation fixed before execution: micro-average over all unequal-final-size pairs within each seed; exact score ties contribute 0.5.

## Result

- LOCALLY_REPRODUCED rows: 1,004,000 across 20 frozen validation seeds.
- MEASURED comparable within-seed pairs: 19,499,483,815.
- MEASURED micro concordance: 0.446355505360.
- MEASURED macro seed concordance: 0.446364583942.
- LOCALLY_REPRODUCED <=45 label rows: 2,079; all unique successes were checked by both frozen verifiers.
- Gate threshold: strictly greater than 0.5; result: FAIL.

## Frozen integration audit

- LOCALLY_REPRODUCED seed: 1596410276.
- LOCALLY_REPRODUCED evaluations: 50,200.
- LOCALLY_REPRODUCED final comparator count: 46 (accepted by both verifiers).
- MEASURED rank calls / model score calls: 50,200 / 386,006.
- MEASURED total ranking / model-only time: 14.467605s / 0.682043s.

## Boundary

- UNKNOWN: E3 final-holdout performance; no E3 seed was executed or used for tuning here.
- UNKNOWN: existence of a 44-comparator network; target 44 was not used in this gate.
- No configuration change is permitted after this validation result.
