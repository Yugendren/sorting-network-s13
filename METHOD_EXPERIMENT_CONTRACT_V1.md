# Mericanii S(13) learned-method experiment contract, version 1

Frozen: 2026-08-15

## 1. Authority and objective

This contract implements the user's 2026-08-15 authorization to build and
evaluate one learned completion-value ranker for the 13-input minimum-size
sorting-network problem. If, and only if, the learned method passes its frozen
matched-compute exam, it may receive one bounded attempt to find a valid
44-comparator network.

The exact user objective is preserved outside the repository at
`/Users/yugendren/.codex/attachments/a087813c-0bfe-4f8a-b19a-2ee06e0b9dfb/goal-objective.md`
with SHA-256
`50adee208bbefcc871e4b5987d181fc5156b81841f015d28cb72fe6788691921`.

For this goal the authority order is:

1. this `METHOD_EXPERIMENT_CONTRACT_V1.md`;
2. `GOAL_STATE.md`;
3. E0-frozen configurations, manifests, feature definitions, and budgets;
4. the predecessor `PROJECT_CONTRACT.md`, only for the immutable B0--B4
   baseline and rules not superseded here;
5. primary-source documentation;
6. implementation convenience.

The primary falsifiable scientific question is:

> Under the same 50,200 completed-candidate evaluations per seed, can a small
> learned completion-value model rank SENSO partial network states better than
> the frozen SENSO-style heuristic?

A negative, reproducible result completes this goal. Search must not continue
indefinitely.

## 2. Frozen predecessor and research snapshot

The experiment begins from all of the following pins:

- baseline commit:
  `f4829768b9de2db170e4234d6c3d774b312eb318`;
- canonical baseline report:
  `evidence/b4/b4-20260815T014232Z/baseline-report.md`;
- report SHA-256:
  `d2cb721147ba442004bb3018db07a3cdf7d2626264f2aabe1a3d2cacae48abb7`;
- baseline verdict: `BASELINE_READY`;
- inherited research snapshot: `44 <= S(13) <= 45` for comparator count;
- public 45-comparator witness SHA-256:
  `35ddd10b0869a8d589559cdca71fc2d3bd619411988017167e4e40e71992bb83`;
- Python verifier source SHA-256:
  `b420583606173d9f892e48e5656580792d2a4a2aa27a39f9a599ff5770e9ab2e`;
- Go verifier source SHA-256:
  `a07336fb4d4d1b8c7b275fd00fe65173df3fd8cb4f9ebd017cc90e1ecea1ee2f`;
- frozen SENSO binary SHA-256:
  `1d6fe20b547fa0e9dd9c899e34b608ac157104f63fd845d858e6e4ae9c0e6cc6`;
- B2 execution configuration SHA-256:
  `71ebce6ae9b803ae4121421d796223c4a2f08b5b2c976e2f45d00ebb675cba78`;
- B2 SENSO configuration SHA-256:
  `871c35212c04a14ff955b010a0ab86894927783ecc6ad076f1b6f711c21b20ff`.

A fresh live audit on 2026-08-15 must be recorded in E0. If a primary source or
maintained artifact list shows that comparator-count `S(13)` is already
settled, the experiment stops without choosing a replacement problem. Because
this contract has no `STALE_TARGET` terminal label, that condition is reported
as `BLOCKED` with the stale-target fact made explicit.

Minimum size and minimum depth remain separate. Depth 9 is context only.

## 3. Scope and prohibitions

Authorized work is serial E0 through E5, with only one active gate:

- E0: freeze the experiment;
- E1: build the learning dataset;
- E2: implement and freeze method version 1;
- E3: run one matched-compute 60-seed holdout exam;
- E4: if E3 fails, make exactly one major repair and run one new 60-seed exam;
- E5: only after a passing E3 or E4, run one bounded 44-comparator campaign.

The only primary method hypothesis is a learned completion-value ranker.
This goal does not authorize RL, diffusion, MCTS, LLM or multi-agent inner-loop
oracles, SAT lower-bound search, a nonexistence proof, multiple unrelated search
methods, paid compute, publication, pushing, or contacting maintainers. LLMs
may design, implement, audit, and analyse but never score candidates in the
search loop.

The 44-comparator target is forbidden in dataset generation, features, labels,
reward shaping, training, validation, checkpoint choice, method selection, and
E3/E4. It appears only in the conditional E5 campaign.

No B0--B4 file may be altered, deleted, or regenerated. New code and evidence
must live outside `evidence/b0` through `evidence/b4`.

## 4. Scientific truth and evidence rules

Facts are labelled only as `PUBLISHED`, `ARTIFACT_VERIFIED`,
`LOCALLY_REPRODUCED`, `MEASURED`, `ASSUMED`, or `UNKNOWN`.

Every claimed successful network must pass both frozen independent B1
verifiers on all 8,192 binary inputs. A SENSO fitness, internal sorted flag,
model score, timeout, best-so-far log, or one verifier is not acceptance.
Verifier disagreement, holdout leakage, scored-artifact mutation, or a failed
integrity replay is terminal `INVALID`.

Every scored attempt is append-only and includes, as applicable:

- contract, parent-manifest, source-commit, build, config, feature, dataset,
  seed-manifest, and checkpoint hashes;
- exact argv, working directory, environment allowlist, stdout, stderr, exit
  code, start/end UTC, monotonic wall time, CPU time, peak RSS, and GPU metrics;
- all successes, ordinary failures, crashes, and timeouts;
- evaluation counts and explicit stop reason;
- candidate artifacts and both verifier reports;
- a recursively complete SHA-256 inventory.

Manifests may refer to immutable large artifacts kept under ignored `.cache` or
`.build` paths, but the manifest, size, and SHA-256 are committed. Secrets,
caches, large datasets, and transient build products are not committed.

An accepted gate gets one canonical immutable evidence directory and a verified
checkpoint commit. Failed and timed-out attempts are retained and inventoried.

## 5. E0 -- experiment freeze

Falsifiable outcome: E0 passes only if the predecessor pins match, the tree was
clean at branch creation, the live status remains open at `44 <= S(13) <= 45`,
both verifier sources are unchanged, all seed partitions and budgets are
immutable, and a clean preflight can replay the baseline evidence inventory.

E0 must commit, before training or scored results:

- exact seed manifests for development, validation, and E3 final holdout;
- a deterministic seed-derivation specification with domain separation;
- a frozen copy-by-hash reference to the original SENSO implementation and
  exact baseline command;
- exact candidate-evaluation accounting;
- feature schema, dataset schema, split policy, method-v1 role, model/training
  configuration, success criteria, uncertainty procedure, resource limits,
  environment allowlist, and terminal decision table;
- local and RTX 3060 hardware/software records;
- checks ensuring final holdout seeds cannot be accepted by development tools.

The development seeds are exactly the predecessor B2 seeds 1 through 20. They
are the only n=13 seeds permitted for E1 dataset generation. Validation seeds
are separate and may be used only for E2 checkpoint/configuration selection.
The 60 E3 seeds are a sealed final holdout: development, training, exploratory
analysis, and tuning commands must reject them.

If E4 is needed, its new 60-seed manifest is generated and committed after the
E3 failure analysis but before any repair implementation. Its domain separator
is committed in E0, and its seeds must be disjoint from all earlier partitions.

E0 records the tested commit and hashes its canonical manifest. No model score
may be generated before the authority freeze commit and E0 configuration
freeze.

## 6. E1 -- dataset

Falsifiable outcome: E1 passes only if read-only instrumentation preserves the
frozen SENSO random trajectory and output, every expected development seed and
record is present, the dataset validates against its frozen schema, and no
validation or holdout seed occurs in any row.

The existing SENSO estimate/reconstruct loop is instrumented without changing
its selection, reconstruction, mutation, random-number calls, evaluation, or
termination. The full frozen B2 development batch is rerun at target size 45,
population 200, generation 500, and 50,200 candidate evaluations per seed.

One row describes the prefix selected at the existing truncation decision and
its unchanged continuation. Features may summarize:

- prefix, parent, and remaining-to-45 comparator counts;
- generation and progress history;
- output-function set counts, level occupancy, lines completed, and current
  line;
- recent comparator identities and per-channel recent activity;
- existing SENSO fitness/heuristic summaries.

Labels are the continuation's final comparator count and whether that count is
at most 45. The internal SENSO sorted state is a dataset-generation assertion,
not independent witness acceptance. Any row representing a claimed <=45
success must be traceable to the full candidate, which is checked by both B1
verifiers.

Exact binary counterexample enumeration is optional only if its cost would
change the baseline trajectory or practical evaluation budget; any omission is
declared in the feature definition. No row is silently dropped. The raw dataset
is immutable, content-addressed, and split by seed, never by randomly mixing
rows from one trajectory across train and validation.

Instrumentation-off and instrumentation-on audit runs use a committed
development sentinel and must agree on evaluation count, final comparator
sequence, and final size. Instrumentation must not consume RNG state.

Additional data, if pre-frozen in E0, may use smaller instances or n=13 at
target 45 only. Method version 1 defaults to no such additional data; enabling
it after seeing results is forbidden.

## 7. E2 -- method version 1

Falsifiable outcome: E2 passes only if the small model trains reproducibly,
beats a constant-score ranker on the frozen validation objective, exports to a
deterministic CPU inference implementation, and the frozen integration changes
only the declared truncation-choice role.

Version 1 has one role: rank which truncation point of an existing SENSO parent
network to revisit. At each reconstruction, the unchanged Gaussian proposal
mechanism produces a frozen number of truncation candidates. The model scores
their partial states; the highest completion-value score is selected with a
predeclared deterministic tie break. After that choice, the original SENSO
frequency model, heuristic fallback, comparator mutation, fitness, population,
and termination operate unchanged.

The model is a small MLP trained as a binary completion classifier for a valid
network of at most 45 comparators. E0 freezes input dimension, normalization,
hidden widths, activation, loss, class handling, optimizer, learning rate,
batch size, epoch/early-stop ceiling, training seeds, proposal count, and tie
break. The parameter ceiling is 100,000 trainable parameters and the checkpoint
must fit comfortably in the RTX 3060's 12 GiB memory.

Training and batched validation may use the authorized RTX 3060 server.
Scored search and deterministic exported-model inference run on the M4 Mac
mini. No network service, GPU, LLM, Python ML runtime, or adaptive training is
allowed in a scored inner loop.

Checkpoint selection uses development training data and the frozen validation
partition only. The chosen checkpoint, exported weights, feature normalization,
build, command, and complete training curves are frozen before E3. After E3
begins, version 1 cannot be tuned.

## 8. E3 -- frozen matched-compute exam

Falsifiable outcome: method version 1 passes only if all six user-specified
criteria below pass on all 60 paired sealed holdout seeds.

Frozen SENSO and frozen Mericanii each receive exactly 50,200 completed-candidate
evaluations on each seed. Runs are paired by seed. Candidate evaluations, not
wall time, are the limiting budget; wall, CPU, memory, and inference time are
reported separately. A crashed, timed-out, under-budget, over-budget, missing,
or invalid run is not a success and may make the exam invalid under the frozen
decision table.

A per-seed success is a network with at most 45 comparators accepted by both B1
verifiers. Version 1 passes only if:

1. every claimed candidate passes both verifiers;
2. Mericanii succeeds on at least 12 of 60 seeds;
3. Mericanii has at least twice as many successes as frozen SENSO on those
   seeds;
4. Mericanii uses no more candidate evaluations per seed than SENSO;
5. the result survives the frozen integrity replay;
6. no holdout data was used for tuning.

The report includes all paired outcomes, full final-size distributions,
evaluation counts, wall and CPU time, time per evaluation, model inference
overhead, peak memory, 95% uncertainty intervals, and a paired effect estimate.
The uncertainty procedure is descriptive and cannot relax the six pass gates.

Integrity replay rebuilds from frozen inputs, re-aggregates all raw attempts,
reruns both verifiers for every success, checks every inventory, and exactly
replays the predeclared first and last paired sentinel seeds. It must reproduce
evaluation counts and comparator sequences.

If any 44-comparator candidate appears, all search stops immediately. Its exact
artifact is frozen, both B1 verifiers alone are run, and control moves directly
to the E5 witness-audit procedure without further tuning or search.

## 9. E4 -- one repair only

E4 runs only if version 1 fails validly. Before code changes, it commits a
failure analysis based on aggregate E3 evidence, names exactly one major
element to change, and freezes a new disjoint 60-seed holdout.

Version 2 may change exactly one of:

- representation;
- learning objective;
- search integration point.

The other two major elements remain byte-for-byte or semantically frozen as
specified by the E4 change manifest. Minor bug fixes are allowed only if they
do not exploit holdout outcomes; an integrity-affecting bug is `INVALID`, not a
repair opportunity.

Development and version-1 validation data may be used for the one repair. E3
holdout rows and outcomes may be used only for the written aggregate failure
diagnosis, never as training examples, feature normalization, hyperparameter
search, checkpoint selection, or seed selection.

Version 2 receives exactly one exam with the same six criteria, 60 paired seeds,
and 50,200 evaluations per method per seed. If it fails, the terminal verdict is
`METHOD_REJECTED`. Version 3 is forbidden.

## 10. E5 -- conditional frontier campaign

E5 is forbidden unless E3 or E4 passes. Before the first frontier result, the
successful source commit, exported checkpoint, configuration, feature schema,
build, and frontier seed manifest are frozen. No retraining, tuning, or method
change is allowed after frontier execution begins.

The campaign searches specifically for a valid 13-input, 44-comparator sorting
network and stops at the first of:

- a dual-verified 44-comparator witness;
- 100,000,000 aggregate completed-candidate evaluations;
- seven calendar days from the recorded UTC start;
- a validity or reproducibility failure.

The evaluation counter is summed across every frontier process and seed.
Parallelism, if frozen, cannot multiply the budget. Intermediate <=45 witnesses
are verified and preserved but do not reset any limit.

On a putative 44-comparator candidate:

1. stop all experiment search processes;
2. preserve the exact comparator sequence and originating state;
3. test all 8,192 inputs with both frozen independent verifiers;
4. repeat verification from a clean build/environment;
5. verify deliberately corrupted variants fail;
6. hash witness, logs, environment, code, and results;
7. produce a minimal independent witness checker;
8. do not publish or contact anyone without new user authorization.

Exhausting E5 without a witness is a measured negative search result, never a
lower bound or proof that 44 is impossible.

## 11. Hardware and resource boundary

The Apple M4 Mac mini is used for coding, orchestration, verification, CPU
search, aggregation, and scored inference. The accessible RTX 3060 server may
be used only for dataset transfer checks, training, and batched validation when
materially useful. RunPod, rented 4090s, and all paid compute are prohibited.

E0 freezes per-process threads, CPU/wall/RSS limits, GPU limits, aggregate gate
limits, and cleanup behavior. Resource exhaustion is preserved as a measured
attempt. External unavailability is `BLOCKED` only if required evaluation truly
cannot proceed after local fallbacks are exhausted.

All commands execute inside
`/Users/yugendren/experiments/sorting_network_s13`, except explicitly recorded
SSH commands to the authorized RTX server. Sibling directories and unrelated
processes are out of scope.

## 12. Terminal decision and stop

Exactly one canonical final report is produced after the last authorized gate.
It contains exactly one of:

- `FRONTIER_WITNESS`: the method passed and a reproducible 44-comparator
  witness passed the complete witness audit;
- `METHOD_VALIDATED_NO_WITNESS`: the method passed, but the bounded E5 campaign
  ended without a verified 44-comparator witness;
- `METHOD_REJECTED`: valid version-1 and permitted version-2 exams both failed;
- `BLOCKED`: a genuine external dependency prevented required evaluation;
- `INVALID`: leakage, verifier disagreement, scientific-integrity failure, or
  reproducibility failure invalidated the experiment.

If version 1 passes, E4 is skipped. If version 1 fails and version 2 passes, E5
runs. If both fail validly, no E5 search occurs. A terminal verdict ends the
goal immediately. No automatic continuation, publication, novelty claim,
nonexistence work, alternative method, or new target is authorized.
