# S(13) Research Programme — Definitive-Answer Track

Last updated: 2026-08-17. Companion: `SOLUTION_STRATEGY.md`,
`docs/evolution-harness-design.md`, `docs/sota-survey.md` (literature).

## Thesis

Only the proof route is guaranteed to terminate with an answer. The
programme therefore treats "settle S(13)" as a **proof-engineering
problem**: take the exact algorithm class that settled n=9–12
(generate-and-prune over prefix output-sets with subsumption pruning;
Codish et al. 2014, Harder's sortnetopt 2021) and attack its exponential
wall with (a) hardware it was never built for, (b) ML that reorders but
never replaces exact mathematics, and (c) machine-checked new pruning
lemmas. Search-for-44 continues in parallel because it is nearly free and
wins instantly if a 44 exists.

## Why this can work (the case for optimism, corrected by the survey)

Survey findings (`docs/sota-survey.md`, 2026-08-17) that anchor the plan:

- **Method that settled n=11/12**: Harder's sortnetopt is a *top-down DP
  over sequence sets* with a Huffman-style generalization of van
  Voorhis's bound — not classic generate-and-prune. n=11: 4h51m and
  178 GiB RAM on one 24-core box; S(12)=39 followed free via van
  Voorhis. Isabelle/HOL-verified certificate.
- **The n=13 wall is MEMORY, not compute**: Harder's own estimate for a
  direct n=13 run is >20,000 TB of RAM. So the attack is on the memory
  exponent: on-line subsumption, out-of-core sharding, tighter interval
  seeding — not raw FLOPs.
- **Known, untried headroom**: Harder's n=11 certificate needed only
  12.7M steps versus 2.46B sets explored (~195× waste), and he *named*
  the fixes (on-line subsumption, Huffman-aware SAT encoding) without
  ever implementing them. The gap to close is ~100–1000×, with a ~195×
  mechanism already identified by the method's own author.
- **Nobody is competing**: sortnetopt has zero forks; no arXiv paper
  attacked S(13) in 2022–2026; no GPU implementation exists. The
  2014→2020 trajectory delivered ~10^6× speedups (S(9): 12 cluster-days
  → 0.5 s) and then everyone stopped.
- **ML fits where exactness survives**: learned branching/ordering in
  complete solvers (NeuroCore/Graph-Q-SAT lineage) — ML orders and
  filters, exact math decides. Trainable on solved n≤12 with instant
  ground truth.
- **GPU caveat**: Dedekind D(9) fell to GPUs in 2023, but that problem
  was compute-bound; ours is memory/random-access-bound. GPUs help on
  the compute-bound pieces (subsumption matching, bound evaluation),
  not as the headline weapon.
- LLM-assisted lemma discovery (architect tier) hunts new
  dominance/symmetry arguments; every lemma is machine-checked before it
  prunes anything, so creativity carries zero soundness risk.

Also noted: the 44 lower bound itself is 2025 *folklore* (van Voorhis's
two-channel theorem applied to S(11)=35, giving 35+⌈log2 392⌉=44), never
written up rigorously — a small publishable result sitting on the table.

## Dual-track structure

| Track | Question | Terminates? | Cost |
|---|---|---|---|
| A: Evolution harness (44-hunt) | Does a 44 exist? | Only if yes | Near-zero (idle CPU + LLM outer loop) |
| B: Proof engineering | Is 44 impossible? | **Yes, if made feasible** | The real investment |

A 44 found by Track A immediately ends Track B. Track B progress
(prefix-space exhaustion for restricted classes) also narrows where
Track A should search — the tracks feed each other.

## Track B milestones (each falsifiable, each with a kill/pivot rule)

| # | Milestone | Success criterion | Pivot rule |
|---|---|---|---|
| M0 | Baseline replication & profiling | sortnetopt replays n=9, n=11 locally (done in B3); profile n=9→11 to find the true hot loops and memory curve | — |
| M1 | Scaling law | Measured cost model fit on n=9,10,11 (+n=12 partial); extrapolated n=13 cost with error bars | If extrapolation says >10^4× beyond reach even with 100× speedup, shift weight to M4 (restricted classes) |
| M2 | On-line subsumption + out-of-core | Implement Harder's own named-but-untried fixes inside sortnetopt's DP; target ≥50× step/memory reduction on the n=11 replay (ground truth known, verification instant) | <10× → profile where the waste actually lives, one redesign |
| M3 | Learned guidance + GPU offload | ML expansion-ordering/interval seeding (incl. 44-seeded intervals) with bit-identical final certificates; GPU kernels for the compute-bound pieces (subsumption matching, bound evaluation) | No node reduction → keep exact pipeline, drop ML guidance |
| M4 | Restricted-class exhaustion | Prove "no 44 exists within class X" for growing classes X (e.g. fixed optimal first two layers, reversal-symmetric networks) — publishable partial results, each a replayable certificate | Classes chosen by measured cost, largest informative first |
| M5 | Full n=13 campaign | Distributed, disk-backed, checkpointed run across all 3 machines; emits independent-verifier-replayable certificate | Go/no-go decided strictly by M1–M3 numbers |

## Non-negotiable soundness rules

1. ML may **order** and **filter**, never **decide**. Every pruning
   decision traces to an exact, machine-checked criterion.
2. Every completed (sub)proof emits a certificate replayable by an
   independent checker (same discipline as the B1 dual verifiers).
3. Determinism and checkpointing: any multi-week run must resume
   bit-identically after power loss.
4. Any 44-candidate from either track: stop, freeze, dual-verify,
   witness-audit procedure. No publication or external contact without
   user approval.

## Hardware assignment

| Machine | Track B role |
|---|---|
| M4 Mac mini | Orchestrator, frontier database, certificate checker, LLM sessions |
| 3060 box #1 | GPU subsumption/prune kernels |
| 3060 box #2 | GPU kernels + ML heuristic training (small models) |

## Governance

Requires a v3 contract on `main` authorising lower-bound/proof work
(the v2 ban was scoped to the feature-engineering goal). Carry forward:
immutable evidence, append-only ledgers, dual verification, one active
falsifiable gate at a time.

## Immediate next actions

1. Literature survey lands in `docs/sota-survey.md` (agent running) —
   confirm no one has already done the GPU/ML attack, and extract
   Harder's exact n=12 cost numbers as the anchor for M1.
2. Draft v3 contract scoping Track A + Track B, M0–M2 first.
3. M0: profile the existing sortnetopt port on n=9 and n=11 replays.
