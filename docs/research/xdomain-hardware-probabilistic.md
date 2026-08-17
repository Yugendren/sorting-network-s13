# Cross-domain survey: hardware-shaped algorithmics and probabilistic/streaming methods

Scope: five technique families from databases, HPC, and sketching, mapped onto the
measured bottleneck profile of the v3 pipeline (internals §8, perf-report M2b §5/§7):

- **Kernel**: `Subsume::search` — exact permutation subsumption, a constraint-propagation
  bipartite matching over channel pairings with a bitmap leaf test
  `subsumes_unpermuted` = `A & ~B == 0`. **78 % of active time** after M2b.
- **Index**: `OutputSetIndex` — k-d tree cascade over truncated abstraction points
  (`DIMS` = 12–32 `u16`s), popcount-bucketed, one lock+index per `|set|`.
- **Memo**: `StateMap` — 32k lock-sharded `BTreeMap<[u8; 2^(k-3)], State>`, 17:1
  read:write, keys 16–64 B at the mass widths (k = 8, 9), never evicts (baseline).
- **Hardware**: Apple M4 (10 cores, 128-bit NEON; SME/AMX matrix unit), RTX 3060
  (Ampere, 12 GB), Ryzen 3600 (AVX2).

Honesty convention: "kernel gain" is speedup of `Subsume::search` alone; end-to-end
is bounded by Amdahl at 78 %: kernel×10 → **3.3× end-to-end**, kernel×∞ → **4.5×**,
unless the index lookup around it moves too.

---

## 1. Bit-level SIMD for containment/dominance testing

**What it is.** The database set-containment-join (SCJ) literature (PRETTI, PSJ,
Bouros et al.'s "Set Containment Join Revisited") converged on a two-phase design:
cheap superimposed *signatures* whose bitwise dominance (`sig(A) & ~sig(B) == 0`) is a
necessary condition, followed by exact verification only on survivors — precisely the
architecture the pipeline already has with abstraction points. On the verification
side, Lemire et al.'s SIMD set-intersection work and the Roaring/CRoaring codebases
show that bitmap AND/ANDNOT/containment kernels are memory-bandwidth-bound and
vectorize essentially to full SIMD width on AVX2 *and* NEON, with superlinear
branch-elimination bonuses. *Positional popcount* (Klarqvist/Lemire FastFlagStats;
Clausecker & Lemire 2024/25 for AVX2, AVX-512 **and ARM ASIMD/NEON**) computes
per-bit-position counts at >90 GiB/s (AVX-512) / ~2.5× less on AVX2, i.e. effectively
at memory bandwidth.

**Mapping to our kernel.**
- The leaf test `subsumes_unpermuted` and the per-pairing dominance comparisons in
  `filter_matching` (sorted `u16` abstraction vectors) are textbook SIMD: NEON
  `vbicq`+`vmaxvq` for 128-bit ANDNOT-is-zero, `vcleq_u16` for 8-lane dominance.
  **Precondition: internals §8.4's packed-`u64` conversion** — the dense `[bool]`
  bitmap currently wastes 8× the bandwidth SIMD would exploit; do that first.
- Perf-report §8 rec 2's per-Hamming-weight histogram invariant is computable *without*
  the positional-popcount machinery: precompute k+1 static weight-class masks over the
  2^k positions, then `hist[w] = popcount(bitmap & mask_w)` — ~40 NEON ops at k = 9.
  Positional popcount proper becomes relevant if signatures are *bit-sliced* (§3).
- Bit-slicing (transposing signatures, Startin's bit-sliced signatures writeup, classic
  signature-file literature) lets one query test 64–128 index candidates per vector op
  with vertical AND/CMP — a good fit for the flat ≤32-entry pre-tree buffers in
  `OutputSetIndex`.

**Expected gain.** 2–8× on the vectorizable parts (leaf test, filter_matching
compares, abstraction-range tests); the matching search's branchy control flow stays
scalar, so honest kernel gain **2–4×**, end-to-end **1.5–2.5×**, plus the 8× transient
memory cut from packing. This compounds with every later idea.

**Implementation cost.** Days–2 weeks; contained in `output_set.rs` /
`output_set/subsume.rs`; the packed conversion is mechanical (internals already calls
it "the highest ratio of benefit to risk in the whole file").

**Risk.** Low. Bit-identical semantics are checkable at n = 9/10 against the twelve
accepted certificates; zero certificate impact. One portability nit: M4 NEON is
128-bit only (no SVE), Ryzen 3600 gives 256-bit AVX2 — keep the kernel
width-generic.

Sources: [Set Containment Join Revisited (Bouros et al.)](https://arxiv.org/pdf/1603.05422) ·
[SIMD Compression and Intersection of Sorted Integers (Lemire & Boytsov)](http://boytsov.info/pubs/simdcompressionarxiv.pdf) ·
[CRoaring (AVX2/AVX-512/NEON)](https://github.com/RoaringBitmap/CRoaring) ·
[Faster Positional-Population Counts for AVX2, AVX-512, and ASIMD (Clausecker & Lemire)](https://arxiv.org/pdf/2412.16370) ·
[positional-popcount (Klarqvist)](https://github.com/mklarqvist/positional-popcount) ·
[Faster Population Counts Using AVX2 (Muła, Kurz, Lemire)](https://arxiv.org/pdf/1611.07612) ·
[5x Faster Set Intersections: SVE2, AVX-512, NEON (Vardanian)](https://ashvardanian.com/posts/simd-set-intersections-sve2-avx512/) ·
[Bit-Sliced Signatures and Bloom Filters (Startin)](https://richardstartin.github.io/posts/bit-sliced-signatures-and-bloom-filters)

---

## 2. GPU subgraph-isomorphism / bipartite-matching engines

**What it is.** GPU subgraph-matching engines fall into BFS-join systems (GSI's
Prealloc-Combine, ICDE'20; cuTS's trie-based joins, SC'21) that avoid backtracking to
keep warps coherent, and stack-based DFS systems (STMatch, SC'22) that replace
recursion with explicit per-warp stacks plus work-stealing. The most relevant recent
datapoint is **SIGMo (SC'25)**: *batched* subgraph isomorphism for molecular matching —
thousands of independent small pattern-match problems — using multi-level iterative
filtering on neighborhood signatures followed by a stack-based DFS join, all on GPU.
Measured, not marketing: SIGMo reaches **8.64×10⁷ matches/s on a V100S vs 2.33×10⁶
for VF3 (CPU) — 33.6×**, and beats the generic GPU engines by far more (**88× vs
cuTS, 1470× vs GSI**, which OOMs on >20-node queries) precisely because generic
engines are mistuned for batches of small problems. Classic GPU bipartite matching
(Deveci et al., Europar'13, Hopcroft-Karp-class) is humbler: **3.5–9× average** over
the best sequential CPU algorithm.

**Mapping to our kernel.** Our workload is SIGMo-shaped, not GSI-shaped: each unit is
a tiny matching search over ≤k channel pairings with bitwise leaf tests on 32–256 B
bitmaps, and there are millions of them. The realistic architecture is: batch the
(query, candidate) pairs that survive the k-d filters across many concurrent lookups,
ship arrays of packed bitmaps + abstraction prefixes to the 3060, run a stack-based
warp-per-problem DFS (one warp = one matching search; the 32-lane leaf test is a
coalesced ANDNOT-reduce over one 2^k-bit bitmap — 8 lanes × 32-bit words covers k = 8
exactly), return a bitmask of "subsumed" verdicts. This is exactly the compute-bound
kernel the programme earmarked for the 3060, and internals §8.1 already lists GPU
offload as the mitigation for the abstraction-cost risk.

**Expected gain.** Honest: **5–20× on the kernel** versus the desktop CPUs here, *if
and only if* batches of ≥10⁴ problems can be assembled — which requires the same
async batch-restructure of `improve` that out-of-core sharding (§8.2) needs anyway.
End-to-end is Amdahl-capped at ~3–4.5× unless candidate generation (index probe) also
moves. Realistic delivered: **2–4× end-to-end**, with the strategic benefit that the
same batching rewrite unlocks §8.2's out-of-core plan.

**Implementation cost.** High — weeks to months: CUDA (or SYCL, as SIGMo did, which
would also cover future AMD/Intel boxes) kernel + the coroutine restructure to make
subsumption queries asynchronous and batchable, + a determinism story (batch order
must not affect derived bounds, or must be logged).

**Risk.** High. (1) Amdahl ceiling if only the leaf verification moves; (2) the 12 GB
3060 sits in the Ryzen box, not the M4 — pipeline topology cost; (3) warp divergence
returns if the per-problem search depth varies wildly (SIGMo mitigates with
signature-based pre-filtering so most batched problems die shallow — our abstraction
filters play the same role); (4) certificate neutrality must be re-argued for
asynchronous verdict arrival (§3.6 invariants 2–4).

Sources: [SIGMo SC'25 (De Caro, Cordasco, Ficarelli, Cosenza)](https://cosenza.eu/papers/DeCaroSC25.pdf) ·
[SIGMo repo](https://github.com/antonio-decaro/SIGMo) ·
[GSI: GPU-friendly Subgraph Isomorphism](https://arxiv.org/abs/1906.03420) ·
[cuTS (SC'21)](https://dl.acm.org/doi/10.1145/3458817.3476214) ·
[STMatch (SC'22)](https://ieeexplore.ieee.org/document/10046078/) ·
[GPU Accelerated Maximum Cardinality Matching (Deveci et al.)](https://inria.hal.science/hal-00923449v1/document) ·
[Jupiter: multi-GPU subgraph matching (EuroSys'25)](https://dl.acm.org/doi/10.1145/3689031.3717491)

---

## 3. Probabilistic filters with safe one-sided error

**What it is.** Superimposed-coding signature files (the pre-inverted-index IR
literature) give a *by-construction* one-sided containment test: if A ⊆ B then
sig(A) ⊆ sig(B) bitwise, so `sig(A) & ~sig(B) != 0` proves non-containment with zero
false negatives; the tunable "false drop" rate is minimized at ~50 % bit density.
Modern membership filters (Bloom, xor, binary fuse — the latter reaching ε ≈ 2^-N at
barely over N bits/key, 2× faster than Bloom) sharpen the space/FPR trade for exact-key
membership, and Mitzenmacher's *sandwiched learned Bloom filter* shows how to wrap any
learned predictor so the no-false-negative guarantee survives. Theory says full subset
querying is fundamentally hard (Charikar–Indyk–Panigrahy, ICALP'02: exponential
space or ~linear scan in the worst case; partial-match cell-probe lower bounds), which
is *why* every practical system is filter + exact verify — there is no exact sublinear
free lunch to find.

**Mapping to our kernel.** The crucial constraint is permutation invariance: any
per-element hash signature breaks under channel relabeling, so generic minhash/LSH
containment sketches (LSH Ensemble etc.) do **not** apply directly — and they have
false negatives, which here would silently erode the 160× subsumption yield (not
soundness, but the entire point of M2). The correct move is the one the codebase half
made already: signatures must be **monotone functions of permutation-invariant
statistics**. The per-Hamming-weight histogram (perf-report §8 rec 2) is exactly such
a statistic: A ⊆ B under permutation ⇒ hist_A[w] ≤ hist_B[w] pointwise (permutations
preserve weight; complement acts as w ↦ k−w, matching the `LowerInvert` trick).
*Thermometer-code* each bucket (unary-encode the count into a few bits at chosen
thresholds) and concatenate: dominance of histograms becomes bitwise signature
containment — a 64–128-bit test that is one or two NEON ops, sits in front of
`subsumes_permuted`, and is provably necessary. This is an order-preserving sketch in
the signature-file sense, not a hash.

**Expected gain.** The abstraction filter already removes most candidates, so this
buys whatever fraction of *survivors* the weight histogram kills — it is a genuinely
independent invariant (per perf-report), so 30–70 % survivor reduction is plausible
but unmeasured. Kernel gain **1.3–3×**, end-to-end **1.2–2×**, at ~16 bytes/entry of
index overhead. FPR context from the literature: 128–256-bit tuned signatures on sets
of this size run ~1–10 % false-drop for membership-style loads; for dominance loads
the honest answer is "measure it" — instrument survivors-per-lookup before/after.

**Implementation cost.** Days. Compute histogram signature at insert (cheap masked
popcounts, §1), store alongside the abstraction point, test before the exact call.
Prove the monotonicity lemma (incl. complement and truncation interplay) in a short
note — it is a five-line proof but it gates soundness of the *pruning-power* claim.

**Risk.** Low for the thermometer-histogram design (exactness preserved: it only ever
skips exact tests that must fail). Medium if tempted by minhash/LSH: false negatives
there are silent memory-yield regressions. Avoid anything with two-sided error in the
eviction path.

Sources: [Signature files chapter (Faloutsos)](http://dns.uls.cl/~ej/daa_08/Algoritmos/books/book5/chap04.htm) ·
[Efficient Set Containment Queries for Skewed Distributions (EDBT'11)](https://openproceedings.org/2011/conf/edbt/TerrovitisBVSM11.pdf) ·
[Binary Fuse Filters (Graf & Lemire)](https://arxiv.org/pdf/2201.01174) ·
[A Model for Learned Bloom Filters, Optimizing by Sandwiching (Mitzenmacher)](https://arxiv.org/pdf/1901.00902) ·
[Charikar–Indyk–Panigrahy, subset query/partial match](https://web.mit.edu/~jfc/tmp/subset%20queries.pdf) ·
[LSH Ensemble: Internet-Scale Domain Search (Zhu et al.)](https://arxiv.org/pdf/1603.07410) ·
[Set Similarity Search Beyond MinHash (Christiani & Pagh)](https://arxiv.org/pdf/1612.07710)

---

## 4. Learned indexes for the spatial index

**What it is.** The Kraska et al. lineage (RMI 2018 → ALEX for updates → Flood/Tsunami
for multi-dimensional scans) replaces comparison search with a learned CDF model +
bounded local correction, and works because errors are correctable by exact local
search. For similarity rather than point queries the closest published work is LIMS
(2022): pivot-based transforms + per-cluster learned models giving *exact* range/kNN
in metric spaces, and "costs and benefits of learned indexing for dynamic
high-dimensional data" (2025) which is candid that dynamic high-dim learned indexes
often lose to tuned classical structures. **No published learned index answers
dominance/containment queries** — our query ("any stored point coordinate-wise ≤ q
with a better value") is not a metric ball, and none of RMI/ALEX/Flood/LIMS covers it.

**Mapping to our kernel/index.** Two correctness-safe roles exist: (a) *learned
traversal ordering* — a tiny model (even a per-bucket linear scorer on popcount +
first abstraction coordinates) ranks k-d subtrees/buckets by probability of containing
a subsumer, so the best-so-far accumulator (M2b change 2) terminates earlier; ordering
never changes what is found, only when. (b) A sandwiched learned filter in front of
the exact test with the backup-filter guarantee (§3). Role (a) is the honest option;
role (b) is dominated by the deterministic histogram signature which needs no training
and has provable zero false negatives.

**Expected gain.** Unmeasured anywhere in the literature for dominance loads;
plausible **1.2–2×** on index lookup (not the 78 % kernel), so end-to-end likely
< 1.3×. The index population also grows ~1,600× from n = 10 to n = 11 (perf-report
§7.1) — brutal distribution shift for any trained model mid-run.

**Implementation cost.** Medium-high, and it is research, not engineering: feature
design under permutation invariance, online retraining or shift-robust models,
plus instrumentation to prove ordering-only impact.

**Risk.** Medium-high. Contract §4 forbids ML-*decided* pruning; ordering is arguably
outside that, but the write-up burden is real, and any accidental coupling of model
output to a skip decision is a soundness bug. Rank last; revisit only if profiling
after §1+§3 shows index traversal order (not exact tests) dominating.

Sources: [The Case for Learned Index Structures (Kraska et al.)](https://arxiv.org/abs/1712.01208) ·
[LIMS: Learned Index for Exact Similarity Search in Metric Spaces](https://arxiv.org/pdf/2204.10028) ·
[Costs and Benefits of Learned Indexing for Dynamic High-Dimensional Data](https://arxiv.org/pdf/2507.05865) ·
[Tao: adaptive ANN search framework](https://arxiv.org/pdf/2110.00696) ·
[Sandwiched learned Bloom filters (Mitzenmacher)](https://arxiv.org/pdf/1803.01474)

---

## 5. Cache-oblivious and succinct layouts for billions of small bitsets

**What it is.** Van Emde Boas / cache-oblivious B-tree layouts (Bender–Demaine–
Farach-Colton) give O(log_B N) transfers for comparison search without knowing the
cache; measured wins are real but for *static or batch-updated sorted* data (COB-tree
7.5× over BerkeleyDB on insert-heavy loads; Eytzinger/vEB layouts beat pointer B-trees
for in-memory static search). Elias-Fano stores monotone sequences in n⌈log(m/n)⌉+2n
bits with O(1) random access — quasi-succinct, the backbone of modern inverted
indexes. Roaring bitmaps optimize *sparse sets over large universes* with 2^16-entry
containers. Minimal perfect hashing (PTHash) builds a collision-free static map at
~2–4 bits/key with one memory probe per lookup, constructible externally at
billion-key scale.

**Mapping to our memo/index.** Three distinct sub-problems:
- **Hot `StateMap` shards** (point lookups by exact 16–64 B key, 17:1 r:w): the
  BTreeMap costs ~4–5 cache misses/lookup at n = 11 shard populations (~10⁵/shard) and
  a *measured 1.9× space overhead* (internals §2.5). A Swiss-table/F14-style
  open-addressing map with SIMD tag probing and inline fixed-size keys does 1–2 misses
  and ~1.1–1.2× overhead. That is a **~2× lookup and ~1.6× memo-memory** win for a
  contained change in `states.rs` — note `dump_states` ordering must be re-sorted at
  dump time since BTreeMap iteration order currently comes for free.
- **Frozen/spilled shards** (the §8.2 out-of-core plan): per-shard generational
  freeze → PTHash MPH (2–4 bits/key) or an Eytzinger/vEB-laid-out sorted array of
  packed keys, fronted by a binary-fuse filter (ε = 2^-16 at ~18 bits/key) so cold
  misses cost zero I/O. Elias-Fano on the *sorted packed keys'* high bits helps less
  than usual because 32–64 B keys are high-entropy — gap compression saves maybe
  10–20 %, not the 2× it gives inverted indexes; the filter+MPH pair is the right tool.
- **Roaring is a mis-fit** for the sets themselves: our bitsets are dense, fixed-width
  2^k-bit blocks (the packed array is already optimal); Roaring's container machinery
  only adds overhead below universe sizes of ~4 K.

**Expected gain.** Memo lookup ~2×, memo RAM ~1.6× (i.e., Harder's 78 B/entry →
~50 B), and for the out-of-core future: filter-guarded spill turns the 4 KiB-per-miss
horror (internals §8.2 risk 1) into filter-probe-only for the ~94 % of gets that miss.
End-to-end today: modest (< 1.3×, the kernel dominates); strategic value for n ≥ 11
scale-out: high.

**Implementation cost.** Swiss-table swap: ~1 week incl. determinism audit.
Freeze+MPH+filter tier: part of the §8.2 campaign, not standalone.

**Risk.** Low-medium. Hash-order nondeterminism must not leak into anything the
contract's determinism rule (§5 rule 3) or dump format observes; eviction (M2's
evict mode) needs tombstone support that BTreeMap gave trivially.

Sources: [Cache-Oblivious B-Trees (Bender, Demaine, Farach-Colton)](https://erikdemaine.org/papers/CacheObliviousBTrees_SICOMP/paper.pdf) ·
[Cache-Oblivious Dynamic Search Trees (Kasheff)](https://people.csail.mit.edu/bradley/papers/Kasheff04.pdf) ·
[Optimal Hierarchical Layouts for Cache-Oblivious Search Trees](https://arxiv.org/pdf/1307.5899) ·
[Partitioned Elias-Fano Indexes (Ottaviano & Venturini)](https://dl.acm.org/doi/10.1145/2600428.2609615) ·
[PTHash: parallel/external MPH construction](https://arxiv.org/pdf/2106.02350) ·
[Roaring Bitmaps: Implementation of an Optimized Software Library](https://arxiv.org/pdf/1709.07821) ·
[Binary Fuse Filters](https://arxiv.org/pdf/2201.01174)

---

## Hardware notes

- **M4**: NEON is 128-bit; no SVE. The SME/AMX unit does INT8 outer-product GEMM at
  ~8 TOPS ([measured on M4 Pro](https://arxiv.org/pdf/2502.05317),
  [SME GEMM studies](https://arxiv.org/html/2512.21473)) but has no bitwise ops — it
  is *not* useful for the subsumption kernel; it could serve abstraction recomputation
  only if that were reformulated as small integer matmuls (it is popcount/sort-shaped;
  poor fit). Treat M4 as a 10-core NEON machine.
- **Ryzen 3600**: AVX2, 256-bit — the better *per-core* SIMD target; keep kernels
  width-generic (Rust `std::simd` or 128/256 dispatch).
- **RTX 3060**: 12 GB fits multi-GB candidate arenas; PCIe batch latency dictates
  ≥10⁴-problem batches; SYCL (per SIGMo) or CUDA both viable.

## Synthesis — ranked

| rank | technique | end-to-end gain (honest) | cost | risk |
|---|---|---|---|---|
| 1 | §1 packed-u64 + SIMD kernel (NEON/AVX2) | 1.5–2.5× + 8× transient mem | days–2 wks | low |
| 2 | §3 weight-histogram thermometer signature pre-filter | 1.2–2× (multiplies rank 1) | days | low |
| 3 | §5 Swiss-table memo shards | <1.3× time, 1.6× memo RAM | ~1 wk | low-med |
| 4 | §2 GPU batched matching (SIGMo architecture) | 2–4× (needs async batching rewrite) | wks–months | high |
| 5 | §4 learned traversal ordering | <1.3×, unproven anywhere | med-high | med-high |

Ranks 1+2 compound (cheaper test × fewer tests) and are prerequisites worth doing
*before* any GPU work: they change the batch-size and arithmetic-intensity math that
decides whether the 3060 offload clears its PCIe overhead, and both are certifiably
behavior-preserving with the existing n = 9/10 validation harness.
