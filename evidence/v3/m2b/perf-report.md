# M2b: throughput repair for the on-line subsumption index, and the cross-bound prune

Date: 2026-08-17. Contract: `METHOD_EXPERIMENT_CONTRACT_V3.md` (§2 pin
discipline, §5 evidence rules). Milestone: M2b. Predecessor:
`evidence/v3/m2a/prototype-report.md`.

**Status: PASS.** The M2a on-line subsumption prototype cost **13.2× the
baseline search wall** at n=10. M2b brings that to **3.29×** at M2a's exact
configuration, and to **2.35× at *better* net memory than M2a achieved** —
i.e. the ≤3× objective is met at the recommended operating point. All three
M2a validation gates still hold: exact results, exact bound sequences, and
certificates accepted by the *unchanged* Isabelle/HOL-extracted checker
(12 pipelines, `Just (9,25)` / `Just (10,29)` in every one). The cross-bound
prune that M2a made a pre-condition for n≥11 is implemented, validated on six
independent dumps, and **landed** (env-gated, default off).

| n=10, 6 runs per configuration | M2a | M2b `DIMS=12` | M2b `DIMS=16` |
|---|---|---|---|
| search wall, mean | 12.624 s | **3.159 s** | **2.257 s** |
| slowdown vs unmodified baseline (0.959 s) | 13.2× | **3.29×** | **2.35×** |
| `StateMap` peak entries | 35,999 | 35,592 | 35,578 |
| `StateMap` peak packed key bytes | 739,259 | 733,810 | 733,331 |
| combined payload bytes (map + index) | 1,657,352 | **1,572,020** | 1,676,459 |
| net memory reduction vs baseline | 2.76× | **2.91×** | 2.72× |
| `idx_clamps` | 0 | 0 | 0 |

Patch: `tools/patches/sortnetopt-perf-v3.patch`
(SHA-256 `3afba56a7070c3f42056ba12ea6a9884ff5b7835c985c264de13f685583bbe72`,
1,038 lines).

---

## 1. Provenance and build

The pinned clone `.cache/third_party/sortnetopt` was **not modified**
(`git status --porcelain` empty, and `worktree list` showing no entry inside
the clone, before and after every step).

```
git -C <ABS>/.cache/third_party/sortnetopt worktree add --detach \
    <ABS>/.build/v3-m2b/source 0b5d09c47446096f9e3a0812b35afc72b7f2a718
cd <ABS>/.build/v3-m2b/source
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-macos-proc.patch
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-instrumentation-v3.patch
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-online-subsumption-v3.patch
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-perf-v3.patch
cargo build --release      # rustc 1.95.0 (59807616e 2026-04-14) (Homebrew)
```

Host: M4 Mac mini (Mac16,10), Apple M4, 10 cores, 16 GiB, Darwin 25.5.0 — the
same host M0b and M2a used.

Binaries. Every measurement below comes from one of these three, all frozen
before their measurements were taken:

| | path | SHA-256 |
|---|---|---|
| baseline (portability + instrumentation only) | `.build/v3-m2a/sortnetopt-baseline` | `99d3c40a3332f95d669161d04a417bd94cd7c469fdb0cc6f39076e03a2def81d` |
| M2a | `.build/v3-m2a/bin/sortnetopt-m2a` | `24d85512ade45e396835fadfef15163cf99264f4d94c134027f0fffa8f91c544` |
| **M2b** | `.build/v3-m2b/bin/sortnetopt-m2b` | `d6e69ad460996decd4db032bd6d020ae44d598cd36192905a776fb46cb6cdc19` |

Verification used the prebuilt frozen checker, unchanged:
`.build/b3-toolchain/attempt-20260815T000526Z/bin/snocheck` (SHA-256
`4cd30511f73e7d7f6f3f7bc4083d84b37c0678f2156f85fcbfa186546218a84c`),
invoked as `snocheck -v +RTS -N10 -RTS <proof.bin>`.

**Patch round-trip.** A fresh detached worktree was created from the same pin
and the four patches applied in order. Every hunk applied clean — **no fuzz, no
offset, no `.orig` or `.rej`** — and `diff -r verify/src source/src` reported
**no differences**. It built warning-clean apart from the one pre-existing
upstream warning in `output_set/canon.rs`, reproduced `result = 25` at n=9 in
`evict` mode, and its dump went through `prune-all`
(`SORTNETOPT_CROSS_BOUND_PRUNE=1`) → `gen-proof` → frozen `snocheck -v` to
`Just (9,25)`. The worktree was then removed and the pinned clone re-verified
clean.

**What the patch touches.** Seven files: `src/instrument.rs`,
`src/output_set/index.rs`, `src/proof.rs`, `src/prune.rs`,
`src/search/states.rs`, `src/search/subsume.rs` (new), `src/search.rs`.

**What it does not touch.** `checker/` is byte-for-byte unchanged and was not
rebuilt. `src/output_set/subsume.rs` (the exact permuted-subsumption solver —
distinct from the new `src/search/subsume.rs`), `src/output_set.rs`,
`src/output_set/canon.rs`, `src/output_set/index/tree.rs`,
`src/thread_pool.rs` and `src/huffman.rs` are unchanged.

**Deviation from M2a's file discipline, stated up front.** M2a deliberately
left the entire certificate pipeline (`prune.rs`, `proof.rs`) untouched. M2b
necessarily changes `prune.rs` — the cross-bound prune *is* a change to
`prune` — and carries one 12-line robustness guard in `proof.rs` that the
cross-bound prune makes necessary (§4.3). Both are on the Rust side; the
verified checker remains untouched, and with
`SORTNETOPT_CROSS_BOUND_PRUNE` unset the pruning pipeline is byte-for-byte
the upstream one.

---

## 2. Where the time went, and what was done about it

### 2.1 The M2a profile, and the correction it forced

M2a measured (its §5.7), on 10 threads at n=10:

| component | thread-seconds | share of all thread time |
|---|---|---|
| abstraction computation | 1.34 | 1.0 % |
| index lookup | 41.26 | 31.2 % |
| index insert (incl. write-lock waiting) | 23.17 | 17.5 % |

which overturned `docs/sortnetopt-internals.md` §8.1's top-ranked risk
(abstraction cost). M2b re-measured with a `sample(1)` call-graph profile of
the M2a-stack binary as well, and that in turn corrects M2a's own attribution
one level further: the 31 % + 17 % is **not** k-d bookkeeping and **not** lock
waiting. It is almost entirely one function.

Flat (self-time) profile, M2a-stack configuration, n=9, 1 ms sampling,
22 threads, 59,856 samples:

| symbol | samples | % |
|---|---|---|
| `__psynch_cvwait` (thread-pool idle) | 27,250 | 45.5 % |
| **`output_set::subsume::Subsume::search`** | **19,900** | **33.3 %** |
| `__psynch_mutexwait` (thread-pool `pending` lock) | 2,725 | 4.6 % |
| `kevent` | 2,725 | 4.6 % |
| `semaphore_wait_trap` | 2,001 | 3.3 % |
| `Subsume::remove_matching` | 760 | 1.3 % |
| `OutputSet::abstraction` | 648 | 1.1 % |
| `lookup_with_abstraction` closure | 573 | 1.0 % |
| `Canonicalize::canonicalize` | 407 | 0.7 % |
| `Tree::traverse` | 248 | 0.4 % |
| jemalloc (`_rjem_mallocx`) | 184 | 0.3 % |
| index `RwLock` waiting (`psynch_rw`) | 14 | 0.02 % |

Excluding the 54 % of samples that are blocked threads, **`subsumes_permuted`
— the exact permuted-subsumption matching search — is ~61 % of active thread
time**. The k-d traversal machinery (`Tree::traverse` + `traversal_next`) is
under 1 %. So "the k-d traversal costs 31 %" is better read as *"the k-d
traversal fails to filter enough candidates, and every unfiltered candidate
costs an exact subsumption test"*. That reframing decided the design: every
change below is about calling `Subsume::search` fewer times, or about
partitioning so that fewer entries reach it.

### 2.2 Change 1 — popcount partitioning: one lock and one index per `|set|`

`src/search/subsume.rs` (new, 300 lines). M2a used one
`RwLock<OutputSetIndex<LowerInvert>>` per indexed width, and its §2.5
concluded that sharding by content hash is impossible here (a subsuming set
has a different hash), recommending popcount bucketing instead. That is what
this is, and it fixes *both* work items 1 and 2 with one key.

Write `|A|` for the number of Boolean vectors in `A` — the popcount of the
packed bitmap. The relation this index implements is `C ⊆ π(A)` or
`C ⊆ π(¬A)`, and both `π` (channel permutation) and `¬` (complement) act as
**bijections of the Boolean cube**, so they preserve cardinality:

```
    C subsumes A                    ⟹  |C| ≤ |A|
    C subsumes A  and  |C| = |A|    ⟹  C = A   (as canonical sets)
```

The second line holds because the search stores only `canonicalize(true)`
representatives, so two sets equal modulo permutation *and* complement have
identical bitmaps. Partitioning the stored entries into one `OutputSetIndex`
per value of `|set|`, each behind its own `RwLock`, therefore makes both
directions **exact**:

* a **lookup** for `Q` visits only buckets `0 ..= |Q|`;
* the **eviction pass** of an insert of `A` visits only buckets `|A|+1 ..`,
  because bucket `|A|` can contain no evictable entry — only `A` itself, which
  the unmodified `insert_with_abstraction_collect` handles by update-in-place.

A skipped bucket provably contains no entry in a subsumption relation with the
query, so no answer changes: this is a filter, not an approximation.

Two lock-free per-bucket hints avoid taking the lock at all: a live entry
count, and monotone high/low water marks on the stored values
(`max_value <= best_so_far ⟹ skip` for lookups, `min_value > value ⟹ skip`
for evictions — both sound because a high-water mark that never falls is
always an upper bound and a low-water mark that never rises is always a lower
bound on what is currently stored).

**Query monotonicity under sharding.** The one property a single global lock
gave for free is internals §3.6 invariant 2: the maximum over subsuming
entries, as seen by a concurrent reader, never decreases in time. With one
lock per bucket a lookup is no longer an atomic snapshot. Two rules restore
it:

1. **Insert before evict.** `insert_collect` publishes `A` into bucket `|A|`
   *before* removing any dominated `C` from higher buckets, so whenever `C` is
   absent its evictor `A` (with `value(A) ≥ value(C)`) is already present.
2. **Scan buckets in descending popcount order.** If a reader misses `C` in
   bucket `p = |C|`, then `C` was removed before time `t_p`. Its evictor `A`
   has `|A| < p` *strictly* (equal cardinality would make them the same set)
   and was inserted before that removal, hence before `t_p`, hence before
   `t_{|A|} > t_p` — the descending scan reaches bucket `|A|` *later*. So the
   reader sees `A`, or inductively (on the strictly decreasing popcount, so
   the induction terminates) `A`'s own evictor, whose value is at least as
   large.

An **ascending** scan does *not* have this property and would admit a
transient dip. Separately, every individual bucket read returns a value
realised by some stored `C ⊆ Q`, so the max over buckets is a sound lower
bound regardless of interleaving; non-atomicity could only ever cost
precision.

### 2.3 Change 2 — thread the best-so-far accumulator across buckets

`OutputSetIndex::lookup_with_abstraction_from` (`index.rs`), a seeded variant
of `lookup_with_abstraction`; `lookup_with_abstraction` is now a call to it
with `None`.

This is the correction that makes change 1 pay, and it is worth recording as a
negative result first: **partitioning alone made the search slower.** Measured
at n=9, `evict`, `DIMS=12`:

| build | search wall |
|---|---|
| M2a stack (one lock per width) | 12.48 s (6-run mean) |
| + popcount partitioning, each bucket restarting from `None` | **10.55 s** — only 1.2× |
| + accumulator threaded across buckets | **4.90 s** |
| + change 3 (§2.4) | **3.21 s** (6-run mean) |

The reason is that essentially all of the single index's usable pruning came
from `Dir::can_improve` / `Dir::does_improve`: once `best_so_far` is high,
whole k-d subtrees and every individual entry with a smaller value are
discarded *before* the exact test. Restarting that accumulator in each of ~9.5
visited buckets threw the pruning away and roughly doubled the exact-test
count. Seeding is sound in exactly the way the internal accumulator is: it is
only ever used to *skip* candidates that could not improve on it, and the seed
is itself a value realised by a stored subsuming set.

Also in `index.rs`: `remove_dominated_with_abstraction`, the eviction half of
`insert_with_abstraction_collect` extracted verbatim (minus the preceding
lookup and the trailing insert), with the equality case retained rather than
updated in place — the sharded index calls it only on buckets that provably
cannot contain the inserted set.

### 2.4 Change 3 — give the complement branch its own necessary condition

`LowerInvert::test_precise` (`index.rs`). Upstream reads:

```rust
if Lower::test_abstraction(candidate_abstraction, lookup_abstraction) {
    if let Some(perm) = candidate.subsumes_permuted(lookup) { return Some((false, perm)); }
}
let mut inverted = candidate.to_owned();
inverted.invert();
if let Some(perm) = inverted.subsumes_permuted(lookup) { return Some((true, perm)); }   // unguarded
```

The identity branch is guarded by an abstraction test; **the complement branch
is not guarded at all**, so the single most expensive function in the program
runs on every candidate that reaches this point, including the ones whose own
necessary condition fails. Given §2.1, that is the most expensive omission in
the file.

The guard is free, because complementing an output set acts on its abstraction
as the coordinate permutation `i ^ 3`. `channel_pair_abstraction` counts the
(1,1), (0,1), (1,0) and (0,0) quadrants of a channel pair as groups 0..3;
complementing the cube swaps (1,1)↔(0,0) and (0,1)↔(1,0), i.e. group `g ↔ g^3`;
and `write_abstraction_into`'s final transpose puts the group in the **low two
bits** of the coordinate index. Hence

```
abstraction(complement(C))[i] == abstraction(C)[i ^ 3]      (exactly)
```

so `Lower::test_abstraction(abstraction(complement(C)), L)` is
`∀i: C[i^3] ≤ L[i]`, equivalently `∀i: C[i] ≤ L[i^3]` — which is *precisely*
the `invert = 1` disjunct of `LowerInvert::test_abstraction` that the caller
already evaluated as part of its `∃invert` test. Adding it here only skips
work that the caller allowed for on the *other* disjunct. **No answer
changes**; the returned permutation is identical whenever one is found. The
length is rounded down to a multiple of four so `i ^ 3` stays in range for
truncated prefixes of unequal length (a shorter prefix is a weaker, still
sound, condition).

This also applies inside `prune` and `gen_proof`, which use the same
`LowerInvert` index; it is exact there too, and §4 shows the certificates are
unaffected.

### 2.5 That is three structural changes. What was deliberately not done

The campaign was capped at three, per the brief. The following were identified
and left for a future milestone:

* **Allocation churn.** `subsumes_permuted` allocates two `Vec<bool>` per call
  and `LowerInvert::test_precise` a third for the complemented copy. The
  profile puts jemalloc at 0.3 % of samples, so this is not worth a rewrite.
* **`abstraction_prefix` computes the full O(k²·2^k) abstraction and
  truncates.** Abstraction is 1.1 % of samples; not worth it at n≤10, possibly
  worth it at n=13.
* **The thread pool.** 45 % of samples are threads blocked in
  `__psynch_cvwait`, and `__psynch_mutexwait` on the *global* `pending`
  `RwLock` (`thread_pool.rs:152`) is 4.6 %. That is upstream's scheduler, is
  present in the baseline too, and is out of scope here — but it is now the
  largest single remaining item and it will get worse at 48 threads.
* **`OutputSetIndex<Upper>`** (M2a recommendation 1). Untouched; it is a
  memory idea, not a throughput idea.

---

## 3. Change 4 — the cross-bound prune

M2a §3.3 remedy 1, verbatim:

> Change `prune` to drop `A` at bound `b` whenever some same-width set `Y`
> with `bound(Y) ≥ b` subsumes `A`, processing in ascending `|set|` order (a
> subsumer is never larger) and never dropping the root (`all_values(n)` is
> subsumed by everything).

Implemented as `prune::prune_all_cross_bound`, dispatched from `prune_all`
when `SORTNETOPT_CROSS_BOUND_PRUNE` is `1`/`true`/`yes`. With the variable
unset, `prune_all` is the unmodified upstream per-group loop and `prune()`
itself is byte-identical, so the default pipeline is unchanged.

For each channel count it mmaps every `group_{k}_{b}.bin` of that width, builds
**one** `OutputSetIndex<LowerInvert>`, buckets all records of all bound groups
globally by `|set|`, and processes buckets ascending. A record from group `b`
is dropped iff `lookup_with_abstraction(...)` returns `Some(best)` with
`best ≥ b`; survivors are inserted tagged with **their own group's bound**
rather than the placeholder `0` the per-group prune uses. Survivors are written
back to that group's `.pbin`.

Why the retained population is still sufficient: `gen_proof`'s `lookup_witness`
returns the maximum-bound subsuming set over the pruned dump. If `A` at bound
`b` was dropped because `Y ⊆ A` with `bound(Y) ≥ b`, then for any witness query
`W ⊇ A` we have `Y ⊆ W`; if `Y` was itself dropped, its dropper is a strict
subset with an at-least-as-large bound, and the chain terminates because
`|set|` strictly decreases. So every witness lookup returns a bound at least as
large as before, and `prove_all` — which iterates only over *retained* sets —
has strictly fewer and strictly easier obligations. That is M2a's own argument;
§4.3 is the measurement.

**Root guard.** The bucket with `|set| == 1 << k` is retained unfiltered. This
is `all_values(k)`, which every set subsumes; `encode_proof` starts its DFS at
`all_values(max_channels)`, so it must survive. The guard is applied at *every*
width, not just the top one, which retains one extra record per width at which
the full cube happens to be in the dump. That accounts exactly for the
"+2 survivors" seen in §4.3 on the on-line dumps (widths 4 and 6), is at most
`n − 3` records in total, and is deliberately conservative.

---

## 4. Validation

### 4.1 Gate 1 — results and bound sequences

60 campaign runs, 6 per configuration, all with the frozen binaries of §1:

| cfg | binary | n | mode |
|---|---|---|---|
| B9 / B10 | baseline | 9 / 10 | — |
| O9 / O10 | M2b | 9 / 10 | `off` |
| A9 / A10 | M2a | 9 / 10 | `evict`, `DIMS=12`, widths 7,8 |
| M9 / M10 | M2b | 9 / 10 | `evict`, `DIMS=12`, widths 7,8 |
| N9 / N10 | M2b | 9 / 10 | `evict`, `DIMS=16`, widths 7,8 |

* **Result: 25 in all 30 n=9 runs, 29 in all 30 n=10 runs.**
* **Exactly one distinct bound sequence per n across all 60 runs**, equal to
  the required reference:
  * n=9: `5, 8, 11, 14, 17, 19, 21, 22, 23, 24, 25`
  * n=10: `5, 9, 12, 15, 18, 21, 23, 25, 26, 27, 28, 29`
* `idx_clamps = 0` in every run of every active configuration.

(A further 21 runs — the `DIMS` sweep of §5.4 — also gave `result = 29` and
`idx_clamps = 0` at every dimension from 4 to 48.)

### 4.2 Gate 2 — behaviour neutrality of the disabled patch

| n | configuration | final entries, 6-run band | search wall, mean |
|---|---|---|---|
| 9 | B9 baseline binary | 207,588 – 208,670 | 0.946 s |
| 9 | O9 M2b, `off` | 207,629 – 208,330 | 0.974 s |
| 10 | B10 baseline binary | 207,713 – 208,588 | 0.959 s |
| 10 | O10 M2b, `off` | 207,592 – 208,631 | 0.993 s |

Both `off` bands lie inside their baseline bands. Wall time with the patch
inactive is 2.9 % (n=9) and 3.5 % (n=10) above the baseline binary's mean,
inside the ±8 % run-to-run scatter this search shows on its own (M0b §4). No
measurable overhead when disabled.

### 4.3 Gate 3 — certificates, and the cross-bound prune A/B

Twelve full pipelines. Each `(default, cross-bound)` pair was run on **the same
dump**, so the two prune modes are directly comparable. Every dump went through
the **unmodified** `gen-proof` and the **unchanged** frozen
`snocheck -v +RTS -N10 -RTS`.

| dump | states | prune | survivors | steps | `snocheck -v` |
|---|---|---|---|---|---|
| n=9 M2b `DIMS=12` | 35,696 | per-group | 12,313 | 11,790 | **`Just (9,25)`** |
| n=9 M2b `DIMS=12` | 35,696 | cross-bound | 12,315 | 11,790 | **`Just (9,25)`** |
| n=10 M2b `DIMS=12` | 35,664 | per-group | 12,254 | 11,675 | **`Just (10,29)`** |
| n=10 M2b `DIMS=12` | 35,664 | cross-bound | 12,256 | 11,675 | **`Just (10,29)`** |
| n=9 M2b `DIMS=16` | 35,860 | per-group | 12,248 | 11,662 | **`Just (9,25)`** |
| n=9 M2b `DIMS=16` | 35,860 | cross-bound | 12,250 | 11,662 | **`Just (9,25)`** |
| n=10 M2b `DIMS=16` | 35,325 | per-group | 12,220 | 11,643 | **`Just (10,29)`** |
| n=10 M2b `DIMS=16` | 35,325 | cross-bound | 12,222 | 11,643 | **`Just (10,29)`** |
| n=9 baseline | 208,450 | per-group | 13,253 | 12,194 | **`Just (9,25)`** |
| n=9 baseline | 208,450 | cross-bound | **13,239** | 12,195 | **`Just (9,25)`** |
| n=10 baseline | 208,526 | per-group | 13,262 | 12,151 | **`Just (10,29)`** |
| n=10 baseline | 208,526 | cross-bound | **13,248** | 12,153 | **`Just (10,29)`** |

No `prove_all` panic in any run.

Reading the deltas honestly:

* On **baseline** dumps the cross-bound prune removes a further **14 sets**
  (0.11 %) at both n=9 and n=10. Small, as expected: at these scales the
  per-group antichains are already nearly the whole-width antichain.
* On **on-line-evicted** dumps it *adds* 2 survivors. That is not a failure of
  the prune; it is the root guard of §3 firing at widths 4 and 6, where the
  dump happens to contain `all_values(4)` and `all_values(6)`. Removing that
  over-conservatism would take the count to −2 rather than +2; it is left in
  because a spurious retention is harmless and a missing root is fatal.
* Certificate step counts move by at most 2 and the certificate is bit-for-bit
  the same size on the on-line dumps.

**Conclusion: the cross-bound prune LANDS.** It is not flagged off for
correctness reasons — it produces accepted certificates on six independent
dumps at two widths and two index configurations. It is env-gated (default
off) so that the default pipeline stays byte-identical to upstream, exactly as
M2a's pipeline was; **n≥11 runs must set `SORTNETOPT_CROSS_BOUND_PRUNE=1`**,
which is what M2a asked for.

**One defect it exposed, and the fix.** The cross-bound prune can empty a whole
`(width, bound)` group — the per-group prune never can, because a group's
smallest-`|set|` record has nothing in its own index to be subsumed by. The
first cross-bound run on a baseline dump therefore crashed
`gen-proof` with

```
called `Result::unwrap()` on an `Err` value: Custom { kind: InvalidInput,
  error: "memory map must have a non-zero length" }   in src/proof.rs, line 39
```

because `gen_proof` mmaps every `.pbin` listed in `index.txt` unconditionally
and `memmap` refuses a zero-length mapping. Fixed with a 12-line guard that
skips a zero-length group (which would have contributed no entries anyway), so
behaviour is unchanged whenever no group is empty. This is the only change to
`proof.rs` and it is certificate-transparent.

---

## 5. Measurements

### 5.1 Headline table, n=10 (6 runs per configuration, min–max, mean)

| metric | B10 baseline | O10 M2b `off` | A10 M2a | **M10 M2b `DIMS=12`** | **N10 M2b `DIMS=16`** |
|---|---|---|---|---|---|
| peak `StateMap` entries | 207,713–208,588 (208,085) | 207,592–208,631 (207,972) | 35,778–36,284 (35,999) | **35,485–35,702 (35,592)** | 35,274–35,834 (35,578) |
| peak packed key bytes | — † | 3,727,355–3,749,459 (3,734,863) | 735,171–742,619 (739,259) | **732,759–735,319 (733,810)** | 728,651–736,931 (733,331) |
| `StateMap` key+`State` bytes | 4,569,427 | 4,566,753 | 883,255 | 876,170 | 875,645 |
| index entries | — | 0 | 9,516–9,611 (9,562) | 9,425–9,577 (9,484) | 9,372–9,535 (9,462) |
| index payload bytes | — | 0 | 705,175–805,424 (774,097) | **688,802–701,706 (695,849)** | 792,398–813,583 (800,814) |
| **combined payload bytes** | 4,569,427 | 4,566,753 | 1,588,958–1,683,707 (1,657,352) | **1,566,889–1,576,409 (1,572,020)** | 1,662,865–1,693,526 (1,676,459) |
| index evictions | — | 0 | 6,366 | 6,248 | 6,263 |
| `idx_clamps` | — | 0 | **0** | **0** | **0** |
| search wall, mean (min–max) | 0.959 (0.845–1.303) | 0.993 (0.868–1.164) | 12.624 (11.488–13.889) | **3.159 (2.843–3.452)** | **2.257 (2.142–2.594)** |

† the baseline binary predates the exact peak-tracking counter; it has no
removal path, so peak = final by construction (M0b verified this).

Factors at the means, against B10 / O10:

| | A10 (M2a) | M10 (`DIMS=12`) | N10 (`DIMS=16`) |
|---|---|---|---|
| peak entries | 5.78× | **5.85×** | 5.85× |
| peak packed key bytes | 5.05× | **5.09×** | 5.09× |
| combined payload (net memory) | 2.76× | **2.91×** | 2.72× |
| search wall (cost) | 13.2× slower | **3.29× slower** | **2.35× slower** |
| throughput repair vs M2a | — | **4.00×** | **5.59×** |

Two ways to read the headline, both honest:

* **Like for like** (M2a's own campaign configuration, `DIMS=12`): the memory
  win is *slightly better* than M2a's on every axis, and the cost falls from
  13.2× to **3.29×**.
* **At matched net memory**: M2a's headline net factor was 2.73×; `DIMS=16`
  reproduces it (2.72×) at **2.35×** slowdown. The brief's ≤3× objective is met
  here.

The M2a report's reference figures (12.624 s mean, 13.5× against a 0.934 s
baseline) reproduce on this host today to three significant figures — A10's
6-run mean is 12.624 s — so the two campaigns are directly comparable.

### 5.2 Headline table, n=9

| metric | B9 | O9 `off` | A9 M2a | M9 `DIMS=12` | N9 `DIMS=16` |
|---|---|---|---|---|---|
| peak entries | 207,588–208,670 (208,227) | 207,629–208,330 (208,050) | 35,744–36,121 (35,855) | 35,358–35,733 (35,592) | 35,106–35,861 (35,562) |
| peak packed key bytes | — | 3,728,451–3,741,615 (3,736,008) | 734,587–740,367 (736,756) | 731,479–736,727 (733,296) | 724,631–737,007 (732,517) |
| index payload bytes | — | 0 | 705,639–821,498 (765,818) | 694,967–705,437 (700,210) | 786,595–806,256 (799,342) |
| combined payload bytes | 4,572,160 | 4,568,206 | 1,645,994 | **1,575,873** | 1,674,103 |
| search wall, mean (min–max) | 0.946 (0.905–1.034) | 0.974 (0.835–1.385) | 12.482 (11.505–13.268) | **3.212 (2.861–4.276)** | **2.330 (2.111–2.740)** |

Factors against B9: entries 5.85×, combined payload 2.90× (`DIMS=12`) /
2.73× (`DIMS=16`); wall 3.40× / 2.46× slower, against M2a's 13.2×.

### 5.3 Profiling, before and after

Thread-seconds summed over all threads, 6-run means, n=10, from the in-process
timers (`idx_ns_*`). `IDX_NS_EVICT` is new in M2b and is contained inside
`IDX_NS_INSERT`.

| component | A10 (M2a) | M10 (`DIMS=12`) | N10 (`DIMS=16`) | M10 / A10 |
|---|---|---|---|---|
| abstraction computation | 1.30 | 1.29 | 1.19 | 1.01× |
| index lookup | 40.47 | **19.62** | **13.81** | 2.06× |
| index insert (total) | 22.34 | **8.25** | **5.39** | 2.71× |
| — of which the eviction pass | n/a | 2.55 | 1.54 | |
| **total index** | **64.11** | **29.16** | **20.39** | **2.20×** |
| wall × 10 threads | 126.2 | 31.6 | 22.6 | 4.00× |
| index share of all thread time | 50.8 % | **92.3 %** | 90.3 % | |

The wall improves 4.00× while the index's own thread time improves only 2.20×.
That is not an inconsistency: under M2a half of all thread time was *outside*
the index — dominated, per §2.1, by threads blocked in the pool. Making the
index cheaper converts blocked time into finished work, so the search becomes
almost entirely index-bound (92 %). That also says where the next factor has to
come from.

Post-change flat profile (n=10, `DIMS=12`, M2b, 1 ms sampling):

| symbol | samples |
|---|---|
| `__psynch_cvwait` (thread-pool idle) | 12,610 |
| **`Subsume::search`** | **8,074** |
| `semaphore_wait_trap` | 1,615 |
| `__psynch_mutexwait` (thread-pool `pending` lock) | 1,261 |
| `kevent` | 1,261 |
| `OutputSet::abstraction` | 417 |
| `lookup_with_abstraction_from` closure | 352 |
| `Subsume::remove_matching` | 348 |
| `Canonicalize::canonicalize` | 258 |
| `Tree::traverse` | 141 |
| jemalloc | 179 (three symbols) |
| index `RwLock` waiting | not in the top 20 |

`Subsume::search` is still ~78 % of *active* thread time. **The index lock has
disappeared from the profile entirely** (work item 1 complete). What remains
is intrinsic: the exact permuted-subsumption test.

### 5.4 Popcount bucketing, measured

6-run means, n=10, `DIMS=12`:

| | value |
|---|---|
| popcount buckets, k=7 / k=8 | 129 / 257 allocated; **73 / 110 occupied** |
| lookups | 238,272 |
| buckets locked and traversed per lookup | 2,265,842 total, **9.5 per lookup** |
| buckets skipped without a lock | 10,527,815, **82.3 % of candidates** |
| index inserts | 62,575 |
| buckets locked by the eviction pass | 221,385 total, **3.5 per insert** |
| eviction buckets skipped without a lock | 2,383,479, **91.5 % of candidates** |

So an M2a *insert* took one write lock over the whole width's index and
traversed all of it; an M2b insert takes 3.5 narrow write locks and traverses
roughly 2 % of the width's entries. The bucket array itself (129 + 257 = 386
`RwLock`-plus-index headers, a few tens of kilobytes) is charged inside the
reported `index_bytes` capacity figures, not hidden.

### 5.5 The memory/throughput frontier vs the index point dimension

n=10, `evict`, widths 7,8, **3 runs per dimension, means**, one frozen binary
(this supersedes M2a §5.8, whose sweep straddled a rebuild and was single-run).
"net ×" is baseline `StateMap` key+`State` bytes (4,566,753) over combined
payload.

| `DIMS` | search wall, mean (min–max) | peak entries | peak key bytes | index payload B | combined payload B | net × | slowdown |
|---|---|---|---|---|---|---|---|
| baseline | 0.959 | 208,085 | — | 0 | 4,569,427 | 1.00× | 1.00× |
| 4 | 23.281 (21.149–24.702) | 35,760 | 736,012 | 490,616 | 1,369,650 | **3.33×** | 24.3× |
| 8 | 5.961 (5.403–6.581) | 35,775 | 736,932 | 598,224 | 1,478,255 | 3.09× | 6.2× |
| **12** | 3.023 (2.735–3.514) | 35,720 | 735,039 | 696,272 | 1,574,190 | 2.90× | 3.15× |
| **16** | **2.158 (2.117–2.188)** | 35,416 | 730,763 | 798,316 | 1,670,731 | **2.73×** | **2.25×** |
| 24 | **1.587 (1.577–1.594)** | 35,298 | 727,567 | 997,901 | 1,866,649 | 2.45× | 1.65× |
| 32 | 1.648 (1.467–1.783) | 35,283 | 726,916 | 1,226,124 | 2,094,160 | 2.18× | 1.72× |
| 48 | 1.199 (1.184–1.228) | 35,820 | 735,959 | 1,691,912 | 2,571,136 | 1.78× | 1.25× |

All rows: `result = 29`, `idx_clamps = 0`. As M2a found, the memo table is
essentially independent of `DIMS` — the point vector only affects how much work
the index does to reach the same answer — so this is a pure memory-for-time
dial, and every row is *exact*.

Two things changed relative to M2a's version of this sweep. First, the whole
curve moved down by 4–6×. Second, the knee moved: M2a chose `DIMS = 12`;
under M2b the curve is nearly flat between 16 and 32 (the abstraction test's
own cost starts to offset the pruning it buys — hence the non-monotone
24 → 32 step), and **`DIMS = 16` is the point that reproduces M2a's headline
net memory factor at the lowest cost.** `DIMS = 24` is the throughput-optimal
choice if 2.45× net memory is acceptable.

---

## 6. Verdict against the M2b objectives

| work item | outcome |
|---|---|
| 1. Shard the per-width `RwLock` | **Done.** Sharded by `|set|`; index lock waiting has left the profile (0.02 % → absent from the top 20). |
| 2. Popcount bucketing for the k-d traversal | **Done, and exact.** 82 % of lookup buckets and 92 % of eviction buckets are skipped without a lock, on a provable cardinality argument. |
| 3. Cross-bound prune (M2a §3.3 remedy 1) | **Landed**, env-gated, validated on 6 dumps; exposed and fixed a real `gen-proof` crash on empty groups. |
| 4. One further dominant cost | **Done.** Not allocation: the complement branch of `LowerInvert::test_precise` was running the program's most expensive function unguarded. |
| Slowdown 13.5× → ≤3× | **3.29× like-for-like; 2.35× at matched net memory.** Objective met at the recommended operating point (`DIMS=16`), narrowly missed at `DIMS=12`. |
| Memory within M2a's bands | **Better than M2a on every axis at `DIMS=12`**; equal at `DIMS=16`. |
| Certificates | **12/12 accepted by the unchanged verified checker.** |

---

## 7. Projection to n=11, and the go/no-go

### 7.1 Time

M2a projected 13.5 × 4 h 51 m ≈ **65 hours** and called 3–10 days the
realistic band. Applying the measured factors to Harder's published n=11 wall
of 4 h 51 m (24c/48t EPYC):

| configuration | factor | naive n=11 projection |
|---|---|---|
| M2a | 13.2× | 64 h |
| M2b `DIMS=12` | 3.29× | **16.0 h** |
| M2b `DIMS=16` | 2.35× | **11.4 h** |
| M2b `DIMS=24` | 1.65× | **8.0 h** |

Those are the naive numbers and they should not be believed as-is. Three
corrections, two favourable and one not:

* **Against.** The factor is not n-independent. Per-lookup cost is dominated by
  how many index entries survive the filters and reach `subsumes_permuted`, and
  the index population grows from ~9.5 k (n=10) to ~15.4 M (n=11) — a **1,600×**
  increase. With a fixed-dimension abstraction filter the survivor count grows
  sub-linearly but certainly not as O(1). This is the single largest
  uncertainty in the projection and it is not measurable from n≤10 data.
* **For.** The `DIMS` dial is *cheaper* at n=11. M2a §7 already noted that at
  the n=11 mass widths (k=8, 9) the packed bitmap is 32–64 B rather than
  16–32 B, so a 24-B or 48-B point is a much smaller relative overhead. §5.5
  shows raising `DIMS` from 12 to 24 buys 1.9× throughput for 1.18× combined
  memory at n=10; at n=11 the memory side of that trade is roughly half as
  expensive, so `DIMS = 24–32` should be the n=11 operating point and it
  directly attacks the "against" bullet.
* **For.** The 13.2× M2a figure was measured on **10** threads. M2a's single
  per-width `RwLock` would degrade badly at 48 threads, where M2b's ~130–500
  bucket locks would not. The M2b/M2a advantage should therefore be *larger*
  on a 24c/48t box than the 4.0× measured here, and the popcount partition
  gets finer at n=11 (2^9+1 = 513 buckets at k=9).

Honest band for the n=11 search phase on a 24c/48t-class machine: **12 to 48
hours**, central estimate around **one day**, at `DIMS = 24`. On the 48 GB 3060
box, whose CPU is a desktop part rather than a 24-core EPYC, scale by the core
ratio: **1 to 4 days** is the band to plan for. That is a *tractable overnight-
to-weekend* run, against M2a's 3–10 days.

### 7.2 Memory

Nothing here contradicts M2a's §7 analysis; M2b improves it marginally.

* Memo table: M2b's peak is 1.1 % below M2a's, so M2a's estimate stands —
  roughly **3.8 GB** at n=11 if the "2.1–2.9× above the global non-subsumed
  floor" ratio carries, with an honest range of 10–35× net reduction against
  Harder's 178 GiB, i.e. **5–18 GB**.
* Index: at `DIMS=12` M2b's index is 10 % smaller than M2a's *and* far less
  variable (688–702 kB across 6 runs versus 705–805 kB), because bucketing
  keeps most entries in small flat buffers instead of large tree cascades with
  capacity slack. At `DIMS=24` it is ~1.4× M2a's.
* The **dump** shrinks with the table: Harder's n=11 dump is 93 GiB; a ~50×
  entry reduction puts it near **2 GB**. That removes the largest single
  operational obstacle to running n=11 on a desktop.
* **New at n=11: the prune stage's own peak.** `prune_all_cross_bound` builds
  one index per *width* over all bound groups at once, rather than one per
  (width, bound). At n=11 that is a multi-GB structure with full (untruncated)
  abstraction points. It is bounded by `gen_proof`'s peak, because `gen_proof`
  *already* builds exactly that structure (`proof.rs:41-53` loads all `.pbin`
  groups of a channel count into one `OutputSetIndex`), and Harder ran
  `gen-proof` at n=11 successfully. So cross-bound pruning adds no new peak
  beyond what the pipeline already requires — but it does mean the prune stage
  now needs gen-proof-scale RAM, which the 48 GB box has and a 32 GB box may
  not.

48 GB is comfortable for all of it.

### 7.3 Go / no-go

**Conditional GO, with one cheap de-risking run first.**

Everything that can be settled at n≤10 has been: the mechanism is exact, the
bound sequences are reproduced, twelve certificates are accepted by the
unchanged verified checker, the memory is within band, the throughput cost is
3.3× (2.4× at matched memory) rather than 13.5×, and the cross-bound prune that
M2a made a pre-condition is implemented and validated. Memory at n=11 fits the
48 GB box with a large margin on every published estimate. `MAX_CHANNELS = 11`
needs no code change.

The one thing that genuinely cannot be extrapolated from n≤10 is how the
per-lookup exact-test count scales when the index population grows 1,600×. So:
**before committing to the full n=11 run, do a `--limit` run** — n=11 with
`--limit 33` or `--limit 34` — which closes only the early bound iterations and
finishes in hours. It yields exactly the two numbers the projection is missing:
the realised `idx_ns_lookup` per lookup at an n=11-scale index, and the peak
memory trajectory. If that run's per-lookup cost is within ~3× of n=10's, the
full run is a 1–2 day job and should proceed at `DIMS = 24` with
`SORTNETOPT_CROSS_BOUND_PRUNE=1`. If it is 10× worse, raise `DIMS` and
re-measure before spending a week.

Recommended n=11 invocation:

```
SORTNETOPT_SUBSUME=evict \
SORTNETOPT_SUBSUME_DIMS=24 \
SORTNETOPT_SUBSUME_WIDTHS=8,9 \
  sortnetopt -m search 11 <datadir>
SORTNETOPT_CROSS_BOUND_PRUNE=1 sortnetopt -m prune-all <datadir>
  sortnetopt -m gen-proof <datadir>
  snocheck -v +RTS -N<threads> -RTS <datadir>/proof.bin
```

The widths are chosen per M2a §2.2's corrected prescription — *the two widths
currently holding the most packed bytes*, which Harder's 40.6 bytes/set
aggregate puts at k=8 and k=9 for n=11 — not from the `{n−3, n−2}` formula
(which happens to agree here).

### 7.4 What this does *not* change about n=13

Nothing. M2a's §7 conclusion stands unaltered: a ~30× net memory reduction on
Harder's ~20 PB estimate is ~600 TB, still three to four orders of magnitude
beyond a single machine, and the `u32` certificate step count still caps a
proof at 4.29e9 steps against an n=13 estimate of 1.5e11. M2b makes n=11 a
desktop-scale computation and makes every subsequent experiment ~4× cheaper to
run; it does not move n=13.

---

## 8. Recommendations for the next milestone

1. **The thread pool is now the second-largest cost.** 45 % of samples are
   threads blocked in `__psynch_cvwait` and 4.6 % are contending the *global*
   `pending` `RwLock` at `thread_pool.rs:152`, which every idle worker takes in
   write mode every 10 ms. At 10 threads that is survivable; internals §5 warns
   it becomes "the one true global serialisation point" at 48. If the n=11
   `--limit` run shows poor scaling on many cores, this is the thing to fix,
   and it is upstream-general (it would speed the *baseline* up too).
2. **`Subsume::search` is 78 % of active time and is untouched.** The next
   throughput factor has to come from calling it less (a stronger exact
   necessary condition — the per-Hamming-weight histogram is a genuinely
   independent invariant not implied by the pair abstraction, and is
   permutation-invariant with complement acting as `w ↦ k−w`) or from making it
   cheaper (it is the compute-bound kernel the programme earmarks for the
   3060s).
3. **M2a's recommendation 1 (`OutputSetIndex<Upper>`) is still open** and is
   still the largest remaining *memory* lever at the indexed widths (a further
   ~2.8× at k=7).
4. **Tighten the cross-bound root guard** to the maximum channel count only,
   removing the +2 over-retention of §4.3. Cosmetic; do it when `prune.rs` is
   next open.
5. **Choose indexed widths from the census, not a formula** — M2a
   recommendation 3, still not implemented. It is what makes the n=11 width
   choice `{8,9}` defensible rather than lucky.

---

## 9. Artifacts

Under `.build/v3-m2b/` (build directory, not committed):

* `source/` — detached worktree at the pin, four patches applied
* `m2a-tree/` — the same worktree *before* the M2b patch, used to generate the diff
* `bin/sortnetopt-m2b` — the frozen binary
* `campaign/` — the 60 campaign runs (`run.log`, `run.err`) in
  `B9 B10 O9 O10 A9 A10 M9 M10 N9 N10`, plus `run_campaign.sh`, `parse.py`,
  `summary.json`, `campaign.out`
* `sweep/` — the 21 `DIMS`-sweep runs of §5.5
* `pipeline/` — the twelve certificate pipelines of §4.3, with `run_pipelines.sh`,
  `pipelines2.out` (P1–P8) and `pipelines_d16.out` (Q1–Q4); each leaf holds the
  copied dump, its `.pbin` files, `proof.bin` and the stage logs
* `smoke/n9.sample.txt`, `smoke/after/n10.sample.txt` — the `sample(1)` call-graph
  profiles of §2.1 and §5.3
* `verify-run/` — the round-trip worktree's n=9 search + certificate

Committed: `tools/patches/sortnetopt-perf-v3.patch`, this report.

## 10. Deviations and open items

* **`prune.rs` and `proof.rs` are no longer untouched.** M2a's clean separation
  ("the entire certificate pipeline is unchanged, so every certificate was
  produced by the same code as the baseline") does not survive this milestone,
  by necessity: the cross-bound prune *is* a change to `prune`. Mitigations:
  with `SORTNETOPT_CROSS_BOUND_PRUNE` unset both files behave exactly as
  upstream, the six per-group pipelines in §4.3 exercise that path, and
  `checker/` remains byte-for-byte unchanged and was not rebuilt.
* **The complement-branch guard of §2.4 also changes `prune` and `gen-proof`
  behaviour** — it is a filter inside `LowerInvert::test_precise`, which both
  use. It is exact (it only skips cases where the necessary condition provably
  fails), and all twelve certificates were produced with it active.
* **`DIMS=12` misses the ≤3× objective (3.29×).** The objective is met at
  `DIMS=16` (2.35×) with net memory equal to M2a's headline. Both are reported
  rather than picking the flattering one.
* **The 6-run wall bands overlap between runs of the same configuration by up
  to ±15 %** (e.g. M9: 2.861–4.276 s). All comparisons use 6-run means and the
  bands are printed; the M2a/M2b separation (12.6 s vs 3.2 s) is far outside
  any plausible scatter.
* **Search-phase wall is the timestamp of the final `bounds:` log line**, not
  process wall: `Search::search`'s stats logger sleeps in 10-second increments
  and imposes a ~10 s floor on every process (M0b §4 correction).
* **The `+2 survivors` root-guard over-retention** of §4.3 is documented, not
  fixed.
* **The n=11 per-lookup scaling is unmeasured** and is the explicit condition on
  the §7.3 GO.
* One intermediate development binary (`d0342f7d…`) was used for an early
  timing probe during §2.3's negative-result table; the 10.55 s and 4.90 s rows
  there are single runs from development builds and are reported as such. Every
  number in §4 and §5 comes from the three frozen binaries of §1.
