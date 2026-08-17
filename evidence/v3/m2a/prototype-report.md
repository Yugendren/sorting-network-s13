# M2a: on-line permutation-subsumption in the sortnetopt search

Date: 2026-08-17. Contract: `METHOD_EXPERIMENT_CONTRACT_V3.md` (§2 pin
discipline, §5 evidence rules). Milestone: M2a.

**Status: PASS as a prototype.** All three hard validation gates are met at
n=9 and n=10 — exact results, exact bound sequences, and certificates accepted
by the *unchanged* Isabelle/HOL-extracted checker. The measured wins are:

| n=10, 6 runs per configuration | reduction |
|---|---|
| `StateMap` peak entries | **5.77×** (8.15× with a wider index) |
| `StateMap` peak packed key bytes | **5.05×** (6.82×) |
| `StateMap` key + `State` bytes | **5.17×** (7.03×) |
| **resident total, counting the index itself** | **2.73×** (2.73×) |
| search wall time | **13.5× slower** (14.2×) |

The honest headline is the fourth row: on-line subsumption shrinks the memo
table by ~5–8×, but the subsumption index needed to do it is itself a
substantial data structure, so the *net* memory win at n=10 is 2.7×. That is
far below M2's ≥50× success criterion and below its <10× pivot threshold, at
n=10. §8 argues, with the measured per-entry cost model, why the net factor
should grow substantially with n, and what has to be fixed to get there.

Patch: `tools/patches/sortnetopt-online-subsumption-v3.patch`
(SHA-256 `b72f952519537ad45f16f3fc60caa850bf349473cf5984c94df36d3d9ed53036`).

---

## 1. Provenance and build

The pinned clone `.cache/third_party/sortnetopt` was **not modified**
(`git status --porcelain` empty, no stray worktrees, after every step).

```
git -C <ABS>/.cache/third_party/sortnetopt worktree add --detach \
    <ABS>/.build/v3-m2a/source 0b5d09c47446096f9e3a0812b35afc72b7f2a718
cd <ABS>/.build/v3-m2a/source
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-macos-proc.patch
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-instrumentation-v3.patch
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-online-subsumption-v3.patch
cargo build --release      # rustc 1.95.0 (59807616e 2026-04-14) (Homebrew)
```

*(Note the absolute path in `worktree add`: a relative path is resolved inside
the `-C` directory and creates `.build/` inside the pinned clone. That happened
once during this milestone, was removed immediately, and the clone re-verified
clean — `git status --porcelain` empty, `worktree prune` run, no tracked
upstream file ever touched.)*

Host: M4 Mac mini (Mac16,10), 10 cores, 16 GiB, Darwin 25.5.0.

Binaries used for every measurement below, both frozen before the campaign:

| | path | SHA-256 |
|---|---|---|
| baseline (portability + instrumentation only) | `.build/v3-m2a/sortnetopt-baseline` | `99d3c40a3332f95d669161d04a417bd94cd7c469fdb0cc6f39076e03a2def81d` |
| M2a | `.build/v3-m2a/bin/sortnetopt-m2a` | `24d85512ade45e396835fadfef15163cf99264f4d94c134027f0fffa8f91c544` |

Verification used the prebuilt frozen checker, unchanged:
`.build/b3-toolchain/attempt-20260815T000526Z/bin/snocheck -v +RTS -N10 -RTS <proof.bin>`.

**Patch round-trip.** A second detached worktree was created from the same pin,
the three patches applied in order (every hunk clean, no fuzz, no offset), and
`diff -r verify/src source/src` reported **no differences**. It built
warning-clean apart from the one pre-existing upstream warning in
`output_set/canon.rs`, and reproduced `result = 25` at n=9 in `evict` mode. The
worktree was then removed and the pinned clone re-verified clean.

**What the patch touches.** Six files:
`src/instrument.rs`, `src/output_set.rs`, `src/output_set/index.rs`,
`src/output_set/index/tree.rs`, `src/search.rs`, `src/search/states.rs`.

**What it does not touch.** `checker/` is byte-for-byte unchanged and was not
rebuilt. `src/prune.rs` and `src/proof.rs` — the entire certificate pipeline —
are unchanged, so every certificate below was produced by the same
`prune-all` → `gen-proof` code as the baseline.

---

## 2. Design

### 2.1 Where the hooks are

Two functions, exactly as `docs/sortnetopt-internals.md` §3.5 predicted, plus
one new mechanism in the index.

**Write side — `StateMap::set` (`search/states.rs`).** Before the ordinary
`BTreeMap` write, and only for the indexed widths, the set is pushed through
`OutputSetIndex::<LowerInvert>::insert_with_abstraction`. That function already
implements store-and-evict: it first looks up the best value over stored sets
that subsume the new one, returns early (without inserting) if the new value
does not improve on it, and otherwise traverses the k-d tree cascade removing
every stored entry the new one dominates. Two things are done with its result:

* the returned value is a **sound lower bound** for the set being written
  (`Y ⊆ A` modulo permutation and complement ⇒ `bound(A) ≥ bound(Y)`; this is
  the same lemma `prune.rs` and `Checker.thy:442` use), so `state.bounds[0]` is
  raised to it before the map write;
* the entries it evicted are removed from the memo table as well.

This is where the abstraction cost was put because M0b measured
`set_inserts : get_calls` at 1:17.

**Read side — `StateMap::get`.** The exact `BTreeMap` lookup is untouched and
remains the fast path. Only on an **exact-key miss**, and only at the indexed
widths, does `get` compute an abstraction and query the index, raising the
`known_bounds` seed's lower bound to the best subsuming bound. This is not an
optimisation: it is what makes eviction sound (§3).

**Eviction plumbing — `OutputSetIndex::insert_with_abstraction_collect`.**
Upstream's `insert_with_abstraction` discards the identity of what it evicts.
The patch adds a variant that reports each evicted entry's packed bitmap to a
callback, and reimplements the original as a call to it with a no-op callback,
so `cmd_gnp` is unaffected. `StateMap` uses the callback to rebuild the shard
hash and delete the corresponding memo-table entry.

**`Edges::add_edge` inside `improve_huffman`** is not modified. It reaches the
index through the ordinary `StateMap::get` it already calls — which is the
2.05-of-2.79-million candidate-set path the brief named — so the first hook
point is covered without touching `search.rs`'s control flow.

### 2.2 Restriction to two widths, and a correction to M0b

The default indexed widths are `k ∈ {n−3, n−2}`, per the brief. Everything else
stays on the existing exact-match path. Widths are overridable at run time
(`SORTNETOPT_SUBSUME_WIDTHS`) so the choice could be *measured* rather than
assumed — and it turned out to matter:

**M0b's rule "the mass sits at k = n−3 and n−2" is an artifact of n=10.** The
n=9 and n=10 memo tables are essentially the same population (M0b §6 conclusion
2: at n=10 the root is closed entirely by the Huffman rule on its ten
9-channel prunings, so n=10 *is* the n=9 computation plus one node). The mass
sits at **absolute widths 7 and 8** in both, which is `{n−2, n−1}` at n=9 and
`{n−3, n−2}` at n=10. Indexing `{6,7}` at n=9 — the brief's formula — leaves
the k=8 bucket, 68 % of the n=9 packed bytes, completely untouched, and the
entry reduction stalls at 3.72×. Indexing `{7,8}` at n=9 gives 5.76×, matching
n=10.

The robust prescription is therefore **"index the two widths currently holding
the most packed bytes"**, which the existing per-channel census already
computes; not a fixed offset from n. Harder's n=11 aggregate (40.6 bytes/set,
i.e. between `packed_len(8)=32` and `packed_len(9)=64`) is consistent with the
mass being at widths 8–9 at n=11, so the offset rule and the absolute rule
happen to agree there.

### 2.3 The index point: why the full abstraction is memory-negative

`OutputSetIndex` stores, per entry, the k-d point (the abstraction vector), the
packed bitmap, and one value byte. The abstraction has
`channels·(channels−1)·4` `u16` coordinates. Per entry:

| k | memo-table entry (packed + `State`) | full-abstraction index point | index point at `DIMS=12` |
|---|---|---|---|
| 7 | 20 B | **336 B** | 24 B |
| 8 | 36 B | **448 B** | 24 B |
| 9 | 68 B | 576 B | 24 B |
| 10 | 132 B | 720 B | 24 B |
| 11 | 260 B | 880 B | 24 B |
| 13 | 1028 B | 1248 B | 24 B |

At the widths where the memo table actually lives at n≤10, the full abstraction
is a **14–21× multiplier on the per-entry cost**, while the whole-run
subsumption ceiling is only ~15.7× (measured, §4). The arithmetic therefore
rules out a net memory win before a line of code runs, and the measurement
confirms it: at n=9 with the full abstraction, `evict` mode cut the memo table
from 4,574,783 B to 1,736,869 B but added a 3,992,256 B index — **combined
5,729,125 B, a net loss of 1.25×.**

The patch therefore adds `OutputSetIndex::new_with_point_dim`: the k-d point is
a **prefix** of the abstraction vector. This is sound, not approximate. Every
`Dir::test_abstraction*` predicate in `index.rs` is a conjunction of
per-coordinate comparisons, so restricting it to a coordinate subset is a
strictly weaker *necessary* condition; the exact arbiter
(`Dir::test_precise` = `subsumes_permuted`) is untouched. A truncated index
returns exactly the same answers as a full one and simply runs more precise
tests to get there. The prefix length is rounded to a multiple of 4 because
`LowerInvert` realises the complement symmetry as the coordinate permutation
`i ^ 3`, which must stay inside the stored prefix.

The abstraction is laid out as `channels − 1` consecutive *rank chunks* of
`channels · 4` coordinates each (rank r = the r-th largest channel-pair count
per channel per group), so a prefix keeps the most discriminating ranks.

`Tree::new` additionally `shrink_to_fit`s the staging buffers it inherits;
without that the index carries up to 2× capacity slack, which is noise in a
memory experiment.

### 2.4 Modes

Everything is behind environment variables, and with none set the search is
behaviourally identical to the instrumentation baseline (no index is allocated
and neither `get` nor `set` reaches one):

| `SORTNETOPT_SUBSUME` | behaviour |
|---|---|
| `off` (default) | baseline |
| `write` | `set` routes through `insert_with_abstraction` and adopts the returned bound |
| `writeread` | + `get` queries the index on exact-key miss |
| `evict` | + index evictions are mirrored into the memo table |

`SORTNETOPT_SUBSUME_DIMS` sets the k-d point dimension (`SORTNETOPT_SUBSUME_RANKS`
expresses the same thing in rank chunks); `SORTNETOPT_SUBSUME_WIDTHS` overrides
the indexed widths.

The modes exist so the three effects can be separated. At n=10 (single runs,
`DIMS≈32`) they decompose as:

| mode | peak entries | index payload | combined | search wall |
|---|---|---|---|---|
| `off` | 208,744 | 0 | 4,586,551 | 1.76 s |
| `write` | 81,218 | 2,236,128 | 4,273,867 | 5.79 s |
| `writeread` | 40,839 | 1,843,368 | 2,866,507 | 8.36 s |
| `evict` | 35,942 | 1,974,944 | 2,856,735 | 9.87 s |

Most of the entry reduction is **not** eviction. `write` alone — propagating
subsumption-derived lower bounds into the memo table — cuts the table 2.6×
purely by making the branch-and-bound converge faster. `writeread` adds another
2.0× by preventing sets from ever being expanded. Eviction contributes the last
1.14×. That ordering was not obvious in advance and is worth carrying into M2b.

### 2.5 Concurrency and lock discipline

One `RwLock<OutputSetIndex<LowerInvert>>` per indexed width. Sharding by
content hash is impossible here — a subsuming set has a different hash, so the
query would have to visit every shard — which is why the index is not sharded
the way `state_shards` is (§8 recommends popcount bucketing instead).

Lock ordering is acyclic by construction: `set` takes the index write lock,
releases it, then takes shard write locks; `get` takes a shard read lock,
releases it, then takes the index read lock. Neither lock is ever held across
an `.await` (both functions are synchronous), so the §3.6-invariant-3 deadlock
with the per-set async lock cannot occur. Eviction from the index and insertion
of the evictor happen inside one write-lock critical section, so the maximum
over subsuming entries never decreases as seen by a concurrent reader
(§3.6 invariant 2).

---

## 3. Soundness and the proof-justification landmine

### 3.1 Bound monotonicity

The search's whole progress protocol uses `state != previous_state` as a change
detector, so a bound that could be revised *downward* would make the fixpoint
loops spin or terminate early.

*Lower bounds.* Index values only ever move up: `insert_with_abstraction`
removes a stored `Z` only when the inserted `A` satisfies `A ⊆ Z` and
`value(A) ≥ value(Z)`, so by transitivity of subsumption
`max{value(Y) : Y in index, Y ⊆ Q}` is non-decreasing in time for every query
`Q`. An evicted memo entry's lower bound is therefore recovered, at least as
large, by the read-side hook. This is the only reason the read-side hook exists.

*Upper bounds.* An evicted entry's upper bound is **lost**; `get` falls back to
`known_bounds[k] = S(k)`, which is sound (a full k-channel sorting network sorts
any width-k output set) but wider. The cost is re-derivation, not
incorrectness, and it is bounded: a set is evicted at most once, because the
`set` call that re-creates it finds itself subsumed, takes the
`insert_with_abstraction` early return, and is therefore never in the index
again — and only index members can be evicted. Measured: 6,452 evictions
against 42,420 inserts at n=10, and `peak_entries` exceeds final entries by 6.

`idx_clamps`, the counter that fires if a subsumption-derived lower bound ever
exceeds a set's own upper bound, is **0 in all 48 campaign runs**.

### 3.2 Why the certificate survives

Claim: for every canonical set `W` and every bound `b` the search ever
attributed to `W`, the dump contains a set `E` with `E ⊆ W` (modulo permutation
and complement) and `lower(E) ≥ b`.

* *index ⊆ memo table*, always: everything inserted into the index is written to
  the map in the same `set` call, and the only removals from the map are
  evictions, which remove from the index first.
* If `b` came from an exact hit, either `W` is still in the map (`E = W`) or `W`
  was evicted, in which case its evictor `A` is in the index (hence the map)
  with `A ⊆ W`, `value(A) ≥ b`.
* If `b` came from the index fallback, `b` is realised by an index member, and
  by monotonicity it is still realised at dump time.
* Eviction chains terminate: an evictor is a strict subset (equality is handled
  by update-in-place, never removal), so `|set|` strictly decreases.

`gen_proof`'s `lookup_witness` searches for the maximum-bound subsuming set over
the pruned dump, so every `huffman_step` / `successor_step` inequality that held
during the search still holds at proof time. This is exactly the argument that
makes the existing off-line `prune` sound; on-line eviction uses the same
criterion, so it inherits it.

### 3.3 The residual risk, stated honestly

The above guarantees that evicted sets can still be *used as witnesses*. It does
**not** guarantee that every *retained* set is justifiable, and `prove_all`
panics with `"no valid proof step found"` if one is not.

The gap: a set `R` whose stored lower bound was raised by subsumption has no
derivation of its own from its own children. Normally the off-line `prune`
deletes it, because the set `Y` that supplied the bound is in the same
`(width, bound)` group and subsumes it. `R` survives only if `Y`'s bound rose
strictly above `R`'s after `R` was written, putting them in different group
files, which `prune` processes independently.

This did not occur at n=9 or n=10: `gen-proof` completed on all six validated
dumps and the verified checker accepted all six certificates. There is also
strong structural evidence that it *cannot* occur often — §5 shows the on-line
index is bit-for-bit the same population as the off-line pruned antichain at
every indexed width, i.e. the sets retained after pruning at those widths are
precisely the index members, whose values are the ones the index itself
certifies.

It remains the failure mode to watch at larger n. Two remedies, both Rust-side
only, both leaving the verified checker untouched:

1. **Cross-bound prune.** Change `prune` to drop `A` at bound `b` whenever some
   same-width set `Y` with `bound(Y) ≥ b` subsumes `A`, processing in ascending
   `|set|` order (a subsumer is never larger) and never dropping the root
   (`all_values(n)` is subsumed by everything). Sound by §3.2's argument, and
   strictly stronger than today's per-group prune.
2. **Separate derived bound.** Carry a fifth byte `derived_lower` in `State`,
   updated only by the successor/Huffman derivations, and key `dump_states`'
   group files on it rather than on the boosted `bounds[0]`.

Remedy 1 is ~30 lines and is the recommended pre-condition for any n≥11 run.

---

## 4. Validation

### 4.1 Gate 1 — results and bound sequences

48 campaign runs, 6 per configuration:

| cfg | binary | n | mode | indexed widths |
|---|---|---|---|---|
| C1 | baseline | 9 | — | — |
| C2 | baseline | 10 | — | — |
| C3 | M2a | 9 | `off` | — |
| C4 | M2a | 10 | `off` | — |
| C5 | M2a | 9 | `evict`, `DIMS=12` | 6, 7 (the `{n−3,n−2}` default) |
| C6 | M2a | 10 | `evict`, `DIMS=12` | 7, 8 (the `{n−3,n−2}` default) |
| C7 | M2a | 9 | `evict`, `DIMS=12` | 7, 8 |
| C8 | M2a | 10 | `evict`, `DIMS=12` | 6, 7, 8, 9 |

* **Result: 25 in all 24 n=9 runs, 29 in all 24 n=10 runs.**
* **Bound sequence bit-identical in all 48 runs**, and equal to the required
  reference:
  * n=9: `5, 8, 11, 14, 17, 19, 21, 22, 23, 24, 25`
  * n=10: `5, 9, 12, 15, 18, 21, 23, 25, 26, 27, 28, 29`

(The naive `grep` for `bounds:` picks up `huffman_bounds` because of greedy
matching; the sequences above were extracted with
`grep -oE "State \{ bounds: \[[0-9]+"`.)

### 4.2 Gate 2 — behaviour neutrality of the disabled patch

The active modes deliberately change the state counts, so the "within the
baseline band" criterion applies to the patch with subsumption **off**:

| n | configuration | final entries, 6-run band |
|---|---|---|
| 9 | C1 baseline binary | 207,335 – 208,650 |
| 9 | C3 M2a, `off` | 207,766 – 208,646 |
| 10 | C2 baseline binary | 207,717 – 209,212 |
| 10 | C4 M2a, `off` | 207,427 – 208,326 |
| 10 | M0b baseline (reference) | 207,750 – 209,388 |
| 10 | M0b instrumented (reference) | 207,208 – 207,876 |

C3 lies inside C1's band. C4's band lies inside the union of all four n=10
baseline observations (207,208 – 209,388); its lower endpoint is 0.14 % below
C2's, which is well inside the ±0.8 % run-to-run scatter this search shows on
its own. Wall time with the patch inactive is if anything *lower* than the
unpatched binary (0.876 s vs 0.934 s at n=10, 0.886 s vs 0.924 s at n=9), i.e.
no measurable overhead.

### 4.3 Gate 3 — certificates

Every dump below went through the **unmodified** `prune-all` → `gen-proof`, and
the **unchanged** frozen `snocheck -v +RTS -N10 -RTS`.

| cfg | states dumped | pruned survivors | certificate steps | `snocheck -v` |
|---|---|---|---|---|
| C1 (n=9 baseline) | 208,650 | 13,266 | 12,239 | **`Just (9,25)`** |
| C5 (n=9 evict, widths 6-7) | 55,884 | 12,726 | 11,834 | **`Just (9,25)`** |
| C7 (n=9 evict, widths 7-8) | 35,912 | 12,284 | 11,742 | **`Just (9,25)`** |
| C2 (n=10 baseline) | 207,717 | 13,404 | 12,305 | **`Just (10,29)`** |
| C6 (n=10 evict, widths 7-8) | 35,968 | 12,383 | 11,866 | **`Just (10,29)`** |
| C8 (n=10 evict, widths 6-9) | 25,611 | 12,018 | 11,518 | **`Just (10,29)`** |

No `prove_all` panic in any run. The certificates are ~4 % *smaller* than the
baseline's, and the pruned population is nearly unchanged — on-line eviction
discards essentially only what the off-line prune would have discarded anyway.

---

## 5. Measurements

### 5.1 Headline table, n=10 (6 runs per configuration, min–max)

| metric | C2 baseline | C4 M2a `off` | C6 evict {7,8} | C8 evict {6,7,8,9} |
|---|---|---|---|---|
| peak `StateMap` entries | 207,717 – 209,212 | 207,427 – 208,326 | **35,968 – 36,254** | **25,516 – 25,666** |
| peak packed key bytes | 3,730,515 – 3,749,283 † | 3,724,179 – 3,742,923 | **739,011 – 742,963** | **546,827 – 550,095** |
| `StateMap` key+`State` bytes | 4,561,383 – 4,593,471 | 4,553,947 – 4,576,227 | 882,987 – 887,979 | 648,991 – 652,623 |
| index entries | — | 0 | 9,513 – 9,586 | 11,856 – 11,944 |
| index payload bytes | — | 0 | 738,652 – 842,314 | 974,543 – 1,079,296 |
| **combined payload bytes** | 4,561,383 – 4,593,471 | 4,553,947 – 4,576,227 | **1,626,631 – 1,727,961** | **1,626,010 – 1,731,919** |
| index evictions | — | 0 | 6,363 – 6,731 | 7,792 – 8,020 |
| `idx_clamps` | — | 0 | **0** | **0** |
| search wall, mean (min–max) | 0.934 (0.862–0.976) | 0.876 (0.826–0.980) | 12.624 (11.868–13.274) | 13.232 (11.968–14.530) |

† the baseline has no removal path, so peak = final by construction; M0b
verified this. `peak_entries` under M2a is tracked exactly, with a `fetch_max`
on every insert, because the 10-second census would otherwise miss a peak
occurring inside a bound iteration.

Reduction factors at band midpoints, C6 against C2:

| | factor |
|---|---|
| peak entries | **5.77×** |
| peak packed key bytes | **5.05×** |
| `StateMap` key+`State` bytes | **5.17×** |
| combined with the index | **2.73×** |
| search wall (cost) | **13.5× slower** |

and C8 against C2: entries **8.15×**, packed bytes **6.82×**, key+`State`
**7.03×**, combined **2.73×**, wall **14.2× slower**. Note that C8 shrinks the
memo table a further 1.41× relative to C6 but its index grows by almost exactly
the same number of bytes, so the *combined* figure is identical to three
significant figures. Indexing more widths moves memory from the map into the
index; it does not create any.

### 5.2 Headline table, n=9

| metric | C1 baseline | C3 M2a `off` | C5 evict {6,7} | C7 evict {7,8} |
|---|---|---|---|---|
| peak entries | 207,335 – 208,650 | 207,766 – 208,646 | 55,610 – 56,064 | **35,912 – 36,341** |
| peak packed key bytes | 3,725,587 – 3,749,283 † | 3,730,307 – 3,748,639 | 1,503,885 – 1,515,485 | **737,151 – 745,779** |
| `StateMap` key+`State` bytes | 4,550,239 – 4,583,883 | 4,561,371 – 4,583,223 | 1,726,325 – 1,739,741 | 880,799 – 891,115 |
| index entries | — | 0 | 4,374 – 4,396 | 9,466 – 9,647 |
| index payload bytes | — | 0 | 299,566 – 337,067 | 729,666 – 843,911 |
| combined payload bytes | 4,550,239 – 4,583,883 | 4,561,371 – 4,583,223 | 2,030,703 – 2,076,808 | **1,616,991 – 1,735,026** |
| search wall, mean | 0.924 | 0.886 | 10.526 | 12.836 |

Factors against C1: C5 gives entries 3.72×, combined 2.22×; C7 gives entries
**5.76×**, combined **2.72×**. This is the width-choice finding of §2.2.

### 5.3 Per-channel histogram, before vs after (run 1 of each config)

**Entries**

| k | C1 (n=9 base) | C5 {6,7} | C7 {7,8} | C2 (n=10 base) | C4 `off` | C6 {7,8} | C8 {6,7,8,9} |
|---|---|---|---|---|---|---|---|
| 3 | 5 | 5 | 5 | 5 | 5 | 5 | 5 |
| 4 | 57 | 52 | 53 | 57 | 57 | 53 | 51 |
| 5 | 2,141 | 1,265 | 1,466 | 2,137 | 2,141 | 1,467 | 1,167 |
| 6 | 36,019 | **7,559** | 14,275 | 35,945 | 35,982 | 14,279 | **6,543** |
| 7 | 132,560 | **11,135** | **9,147** | 131,991 | 132,371 | **9,128** | **8,890** |
| 8 | 34,127 | 32,127 | **7,225** | 33,840 | 34,028 | **7,294** | **6,985** |
| 9 | 3,741 | 3,741 | 3,741 | 3,741 | 3,741 | 3,741 | **1,969** |
| 10 | — | — | — | 1 | 1 | 1 | 1 |
| total | 208,650 | 55,884 | 35,912 | 207,717 | 208,326 | 35,962 | 25,611 |

**Packed key bytes**

| k | C1 | C5 | C7 | C2 | C4 | C6 | C8 |
|---|---|---|---|---|---|---|---|
| 3 | 5 | 5 | 5 | 5 | 5 | 5 | 5 |
| 4 | 114 | 104 | 106 | 114 | 114 | 106 | 102 |
| 5 | 8,564 | 5,060 | 5,864 | 8,548 | 8,564 | 5,868 | 4,668 |
| 6 | 288,152 | 60,472 | 114,200 | 287,560 | 287,856 | 114,232 | 52,344 |
| 7 | 2,120,960 | 178,160 | 146,352 | 2,111,856 | 2,117,936 | 146,048 | 142,240 |
| 8 | 1,092,064 | 1,028,064 | 231,200 | 1,082,880 | 1,088,896 | 233,408 | 223,520 |
| 9 | 239,424 | 239,424 | 239,424 | 239,424 | 239,424 | 239,424 | 126,016 |
| 10 | — | — | — | 128 | 128 | 128 | 128 |

Bold entries are indexed widths. The reduction at an indexed width is 14.5×
(k=7, C6) and 4.6× (k=8, C6); un-indexed widths still shrink 2.5× (k=6) purely
because the search converges faster, and k=9 is untouched unless indexed.

### 5.4 The on-line index reaches the off-line ceiling exactly

This is the sharpest result of the milestone. For every configuration, the
number of entries in the live on-line index equals, exactly, the number of
survivors the *off-line* `prune` produces at that width:

| cfg | width | on-line index entries | off-line `.pbin` records |
|---|---|---|---|
| C5 (n=9) | 6 | 768 | 768 |
| C5 (n=9) | 7 | 3,606 | 3,606 |
| C6 (n=10) | 7 | 3,288 | 3,288 |
| C6 (n=10) | 8 | 6,298 | 6,298 |
| C7 (n=9) | 7 | 3,266 | 3,266 |
| C7 (n=9) | 8 | 6,200 | 6,200 |
| C8 (n=10) | 6 | 730 | 730 |
| C8 (n=10) | 7 | 3,180 | 3,180 |
| C8 (n=10) | 8 | 6,048 | 6,048 |
| C8 (n=10) | 9 | 1,961 | 1,961 |

So the on-line mechanism achieves the **full** subsumption ceiling at the widths
it covers — the index *is* the subsumption-minimal antichain, computed during
the search rather than after it. §8.1's risk 5 ("a set can only be evicted once
its subsumer exists, so expect well below the ceiling") turns out not to bite,
because the search's own priority order — `(level, |target|, bounds[0])`, and
`Edges::improve_next` sorting children by `len` ascending — happens to visit
smaller (hence subsuming) sets first.

The memo table nevertheless holds 9,128 entries at k=7 where the index holds
3,288. The difference, 5,840 sets, are those that were *already subsumed when
first written*: `insert_with_abstraction` took its early return, so they never
entered the index and can therefore never be evicted. They cannot simply be
dropped — see §8, recommendation 1.

### 5.5 Whole-run subsumption ceiling (the target being chased)

Off-line `prune-all` on the baseline dumps:

| n | states dumped | non-subsumed survivors | ceiling |
|---|---|---|---|
| 9 | 207,509 | 13,327 | **15.6×** |
| 10 | 208,336 | 13,246 | **15.7×** |

(consistent with Harder's published n=9 figure of 206,279 → 13,034). The
achieved entry reductions — 5.77× (C6) and 8.15× (C8) — are 37 % and 52 % of
that ceiling. Equivalently, the memo table under `evict` sits **2.9× (C6) and
2.1× (C8) above the global non-subsumed floor**, down from 15.7×.

### 5.6 Bound iterations: eviction happens where the memory is

| iter | lower | C2 states / new | C6 states / new | C8 states / new |
|---|---|---|---|---|
| 8 | 26 | 39 / 31 | 40 / 32 | 39 / 31 |
| 9 | 27 | 462 / 423 | 444 / 444 | 374 / 399 |
| 10 | 28 | 24,942 / 24,480 | 5,557 / 5,924 | 3,555 / 4,161 |
| 11 | 29 | 207,717 / 182,775 | 35,962 / 36,005 | 25,611 / 28,953 |

`new_states` exceeding live `states` in C6/C8 is the eviction signal: 36,005
keys were created in the final iteration and 35,962 survive it, so absorption
is operating *inside* the iteration that builds 88–100 % of the table, which
was the M0b requirement.

### 5.7 Throughput cost, attributed

C6 run 1: 13.21 s wall on 10 threads = 132.1 thread-seconds. Time spent under
the index, summed across threads (lock waiting included):

| component | thread-seconds | share of all thread time |
|---|---|---|
| abstraction computation | 1.34 | **1.0 %** |
| index lookup (read lock + traversal + `subsumes_permuted`) | 41.26 | **31.2 %** |
| index insert (write lock + two traversals + eviction) | 23.17 | **17.5 %** |
| total index | 65.77 | **49.8 %** |

**This overturns the top-ranked risk in `docs/sortnetopt-internals.md` §8.1.**
The abstraction cost — "roughly a 240× slowdown of the hottest operation",
identified as "the most likely reason the idea was shelved" — is 1 % of run
time. Restricting the index to two widths and moving the work to the write side
was enough to make it a non-issue. What actually costs is the k-d tree
traversal with its exact `subsumes_permuted` leaf tests, and the single
per-width `RwLock` (the insert figure includes write-lock waiting on 10
threads).

Note also that the search itself does far *less* work in `evict` mode:

| counter | C2 baseline | C6 evict |
|---|---|---|
| `get_calls` | 3,524,458 | 720,727 |
| `get_misses` | 1,123,039 | 348,914 |
| `set_calls` | 426,067 | 109,148 |
| `set_inserts` | 207,717 | 42,420 |
| `idx_lookups` | — | 241,122 |
| `idx_get_boosts` | — | 238,496 (98.9 % of lookups) |
| `idx_inserts` | — | 63,484 |
| `idx_set_boosts` | — | 27 |
| `idx_evictions` | — | 6,452 |

4.9× fewer `get` calls, yet 13.5× more wall time: the per-operation cost rose
about 66×. The read-side hook succeeds 98.9 % of the time, which is why it is
worth its cost despite being the single most expensive component.

### 5.8 Memory/throughput frontier vs the index point dimension

n=10, `evict`, single runs, sweeping `SORTNETOPT_SUBSUME_DIMS`:

| `DIMS` | peak entries | index payload B | combined payload B | net factor | search wall (s) |
|---|---|---|---|---|---|
| baseline | 207,241 | 0 | 4,547,623 | 1.00× | 1.07 |
| 4 | 36,104 | 568,660 | 1,453,035 | 3.13× | 104.2 |
| 8 | 35,980 | 649,645 | 1,530,456 | 2.97× | 21.7 |
| **12** | **35,768** | **787,363** | **1,664,498** | **2.73×** | **14.4** |
| 16 | 35,984 | 863,440 | 1,746,907 | 2.60× | 15.0 |
| 24 | 35,721 | 1,193,427 | 2,071,234 | 2.20× | 9.9 |
| 32 | 36,249 | 1,450,173 | 2,338,932 | 1.94× | 8.7 |
| 48 | 35,778 | 1,924,872 | 2,803,191 | 1.62× | 5.7 |
| 64 | 36,094 | 2,206,528 | 3,091,231 | 1.47× | 5.2 |
| 96 | 36,171 | 3,280,601 | 4,166,784 | 1.09× | 4.4 |
| 128 | 35,928 | 4,593,495 | 5,475,578 | 0.83× | 3.8 |
| full (224 @ k=8) | — | — | — | **< 1× (net loss)** | ~3.5 |

All rows gave `result = 29` and `idx_clamps = 0`. The memo table is essentially
independent of `DIMS` — the point vector affects only how much work the index
does to reach the same answer — so this is a pure memory-for-time dial.
`DIMS = 12` was chosen for the campaign as a reasonable knee. (These wall times
straddle a mid-sweep rebuild that added the timing counters; the campaign
numbers in §5.1, taken with a single frozen binary, are the authoritative ones.)

---

## 6. Verdict

**PASS as a prototype; FAIL against M2's ≥50× memory criterion at n=10.**

* Correctness: unimpeachable at the scales tested. Exact results, exact bound
  sequences, six certificates accepted by the unchanged verified checker,
  `idx_clamps = 0` in 48 runs, patch round-trips, pinned clone untouched.
* `StateMap` reduction: **5.77× entries / 5.05× packed bytes** at n=10 with the
  brief's width prescription; **8.15× / 6.82×** with four indexed widths.
* Net resident reduction, counting the index: **2.73×**.
* Throughput cost: **13.5× slower** (14.2× for four indexed widths), i.e. a
  +1250 % increase in search wall time. Zero cost when the patch is disabled.
* The on-line index attains the off-line subsumption ceiling **exactly** at every
  indexed width. The gap between 2.73× and the 15.7× whole-run ceiling is
  entirely (a) un-indexed widths, (b) already-subsumed sets that the design
  cannot drop, and (c) the index's own footprint.

---

## 7. Projection to n=11 and n=13

**n=11.** Three things move in the design's favour simultaneously:

1. The subsumption ceiling grows sharply — 15.7× at n=10, **160×** at n=11
   (Harder: 2,462,890,689 stored → 15,432,816 non-subsumed).
2. The index's relative cost falls. With a truncated 12-coordinate point the
   index entry is 24 B of point plus the packed bitmap, and the packed bitmap at
   the n=11 mass widths (k=8, 9) is 32–64 B rather than 16–32 B, so the point is
   no longer the dominant term at all.
3. Measured here, the memo table under `evict` sits 2.1–2.9× above the global
   non-subsumed floor. If that ratio carries, the n=11 table would hold roughly
   3 × 15.4M ≈ 45M entries instead of 2.46e9 — a **~55× entry reduction** — and
   at ~84 B/entry resident (40.6 B mean packed + 4 B `State`, times the ~1.9
   B-tree overhead factor Harder's figures imply) that is **≈ 3.8 GB**, plus an
   index of ~15.4M entries at ~100 B ≈ 1.5 GB. Total **≈ 5–6 GB against
   Harder's 178 GiB, i.e. ~30× net**, which would move n=11 from a 24-core
   server to a laptop and remove the 93 GiB dump entirely.

   The honest range is **10–35×**, because the "2.1–2.9× above the floor" ratio
   is measured on a search two orders of magnitude smaller than n=11 and the
   number of index members grows 1,600×, which makes each lookup more expensive
   and each eviction rarer relative to the population. Throughput is the
   bigger worry: 13.5× on Harder's 4 h 51 m gives ~65 hours, and the lookup cost
   will grow with `log(index size)` on top; 3–10 days on a 24-core box is the
   realistic band unless recommendation 2 below lands first. Before any n=11
   run, remedy 1 of §3.3 (cross-bound prune) should be implemented, because the
   justification landmine has only been tested at populations of ~13k retained
   sets.

**n=13.** Not close. 2.2e13 sets at Harder's ~20 PB; a 30× net reduction gives
~600 TB. That is still 3–4 orders of magnitude beyond a single machine and
about 1.5 orders beyond a large cluster's RAM. **M2a alone does not make n=13
feasible.** Its value at n=13 is as a *multiplier* on the out-of-core and
distributed work (internals §8.2): 600 TB of NVMe across a few dozen nodes is a
recognisable engineering project, whereas 20 PB is not. It also does nothing
about the separate, unremarked M5 blocker — the `u32` step count in the
certificate format caps a proof at 4.29e9 steps against an n=13 estimate of
1.5e11.

---

## 8. Recommendations for M2b

1. **Instantiate `OutputSetIndex<Upper>`.** The residual factor at the indexed
   widths is entirely the 5,840-of-9,128 (k=7, n=10) sets that were already
   subsumed when first written and so never entered the index. They cannot be
   dropped today because `get` would then lose their *upper* bound and return a
   reopened interval, which makes `improve`'s `state != previous_state` progress
   detector oscillate between the index-derived state and the derived one. An
   upper-bound index — already fully written at `index.rs:207-271` and never
   instantiated anywhere in the crate — lets the fallback return a *complete*
   interval, at which point those sets can be dropped and k=7 goes from 9,128
   to 3,288 (a further **2.8×**, and the whole memo table to within ~1.3× of the
   non-subsumed floor).

2. **Shard the index by popcount, not by hash.** 49.8 % of thread time is inside
   the index and much of the insert component is write-lock waiting on a single
   `RwLock` per width. A subsuming set never has more bits set, so bucketing by
   `|set|` is subsumption-compatible: a query scans buckets `0..=|A|` and an
   insert takes one narrow lock. This is what the off-line `prune` already does
   implicitly (ascending size buckets) and it is the only sharding key that
   works here.

3. **Choose indexed widths from the census, not from a formula.** `{n−3, n−2}`
   is right at n=10 and wrong at n=9 (3.72× vs 5.76×). The per-channel byte
   census already exists; pick the top two (or four) buckets at the first bound
   iteration that populates them.

4. **Land the cross-bound prune (§3.3 remedy 1) before n=11.** ~30 lines, sound,
   strictly stronger than today's per-group prune, and it closes the only
   soundness-adjacent gap this milestone leaves open.

5. **Reconsider the M2 success criterion.** The measured whole-run subsumption
   ceiling at n=9/10 is 15.7×, not 160×; the 160× is an n=11 number and grows
   with n. A criterion of "≥50×" is unreachable at n=10 *in principle*, so the
   gate should be expressed as a fraction of the measured ceiling at the n being
   tested (this milestone achieved 37–52 % of it on entries, and the index
   itself reaches 100 % of it at every width it covers).

---

## 9. Artifacts

Under `.build/v3-m2a/` (build directory, not committed):

* `source/` — detached worktree at the pin, three patches applied
* `baseline-tree/` — the same worktree *before* the M2a patch, used to generate the diff
* `sortnetopt-baseline`, `bin/sortnetopt-m2a` — the two frozen binaries
* `campaign/C1..C8/` — the 48 campaign runs (`run.log`, `run.err`,
  `counters.json`, and the `group_*.bin` / `index.txt` dumps)
* `campaign/campaign.md` — raw extraction (superseded by the tables above)
* `sweep/` — the `DIMS` sweep of §5.8
* `runs/baseline-summary.md` — the initial 6-run baseline band and the off-line
  subsumption-ceiling census of §5.5
* `smoke/` — the mode-decomposition runs of §2.4 and the full-abstraction
  memory-loss measurement

Committed: `tools/patches/sortnetopt-online-subsumption-v3.patch`, this report.

## 10. Deviations and open items

* **Gate 2 is applied to the disabled patch.** "Per-bound state counts within
  the baseline band" cannot hold for a patch whose purpose is to reduce state
  counts. It was applied to `SORTNETOPT_SUBSUME=off` (§4.2); for the active
  modes the behavioural checks are the exact result, the exact bound sequence,
  and the certificate.
* The wall times in the `DIMS` sweep (§5.8) straddle a rebuild that added the
  timing counters; §5.1's campaign figures, taken with one frozen binary in a
  single sequential run, are authoritative.
* Peak `StateMap` occupancy is now tracked exactly (a `fetch_max` on every
  insert, decremented on every eviction) rather than sampled from the 10-second
  census, because the census can miss a peak occurring inside a bound iteration
  once removals exist. Measured peak exceeds final live entries by only 6 at
  n=10, so eviction is spread out rather than bursty.
* n=11 was not run and is out of reach on this host (178 GiB baseline).
* A `git worktree add` with a path relative to the `-C` directory briefly
  created `.cache/third_party/sortnetopt/.build/`. It was removed immediately
  and the clone re-verified clean (`git status --porcelain` empty, `worktree
  prune` run, `worktree list` showing no entry inside the clone). No tracked
  upstream file was ever touched.
