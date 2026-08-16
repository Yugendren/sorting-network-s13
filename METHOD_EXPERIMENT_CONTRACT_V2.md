# Mericanii S(13) learned-method experiment contract, version 2
# Feature-engineering branch

Created: 2026-08-17
Branch: goal/s13-feature-eng-v1-omp
Based on terminal commit of goal/s13-method-v1: d72cedf

## 1. Authority and objective

This contract authorises a focused feature-engineering investigation to improve
training-data diversity for the Mericanii learned completion-value ranker.  The
predecessor goal/s13-method-v1 experiment was terminated with verdict
`METHOD_REJECTED`.  Its canonical terminal report is immutable:

    evidence/final/final-20260815T044410Z/canonical-terminal-report.md
    SHA-256: 1417ca51...bcbab

Diagnosed failure modes motivating this goal:

1. **Label scarcity / seed concentration** — all 1,216 positive (<=45)
   training rows came from a single development seed (seed 18); training seeds
   1–16 contained zero positives.  The model could not generalise.
2. **Feature blind-spots** — the 85-dimensional v1 feature set captured
   prefix-level statistics and recent-comparator identities but omitted
   structural properties (output-set entropy, channel-pair coverage,
   symmetry indicators, comparator-depth profile) that distinguish promising
   prefixes from dead-end ones.
3. **Normalisation domain mismatch** — standardisation was fitted on seeds
   1–16 only, which had a different population distribution from the single
   informative calibration seed.

The scientific question for this goal is:

> Can an enriched feature set that better characterises network completability,
> combined with a training-data strategy that produces positive labels across
> more seeds, yield a ranker whose within-seed concordance exceeds 0.5 on a
> frozen validation set?

This is a feature-engineering and data-diversity study, not a new search
method.  The SENSO search loop, evaluation budget, verifiers, and candidate
schema are inherited unchanged.

Authority order:

1. This `METHOD_EXPERIMENT_CONTRACT_V2.md`.
2. `GOAL_STATE.md` (this branch's version).
3. F0-frozen configurations, seed manifests, and feature definitions.
4. `METHOD_EXPERIMENT_CONTRACT_V1.md` and `PROJECT_CONTRACT.md` for immutable
   predecessor facts (B0–B4 baseline, verifier hashes, SENSO binary hash).
5. Primary-source documentation.
6. Implementation convenience.

## 2. Inherited pins (immutable)

All of the following are inherited verbatim and must not change:

- Frozen Python verifier SHA-256:
  `b420583606173d9f892e48e5656580792d2a4a2aa27a39f9a599ff5770e9ab2e`
- Frozen Go verifier SHA-256:
  `a07336fb4d4d1b8c7b275fd00fe65173df3fd8cb4f9ebd017cc90e1ecea1ee2f`
- Frozen SENSO binary SHA-256:
  `1d6fe20b547fa0e9dd9c899e34b608ac157104f63fd845d858e6e4ae9c0e6cc6`
- B0–B4 evidence inventory: immutable; never alter, delete, or regenerate.
- Baseline commit: `f4829768b9de2db170e4234d6c3d774b312eb318`.
- Research snapshot (2026-08-15): `44 <= S(13) <= 45`.
- Public 45-comparator witness SHA-256:
  `35ddd10b0869a8d589559cdca71fc2d3bd619411988017167e4e40e71992bb83`.
- Candidate-evaluation accounting: `200 + 500 * 100 = 50,200` per seed.
- SENSO configuration: population 200, generations 500, target <=45.

## 3. Scope and prohibitions

### Authorised

- F0: freeze this experiment (seeds, feature schema v2, dataset schema v2,
  model config, success criteria).
- F1: build the new dataset using the enriched feature set over extended
  development seeds; instrument SENSO read-only; verify trajectory preservation.
- F2: train and freeze a new ranker on the diversified dataset; validate
  concordance on a frozen hold-out.
- F3: if F2 passes concordance, run one paired 60-seed matched-compute exam
  (same protocol as E3/E4: 50,200 evaluations per method per seed, six frozen
  criteria, dual-verified successes).
- F4: if F3 fails, make exactly one additional feature or data repair and run
  one new exam.  Version 3 is then forbidden.
- F5: conditional 44-comparator frontier campaign, only if F3 or F4 passes.

### Prohibited (same as predecessor, plus the following)

- Altering or rerunning anything under `evidence/b0`–`evidence/b4` or
  `evidence/e0`–`evidence/final`.
- RL, diffusion, MCTS, LLM inner-loop search, SAT lower-bound work.
- A third version after F4 fails.
- Paid compute.
- Using the 44-comparator target in dataset generation, features, labels,
  reward, training, validation, or F3/F4 exams.
- Using any F3 holdout row as a training example, normalisation input, or
  hyperparameter signal before that exam.
- Contacting maintainers or publishing results.

## 4. Feature-engineering hypotheses (pre-frozen; finalised in F0)

The following candidate feature groups are under consideration.  Exactly those
selected during F0 are frozen in `config/experiment-v2/features-v2.json` and
may not be changed afterwards.

### Group A — Output-set structural entropy
- Shannon entropy of the per-channel output-function-set size distribution.
- Normalised Gini coefficient of output-set sizes across channels.
- Fraction of channels whose output set is a singleton (fully determined).
- Fraction of channels whose output set is still the full 8192 (unconstrained).

### Group B — Comparator-pair coverage and channel symmetry
- Number of distinct channel pairs covered by prefix comparators, normalised
  by C(13,2)=78.
- Coverage asymmetry: max pair frequency minus min pair frequency, normalised.
- Histogram of comparator-depth (level) occupancy, binned into early/mid/late
  thirds of the 45-comparator budget.
- Indicator: whether the prefix is symmetric under channel reversal (network
  reflects to itself), per the Valsalam/Miikkulainen observation that symmetric
  prefixes correlate with shorter completions.

### Group C — Progress velocity signals
- Rolling average of output-set size reduction per comparator over the last
  4, 8, and 16 comparators (three features).
- "Stall fraction": proportion of the last 8 prefix comparators that produced
  zero reduction in any channel's output-set size.

### Group D — Extended generation/population context
- Normalised position of the current parent in the population hall-of-fame
  (rank / population_size).
- Ratio of current-generation best fitness to generation-1 best fitness.

### Group E — Data-diversity seeds
The v1 experiment used B2 development seeds 1–20.  Those are retained.
Additionally, up to 20 fresh n=13 target-45 SENSO runs with new seeds
(range 1001–1020) may be added to the dataset to supply positive labels from
diverse starting points.  These seeds must:
- be declared and frozen in F0 before any run;
- be disjoint from all predecessor seed partitions;
- use the same SENSO binary and configuration;
- pass the same instrumentation-on/off trajectory sentinel.

Extra-seed usage is a binary F0 decision; it may not be enabled after seeing
any F1 result.

## 5. Evidence and integrity rules

Identical to the predecessor contract (Section 4 of
`METHOD_EXPERIMENT_CONTRACT_V1.md`).  Every scored attempt is append-only with
complete hashes, commands, resource measurements, and verifier reports.  A
negative reproducible result completes this goal.

## 6. Terminal verdicts

- `CONCORDANCE_PASS / EXAM_PASS`: ranker beats constant-score baseline on
  frozen validation and passes the six paired-exam criteria.
- `CONCORDANCE_FAIL`: ranker does not clear 0.5 concordance; goal is
  complete; no further feature version is authorised.
- `EXAM_FAIL`: concordance passed but both F3 and (if run) F4 exams failed;
  terminal verdict `METHOD_REJECTED_V2`.
- `FRONTIER_FOUND_44`: a valid 44-comparator candidate appeared during F5;
  freeze immediately, run both verifiers only, follow the witness-audit
  procedure.
- `INVALID`: verifier disagreement, holdout leakage, or failed integrity
  replay; all search stops.
