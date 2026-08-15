# Mericanii method V1 validation report

Run: `e2-validation-20260815T030452Z`  
Tested commit: `446ae4bcefda5f62edceed31a33fa9869c4cf838`  
Gate decision: `FAIL`

This is an E2 gate decision, not a terminal goal verdict.

## Frozen identities

- ARTIFACT_VERIFIED contract SHA-256: `6d8e9c3d0c4719bbd4c28bf55bc068ead10407e4a5928978afc55be338e503e6`.
- ARTIFACT_VERIFIED model export SHA-256: `eb606f4f6712a1eaa53bde8d36c0c8280c635c73453d22a861112ccf356babb7`.
- ARTIFACT_VERIFIED model checkpoint SHA-256: `ad736315f79493ffccaee6418a4d95624282374bb6e844d0001346dd88d617ab`.
- ASSUMED primary aggregation fixed before execution: micro-average over all unequal-final-size pairs within each seed; exact score ties contribute 0.5.

## Result


## Error

`offline validation scoring failed: CRASH`

## Boundary

- UNKNOWN: E3 final-holdout performance; no E3 seed was executed or used for tuning here.
- UNKNOWN: existence of a 44-comparator network; target 44 was not used in this gate.
- No configuration change is permitted after this validation result.
