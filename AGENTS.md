# Execution scope

`METHOD_EXPERIMENT_CONTRACT_V2.md` is the active scientific execution
authority for the feature-engineering branch. Read it completely before
acting, then read `GOAL_STATE.md`, the predecessor contracts
(`METHOD_EXPERIMENT_CONTRACT_V1.md`, `PROJECT_CONTRACT.md`), and inspect
Git, dependencies, and evidence.

The completed B0–B4 baseline and E0–final evidence are immutable. Never
alter, delete, or regenerate anything under `evidence/b0` through
`evidence/b4` or `evidence/e0` through `evidence/final`.

The active goal has one feature-engineering hypothesis and at most two
ranker versions:

1. F0 freezes sources, seeds (including any Group-E extra seeds), the v2
   feature schema, model config, and evidence rules;
2. F1 instruments unchanged SENSO and builds a diversified training dataset
   with the v2 feature set;
3. F2 trains and freezes one small ranker on the diversified dataset;
4. F3 runs one paired 60-seed, 50,200-evaluation-per-method exam;
5. F4 may change exactly one element (feature set, data strategy, or
   objective) and run one new exam if F3 fails;
6. F5 runs one bounded 44-comparator campaign only if a ranker version
   passes F3 or F4.

Do not use target 44 in training, features, reward, model selection, F3, or
F4. Do not add RL, diffusion, MCTS, LLM/multi-agent search, SAT lower-bound
work, unrelated methods, paid compute, or a third version. LLMs are never
scored inner-loop oracles. A negative reproducible result is completion.

Work serially with one falsifiable gate active. Preserve every scored
success, failure, crash, and timeout with exact commands, hashes, resources,
and a complete immutable inventory. Every claimed successful network must
pass both unchanged B1 verifiers. Holdout leakage, verifier disagreement, or
failed integrity replay is `INVALID`.

If a 44-comparator candidate appears, stop search, freeze it, run the two
frozen verifiers, and follow only the contract's witness-audit procedure.
Do not publish or contact anyone.

Authority order:

1. `METHOD_EXPERIMENT_CONTRACT_V2.md`
2. `GOAL_STATE.md`
3. F0-frozen configuration and manifests
4. `METHOD_EXPERIMENT_CONTRACT_V1.md` and `PROJECT_CONTRACT.md` for
   immutable baseline facts not superseded above
5. primary sources
6. implementation convenience
