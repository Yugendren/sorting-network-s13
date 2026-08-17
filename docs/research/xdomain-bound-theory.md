# Cross-Domain Bound Theory for S(13) >= 45

**Date:** 2026-08-17. **Task:** hunt lower-bound mathematics, information theory, and
proof techniques from adjacent fields that could (a) give S(13) >= 45 directly or
nearly, or (b) yield new machine-checkable pruning lemmas for the Track-B DP.
**Method:** web survey + primary-source extraction (Harder arXiv:2012.04400 full text,
Dobbelaere's F(N) gist, van Voorhis's Stanford TR CS-TR-71-238) + local computations
(reproduced below; scripts were run in this session, re-runnable in minutes).

**Headline numbers.** The gap is 0.39 bits: log2 F(13) = 8.615, and ceil(log2 F(13)) = 9
gives the 44. Any refinement of van Voorhis's two-channel count by a factor >= 1.31
(F(13) >= 513) yields S(13) >= 45 **without any large computation**. Empirically the
two-channel bound undershoots the true S(N)-S(N-2) by 1-2 at every N in 9..12, so one
extra unit at N=13 is plausibly *true*; the question is purely proof technique.

---

## 0. Verified state of play

- S(13) in {44, 45}. 45 = Juillé 1995 witness (45 comparators, 10 layers).
- 44 = van Voorhis two-channel theorem, S(N) >= S(N-2) + P(2,N), P(2,N) >=
  ceil(log2 F(N)), applied by Dobbelaere (April 2025, on Firet's suggestion) to
  Harder's S(11)=35: F(13)=392 => 35 + 9 = 44. Folklore-verified; no paper.
- Harder's prover uses the *one-channel* theorem generalized to partial sorting
  networks via Huffman's algorithm (Theorem 26 of arXiv:2012.04400, full statement in
  §1.3 below). The two-channel theorem has **never** been generalized to partial
  sorting networks or used inside any search. This is the single largest identified
  opening (see §6 and Recommendation 1).

### F(N) table (computed this session from Dobbelaere's recursion; reproduces his 44/48/53/57/63)

| N | F(N) | log2 F | ceil = two-ch bound | actual S(N)-S(N-2) | slack |
|---|------|--------|---------------------|--------------------|-------|
| 3 | 8 | 3.000 | 3 | 3 | 0 |
| 4 | 16 | 4.000 | 4 | 4 | 0 |
| 5 | 36 | 5.170 | 6 | 6 | 0 |
| 6 | 52 | 5.700 | 6 | 7 | 1 |
| 7 | 80 | 6.322 | 7 | 7 | 0 |
| 8 | 96 | 6.585 | 7 | 7 | 0 |
| 9 | 168 | 7.392 | 8 | 9 | 1 |
| 10 | 200 | 7.644 | 8 | 10 | 2 |
| 11 | 256 | 8.000 | 8 | 10 | 2 |
| 12 | 288 | 8.170 | 9 | 10 | 1 |
| 13 | **392** | **8.615** | **9** | 9 or 10 | 0 or 1 |
| 14 | 424 | 8.728 | 9 | — | — |
| 15 | 480 | 8.907 | 9 | — | — |
| 16 | 512 | 9.000 | 9 | — | — |
| 17 | 784 | 9.615 | 10 | — | — |

Two readings: (i) the bound was *never* off by more than 2 and is off by 1-2 for all
of N=9..12, so S(13)-S(11) = 10 (i.e. S(13)=45) fits the pattern; (ii) to certify the
last unit, either F(13) must be improved to >= 513 (factor 1.31, 0.39 bits) or the
slack must be closed on the P(2,N) side by structural/case analysis.

**Downstream payoff if S(13)=45 is proven:** S(14) >= 49 (vs UB 51), S(15) >= 45+9 = 54
(current LB 53), S(16) >= 49+9 = 58 (current LB 57), S(17) >= 54+10 = 64 (current LB 63).
Three published-table entries improve for free.

---

## 1. The full landscape of size lower-bound theorems

### 1.1 Information-theoretic counting bound
S(n) >= ceil(log2 n!) comparisons in the *comparison-tree* model; every network induces
a comparison algorithm, so it applies. At n=13: ceil(log2 13!) = 33. **Blocks from 45:**
off by 12; it charges each comparator a full bit, but comparators in a network are
oblivious and mostly redundant information-wise. Dead numerically forever at n=13.

### 1.2 Van Voorhis one-channel (1972, IEEE ToC / TAOCP 5.3.4)
S(n) >= S(n-1) + ceil(log2 n). Proof (as reconstructed in Harder §3.1, verified from
full text): prune the max-path from input channel i (follow the 1 of the one-hot input
<i:n>); c/i is an (n-1)-sorter; delta(c,i) = #comparators on the path; the union of
all n pruned paths is a binary tree with n leaves rooted at output n; max_i delta(c,i)
= tree height >= ceil(log2 n). **At n=13:** S(12)+4 = 43. Blocks: the tree-height term
can never exceed ceil(log2 n); all slack in "the deleted path is not the only work the
extra channel causes" is discarded.

### 1.3 Harder's Huffman generalization (arXiv:2012.04400, Theorem 26) — the prover's engine
For X ⊆ B^n with prunable channels p(X) != {} (i one-hot in X):
s(X) >= H_{1+max}{ s(X/i) | i in p(X) }, where H_{1+max} is Huffman's algorithm in the
Huffman algebra (N0, <=, 1+max) and X/i = {x/i | x in X, x_i = 1}. Van Voorhis
one-channel is the equal-leaves special case. Not negation-symmetric: computed for X
and X̄ and the max is taken (Harder p.15). Certificate rules: Triv, PH (|X| >= n+1 =>
s(X) >= 1), Succ, Huffman — all four verified in Isabelle/HOL. **Blocks from 45:** at
the root all 13 leaves equal s(B^12), giving 39+4 = 43; deeper in the DP it is the
pruning workhorse but each application still only counts *one* system of max-paths.

### 1.4 Van Voorhis two-channel (Plenum 1972 "Toward a Lower Bound for Sorting Networks")
S(N) >= S(N-2) + P(2,N), P(2,N) >= ceil(log2 F(N)), with F given by the min-over-tree-
shapes recursion in Dobbelaere's gist (minf(size,depth); v = 2*(fl + fr + 2^(dl+dr))).
This is the current record: 35 + 9 = 44. **Blocks from 45:** F(13)=392 < 513. The count
is a min over *all* pairs-of-pruned-path tree shapes; the minimizing shapes are very
special (see §6.2), and the counting itself is conservative (the empirical slack of
1-2 units at N=9..12 shows either F or the P >= log2 F step loses real work).
**Caveat:** the exact definition of P(2,N) (as a property of the deleted comparators
when two channels are pruned) could not be pulled from an open full text — Springer
chapter paywalled, DTIC AD0721701 ("An Improved Lower Bound for the Bose-Nelson
Sorting Problem", TN-7, Feb 1971 — the TR version) blocks robots, Stanford's mirror
carries a *different* VV report (divide-sort-merge, CS-TR-71-238, retrieved in full).
**Action item: obtain the Plenum chapter via library/ILL before building on the
theorem — required anyway for the planned rigorous write-up of the 44.**

### 1.5 Kahale-Leighton-Ma-Plaxton-Suel-Szemerédi (STOC 1995)
Size >= (1.12 - o(1)) n log n via a counting argument over epsilon-halver quality.
**Blocks from 45:** the o(1) and the halver constants make it vacuous at n=13 (the
"~52" one gets by plugging n=13 into the leading term is not a valid instantiation;
the proof needs n large). No one has ever extracted an effective small-n version; the
machinery (potential functions over partial orders induced by wires) is the closest
thing to an "adversary for networks" in the literature — see §2.

### 1.6 Yao; depth bounds; merging/selection networks
- Yao 1980 (Bounds on selection networks) and Alekseev 1969: (n,t)-selection networks
  need >= (n-t)*ceil(log2(t+1)) comparators. At (13,2): 22. Not additive with S(11);
  no known way to compose with a residual-sorting bound without re-deriving van
  Voorhis. Depth records (Yao 2.41 log n; KLMPSS ~3.27 log n; ITCS 2023
  Dobrokhotova-Maikova-Kozachinskiy-Podolskii for constant depth/k-ary) are depth-only
  and vacuous for size at n=13 (T(13)=9 is already known exactly).
- Merging networks: M(2,n) is *exactly known* (Batcher optimal for m <= 4; SIAM J.
  Comput. and "On Optimal Merging Networks"; Yao & Yao lower bounds). Tempting but
  **not transferable**: see the insert-cost computation in §6.3 — the two extracted
  channels of a 13-sorter do strictly less work than a standalone (2,11) merge/insert
  network, so exact merging complexities cannot replace P(2,N).
- Comparison-tree exact results (Stober & Weiss ALENEX 2023: sorting 16 *elements*
  needs 46 *comparisons*; Peczarski's earlier 13..15 results): valid for networks too
  but numerically ~33-34 at n=13. Useless directly; their search discipline (huge
  exhaustive poset search with certificates) is a methods cousin, not a bound.

### 1.7 Anything newer (2015-2026)?
Systematic sweep found **no new size lower-bound theorem for comparator networks
since KLMPSS 1995**. The only movement on S(13) in 2022-2026 is Dobbelaere's April
2025 application of the 1972 two-channel theorem. The theorem shelf is short: 1.1-1.6
above is the complete published arsenal. Consequence: any new valid inequality — even
a +1 refinement — is publishable and directly load-bearing.

---

## 2. Adversary / potential-function arguments and the obliviousness lever

**What exists.** Classical adversary arguments (Knuth's merging adversary, Ford-
Johnson optimality analyses, Stober-Weiss) live in the comparison-tree model: the
adversary answers queries adaptively and the bound is against *adaptive* algorithms —
so these bounds are automatically weaker than what oblivious networks require
(n log n-ish vs the conjectured ~n log^2 n/divide-sort-merge reality). The only
published techniques that *exploit* obliviousness are:
1. Van Voorhis's path-pruning (the deleted max-path is well-defined only because the
   circuit is fixed before the input — this IS an oblivious-only argument), and
2. KLMPSS's halver-quality counting (a fixed wiring must be a good expander at every
   scale — again oblivious-only), and
3. Floyd's M2(4n) >= 2*M2(2n) + n merging bound and its VV generalization (class-A/
   class-B comparator partition in the retrieved Stanford TR — comparators are
   partitioned by *position*, impossible in an adaptive model).

**Assessment.** A comparator-network adversary would fix a *distribution/poset
potential* over B^n and charge each comparator max potential drop; sortedness needs
total drop >= Phi_0. For the counting potential Phi = log2 |X| this is exactly the
pigeonhole/information bound (each comparator merges pairs x, x^swap: |X| shrinks by
at most... in fact a comparator can halve |X|, giving only the useless log2(2^13/14)
~= 9.2 *total*, not per-suffix). The known way to beat it is to make the potential
*structure-aware* (KLMPSS). A bespoke potential achieving 45 at n=13 would need to be
discovered essentially by search over potential families — feasible as an LP over
small state spaces (see §5), not by hand. **Honest rating: medium-low probability of
a standalone win; high synergy as a per-node pruning bound if found via LP (§5).**

---

## 3. Entropy / Dedekind-lattice methods (output sets as monotone functions)

Each channel of a prefix computes a monotone Boolean function of the inputs; output
sets X = outputs(C) are exactly the images of B^n under monotone comparator maps, and
Harder's "well-behaved sets" (unions of threshold sets, Def. 28) are the DP's state
space. The adjacent-field results:
- **Kahn's entropy method / Kleitman-Markowsky** (Dedekind problem): upper bounds on
  the *number* of monotone functions / antichains. Shearer-type entropy counting gives
  log D(n) ~ C(n, n/2)(1 + o(1)).
- **Hansel chains**: symmetric chain decompositions giving D(n) <= 3^C(n,n/2); used in
  all modern Dedekind computations (incl. D(9) 2023).
- **Sparse-Sperner / container results 2023-2025** (arXiv:2411.03400 etc.): counts of
  antichains of given size.

**What they can and cannot do here.** They bound *how many* states exist, not *how
many comparators* remain. Directly: no route to S(13) >= 45. Indirectly, two real uses:
1. **A priori frontier-size bounds for M1 (scaling law):** the number of canonical
   well-behaved sets at n=13 is bounded by antichain-counting over the 13-cube modulo
   S_13 x negation; a Hansel/entropy computation would put *provable error bars* on
   the ~3x10^13 extrapolation and on shard sizing for M2's out-of-core tables. Cheap,
   useful engineering mathematics — not a bound theorem.
2. **Chain-decomposition pruning invariant (speculative):** a Hansel chain
   decomposition of X gives |X| >= (#chains) and every comparator respects chains
   order-monotonically; a per-chain pigeonhole could strengthen PH from "s(X) >= 1 if
   |X| >= n+2" to a graded bound s(X) >= f(chain profile of X). Nobody has tried it.
   Machine-checkable (the chain decomposition is an explicit witness; the rule is a
   counting check). Expected gain: small constant per node; worth a 1-day experiment
   against the n=9 memo table (ground truth for every s(X) is available from M0 runs).

---

## 4. Sensitivity / certificate complexity / polynomial method

Sweep result: **no published attempt** applies sensitivity, block sensitivity,
certificate complexity, or the polynomial method to minimum-size sorting networks.
Structural reasons they fail here: (i) the outputs (order statistics = threshold
functions t_k) have full degree and full sensitivity n, but so do the outputs of any
*selection* network — these measures see the function computed, not the circuit
economy; (ii) polynomial-method lower bounds count query steps of adaptive algorithms
(again <= comparison-tree strength); (iii) Razborov-style monotone-circuit bounds
target functions with cryptographic-ish structure (clique/matching) and their small-n
constants are vacuous; a sorting network *is* a monotone circuit for all 13 threshold
functions simultaneously (AND/OR pairs), and the best known monotone-complexity fact
for MAJ_13-with-shared-gates is far below 44 gate-pairs. **Rating: dead end for the
target; do not invest.** (One citable connection for the write-up: any size-s sorting
network gives a 2s-gate monotone circuit computing all thresholds; so S(13) >= 45 would
prove a modest sharp small-n monotone-complexity result — a framing that may interest
circuit-complexity readers, not a proof technique for us.)

---

## 5. LP / SDP relaxations

Sweep result: **nothing published.** No ILP formulation with a useful LP bound, no
Lovász-theta/SDP relaxation, for min-size sorting networks (Fonollosa 2018 is SAT with
cardinality constraints — no relaxation bound; Morgenstern-Schneider likewise). This
is virgin territory, but the honest expected value differs sharply by use:
- **Global LP for S(13) >= 45 directly: hopeless.** Any compact LP over comparator
  position variables has massive symmetry; fractional solutions will sit near the
  information bound (~33-40). SDP hierarchies at the size needed (78 positions x 44
  slots) are numerically out of reach at useful rounding tightness.
- **Per-node LP bound inside the DP: genuinely promising.** Harder's Huffman bound is
  the exact optimum of a min-over-trees problem for *one* system of max-paths on X
  (or, separately, on X̄). A small LP per node can jointly constrain:
  (a) the max-path tree of X (Huffman leaves s((X/i)°)),
  (b) the min-path tree of X̄,
  (c) shared-comparator accounting between the two systems (a comparator has one max
      and one min output, so it can serve at most one 1-path and one 0-path — the
      overlap variables are constrained, and today the prover just takes max(a,b)),
  (d) per-channel degree lower bounds (channels whose value-multiset in X is
      unfinished need >= 1 more touch — a PH-per-channel refinement).
  Any dual-feasible solution is a sound bound. **Machine-checkable version:** new rule
  `LPDual`: certificate stores the rational dual vector y; checker verifies A^T y <= c
  and b^T y >= k in exact arithmetic (no LP solver in the trusted base — textbook
  weak-duality check, small Isabelle obligation). **Cheap validation experiment:**
  M0's instrumentation gives the exact gap histogram s(X) - HuffmanBound(X) over all
  memoized n=9 sets; if mass sits at gap >= 1 (Harder's 195x explored-vs-needed waste
  says it does), even a +1-average LP bound compounds exponentially down the DP.

---

## 6. The one-unit gap: S(13)-S(11) in {9,10} — computations and closing strategies

### 6.1 Where exactly the 44 loses
Chain: S(13) >= S(11) + P(2,13) >= 35 + ceil(log2 F(13)) = 35 + ceil(8.615) = 44.
Needed: one more unit in P(2,13). Options: (A) prove F(13) >= 513 under a corrected
count; (B) prove P(2,13) >= 10 by structure/case analysis at the tight shapes; (C)
bypass with a partial-set two-channel rule strong enough that the *DP* (restricted or
full) certifies 45 (Recommendation 1); (D) find the 44 network (Track A) — then all
of this is moot.

### 6.2 The tight shapes are few (computed this session)
minf(13,d) by root depth-budget: d=4: 392, d=5: 496, d=6: 856, ... (rising fast).
Root splits (d, left-size/left-depth, right-size/right-depth) achieving count <= 512:
- d=4: (5,3 | 8,3), (6,3 | 7,3), (7,3 | 6,3), (8,3 | 5,3) — all = 392
- d=5: (4,2 | 9,4) — = 496
**Only 5 root-split classes** of the two-channel pruning structure are consistent
with a 44-comparator 13-sorter; every other shape already forces >= 513 outcomes,
i.e. >= 10 removed comparators, i.e. 45. A "tightness structure theorem" would say:
a 44-net's two-channel deletion structure realizes one of these 5 shapes for *every*
choice of channel pair (or at least for the minimizing pair), which pins the back-end
geometry hard (cf. the End-Game paper's last-layer/adjacent-comparator constraints —
same genre, independently derived). Each shape class is then a *restricted class* in
exactly the M4 sense, attackable by targeted DP/SAT exhaustion orders of magnitude
smaller than the full n=13 run. **This composes the two-channel theorem with M4 into
a concrete finite programme for the last unit.** Prerequisite: the Plenum chapter's
precise semantics of the tree shapes (what dl/dr and the 2^(dl+dr) term count) —
verify before formalizing; then the case enumeration itself is machine-checkable
(finite list + per-class exhaustion certificates).

### 6.3 Exact insert-network costs — what P(2,N) is NOT (computed this session)
I1(N) = exact min comparators to sort {channel 1 free, rest pre-sorted} (BFS over
output sets): I1(N) = N-1 for N=3..8 — matches the known merging value M(1,n)=n. But
S(N)-S(N-1) = 2,2,4,3,4,3 over the same range: **I1 > true difference at N=6,8.**
I2(N) = same with two free channels: 4,6,7,9,10 for N=4..8 vs S(N)-S(N-2) =
4,6,7,7,7: **I2 > true difference at N=7,8.** Conclusion (important negative result):
no theorem of the form S(N) >= S(N-2) + (exact 2-insertion/merging cost) can be true —
the two "extra" channels inside an optimal N-sorter do strictly less attributable work
than a standalone insertion network, because the residual network is not required to
sort N-2 first. Any refinement must stay inside the deleted-comparators/path-tree
accounting (or LP-relax it), not import merging complexities. This kills the most
tempting cross-domain shortcut and calibrates all "exact P(2,N)" hopes: P(2,13) is
somewhere in [9, 10] and (given I2's trend ~N+2 >> 10) the deleted-comparator
quantity, not insertion cost, is the object to bound.

### 6.4 Candidate refinements, ranked
1. **Two-channel Huffman rule for partial sorting networks ("Huffman2").** Generalize
   Theorem 26 to second-order pruning: for prunable i, and j prunable in X/i,
   s(X) >= s((X/i)/j) + delta(c,i) + delta(c/i,j); the c-independent lower bound over
   all realizable pairs-of-path-systems is a min-cost over VV's two-tree structures
   with *unequal leaves* k_ij = s(((X/i)/j)°) — the same move Harder made on the
   one-channel theorem, applied to the theorem that already produced the 44. At the
   root with equal leaves it reproduces 44; with unequal leaves *inside* the DP it
   strictly dominates chained Huffman applications wherever the two pruned subproblem
   bounds differ (which is exactly where Harder's memo mass sits, per M0b: k = n-3,
   n-2). Needs: (i) the exact VV structure lemma (Plenum chapter), (ii) an efficient
   min-cost algorithm or any *sound relaxation* — even DP-over-shapes à la minf is
   fine since soundness only needs a lower bound on realizable costs, (iii) an
   Isabelle-verified `Huffman2` certificate rule (premises: s(Y_ij) >= k_ij with
   permutation/negation witnesses, conclusion: s(X) >= G({k_ij}); checker re-runs G).
   Risk: the Huffman-algebra optimality trick may not extend (Huffman's greedy needs
   the algebra axioms; the two-tree cost may need explicit DP) — acceptable, since the
   checker can verify a DP table instead of a greedy run.
2. **Tightness case-split at the root (§6.2)** — the cheapest path to a *standalone*
   S(13) >= 45 paper if the 5 shape classes can each be refuted by restricted-class
   exhaustion; no new DP infrastructure needed beyond M4's.
3. **Per-node LP with dual certificates (§5)** — strictly-more-general accounting (X
   and X̄ trees + overlap + degree constraints); empirical gap histogram on n=9 decides
   in a day whether it buys the +1 per node that compounds.
4. **F(N)-recursion audit.** The recursion's v = 2*(fl+fr+2^(dl+dr)) mixes counts
   linearly where the underlying outcome sets may force products; VV chose the min
   over shapes conservatively. A modern re-derivation (with the Plenum proof in hand)
   may already yield F(13) >= 513 by pure re-counting; even if not, it produces the
   rigorous write-up of the 44 that the programme owes the record anyway. Low cost,
   uncertain gain, mandatory groundwork for items 1-2.
5. **Hansel-chain graded pigeonhole (§3)** — small, clean, testable against solved
   memo tables; expected sub-unit average gain; do only if 1-3 stall.

### 6.5 What does NOT work (verified dead ends)
- Exact merging/insertion complexities as P(2,N) (disproved by computation, §6.3).
- Comparison-tree adversaries and Stober-Weiss-style values (<= 34 at n=13).
- KLMPSS at n=13 (asymptotic constants; no effective version exists).
- Sensitivity/polynomial/certificate measures (model-insensitive to network size, §4).
- Global LP/SDP for 45 (symmetry + scale, §5).
- One-channel chains: S(12)+ceil(log2 13) = 43 is a hard ceiling for that route.

---

## Machine-checkability contract summary

| Candidate | New certificate rule | Trusted-base delta | Validation path |
|---|---|---|---|
| Huffman2 (two-channel partial) | `Huffman2(X; {(i,j) -> Y_ij, k_ij, perm/neg}); concl s(X) >= G(k)` | Isabelle proof of the two-path pruning lemma + soundness of G (DP over shapes) | replay n=9/n=11: certificates must shrink; all bounds must match known s(X) |
| Root case-split | finite shape list + per-class exhaustion certs (existing Succ/Huffman rules inside each class) | only the shape-completeness lemma | each class run is an M4-style replayable certificate |
| LPDual | rational dual vector; checker does exact A^T y <= c, b^T y >= k | weak-duality lemma (small) | gap histogram vs known s(X) on n=9 memo table |
| Hansel PH | explicit chain decomposition witness + counting check | symmetric-chain lemma | same n=9 histogram |
| F-audit | none (root-level theorem, one certificate line) | the re-derived counting lemma | reproduce F table; cross-check N=3..12 against known S diffs (table §0) |

## Sources
- Van Voorhis, "Toward a Lower Bound for Sorting Networks", Complexity of Computer
  Computations, Plenum 1972 (paywalled: https://link.springer.com/chapter/10.1007/978-1-4684-2001-2_12);
  TR version "An Improved Lower Bound for the Bose-Nelson Sorting Problem", Stanford
  DSL TN-7, Feb 1971, DTIC AD0721701 (robot-blocked: https://apps.dtic.mil/sti/citations/AD0721701) — **obtain via ILL**.
- Van Voorhis, "A Lower Bound for Sorting Networks that Use the Divide-Sort-Merge
  Strategy", STAN-CS-71-238 (full text retrieved: http://i.stanford.edu/pub/cstr/reports/cs/tr/71/238/CS-TR-71-238.pdf) — source of the class-A/class-B oblivious partition argument and Floyd's M2(4n) >= 2M2(2n)+n.
- Van Voorhis, "An Improved Lower Bound for Sorting Networks", IEEE ToC C-21(6), 1972. https://ieeexplore.ieee.org/document/5009021/
- Harder, arXiv:2012.04400 (full text extracted this session: Lemmas 10-20, Theorem 26,
  Definition 57 rules, §10.1 future work). https://arxiv.org/abs/2012.04400
- Dobbelaere, F(N) gist (code retrieved verbatim via GitHub API):
  https://gist.github.com/bertdobbelaere/0a30f5321965732b59c102fa9e3250bb
- KLMPSS, "Lower bounds for sorting networks", STOC 1995. https://www.researchgate.net/publication/221590742_Lower_bounds_for_sorting_networks
- Yao, "Bounds on Selection Networks", SIAM J. Comput. 1980; Yao & Yao, "Lower Bounds
  on Merging Networks", J.ACM 1976; "The asymptotic complexity of merging networks",
  J.ACM (Miltersen-Paterson-Tarui). https://dl.acm.org/doi/10.1145/227595.227693
- "On Optimal Merging Networks" (exact M(2,n), Batcher optimal m <= 4):
  https://link.springer.com/chapter/10.1007/978-3-540-45138-9_9 ; "Lower Bounds for
  Merging Networks": https://www.sciencedirect.com/science/article/pii/S0890540101929347
- Stober & Weiss, arXiv:2206.05597 (comparison-tree S16=46). https://arxiv.org/abs/2206.05597
- Dobrokhotova-Maikova, Kozachinskiy, Podolskii, ITCS 2023 constant-depth:
  https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ITCS.2023.43
- Kahn entropy / Dedekind: "Entropy, independent sets and antichains" (Kahn 2002):
  https://www.researchgate.net/publication/228606065 ; sparse Sperner 2024:
  https://arxiv.org/html/2411.03400v2 ; containers+entropy 2025: https://arxiv.org/pdf/2512.02995
- Dörrer, "Exact Lower Bounds for the Number of Comparisons in Selection", SEA 2025:
  https://drops.dagstuhl.de/storage/00lipics/lipics-vol338-sea2025/LIPIcs.SEA.2025.16/LIPIcs.SEA.2025.16.pdf
- Session computations: F(N) table + tight-shape enumeration + I1/I2 BFS (scripts
  `fcalc.py`, `insert.py`, scratchpad; trivially re-runnable, < 1 min total).
