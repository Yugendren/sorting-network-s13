# S(13) Solution Strategy

Last updated: 2026-08-17. Branch: `main` (now carries full history of
`goal/s13-baseline` → `goal/s13-method-v1` → `goal/s13-feature-eng-v1-omp`).

## The problem

Determine whether a 13-input sorting network needs 44 or 45 comparators.
Known (re-audited 2026-08-15): `44 <= S(13) <= 45`. Exactly one of two
outcomes settles it:

1. **Find a valid 44-comparator network** → S(13) = 44. A search problem.
2. **Prove no 44-comparator network exists** → S(13) = 45. A proof problem
   (exhaustive generate-and-prune or SAT, the way S(11)=35 and S(12)=39
   were settled).

Honest prior: the community's expectation is that 45 is optimal. If that is
true, *no amount of searching will ever find a 44* — only the proof route
settles it. The search route is cheap and has a spectacular payoff if the
prior is wrong; the proof route is expensive but is the only guaranteed
path to an answer.

## Baseline: what we already have (yes, we have one)

| Asset | Status | What it gives us |
|---|---|---|
| SENSO evolutionary search (frozen binary, hash-pinned) | Working | Reproducibly finds 45-comparator networks (e.g. seed 18); ~2/60 seeds succeed at 45 within the 50,200-eval budget |
| Two independent verifiers (Python + Go, hash-pinned) | Working | Ground truth for any candidate; both must accept |
| Matched-compute exam protocol | Frozen | Fair comparison harness: 50,200 evaluations/seed, 60 paired seeds, six criteria |
| Random baseline (`src/random_baseline.py`) | Working | Floor reference |
| sortnetopt (Harder's S(11)/S(12) proof tool) | Ported, replayed n=9 and n=11 certificates | The only known proof-route machinery |
| Negative results (v1, v2 rankers) | Frozen evidence | Learned truncation ranker: concordance 0.446 (<0.5 fail); exam 0/60 vs SENSO 2/60 |

So the bar any new method must clear: **beat SENSO's 2/60 at target 45
under matched compute**, and ultimately produce a dual-verified
44-comparator witness.

## Attack plan (ranked by expected value)

| # | Approach | Route | Why | Feasibility on our hardware |
|---|---|---|---|---|
| 1 | **LLM-driven heuristic evolution** (AlphaEvolve/FunSearch style): Claude writes and mutates *programs* that construct/complete networks; the frozen verifiers + comparator count are the fitness function | Find 44 | Uses our biggest asset (the LLM) where it is strongest — writing code and inventing heuristics — in the *outer* loop, so scoring stays cheap and deterministic | High — pure local compute, LLM calls only between generations |
| 2 | **Symmetry-restricted search**: restrict to networks symmetric under channel reversal (Valsalam–Miikkulainen); this shrank the space and produced best-known networks for n=17–22 | Find 44 | Halves effective search space; the 45-witness class is known to be symmetric-friendly | High |
| 3 | **Prefix-restricted SAT synthesis**: fix strong first layers (Green filter / optimal prefixes up to symmetry), SAT-encode "complete this prefix to 44 total" per prefix slice | Find 44, partial evidence toward 45 | Full n=13 SAT is out of reach, but prefix-constrained slices are tractable; each UNSAT slice is real evidence toward 45 | Medium — instance-size dependent; needs experimentation |
| 4 | Improved learned ranker (current v2 feature-engineering programme) | Find 44 | Already scaffolded (F0 in progress); but two prior versions failed and the concordance ceiling looks low | High, but low prior of success |
| 5 | Full generate-and-prune proof at n=13 (sortnetopt scaled up) | Prove 45 | The only definitive route if 45 is optimal | **Low** — n=12 needed massive cluster compute; n=13 is orders of magnitude worse. Track pruning-theory improvements; not runnable locally today |

**Recommended play**: run #1 + #2 together (LLM-evolved constructors over a
symmetry-restricted space, verified by the frozen dual verifiers), with #3
as the second track once #1's infrastructure exists. Keep #4 alive only if
its F2 concordance gate passes cheaply. Log every scored attempt
append-only as before.

## Governance note

The v2 contract's prohibitions (no SAT work, no LLM inner-loop, no MCTS,
two-version cap) were per-goal choices scoped to
`goal/s13-feature-eng-v1-omp`. Working on `main` toward the open problem
itself requires a **new goal contract** (v3) that authorises the chosen
attack(s). Non-negotiables to carry forward regardless:

- B0–B4 and all predecessor evidence remain immutable.
- Every claimed network must pass both frozen verifiers.
- Target 44 candidates trigger the witness-audit procedure: stop, freeze,
  dual-verify, no publication or external contact without user approval.
- Every scored attempt preserved append-only with hashes and commands.

## Immediate next steps

1. User picks the attack mix (recommended: #1 + #2).
2. Draft `METHOD_EXPERIMENT_CONTRACT_V3.md` scoping it (budget, gates,
   success criteria, verdicts).
3. Build the evolution harness: candidate-program sandbox → network
   emitter → dual-verifier scoring → append-only ledger.
4. First falsifiable gate: does the evolved-heuristic track beat SENSO's
   2/60 at target 45 under matched compute?
