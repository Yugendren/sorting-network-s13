# Execution scope

`METHOD_EXPERIMENT_CONTRACT_V1.md` is the active scientific execution
authority. Read it completely before acting, then read `GOAL_STATE.md`, the
predecessor `PROJECT_CONTRACT.md`, and inspect Git, dependencies, and evidence.

The completed B0--B4 baseline is immutable. Never alter, delete, or regenerate
anything under `evidence/b0` through `evidence/b4`. Its canonical report is
`evidence/b4/b4-20260815T014232Z/baseline-report.md`.

The active goal has one learned-method hypothesis and at most two versions:

1. E0 freezes sources, seeds, features, budgets, hardware, evidence rules, and
   the version-1 truncation-ranker role;
2. E1 instruments unchanged SENSO and builds development data at target 45;
3. E2 trains and freezes one small completion-value model;
4. E3 runs one paired 60-seed, 50,200-evaluation-per-method exam;
5. E4 may change exactly one major element and run one new exam if E3 fails;
6. E5 runs one bounded 44-comparator campaign only if a method version passes.

Do not use target 44 in training, features, reward, model selection, E3, or E4.
Do not add RL, diffusion, MCTS, LLM/multi-agent search, SAT lower-bound work,
unrelated methods, paid compute, or a third version. LLMs are never scored
inner-loop oracles. A negative reproducible result is completion.

Work serially with one falsifiable gate active. Preserve every scored success,
failure, crash, and timeout with exact commands, hashes, resources, and a
complete immutable inventory. Every claimed successful network must pass both
unchanged B1 verifiers. Holdout leakage, verifier disagreement, or failed
integrity replay is `INVALID`.

If a 44-comparator candidate appears, stop search, freeze it, run the two frozen
verifiers, and follow only the contract's witness-audit procedure. Do not
publish or contact anyone.

Authority order:

1. `METHOD_EXPERIMENT_CONTRACT_V1.md`
2. `GOAL_STATE.md`
3. E0-frozen configuration and manifests
4. `PROJECT_CONTRACT.md` for immutable baseline facts not superseded above
5. primary sources
6. implementation convenience
