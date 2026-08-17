# Cross-domain survey: computational group theory & isomorph-free generation

Date: 2026-08-17. Scope: five techniques from CGT / isomorph-free exhaustive
generation, mapped against the measured bottleneck profile of the sortnetopt
pipeline (`docs/sortnetopt-internals.md` §2-3, §8;
`evidence/v3/m2a/prototype-report.md` §5.7).

Bottleneck recap, for calibration:

* The exact permutation-subsumption test `subsumes_permuted`
  (`src/output_set/subsume.rs`) — a constraint-propagation matching search per
  pair — dominates the online-subsumption prototype: index lookup + insert is
  **49.8 % of all thread time** at n=10 in `evict` mode, and the leaf cost is
  the exact test (M2a §5.7). In the offline pipeline it is the prune/proof
  bottleneck (~78 % of that stage's runtime).
* Exact *equality* modulo S_n × complement is already O(1): `canon.rs` computes
  a canonical form (a hand-rolled individualization-refinement) and `StateMap`
  hashes it. Equality is not the problem; **containment** is.
* Memo mass sits at the two widths holding the most packed bytes (absolute
  widths 7-8 at n=9/10; inferred 8-9 at n=11), growth ×12,000 per +2 channels.
* n=13 extrapolation: ~3e13 explored sets, ~20 PB naive; M2a-style online
  subsumption projected 10-35× net — still 3-4 orders short.

---

## 0. A load-bearing distinction, stated first

The brief's question 1 asks whether canonical labeling could "replace pairwise
permutation-subsumption testing entirely (canonical form = O(1) hash lookup
instead of matching search)." **It cannot, and the reason should be recorded so
the idea is not re-litigated.**

Canonical forms decide *isomorphism* (equality up to the group action):
canon(A) == canon(B) iff ∃π. π(A) = B. `subsumes_permuted` decides
*embedding*: ∃π. π(A) ⊆ B. Embedding is not an equivalence relation, has no
class representative, and is not reducible to comparing two canonical strings —
two sets can be in strict subsumption relation while their canonical forms are
arbitrarily dissimilar (the canonical labeling of B is driven by B's own
structure, not by any subset's). The graph-theory analogue is exact: canonical
labeling (nauty/Traces) solves graph isomorphism; *subgraph* isomorphism is
NP-complete and is solved by CSP search (Glasgow solver), not by canonization.
Sortnetopt already exploits everything a canonical form can give
(O(1) equality dedup in `StateMap`); the residual 78 % is inherently a
matching-search problem, and the right cross-domain sources are the subgraph-
isomorphism and ILP θ-subsumption literatures (§2), not canonization (§1).

What canonical machinery *can* still contribute: (a) cheaper/stronger
permutation-invariant filters so fewer pairs reach the exact test (§2.2),
(b) isomorph-free *generation* so fewer objects exist to be tested (§1),
(c) orbit counting to predict how many objects there are at all (§3).

---

## 1. McKay-style canonical augmentation (isomorph-free generation)

**What it is.** McKay's canonical construction path method
([orderly.pdf, J. Algorithms 26 (1998) 306-324](https://users.cecs.anu.edu.au/~bdm/papers/orderly.pdf);
tutorial: [computationalcombinatorics.wordpress.com](https://computationalcombinatorics.wordpress.com/2012/08/13/canonical-deletion/))
generates each isomorphism class of objects exactly once by only accepting an
augmentation X → X∪{e} when e is (equivalent under Aut(X∪{e}) to) the
*canonical deletion* of the larger object. It needs no global "seen" table —
duplicate rejection is a local test — which is precisely why it is used when
the class population exceeds memory. The alternative, orderly generation
(Faradžev/Read), extends only canonical representatives and has the same
no-global-table property.

**Mapping to our bottleneck.** The search's dedup-by-hash role of `StateMap`
could in principle be replaced: expand a child output set only if the
comparator that produced it is the canonical last comparator of the child.
That would delete the memo table *as a dedup device* — O(depth) memory for
duplicate rejection. But sortnetopt's `StateMap` is not primarily a dedup
device: it is the DP value table (bounds shared across the DAG's many-parents
structure) and, after M2a, the subsumption antichain. Canonical augmentation
removes *isomorph* duplicates only; the measured redundancy is 99.4 %
*subsumption* redundancy (internals §8.0), which canonical augmentation does
not touch. A canonical-augmentation rewrite fits a bottom-up generate-and-prune
pipeline (the Codish et al. style, and sortnetopt's legacy `gnp` command), not
the top-down bound-improving B&B, whose whole point is sharing `State` between
parents.

**Expected gain.** On the current architecture: ~0 on memory (the antichain
must be stored anyway for subsumption), ~0 on the exact-test count. As the
skeleton of a hypothetical distributed generate-and-prune rewrite: removes the
global visited-set, which is the thing that makes distribution hard (internals
§5) — architectural value, not a constant factor.

**Cost / risk.** A rewrite of the search core (weeks), and the parent-child
"canonical deletion" test for output sets requires computing Aut(child) per
expansion — comparable cost to one canonicalization per child, which is already
paid. Risk: high — it abandons the DP that makes the top-down search efficient,
and the certificate emission assumes the DP structure. **Not recommended as a
line of attack for M2/M3; note it as the natural skeleton if a bottom-up
distributed pipeline is ever built.**

## 2. Faster embedding tests: subgraph-isomorphism / θ-subsumption technology

This is the direct hit on the 78 %. `Subsume::search` (filter_matching →
move_unique → select_guess → propagate → undo stack) is, structurally, a
1990s-era CSP solver: forward checking, unit propagation, min-degree branching.
Two mature literatures have spent 20 years past that point on the *same
problem shape*.

**2a. Glasgow subgraph solver techniques**
([McCreesh-Prosser-Trimble, ICGT 2020](https://ciaranm.github.io/papers/icgt2020-glasgow-subgraph-solver.pdf);
[github.com/ciaranm/glasgow-subgraph-solver](https://github.com/ciaranm/glasgow-subgraph-solver)).
State of the art for ∃π. π(pattern) ⊆ target. The measured-effective
ingredients, in their order of importance:

1. **Restarts + nogood recording**: run with a randomized value ordering,
   restart on a budget, record nogoods so no subtree is revisited. Two orders
   of magnitude on satisfiable instances in their benchmarks; our workload is a
   mix (index lookups mostly fail the exact test; prune hits succeed), so the
   honest transfer estimate is smaller.
2. **Bit-parallel all-different propagation**: our `remove_matching` is
   pairwise; a Régin-style or bit-parallel Hall-set all-different over the
   channel-matching variables prunes strictly more per node. Channel counts are
   ≤ 13, so the domains fit in one word each — the bit-parallel variant is
   nearly free.
3. **Invariant-based value filtering beyond degree**: they use neighbourhood
   degree sequences and path counts. Our analogue: per-channel-pair abstraction
   rows (already computed for the k-d point) used as *dominance* filters inside
   the matching, not just as a pre-filter — i.e., push `test_abstraction`
   coordinate dominance down into `filter_matching`'s per-pair test at all
   prefix depths, not only depth 0.

**2b. ILP θ-subsumption engines.** θ-subsumption (∃ substitution θ. Aθ ⊆ B) is
the identical problem over clause literals. Django
([Maloberti-Sebag, Machine Learning 55 (2004)](https://link.springer.com/article/10.1023/B:MACH.0000023150.80092.40))
recast it as CSP and gained "several orders of magnitude"; Subsumer
([Santos-Muggleton, ILP 2010](https://drops.dagstuhl.de/opus/volltexte/2010/2595))
adds **dynamic decomposition into independent components** — if the constraint
graph of the matching splits, solve the components independently and multiply.
For output sets: after `move_unique` commits forced channel pairings, the
residual bipartite compatibility graph often decomposes (channels interacting
only through already-fixed channels); solving blocks independently turns a
product search space into a sum.

**Mapping.** Drop-in replacement of `Subsume::search`'s internals; the call
sites (`index.rs` `test_precise`, `prune.rs`, `proof.rs`) are unchanged;
certificate-transparent (the test's *answer* is what matters, and `proof.rs`
re-derives permutations itself).

**Expected gain.** Honest: **2-5× on the exact-test component** (i.e., on
~50-78 % of the relevant stage), so roughly 1.5-3× end-to-end on prune/proof
and on the M2a online mode's 13.5× slowdown. Not an order of magnitude — the
instances are small (≤ 13 variables), so the asymptotic wins of nogoods/
decomposition have limited room. The cheapest item (bit-parallel domains +
all-different) is likely most of it.

**Cost.** Days-to-two-weeks in `subsume.rs` only, benchmarkable in isolation
against the M0b counter `subsumption search branches`. **Risk: low.** Pure
performance; differential-testable against the existing implementation on
millions of pairs.

**2c. A second-stage refinement filter (partition refinement as pre-test).**
Between the k-d tree's 12-coordinate prefix filter and the exact test, insert
one round of individualization-free *joint* partition refinement: refine the
channel partitions of A and B simultaneously by the abstraction rows and check
that B's cells dominate A's compatible cells (a necessary condition). This is
the standard IR idea (nauty's refinement,
[Practical Graph Isomorphism II](https://www.sciencedirect.com/science/article/pii/S0747717113001193);
[McKay-Piperno introduction](https://pallini.di.uniroma1.it/Introduction.html))
used as a *filter* rather than a canonizer, computed on demand and never
stored — so it does not repeat M2a's full-abstraction memory mistake (M2a §2.3
showed storing full abstractions is memory-negative). Expected: cuts the number
of pairs reaching the matching search by 2-10× at O(n·2^k) per pair. Risk: low;
it is a strictly-necessary-condition filter, soundness is one lemma.

## 3. Orbit counting to predict frontier sizes (n=13 feasibility instrument)

**What it is.** Two complementary estimators. (a) *Burnside-process +
importance sampling* ([Diaconis et al., arXiv:2501.11731](https://arxiv.org/abs/2501.11731);
Jerrum's Burnside process): a Markov chain whose stationary distribution is
uniform on orbits, combined with importance weights, gives unbiased estimates
of the number of orbits of a group action with controlled variance. (b)
*Knuth/Chen search-tree size estimation* (Knuth 1975; heuristic sampling
[Kilby et al.](https://www.cs.ubc.ca/~hutter/EARG.shtml/earg/stack/WS06-11-005.pdf);
stochastic enumeration [Rubinstein](https://link.springer.com/article/10.1007/s11009-015-9457-4)):
random root-to-leaf probes with product-of-branching-factor weights estimate
the size of a search tree/DAG without exploring it.

**Mapping.** The n=13 planning numbers (~3e13 sets, ~20 PB) are a two-point
extrapolation of the ×12,000-per-+2-channels law. A stratified Knuth estimator
run *inside the instrumented searcher* — probe random `improve` descents,
weight by branching factor, stratify by (width, |set|) — yields per-width
frontier estimates for n=12/13 at the cost of thousands of probes instead of
the full search. The pure-Burnside variant (count orbits of *all* vector sets)
is useless here — the reachable output sets are a vanishing fraction of all
sets, so the estimator must sample the reachable class, which is exactly what
search-tree probing does. Precedent that the orbit-counting arithmetic works at
this scale: Pawelski's R(9) — the number of inequivalent monotone Boolean
functions of 9 variables — via Burnside's lemma over the 29 cycle types of S_9
([arXiv:2305.06346](https://arxiv.org/pdf/2305.06346),
[JIS paper](https://cs.uwaterloo.ca/journals/JIS/VOL25/Pawelski/pawelski7.pdf)).

**Expected gain.** Zero speedup; **decisive planning value**: it converts "~20
PB (author's estimate)" into a per-width memory/step budget with error bars,
which is the input the M2 pivot rule and the out-of-core sharding design
(internals §8.2) actually need. DAG-vs-tree double counting biases the raw
Knuth estimator upward — the canonical-hash hit rate per width (already an M0b
counter) corrects it.

**Cost.** Days: a probe mode in the instrumented build + an analysis notebook.
**Risk: medium** — variance can be brutal on deep skewed trees; mitigate with
heuristic stratification and by validating the estimator against the exactly
known n=9/10/11 populations first (three calibration points exist for free).

## 4. Lessons from the 2023 D(9) computations and comparator-network generation

**What they did.** Both independent D(9) computations avoided pairwise
comparison entirely and are the best modern exemplars of "canonicalize + orbit
arithmetic at scale":

* Van Hirtum et al. ([arXiv:2304.03039](https://arxiv.org/abs/2304.03039);
  [ACM TRETS 2024](https://dl.acm.org/doi/full/10.1145/3674147)) enumerated the
  **490M canonical equivalence classes** of monotone Boolean functions on 7
  variables once, offline (canonization under S_7, implemented in Rust), then
  expressed D(9) as a sum over class pairs of a per-pair "P-coefficient"
  computed by an FPGA kernel — 490M independent, separately verifiable work
  units, each result CPU-checkable.
* Jäkel ([arXiv:2304.00895](https://arxiv.org/abs/2304.00895) /
  [J. Comput. Algebra 2023](https://www.sciencedirect.com/science/article/pii/S2772827723000037))
  used (anti-)isomorphic lattice intervals and matrix-permanent formulas over
  canonical representatives, with orbit sizes as multiplicities.

* For comparator networks specifically: Codish-Cruz-Filipe-Schneider-Kamp
  generated **all two-layer prefixes modulo symmetry**
  ([arXiv:1404.0948](https://arxiv.org/pdf/1404.0948)), reducing n=13's first
  two layers to a few hundred canonical representatives; this plus the
  Bundala-Závodný subsumption relation is the backbone of every recent
  optimality proof ([To the end and back again, JCSS 2017](https://www.sciencedirect.com/science/article/pii/S0022000016300162)).
  Nobody in this literature has published a McKay-style canonical-augmentation
  enumeration of output sets; the field uses canonical prefixes + subsumption,
  i.e., exactly Harder's architecture.

**Mapping — three transplants, in decreasing confidence.**

1. **Split-by-canonical-prefix for distribution and for the u32 certificate
   blocker.** The D(9) pattern "one canonical enumeration at small size →
   millions of independent subcomputations → separately checkable results"
   maps onto: enumerate canonical 2-layer (or 3-layer) prefixes of width 13,
   run an independent bounded search per prefix, and compose per-prefix
   certificates *outside* the verified kernel. This simultaneously answers the
   multi-machine gap (internals §5: no distribution support) and the M5
   certificate blocker (u32 caps a monolithic proof at 4.29e9 steps vs ~1.5e11
   needed): per-prefix certificates each stay under the cap. The composition
   lemma ("min over canonical prefixes + prefix lengths bounds S(13)") is the
   van Voorhis-style argument the programme already needs at M1.
2. **Precompute the bottom of the DP.** D(9)'s enumerate-small-widths-once:
   the populations at widths ≤ 8 are search-independent (same canonical sets
   recur in every run — M2a §5.4 shows the width-k antichains are stable).
   A one-time canonical table of width-≤ 9 output sets with exact bounds,
   mmap-shared across all machines/runs, removes those widths from `StateMap`
   forever. Caveat to verify first: whether every width-k set reachable in the
   n=13 search is reachable from `all_values(k)` (prunings of output sets are
   not obviously k-channel output sets); if not, the table must be keyed on
   the larger reachable class and the precomputation is itself a search.
3. **Orbit-size weighting** (Burnside arithmetic instead of enumeration) —
   the D(9) trick of never listing class members — has no direct analogue in a
   bound-proving B&B (we need per-class bounds, not counts). No transplant.

**Expected gain.** Item 1: not a constant factor — it is the difference
between "cannot run n=13 at all" (single global RAM table + u32 cap) and "can
run it as N independent jobs." Item 2: removes the sub-mass widths from
resident memory (at n=13 those are not the peak widths, so honest memory gain
is small, maybe 1.2-2×; the real win is skipping re-derivation work every run).

**Cost / risk.** Item 1 is a project-scale architecture decision (M1 material),
weeks-months; risk medium — the composition proof must be written, and
per-prefix searches lose cross-prefix memo sharing (Harder's DP shares
sub-states across the whole cube; measured sharing across prefixes is unknown —
instrument this before committing: it could cost anywhere from 1.5× to ~10×
extra total work). Item 2: ~1-2 weeks; risk low except the reachability caveat.

## 5. Antichain / Dilworth-type bounds on maximum frontier size

**What it is.** The pruned frontier per (width, bound) is by construction an
antichain in the subsumption quasi-order (that is what `prune` computes, and
M2a §5.4 showed the online index equals it exactly). The question is whether
poset width theory gives an a priori cap. Dilworth: width = min chain cover
([Dilworth's theorem](https://en.wikipedia.org/wiki/Dilworth%27s_theorem));
Sperner: the width of the subset lattice 2^[N] is C(N, N/2)
([Antichain](https://en.wikipedia.org/wiki/Antichain)).

**Mapping and honest assessment.** The ambient bound is useless: output sets
live in 2^[2^k], so Sperner gives C(2^k, 2^(k-1)) — astronomically loose. The
relevant order is subsumption (⊆ mod S_k × complement) restricted to
*reachable* output sets, and no non-trivial width bound for that poset exists
in the literature. The closest bodies of work are (a) the antichain method in
automata theory (De Wulf-Doyen-Raskin, universality via ⊆-minimal state sets),
where frontiers are empirically tiny but provably exponential in the worst
case, and (b) graph-subsumption state-space exploration
([GROOVE, arXiv:1210.6413](https://arxiv.org/pdf/1210.6413)) — same picture:
order-of-magnitude empirical reductions, no useful analytic cap. A genuinely
new theorem here (an LYM-type inequality over reachable output sets weighted by
orbit size) would be a research contribution, not an implementation task.

**Expected gain.** As theory: unknown, probably none on a useful timescale.
The pragmatic substitute is §3's empirical estimator: the quantities the bound
would cap (15.4M at n=11 per Harder; extrapolated ~1.5e11-ish certificate-
relevant sets at n=13) are exactly what stratified sampling estimates. One firm
anchor the antichain view *does* give: the online index can never beat the
antichain floor (M2a hit it exactly), so **the subsumption ceiling at n=13 is
predictable in advance** by estimating the antichain size per width — feed
that into the M2 gate instead of the fixed "≥50×" criterion (M2a rec. 5).

**Cost / risk.** Zero implementation; fold into §3's estimator. Risk of
pursuing the theory route: high (open-ended), recommend against as programme
work.

---

## Summary table

| # | technique | attacks | honest gain | cost | risk |
|---|---|---|---|---|---|
| 1 | canonical augmentation | dedup memory | ~0 on current architecture; skeleton for a bottom-up rewrite only | weeks | high |
| 2a/b | Glasgow/Django CSP tech in `subsume.rs` | the 78 % exact test | 2-5× on the test, 1.5-3× on prune/proof and M2 online overhead | days-2 wks | **low** |
| 2c | on-demand refinement pre-filter | # pairs reaching exact test | 2-10× fewer exact tests | days | **low** |
| 3 | orbit/tree-size sampling estimator | n=13 planning numbers | no speedup; per-width budgets with error bars, 3 free calibration points | days | medium |
| 4.1 | canonical-prefix decomposition (D(9) pattern) | distribution + u32 certificate cap | feasibility-class, not constant-factor; unknown memo-sharing loss (measure first) | M1-scale | medium |
| 4.2 | precomputed small-width canonical tables | resident memory, re-derivation | 1.2-2× memory; large re-run savings; reachability caveat | 1-2 wks | low-med |
| 5 | antichain width theory | frontier size bound | none available; use §3 empirically | — | high (open research) |

## Sources

* McKay, [Isomorph-free exhaustive generation](https://users.cecs.anu.edu.au/~bdm/papers/orderly.pdf), J. Algorithms 26 (1998).
* [Canonical deletion tutorial](https://computationalcombinatorics.wordpress.com/2012/08/13/canonical-deletion/); [U. Ottawa lecture notes](https://www.site.uottawa.ca/~lucia/courses/5165-10/IsomorphFreeGen.pdf).
* McKay & Piperno, [Practical Graph Isomorphism II](https://www.sciencedirect.com/science/article/pii/S0747717113001193); [nauty/Traces home + benchmarks](https://pallini.di.uniroma1.it/); [nauty user guide (hypergraphs via Levi/bipartite reduction)](https://users.cecs.anu.edu.au/~bdm/nauty/nug26.pdf).
* McCreesh, Prosser, Trimble, [The Glasgow Subgraph Solver](https://ciaranm.github.io/papers/icgt2020-glasgow-subgraph-solver.pdf), ICGT 2020; [repo](https://github.com/ciaranm/glasgow-subgraph-solver).
* Maloberti & Sebag, [Fast θ-subsumption with CSP algorithms (Django)](https://link.springer.com/article/10.1023/B:MACH.0000023150.80092.40), Mach. Learn. 55 (2004); Santos & Muggleton, [Subsumer](https://drops.dagstuhl.de/opus/volltexte/2010/2595), ILP 2010.
* Diaconis et al., [Counting group orbits: Burnside process + importance sampling](https://arxiv.org/abs/2501.11731) (2025).
* Kilby, Slaney, Thiébaux, Walsh, [Estimating search tree size](https://www.cs.ubc.ca/~hutter/EARG.shtml/earg/stack/WS06-11-005.pdf); Rubinstein et al., [Stochastic enumeration for counting trees](https://link.springer.com/article/10.1007/s11009-015-9457-4).
* Van Hirtum et al., [A computation of D(9) using FPGA supercomputing](https://arxiv.org/abs/2304.03039); [ACM TRETS version](https://dl.acm.org/doi/full/10.1145/3674147).
* Jäkel, [A computation of the ninth Dedekind number](https://www.sciencedirect.com/science/article/pii/S2772827723000037) (2023).
* Pawelski, [Inequivalent monotone Boolean functions of 9 variables](https://arxiv.org/pdf/2305.06346); [8-variable JIS paper](https://cs.uwaterloo.ca/journals/JIS/VOL25/Pawelski/pawelski7.pdf).
* Codish, Cruz-Filipe, Frank, Schneider-Kamp, [Sorting networks: to the end and back again](https://www.sciencedirect.com/science/article/pii/S0022000016300162), JCSS 2017; [Two-layer prefixes](https://arxiv.org/pdf/1404.0948); Bundala & Závodný symmetry relation (op. cit.).
* [Dilworth's theorem](https://en.wikipedia.org/wiki/Dilworth%27s_theorem); [Antichain / Sperner](https://en.wikipedia.org/wiki/Antichain); Rensink & Zambon, [Graph subsumption in abstract state space exploration](https://arxiv.org/pdf/1210.6413).
