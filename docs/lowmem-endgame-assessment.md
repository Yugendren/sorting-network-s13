# The Low-Memory Endgame — Can Ladder Levels 7–8 Be Computed Without Holding Them?

**Date:** 2026-08-18.
**Scope:** read-only reconnaissance plus new arithmetic and new differential
measurements over already-archived artifacts. Nothing in `src/`, `tools/`,
`.cache/third_party/` or any other `docs/` file was modified; no search was run;
no network was constructed. All new work is in `.build/v3-lowmem/`.
**Predecessors:** `docs/transforms-assessment.md` (the Universal Level Law),
`evidence/v3/limits/report.md` (the measured n=12/13 ladder),
`docs/sortnetopt-internals.md` (engine archaeology),
`docs/s13-shape-case-split.md` (the 3-class split).

---

## 0. Verdicts

| # | family | verdict | one line |
|---|---|---|---|
| 1 | certified recomputation / pebbling / IDA*-style bounded memo | **KILL** | the knob has no travel: **99.59 %** of the memo is created by the *final* bound iteration, so "hold level ℓ₀, recompute above" holds back 1/33…1/246 of the footprint; and Lengauer–Tarjan makes generic DAG recomputation doubly-exponential |
| 2 | meet-in-the-middle / bidirectional / backward reachability | **KILL** | the backward object is not computable — un-applying a comparator to a set `Y` has up to `2^{\|Y\|}` preimages; and the forward half is generate-and-prune, which is the method Harder's DP already beat |
| 3 | bisimulation / future-equivalence quotient | **PARK** (one cheap probe) | every certified coarsening in the literature (merge-and-shrink, label reduction) needs the explicit graph first; the only local certificate available is *mutual* subsumption, which the preorder already quotients. One 20-line probe bounds the residual headroom |
| 4 | cross-class / cross-job amortization | **PROMOTE — strongest item in this document** | **new measurement:** the level-4 memo tables of a full n=9 run and a full n=10 run agree **as sets of keys** to Jaccard **0.9936**, and **99.92 %** of shared keys carry the *identical* stored lower bound. The memo is a root-independent, n-independent oracle; the checkpoint format already stores exactly it |
| 5 | streaming / semi-external with provable passes | **PROMOTE — the only family that raises the memory ceiling** | **new machine-checked structure:** `(width, \|X\|)` is a topological quasi-order on the DP DAG, giving 1,185 measured shells at level 5 with the largest at **1.41 %** of the level ⇒ a hash-DDD/SDD external memo needs `O(1 %)` of the level in RAM, `O(sort(N))` I/O, and is bounded only by *disk capacity* |
| 6a | other memory-bounded exhaustive search (cube20, Korf's external BFS, Chinook, PEMM) | **KILL as a transplant; the architecture is kept in §7, and the indictment is of our *representation*** | cube20 was **not** a memory-for-time trade: 2.3 GB/worker, 35 CPU-years, a **2.2×10⁹× memory reduction at negative time cost**, because the RAM-sized coset bitmap is what unlocked a 256,000× batching win — the memory bound was chosen *first*. Its two levers (group quotient, solve-many-at-once) are already `canonicalize(true)` and the output-set DP. What separates us is **bytes per state: 0.125 (cube20), 0.25 (Korf/Chinook), vs 30–90 (ours)** — and every precedent gets there via a **bijective rank function** we provably cannot have (MPHF needs the complete keyset up front) |
| 6b | **Codish et al. "End Game" last-layer / co-saturation suffix theory** | **PROMOTE to the ranked queue (not to the endgame plan)** | the only family found anywhere that reduces **`N`**: last layers are `F_{n+1}−1` not `C(n,2)`-choose (82,000× at n=17), co-saturation another 30×, **1,440 co-saturated two-layer suffixes at n=13**, and a *measured* 6.5 → 1.5 CPU-years on the optimal-**size** `S(9)=25` proof. Harder uses none of it. It lives on the forward object, so it composes with the shape case split as a prefix/suffix pincer |
| — | **level 8 at n=13** | **OUT OF REACH — unconditionally, on this hardware** | the *pure touch time* (zero memory cost, zero re-expansion) is **59–124 M4-days at the optimistic/geometric multipliers** and **140 years** at the measured ceiling. Memory technique cannot help: throughput, not memory, is the first wall |
| — | **level 7 at n=13** | **out of reach on owned hardware; marginal on a $100 burst, and only conditionally** | 3.8–209 M4-days and 3.5–195 TB. It becomes a 3-day / 3.5 TB job **iff** the level-5→6 multiplier lands near the 33× floor — which is *unmeasured*. |
| — | **decisive action 1** | **measure level 6** | `n=11 --limit 35` (it is `D(11)`, so it terminates and self-checks). Cost 0.03–0.85 M4-days and 21–607 GB. It collapses a 4-order-of-magnitude bracket to a number, and every verdict above becomes quantitative |
| — | **decisive action 2** | **measure the ladder with subsumption ON** | every number in this document was measured with subsumption **off**. The compression factor grows 1.3 → 2.2 → 15.8 → **160×** over n=5,7,9,11 and extrapolates to 1,500–3,000× at n=13. If turning the index on shrinks the *per-level multipliers* (not just the stored population), levels 7–8 come back into scope. Nothing else has that leverage, because nothing else reduces `N` |

---

## 1. What is new in this document

Six results, all produced this session and all reproducible from artifacts already in the repository (§11):

1. **The memo is a root-independent, n-independent oracle — verified as sets,
   not counts.** (§6.1) The Universal Level Law was previously a statement about
   *census counts*. It is now checked at the level of the actual packed keys.
2. **`(width, |X|)` is a topological quasi-order on the DP DAG** — machine-checked
   by exhaustive BFS at n ≤ 5 and by random DP walks at n ≤ 10. (§7.1) With a measured
   4–7 % tie rate that is the design's one open risk.
3. **The measured shell histogram** of three real memo dumps (levels 3, 4, 5):
   299 / 456 / 1,185 shells, largest shell 2.62 % / 2.76 % / **1.41 %** — falling.
   (§7.2)
4. **The ceiling of every frontier/layered-memory scheme is 1.57–1.91×** (states)
   and 1.25–1.77× (bytes), computed from the width census. (§3.2)
5. **99.59 % of the memo is created by the final bound iteration** — the fact
   that kills checkpoint-and-recompute. (§3.1)
6. **The engine's throughput does not scale with cores**: 170,882 states/s on a
   10-core M4 at 99.98 % pool utilisation vs 141,059 states/s on Harder's
   24c/48t EPYC. (§2.1) This is what makes *time*, not memory, the first wall.

Plus one calibration that reframes the whole question (§8.1a): every exhaustive
computation in the literature that reached 10¹²–10¹⁹ states did so at **1 bit to
4 bytes per state**, via a bijective rank function. We are at **30–90 bytes** and
cannot have a rank function. That gap, not the partitioning scheme, is what
separates this programme from its precedents.

---

## 2. The three walls, and which one binds

### 2.1 Wall 1 — throughput (binds first at levels 7 and 8)

| anchor | states | wall | states/s |
|---|---|---|---|
| n=13 `--limit 42` (M4, 10 cores, 99.98 % pool util) | 50,922,864 | 299.3 s | **170,882** |
| n=12 `--limit 38` (same box) | 50,788,878 | 327.3 s | 155,794 |
| n=13 `--limit 43`, killed mid-iteration | ~89.7 M | ~550 s | ~163,000 |
| Harder full n=11, **24c/48t EPYC** | 2,462,890,689 | 4 h 51 m | **141,059** |

A 4.8× core count buys **nothing**. (Tier-2b already established why: the pool is
not descheduling-bound and already runs at 931–943 % of a 10-core box; the limit
is per-state work and memory bandwidth, and `packed_pvec()` recomputation on the
`StateMap` hot path — `internals` §5.) **Treat 1.5×10⁵ states/s as a hardware
constant.** Every level cost below is quoted in *M4-days* on that basis, and a
cloud burst should be assumed to buy well under one order of magnitude of it.

Consequently, the floor that no memory technique can cross:

| growth scenario | level 6 | level 7 | level 8 |
|---|---|---|---|
| OPTIMISTIC (5→6 consolidates, 8.4×) | 0.03 d | 7.1 d | **59.5 d** |
| GEOMETRIC (33.0×/level, the measured geometric mean) | 0.11 d | 3.8 d | **124 d** |
| ALTERNATING-ESCALATING (15× / 1000× / 30×) | 0.05 d | 51.7 d | **1,550 d** |
| PESSIMISTIC (245.9×/level, the measured ceiling) | 0.85 d | 209 d | **51,300 d** |

These are *pure touch times*: every distinct state at that level visited exactly
once, zero memory cost, zero re-expansion, perfect parallelism. **Level 8 is
59 M4-days at its most optimistic and 140 years at its worst.** No scheme in this
document changes that number, because none of them reduces `N`.

### 2.2 Wall 2 — resident memory

Measured at level 5, n=13: 50,922,864 states, 1,509,939,963 packed key bytes
(**29.65 B/state**), 3.35 GB RSS (**65.79 B/state**, B-tree overhead 2.22×).

The bytes/state figure *rises* with level, because the census is a travelling
wave in channel width (`transforms-assessment` §2.5). Measured peak width by
level: w5, w6, w7, w7, w8 for ℓ = 1…5 — a drift of 0.5–0.75 widths per level. At
0.5 widths/level the projection is 44.5 B/state at level 6, 59.3 at level 7,
89.0 at level 8. **The constant-29.65-B/state extrapolation in
`evidence/v3/limits/report.md` therefore understates levels 7–8 by 2–3×.**

### 2.3 Wall 3 — disk

**Correction to the brief, measured on the machine:** the M4 has **~24 GiB free**,
not ~200 GB. `df`: a single 228 GiB internal volume, `/System/Volumes/Data`
178 GiB used, 24 GiB available; `diskutil info /` reports 25.3 GB container free
space; no external volume is mounted. Of the used space, `.build` is **22 GB**
and `.cache` **7.4 GB** — so ~30 GB is recoverable by archiving completed
campaign artifacts, which would roughly double the M4's usable scratch and is the
cheapest capacity action available anywhere in this document. The 324 GB figure
for the server is taken as given and not independently checked here.

| store | states at 33.7 B/rec (L5) | at 48.5 B/rec (L6) | at 63.3 B/rec (L7) |
|---|---|---|---|
| M4 free disk, 26 GiB | 7.5e8 | 5.2e8 | 4.0e8 |
| server free disk, 324 GiB | 9.3e9 | 6.5e9 | 4.9e9 |
| 4 TB NVMe (retail ~$200 — *outside the $100 budget*) | 1.07e11 | 7.4e10 | 5.7e10 |
| AWS `is4gen.8xlarge` local NVMe, 30 TB | 8.0e11 | 5.6e11 | 4.3e11 |

**On-disk records are sorted runs with no B-tree overhead** — packed key + the
4-byte `State`, which is exactly what `dump_states` already writes plus the
bound. I/O is *not* a wall: a two-pass external sort of even 420 GB is 0.09–0.23 h
of pure bandwidth against 0.85 M4-days of compute (§7.3).

### 2.4 The load-bearing assumption behind all of it, stated plainly

**Every level cost in this document is measured with subsumption OFF.** The
33–246× multipliers, the 50.9 M states at level 5, the 1.5×10⁵ states/s — all of
it. The subsumption compression factor is *growing fast with `n`*:

| n | total states | non-subsumed | factor |
|---|---|---|---|
| 5 | 34 | 26 | 1.3× |
| 7 | 550 | 247 | 2.2× |
| 9 | 206,279 | 13,034 | **15.8×** |
| 11 | 2,462,890,689 | 15,432,816 | **160×** |

(Harder, arXiv:2012.04400, Table 1.) Extrapolating the sequence 1.3 / 2.2 / 15.8
/ 160 puts n=13 somewhere in the **1,500–3,000×** range. If even a fraction of
that were realised *on-line* — i.e. if subsumed states were never expanded rather
than merely never stored — the per-level multipliers themselves would shrink and
every number in §2.1–2.3 would move by orders of magnitude.

The measured evidence does **not** currently support that hope:

| configuration | memory reduction | wall cost | source |
|---|---|---|---|
| n=10, M2a prototype | 2.73× resident | 13.2× | `evidence/v3/m2a` |
| n=10, M2b `DIMS=16` | 2.72× resident | **2.35×** | `evidence/v3/m2b` |
| n=10, M2b `DIMS=12` | 2.91× resident | 3.29× | `evidence/v3/m2b` |
| n=12, `evict`/DIMS=24/widths 8,9 | ≥9× | ≥5.5× | `evidence/v3/limits` |

i.e. an exchange rate `time ∝ memory_reduction^α` with **α ≈ 0.78–1.11** at the
measured operating points, and *work going up, not down*. And M2a §8.5 records
that on-line subsumption realises only **37–52 %** of the whole-run ceiling at
n=9/10.

> **This is the second decisive measurement, and it is cheap: run the n=11 ladder
> to level 5 (and, if it holds, level 6) with the index ON, and compare the
> per-level multipliers against the subsumption-off ladder.** If the multipliers
> fall from 33–246× to, say, 5–20×, the entire endgame changes character and
> levels 7–8 come back into scope. If they do not move, §10's table stands.
> Nothing else in this document has that leverage, because nothing else in this
> document reduces `N`.

---

## 3. Family 1 — certified recomputation / time–memory tradeoffs: **KILL**

Three independent reasons, in decreasing order of how much they should be
trusted.

### 3.1 Reason 1 (measured, decisive): the knob has no travel

The ladder's levels are **nested**, not a partition: `StateMap` has no eviction
path at all (`internals` §2.5), so `M_1 ⊆ M_2 ⊆ … ⊆ M_ℓ`. Measured per-iteration
new-state fractions from `.build/v3-limits/probe13-off-L42/instrument.json`:

| iteration | bounds | states | new_states | new % |
|---|---|---|---|---|
| 12 | [39,45] | 545 | 502 | 92.1 |
| 13 | [40,45] | 25,750 | 25,205 | 97.9 |
| 14 | [41,45] | 208,375 | 182,625 | 87.6 |
| **15** | **[42,45]** | **50,922,864** | **50,714,489** | **99.59** |

"Store only levels ≤ ℓ₀ and recompute above" therefore withholds
**1/33 to 1/246** of the footprint. The scheme the question asks for — hold
level 5 (3.35 GB) while computing level 8 — is not a tradeoff at all: level 5 is
0.0009 % of level 8's footprint, so this is simply "compute level 8 with no
memo".

This also **kills REVOLVE / binomial checkpointing** (Griewank–Walther,
*Algorithm 799*, ACM TOMS 26(1):19–45, 2000, whose optimality theorem
`p(m,s) = t·m − C(s+t, t−1)` is genuinely excellent: 10¹² steps in 8.6× time
with 100 checkpoints). REVOLVE requires a **chain of comparably-sized states**.
The ladder is a **monotone accumulator**. There is no state to forget and
recompute; the thing you would forget is the thing you are building.

### 3.2 Reason 2 (measured, decisive): the layered-memory ceiling is 1.9×

The literature's one genuinely free lunch is layering: Zhou & Hansen's *locality*
theorem (*Breadth-First Heuristic Search*, ICAPS-04 / AIJ 170:385–408, 2006,
Thm 1) says retaining `locality` previous layers costs **zero** recomputation;
Korf's frontier search (JACM 52(5):715–748, 2005) reduces memory from |space| to
|widest layer| — measured up to 46× on his domains. The whole family's ceiling is
`total / widest retained slice`.

The only natural layering of this DAG is **channel width** (comparator edges stay
at `w`, prune edges go to `w−1`), so processing width `w` needs all of `w−1`
resident as well. From the census:

| n | level | total | widest 1 width | widest 2 adjacent | reduction (1w) | reduction (2w) |
|---|---|---|---|---|---|---|
| 13 | 3 | 25,750 | 15,259 | 23,247 | 1.69× | 1.11× |
| 13 | 4 | 208,375 | 132,441 | 168,471 | 1.57× | 1.24× |
| 13 | 5 | 50,922,864 | 26,647,959 | 44,201,202 | **1.91×** | **1.15×** |

In bytes at level 5: total 1.510 GB, widest width (w8) 0.853 GB → **1.77×**;
widest 2 adjacent → 1.25×.

**Independent corroboration from a different state-space representation.** Codish,
Cruz-Filipe, Frank & Schneider-Kamp (*Sorting nine inputs requires twenty-five
comparisons*, JCSS 82(3):551–563, 2016 / arXiv:1405.5754) publish the full
per-layer profile `|R^n_k|` of the *forward* generate-and-prune space:

| n | peak layer | peak / total | widest **two adjacent** layers / total |
|---|---|---|---|
| 7 | k=9 of 16 (56 % of depth) | 678 / 2,736 = 24.8 % | 45.4 % ⇒ **2.20×** |
| 8 | k=11 of 19 (58 % of depth) | 16,095 / 59,284 = 27.1 % | 46.8 % ⇒ **2.14×** |

So a layered scheme holding a two-layer window keeps ~47 % of everything, for a
**2.1–2.2× ceiling** — a completely different object (forward networks, not
backward output sets) landing on the same number as our 1.15–1.91×. Note also
that their peak sits at 56–58 % of depth, i.e. **past** the middle, which is the
same statement as our memo mass sitting at widths n−3, n−2.

**The mass sits in two adjacent layers, in both representations.** Frontier
search, sparse-memory search, DCFA*, BFIDA* and layer-dropping all reduce memory
by exactly this ratio. 2× against a 10⁵ deficit is not a technique, it is a
rounding error.

### 3.3 Reason 3 (theory): generic DAG recomputation is doubly exponential

Lengauer & Tarjan, *Asymptotically tight bounds on time-space trade-offs in a
pebble game*, JACM 29:1087–1130, 1982:

- **Thm 6.2 (upper).** Every DAG of `n` vertices, in-degree ≤ ℓ, pebbles in space
  `s` with time `≤ s·2^{2^{O(n/s)}}`.
- **Thm 11.2 (lower).** There are explicit in-degree-2 DAGs where *any*
  black-white pebbling in space `s` needs time `≥ s·2^{2^{εn/s}}`.

At the memory-reduction ratios this programme needs (10²–10⁵) the bound is
`2^{2^{100}}`-shaped. The theorem is tight, so "be cleverer about the DAG" is
not available. What *is* available is exploiting structure — layering (§3.2, only
1.9× here) or the shell decomposition (§7, which is the one that works).

Best exposition with full proofs: Nordström, *New Wine into Old Wineskins: A
Survey of Some Pebbling Classics*
(https://jakobnordstrom.se/docs/publications/PebblingSurveyTMP.pdf).

### 3.4 The sharing factor: why "no memo" is not on the table either

From the same instrument file, at level 5, n=13:

| quantity | value | per distinct state |
|---|---|---|
| distinct states (DAG nodes) | 50,922,864 | 1 |
| successor edges | 183,992,018 | 3.61 |
| Huffman-pruning edges | 523,863,862 | 10.29 |
| forced-pruning edges | 1,107,641 | 0.02 |
| **total edges** | **708,963,521** | **13.92** |
| `StateMap::get` calls | 915,105,029 | 17.97 |
| `improve()` calls | 73,430,460 | 1.44 |

Average in-degree **13.92**. Unfolding this DAG into a tree — which is what any
memo-free recursion does — costs `13.9^depth`: 2.7×10¹¹ at depth 10, 10⁴⁸ at
depth 42. Note also `lock_contended = 1,474` against 73.4 M acquisitions: the
DAG-forming dedup is essentially uncontended, i.e. the sharing is *already*
being harvested optimally.

### 3.5 IDA*-style bounded memoisation, specifically

The IDA* overhead theorem (`b/(b−1)` over iterations) is genuine but conditional
on exponential per-iteration growth, and applies to **trees**. On graphs the
picture inverts: Martelli (1977) gives `Ω(2^{S₊})` worst-case re-expansion for
A* with an inconsistent heuristic; Sturtevant & Helmert (*Exponential-Binary
State-Space Search*, IJCAI-19 / arXiv:1906.02912) show `Θ(N²)` for tree-search
IDA* and give the sharpest known fix at `O(S₊·log C*)`. Crucially:

- **There is no theorem of the form "a transposition table of size M reduces
  re-expansions by f(M)".** The literature sweep found none. What exists is
  measurement: Reinefeld & Marsland (IEEE PAMI 1994) report 35–73 % node
  reduction from a TT — in domains with *mild* transposition (15-puzzle,
  TSP). Zhou & Hansen (ICAPS-04) report the opposite regime on planning
  benchmarks: "IDA* performs much worse than A* due to excessive node
  re-generations."
- Our `m/n ≈ 14–18` puts us firmly in the second regime.
- MREC, MA*, SMA*, RBFS all have *correctness* theorems and no
  memory-vs-re-expansion bound.

**Verdict 1: KILL.** Not because the schemes are wrong, but because the object
they act on does not have the shape they need. The one usable idea in this family
— *layer-structured* storage — is quantified in §3.2 at 1.9× and folded into
§7 where it belongs (a much finer layering does much better).

---

## 4. Family 2 — meet-in-the-middle / bidirectional: **KILL**

### 4.1 The correct formulation

Let `R_m` = canonical output sets reachable from the full 13-cube by exactly `m`
non-redundant comparators, and `B_k = { X : bound(X) ≤ k }` = sets sortable in
`k` comparators. Then for **any single** `m`,

```
S(13) ≥ 45   ⟺   R_m ∩ B_{44−m} = ∅
```

because a 44-comparator network splits as a length-`m` prefix and a
length-`(44−m)` suffix. This is a genuine meet-in-the-middle and it is exactly
the Codish–Cruz-Filipe–Frank–Schneider-Kamp *generate-and-prune* schema, and the
Track-B prefix-decomposition schema.

### 4.2 Why the backward half is not computable

`B_k` must be generated by *un*-applying comparators from the sorted set. The
preimage of a set `Y` under `apply_comparator(i,j)` is
`{ X : c(X) = Y }`. Every vector `v ∈ Y` that is *in order* on `(i,j)` may have
arisen from itself, from its swap, or from both; only the strictly-ordered
vectors are forced. So a single set `Y` has up to `2^{|Y_{ordered}|}` preimages,
with `|Y| ≤ 8192`. **The backward branching factor is exponential in the state
size, not in the channel count.** There is no retrograde analysis here — this is
categorically unlike chess/checkers tablebases, where the preimage of a position
under a move is a bounded set.

This is the precise reason endgame-tablebase technique does not transplant, and
it should be recorded as such: the programme's DP is a *forward* fixpoint with a
*backward-in-value* recursion, not a backward-in-state one.

### 4.3 Why the forward half is the method that was already beaten

`R_m` modulo subsumption *is* generate-and-prune. Harder's DP (arXiv:2012.04400)
supplanted it at n=11 precisely because `|R_m|` at the middle explodes and the
subsumption-minimal antichain of the middle layer is the very quantity this
programme is bounding at 10¹²–10¹⁵ (`transforms-assessment` §3.1: the measured
non-subsumed frontier at n=11 is already 10^7.19). Meet-in-the-middle asks us to
materialise both halves of exactly the object we cannot materialise once.

There is no `m` where both sides are small: the two curves cross at the widest
point by construction.

### 4.4 What survives (recorded, not promoted)

- The **prefix decomposition** is the `m` small end of this identity, and is
  already the programme's plan; it is a *work* decomposition, not a memory one
  (§6.3).
- Schroeppel–Shamir (time `T`, space `T^{1/2}`; SICOMP 10(3), 1981, and the
  first improvement in 40 years, Nederlof & Węgrzycki STOC 2021,
  arXiv:2010.08576) requires the instance to split into **four independently
  enumerable parts producible in sorted order**. A comparator network is a
  sequence whose state depends on every prefix; there is no such split. It does
  not transfer.
- **Hirschberg's linear-space LCS (CACM 18(6), 1975)** *is* the transferable
  meet-in-the-middle-for-space idea, generalised by Korf et al.'s frontier
  search (JACM 52(5), 2005) and Zhou–Hansen's layered duplicate detection
  (AIJ 170, 2006). Its reduction is `total / widest window` — which §3.2 already
  measures at 1.9–2.2×.

### 4.5 The bidirectional-search theory, and what it does and does not promise

Worth recording precisely because the modern theory is sharp and its answer is
unambiguous:

- **No theorem in this literature bounds peak memory.** Eckerle et al.'s
  must-expand-pair conditions (ICAPS-17), Chen et al.'s vertex-cover lower bound
  and NBS's `2·VC` optimality (IJCAI-17), and Shaham et al.'s exact minimal set
  (SoCS-18) are all statements about **node expansions**.
- The *proven achievable* saving is a small constant. Sturtevant et al.
  (*Predicting the Effectiveness of Bidirectional Heuristic Search*, ICAPS-20)
  compute the theoretically optimal bidirectional gain: 12-Pancake with GAP\2
  **2.28×**, Rubik's Cube with 7edges **2.30×** — and with a *stronger* heuristic
  (GAP\3-MAX(4), 6edges-MAX(6)) the same measurements give **1.02× and 1.00×**.
  On the 15-puzzle with Manhattan distance, NBS is 1.47–1.53× **worse** than the
  best unidirectional search.
- Barker & Korf (AAAI-15) state the general position: any front-to-end
  bidirectional heuristic search will likely be dominated by unidirectional
  heuristic search or by bidirectional *brute-force* search.
- Our Huffman/van Voorhis bound is a **strong** admissible heuristic — the column
  in which every measured bidirectional gain collapses to 1.0×.
- MM's own external-memory realisation (PEMM, AIJ 252:232–266, §7.3) solved
  Rubik's superflip at depth 20 using **5.0 TB of disk** and 59,743 s. That is
  the honest shape of the trade: bidirectionality converted an `O(depth)`-memory
  algorithm into a 5 TB one to buy a 79× expansion reduction. Against a baseline
  that already stores everything, it does not shrink storage — it stores *two*
  closed sets.
- MM's paper also states our exact worry in general form: *"Rubik's Cube has
  D = 20 and the number of states at distance d only begins to decrease when
  d = 19."* The middle layer is not thin in spaces like ours.

**What is worth stealing from this literature anyway** is PEMM's *architecture*,
not its bidirectionality: states unsorted on disk, RAM holding only per-bucket
metadata, buckets keyed by `(priority, g, direction, low bits of hash)`,
hash-based delayed duplicate detection, delayed solution detection. That is the
§7 design, and it is why §7 is a PROMOTE.

**Verdict 2: KILL**, with the preimage-cardinality argument (§4.2) as the reason
to record and the ICAPS-20 collapse-under-a-strong-heuristic table as the
corroboration.

---

## 5. Family 3 — bisimulation / future-equivalence quotient: **PARK**

### 5.1 What would have to be true

Two states `A ≠ B` may be merged if they have the same optimal completion cost
**and** the same effect on the bound recursion. The deployed relation is the
subsumption preorder `R = { (A,B) : ∃σ ∈ S_13 × C_2, σ(A) ⊆ B }`, whose induced
equivalence (mutual subsumption) is already quotiented by canonicalisation plus
`prune`. A *coarser* certified equivalence must therefore be one that is not
implied by containment in either direction.

### 5.2 What the literature offers, and why it does not transfer

- **Merge-and-shrink with bisimulation-based shrinking** (Helmert, Haslum,
  Hoffmann, Nissim, JACM 61(3):16, 2014; Nissim–Hoffmann–Helmert, IJCAI-11) is
  the reference certified coarsening, and it *does* avoid building the full
  system — but only by exploiting a **factored** representation (atomic variable
  projections, merged pairwise, shrunk under a size limit `N`). We have no
  factoring of `X ⊆ {0,1}^n` into variables. And the paper's own verdict on the
  underlying object is blunt: *"in practical examples there rarely exist compact
  bisimulations… the size of bisimulations in Gripper is exponential in the
  number of objects."* Coverage tops out at 802 of 1,271 IPC tasks *with no size
  bound at all*. Paige–Tarjan (`O(m log n)`) and Henzinger–Henzinger–Kopke
  (coarsest simulation) both need the explicit graph.
- **Simulation-based dominance pruning** (Torralba & Hoffmann, IJCAI-15) is the
  closest analogue to subsumption — a dominance relation is exactly
  `s ⪯ t ⟹ h*(t) ≤ h*(s)`, and Harder's `X ⋤ Y ⟹ s(X) ≤ s(Y)` is an instance.
  Their measured reduction factors (evaluated states vs A*) run from 1× to
  **53,968×** (Gripper) — but the decisive column is the comparison of *blind*
  versus *LM-cut* baselines: with a strong admissible heuristic the same table
  collapses (PipesTank 33.4× → 1.8×, Airport 1.2× → 1×), and their §8 says so
  outright: *"the extent of the reduction is dramatically diminished."*
  We are in the strong-heuristic column.
  **What is worth stealing is their engineering, not their theory**: a BDD per
  `g`-value holding every state dominated by an expanded node, checked at
  *generation* time against the *closed* list only. That is precisely the
  on-line subsumption Harder reports never getting to work, in a shape designed
  around exactly our tradeoff (low check cost, high maintenance cost).
- **Symmetry reduction** (Emerson–Sistla; Clarke–Emerson–Jha–Sistla, CAV 1998) is
  capped at `|G|`, which here is `13!·2 = 1.25×10^10`, and is **already
  harvested** by `canonicalize(true)`. The measured gap is instructive: CAV-98
  reports BDD-size reductions of 12.7–49.5× against groups of size `10!`–`12!` —
  four to five orders below the ceiling, because representative selection, not
  the group, binds.

No technique in this literature produces a *local* certificate — a rule for
deciding `A ≡ B` from `A` and `B` alone, without the graph. On-the-fly
bisimulation checkers exist (Fernandez–Mounier CONCUR'91; the OPEN/CÆSAR
framework) but they explore the product graph on demand, worst case in full.

### 5.3 The exact-equality certificates we already have, ranked

Sound sufficient conditions for `s(X) = s(Y)`, cheapest first:

1. **Mutual subsumption** — `X ⋤ Y` and `Y ⋤ X`. Certificate: two permutations.
   Already implied by deployed machinery.
2. **Similarity** (permutation + complement; Harder Lemmas 4–5, Cor. 6).
   Certificate: one `σ ∈ S_n` and one bit. This is `canonicalize(true)`.
3. **Unique prunable channel** (Harder Lemma 53): if exactly one channel is
   prunable then `s(X) = s(X/i)` — an *exact equality across channel counts*,
   checkable in `O(|X|·n)`. This is `search.rs:167-206` (step 3 of `improve`),
   and it is the only rule in the whole apparatus that reduces the dimension
   while preserving the value exactly. It is also, per §6.2, why 99.8 % of the
   memo lives below the top width.

There is no fourth entry. A coarser certified relation would have to be a
two-sided cost-simulation, and obtaining a coarsest one is the intractable part.

### 5.4 The one honest measurement, and the cheap probe that would bound it

The measured decomposition at n=11 (`internals` §8.0) is:

```
2,462,890,689 explored  --÷160-->  15,432,816 non-subsumed  --÷1.22-->  12,659,079 certificate steps
```

so 99.4 % of the *identified* waste is subsumption redundancy and only 1.22×
remains between the subsumption-minimal antichain and reachability. **But that
1.22× is not a bound on the coarser-equivalence headroom** — a coarser relation
would merge *within* the 15.4 M antichain, and nothing in the repository bounds
that. Claiming otherwise would be dishonest.

**The 20-line probe that would bound it** (proposed, not run): on an existing
level-4 or level-5 dump, group the stored states by
`(width, bound, ABS)` where `ABS` is the rank-2 per-channel abstraction that
`filters.py` already computes, and count classes vs members. States sharing an
`ABS` vector and a bound are the *candidate* merge classes; the ratio
`states / classes` is a hard upper bound on what any abstraction-expressible
equivalence can deliver. `transforms-assessment` §4.3 already reports that `ABS`
makes only 7 false accepts in 3,594 rejectable pairs at n=7 — which suggests the
ratio will be close to 1, i.e. **near-zero headroom** — but the population there
was synthetic and small-`n`, and the honest answer is that it has not been
measured on a real dump.

**Verdict 3: PARK.** The probe costs an afternoon and would either close the
family or reopen it with a number. Do not spend engineering on it before the
level-6 measurement.

---

## 6. Family 4 — cross-class / cross-job amortization: **PROMOTE**

This is the strongest item in the document, and the reason is a new measurement.

### 6.1 New measurement: the memo is a root-independent, n-independent oracle

`State.bounds` is *by definition* a property of the output set alone — "a closed
interval on the minimum number of comparators required to sort every vector in
the set" (`internals` §1.2). It does not depend on the root, on the prefix, on
the class, or on `n`. That is a definition, not a conjecture. What was not known
is whether two independent runs actually *populate the same table*.

Compared, as sets of `(width, packed key)` pairs, the full n=9 run
(`.build/v3-m0b/runs/baseline-n9-a`, result 25 = level 4) against the full n=10
run (`baseline-n10-a`, result 29 = level 4):

| width | \|A\| (n=9) | \|B\| (n=10) | \|A∩B\| | \|A\B\| | \|B\A\| |
|---|---|---|---|---|---|
| 3 | 5 | 5 | 5 | 0 | 0 |
| 4 | 57 | 57 | 57 | 0 | 0 |
| 5 | 2,141 | 2,141 | 2,141 | 0 | 0 |
| 6 | 36,061 | 36,005 | 35,943 | 118 | 62 |
| 7 | 132,585 | 132,399 | 132,088 | 497 | 311 |
| 8 | 34,059 | 33,894 | 33,802 | 257 | 92 |
| 9 | 3,741 | 3,741 | 3,741 | 0 | 0 |
| 10 | 0 | 1 | 0 | 0 | 1 |
| **total** | **208,649** | **208,243** | **207,777** | 872 | 466 |

**Jaccard = 0.9936.** Widths 3, 4, 5 and 9 are *bit-identical sets*. The residual
0.2–0.8 % at widths 6–8 is the same nondeterministic-search-order spread that
makes repeated runs of the same binary differ by a few hundred states.

And on the shared keys, the *values* agree:

```
shared (width,key) pairs      : 207,777
identical stored lower bound  : 207,603   (99.9163 %)
differences (B − A) histogram : {−1: 82, +1: 65, −3: 5, −2: 4, +4: 4, …}  (174 total)
```

The 174 disagreements are all **weakenings, not contradictions**: a run stops
improving a node once the root's race is settled, so a node can carry a weaker
(still sound) bound in one run. Both values are valid lower bounds on the same
quantity, so the merge rule is simply

> `lower := max(lower_A, lower_B)`, `upper := min(upper_A, upper_B)`

which is sound and monotone, and is exactly the invariant `improve` already
requires (`internals` §3.6, invariants 1–2).

### 6.2 What this buys, and how much of the mass is class-private

Recall the width census at level 5, n=13, and where the class constraint lives.
The 3-class split (`s13-shape-case-split` §7.3) is a constraint on the *forward*
object — the width-13 network prefix's max-path geometry — and cannot be pushed
into the backward set-DP at all. So a class can only distinguish states at the
widths where a width-13 root's identity is still visible:

| level | total | width ≥ 9 | width ≥ 10 | width ≥ 11 |
|---|---|---|---|---|
| 3 | 25,750 | 0.505 % | 0.0155 % | 0.0117 % |
| 4 | 208,375 | 1.797 % | 0.0019 % | 0.0014 % |
| 5 | 50,922,864 | 11.13 % | **0.157 %** | 0.0028 % |

At level 5, **99.84 % of the states — and 99.31 % of the bytes — sit at width
≤ 9**, where they are provably shared by every class, every prefix and every `n`.
Only 80,160 states have width ≥ 10, and only 1,446 have width ≥ 11.

**Caveat, stated plainly.** The width wave advances. Projecting the level-5 width
profile forward at 0.5–1.0 widths per level, the width-≥10 share rises to ~11 %
at level 6 and — at the aggressive 1-width/level model — 63 % at level 7 and
98 % at level 8. So the *shared fraction shrinks exactly where we need it*. At
level 6 the sharing is still overwhelming; at level 7 it is a coin flip; at level
8 it is gone. This is another reason level 6 is the measurement that decides
everything.

### 6.3 The concrete scheme

> **The shared bound oracle.** Maintain one persistent, append-mostly table
> `T : (width, canonical packed set) → [lower, upper]`, shared by every
> class campaign, every prefix job, and every width `n`. Every job seeds its
> `StateMap` from `T` and contributes back. Merge by `max`/`min`.

Engineering, in order of size:

1. **Tier-2b checkpoints already are this table.** `checkpoint.rs` writes the
   globally-quiesced `StateMap` with a header hash, identity hash and payload
   hash; shard assignment is recomputed from the packed key on load, so a
   checkpoint is already portable across machines and `num_cpus`
   (`evidence/v3/tier2b/report.md`). Cost: 372 ms stall / 62.8 MB at 1.98 M
   states, +0.06 % of runtime at the 600 s default interval.
2. **The one blocking change: cross-width import.** The current resume path
   *correctly refuses* a cross-width checkpoint ("cross-width checkpoint
   correctly refused", limits report). What is needed is a distinct, read-only
   **seed-import** path that accepts a foreign table, imports only `bounds`
   (never `huffman_bounds`, which is an internal headroom memo), and merges by
   `max`/`min`. §6.1 is the soundness evidence; the argument is one paragraph
   (bounds are a property of the set).
3. **The certificate obligation this creates, which must be paid anyway.**
   Imported bounds have no in-run justification, so `GenProof::prove_all` would
   strand them (`internals` §3.6 invariant 4 — "almost certainly what Harder
   meant by on-line subsumption interacting badly with his bound-derivation
   order"). The fix is to record justifications at derivation time and compose
   per-job certificates. **This is required regardless**: step ids are `u32`
   (`proof.rs:174,191`), capping a certificate at 4.29×10⁹ steps against an
   n=13 estimate of ~1.5×10¹¹ — 35× beyond what the format can express
   (`internals` §6.3). Certificate composition is on the critical path with or
   without this item; the oracle just makes it *also* the enabler.

**Verdict 4: PROMOTE.** It is the cheapest large win available, it is validated
by a direct measurement rather than by an argument, and its prerequisite
(certificate composition) is already mandatory.

---

## 7. Family 5 — streaming / semi-external with provable passes: **PROMOTE**

This is the only family that raises the *memory* ceiling, and the reason it works
is a structural fact that had not been checked.

### 7.1 New structural result: `(width, |X|)` is a topological quasi-order

The DP DAG has exactly two edge kinds (`internals` §1.2): apply a non-redundant
comparator (`w → w`), and prune an extremal channel (`w → w−1`).
`.build/v3-lowmem/topo.py` machine-checks what those do to `|X|`:

| test | population | comparator edges | `|Y| > |X|` | `|Y| = |X|` |
|---|---|---|---|---|
| exhaustive BFS, n=3 | 7 sets | 11 | 0 | 0 |
| exhaustive BFS, n=4 | 44 sets | 142 | 0 | 0 |
| exhaustive BFS, n=5 | 581 sets | 3,160 | 0 | 0 |
| random networks, n=6 | — | 3,535 | 0 | 0 |
| random networks, n=7 | — | 4,377 | 0 | 0 |
| **mixed DP walks** (comparators applied to already-pruned sets), n₀=7 | 300 walks | 1,696 | 0 | **72 (4.2 %)** |
| **mixed DP walks**, n₀=8 | 300 walks | 2,106 | 0 | **105 (5.0 %)** |
| **mixed DP walks**, n₀=9 | 300 walks | 2,407 | 0 | **157 (6.5 %)** |

Prune edges: 50,185 tested, `|pruned| ≥ |X|` in **0** cases, and the width always
drops by one.

So:

> **Shell Lemma (measured; proof open).** Every DP edge from `X` goes to a state
> `Y` with `width(Y) < width(X)`, or `width(Y) = width(X)` and `|Y| ≤ |X|`.
> `|Y| < |X|` strictly whenever `X` is an output set of the full cube; ties occur
> only after channel pruning, at a measured rate of **4–7 %** of comparator
> edges.

Two consequences.

- **The `(width, |X|)` pair is a valid delayed-duplicate-detection bucketing.**
  Process shells in descending `(width, |X|)`; a generated successor always lands
  in a bucket that has not yet been closed, so duplicates within a bucket can be
  eliminated by one sorted merge when the bucket is opened. This is Korf's
  hash-based DDD (*Best-First Frontier Search with Delayed Duplicate Detection*,
  AAAI-04; *Linear-Time Disk-Based Implicit Graph Search*, JACM 55(6), 2008) with
  a *provably correct* bucket function rather than a hash.
- **It is simultaneously a Zhou–Hansen structured-duplicate-detection projection**
  (*Structured Duplicate Detection in External-Memory Graph Search*, AAAI-04):
  `p(X) = (width(X), |X|)` has bounded abstract out-degree, and Thm 1 then says
  the duplicate-detection scope of a node is contained in the pre-images of its
  abstract successors — i.e. one shell at a time need be resident.

**The ties are the design's one open risk, and they look shallow.** A shell with
internal edges needs an inner fixpoint rather than a single pass; its depth is
the number of sub-passes. `topo.py` TEST 4 measures the length of *consecutive*
same-shell runs along random DP walks:

| n₀ | comparator edges | ties | run-length histogram | max |
|---|---|---|---|---|
| 8 | 2,707 | 152 (5.6 %) | {1: 97, 2: 23, 4: 1, 5: 1} | 5 |
| 9 | 3,290 | 189 (5.7 %) | {1: 121, 2: 25, 3: 6} | 3 |
| 10 | 3,736 | 277 (7.4 %) | {1: 162, 2: 41, 3: 11} | 3 |

~80 % of tie runs are length 1 and none exceeded 5 in ~9,700 edges. That points
at a **bounded k-pass sorted merge with k ≈ 5**, which is exactly the structure
`prune.rs` already uses offline (ascending `|X|` buckets, one pass per bucket).
This is indicative, not a bound — these are runs along random walks, not maximal
chains inside a shell. **The cheapest possible instrumentation ask in this
document** is a three-line counter next to the existing ones: `succ_same_shell`
— successors whose `(width, popcount)` equals the parent's — plus the maximum
same-shell chain length observed. That converts "k-pass merge" from an indication
into a number.

### 7.2 New measurement: shells are fine-grained, and getting finer

`.build/v3-lowmem/shells.py` reads real `group_{w}_{b}.bin` dumps and histograms
by `(width, popcount)`:

| level | run | states | shells | largest shell | largest % | top-16 % | top-64 % |
|---|---|---|---|---|---|---|---|
| 3 | n=9 `--limit 24` | 25,128 | 299 | 659 | 2.62 % | 34.95 % | 85.35 % |
| 4 | n=10 full | 208,243 | 456 | 5,748 | 2.76 % | 36.70 % | 77.37 % |
| **5** | **n=11 `--limit 34`** | **50,221,718** | **1,185** | **708,512** | **1.41 %** | 19.77 % | 64.50 % |

Shell count grows 1.53× then 2.60× per level; the **largest-shell share falls**
(2.62 → 2.76 → 1.41 %). The hard ceiling on shell count at n=13 is
`Σ_{w=3..13} (2^w + 1) = 16,387`, so there is a great deal of room left.

Holding the largest-shell share **flat at 1.41 %** (conservative — it is falling)
gives the RAM requirement of a shell-bucketed external memo:

| growth scenario | level | states | RAM for one shell |
|---|---|---|---|
| OPTIMISTIC | 6 | 4.3e8 | **0.29 GB** |
| | 7 | 1.1e11 | 93 GB |
| GEOMETRIC | 6 | 1.7e9 | **1.15 GB** |
| | 7 | 5.5e10 | **49.5 GB** |
| PESSIMISTIC | 6 | 1.3e10 | **8.6 GB** |
| | 7 | 3.1e12 | 2,750 GB |

**At level 6, one shell fits in the M4's RAM under every scenario.** At level 7 it
fits the server's 47 GB under the geometric scenario. **The RAM wall is solvable.**
What is left is disk capacity and wall time.

### 7.3 I/O is not the constraint

External-sort pass count is `1 + ⌈log_{M/B}(N/M)⌉`. With `M = 40 GB` and
`B = 1 MB` the merge fan-in is ~40,960, so anything below 1.6 PB sorts in **two
passes**; total I/O ≈ 4× the data volume.

| dataset | M4 internal SSD (~2 GB/s) | NVMe (~5 GB/s) |
|---|---|---|
| level 6 @ 33× (57 GB) | 0.03 h | 0.01 h |
| level 6 @ 246× (420 GB) | 0.23 h | 0.09 h |
| level 7 @ 33× (3.5 TB) | 1.9 h | 0.8 h |
| level 7 @ 246× (195 TB) | 108 h | 43 h |

Against 0.11–0.85 M4-*days* of compute at level 6, the I/O is **1–3 % of the
run**. Streaming is free; the only question is whether the bytes fit.

### 7.4 The trap to avoid, and the honest risks

- **Do not build a random-access disk-backed memo.** Suzuki & Fukunaga (SoCS
  2026, arXiv:2606.01840) measure immediate duplicate detection on a PCIe-Gen4
  NVMe at **1,847 expansions/s** with `O_DIRECT` versus 319,720 with the page
  cache and 1,076,117 in RAM — a 173× cliff. Corroborated by the QD1 random-read
  penalty on a 990 Pro (~87× vs sequential, collapsing to ~1.3× at QD32).
  Sequential sorted-merge or nothing.
- **The real risk is that the restructuring increases `N`.** The engine's
  50.9 M states at level 5 are the *demand-driven* population under a
  branch-and-bound ordering heuristic (`search.rs:461` / `472`). A
  level-synchronous external sweep changes the expansion order, and `internals`
  §8.2 already flags that a batched semi-external `improve` "is a substantial
  rewrite of the async coroutine structure … and it changes the search order".
  If the order change inflates `N` by even 3×, it eats the entire win.
  **Mitigation:** prototype at n=11 `--limit 34` (a known 50.2 M-state, 333 s
  target) and gate on `N` within 1.2× of the in-memory run.
- **Sustained NVMe write is 4–7× below the marketing figure** (990 Pro ~1.8 GB/s
  after the SLC cache; SN850X ~0.92 GB/s), and a 2-pass sort writes 2× the
  volume. Endurance is a real line item at multi-TB scale (~$0.28–0.42 per TB
  written of drive life). The M4's SSD is soldered and publishes no TBW — **do
  not run the bulk phase on the M4.**

### 7.5 What going external actually costs — the measured range is 0.58× to 5×

Disk has a worse reputation than the measurements support. The published
exchange rates, all from controlled experiments:

| trade | memory bought | **time factor** | source |
|---|---|---|---|
| SDD on multiple sequence alignment, external | 10–40× | **0.58× (faster)** | Zhou & Hansen, AAAI-04 |
| SAT: `Fix-2` prefix split vs single `Fix-1`, n=13 depth | >4 GB → fits | **<1× (faster)** | Bundala & Závodný, arXiv:1310.6271 |
| SDD on the 15-puzzle, external | 16–58× | **1.24×** | Zhou & Hansen, AAAI-04 |
| BFHS vs A*, both in RAM | 12–16× | **1.30–1.40×** | Zhou & Hansen, ICAPS-04 |
| **A\*+DDD on disk vs A\* in RAM** (15-puzzle, 100 instances) | **unbounded** — 83/100 solved → **100/100** | **~5×** | Korf, AAAI-04 |
| TBBFS end-to-end vs pure compute rate | — | ~3.6× | Korf, AAAI-08 |
| **networked cluster storage** (Kunkle–Cooperman vs TBBFS) | — | **8.9–17.8×** | Korf, AAAI-08 |

Two conclusions that matter for our sizing:

1. **The 10–100× disk penalties in folklore come from *network-attached* storage,
   not from disk.** On a single box with local NVMe, budget **2–5×**, and it can
   be *negative* when the abstraction that enables externalisation also improves
   cache locality — which is exactly what a `(width, |X|)` shell sweep does to a
   currently-random-access `StateMap`.
2. Korf & Schultze's own summary of their 15-puzzle BFS is *"contrary to the
   usual assumption in the literature of disk-based algorithms, our program is
   CPU-bound rather than I/O-bound"* — consistent with §7.3's finding that our
   I/O is 1–3 % of the run.

Also worth copying verbatim: hash-based DDD beat sorting-based DDD on the
14-puzzle by **3.5× in storage *and* 3.5× in time** (259 GB/88 h → 75 GB/24 h
50 m), and it is **interruptible with zero storage overhead** — the filesystem
state is the checkpoint. That last property is what makes AWS spot usable.

**Verdict 5: PROMOTE**, as the memory-ceiling item, with the `N`-inflation gate
as its go/no-go.

---

## 8. Family 6 — other memory-bounded exhaustive search

### 8.1 cube20.org — the decomposition was free, and both its levers are already present

Source: Rokicki, Kociemba, Davidson & Dethridge, *The Diameter of the Rubik's
Cube Group Is Twenty*, SIAM J. Discrete Math. 27(2):1082–1105, 2013
(https://tomas.rokicki.com/rubik20.pdf), with the memory discussion sharpest in
its predecessor Rokicki, *Twenty-Five Moves Suffice*, arXiv:0803.3435.

| quantity | value |
|---|---|
| `|G|` | 4.325×10¹⁹ |
| subgroup `H` (Kociemba phase-1 target) | `|H| = 8!·8!·4!/2 = 19,508,428,800` |
| cosets of `H` | 2,217,093,120 |
| after `H`'s 16-way symmetry | 138,639,780 |
| after a further **set cover** | **55,882,296** cosets actually solved (39.7× total) |
| **RAM per worker** | **2.3 GB** — *"a bitmap of this size requires 2.3GB of memory"* (§6.3), 1 bit/position, plus a ~170 M-entry pattern database |
| per-coset time | 19.622 s on a 4-core 2.8 GHz Nehalem |
| total | **34.75 CPU-years ≈ 139 core-years** on Google's idle cycles, "a few weeks" wall |

**The decisive fact is that this was not a memory-for-time trade at all — it went
the other way.** The paper's own ladder of alternatives (§2, §5):

| approach | memory | cost |
|---|---|---|
| optimal solver per position | **33 GB** of tables | 7,000,000,000 CPU-years |
| Kociemba two-phase per position | ~300 MB | 3,700,000 CPU-years |
| coset method, symmetry only, depth-15 + 5 prepasses | 2.3 GB | 87 CPU-years |
| **actual (adds set cover)** | **2.3 GB** | **35 CPU-years** |

Against a hypothetical monolithic in-memory search (4.325×10¹⁹ bits = **5.4 EB**),
the coset decomposition is a **2.2×10⁹× memory reduction at negative time cost.**
The reason is the batching it unlocks: Table 2.1 gives 2.0 positions/s solved
individually against **2×10⁶/s** in coset form (optimal), and 3,900/s against
**10⁹/s** (near-optimal) — a 256,000× throughput gain, available *only because
the check-off table fits in RAM*. The 2.3 GB was chosen **first** and everything
else designed backwards from it, including the choice of `H` (ten of the eighteen
moves fix its relabelled solved state, so one linear "prepass" extends the whole
found set by ten moves at 65 billion group operations/s).

**And the redundancy it accepted almost exactly cancelled.** Five prepasses × ten
moves = **50 touches per position** inside a coset; but the 39.7×
symmetry-plus-set-cover reduction pays for it, so the whole proof costs
**≈1.26 group operations per certified position** — the paper's own version being
that it "used fewer core-cycles (about 1.2×10¹⁹) than there are cube positions".

**Both mechanisms are already structurally present in this programme, and
neither is a free lever here.**

- The group quotient is `canonicalize(true)` — canonical form modulo
  `S_13 × C_2`, `|G| = 13!·2 = 1.25×10^10` (`internals` §2.3), paid on every
  generated state. `transforms-assessment` §3.1 already prices what it buys:
  exactly `log10|G| = 10.1` orders, against an empirical-vs-order-theoretic gap
  of 2,440 orders. Harvested, and not enough.
- "Solve many at once" is the entire design of the output-set DP. **One node is
  an output set `X`, and its bound covers *every* network that produces `X`.**
  That amortisation is already larger than cube20's.

**What the comparison actually indicts is our representation, not our
decomposition.** cube20's cell is 1 bit/state; ours is 30–90 bytes. The right
reading of §8.1 is therefore the question in §8.1a: *what is the S(13) analogue of
`H`* — a partition whose cells are 10⁹–10¹⁰ states, whose per-cell work is a
linear sweep rather than random access, and whose cells are related by a symmetry
group large enough to pay for the intra-cell redundancy? The `(width, |X|)` shell
of §7 is the closest candidate this document found: cells of the right size
(measured 7×10⁵ at level 5, projected 10⁸–10⁹ at level 7), swept sequentially,
with `S_13 × C_2` already amortised into the key. It is not a coset decomposition
and it does not unlock a 10⁵× batching win — but it is the same *shape* of idea,
and it is the reason §7 is the PROMOTE.

### 8.1a Bytes per live state — the number that actually separates us from the precedents

| system | states reached | RAM held | **bytes/state** | **states per byte of RAM** |
|---|---|---|---|---|
| cube20 coset bitmap | 1.95×10¹⁰ per cell | 2.44 GB | **0.125** (1 bit) | 8.0 (1.8×10¹⁰ amortised over `\|G\|`) |
| Korf two-bit BFS / TBBFS | 1.3×10¹² | 2 GB | **0.25** (2 bits) | ~610 |
| Chinook 2003, non-captures phase | ~10¹¹ per slice | 200 MB page cache | — | **500** (499/500 hit rate) |
| Syzygy 7-piece generation | 4.24×10¹⁴ | ~1 TB | — | ~424 |
| Korf 15-puzzle BFS (working set) | 1.05×10¹³ | ~400 MB | 4 (on disk) | ~26,000 |
| **sortnetopt n=11 search** | 2.46×10⁹ | **178 GiB** | **~78** | **0.013** |
| **sortnetopt n=13 level 5 (measured here)** | 5.09×10⁷ | 3.35 GB | **65.8** | 0.015 |
| — same, packed keys only | | 1.51 GB | **29.7** | 0.034 |

Every computation that reached 10¹²–10¹⁹ states did so at **≤4 bytes per state**,
and the two that reached the top got to **1–2 bits**. All of them get there the
same way: a **bijective rank function** from state to integer, so the visited set
is a direct-address bit array and needs no key at all.

**We cannot have one.** A canonical output set is an arbitrary subset of
`{0,1}^w` whose canonical form is defined by a refinement procedure
(`canon.rs`), not by a formula; there is no rank. Minimal perfect hashing
(RecSplit ~1.56 bits/key, PTHash ~2.4) needs the **complete keyset up front** —
which is precisely the thing being computed. This is the single largest constant
between us and the precedents and it is **not closable**.

What *is* closable is the 2.22× B-tree overhead: 65.8 B/state resident against
33.7 B/state of packed key + `State`. Sorted runs on disk pay the 33.7 and not
the 65.8, which is one of the reasons §7 is worth building — it is a ~2× win that
comes free with the restructuring.

### 8.2 The external-memory anchors, for calibration

| computation | states | B/state | disk | wall | RAM | source |
|---|---|---|---|---|---|---|
| 15-puzzle complete BFS | 1.05e13 | 4 | 1.4 TB | 28 d 8 h | **2 GB** | Korf & Schultze, AAAI-05 |
| 15 unburned pancakes (TBBFS) | 1.3e12 | **2 bits** | 327 GB + logs | 41.7 d | **2 GB** | Korf, AAAI-08 |
| Rubik's edge-cube subspace | 9.8e11 | 2 bits | ~3 TB | 35.1 d | 2 GB | Korf, AAAI-08 |
| 4-peg Hanoi, 24 disks | 1.79e11 | — | ~130 GB | ~19 d | 1 GB | Korf, AAAI-04 |
| Rubik superflip depth-20 (PEMM) | 3.8e10 exp. | — | 5.0 TB | 28 h | 128 GB | Sturtevant & Chen, IJCAI-16 |

Two calibrations matter.

1. **These are all 10¹²–10¹³-state computations done on 1–2 GB of RAM.** So the
   *memory* part of our problem is squarely within precedent — at level 7's
   optimistic 1.1e11 states we would be *below* Korf's 15-puzzle scale.
2. **They are all 2 or 4 bytes per state, and ours is 30–90.** Korf gets 2 *bits*
   by having a **bijective rank function** from state to integer, so the visited
   set is a direct-address bit array. We have no such rank: a canonical output
   set is an arbitrary subset of `{0,1}^w`, and its canonical form is defined by
   a refinement procedure, not by a formula. **This is the single largest
   constant-factor gap between our situation and the precedents, and it is not
   closable** — minimal perfect hashing (RecSplit at 1.56 bits/key, PTHash at
   2.4) requires the *complete keyset up front*, which is precisely what we are
   computing.
3. Korf & Schultze's hash-based DDD is **interruptible with zero storage
   overhead** — the filesystem state is the checkpoint, and duplicate work after
   a restart merges away harmlessly. That property is worth real money on spot
   instances and is a free by-product of the §7 design.

### 8.3 The redirect this reconnaissance actually found — **PROMOTE to the queue**

The brief asked for "anything else in the literature of memory-bounded
exhaustive search". The most valuable thing the sweep turned up is not a memory
technique at all. It is the one family that attacks `N` — which §2.4 and §10
establish is the only lever with the right exponent — and it is **specific to
comparator networks and completely unexploited by this programme**.

**Codish, Cruz-Filipe & Schneider-Kamp, *Sorting Networks: The End Game*, LATA
2015 (arXiv:1411.6408); extended as Codish, Cruz-Filipe, Ehlers, Müller,
Schneider-Kamp, *Sorting networks: To the end and back again*, JCSS
104:184–201, 2019.**

| result | statement | quantified |
|---|---|---|
| Lemma 3 | in a non-redundant sorting network every last-layer comparator is `(i, i+1)` | candidates `n(n−1)/2 → n−1` |
| Theorem 5 | the number of possible last layers is `L_n = F_{n+1} − 1` (Fibonacci) | `L_17 = 2,583` vs `G_17 = 211,799,312` general layers — **82,000×** |
| Cor. 10 | penultimate-layer comparators satisfy `j − i ≤ 3`, with forced companions | — |
| Theorem 11 | every comparator at layer `k` connects **adjacent `k`-blocks** | a backward-propagating constraint at *every* layer |
| Thm 14 / Def. 17 | co-saturated last layers are counted by the Padovan sequence `K_n = P_{n+5}` | `K_17 = 86` vs `L_17 = 2,583` — another **30×** |
| Table 1 | distinct co-saturated **two-layer suffixes** | **n = 13 → 1,440** |

And the measured payoff, in **the optimal-*size* setting, not just depth**
(their §6): adding last-three-comparator constraints and Corollary 12 to the
`S(9) = 25` proof reduced it from **6.5 CPU-years to just over 1.5 CPU-years**
— on the 288-thread cluster, 8 days to 2 days, a **4.3×**. Ehlers & Müller
(arXiv:1410.2736) used last-layer constraints to eliminate **381 of 609**
depth-9 17-channel prefixes.

Two things make this the right item to promote:

1. **It reduces `N`, and §10 shows nothing else available does.** Every other
   family in this document moves bytes around.
2. **It lives on the same object as the shape case split** — the forward network
   prefix, not the backward output set (`s13-shape-case-split` §7.3: "the class
   constraint lives on the *forward* object … this case split cannot be pushed
   into the Harder-style DP as-is"). So it composes with, rather than competes
   with, the already-committed decomposition: **prefix constraints from the
   shape case split × suffix constraints from the End Game theory is a pincer on
   the same enumeration**, and both need the same missing engine piece
   (Tier-2 #6, canonical prefix decomposition, plus the max-path tracer).

Caveats, stated: the End Game results are proved for *layered* networks and most
of the quantification is in the depth setting; the size-setting application in
their §6 is real but is one data point at n=9 in a SAT encoding, not in a
Harder-style DP. Binding it to this programme's engine is genuine work and is
**not** a low-memory technique — it belongs in the ranked queue next to the case
split, not in the endgame plan of §11.

### 8.4 Two unexploited items inside `sortnetopt` itself, recorded

- Harder's canonical labelling (§6.1 of arXiv:2012.04400) *"does not use orbits
  of the automorphism group for pruning, and instead only prunes the subtree
  which led us to discover an automorphism."* Full orbit pruning is standard
  nauty/Traces practice and is typically worth a large constant.
- The scheduling of `PrunedImproveStep` vs `HuffmanImproveStep` vs
  `SuccessorImproveStep` inside `improve` is, by the author's own admission, an
  unanalysed heuristic (*"a comprehensive comparison of different strategies
  would require further experiments"*). Those are the two `sort_by_key` calls at
  `search.rs:461` and `472` that `internals` §5 already flags as the ML-ordering
  insertion point.

---

## 9. What the money and the machines actually buy

### 9.1 AWS, 2026 spot prices (us-east-1, representative)

| instance | RAM | local NVMe | spot $/h | hours on $100 |
|---|---|---|---|---|
| `is4gen.8xlarge` (Graviton2) | 192 GiB | **30 TB** | $1.36 | **73.5** |
| `i3en.24xlarge` | 768 GiB | **60 TB** | $3.63 | 27.6 |
| `i7ie.24xlarge` | 768 GiB | 60 TB | $4.33 | 23.1 |
| `x1e.32xlarge` | **3,904 GiB** | 3.84 TB | $4.70 | 21.3 |
| `u7i-6tb.112xlarge` | 6 TiB | — | **$62.79 on-demand, no spot** | 1.6 |

Notes that change the decision:
- **No `u-`/`u7i-` high-memory instance has spot pricing at all.** $100 buys 16
  minutes of a 32 TB box. Rule the family out.
- **AWS new-account credits are $100 immediately plus up to $100 more.** Check
  whether the entire budget can be credit before spending cash.
- **Egress is the trap**: pulling 10 TB out costs ~$891. Never egress the memo;
  export certificates only.
- **Instance-store NVMe is lost on spot termination.** The §7 design's
  restart-tolerance is what makes spot usable at all.
- **A Hetzner-class dedicated box buys ~18–22 days for $100** versus 21–73 hours
  on AWS spot — and no interruption. Given that this engine does *not* core-scale
  (§2.1) and needs long wall time, **dedicated time beats parallel width**. AWS
  wins only on one axis: 30–60 TB of local NVMe, which nothing else in the budget
  can match.

### 9.2 The phase profile decides which phase goes where

Harder's own n=11 numbers (arXiv:2012.04400 §9), which are the only end-to-end
pipeline measurements that exist at this scale:

| phase | peak RAM | wall | output | machine |
|---|---|---|---|---|
| **search** | **178 GiB** | 4 h 51 m | 93 GiB, 2,462,890,689 sets | EPYC 7401P 24c/48t |
| pruning (partitioned, one part resident at a time) | **16 GiB** | 2 d 3 h 39 m | 874 MiB, 15,432,816 sets | same |
| certificate generation | 54 GiB | 19 h 02 m | 2,926 MiB, 12,659,079 steps | same |
| **verification** | **6 GiB** | **34 m** | `Some (11, 35)` | Ryzen 9 3950X |

**Verification is ~30× cheaper in memory and ~8.6× cheaper in wall than the
search that produced it.** Two operational consequences:

- **A rented box should only ever run the search phase.** Pruning, certificate
  generation and verification all fit on owned hardware, and verification fits
  on the M4.
- **Egress certificates, never the memo.** The n=11 certificate is 2.9 GiB
  against a 93 GiB dump; at $0.09/GB that is a rounding error where the memo is
  not (10 TB of egress ≈ $891).

*(A caution on a tempting mis-reading: the 178 GiB → 16 GiB drop across search →
prune is **not** an 11×-memory-for-10.7×-time tradeoff. They are different
workloads on different inputs. The partitioned prune is genuinely an
out-of-core organisation choice, but no in-memory prune was ever run, so the
repository contains no controlled measurement of its cost. Do not cite it as an
exchange rate; §2.4's table is the controlled data.)*

### 9.3 Which scenario × machine completes

Disk requirement uses the shifted bytes/state model (§2.2); "fits" additionally
requires one 1.41 % shell to be RAM-resident.

| scenario | level | states | disk needed | wall | smallest machine that fits |
|---|---|---|---|---|---|
| OPTIMISTIC | 6 | 4.3e8 | 20.6 GB | 0.03 d | **M4** |
| | 7 | 1.1e11 | 6.6 TB | 7.1 d | AWS `is4gen.8xlarge` (needs 2.3× its $100 hours) |
| | 8 | 8.8e11 | 81 TB | 59 d | **none** |
| GEOMETRIC | 6 | 1.7e9 | 81.5 GB | 0.11 d | **server** |
| | 7 | 5.5e10 | 3.5 TB | 3.8 d | AWS `is4gen.8xlarge` (3.8 d vs 3.06 d affordable) |
| | 8 | 1.8e12 | 170 TB | 124 d | **none** |
| ALTERNATING | 6 | 7.6e8 | 37 GB | 0.05 d | **server** |
| | 7 | 7.6e11 | 48 TB | 52 d | **none** |
| PESSIMISTIC | 6 | 1.3e10 | 607 GB | 0.85 d | 4 TB NVMe ($200 — outside budget) |
| | 7 | 3.1e12 | 195 TB | 209 d | **none** |

---

## 10. Best reachable level, per machine

Assumptions: the §7 shell-bucketed external memo is built (otherwise subtract
roughly one level everywhere); 80 % of RAM and 90 % of disk usable; the engine's
measured 1.71×10⁵ states/s; no subsumption (which trades ~9× memory for ~5.5×
wall and would shift the disk-bound rows up by ~0.6 of a level at the cost of
0.5 of a level of wall).

| machine | binding constraint | best level, RAM-only (today's engine) | best level, with §7 external memo | wall at that level |
|---|---|---|---|---|
| **M4** — 10 c, 16 GiB, 26 GiB free disk | **disk (26 GiB)** | **5** (measured: level 5 = 3.35 GB, done) | **5.5–5.8** — level 6 only under the OPTIMISTIC multiplier | ≤ 1 h |
| **server** — 47 GiB, 324 GiB free disk | **disk (324 GiB)** | 5.5–5.8 | **6.0–6.5** — level 6 under OPTIMISTIC/GEOMETRIC/ALTERNATING; *not* under PESSIMISTIC | 1–20 h |
| **server + 4 TB NVMe** ($200, outside budget) | wall | 5.5–5.8 | **6.4–7.2** — level 6 always; level 7 only at the 33× floor | 0.8 d – 3.8 d |
| **$100 AWS `is4gen.8xlarge` spot** (192 GiB, 30 TB, 73.5 h) | **wall (73.5 h)** | ~6.3 | **7.0–7.2 in capacity, ~6.8 in time** | capacity for level 7, but only 3.06 days of it |
| **$100 AWS `i3en.24xlarge` spot** (768 GiB, 60 TB, 27.6 h) | **wall (27.6 h)** | ~6.5 | 7.2 in capacity, **~6.5 in time** | 1.15 days |
| **any machine, level 8** | **wall** | — | — | **59 d (optimistic) to 140 y (ceiling) of pure touch time** |

> **The honest headline: level 8 is out of reach, and it is out of reach on
> *time*, not on memory.** Every technique in families 1–5 reduces bytes per
> state or bytes held at once. **None of them reduces `N`**, and
> 1.8×10¹²–7.6×10¹⁴ states at 1.7×10⁵ states/s is 124 days to 140 years before a
> single byte is stored.
>
> Exactly three things could change that, and all three are outside the
> low-memory question the brief asked:
> 1. **On-line subsumption actually shrinking the per-level multipliers** at
>    n=13 scale (§2.4) — the compression ceiling grows 1.3 → 2.2 → 15.8 → 160×
>    over n=5,7,9,11 and is the largest single unexploited number anywhere in
>    this programme. **Unmeasured above level 4.**
> 2. **Forward structural constraints that make states unnecessary** — the shape
>    case split (already committed) and the Codish End Game suffix theory
>    (§8.3, unexploited, `1,440` co-saturated two-layer suffixes at n=13, a
>    measured 4.3× on the optimal-size `S(9)` proof).
> 3. A throughput increase the engine's architecture does not currently permit
>    (§2.1).
>
> **Level 7 is out of reach on owned hardware** and marginal on the $100 burst,
> *conditional on a multiplier we have not measured*.
>
> **Level 6 is reachable on the server, today, with the §7 design** under three
> of four growth scenarios — and it is the measurement that decides everything
> else.

---

## 11. The composed plan

### Step 0 — measure level 6 (blocking; nothing else should start first)

`n=11 --limit 35`. It is `D(11) = 6`, so it **terminates** and self-checks
(`result` must be 35, and the certificate must be accepted by the unchanged
frozen `snocheck`). By the Universal Level Law it costs the same as
`n=13 --limit 43`, is ~5 % cheaper in bytes, and unlike the n=13 run it produces
a verifiable answer.

- Machine: **server** (47 GiB, 324 GiB disk), with
  `SORTNETOPT_CHECKPOINT_DIR` set and `..._INTERVAL_SECS=600` (measured cost
  0.06 % of runtime).
- Budget: 0.11 d / 81 GB (geometric) to 0.85 d / 607 GB (pessimistic). If RSS
  crosses ~40 GB, restart with the on-line index (`evict`, DIMS=24, widths chosen
  from the level-5 census — the census says **w8, w9**, not a fixed formula):
  ≥9× memory for ≥5.5× wall, measured at n=12.
- Deliverable: the level-6 state count, the level-6 width census, the level-6
  shell histogram (rerun `shells.py` on the dump), and the 5→6 multiplier.
- **This one number collapses a 4-order-of-magnitude bracket.** Every "marginal"
  above becomes a yes or a no.

### Step 0b — measure the same ladder with the index ON (runs beside Step 0)

Same machine, same binary, `SORTNETOPT_SUBSUME=evict`, `DIMS=24`, widths **8,9**
(census-chosen, not formula-chosen — M2a recommendation 3). Run `n=11 --limit 33,
34, 35` and record the *multipliers*, not just the peak memory.

- If the multipliers fall materially below 33×, re-derive §9.3 and §10 and the
  whole endgame reopens.
- If they do not, the §10 table stands and the effort belongs in §8.3 instead.
- Cost: 5.5× the Step-0 wall at the measured n=12 exchange rate, so 0.6–4.7 d
  at level 6 — and it is the *only* experiment in the programme that could move
  the answer by orders of magnitude.

### Step 1 — three cheap instrumentation asks, all behaviour-preserving

1. `succ_same_shell` and the maximum same-shell chain length (§7.1) — closes the
   one open risk in the external design.
2. `filter_exact_hits` next to the existing `filter_exact_calls`
   (`transforms-assessment` §4.3 already names this as the cheapest ask).
3. Per-`(width, popcount)` live counts in `log_stats`, so the shell histogram
   comes out of every run for free instead of out of a dump.

### Step 2 — the shared bound oracle (§6), which is mostly already built

Add a read-only **seed-import** path beside the existing checkpoint resume:
accept a foreign table, import `bounds` only, merge by `max`/`min`. Validate at
n=9/n=10 with the standard gate (exact result, exact bound sequence, certificate
accepted by the unchanged checker). §6.1 is the soundness evidence.

Pair it with **per-job certificate composition**, which the `u32` step-id cap
makes mandatory anyway.

### Step 3 — the shell-bucketed external memo (§7), gated

Prototype against `n=11 --limit 34` (known: 50.2 M states, 333 s, 3.17 GB).
**Gate: `N` within 1.2× of the in-memory run.** If the reordering inflates the
demand-driven population, stop — that is the failure mode that eats the whole
win. Sorted-merge only; no random-access disk map (§7.4).

### Step 4 — where the $100 goes

**Nowhere, yet.** Concretely:

- Steps 0–3 all run on hardware already owned. Spending before Step 0 is
  spending on a 4-order-of-magnitude bracket.
- **Check first whether the $100 can be AWS new-account credit** ($100 immediate
  + up to $100 more).
- **If Step 0 returns a 5→6 multiplier near the 33× floor**, the burst that makes
  sense is `is4gen.8xlarge` spot (192 GiB RAM, 30 TB NVMe, $1.36/h, 73.5 h on
  $100) for a level-7 attempt: it has the capacity (3.5 TB needed) and roughly
  three-quarters of the time (3.06 affordable days against 3.8 M4-days of
  compute, on a Graviton2 that is probably slower per core than the M4). That is
  an honest coin flip, not a plan — and it is only reachable at the floor.
- **If Step 0 returns a multiplier above ~50×, do not spend the $100 at all.**
  Level 7 then needs 48–195 TB and 52–209 days, which no amount of $100 reaches.
  Put the money into a 4 TB NVMe for the server instead (it makes level 6
  unconditional and is reusable), and put the effort into reducing `N` —
  on-line subsumption at n=13 scale and the class/prefix decomposition — which
  is the only lever with the right exponent.
- **If it is spent, it buys the search phase only.** Pruning, certificate
  generation and verification all fit on owned hardware (§9.2: verification is
  6 GiB / 34 m against a search that took 178 GiB / 4 h 51 m at n=11). Egress
  the certificate, never the memo. Rely on hash-based DDD's zero-overhead
  interruptibility (§7.5) to survive spot reclamation, and calibrate against a
  local sub-job first (Step 5 rule 1).

### Step 5 — three governance rules taken straight from the precedents

1. **Calibrate before extrapolating.** Rokicki ran **1 coset in 700** on a known
   local machine before trusting the extrapolated total, and used it to
   cross-validate the results coming back from Google's fleet. Any AWS run must
   be preceded by the same: a fixed sub-job run on the server, its cost recorded,
   and the burst's per-unit cost compared against it.
2. **Independent recomputation, not internal consistency.** Chinook's 7-piece
   databases contained a real error of several thousand positions that
   **passed every one of their internal verification tests**; it was found only
   when an outside group recomputed them. This is the argument for the
   programme's existing bit-identical-certificate gate and for the two
   independent B1 verifiers — and it means "the run self-checked" is never
   sufficient.
3. **Budget verification as a first-class line.** Schur Number Five cost
   14 CPU-years to solve and **36 CPU-years to verify** (2.5×); Chinook spent
   **40 % of wall clock** on verification; sortnetopt's certificate generation
   is 4× its search wall at n=11. Our asymmetry runs the other way on *memory*
   (§9.2), but not on time.

### The splitting-cost trap, quantified

Because §11 hands work to a per-(class × prefix) decomposition, the precedents'
warning about granularity is directly on point and is unanimous:

- **Boolean Pythagorean Triples** (Heule–Kullmann–Marek, SAT 2016): of 35,000
  CPU-hours, **21,900 (62 %) went on *splitting*** and only 13,200 on solving.
- **Schur Number Five** (Heule, AAAI-18): total single-core runtime as a function
  of cube count is **U-shaped** — it falls well below plain CDCL, then rises
  again as splitting dominates. Their optimum was ~10⁴ cubes per subproblem, and
  they built a *hardness predictor* (a cheap partial split whose runtime predicts
  difficulty) to keep cells balanced, splitting anything over 1 s and merging
  siblings under 0.1 s. Their stated reason was memory: *"solving these hard
  subproblems required disproportionally more memory… solving a few hard problems
  on the same chip at the same time could kill all threads."*
- **Chinook** (Schaeffer et al., ACG10 2003): over-slicing multiplies the
  per-slice *Lookups* phase, which is **24 % of their wall clock**; they
  explicitly recommend not slicing sub-databases that are already small.
- The counter-example, and the encouraging one: **Bundala & Závodný** found that
  for n=13 checking *all* the depth-two-prefix `Fix-2` formulas was **faster than
  checking the single `Fix-1` formula**, despite restarting the solver per
  prefix — splitting was free memory *and* a speedup. That is the outcome to aim
  for, and §6's shared bound oracle is what makes it reachable here, because it
  is what stops each cell re-deriving the shared core.

**Concrete rule for this programme:** do not choose the prefix depth by
convenience. Measure the per-cell cost at two depths at n=11, plot the total, and
pick the minimum — and expect the shared-oracle seeding to move that minimum
toward *finer* cells than it would otherwise sit.

### What is explicitly *not* in the plan

- No pebbling/recomputation scheme (§3).
- No bidirectional or backward reachability (§4).
- No bisimulation quotient beyond the one afternoon probe (§5).
- No REVOLVE-style checkpoint schedule (§3.1).
- No random-access disk-backed memo (§7.4).
- No expectation that a cloud burst buys parallel speedup (§2.1).

---

## 12. Reproduction

Everything below is pure stdlib Python over artifacts already in the repository.
No search was run and no binary was invoked.

```
python3 .build/v3-lowmem/census.py      # width/byte census, level extrapolation, machine capacity
python3 .build/v3-lowmem/wave.py        # travelling-wave model, bytes/state at levels 6-8
python3 .build/v3-lowmem/tradeoff.py    # sharing factor, measured alpha, tradeoff curve, touch-time floor
python3 .build/v3-lowmem/layers.py      # the 1.9x frontier/layer ceiling; nested-level fact; disk sizing
python3 .build/v3-lowmem/topo.py        # Shell Lemma: (width,|X|) topological quasi-order + tie rate
python3 .build/v3-lowmem/shells.py <rundir>   # (width,|X|) shell histogram of one dumped memo
python3 .build/v3-lowmem/shells_fast.py # the same over all three real dumps (levels 3,4,5)
python3 .build/v3-lowmem/sdd.py         # shell-bucketed external memo sizing, per machine
```

and the cross-run set/value comparison of §6.1:

```
python3 .build/v3-lowmem/overlap.py     # Jaccard + bound agreement, n=9 vs n=10 level-4 dumps
```

Inputs used: `.build/v3-transforms/ladders.json`;
`.build/v3-limits/probe13-off-L{37..42}/instrument.json`;
`.build/v3-limits/census12-L{34..38}/instrument.json`;
`.build/v3-m0b/runs/baseline-n9-a/`, `baseline-n10-a/` (level-4 dumps);
`.build/v3-transforms/n9/L24/_search_9/` (level-3 dump);
`.build/v3-transforms/n11/L34/_search_11/` (level-5 dump, 1.4 GB).
Hardware facts (`sysctl`, `df`) were read on the M4 on 2026-08-18.
