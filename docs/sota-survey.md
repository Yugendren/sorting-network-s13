# State of the Art: The S(13) Optimal Sorting Network Problem

**Survey date:** 2026-08-17
**Open problem:** Does a 13-input sorting network require 44 or 45 comparators? Current status: **44 <= S(13) <= 45.**

All claims below are sourced from primary documents (arXiv full texts, GitHub repos, raw HTML of Dobbelaere's tables, OEIS, HackerNews author comments). Numbers that came through lossy PDF/HTML extraction and could not be cross-checked against a second source are flagged with (unverified).

---

## Key takeaways for our attack plan

1. **The gap is exactly one comparator, and this is newer news than most people know.** The published literature (Wikipedia, Harder 2020) gives only S(13) >= 43 via the classic van Voorhis recurrence. The bound of **44** dates from **April 2025**: Bert Dobbelaere, on a suggestion by Jelmer Firet, applied van Voorhis's lesser-known *two-channel* theorem S(N) >= S(N-2) + P(2,N) with P(2,N) >= ceil(log2 F(N)) to Harder's S(11)=35: F(13)=392, so S(13) >= 35 + 9 = 44. This exists only as a SorterHunter changelog entry and a gist — **no paper**. We independently re-ran Dobbelaere's gist code during this survey and reproduced F(13)=392. Writing this argument up rigorously (or formally) is publishable low-hanging fruit and de-risks our foundation.
2. **The problem therefore splits into two asymmetric sub-attacks:** (a) *find* a 44-comparator network — cheap to attempt (CEGAR SAT synthesis over the 117 canonical two-layer prefixes, SorterHunter-class stochastic search); 30 years of failure since Juillé's 45 (1995) is weak evidence none exists; (b) *prove* S(13) >= 45 — requires a Harder-style or generate-and-prune-style exhaustive lower-bound computation. Nobody has published a cost estimate for the certificate-targeted variant of (b).
3. **Harder's own estimate for a direct n=13 run of his DP: ">20,000 TB of RAM and proportionally longer" (HN, 2021)** — but his certificate for n=11 has only 12.7M steps versus 2.46B sequence sets explored, a **~195x gap between the work done and the work needed**. He explicitly names *on-line subsumption during search* as the untried idea that could close this gap, plus a *CNF/SAT encoding that exploits the Huffman bound*. Neither has been attempted by anyone, 2021-2026.
4. **The field is empty.** sortnetopt has 0 forks and no issues; no arXiv paper 2022-2026 attacks S(13) size-optimality; no distributed/BOINC effort exists; no GPU implementation of generate-and-prune or the Huffman-bound DP exists. Any headroom we exploit is uncontested.
5. **The algorithmic trajectory is violently favorable.** S(9) cost 12 days on 144 cores (2014) -> 29 h on 32 cores (Frasinaru-Raschip matching-based subsumption, 2017/2019) -> 44 min on 16 cores (Harder's sortnetopt-gnp: k-d tree over output sets + bipartite matching) -> **0.5 s / 58 MiB** (Harder's Huffman-bound DP, 2020). Two independent 10^4-10^7x speedups landed within six years, then everyone stopped. S(11) — expected to be out of reach — fell for ~5 CPU-hours of search + 178 GiB RAM on one 24-core box.
6. **The bottleneck is memory capacity and random access, not FLOPs** (Harder's own diagnosis). Growth in bounded sequence sets is ~12,000x per +2 channels (206,279 at n=9 -> 2.46x10^9 at n=11 -> naive ~3x10^13 at n=13, i.e. petabyte-scale tables). Attack surfaces: (i) on-line subsumption to keep only the ~certificate-sized frontier; (ii) starting the successive-approximation DP from the *44* lower bound instead of 43 (the interval to fathom is half as wide); (iii) out-of-core / sharded canonical-form tables (NVMe, CXL); (iv) exploiting that we only need s(13) >= 45, not the exact value.
7. **GPU precedent exists but transfer is not automatic.** The 9th Dedekind number (2023) — a symmetry-reduced enumeration over monotone Boolean functions, structurally cousin to output-set lattices — took only 5,311 A100 GPU-hours (vs 47,000 FPGA-hours independently). But D(9) was compute-bound with modest memory; the sorting-network DP is memory-bound. GPUs plausibly help the *subsumption/matching* inner loops (bitset ops over 2^13-bit sets are tiny) if the table can be sharded.
8. **ML can help only in one place: exactness-preserving search guidance.** No learning-based method has even matched the 1995 upper bound of 45 at n=13 (DQN construction is ~6 comparators off optimal already at n=10). But learned branching/ordering inside complete solvers (NeuroCore +10-11% solved UNSAT-heavy benchmarks; Graph-Q-SAT 2-3x fewer iterations; Neuro# orders-of-magnitude on family-trained #SAT) only reorders complete search — train on solved n=9/11 instances, deploy on n=13, soundness untouched. AlphaDev/AlphaTensor/FunSearch/AlphaEvolve are constructors (upper bounds only); AlphaEvolve is the natural off-the-shelf tool for attack (a) since candidate networks are trivially checkable (2^13 = 8,192 vectors).
9. **Verification is a solved template.** Both proof lines end in machine-checked certificates: Coq-extracted checker for S(9) (27 GB of witnesses, checked in under a week) and Isabelle/HOL-extracted checker for S(11) (2.9 GB certificate, checked in 34 min). Any S(13) result must ship a certificate; Harder's 4-rule derivation system (Triv/PH/Succ/Huffman) is reusable as-is.
10. **Realistic assessment:** attack (a) is cheap and should be run first/continuously; attack (b) needs roughly a 100-1000x memory reduction over Harder's direct extrapolation before it fits any real machine. The identified-but-untried ideas (on-line subsumption, 44-seeded intervals, Huffman-aware SAT, matching+k-d-tree subsumption fused into the DP) are exactly the multipliers to prototype at n=9/n=11 where ground truth is instant/cheap.

---

## 1. Status of the bounds: where 44 and 45 come from

| n | 9 | 10 | 11 | 12 | **13** | 14 | 15 | 16 | 17 |
|---|---|----|----|----|--------|----|----|----|----|
| S(n) lower | 25 | 29 | 35 | 39 | **44** | 48 | 53 | 57 | 63 |
| S(n) upper | 25 | 29 | 35 | 39 | **45** | 51 | 56 | 60 | 71 |

Source: [Bert Dobbelaere, "List of sorting networks"](https://bertdobbelaere.github.io/sorting_networks.html) (last updated 2025-11-07; verified from raw HTML for this survey). Best known 13-input networks: **(45 comparators, 10 layers)** and (46 comparators, 9 layers). Depth T(13)=9 is proven (Bundala-Zavodny 2014).

- **Upper bound 45:** Hugues Juillé (1995), found by the END evolutionary algorithm (LNCS 929, pp. 246-260), improving a 25-year-old 46-comparator record by one; listed in Knuth TAOCP Vol. 3 sect. 5.3.4. Unimproved for 30 years despite SENSO (2013), SorterHunter, and SAT-based search all reproducing exactly 45.
- **Lower bound 44:** *not* the classic chain S(13) >= S(12) + ceil(log2 13) = 39+4 = 43. It is van Voorhis's two-channel relation **S(N) >= S(N-2) + P(2,N)**, P(2,N) >= ceil(log2 F(N)) with F defined by a recursive min over merge-tree shapes, from the same 1972 paper ([D.C. Van Voorhis, "Toward a Lower Bound for Sorting Networks", Complexity of Computer Computations, Plenum 1972, pp. 119-129](https://link.springer.com/chapter/10.1007/978-1-4684-2001-2_12)). F(13)=392 => P(2,13) >= 9 => S(13) >= S(11)+9 = 44. Applied 2025-04-21 by Dobbelaere on Jelmer Firet's suggestion (SorterHunter commit cac0ebac; [Dobbelaere's F(N) derivation gist](https://gist.github.com/bertdobbelaere/0a30f5321965732b59c102fa9e3250bb) — we re-ran it and reproduced F(13)=392, and the same recursions reproduce his 48/53/57/63 for n=14..17). **No indexed paper by Firet exists; treat S(13) >= 44 as folklore-verified from van Voorhis's published theorem, not a peer-reviewed result.**
- **Stale sources:** [Wikipedia's Sorting network article](https://en.wikipedia.org/wiki/Sorting_network) still lists 43..45 for n=13; [OEIS A003075](https://oeis.org/A003075) is exact through a(12)=39 and marks 45 for n=13 as *conjectured* (a(11)-a(12) added by Harder, Dec 2019).
- Framing statistic: depth optimality is known through n=17; size optimality lags five channels behind at n=12.

**Citation trap** (relevant when writing anything up): Codish et al. 2014 state van Voorhis as "S(n+1) >= S(n) + ceil(log2 n)"; Harder/Knuth/Wikipedia state S(n) >= S(n-1) + ceil(log2 n). These disagree just above powers of two; the historical bound tables confirm the second form is correct.

---

## 2. How S(9)=25 and S(10)=29 were proved (Codish, Cruz-Filipe, Frank, Schneider-Kamp 2014)

**Papers:** ["Twenty-Five Comparators is Optimal when Sorting Nine Inputs (and Twenty-Nine for Ten)"](https://arxiv.org/abs/1405.5754) (arXiv:1405.5754, ICTAI 2014); journal version ["Sorting nine inputs requires twenty-five comparisons"](https://www.sciencedirect.com/science/article/pii/S0022000015001397), JCSS 82(3):551-563, 2016.

**Method.** Generate-and-prune (Parberry's idea made feasible), iterating **one comparator at a time**, not layer by layer. Maintain a complete set R_k of k-comparator prefixes modulo subsumption: Generate extends every network in R_k by each of the n(n-1)/2 comparator positions (skipping redundant comparators — Graham's criterion — which cuts peak set size >40% and halves runtime); Prune deletes every network subsumed by a retained one. Each network is stored with its **output set** outputs(C) = {C(x) : x in {0,1}^n} (0/1 principle), partitioned by Hamming weight. **Subsumption:** C_a subsumes C_b iff some channel permutation pi has pi(outputs(C_a)) a subset of outputs(C_b); the key lemma (via Knuth's untangling of generalized networks, ex. 5.3.4.16) shows subsumed networks can be discarded without losing any optimal-size sorting network. Fast refutations: per-weight cardinality comparison kills >70% of subsumption tests; position-set invariants ("where can value x sit at weight k") kill ~15% more and restrict the permutation search. If |R_k| reaches 1 at k with no sorting network of size k-1 surviving, S(n)=k. Note: **symmetry breaking here is implicit in subsumption + untangling** (all first comparators are equivalent, so |R_1|=1); fixed-first-layer/saturated-layer symmetry breaking belongs to the *depth* line (Section 4).

**Quantitative record (n=9):**
- Search space: 36^24 ≈ 2.2x10^37 candidate 24-comparator networks (36 = C(9,2) positions); reduced to ~3.3x10^21 reachable via the 914,444 representatives at k=14.
- |R_k| peaks at **|R_14| = 914,444** (|N_14| = 18,420,674 before pruning). Full table: 1, 3, 7, 20, 59, 208, 807, 3415, 14343, 55991, 188730, 490322, 854638, **914444**, 607164, 274212, 94085, 25786, 5699, 1107, 250, 73, 27, 8, 1.
- >10^13 subsumption checks, worst case 9! = 362,880 permutations each; sequential estimate ~9 CPU-years.
- **Hardware:** cluster of 144 Intel E8400 cores @ 3 GHz, 288 threads; SWI-Prolog + BEE + CryptoMiniSAT. Reaching R_14 took **7 d 17 h 58 m**; finishing k=15..25 by pure generate-and-prune took ~5 more days. The hybrid SAT finish (914,444 UNSAT instances from R_14) totaled 3,028 CPU-hours + 333 h overhead ≈ **12 h wall on 288 threads**.
- Largest file (N_15): ~11 GB; ~27-50 GB of proof witnesses overall.
- S(10)=29 follows free via van Voorhis from S(9)=25, matching Waksman's 1969 network. Propagated pre-2019 lower bounds: S(11..16) >= 33, 37, 41, 45, 49, 53.

**Formal verification follow-ups:** Coq-certified extracted checker ([arXiv:1502.05209](https://arxiv.org/abs/1502.05209), ITP 2015; [arXiv:1502.08008](https://arxiv.org/abs/1502.08008), CICM 2015; journal: [Cruz-Filipe, Larsen, Schneider-Kamp, JAR 59(4):425-454, 2017](https://link.springer.com/article/10.1007/s10817-017-9405-9)). Untrusted oracle shortcuts ~1.6M NP-complete subsumption witnesses; after optimization the full n=9 proof verified "in under a week on a modest processor" (memory was the bottleneck). Logs and an independent Java verifier (n=9 in ~6 h) at [imada.sdu.dk/~petersk/sn/](https://imada.sdu.dk/~petersk/sn/).

**Later speedups of the same computation** (the clearest measure of algorithmic headroom in this field):

| Year | Who | S(9) full run | Hardware |
|---|---|---|---|
| 2014 | Codish et al. | ~12 days | 144 cores / 288 threads |
| 2017/19 | [Frasinaru & Raschip](https://arxiv.org/abs/1707.08725) (CPAIOR 2019) | 29 h | 32 Xeon E5-2670 cores |
| 2020 | [Harder, sortnetopt-gnp](https://github.com/jix/sortnetopt-gnp) | 44 min | 16-core Ryzen 9 3950X |
| 2020 | [Harder, sortnetopt DP](https://github.com/jix/sortnetopt) | **0.5 s / 58 MiB** | laptop-class |

Frasinaru-Raschip replaced brute-force permutation enumeration in subsumption by **enumeration of perfect matchings in a bipartite "subsumption graph"** of compatible channels (example: (n,k)=(8,9) drops from 4.97x10^9 permutation checks to 1.30x10^6 matchings, >3800x (unverified)); >10x overall. Harder's gnp added a k-d-tree over output sets keyed by channel-abstraction vectors, testing whole subtrees at once.

---

## 3. How S(11)=35 and S(12)=39 were proved (Jannis Harder, sortnetopt, 2020)

**Sources:** [arXiv:2012.04400, "An Answer to the Bose-Nelson Sorting Problem for 11 and 12 Channels"](https://arxiv.org/abs/2012.04400) (v1 Dec 2020, v3 Jul 2022; apparently never journal/conference published); code [github.com/jix/sortnetopt](https://github.com/jix/sortnetopt); blog [Part 1](https://jix.one/proving-50-year-old-sorting-networks-optimal-part-1/), [Part 2](https://jix.one/proving-50-year-old-sorting-networks-optimal-part-2/) (series unfinished); [HN thread with author comments](https://news.ycombinator.com/item?id=27047108); certificate at Zenodo DOI 10.5281/zenodo.4108365.

### 3.1 Algorithm — not generate-and-prune, and not SAT

Harder recurses **top-down over "sequence sets"** X subset of B^n (the sets of Boolean vectors a partial sorting network must still sort), defining s(X) = minimal comparators to sort every element of X; s(B^n) = S(n). Components:

- **Successor recurrence:** s(X) = 1 + min{ s(X^[i,j]) } over non-redundant comparators, giving optimal substructure for dynamic programming over canonicalized sets.
- **The Huffman bound (the crucial novelty):** van Voorhis's bound generalized to arbitrary sequence sets. For prunable channels i (one-hot vector in X), s(X) >= the value of running **Huffman's algorithm** in the algebra (N0, <=, 1+max) over the multiset {s(X/i)} of pruned subproblem bounds. Van Voorhis's ceil(log2 n) tree-height argument is the equal-leaves special case. Computed for both X and its negation (the bound is permutation- but not negation-invariant). Per the blog, integrating van Voorhis's bound into computer search had never been attempted before.
- **Well-behaved interiors:** the recursion is restricted to unions of threshold sets (computed by two DFS passes over the induced Hasse-diagram subgraph), guaranteeing prunable channels always exist.
- **Successive approximation:** every canonical set carries an interval b(X) containing s(X), initialized to [1, best-known-upper-bound] — so known networks are exploited, never rediscovered. Intervals tighten via SuccessorUpdate, HuffmanUpdate, and a single-prunable-channel shortcut, until s(B^11) is fathomed.
- **Data structures:** sequence sets as 2^n-bit vectors (packed in the memo table, unpacked to byte-per-element for ops); canonicalization modulo S_n x negation via a **custom Traces-style (McKay/Piperno) canonical labeling working directly on the bit-vector**; shared concurrent memo table with per-entry locking; custom Rust async-await work-scheduling runtime. Single machine, multithreaded — **not distributed** ("all cores do frequent random accesses to all the used memory").
- **Subsumption** (X subsumes Y iff a permuted/negated copy of X is a subset of Y) is used **only offline, during certificate generation** — not during search. Pipeline: order-invariant integer abstractions -> per-channel compatibility -> perfect matchings in the bipartite subsumption graph (following Frasinaru-Raschip) -> k-d-tree with bounding-box matching tests to skip whole subtrees.

### 3.2 Cost (paper Section 9; authoritative)

Search machine: AMD EPYC 7401P, 24c/48t @ 2 GHz. Verification: Ryzen 9 3950X.

| Phase (n=11) | Time | Peak RAM |
|---|---|---|
| Search (proves S(11)>=35) | **4 h 51 m** | **178 GiB** (93 GiB written to disk) |
| Pruning subsumed sets | 2 d 3.5 h | 16 GiB |
| Certificate generation | 19 h | 54 GiB |
| Isabelle/HOL-verified check | **34 m** | 6 GiB |

Whole pipeline < 80 h. Scaling: sequence sets bounded / non-subsumed / certificate steps — n=9: 206,279 / 13,034 / 11,934; n=11: **2,462,890,689 / 15,432,816 / 12,659,079**. Harder: "all measured values are consistent with double exponential or even faster growth." **S(12)=39 required no computation**: van Voorhis from S(11)=35 meets the known 39-comparator network. (Symmetrically: proving S(13)=45 would give S(14) >= 49 free — still short of the 51 upper bound.)

### 3.3 Verification

Certificate = derivation in a **4-rule system**: Triv (s(X)>=0), PH (pigeonhole), Succ (successor recurrence, premises may be permuted/negated subsets), Huffman. Checker extracted **from Isabelle/HOL to Haskell** (verified core + unverified parser); trusted base = problem statement + Isabelle kernel + GHC. n=11 certificate: 2,926 MiB (1.2 GB zstd), checked in 34 min / ~6 GiB (≈3 h on a laptop).

### 3.4 What Harder said about n=13

The paper says nothing about 13 channels. On HN (May 2021, user jix, verbatim): *"my estimate is that it would take over **20000 TB of RAM** and take proportionally longer... Distributing the computation would also slow it down a lot as all cores are doing frequent random accesses to all the used memory. So s(12) seems to be the end of what's possible with this exact approach, but I think some of the theory I developed might be usable beyond."* Paper future work: memory is "the biggest obstacle"; **on-line subsumption during search** could let the search directly discover the ~certificate-sized derivation ("performing much less work" — n=11 headroom: 12.7M certificate steps vs 2.46B sets explored, ~195x), but interacted badly with his bound-derivation order; also proposes a **CNF/SAT encoding benefiting from the Huffman bound**. Neither idea has been tried publicly.

---

## 4. SAT-based approaches

### 4.1 Depth optimality: Bundala & Zavodny (LATA 2014)

["Optimal Sorting Networks"](https://arxiv.org/abs/1310.6271) (arXiv:1310.6271). SAT variables g^k_{i,j} (comparator (i,j) in layer k) + per-input value variables; 0/1 principle plus a windows/subsequence lemma limits the inputs encoded. Depth-d optimality = UNSAT of the depth-(d-1) formula. **Two-layer symmetry breaking:** first layer fixed WLOG; second layers restricted to *saturated* layers reduced modulo permutation/reflection — for n=13: 568,504 two-layer nets -> 212 representatives (unverified intermediate counts vary slightly across papers), one SAT instance each. Off-the-shelf MiniSAT 2.2. Results: T(11)=T(12)=8, T(13)=...=T(16)=9. Costs: n=9 depth-6 UNSAT < 1 s (vs Parberry's 1989 estimate of 200 h — 4 orders of magnitude from encoding + solver progress alone); **n=13 depth-8 UNSAT ~11-13 h total** over 212 instances.

[Codish, Cruz-Filipe, Schneider-Kamp, "Efficient Generation of Two-Layer Prefixes"](https://arxiv.org/abs/1404.0948) (SYNASC 2014) generates canonical saturated prefixes grammatically: minimal complete sets R(n) = 48, 50, **117**, 211, 609 for n = 11, 12, **13**, 16, 17. Any fixed-size n=13 attack can reuse the 117 canonical two-layer prefixes. n=13 generation takes under a second.

### 4.2 Ehlers & Muller line

- ["Faster Sorting Networks for 17, 19 and 20 Inputs"](https://arxiv.org/abs/1410.2736): hand-crafted prefixes + **CEGAR / counterexample-guided SAT completion** — start with few inputs, add a counterexample per iteration; n=20 depth-11 converged after 588 iterations (587 counterexamples out of 2^20 possible). New depth upper bounds t(17)<=10, t(19)<=11, t(20)<=11.
- ["New Bounds on Optimal Sorting Networks"](https://arxiv.org/abs/1501.06946) (CiE 2015): encoding improvements — representative-per-class chosen to minimize variables; oneDown/oneUp propagation variables roughly halving clause count (n=16/d=8: 3.99M -> 2.05M clauses (unverified)); last-layer constraints. Average 8.2x, up to 17.1x speedup (unverified). **Main result T(17)=10**: UNSAT over all 609 two-layer prefixes, **27.63x10^6 CPU-seconds ≈ 320 CPU-days** on Xeon E5-4640, hardest single instance ~27 h (unverified), MiniSAT 2.20.
- Ehlers, "Merging almost sorted sequences yields a 24-sorter" (Information Processing Letters 118:17-20, 2017): stack two 12-channel prefixes, SAT-synthesize the merging suffix -> depth 12 for n=24 (previous 13). The prefix+SAT-completion template reused by Wang 2025.
- ["Sorting networks: to the end and back again"](https://www.sciencedirect.com/science/article/pii/S0022000016300162) (Codish, Cruz-Filipe, Ehlers, Muller, Schneider-Kamp, JCSS 104:184-201, 2019; arXiv:1507.01428) + ["The End Game"](https://arxiv.org/abs/1411.6408) (LATA 2015): exploit the network's *back end* — WLOG last-layer comparators are adjacent-channel; only F_{n+2}-1 (Fibonacci) possible last layers, co-saturation cuts further (n=17: 86 candidate last layers vs 2,583 (unverified); 45,664 two-layer suffixes modulo symmetry (unverified)). **Common miscitation warning: this paper contains no size results for n=11/12 — those are Harder's.**

### 4.3 Fixed-size SAT encodings

[Fonollosa, "Joint Size and Depth Optimization of Sorting Networks"](https://arxiv.org/abs/1806.00305) (2018) is the canonical size-within-depth encoding: BZ/EM depth encoding + cardinality constraints on total comparator count (cardinality circuits themselves built from sorting networks, O(n log^2 k) clauses); symmetry breaking via complete two-layer prefix sets (403 prefixes for n=11, 786 for n=12 in the size-constrained variant (unverified)). Results: minimal size at given depth for n<=12 — e.g. n=10/d=7 needs 31 comparators, n=12/d=9 gives 39; jointly size-and-depth-optimal networks do *not* exist for n=10 or 12. Key statement: for n >= 13 the size-oriented encoding is "out of the reach of current SAT solvers" (paraphrase (unverified)). See also [arXiv:1807.05377](https://arxiv.org/abs/1807.05377) (encoding reductions, single-exception sorters). Earlier: Morgenstern & Schneider (MBMV 2011) needed 21 days for n=10 depth synthesis.

### 4.4 Why size-optimal SAT for n=13 is infeasible today

1. **Search-space arithmetic:** 78 = C(13,2) comparator positions; 78^44 ≈ 1.8x10^83 comparator sequences of length 44 (vs 36^24 ≈ 2.2x10^37 for the n=9 problem that already defeated direct SAT — Codish et al. report solvers "making no discernible progress even after weeks" at n=9/k=24).
2. **No layer structure:** the size problem lacks the layered scaffolding that made T(13) and T(17) tractable; symmetry breaking gives only the 117 two-layer prefixes plus no depth cap.
3. **UNSAT direction:** proving S(13)=45 means refuting *all* 44-comparator networks. The largest layered UNSAT ever done (T(17)=10) cost ~320 CPU-days in 2015 over a far smaller effective space.
4. Every explicit statement in the literature (Codish 2014, Fonollosa 2018, Harder 2020) concurs; nothing 2022-2026 contradicts it for the UNSAT direction. The SAT-side opening is attack (a): if S(13)=44 is true, CEGAR synthesis over 117 prefixes with a few hundred counterexample inputs is cheap to run and would settle the problem positively.

### 4.5 Recent SAT-adjacent results (2022-2026)

- [Chengu Wang, "Depth-13 Sorting Networks for 28 Channels"](https://arxiv.org/abs/2511.04107) (arXiv:2511.04107, Nov 2025): 16-channel 5-layer prefix stacked on a 12-channel 5-layer prefix (2,164 non-redundant candidates, best 4 kept by output-set size), greedy extension, reflection-symmetric restriction, MiniSat completion of layers 7-13. Depth 14 -> **13** for n=27, 28. **Entire computation < 20 minutes on a Mac mini M2 / 16 GB.** Proof the prefix+SAT toolchain still yields real results cheaply.
- [Stober & Weiss, "Lower Bounds for Sorting 16, 17, and 18 Elements"](https://arxiv.org/abs/2206.05597) (ALENEX 2023): adjacent problem (comparison *trees*, not networks) — exhaustive SAT-flavored search proved sorting 16 elements needs 46 comparisons, disproving Knuth's 45 conjecture. Evidence Knuth-era exhaustive frontiers are moving again.
- [Cruz-Filipe & Schneider-Kamp, "Minimizing Sorting Networks at the Sub-Comparator Level"](https://easychair.org/publications/paper/v6QM6/open) (LPAR-25, 2024): SAT formulation systematizing and beating all of AlphaDev's discoveries, applied up to 128 inputs.
- Sorting-network SAT instances are classic competition benchmarks (they appear in the original Cube-and-Conquer paper, Heule et al. HVC 2011), but **no cube-and-conquer or massively parallel attempt targeting S(13) has been published**.

---

## 5. ML / RL / evolutionary approaches

Two camps: **(A) constructors** (upper bounds only — a found 44-comparator network would settle the problem constructively) and **(B) exactness-preserving guides** (reorder a complete search; only camp that can contribute to a *proof*).

### 5.1 AlphaDev (DeepMind, Nature 2023) — camp A, and not about comparator counts

[Mankowitz et al., "Faster sorting algorithms discovered using deep reinforcement learning"](https://www.nature.com/articles/s41586-023-06004-9), Nature 618:257-263; [code](https://github.com/deepmind/alphadev). AlphaZero-style MCTS over x86 assembly ("AssemblyGame") optimizing *instruction count/latency* of fixed-size sort kernels: sort3 18->17 instructions, sort5 46->42, VarSort5 115->63; merged into LLVM libc++. **It did not change any comparator network** — the human baselines are the standard optimal networks; sort3 still does 3 compare-exchanges. Its brute-force "optimality" claim for sort3 (~10^32 programs, >3 days) was contested by Cassio Neri (14-instruction counterexamples under different instruction-set assumptions) and the LPAR-25 paper showed all its tricks reduce to one SAT-checkable MOV-elimination pattern. Irrelevant to S(13) except as a scale warning: 3 days to exhaust 17-instruction programs.

### 5.2 Evolutionary constructors — the source of the n=13 upper bound

- **Juillé END (1995)**: massively parallel beam-search-like "evolving non-determinism" (population 65,536 on 4,096 MasPar processors); **found the first 45-comparator 13-sorters**, and matched Green's 60 for n=16 from scratch. [Summary page](https://www.cs.brandeis.edu/~hugues/sorting_networks.html).
- [Valsalam & Miikkulainen, "Using Symmetry and Evolutionary Search to Minimize Sorting Networks"](https://www.jmlr.org/papers/v14/valsalam13a.html) (JMLR 14:303-331, 2013): SENSO — symmetry-decomposed greedy construction + EDA sampling near the minimal region; single Xeon core, 37 MB. Matched best-known for n<=16 (incl. 45 at n=13) and improved n=17-22 by 1-2 comparators (71, 78, 86, 92, 102, 108); n=17: 71 still stands.
- Hillis (1990) co-evolution on the CM-2: 61 comparators for n=16 (with Green's first 32 hard-wired) — historic, superseded.
- [Dobbelaere's SorterHunter](https://github.com/bertdobbelaere/SorterHunter) (simulated annealing) holds most current records for 17 <= n <= 32; **n=13's 45 was never improved by it**.

### 5.3 RL for network construction — currently far from competitive

[Burca & Raschip, "Finding Minimal-Size Sorting Networks Using Deep Q-Learning"](https://www.scitepress.org/Papers/2026/142346/142346.pdf) (ICAART 2026) + "Identifying Optimal-Size Sorting Networks with Reinforcement Learning" (ICTAI 2025): DQN + action masking + post-hoc pruning. Optimal only to n=5; at n=10 produces 35 vs optimal 29. The Iasi group (Raschip is co-author of the subsumption-matching paper) is the only group visibly active on the optimal-size problem 2025-2026 — from the heuristic side. No AlphaZero-style or GNN system targeting comparator-network size exists; none has reproduced even 45 at n=13.

### 5.4 Exactness-preserving learned guidance — camp B, the transferable family

Learned branching/ordering affects only exploration order in complete solvers; soundness is structural. Directly compatible with a Codish/Harder-style pipeline, trainable on solved n <= 12 instances:

- [Gasse et al., "Exact Combinatorial Optimization with GCNNs"](https://arxiv.org/abs/1906.01629) (NeurIPS 2019): GCNN imitation of strong branching in SCIP; severalfold solve-time reductions, generalizes to larger instances.
- [Graph-Q-SAT](https://arxiv.org/abs/1909.11830) (NeurIPS 2020): GNN Q-function guiding MiniSat branching; **2-3x fewer iterations, works on UNSAT** (the side an S(13)>=45 proof lives on), zero-shot transfer to 5x larger problems.
- [NeuroCore](https://arxiv.org/abs/1903.04671) (Selsam & Bjorner, SAT 2019): unsat-core variable prediction periodically overwriting activity scores; +10%/+11%/+6% problems solved for MiniSat/Glucose/Z3. Successor [NeuroBack](http://spark.ece.utexas.edu/pubs/ICLR-24-yang.pdf) (ICLR 2024) removes solve-time GPU need.
- [Neuro#](https://arxiv.org/abs/2007.03204) (AAAI 2021): learned branching for exact #SAT; orders-of-magnitude wall-clock speedups on larger instances of a trained family — the closest analogue to enumerate-and-prune search.
- Pattern precedents: RL-chosen BDD variable orders always yield valid bounds ([Cappart et al., AAAI 2019](https://arxiv.org/abs/1809.03359)); MapleSAT's bandit-learned LRB branching won SAT Comp 2016.

### 5.5 Alpha* / FunSearch-style systems

[AlphaTensor](https://www.nature.com/articles/s41586-022-05172-4) (Nature 2022; 47-mult 4x4 matmul over F2), [FunSearch](https://www.nature.com/articles/s41586-023-06924-6) (Nature 2024; cap-set lower bounds), [AlphaEvolve](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/) (2025; 48-mult complex 4x4 matmul, improved best-known bounds on ~20% of 50+ open problems, kissing number D11 592->593) are all **constructors** — certificates of existence, never impossibility proofs. AlphaEvolve is the natural off-the-shelf tool for hunting a 44-comparator network (candidates machine-checkable against 8,192 vectors). [AlphaProof](https://www.nature.com/articles/s41586-025-09833-y) (Nature 2025) is the only camp-B-adjacent member (Lean-checked proofs) but targets olympiad statements, not finite exhaustion.

---

## 6. Recent activity, community, and GPU acceleration (2022-2026)

### 6.1 Direct attacks on S(13)

**None exist.** arXiv sweep 2022-2026 finds no size-optimality attack on any n >= 13. [jix/sortnetopt](https://github.com/jix/sortnetopt): 0 forks, 0 issues, last push Dec 2020. Harder's paper got a v3 housekeeping revision (Jul 2022) with no new n=13 content. No BOINC/distributed proposal exists. HN discussion of [Part 1](https://news.ycombinator.com/item?id=27047108) (53 points) contains the only n=13 cost estimate anywhere; [Part 2's submission](https://news.ycombinator.com/item?id=28495307) got 1 point. Dobbelaere's 2022-2026 changelog is all n>=21 sizes and n=25-28 depths — except the April 2025 lower-bound refinement (Section 1), which is the **only movement on S(13) in the entire period, and it was on the lower-bound side: 43 -> 44.**

### 6.2 Subsumption/algorithmic improvements

Covered in Sections 2-3: Frasinaru-Raschip bipartite matching (CPAIOR 2019, >10x), Harder's k-d tree + abstractions (2020, additional ~40x on core-hours), Harder's Huffman-bound DP (2020, ~10^6x on n=9). **The published lines were never merged**: nobody has combined matching-based subsumption *online* inside the DP, or the 117-prefix symmetry breaking with either.

### 6.3 GPU / FPGA

**No public GPU implementation of generate-and-prune or any sorting-network optimality search exists** (searches return only bitonic-sort implementations). Strongest transfer precedent: the **9th Dedekind number** (2023) — [Jakel, arXiv:2304.00895](https://arxiv.org/abs/2304.00895): **5,311 A100 GPU-hours**; independent [Van Hirtum et al. FPGA computation](https://doi.org/10.1145/3674147): ~47,000 FPGA-hours. D(9) is a symmetry-reduced enumeration over monotone Boolean functions — structurally cousin to output-set lattices — showing 10^20-scale symmetry-reduced combinatorics is now a few-thousand-GPU-hour job. Caveat: D(9) was compute-bound; the sorting-network DP is memory-bound with random access over a huge canonical-form table, so transfer requires solving the sharding problem first.

### 6.4 Theory sidebar

[Dobrokhotova-Maikova, Kozachinskiy, Podolskii, "Towards Simpler Sorting Networks and Monotone Circuits for Majority"](https://arxiv.org/abs/2310.12270) (2023): asymptotic depth improvements with k-ary gates; not relevant to exact small-n but citable as recent theory. Asymptotic size lower bound remains [Kahale-Leighton-Ma-Plaxton-Suel-Szemeredi, STOC 1995](https://www.researchgate.net/publication/221590742_Lower_bounds_for_sorting_networks): size >= (1.12-o(1)) n log n — numerically useless at n=13 (~52).

---

## 7. Feasibility assessment for S(13)

**Cost anchors:**

| Quantity | n=9 | n=11 | n=13 (extrapolated) |
|---|---|---|---|
| Sequence sets bounded (Harder DP) | 206,279 | 2.46x10^9 | ~3x10^13 (x12,000/2ch) |
| Search RAM | 58 MiB | 178 GiB | **~20 PB (Harder's own estimate)** |
| Search time | 0.5 s | 4 h 51 m (24c) | "proportionally longer" |
| Certificate steps | 11,934 | 12.7M | ~1.5x10^11 (same ratio) |

**Signals that n=13 is closer than commonly believed:**
1. The lower bound is already 44, so exactly one comparator value (44) must be refuted — and per-interval work in Harder's successive approximation shrinks with a tighter initial bound. Nobody has costed the certificate-targeted variant.
2. The ~195x explored-vs-needed gap at n=11 (2.46B sets bounded vs 12.7M certificate steps) is documented headroom; Harder named the mechanism to capture it (on-line subsumption) and never tried it.
3. Field-wide algorithmic improvement rate 2014-2020 was ~10^6-10^7x on the benchmark computation, then all activity stopped — 2021-2026 is untouched.
4. Memory hardware moved: 4-12 TB single nodes, CXL pooling, NVMe out-of-core tables. 20 PB / (195x subsumption headroom x tighter intervals x out-of-core) plausibly lands within 1-2 further algorithmic multipliers of a large single node.
5. Wang 2025 demonstrates the SAT-completion side is nearly free on modern hardware; the 44-network hunt (attack (a)) costs almost nothing to run continuously.
6. D(9) precedent: symmetry-reduced 10^20-scale enumeration ≈ 5,000 GPU-hours in 2023.

**Countervailing:**
- Growth is "double exponential or faster" (Harder's measured words); a naive n=13 run is ~10^4-10^5x the n=11 cost in both time and memory.
- Harder himself, distribution "would slow it down a lot" due to random-access patterns; s(12) "the end of what's possible with this exact approach."
- Every explicit literature statement says direct size-SAT at n >= 13 is out of reach; 30 years of heuristic search never found a 44-comparator network (weak evidence S(13)=45, i.e., the hard UNSAT direction is the true one).
- Zero community activity also means zero validated intermediate results to build on beyond Harder's artifacts.

**Recommended reading order for the team:** Harder's blog Parts 1-2 -> arXiv:2012.04400 (Sections 5-7, 9, Appendix A) -> sortnetopt source -> arXiv:1405.5754 -> arXiv:1707.08725 -> Dobbelaere's gist (F(N)) -> arXiv:1404.0948 (two-layer prefixes) -> arXiv:2511.04107 (cheap modern SAT completion).

---

## References (primary sources)

1. Van Voorhis, D.C. "Toward a Lower Bound for Sorting Networks." *Complexity of Computer Computations*, Plenum, 1972, 119-129. https://link.springer.com/chapter/10.1007/978-1-4684-2001-2_12
2. Van Voorhis, D.C. "An Improved Lower Bound for Sorting Networks." *IEEE Trans. Computers* C-21(6), 1972. https://ieeexplore.ieee.org/document/5009021/
3. Codish, Cruz-Filipe, Frank, Schneider-Kamp. "Twenty-Five Comparators is Optimal when Sorting Nine Inputs (and Twenty-Nine for Ten)." ICTAI 2014. https://arxiv.org/abs/1405.5754 — journal: JCSS 82(3):551-563, 2016. https://www.sciencedirect.com/science/article/pii/S0022000015001397
4. Codish, Cruz-Filipe, Schneider-Kamp. "The Quest for Optimal Sorting Networks: Efficient Generation of Two-Layer Prefixes." SYNASC 2014. https://arxiv.org/abs/1404.0948
5. Codish, Cruz-Filipe, Schneider-Kamp. "Sorting Networks: the End Game." LATA 2015. https://arxiv.org/abs/1411.6408
6. Codish, Cruz-Filipe, Ehlers, Muller, Schneider-Kamp. "Sorting networks: to the end and back again." JCSS 104:184-201, 2019. https://www.sciencedirect.com/science/article/pii/S0022000016300162
7. Cruz-Filipe, Schneider-Kamp. "Formalizing Size-Optimal Sorting Networks: Extracting a Certified Proof Checker." ITP 2015. https://arxiv.org/abs/1502.05209
8. Cruz-Filipe, Schneider-Kamp. "Optimizing a Certified Proof Checker for a Large-Scale Computer-Generated Proof." CICM 2015. https://arxiv.org/abs/1502.08008
9. Cruz-Filipe, Larsen, Schneider-Kamp. "Formally Proving Size Optimality of Sorting Networks." JAR 59(4):425-454, 2017. https://link.springer.com/article/10.1007/s10817-017-9405-9
10. Bundala, Zavodny. "Optimal Sorting Networks." LATA 2014. https://arxiv.org/abs/1310.6271
11. Ehlers, Muller. "Faster Sorting Networks for 17, 19 and 20 Inputs." 2014. https://arxiv.org/abs/1410.2736
12. Ehlers, Muller. "New Bounds on Optimal Sorting Networks." CiE 2015. https://arxiv.org/abs/1501.06946
13. Ehlers. "Merging almost sorted sequences yields a 24-sorter." IPL 118:17-20, 2017.
14. Frasinaru, Raschip. "An Improved Subsumption Testing Algorithm for the Optimal-Size Sorting Network Problem." CPAIOR 2019. https://arxiv.org/abs/1707.08725
15. Fonollosa. "Joint Size and Depth Optimization of Sorting Networks." 2018. https://arxiv.org/abs/1806.00305 — and https://arxiv.org/abs/1807.05377
16. Harder. "An Answer to the Bose-Nelson Sorting Problem for 11 and 12 Channels." 2020-2022. https://arxiv.org/abs/2012.04400 — code https://github.com/jix/sortnetopt, https://github.com/jix/sortnetopt-gnp — blog https://jix.one/proving-50-year-old-sorting-networks-optimal-part-1/ , .../part-2/ — certificate: Zenodo 10.5281/zenodo.4108365 — HN: https://news.ycombinator.com/item?id=27047108
17. Dobbelaere. "List of sorting networks" + SorterHunter. https://bertdobbelaere.github.io/sorting_networks.html , https://github.com/bertdobbelaere/SorterHunter — F(N) gist: https://gist.github.com/bertdobbelaere/0a30f5321965732b59c102fa9e3250bb
18. Wang. "Depth-13 Sorting Networks for 28 Channels." 2025. https://arxiv.org/abs/2511.04107
19. Stober, Weiss. "Lower Bounds for Sorting 16, 17, and 18 Elements." ALENEX 2023. https://arxiv.org/abs/2206.05597
20. Cruz-Filipe, Schneider-Kamp. "Minimizing Sorting Networks at the Sub-Comparator Level." LPAR-25, 2024. https://easychair.org/publications/paper/v6QM6/open
21. Mankowitz et al. "Faster sorting algorithms discovered using deep reinforcement learning." Nature 618:257-263, 2023. https://www.nature.com/articles/s41586-023-06004-9
22. Valsalam, Miikkulainen. "Using Symmetry and Evolutionary Search to Minimize Sorting Networks." JMLR 14:303-331, 2013. https://www.jmlr.org/papers/v14/valsalam13a.html
23. Hillis. "Co-evolving parasites improve simulated evolution as an optimization procedure." Physica D 42:228-234, 1990.
24. Juillé. "Evolving Non-Determinism" (END). LNCS 929:246-260, 1995. https://www.cs.brandeis.edu/~hugues/sorting_networks.html
25. Burca, Raschip. "Finding Minimal-Size Sorting Networks Using Deep Q-Learning." ICAART 2026. https://www.scitepress.org/Papers/2026/142346/142346.pdf
26. Gasse et al. NeurIPS 2019. https://arxiv.org/abs/1906.01629 · Kurin et al. (Graph-Q-SAT) NeurIPS 2020. https://arxiv.org/abs/1909.11830 · Selsam, Bjorner (NeuroCore) SAT 2019. https://arxiv.org/abs/1903.04671 · Vaezipoor et al. (Neuro#) AAAI 2021. https://arxiv.org/abs/2007.03204 · NeuroBack ICLR 2024. http://spark.ece.utexas.edu/pubs/ICLR-24-yang.pdf
27. Jakel. "A computation of the ninth Dedekind number." 2023. https://arxiv.org/abs/2304.00895 · Van Hirtum et al., ACM TRETS. https://doi.org/10.1145/3674147
28. Kahale, Leighton, Ma, Plaxton, Suel, Szemeredi. "Lower bounds for sorting networks." STOC 1995.
29. OEIS A003075 (minimal size; exact through n=12). https://oeis.org/A003075
30. Wikipedia, "Sorting network" (n=13 lower bound listed there, 43, is stale). https://en.wikipedia.org/wiki/Sorting_network
