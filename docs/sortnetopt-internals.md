# sortnetopt internals — code archaeology for Track B / M0

> ## ⚠ CORRECTION 2026-08-22 — §"Seeding the bounds table" is **WITHDRAWN**
>
> **What is withdrawn.** The recommendation in this document to raise
> `sortnetopt`'s *lower* bound seed from the universal `1` to **44** for the
> n = 13 root ("Since S(13) ∈ {44, 45}, seeding `[44, 45]` means a single
> iteration decides the question"). That recommendation is retired
> permanently. Do not implement it.
>
> **Why.** The recommendation was already gated by this document's own risk
> analysis: *"The seed must be an independently proved bound. The 44 bound is
> currently folklore … so using it as a seed requires the write-up in
> `docs/s13-lower-bound-note.md` to exist and be checked first."* That gate can
> never open. The audit of van Voorhis (1972) — `docs/kraft-dispute-verdict.md`,
> `docs/paper/audit-paper-v2.md` — establishes that equations (5) and (6) of the
> chapter are false, that equation (7) is derived from them and from nothing
> else, and that consequently **no correct argument for `P(2,13) ≥ 9`, and hence
> none for `S(13) ≥ 44`, is available**. The precondition is unsatisfiable, so
> the recommendation is dead, not deferred.
>
> **The hazard this closes.** A too-high lower seed produces a *wrong answer
> silently*: `improve` can close the interval by upper-bound descent and return
> the seed unproved. Seeding 44 would have produced a fabricated `S(13) ≥ 44`.
>
> **What replaces it.** Nothing. The proved floor is `S(13) ≥ 43` (the one-value
> bound, unaffected by the audit). No lower-bound seeding is authorised under
> this programme; the lower seed stays at the engine's universal default.
>
> **Scope of this banner.** Only the lower-seed recommendation is withdrawn. The
> rest of this document — the code archaeology, the measured internals, the
> upper-bound / `MAX_CHANNELS` extension and the other ranked attack surfaces —
> is unaffected and remains current.

Target: Jannis Harder's `sortnetopt`, pinned read-only clone at
`.cache/third_party/sortnetopt`, commit
`0b5d09c47446096f9e3a0812b35afc72b7f2a718` (verified via `git rev-parse`).
Paper: arXiv:2012.04400.

All paths below are relative to that clone unless prefixed with the project
root. **Nothing in the clone was modified.** Two small Python differential
tests were run in scratch (results reported in §3.6); no build was performed.

Anchor measurements used throughout, from `docs/sota-survey.md:98,206-209`
(Harder's paper/HN figures):

| | n=9 | n=11 | n=13 (extrapolated) |
|---|---|---|---|
| sequence sets bounded (explored) | 206,279 | 2,462,890,689 | ~3e13 |
| non-subsumed sets | 13,034 | 15,432,816 | — |
| certificate steps | 11,934 | 12,659,079 | ~1.5e11 |
| search RAM | 58 MiB | 178 GiB (93 GiB dumped) | ~20 PB (author's estimate) |
| search wall time | 0.5 s | 4 h 51 m (24c/48t EPYC) | — |

---

## 1. Overall algorithm

### 1.1 Entry point and driver

`src/bin/sortnetopt.rs:101-114` (`cmd_search`) builds
`OutputSet::all_values(channels)` — the full Boolean cube, i.e. the set of all
2^n input vectors — optionally applies a `--prefix` comparator list, and calls
`Search::search`.

`src/search.rs:31-78` (`Search::search`):

* line 37: a single `StateMap` — the DP memo table (§2.5). This is the whole
  persistent state of the search.
* line 44: `initial.canonicalize(true)` — canonicalise modulo channel
  permutation *and* complement/reversal.
* lines 46-71: `ThreadPool::scope`, spawning a 10-second stats logger
  (47-56) and the main loop (58-68).
* lines 58-68: **successive approximation.** Repeatedly call `improve` on the
  root until `bounds[0] == bounds[1]` (interval closed) or `bounds[0] >= limit`.
  Each `improve` call raises the lower bound or lowers the upper bound by at
  least one somewhere in the DAG.
* lines 73-75: `dump_states` writes the entire memo table to disk (§3.2).

The pipeline as a whole is `search_and_verify.sh:25-33`:
`search` → `prune-all` → `gen-proof` → `snocheck`. Search, subsumption pruning
and certificate generation are **three separate process invocations** over
files on disk.

### 1.2 What a search node is

There is no `Node` struct. A node is a **canonical `OutputSet`** — a set of
Boolean vectors of width k, 3 ≤ k ≤ `MAX_CHANNELS` (= 11,
`src/output_set.rs:13`) — used as the key of `StateMap`. Its value is

```rust
// src/search/states.rs:17-21
pub struct State {
    pub bounds: [u8; 2],           // [lower, upper] on comparators still needed
    pub huffman_bounds: [u8; 2],   // sub-interval still reachable via the Huffman rule
}
```

`bounds` is a closed interval on the minimum number of comparators required to
sort every vector in the set. `huffman_bounds` is an internal memo of how much
the van Voorhis/Huffman rule can still contribute at this node, so the
(expensive) Huffman sub-search is not re-run once exhausted
(`src/search.rs:208`, `269`).

Default (unvisited) states, `src/search/states.rs:62-88`:

* sorted set → `[0, 0]`
* ≤ 2 channels → `[1, 1]`
* otherwise → `[1, known_bounds[channels]]` with
  `known_bounds = [0,0,1,3,5,9,12,16,19,25,29,35]` (line 76) — i.e. the interval
  is seeded from the *known optimal sizes* S(0..11), falling back to n(n-1)/2.
  **This table is the interval-seeding hook** (see §8.3).

The search DAG is implicit: vertices are canonical output sets; edges are
(a) apply a non-redundant comparator (same width), (b) prune an extremal
channel (width − 1).

### 1.3 The recursion: `Search::improve`

`src/search.rs:127-259`. One call performs *one* bound improvement and returns
the new `State`; the caller re-reads and decides whether to call again.

1. **Dedup / lock** (134-146). Re-read the state; return immediately if it
   changed since the caller's snapshot, or if the interval is closed. Otherwise
   acquire the per-set async lock `StateMap::lock`
   (`src/search/states.rs:106-144`). If another task already holds it, `await`
   its completion and loop — this is what collapses the search *tree* into a
   *DAG* and prevents duplicated work on shared subproblems.

2. **Extremal channels** (157-165). For each polarity p ∈ {false, true},
   collect the channels c for which the singleton vector e_c (p = false) or its
   complement (p = true) is present:
   `OutputSet::channel_is_extremal`, `src/output_set.rs:491-498`. These are the
   channels that can still receive the minimum (resp. maximum) value.

3. **Forced-channel (van Voorhis) reduction** (167-206). If exactly one channel
   is extremal for some polarity, the set is equivalent to its (n−1)-channel
   pruning. **Both** bounds are transferred, in both directions
   (181-199), and `improve` recurses on the pruned set until one moves. This is
   the mechanism that drives the DP *down in channel count*, and it is why most
   entries in the memo table have fewer than n channels (§2.5).

4. **Huffman bound** (208-214). If `huffman_bounds[1] > bounds[0]` there is
   still headroom; run `improve_huffman` (§1.4).

5. **Successor expansion** (216-227). For `i` in `0..channels`, `j` in `0..i`:
   `target.apply_comparator([i, j])` (`src/output_set.rs:568-597`) returns
   `false` for *redundant* comparators (those where all vectors are already in
   order, or all out of order) — those are skipped. Survivors are
   `canonicalize(true)`d and registered as edges.

6. **Fixpoint loop** (229-258):
   * `combined_upper_bound = 1 + min_c upper(succ_c)` (230-242). Sound: pick the
     best first comparator and append its best network.
   * `combined_lower_bound = 1 + min_c lower(succ_c)` (244-253). Sound: any
     sorting network for A must begin with *some* non-redundant comparator.
   * If the lower bound improved, store and return.
   * Otherwise `Edges::improve_next` improves exactly one child (the current
     argmin, by the ordering heuristic at 460-477) and the loop repeats.

This is textbook branch-and-bound with memoisation, driven top-down from the
full cube, with the two bound families (successor and Huffman) racing each
other.

### 1.4 The van Voorhis / Huffman bound

Kernel, `src/huffman.rs:3-14`:

```rust
pub fn max_plus_1_huffman(values: &[u8]) -> u8 {
    let mut heap: BinaryHeap<Reverse<u8>> = values.iter().map(|&v| Reverse(v)).collect();
    while let Some(Reverse(first)) = heap.pop() {
        if let Some(Reverse(second)) = heap.pop() {
            heap.push(Reverse(first.max(second) + 1));   // <- combine two smallest
        } else { return first; }
    }
    0
}
```

Greedy Huffman merge where the cost of combining two subtrees is
`1 + max(a, b)` rather than `a + b`. Mirrored exactly by the checker:
`checker/snocheck/src/Check.hs:71-88` (`huffmanBound`) and
`checker/verified/Checker.thy:919` (`sucmax_value_bound_huffman`).

Driver: `Search::improve_huffman`, `src/search.rs:261-347`.

* 273-299: for each polarity, prune every extremal channel into an
  (n−1)-channel set, canonicalise, register as an edge.
* 303-344: loop until `huffman_bounds[1] <= bounds[0]`. Per polarity, compute
  `max_plus_1_huffman` over the children's lower bounds (a valid lower bound for
  the parent) and over their upper bounds (a ceiling on what this rule can ever
  yield). If a polarity's Huffman *upper* bound has fallen to `bounds[0]`, its
  edges are dropped (line 319) — that polarity is exhausted. If the Huffman
  *lower* bound exceeds `bounds[0]`, store it and return (326-330).
* 343: otherwise improve one child and repeat.

Intuition: each extremal channel must eventually be merged away by a
comparator; merging two groups costs one comparator plus the max of their
costs; the optimal merge order is the Huffman one. The single-extremal-channel
case degenerates to `max_plus_1_huffman([b]) = b`, which is exactly the van
Voorhis two-channel argument and is short-circuited by step 3 of §1.3.

---

## 2. Data structures

### 2.1 `OutputSet` — the representation

```rust
// src/output_set.rs:29-33
pub struct OutputSet<Bitmap = Vec<bool>> { channels: usize, bitmap: Bitmap }
```

The working representation is a **dense `[bool]` of length 2^channels — one
byte per Boolean vector**, not a bit set. At n = 11 that is 2048 bytes per live
set; at n = 13 it would be 8192 bytes. Bit packing exists only for keys and
storage: `pack_into_slice` / `unpack_from_slice`
(`src/output_set.rs:385-416`, `641-667`), giving `2^channels / 8` bytes
(`packed_len_for_channels`, line 83).

This 8× expansion is deliberate — the hot inner loops
(`apply_comparator`, `prune_extremal_channel_into`, `channel_*_abstraction`)
are all byte-indexed strided scans that would need masking/shifting on a packed
representation. It costs 8× on every transient buffer and on every
`packed_pvec()` call in the `StateMap` hot path.

### 2.2 Hard n = 11 ceilings

`MAX_CHANNELS = 11` (`src/output_set.rs:13`) and the derived aliases at 14-22:

| alias | capacity | at n=11 | needed at n=13 |
|---|---|---|---|
| `BVec<T>` | `1 << MAX_CHANNELS` | 2048 | 8192 |
| `PVec<u8>` | `1 << (MAX_CHANNELS-3)` | 256 | 1024 |
| `AVec<u16>` | **fixed 512** | needs 440 | needs **624 → overflows** |

`MAX_ABSTRACTION_SIZE = channels·(channels−1)·4` is 440 at n = 11 but 624 at
n = 13, while `AVec` is hard-coded to 512 (`src/output_set.rs:22`). Raising
`MAX_CHANNELS` without fixing this silently overflows an `ArrayVec` in
`OutputSet::abstraction` (483-489).

Worse: `OutputSetMap` in `src/search/states.rs:171-181` has **hand-written arms
for channel counts 3..11 only**. `get_with_packed` returns `None` for anything
else (line 328, `_ => None` — a *silent* cache miss), while `set_with_packed`
hits `unreachable!()` (line 374). A naive `MAX_CHANNELS` bump produces a search
that silently loses all memoisation at widths 12-13 and then panics. Both files
must be extended together.

### 2.3 Canonicalisation

`src/output_set/canon.rs`. A graph-isomorphism-style refinement over channel
permutations, with the complement symmetry folded in.

* `Canonicalize::new` (116-161): moves *unconstrained* channels
  (`is_channel_unconstrained`, `src/output_set.rs:177-192`) to the high end and
  excludes them from the search (`used_channels`). Seeds the candidate layer
  with the identity and, when `inversion` is set, with the complemented copy.
* `canonicalize` (163-190): loop of `prune_using_fingerprints` (224-244) →
  `move_singleton` (246-274) → `prune` (276-335) → `individualize` (337-388) →
  `refine` (390-440), until all channels are fixed. The candidate layer holds
  every permutation still tied for the extremal fingerprint; individualisation
  branches on a partition cell and keeps only maximal-fingerprint children.
* Fingerprints: `channel_fingerprint` (`src/output_set.rs:194-211`),
  `low_channels_fingerprint` (213-231), `low_channels_channel_fingerprint`
  (233-266) — all cheap strided popcount-style scans hashed with `FxHasher`.
* Returns `Perm { invert, perm }` (`src/output_set.rs:674-687`).

**The search discards the returned permutation** — `src/search.rs:44, 176, 222,
296` all ignore it. Only the canonical representative is needed; the
permutation needed for the certificate is recovered much later by
`subsumes_permuted` inside `proof.rs`. That is a deliberate memory trade and it
means the search stores no provenance whatsoever.

### 2.4 Abstractions and the subsumption test

* **Abstraction** (`src/output_set.rs:337-489`): a permutation-invariant
  fingerprint vector of `channels·(channels−1)·4` `u16`s built from
  `channel_pair_abstraction` (337-368), then sorted within groups and
  transposed. Used as (a) the k-d tree point and (b) a cheap *necessary*
  condition for subsumption (`Lower::test_abstraction`, `index.rs:101-106`;
  the `LowerInvert` variant at 173-181 exploits the layout so that complementing
  is the index permutation `i ^ 3`).

  **Cost**: `write_abstraction_into` (438-481) is O(n² · 2^n / 4) — about 62k
  inner iterations at n = 11, 346k at n = 13 — versus 256 iterations for
  `pack_into_slice`. Roughly **240× more expensive than the current `StateMap`
  key computation.** This single fact is the main obstacle to naive on-line
  subsumption (§8.1).

* **Exact subsumption** (`src/output_set/subsume.rs`): "does some permutation of
  A make A ⊆ B?" solved as constraint propagation over a channel-to-channel
  matching, `Subsume::search` (44-89):
  `filter_matching` (219-278) removes pairings whose prefix-restricted
  abstractions violate dominance; `move_unique` (280-308) commits forced
  pairings and physically swaps channels; `select_guess` (184-217) branches on
  the lowest-degree pairing; `remove_matching` (125-167) propagates; an undo
  stack (91-119) rolls back. The leaf test is `subsumes_unpermuted`
  (`src/output_set.rs:370-375`) = bitmap-wise `self ⊆ other`.

  Semantics to keep straight: `A.subsumes(B)` means **A ⊆ B**, and the lemma is
  *smaller set ⇒ its bound transfers upward*: if A ⊆ B then any network sorting
  B sorts A, hence `bound(B) ≥ bound(A)`. The checker enforces exactly this
  direction (`Check.hs:118`, `Checker.thy:442`).

* **`OutputSetIndex<Dir>`** (`src/output_set/index.rs:273-622` +
  `index/tree.rs`): a cascade of k-d trees over abstraction points, each node
  augmented with `(size, [min,max] value)` (`tree.rs:29-33, 50-97`). Lookups
  prune by value range (`can_improve`) and by abstraction-range dominance
  (`test_abstraction_range`) before unpacking any bitmap
  (`index.rs:308-347`). Inserts buffer into a flat array until
  `TREE_THRESHOLD = 32` (line 14), then merge-cascade smaller trees
  (452-482) — amortised O(log N) trees. Split rule: widest abstraction
  dimension, midpoint, leaves ≤ `SPLIT_THRESHOLD = 16` (`tree.rs:3, 168-218`).

  Three directions exist: `Lower` (56-120), `LowerInvert` (122-205), `Upper`
  (207-271). **`Upper` is dead code — grep confirms it is never instantiated
  anywhere in the crate.** It is a fully written, unused half of the on-line
  subsumption machinery.

### 2.5 Where the memory actually goes

`StateMap`, `src/search/states.rs:23-152`. This is the *only* structure that
grows with the search.

* Sharding: `shards = (num_cpus² · 8).next_power_of_two()` (line 30-31) — 32,768
  shards on a 48-thread box. Shard index = FxHash of the packed bitmap
  (49-54).
* Each shard is `RwLock<OutputSetMap<State>>`, where `OutputSetMap` is **nine
  separate `BTreeMap<[u8; 2^(k-3)], State>`, one per channel count 3..11**
  (171-181). Fixed-size array keys mean no per-entry heap allocation and no
  pointer chasing; `State` is 4 bytes.
* **Nothing is ever evicted.** There is no removal path at all except
  `lock_shards` (`StateLock::drop`, 162-169). The memoisation table *is* the
  frontier, and the frontier is the entire history of the search.

Cross-check of the published figures (the arithmetic is worth trusting because
`dump_states` writes packed bitmaps and nothing else, `src/search.rs:102`):

* 93 GiB dumped ÷ 2.46e9 sets = **40.6 bytes of packed key per set on average**.
* 178 GiB resident ÷ 2.46e9 sets = **78 bytes per entry** → B-tree overhead
  factor ≈ 1.9, consistent with ~70 % node fill plus 4-byte `State` and
  alignment.

40.6 bytes/set means the population is dominated by **8–9-channel sets**
(32 and 64 bytes packed), **not** by 11-channel ones (256 bytes). In other
words the mass of the DP lives in the extremal-pruning recursion *below* the
top level (§1.3 step 3 and §1.4), not in the top-level successor layer. This
is an inference from two published aggregates, and it is the first thing the
instrumentation in §7 should confirm or refute, because it decides where
sharding and on-line subsumption should be aimed.

Secondary, bounded-size structures:

* `lock_shards` (line 25): same shape, one entry per in-flight set, removed on
  drop. Bounded by concurrency.
* `Edges` (`src/search.rs:350-362`): per-`improve`-frame. Holds an
  `FxHashMap<Arc<OutputSet>, usize>` plus one `Arc<OutputSet>` — a full dense
  2^n-byte bitmap — per successor. Up to n(n−1)/2 = 55 successors at n = 11:
  ≈110 KB per live frame; at n = 13, 78 × 8192 B = **640 KB per frame**. Frames
  are per suspended async task, and there can be many thousands.
* `ThreadPool::Pending::queue` (`src/thread_pool.rs:21-24`): `BTreeMap` of
  deferred tasks with a self-tuning GC (158-172, `next_gc = max(len,5000)·2`).
  Bounded by suspended frames, not by search size.

---

## 3. Subsumption: store-then-prune, and where on-line subsumption goes

### 3.1 The finding

**The search performs no subsumption testing whatsoever.** `grep` over `src/`
shows `OutputSetIndex`, `lookup_*_with_abstraction`,
`insert_*_with_abstraction` and `subsumes_permuted` occurring **only** in
`src/prune.rs`, `src/proof.rs`, and `src/bin/sortnetopt.rs` (the legacy `gnp`
command). Neither `src/search.rs` nor `src/search/states.rs` references any of
them. Subsumption is a strictly offline post-process.

### 3.2 Stage 1 — store everything

`Search::dump_states`, `src/search.rs:80-107`. Drains every shard and writes
each set's **packed bitmap only** into `group_{channels}_{bounds[0]}.bin`,
one file per (channel count, lower bound) pair, with the file list in
`index.txt`. The bound is carried by the *filename*; the file is a headerless
array of fixed-stride records. Upper bounds and `huffman_bounds` are discarded.
Every set ever visited is written, subsumed or not — 93 GiB at n = 11.

### 3.3 Stage 2 — offline prune

`prune::prune`, `src/prune.rs:37-113`, per group file:

1. `mmap` the group (39, 49).
2. Bucket record indices by |set| = popcount of the packed bytes, ascending
   (`BTreeMap<usize, Vec<usize>>`, 51-67).
3. For each bucket in ascending size order: a rayon-parallel filter (83-94)
   keeping only records for which
   `index.lookup_with_abstraction(...).is_none()` — i.e. no already-inserted
   set subsumes them; then a **serial** insert of the survivors via
   `insert_new_unchecked_with_abstraction` (96-106).
4. Output `.pbin`; `prune_all` (115-125) loops over `index.txt`.

Soundness: all sets in a group share the same lower bound b. If C ⊆ A (modulo
permutation and complement) and `bound(C) = b`, then `bound(A) ≥ b`, so A adds
nothing. Retaining the subsumption-minimal antichain per (channels, bound)
preserves every derivable bound. Processing buckets in ascending |set| order is
what makes one pass sufficient — a subsuming set is never larger.

Note the parallel filter tests against a *frozen* index (the index is not
mutated during the `into_par_iter`), so equal-sized sets within one bucket are
never compared to each other. A little mutual redundancy survives; this is
exactly what makes the rayon parallelism sound.

Measured effect at n = 11: 2,462,890,689 → 15,432,816 survivors — **160×**.

### 3.4 Stage 3 — certificate generation

`proof::gen_proof`, `src/proof.rs:23-73`. All `.pbin` groups for a given
channel count are loaded into **one** `OutputSetIndex<LowerInvert>` with the
bound as the stored value (41-53); §6 covers the rest.

### 3.5 Exactly where on-line subsumption plugs in

Two functions, and only two:

**Read side — `StateMap::get`, `src/search/states.rs:48-89`.** Currently an
exact FxHash + `BTreeMap` lookup on the canonical packed form; the *only* place
a bound is read. On-line lower-bound subsumption means: additionally query a
per-channel-count `OutputSetIndex<LowerInvert>` for the maximum bound over
stored sets that subsume the query, and return
`bounds[0] = max(exact, subsuming)`. Symmetrically, the already-written and
unused `Upper` direction (`index.rs:207-271`) answers "is the query a subset of
a stored set with a small upper bound", giving `bounds[1] = min(...)`.

**Write side — `StateMap::set`, `src/search/states.rs:91-104`.** The *only*
place a bound is written. On-line pruning means calling
`OutputSetIndex::insert_with_abstraction` (`index.rs:485-579`) instead of a
plain map insert. That function **already implements store-and-evict**: it
looks up the best existing value (491), then traverses the trees and the flat
buffer removing every stored entry the new one dominates (508-535, returning
`TraversalMut::Remove`; tree removal at `tree.rs:365-444`), then inserts.

It is currently exercised only by `cmd_gnp` (`src/bin/sortnetopt.rs:146, 168`),
the legacy generate-and-prune demo. **Harder built the data structure for
on-line subsumption and wired it only into the demo command, never into the
DP.** The plumbing gap is roughly 60 lines.

### 3.6 Invariants on-line subsumption must preserve

1. **Bound monotonicity.** `bounds[0]` may only increase and `bounds[1]` only
   decrease for a given set, forever. The entire `improve` protocol uses
   `state != previous_state` as a change detector (`search.rs:136-137, 150-151`)
   and `Edges` caches child-state snapshots (`search.rs:374, 392`). A
   subsumption-derived bound that could later be revised *downward* would make
   the fixpoint loops at `search.rs:229-258` and `303-344` either spin forever
   or terminate early with a wrong answer.

2. **Query monotonicity in time.** Once `get(A)` returns lower bound b it must
   never return less. `insert_with_abstraction` evicts only entries *dominated
   by* the new one, so the max over subsuming entries never decreases — the
   property holds today and must survive any sharded or out-of-core
   reimplementation (in particular: an eviction and its replacing insert must
   be atomic with respect to concurrent queries).

3. **Lock ordering.** `StateMap::lock` (`states.rs:106-144`) serialises work
   per canonical set via a `oneshot` channel, held across `.await` points. A
   subsumption index shared across sets adds a second lock. It must be taken
   strictly inside or strictly outside the per-set lock, consistently, and must
   **never** be held across an `.await` — otherwise the two deadlock. Safest
   shape: index sharded by (channels, hash), short critical sections only.

4. **Justifiability at proof time.** `GenProof::prove_all`
   (`src/proof.rs:114-141`) *panics* with `"no valid proof step found"` (137) if
   a retained set has no valid justification. `successor_step` (281-296) returns
   `None` when any successor's looked-up bound is below `bound − 1`. On-line
   subsumption changes which sets survive, so it can strand a set whose
   successors were pruned away before they reached a sufficient bound. Either
   the on-line variant must retain enough of the frontier to re-justify every
   claimed bound, or the search must record the justification at derivation
   time. **This is almost certainly what Harder meant by on-line subsumption
   "interacting badly with his bound-derivation order."** Recording
   justifications inline is the robust fix and it also makes the separate
   `prune`/`gen-proof` passes largely unnecessary.

5. **`prune_extremal_channel_into` requires genuine output sets.**
   `src/output_set.rs:500-550` is *not* the checker's simple filter. It is a BFS
   over the up-set from e_c: it seeds the queue with the singleton `mask`
   (531-532) and only reaches vectors it can arrive at by adding one bit at a
   time while staying inside the set (534-549). The checker's version
   (`Checker.thy:774-779`, `VectSet.hs:78-90`) simply filters and shifts.

   Differential test (scratch, Python, both semantics transcribed literally):
   over **3,000 random comparator networks at n ∈ {4..7}, all extremal channels
   and both polarities: 0 mismatches**. Over **20,000 arbitrary (non-output-set)
   vector sets: 45,743 / 90,108 ≈ 51 % mismatches, and the Rust result is always
   a strict subset** (0 violations of `rust ⊆ haskell` in 20,000 further trials).

   So the BFS is a valid optimisation *only* on genuinely reachable output sets,
   where the monotone-network structure guarantees a bit-at-a-time path. This
   invariant is undocumented in the source. Any modification that feeds a
   synthetic or merged vector set into this function (an intersection produced
   by interval seeding, a hand-built "generalised" set, a relaxation) will
   silently produce a *smaller* set than the checker computes. That is
   conservative for the search (smaller set ⇒ weaker bound) but it makes
   Huffman witnesses fail `is_subset_vt` at the checker, i.e. **valid-looking
   searches producing rejected certificates**. Rule: only ever pass sets
   obtained from `all_values` by `apply_comparator`,
   `prune_extremal_channel_into`, `swap_channels`, or `invert`.

---

## 4. Caching / memoisation inventory

| structure | file:line | keyed by | growth | evicted? |
|---|---|---|---|---|
| `StateMap.state_shards` | `search/states.rs:24, 171-181` | canonical packed bitmap, per channel count | **the whole search**; 2.46e9 @ n=11 | **never** |
| `StateMap.lock_shards` | `search/states.rs:25` | same | in-flight sets only | on `StateLock::drop` (162-169) |
| `Edges.target_to_id` | `search.rs:352` | `Arc<OutputSet>` | ≤ n(n−1)/2 per frame | with the frame |
| `OutputSetIndex` tree cascade | `index.rs:276-281, 452-482` | abstraction point | offline only; 15.4M @ n=11 | only via `insert_with_abstraction` |
| `GenProof.output_sets/steps/step_ids` | `proof.rs:90-92` | `Arc<OutputSet>` | 15.4M @ n=11 | never (separate process) |
| `GenProof.step_data` | `proof.rs:93` | — | 12.7M `Box<[u8]>`, one alloc each | never |
| `ThreadPool.pending.queue` | `thread_pool.rs:21-24` | `(Prio, id)` | suspended frames; self-GC at 158-172 | weak refs dropped |

Growth law from the measurements: **×12,000 per +2 channels** for the memo
table (206,279 → 2.46e9 → ~3e13). Everything else is either bounded by
concurrency or is a separate process invocation whose peak is set by the
*pruned* population (15.4M at n = 11), which is 160× smaller.

---

## 5. Parallelism

Custom pool, `src/thread_pool.rs:124-217`. Not rayon (rayon is used only in the
offline stages).

* `num_cpus::get()` OS threads (139), each running the same loop:
  1. Drain the ready queue — a crossbeam unbounded channel (147-149).
  2. Take the **global** `pending` write lock (152); ingest up to
     `pending_receiver.len() * 2` newly deferred tasks (154-180), running the
     self-tuning GC when the queue exceeds `next_gc`; then schedule the single
     highest-priority pending task and `continue 'outer` (182-189).
  3. Block on the ready queue for 10 ms (192).
* Tasks are `async_task` futures. `spawn_delayed` (83-114) creates a task that
  is **not** enqueued until `Schedule::schedule()` is called — this is the
  entire mechanism for speculative-but-deferred work.
* `unsafe transmute` widens the future's lifetime to `'static` (92-97); soundness
  rests on `ThreadPool::scope` joining all workers via a `scopeguard` (206-210).

Work distribution in the search:

* `Prio = (usize, usize, u8)` = `(level, |target|, target.bounds[0])`
  (`search.rs:28, 494-497`). `BTreeMap` ordering ⇒ **shallowest recursion level
  first, then smallest output set, then weakest lower bound.**
* `Edges::improve_next` (`search.rs:411-509`) is the fan-out point: poll all
  running children (427-439), retire closed ones (441-448), return as soon as
  *any* child finished (450), else re-sort by the heuristic (460-477) and
  (re)spawn. The rank-0 child is scheduled eagerly (504-506); the rest are only
  made *pending* (492-499), i.e. speculative work that runs when cores are idle.
* Ordering heuristics: with a `limit` (the lower-bound race), sort by
  `(bounds[0] >= limit, len, bounds[0], bounds[1])` — prefer children that
  cannot yet be dismissed and are small. Without, `(bounds[0], len, bounds[1])`.
  **These two `sort_by_key` calls at `search.rs:461` and `472` are the exact
  insertion point for ML-based expansion ordering (M3).**

Synchronisation points, in order of importance:

1. **Global `pending` `RwLock`** (`thread_pool.rs:152`) — taken by every idle
   worker, every 10 ms, in write mode. The one true global serialisation point.
2. **Per-set async lock** (`states.rs:106-144` / `search.rs:134-146`) — the
   DAG-forming dedup. Contention here is *useful* work avoided.
3. **Per-shard `RwLock`** on `state_shards[i]` — 32,768 shards keeps contention
   negligible, but every `get`/`set` still recomputes `packed_pvec()` over the
   whole dense bitmap (`states.rs:49, 92`), so the hot path is
   memory-bandwidth-bound before it is lock-bound.

No work stealing, no NUMA awareness, **no multi-machine distribution**
(`README.md:56`). Harder's HN remark that distributing would "slow it down a
lot" follows directly from `StateMap` being a globally shared random-access
table with no locality.

Offline stages use rayon: `prune.rs:83` (parallel filter over one size bucket)
and `proof.rs:127` (parallel justification of all pruned sets).

---

## 6. Certificate emission and the checker contract

### 6.1 Emission (`src/proof.rs`)

* `prove_all` (114-141): for every pruned set with its recorded bound, take the
  first justification that validates —
  `trivial_step` (232-240: bound 0, or bound 1 with the set unsorted) →
  `huffman_step` (242-279) → `successor_step` (281-297). Rayon-parallel.
  **Panics if none validates** (137).
* `huffman_step`: tries the polarity with *fewer* extremal channels first
  (253-254); prunes each extremal channel; `lookup_witness` for each; accepts if
  `max_plus_1_huffman(bounds) >= bound`.
* `successor_step`: `for i in 0..channels { for j in 0..i }`, keeping
  non-redundant comparators; requires every successor bound + 1 ≥ bound.
* `lookup_witness` (207-230): `lookup_subsuming_with_abstraction` yields
  `(bound, (invert, perm), witness_set)`. If nothing subsumes, the witness is
  `None` and the checker re-derives 0 or 1 itself (228).
* `encode_proof` (143-187): memoised DFS from the root
  (`gen_proof` calls it on `all_values(max_channels)`, line 65). A step is
  pushed only **after** all its witness steps (168-183), so witness ids are
  strictly smaller than the referring id, and the root lands last.
* `write_proof` (189-205): `u32` step count; then per step a `u64` offset and a
  `u32` length; then the payloads.

Step payload layout (matching `Decode.hs:42-78`):

```
[channels u8][bound u8][packed bitmap: 2^max(0,channels-3) bytes]
[witness kind u8: 0 = Huffman pol=false, 1 = Huffman pol=true, 2 = Successors]
then per witness:  2                                    (absent)
               |  [invert u8][perm bytes][step id u32 LE]
   perm length = channels-1 for Huffman, channels for Successors
```

`src/fix.rs:13-82` retrofits the `bound` byte into pre-format-change
certificates; it is not part of the current pipeline.

### 6.2 What the checker verifies

`checker/snocheck/src/Check.hs` is an unverified *reference* checker
(`snocheck -r`); the real one is `Verified/Checker.hs`, extracted from
`checker/verified/Checker.thy` (`snocheck -v`, `Main.hs:18-25`). Only the
extracted code plus `strict_and_parallel.patch` (evaluation order only) is
trusted.

* `check_proof` (`Checker.thy:1428-1433`): **every** step index 0..len−1 must
  pass `check_step` with `step_limit` equal to its own index.
* `check_step` (1327-1330) dispatches on the witness kind.
* `get_bound` (425-445): a witness requires `0 ≤ id < step_limit`; `perm` is a
  genuine permutation (all entries `< width`, `length = width`, `distinct`); the
  referenced step's vectors all have the right width; and
  `is_subset_vt (permute perm (invert inv B)) A` — **the transformed witness set
  must be a subset of the target set**. Absent witness ⇒ bound is 1 if the set
  is unsorted, else 0.
* `check_successors` (553-574): the checker **recomputes the comparator list
  itself** from `ocmp_list width = concat (map (λi. map (λj. (j,i)) [0..<i]) [0..<n])`
  (534) filtered by `is_redundant_cmp_vt` (515-517), and requires
  `length nrcmps = length witnesses` with positional correspondence; requires
  `bound ≠ 0` and the set unsorted; and every successor bound + 1 ≥ bound.
* `check_huffman` (906-927): recomputes
  `extremal_channels_vt A width pol = filter (...) [0..<n]` (750-752) —
  **ascending channel index** — prunes each with `prune_extremal_vt` (774-779),
  requires one witness per extremal channel positionally, all bounds defined,
  and `sucmax_value_bound_huffman bounds ≥ bound`.
* `check_proof_get_bound` (1441-1448): returns `(width, bound)` of the **last**
  step.

Top-level guarantee (`Checker_Codegen.thy:5-8`):
`check_proof_get_bound cert = Some (width, bound) ⟹ lower_size_bound (nat width) (nat bound)`,
where (`Sorting_Network_Bound.thy:36-43`)

```
partial_lower_size_bound X k = (∀cn. (∀x ∈ X. mono (fold apply_cmp cn x)) ⟶ length cn ≥ k)
lower_size_bound n k        = partial_lower_size_bound {x. fixed_len_bseq n x} k
```

### 6.3 The contract: what must remain untouched

The certificate records **only** the step DAG. It contains no upper bounds, no
`huffman_bounds`, no `StateMap`, no subsumption structure, no search order. The
checker never learns how a bound was found. Therefore the invariants are
exactly:

1. Step ids strictly increasing along witness edges (topological, acyclic).
2. The **last** step is the claim: root set = all 2^n vectors, `width = n`.
3. Successor witnesses ordered exactly as `ocmp_list` — outer `i` ascending,
   inner `j` ascending, comparator `(j, i)` — non-redundant only, positional
   1:1. Note `apply_comparator([i, j])` with `i > j` puts the *min* on channel
   `j`, matching the Isabelle `(j, i)` convention; verified against
   `is_redundant_cmp_vt`.
4. Huffman witnesses ordered by ascending extremal channel index, positional
   1:1, and the polarity byte must match the polarity used for that list.
5. Perms are genuine permutations of the right width; the permuted (optionally
   complemented) witness set is a genuine **subset**.
6. Byte layout of §6.1, `bound` at offset 1, packed length exactly
   `2^max(0, channels−3)`.

**Corollary for M2/M3: on-line subsumption, out-of-core sharding, ML expansion
ordering, and GPU kernels are all certificate-transparent.** None of them
touches the six invariants. Interval seeding is transparent too, provided seeds
only change search *order* and the final claimed bound remains justified.

**Blocker for M5, currently unremarked.** Step ids are `u32`
(`proof.rs:174`) and the step count is `u32` (`proof.rs:191`), matching
`read32LE` in `Decode.hs:19`. That caps a certificate at 2^32 ≈ 4.29e9 steps.
The n = 13 extrapolation is ~1.5e11 certificate steps
(`docs/sota-survey.md:209`) — **35× beyond what the format can express.** An
n = 13 certificate in this format is not representable. Either the container
must be widened (a checker change, hence an Isabelle change — expensive and it
breaks the "unchanged verified checker" clause of the v3 contract §5), or the
proof must be decomposed into independently-checkable per-subproblem
certificates that compose outside the verified kernel (cheaper, and the
composition argument then needs its own proof). This should be decided at M1,
not at M5.

By contrast, raising `MAX_CHANNELS` to 13 needs **no** checker change: the
checker is width-generic (`nat` arithmetic throughout,
`encodedSetLength = bit (0 max (channels-3))` at `Decode.hs:50`). All the
n = 11 hard-coding is on the Rust side (§2.2).

---

## 7. Instrumentation plan

Ground rules: counters must not change control flow, must not change which sets
are visited, and must not perturb scheduling. Use `AtomicU64` with
`Ordering::Relaxed` (or per-thread cells), and never place them inside the
shard `RwLock` critical sections.

### 7.0 Do this first — zero code change

Two facts are already obtainable without touching a line:

* `--mem-usage` exists (`bin/sortnetopt.rs:23-25`, `logging.rs:42-63`) and the
  project already carries `tools/patches/sortnetopt-macos-proc.patch` for the
  `/proc` read.
* `states: N` is logged every 10 s (`search.rs:47-56, 109-111`).
* **After any run, `dump_states` gives the exact per-(channels, bound)
  population for free**: `ls -l group_K_B.bin ÷ packed_len_for_channels(K)`.

Run n = 9 and n = 10 to completion with `--mem-usage` and census the group
files. That alone settles the §2.5 inference about where the mass lives, with
no patch and no risk.

### 7.1 Counters, by exact function and line

All in a project-owned patch applied to a detached worktree, per the
`tools/setup_sortnetopt.py` pattern (never in the pinned clone).

| metric | function | file:line | note |
|---|---|---|---|
| sets generated — successors | `Search::improve` | `search.rs:221` | inside `if target.apply_comparator(...)`, before `canonicalize` |
| sets generated — extremal prunings | `Search::improve` | `search.rs:169-176` | forced-channel path |
| sets generated — Huffman prunings | `Search::improve_huffman` | `search.rs:293-297` | separate counter |
| canonicalisations run | `OutputSet::canonicalize` | `output_set.rs:627` | pairs with the above to expose the canonical-collision rate |
| memo hit / miss | `StateMap::get` | `states.rs:56-60` | `Some` arm vs `else` |
| distinct sets stored, **per channel count** | `StateMap::set` | `states.rs:99` | `[AtomicU64; 14]`; insert-vs-update is already distinguishable from the `BTreeMap::insert` return at `states.rs:344-373` |
| `improve` invocations per level | `Search::improve` | `search.rs:127` | `level` is already a parameter |
| dedup / lock contention | `StateMap::lock` | `states.rs:114-118` | `Ok(existing)` = someone else is on it |
| Huffman evaluations | `max_plus_1_huffman` | `huffman.rs:3` | called from `search.rs:315-316` and `proof.rs:269` |
| **peak frontier per channel count** | `Search::log_stats` | `search.rs:109-111` | **highest-value single change**: make `OutputSetMap::len` (`states.rs:200-210`) return `[usize; 14]` instead of a sum and log the vector; take a running max |
| resident-bytes estimate | same | `search.rs:109` | Σ_k count_k·(2^(k−3)+4); compare with jemalloc stats |
| subsumption tests run | `OutputSet::subsumes_permuted` | `output_set.rs:377` | offline today; becomes *the* key on-line counter |
| subsumption search branches | `Subsume::search` | `subsume.rs:44, 68` | cost-model input for the GPU offload decision |
| index candidates examined vs pruned | closures in `lookup_*_with_abstraction` | `index.rs:308-347`, `380-416` | measures k-d tree effectiveness |
| prune ratio per bucket | `prune::prune` | `prune.rs:80, 108` | `subsumed_len` is already logged; add per-bucket in/out |
| certificate steps by justification kind | `GenProof::prove_all` | `proof.rs:130-133` | Trivial / NotSorted / Huffman / Successors histogram — tells you how much of the 12.7M is Huffman-derived |

### 7.2 Behaviour-preservation argument

Every entry above is a read of an already-computed value at a point where no
branch depends on the counter. The only structural edit is `OutputSetMap::len`
returning an array instead of a scalar, which is pure. `log_stats` already runs
on its own task at a fixed 10 s cadence (`search.rs:47-56`) so the extra work is
off the critical path.

Checkpoint discipline (contract §5): after instrumenting, re-run n = 9 through
`search_and_verify.sh` and require `Just (9,25)` from the **unchanged**
`snocheck`, plus a byte-identical `proof.bin` against the pre-patch run. Any
difference means the patch changed search behaviour and must be reverted.

---

## 8. Attack surface ranking

### 8.0 Where the 195× actually lives — decomposed

The 195× is 2.46e9 explored ÷ 1.27e7 certificate steps. But the middle number
is published too (`sota-survey.md:98`), and it splits the gap cleanly:

| stage | n=11 count | factor |
|---|---|---|
| sets explored and stored | 2,462,890,689 | |
| → non-subsumed (after offline `prune`) | 15,432,816 | **÷ 160** |
| → reachable from the root (certificate) | 12,659,079 | ÷ 1.22 |

**About 99.4 % of the identified waste is subsumption redundancy, and all of it
sits in `StateMap`.** That is a measured decomposition, not a conjecture, and
it fixes the ranking below. The remaining 1.22× is unreachable-from-root
material and is not worth attacking.

### 8.1 Rank 1 — on-line subsumption in `StateMap`

**Ceiling: 160× memory at n = 11. Realistic: well below that.**

*Sketch.* Add to `StateMap` a per-(channel-count, shard)
`OutputSetIndex<LowerInvert>` for lower bounds and an `OutputSetIndex<Upper>`
for upper bounds (the `Upper` impl already exists, `index.rs:207-271`).

* `StateMap::get` (`states.rs:48-89`): keep the exact `BTreeMap` lookup as the
  fast path. **Only on a miss**, or only when the exact entry's interval is
  still wide, issue the index query and widen the returned interval with
  `max`/`min`.
* `StateMap::set` (`states.rs:91-104`): route through
  `OutputSetIndex::insert_with_abstraction` (`index.rs:485-579`), which already
  performs dominated-entry eviction, and mirror the eviction into the
  `BTreeMap`.
* Record the justification (kind + witness set ids) alongside the bound at
  derivation time, so `prove_all` never strands a set (§3.6 invariant 4). This
  also makes the separate `prune`/`gen-proof` passes largely redundant.
* Validate at n = 9 first: bit-identical bound, certificate accepted by the
  unchanged `snocheck`, and the §7 counters showing the stored population
  dropping toward the 13,034 non-subsumed figure.

*Risks, in descending severity.*

1. **Abstraction cost on the hot path.** `OutputSet::abstraction`
   (`output_set.rs:438-489`) is O(n²·2^n/4) ≈ 62k inner iterations at n = 11
   versus 256 for `pack_into_slice`. Putting it on every `get` is roughly a
   **240× slowdown of the hottest operation in the search.** Mitigations:
   memoise the abstraction next to the `State` (costs 880 B/entry at n = 11 —
   *more* than the key, so only for large-channel-count entries); query the
   index only on exact-miss; incrementally update the abstraction across
   `apply_comparator`; offload abstraction + matching to GPU (this is precisely
   the compute-bound kernel the programme earmarks for the 3060s). **Measure
   this before committing to the design** — it is the most likely reason the
   idea was shelved.
2. **Justification stranding** (§3.6.4) — the failure Harder describes.
3. **Eviction/query atomicity** under concurrency (§3.6.2).
4. **Lock-order deadlock** with the per-set async lock (§3.6.3).
5. **Timing of the win.** The 160× is measured over the *final* population. A
   set can only be evicted once its subsumer exists, so transient peak memory
   will be well above the steady-state ideal. Expect the honest number to be
   somewhere in 5-30×, which is why M2's success criterion is ≥ 50× and its
   pivot rule at < 10× matters.

*Certificate impact:* none, given invariant 4 is handled (§6.3).

### 8.2 Rank 2 — out-of-core sharding of the frontier

**Does not reduce the exponent.** 20 PB of NVMe is as infeasible as 20 PB of
RAM. Its value is (a) as a *multiplier* on rank 1 — 160× on 20 PB is 125 TB,
which is a few dozen NVMe nodes rather than an impossibility — and (b) as the
only route to multi-machine execution, which the code does not support at all.

*Sketch.* The shard key already exists twice over: `OutputSetMap` is split by
channel count (`states.rs:171-181`) and `StateMap` shards by hash
(`states.rs:52-54`). Keep channel counts ≤ 8 fully resident (small and hot);
spill 9..13 to per-shard append-only files, fronted by a quotient/Bloom filter
plus an LRU page cache. Serialisation already exists and is battle-tested:
`pack_into_slice` / `from_packed` and the `group_K_B.bin` format
(`search.rs:80-107`, `prune.rs:22-35` reads it back via `mmap`).

*Risks.*

1. **Random access is the whole problem** — Harder's own diagnosis. A naive
   disk-backed map turns a 78-byte lookup into a 4 KiB page fault. The real fix
   is to *batch*: restructure `improve` so a frame emits a set of pending
   `get` requests, sorts them by shard, and resumes when the batch returns —
   a semi-external BFS. That is a substantial rewrite of the async coroutine
   structure in `search.rs:127-259` and `411-509`, and it changes the search
   *order* (though not the result).
2. **Determinism and checkpointing** (contract §5 rule 3): resumability after
   power loss requires the spill files plus an ordering log. Achievable because
   `State` is 4 bytes and the map is append-mostly, but it must be designed in,
   not retrofitted.
3. **The global `pending` lock** (`thread_pool.rs:152`) becomes a serialisation
   disaster once workers block on I/O. Expect to replace the pool.

*Certificate impact:* none.

### 8.3 Rank 3 — interval seeding

**Cheapest to implement, smallest expected win, do it first anyway** because it
is a one-line experiment that calibrates the cost model for M1.

*Sketch.* `src/search/states.rs:76`:

```rust
let known_bounds = [0, 0, 1, 3, 5, 9, 12, 16, 19, 25, 29, 35];
```

This seeds `bounds = [1, known_bounds[channels]]`. Two changes:

* Extend the table to n = 13 with the best known upper bounds (S(12) = 39,
  S(13) ≤ 45), which is required anyway to raise `MAX_CHANNELS`.
* ~~Raise the *lower* seed from the universal `1` to the best known lower bound
  for that width — for the n = 13 root that is 44 (van Voorhis from S(11) = 35),
  halving the interval the successive-approximation loop
  (`search.rs:58-68`) must close. Since S(13) ∈ {44, 45}, seeding
  `[44, 45]` means a single iteration decides the question.~~
  **WITHDRAWN 2026-08-22 — precondition permanently unsatisfiable; see the
  correction banner at the head of this file. Do not implement.**
* `--limit` (`bin/sortnetopt.rs:47`, used at `search.rs:61`) already lets the
  search stop once the lower bound reaches a target — for the S(13) ≥ 45
  question, `--limit 45` is the natural framing and it is already supported.

*Risks.*

1. **Soundness of a seeded lower bound.** A too-high lower seed produces a
   *wrong* answer silently: `improve` can close the interval by upper-bound
   descent and return the seed. The seed must be an independently proved bound.
   The 44 bound is currently *folklore* (`docs/research-programme.md:52-54`), so
   using it as a seed requires the write-up in
   `docs/s13-lower-bound-note.md` to exist and be checked first. Contract §4
   forbids ML-decided pruning; a folklore-justified seed is in the same spirit
   of hazard.
2. **The certificate must still justify the claimed bound.** A seeded bound
   that is never *derived* has no proof step, so `prove_all` will panic or the
   root step will claim a bound its witnesses do not support. Interval seeding
   is only safe as a **search-order / early-termination** device
   (`--limit`), not as a bound assertion. State this explicitly in the M3
   design.
3. **The memo table converges to the same fixed point** regardless of seeding —
   the win is in iteration count and transient population, not in the
   steady-state memory that actually kills n = 13.

### 8.4 Rank 4 (unprompted, but it is sitting there)

The dense `[bool]` bitmap (§2.1) is an 8× memory multiplier on every transient
`OutputSet`, every `Edges` frame (640 KB per frame at n = 13, §2.5), and every
`canonicalize`/`subsume` working buffer, plus an 8× memory-bandwidth cost on
`packed_pvec()` in the `StateMap` hot path. It does *not* affect `StateMap`
itself (which stores packed keys). Converting to a packed `u64` word
representation would speed up `apply_comparator`, `prune_extremal_channel_into`
and `subsumes_unpermuted` by roughly the SIMD width and cut transient memory
8×. It is mechanical, well-contained, has zero certificate impact, and would
make every subsequent experiment cheaper. It is not on the critical path for
the memory exponent, which is why it ranks below the three above — but it is
the highest ratio of benefit to risk in the whole file.

---

## Appendix: quick file map

| file | lines | role |
|---|---|---|
| `src/search.rs` | 510 | branch-and-bound DP, `improve`, `improve_huffman`, `Edges` |
| `src/search/states.rs` | 411 | `StateMap` — the memo table, sharding, per-set async lock |
| `src/output_set.rs` | 851 | `OutputSet`, comparators, packing, abstractions, extremal pruning |
| `src/output_set/canon.rs` | 441 | canonical form under S_n × complement |
| `src/output_set/subsume.rs` | 309 | permuted-subsumption via matching + propagation |
| `src/output_set/index.rs` | 622 | `OutputSetIndex<Lower|LowerInvert|Upper>`; `Upper` is dead code |
| `src/output_set/index/tree.rs` | 617 | augmented k-d tree with removal |
| `src/huffman.rs` | 14 | `max_plus_1_huffman` |
| `src/prune.rs` | 125 | offline subsumption pruning of the dumped frontier |
| `src/proof.rs` | 298 | justification search + certificate encoding |
| `src/fix.rs` | 82 | legacy certificate format upgrade |
| `src/thread_pool.rs` | 218 | custom priority thread pool with deferred scheduling |
| `checker/verified/Checker.thy` | 1485 | verified checker; `check_proof_get_bound` at 1441 |
| `checker/verified/Sorting_Network_Bound.thy` | 44 | the statement being proved |
| `checker/snocheck/src/*` | ~380 | unverified parser/translator + reference checker |
