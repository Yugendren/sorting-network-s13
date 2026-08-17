# Cross-domain survey: symbolic data structures and heuristic-search algorithmics for the S(13) frontier

Date: 2026-08-17. Scope: techniques from model checking, AI planning, SAT/ATP,
and exhaustive combinatorial search, mapped onto the sortnetopt bottleneck
profile as measured in `docs/sortnetopt-internals.md` (§2.5, §8) and
`evidence/v3/m2a/prototype-report.md`.

**Bottleneck recap (what any technique must beat).**

* The frontier at width k is a family of canonical subsets of {0,1}^k, stored
  as packed bitmaps of 2^k/8 bytes (16–64 B at the mass widths k = 7–9).
  2.46e9 sets / 178 GiB RAM / 93 GiB dump at n=11; ~3e13 sets / ~20 PB
  extrapolated at n=13.
* The dominance relation is **subset-modulo-channel-permutation-and-complement**
  (`subsumes_permuted`), not literal subset. This one fact disqualifies or
  weakens several off-the-shelf techniques below.
* M2a measured: on-line subsumption reaches the per-width antichain ceiling
  exactly, but costs 13.5× wall time, of which 49.8% of all thread-seconds is
  inside the index (31.2% lookup, 17.5% insert; abstraction computation is
  only 1.0%). The exact `subsumes_permuted` leaf test and a single per-width
  `RwLock` are the cost, not the feature vector.
* Structural facts to exploit: `apply_comparator` never increases |set|;
  extremal pruning strictly decreases width; so the DAG is stratified by
  (width, popcount), both monotone non-increasing along edges. The offline
  prune already uses ascending-|set| buckets for exactly this reason.

Verdict summary (details per section):

| # | technique | attacks | honest expected gain | cost | risk |
|---|---|---|---|---|---|
| 1 | ZDD frontier | memory | 3–20× on *disk dump* only; likely ≤1× or negative in RAM | high | **high** |
| 2 | DDD / SDD external-memory search | memory ceiling | 10–50× effective capacity per node + multi-node route | high | medium |
| 3 | Pattern databases | time + small memory | 1.5–2× memory, lock relief; bound strengthening unlikely | low–med | low (freeze) / high (new bounds) |
| 4 | SAT/ATP subsumption engines | the 13.5× slowdown | 3–10× on index overhead → ~2–4× wall | **low** | **low** |
| 5 | Hash-consing / chunk sharing | memory | 1.5–4× on stored keys (needs census; measurable today) | low | low |

---

## 1. ZDDs / BDDs: one decision diagram per width instead of millions of bitsets

**What it is.** A zero-suppressed decision diagram (Minato 1993; Knuth TAOCP
4A Fascicle 1) is a canonical DAG representing a family of sets over a fixed
variable universe, with node sharing across members; for structured sparse
families it routinely achieves orders-of-magnitude compression over explicit
listing. The "family algebra" gives union, intersection, difference, and —
crucially for us — `nonsupersets`/`nonsubsets` and `minimal`/`maximal`
(antichain extraction), i.e. exactly bulk subsumption pruning as single
symbolic operations. The universe here would be the 2^k vectors of {0,1}^k
(256 variables at k=8, 512 at k=9), and the width-k frontier one ZDD whose
members are output sets.

**Mapping to our bottleneck.** The frontier *is* a family of sets of binary
vectors, and the offline prune (group file → subsumption-minimal antichain) is
literally `Z.minimal_under_containment` in family algebra — one symbolic op
replacing 2.46e9 pairwise-indexed tests. Two obstructions, one fatal-unless-
solved: (a) our dominance is subset **modulo channel permutation ×
complement**; ZDD containment ops are literal. Making the ZDD closed under the
symmetry means inserting up to k!·2 permuted variants per set (80,640 at k=8),
and because a channel permutation permutes the 2^k *variables*, the permuted
copies share structure poorly under any fixed variable order — ZDD size is
notoriously order-sensitive. (b) Complexity: it is now *proven* (Kobayashi et
al., ISAAC 2024) that the family-algebra operations Knuth lists — including
maximal/minimal and nonsupersets — **cannot be done in worst-case poly time in
the input ZDD sizes**; intermediate blow-up is real, not folklore pessimism.
Also note our member sets are *dense* subsets of the cube (up to 2^k of 2^k
elements); ZDDs favor sparse members, so one would store complements —
another unvalidated assumption. Measured literature ratios (e.g. Top-ZDD /
DenseZDD work: 3× further compression over plain ZDDs on set-family
benchmarks; "orders of magnitude vs explicit listing" for itemset families)
are for families *without* a quotient by a symmetry group; no prior art was
found applying ZDDs to sorting-network output sets, so no transferable
measured ratio exists for our family shape.

**Where it can still win.** The 93 GiB dump is written per (width, bound)
group — exactly the granularity at which a ZDD-per-group archive format makes
sense, since the offline `prune`/`gen-proof` stages read groups sequentially
anyway and canonical-form sets at one width share long common prefixes of
their bitmaps. A ZDD (or even a simple trie/prefix-sharing encoding) of a
group file is a contained, offline experiment: build it from an existing
`group_8_*.bin`, measure nodes×(node size ≈ 20–30 B) vs raw bytes.

* **Expected gain:** disk-dump compression 3–20× (speculative; measure on
  existing n=10/n=11 group files before believing anything). In-RAM online
  frontier: expected ≤1× — the k!·2 symmetry closure and the per-set `State`
  payload (ZDDs store families, not maps) most plausibly make it a loss.
* **Implementation cost:** high. No mature Rust ZDD crate at this scale;
  CUDD/Sylvan are C and BDD-centric; the symmetry problem is research-grade.
* **Risk:** high. Proven worst-case blow-up of the exact ops we need, order
  sensitivity, no prior art on this family. **Do the one-afternoon offline
  compression census; do not build the online version.**

Sources: [Minato/ZDD overview](https://www.emergentmind.com/topics/zero-suppressed-binary-decision-diagrams-zdds),
[Knuth TAOCP Vol 4 Fasc 1](https://dl.acm.org/doi/10.5555/1593023),
[Kobayashi et al., Single Family Algebra Operation on BDDs and ZDDs Leads to Exponential Blow-Up, ISAAC 2024](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ISAAC.2024.52) ([arXiv:2403.05074](https://arxiv.org/pdf/2403.05074)),
[Top ZDDs (SEA 2020)](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SEA.2020.6),
[DenseZDD](https://link.springer.com/chapter/10.1007/978-3-319-38851-9_14),
[Knuth ZDD lecture notes](https://crypto.stanford.edu/pbc/notes/zdd/).

---

## 2. Frontier search, delayed duplicate detection (DDD), structured duplicate detection (SDD)

**What it is.** The planning/search community's discipline for exhaustive
search with frontiers far beyond RAM: (i) *frontier search* (Korf) stores only
the open layer and deletes closed layers, reconstructing paths later;
(ii) *delayed duplicate detection* (Korf 2003/2004, and hash-based DDD in his
linear-time disk-based search) appends generated states to disk files
unchecked and merges duplicates later with **sequential-only** I/O — this is
what completed the full BFS of the Fifteen Puzzle (~10^13 states, ~1.4 TB
disk-resident frontier); (iii) *structured duplicate detection* (Zhou &
Hansen 2004–2007) partitions states by a projection ("abstraction") chosen so
each bucket's successors land in few buckets ("duplicate-detection scope"),
keeping only active buckets in RAM — measured **16–58× internal-memory
reduction at ~+24% runtime**, and the same partition doubles as the
synchronization unit for parallel and multi-machine search. Cooperman &
Kunkle's 26-move Rubik result (7 TB disk) and the cube20.org "God's number =
20" computation (coset decomposition into 2.2e9 independent subproblems, 35
CPU-years) are the existence proofs at our target scale.

**Mapping to our bottleneck.** Harder's own diagnosis — `StateMap` is a
globally shared random-access table, so distribution "would slow it down a
lot" — is precisely the disease DDD/SDD was invented to cure. Our graph hands
us the SDD abstraction for free: **(width, popcount)** is monotone
non-increasing along every edge (comparators never grow |set|; pruning drops
width), so the duplicate-detection scope of bucket (k, s) is {(k, s' ≤ s)} ∪
{(k−1, ·)} — far better locality than sliding-tile projections, and identical
to the bucketing `prune.rs` already uses offline. It is also
subsumption-compatible (a subsumer never has larger popcount — M2a
recommendation 2), so **the same sharding serves duplicate detection, batched
subsumption, out-of-core spill, and multi-node ownership simultaneously**.
Concretely: restructure `improve` so a frame emits batched `get`/`set`
requests keyed by (width, popcount-bucket, shard-hash); buckets are
append-only runs on NVMe, merged and subsumption-pruned when scheduled — DDD's
"append now, dedupe sequentially later" replacing today's per-lookup
random access. Two mismatches to engineer around: our search is a
bound-improving DP over a DAG, not a one-pass BFS — states are *re-read*
across successive-approximation iterations, so closed strata cannot be deleted
(frontier-search's signature trick does not apply); but M0b/M2a measured that
88–100% of the table is built in the final bound iteration, so the re-read
traffic across iterations is small relative to the final-iteration build, and
the stratification means bounds can be finalized bottom-up per stratum
(retrograde style: process (k, s) after (k, s' < s) and (k−1, ·)), converting
random gets into sequential merges. The cube20 coset decomposition also maps
directly onto splitting n=13 by first-layers prefix into independently-run,
independently-certified subproblems — which simultaneously dodges the u32
certificate-step-count blocker (internals §6.3).

* **Expected gain:** no reduction in state count — this is a *capacity*
  technique. 10–50× effective memory per node (Zhou–Hansen's 16–58× is the
  honest anchor) at ~1.2–2× time cost if batching is done well, plus the only
  credible route to multi-machine execution. Composed with M2a's 10–35×
  net subsumption reduction, n=11 fits on one workstation and n=13 moves from
  "20 PB RAM" to "hundreds of TB of NVMe across a cluster" — still a major
  project, but a recognisable one.
* **Implementation cost:** high — rewrites the async coroutine structure of
  `search.rs` and replaces the thread pool (the global `pending` lock dies the
  moment workers block on I/O). This is the M2b/M3-scale item the internals
  doc already ranks #2; the cross-domain literature mainly *de-risks* it by
  supplying the design pattern and measured constants.
* **Risk:** medium. Search order changes (result provably invariant, but
  bound-sequence gates must be re-baselined); determinism/checkpointing must
  be designed in; the batched-DP-over-DAG variant (as opposed to pure BFS) is
  our own engineering, not a paper we can copy.

Sources: [Korf, Best-First Frontier Search with Delayed Duplicate Detection, AAAI 2004](https://cdn.aaai.org/AAAI/2004/AAAI04-103.pdf),
[Korf, Delayed Duplicate Detection, IJCAI 2003](https://dl.acm.org/doi/10.5555/1630659.1630926),
[Korf, Linear-time disk-based implicit graph search](https://www.semanticscholar.org/paper/Linear-time-disk-based-implicit-graph-search-Korf/41cc7c530654b139759f193a0814340c807ecd74),
[Zhou & Hansen, Structured Duplicate Detection in External-Memory Graph Search, AAAI 2004](https://cdn.aaai.org/AAAI/2004/AAAI04-108.pdf),
[Zhou & Hansen, Parallel Structured Duplicate Detection, AAAI 2007](https://www.semanticscholar.org/paper/Parallel-Structured-Duplicate-Detection-Zhou-Hansen/28549c5569025c9fca43a22202e0a1f74985d3e3),
[Zhou & Hansen, Domain-Independent SDD](https://cdn.aaai.org/Workshops/2006/WS-06-08/WS06-08-006.pdf),
[cube20.org — God's Number is 20](https://www.cube20.org/),
[Rokicki et al., The Diameter of the Rubik's Cube Group Is Twenty](https://tomas.rokicki.com/rubik20.pdf),
[Rokicki, Twenty-Five Moves Suffice](https://arxiv.org/pdf/0803.3435).

---

## 3. Pattern databases / abstraction heuristics

**What it is.** A pattern database (Culberson & Schaeffer 1998; Korf & Felner's
disjoint/additive variants) precomputes the exact cost-to-go for every state
of an *abstraction* (homomorphic projection) of the search space into a
read-only lookup table, giving an admissible, consistent heuristic for the
concrete search. Disjoint PDBs partition the problem so abstract costs add
without overestimating. The tables are computed once by exhaustive backward
search over the (small) abstract space and then shared across all searches,
machines, and runs.

**Mapping to our bottleneck.** Two distinct readings, of very different
quality:

*Reading A — freeze the small widths (sound, cheap).* The DP already *is* a
cost-to-go table; the PDB move is to make the low-width strata a **static,
precomputed, read-only artifact**. All canonical output sets of width ≤ 7 that
are reachable ever (union over runs) number in the low hundreds of thousands
(n=10 census: 170k entries at k ≤ 7), and their exact bounds never change
between runs. Precompute once, `mmap` everywhere: those widths leave the
mutable `StateMap`, the shard locks, and the eviction problem entirely; on a
multi-node design they replicate for free instead of being sharded. This
mirrors Zhou & Hansen's external-memory PDBs. Memory saved is real but modest
at n=11–13 (the mass is at widths 8–9); the bigger wins are lock-path relief
and cross-run amortization.

*Reading B — a stronger admissible bound than van Voorhis/Huffman (research
bet).* The Huffman bound is already an abstraction heuristic: it relaxes "a
network sorting A" to "channels must be pairwise merged, each merge costing
1 + max of children". A PDB-style strengthening would need a different
homomorphism of output sets — e.g. project to a channel subset, or to the
popcount-layer profile (|A ∩ layer_j|)_j — with the property that every
comparator application in the concrete maps to at most one unit-cost step in
the abstract; then exhaustively solve the abstract space. Nothing in the PDB
literature hands us such a projection: comparators act on *pairs* of channels
and a channel-subset projection collapses comparators to no-ops
non-uniformly, which destroys the unit-cost mapping (you get admissible but
very weak, like non-additive tile PDBs with most tiles removed). And any
bound the search *uses* must be re-derivable at certificate time (the
justification landmine, internals §3.6.4) — a PDB bound has no proof step in
the current format unless it decomposes into subsumption + Huffman/successor
steps the checker already knows.

* **Expected gain:** Reading A: perhaps 1.3–2× memory at n=10-scale, less at
  n=13 (mass moves up-width); real value is removing small widths from every
  lock/eviction/sharding design and reusing tables across the whole campaign.
  Reading B: unbounded upside in principle, but no concrete candidate
  abstraction survives first contact; treat as a paper-sized bet, not a
  milestone.
* **Implementation cost:** Reading A: low-medium (a dump-format reader plus a
  read-only tier in `StateMap::get`). Reading B: high, plus checker/format
  implications.
* **Risk:** Reading A: low — it is memoization made persistent; certificate
  path unchanged if the frozen tier keeps its group-file provenance.
  Reading B: high (admissibility proofs, certificate justification).

Sources: [Culberson & Schaeffer lineage + overview](https://dl.acm.org/doi/10.1016/S0004-3702%2801%2900092-3),
[Korf & Felner, Disjoint Pattern Database Heuristics](https://www.sciencedirect.com/science/article/pii/S0004370201000923),
[Felner, Korf & Hanan, Additive Pattern Database Heuristics, JAIR](https://dl.acm.org/doi/10.5555/1622487.1622496),
[Zhou & Hansen, External-Memory Pattern Databases Using SDD](https://www.semanticscholar.org/paper/External-Memory-Pattern-Databases-Using-Structured-Zhou-Hansen/72edd38cf4c090c94ca7bf69d6c0abb746c4e508).

---

## 4. Subsumption engines from SAT solvers and theorem provers

**What it is.** ATP/SAT systems answer "does any stored clause subsume this
one" (forward) and "which stored clauses does this one subsume" (backward)
billions of times; thirty years of engineering has converged on: (i) **feature
vector indexing** (Schulz, E prover) — each clause gets a fixed-length vector
of cheap features that are *monotone under subsumption* (a subsumer's feature
never exceeds the subsumee's); vectors live in a shared-prefix **trie**, and a
forward query walks only branches with all coordinates ≤ the query's (≥ for
backward), running the exact test only at surviving leaves; (ii) **one-word
signatures** (SatELite, CaDiCaL): a 64-bit hash-of-features per clause so that
`sig(A) & ~sig(B) != 0` refutes A ⊆ B in one AND-NOT before anything else
runs; (iii) length/popcount bucketing as feature #0; (iv) lazy backward
subsumption (Zhang 2005) via one-watched-literal schemes instead of eager
eviction. Schulz's measured claim: FVI made subsumption cheap enough that E
could afford aggressive simplification that was previously prohibitive, with
small indices and a trivially simple implementation.

**Mapping to our bottleneck.** This is the *same problem*, already solved
under harsher constraints (their subsumption test is NP-complete
θ-subsumption; ours, permuted subset, is a constrained matching of similar
flavor). sortnetopt's `abstraction` vector *is* a feature vector in exactly
Schulz's sense — every coordinate is monotone under permuted containment
(that is what `test_abstraction` checks) — but it is deployed as a **k-d tree
cascade over 24–448-dim points**, which is the one data structure the ATP
community tried and abandoned for this workload (high-dim k-d trees degrade
toward linear scans; M2a's 31.2% lookup + 17.5% insert shares say ours is
degrading too). Direct transfers, in order of (gain / effort):
  1. **64-bit permutation-invariant signature per stored set**, packed from
     quantized invariant features (popcount-layer profile, extremal-channel
     counts, top abstraction coordinates). One AND-NOT rejects a candidate
     before the k-d node test, and signatures for a whole bucket scan
     vectorize (8–32 per cache line). SatELite-lineage solvers report this
     filter removes the vast majority of exact tests; our leaf test
     (`subsumes_permuted`, a backtracking matching) is far more expensive
     than theirs, so the filter is worth *more* here.
  2. **Replace the k-d cascade with a popcount-bucketed FV trie** on the
     12–24 most discriminating coordinates (M2a's DIMS sweep already
     identified the knee at 12). Tries give shared prefixes (memory), cheap
     insert (no cascade rebuilds — M2a's 17.5% insert cost includes exactly
     those), and a natural fit with the ascending-popcount scan order that
     both `prune.rs` and recommendation 2 of M2a already use.
  3. **Asymmetric forward/backward structures**: forward (get-side, 98.9%
     hit rate, hottest) wants the trie + signatures; backward (eviction) can
     go lazy à la Zhang — mark dominated entries dead and sweep them during
     the existing merge/census passes instead of eagerly restructuring.
* **Expected gain:** memory-neutral to mildly positive (trie prefix sharing
  vs 24-B k-d points); the target is the **13.5× wall-time regression**:
  cutting exact-test invocations 5–20× via signatures plus removing cascade
  rebuild costs makes 3–10× reduction of the 49.8% index share realistic →
  net wall-time regression drops to roughly 2–4×, which changes the n=11
  projection from "3–10 days" toward "1–2 days". No effect on the state-count
  exponent.
* **Implementation cost:** low-to-medium — signatures alone are ~100 lines
  inside `OutputSetIndex` and testable against the existing M2a harness with
  bit-identical results required; the trie swap is a contained replacement of
  `index/tree.rs` behind the same API.
* **Risk:** low. Both filters are *necessary-condition* prefilters in front
  of an unchanged exact arbiter, exactly like M2a's truncated-prefix argument
  (§2.3): answers cannot change, only speed. Certificate-transparent.

Sources: [Schulz, Simple and Efficient Clause Subsumption with Feature Vector Indexing](https://link.springer.com/chapter/10.1007/978-3-642-36675-8_3),
[E prover FVI notes](http://www.eprover.eu/E-eu/FVIndexing.html),
[Schulz, Fingerprint Indexing for Paramodulation and Rewriting](https://link.springer.com/chapter/10.1007/978-3-642-31365-3_37),
[Eén & Biere, SatELite: Effective Preprocessing in SAT](https://www.ccs.neu.edu/home/pete/courses/Decision-Procedures/2007-Fall/readings/Een_Biere_Preprocessing_SAT_Var_Clause_Elimination.pdf) (64-bit clause signatures),
[Biere et al., Preprocessing chapter, Handbook of Satisfiability](https://cca.informatik.uni-freiburg.de/papers/BiereJarvisaloKiesl-SAT-Handbook-2021-Preprocessing-Chapter-Manuscript.pdf),
[Zhang, On Subsumption Removal and On-the-Fly CNF Simplification](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/sat_2005_subsumption.pdf),
[Sedlar et al., SAT Solving for Variants of First-Order Subsumption](https://arxiv.org/pdf/2412.16058).

---

## 5. Hash-consing / Merkle-style structural sharing of stored bitmaps

**What it is.** Hash-consing keeps exactly one copy of every distinct
substructure in a global unique table and represents objects as small ids
pointing at shared parts; applied recursively it yields maximal sharing (a
BDD/ZDD is precisely bitmaps hash-consed to fixpoint on halves), and it makes
equality O(1) and memoization by id trivial. It is the workhorse of BDD
packages, SMT/ATP term banks, and content-addressed stores.

**Mapping to our bottleneck.** A width-9 packed key is 64 B; split it at the
top channel: the two 32-B halves are the sub-bitmaps for channel 9 = 0 / 1 —
i.e. genuinely meaningful subfamilies (they are one-channel restrictions, the
same objects extremal pruning manipulates), so cross-set repetition is
structurally plausible, not just hoped for: canonical form pushes constrained
channels into fixed positions, and millions of near-antichain sets at one
width plausibly reuse a much smaller pool of halves/quarters. Storing
(id_hi: u32, id_lo: u32) + a shared half-pool turns 64 B into 8 B plus pool;
recursing one more level turns the pool entries into id-pairs too. This is
the *bottom-up* road into ZDD territory that keeps the exact per-set `State`
payload, the existing subsumption machinery (reconstruct or stream bitmaps
from ids), and dodges section 1's family-algebra risks entirely. The decisive
number is measurable **today, with zero code in the search**: over an existing
`group_9_*.bin` / `group_8_*.bin` dump, count distinct 32-B and 16-B aligned
halves vs total. If distinct/total at n=10–11 is ≤ 25%, the technique pays
2–4× on exactly the strata (widths 8–9) where the n=11–13 mass sits, and it
*composes multiplicatively* with M2a's antichain reduction and section 2's
out-of-core sharding (smaller records = fewer bytes moved per batch).

* **Expected gain:** 1.5–4× on stored key bytes at the mass widths — honest
  only after the census; could be ~1× if canonical antichain sets turn out
  to have near-unique halves. Zero gain on entry *count*.
* **Implementation cost:** census: one hour with existing dumps. In-search
  adoption: medium — an append-only interned pool per width (append-only
  means no refcounting, matching the memo table's no-eviction baseline;
  M2a's eviction path would leak pool slots, acceptably).
* **Risk:** low. Purely representational; bitmaps reconstruct exactly;
  certificate-transparent. Main hazard is CPU: `subsumes_unpermuted` and
  abstraction computation want contiguous bitmaps, so hot paths must unpack
  ids to a scratch buffer (cheap, but it partially offsets the bandwidth win).

Sources: [Braibant, Jourdan & Monniaux, Implementing and reasoning about hash-consed data structures](https://arxiv.org/pdf/1311.2959),
[BDDs in OCaml — unique tables](https://braibant.github.io/update/2014/06/17/bdd-1.html),
[Zhou & Have, Efficient Tabling of Structured Data with Enhanced Hash-Consing](https://arxiv.org/abs/1210.1611),
[Knuth TAOCP 4A Fasc. 1 (BDD/ZDD node sharing)](https://dl.acm.org/doi/10.5555/1593023).

---

## Cross-cutting recommendations

Ordered by (evidence strength × fit to the measured bottleneck ÷ risk):

1. **Adopt the ATP subsumption-engine playbook inside `OutputSetIndex` (§4)**
   — 64-bit invariant signatures first, popcount-bucketed FV-trie second.
   It attacks the M2a-measured 49.8% index cost with the lowest-risk,
   best-evidenced engineering in this survey, is certificate-transparent, and
   is a precondition for M2a being affordable at n=11.
2. **Design the out-of-core/multi-node layer as SDD with the (width,
   popcount) partition (§2)** — the partition is handed to us by the problem,
   is subsumption-compatible, and the planning literature supplies measured
   constants (16–58× memory at +24% time) and the parallelization pattern.
   Adopt the cube20 coset-style decomposition of n=13 into independently
   certified prefix subproblems at the same time (also solves the u32
   step-count blocker).
3. **Run the two zero-code censuses this week**: (a) distinct-half count on
   existing group files (§5 go/no-go); (b) ZDD/trie compression of one group
   file (§1 go/no-go, offline-archive use only).
4. **Freeze widths ≤ 7 as a read-only shared PDB tier (§3 Reading A)** when
   the multi-node design lands; skip Reading B unless someone produces a
   candidate homomorphism with an admissibility proof.
5. **Do not pursue online ZDD frontiers (§1)** — proven worst-case blow-up on
   the needed ops, permutation symmetry unhandled, no prior art; revisit only
   if census (3b) shows startling ratios.
