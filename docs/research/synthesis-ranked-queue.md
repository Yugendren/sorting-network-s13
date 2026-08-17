# Cross-Domain Research Synthesis — Ranked Experiment Queue

Date: 2026-08-17. Inputs: the four survey documents in this directory
(`xdomain-group-theory.md`, `xdomain-symbolic-search.md`,
`xdomain-bound-theory.md`, `xdomain-hardware-probabilistic.md`), each
grounded against the measured M0b/M2a/M2b bottleneck profile.

> **CORRECTION (2026-08-17, machine-checked)**: independent re-derivation
> (`tools/verify_shape_case_split.py`, `docs/s13-shape-case-split.md`)
> found the "5 classes" below was an enumeration slip. The corrected
> count is **3 unordered root-split classes** (84 of 208,012 plane
> shapes; 6 up to reflection) — the argument itself reproduced exactly
> and is *sharper* than claimed. C3 (the 4|9 split) is the cheapest
> class to kill. One silent assumption (E1′: the per-network,
> un-minimised form of van Voorhis's bound) carries the whole split and
> must be confirmed against the primary source before any campaign
> relies on it. Read the corrected document, not this section's numbers.

## The headline: a five-front battle plan for S(13) >= 45

The bound-theory survey computed (this session, from F(13)=392 and
log2 F(13) = 8.615, only 0.39 bits of slack) that **only 5 root
tree-shape classes are consistent with a 44-comparator network** — every
other shape forces >= 513 reachable outcomes and hence >= 45 comparators.
Therefore:

> S(13) = 45 can be proven by 5 independent restricted exhaustions, one
> per surviving shape class. Each is dramatically smaller than the full
> n=13 space. And the attack is win-win: exhausting a class either
> refutes it or *finds the 44-comparator witness inside it*.

Combined with the D(9)-pattern prefix decomposition (group-theory
survey) and structured duplicate detection (symbolic survey), each class
campaign further splits into independent per-prefix jobs with separately
checkable certificates — distributable across machines, and immune to
the u32 certificate-step cap. This composition — case-split by
information-theoretic shape analysis, then canonical-prefix
decomposition, then the M2 memory-reduced engine per job — is the novel
methodology of this programme.

## Ranked queue

### Tier 1 — engineering multipliers (days each, low risk, land first)

| # | Experiment | Expected gain | Source survey |
|---|---|---|---|
| 1 | Packed-u64 bit-packing + SIMD (NEON) `Subsume::search` | 1.5–2.5× time, 8× transient memory, bit-identical | hardware |
| 2 | Weight-histogram thermometer pre-filter (provably one-sided) | ×1.2–2 on top of #1; same code area | hardware |
| 3 | Feature-vector signature pre-filter in `OutputSetIndex` (E-prover/SatELite lineage, 64-bit invariant signatures) | attacks the measured ~50% index-traversal cost of the on-line path; ~100 lines | symbolic |

These three change the arithmetic for everything downstream (including
whether GPU offload is worth building at all). GPU (SIGMo-style batched
matching, 30–90× literature numbers on our workload shape) is
**deferred** until after they land.

### Tier 2 — kernel and scale-out (1–2 weeks each)

| # | Experiment | Expected gain | Source survey |
|---|---|---|---|
| 4 | Glasgow-subgraph-solver technology in the exact matcher (bit-parallel all-different, nogoods/restarts, component decomposition) | 2–5× on the exact test | group theory |
| 5 | Structured duplicate detection keyed on (width, popcount): external-memory sharding, monotone along DAG edges and subsumption-compatible | 16–58× memory at ~+24% time (published); enables NVMe spill + multi-node | symbolic |
| 6 | D(9)-pattern canonical 2/3-layer prefix decomposition (Codish-style representatives, a few hundred at n=13) | distribution + certificate-cap workaround; measure cross-prefix memo-sharing loss first | group theory |

### Tier 3 — theory (the biggest levers, least certain timelines)

| # | Experiment | Expected gain | Source survey |
|---|---|---|---|
| 7 | **"Huffman2"**: generalize van Voorhis's two-channel theorem to partial networks with unequal leaf bounds, as Harder did for the one-channel theorem; Isabelle-templated certificate rule | strictly dominates current pruning where the memo mass sits — exponential effect | bound theory |
| 8 | **Five-shape root case-split → S(13) >= 45 campaign** (the headline above) | reduces the open problem to 5 bounded campaigns | bound theory |
| 9 | Knuth/Burnside sampling estimator calibrated on n=9/10/11 to budget each class/prefix job with error bars before committing compute | planning accuracy | group theory |

Blocking item for #7: the van Voorhis Plenum 1972 book chapter —
only F(N)'s recursion is verifiable online; the P(2,N) semantics need
the primary source (inter-library loan / library scan; USER ACTION).

## Ideas killed, with citations (negative results that save weeks)

- **ZDD frontier compression**: ISAAC 2024 — family-algebra subsumption
  ops have worst-case exponential blow-up; permuted subsumption breaks
  literal containment. (symbolic)
- **Canonical labeling to replace `subsumes_permuted`**: canonization
  decides equality-mod-permutation (already O(1) here); containment-
  mod-permutation is a sub-isomorphism CSP — same class as subgraph
  isomorphism. Attack with embedding tech (#4), not canonization.
  (group theory)
- **Roaring bitmaps**: mis-fit — our bitsets are dense fixed-width.
  (hardware)
- **Learned indexes for the dominance query**: no published support;
  CIP'02 proves no exact sublinear subset-query structure exists —
  vindicates filter+verify as the only architecture. (hardware)
- **Global LP/SDP relaxations, sensitivity/polynomial methods, KLMPSS,
  exact-merging-cost shortcut (I2(7)=9>7 disproves it)**: assessed and
  killed in the bound-theory survey with session computations.

## Recommended immediate sequence

1. One lead campaign: Tier-1 items #1+#2+#3 together (they share code
   areas), validated by the standard protocol (n=9/n=10 bands +
   unchanged checker).
2. In parallel: draft the five-shape case-split as a formal document
   (`docs/s13-shape-case-split.md`) with machine-checked shape
   enumeration — this is the paper skeleton.
3. User: request the Plenum 1972 van Voorhis chapter (ILL).
4. After Tier 1 lands: re-run the n=11 benchmark, update all n=13
   budgets via #9, then decide Tier 2 order.
