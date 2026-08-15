# Mericanii S(13) learned-method experiment — canonical terminal report

Run: `final-20260815T044410Z`
Terminal source commit: `fbb89f355fc16f72b24aab6a5b808692551e3854`
Authority: `METHOD_EXPERIMENT_CONTRACT_V1.md`
Authority SHA-256: `6d8e9c3d0c4719bbd4c28bf55bc068ead10407e4a5928978afc55be338e503e6`

## Terminal verdict

`METHOD_REJECTED`

Both permitted method versions failed validly. The objective-only V2 repair
completed its one frozen matched-compute exam but did not demonstrate an
advantage over SENSO. The conditional frontier campaign was therefore forbidden
and never began.

## Answer to the scientific question

The tested learned completion-value ranker did **not** rank partial sorting
networks better than the frozen SENSO heuristic under the same completed-candidate
evaluation budget.

- LOCALLY_REPRODUCED: frozen SENSO succeeded on 2 of 60 E4 holdout seeds.
- LOCALLY_REPRODUCED: Mericanii V2 succeeded on 0 of 60 E4 holdout seeds.
- LOCALLY_REPRODUCED: each method used exactly 50,200 candidate evaluations on
  every seed, or 3,012,000 evaluations per method.
- LOCALLY_REPRODUCED: every one of the 120 final candidates passed both frozen
  independent verifiers on all 8,192 binary inputs.
- MEASURED: the paired success-rate effect, Mericanii minus SENSO, was -0.0333;
  the frozen 10,000-resample paired-bootstrap 95% interval was [-0.0833, 0.0000].

This is a reproducible negative result for the tested method, not a general
claim about learned search.

## Gate history

| Stage | Outcome | Evidence |
|---|---|---|
| Frozen predecessor | `BASELINE_READY` | `evidence/b4/b4-20260815T014232Z/baseline-report.md` |
| E0 experiment freeze | PASS | `evidence/e0/e0-20260815T021424Z` |
| E1 development dataset | PASS | `evidence/e1/e1-20260815T022353Z` |
| Method V1 | FAIL at frozen E2 validation | `evidence/e2/e2-validation-resume-20260815T031541Z` |
| Method V2 objective repair | PASS training and integration | `evidence/e4/e4-train-20260815T032452Z` |
| Method V2 frozen exam | FAIL validly | `evidence/e4/e4-exam-20260815T034631Z` |
| Conditional frontier campaign | NOT RUN | Prohibited after method failure |

V1 used the frozen binary-completion objective. Its validation micro
within-seed concordance was 0.446355505360, below the strict 0.5 gate, and every
validation seed scored below 0.5. V1 therefore did not enter its E3 holdout.

The one permitted repair changed exactly one major element: the learning
objective. V2 replaced binary BCE with regression on standardized negative
final comparator count. The 85-feature representation, 85-64-32-1 MLP,
truncation-point integration patch, proposal policy, mutation, verification,
and evaluation budget remained frozen. Two deterministic RTX 3060 training
replays selected epoch 5 and exported byte-identical weights; development
calibration concordance was 0.805550041740.

## Frozen E4 exam result

| Measure | Frozen SENSO | Mericanii V2 |
|---|---:|---:|
| Successes | 2/60 | 0/60 |
| Wilson 95% interval | [0.0092, 0.1136] | [0.0000, 0.0602] |
| Final-size distribution | 45: 2; 46: 56; 47: 2 | 46: 27; 47: 33 |
| Candidate evaluations | 3,012,000 | 3,012,000 |
| Mean wall seconds/seed | 19.1977 | 33.2550 |
| Wall seconds/evaluation | 0.000382424 | 0.000662451 |
| Maximum peak RSS | 17,203,200 bytes | 17,317,888 bytes |

The six frozen criteria resolved as follows:

1. PASS — every claimed candidate was accepted by both verifiers.
2. FAIL — Mericanii produced 0 successes, below the required 12 of 60.
3. FAIL — Mericanii did not produce at least twice SENSO's 2 successes.
4. PASS — both methods used exactly 50,200 evaluations on every seed.
5. PASS — the frozen integrity replay succeeded.
6. PASS — no E4 holdout row or outcome was used for tuning.

MEASURED model overhead was 872.931173 seconds in the full ranking operation,
43.7493% of V2 search wall time. The exported MLP score computation itself used
41.261445 seconds, 2.0679% of V2 wall time; the remainder of ranking overhead
was feature/proposal construction and selection around the model.

## Integrity and reproducibility

- ARTIFACT_VERIFIED: E4 exam manifest SHA-256
  `21059f51efcd92421ba2cdcc2be3ce5996ab2292bf4be370d61539fdcc20fea9`.
- ARTIFACT_VERIFIED: E4 aggregation SHA-256
  `299e762e77089e36987322dd82d6f10088307583cb958a33182e42f679744d1c`.
- ARTIFACT_VERIFIED: E4 recursive inventory SHA-256
  `9b12a7ec1432e7276d6bb7b439b0eefef573ed23ba96f08a007febf8dacb93c2`.
- ARTIFACT_VERIFIED: selected V2 checkpoint SHA-256
  `60af80b18701f0c93276134b95e8f7ce554c20163020b03ec2d32d8ffe53383f`.
- ARTIFACT_VERIFIED: V2 model export SHA-256
  `7c7ec61f499e37c290a8e1040374daceac3df29fe6f11354472b896c847e9e6a`.
- ARTIFACT_VERIFIED: unchanged integration patch SHA-256
  `f2d8fd259f1ceab62e2e41f826f0573feb1d05cdbd4e17f5cf82df9960f1a132`.
- ARTIFACT_VERIFIED: scored V2 binary SHA-256
  `382e4a298f56bacf52d633ae80d08d3ede8590f5083e7726cf0a61d54d337fdf`.
- LOCALLY_REPRODUCED: all 120 raw attempts were reaggregated from disk.
- LOCALLY_REPRODUCED: both SENSO successes were replayed through both verifiers.
- LOCALLY_REPRODUCED: SENSO and V2 were rebuilt from frozen inputs.
- LOCALLY_REPRODUCED: both rebuilt methods exactly reproduced evaluation counts
  and comparator sequences on holdout ordinals 1 and 60, four comparisons total.
- LOCALLY_REPRODUCED: the final E4 inventory checker verified 19 immutable
  experiment evidence directories before terminal reporting.

## Scientific boundary

- UNKNOWN: whether a valid 44-comparator 13-input sorting network exists.
- PUBLISHED snapshot retained: `44 <= S(13) <= 45` for comparator count.
- No 44-comparator candidate appeared in E1, E2, or E4.
- No target-44 reward, label, threshold, tuning signal, or scored E4 objective
  was used.
- No 44-comparator frontier search was run.
- Failure to find 44 is not evidence that 44 is impossible and establishes no
  new lower bound.
- No version 3, alternative search method, publication, push, maintainer
  contact, or novelty claim is authorized.

## Stop

The active goal is complete. This report ends the experiment. Do not continue
searching automatically.
