# Execution scope

`PROJECT_CONTRACT.md` is the scientific execution authority. Read it completely
before acting, then read `GOAL_STATE.md` and inspect Git, dependencies, and
evidence.

The active goal is baseline-only:

1. freeze the current problem and source snapshot;
2. establish two independent witness verifiers;
3. reproduce a known 45-comparator constructive baseline under frozen seeds;
4. reproduce the small exact workflow and replay Harder's published n=11
   certificate;
5. issue one baseline verdict and stop.

Do not search for a 44-comparator network. Do not attempt to prove that 44 is
impossible. Do not train ML/RL models, use diffusion, add an LLM search loop,
rent a GPU, or begin the Mericanii experimental method. These require a later
contract after `BASELINE_READY`.

Work on one milestone and one falsifiable gate at a time. Preserve failed and
timed-out runs. A solver status or unsuccessful search is not a proof. Every
accepted network must pass both independent verifiers. Every lower-bound claim
must use an independently replayed certificate tied to the exact formula or
derivation.

Authority order:

1. `PROJECT_CONTRACT.md`
2. `GOAL_STATE.md`
3. frozen configuration and test manifests
4. primary-source documentation
5. implementation convenience

If the live audit shows that `S(13)` has already been settled, stop with
`STALE_TARGET`; do not silently choose a different open problem.

