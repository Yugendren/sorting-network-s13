# Mericanii method-v1 protocol

The active authority is `METHOD_EXPERIMENT_CONTRACT_V1.md`. This document is a
compact implementation map; machine-readable values in
`config/experiment-v1/` take precedence.

## Controlled intervention

Frozen SENSO draws one Gaussian truncation point for each reconstructed child.
Version 1 uses that same draw as proposal zero and deterministically adds nearby
prefix proposals at offsets -2, +2, -4, +4, -8, +8, plus the empty prefix.
Duplicates are removed without reordering. A compiled 7,617-parameter MLP ranks
the resulting partial states, and the highest logit wins. Equal scores choose
proposal zero, exactly recovering the original truncation decision and RNG
call count.

Everything after the truncation choice remains SENSO: the learned-frequency
reconstruction, heuristic fallback, comparator mutation, fitness, population,
generation count, and verifier acceptance. The model does not propose
comparators and receives no 44-related input or label.

## Data boundary

E1 reruns only predecessor seeds 1--20 at target 45. Seeds 1--16 train the
classifier and 17--20 select its epoch. Twenty separately derived validation
seeds support one E2 generalization/integration audit but no gradient update.
The 60 E3 seeds are sealed until the scored exam. A domain and SHA-256
commitment reserve the E4 seeds without materializing an E4 manifest before a
version-1 failure analysis.

Each development reconstruction records 85 compact prefix features, its final
size, and its <=45 label. Exact 8,192-input counterexample counts are omitted
because doing that for 1,004,000 rows would materially alter runtime. Output
function set/level summaries retain exact partial-state structure at far lower
cost. Any <=45 row also carries its full sequence for both independent
verifiers.

## Evaluation

E3 pairs the original frozen SENSO binary and frozen Mericanii build on 60
untouched seeds. Each gets exactly 50,200 candidate evaluations per seed. The
six contract criteria are conjunctive; uncertainty is descriptive and cannot
relax them. Runs alternate method order by seed index, execute one at a time,
and report inference overhead separately.

Only a passing method unlocks E5. That campaign is capped at 100,000,000 total
candidate evaluations and seven calendar days, and it never supports a
nonexistence claim.
