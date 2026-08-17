# M0b: project-owned instrumentation of the sortnetopt search

Date: 2026-08-17. Contract: `METHOD_EXPERIMENT_CONTRACT_V3.md` (§5 evidence
rules; §2 pin discipline). Milestone: M0b. Status: **PASS** — instrumentation
built, validated at n=9 and n=10, decisive memo-mass measurement obtained.

Patch: `tools/patches/sortnetopt-instrumentation-v3.patch`
(SHA-256 `b0626888846b89b8cd0472f1868c1b6ab5af358af3fbd89213e7c91fa55da0d5`).

---

## 1. Provenance and build

The pinned clone `.cache/third_party/sortnetopt` was **not modified**
(`git status --porcelain` empty, tracked and untracked, after every step).

```
git -C .cache/third_party/sortnetopt worktree add --detach \
    /Users/yugendren/experiments/sorting_network_s13/.build/v3-m0b/source \
    0b5d09c47446096f9e3a0812b35afc72b7f2a718
cd .build/v3-m0b/source
patch -V none -p1 -i tools/patches/sortnetopt-macos-proc.patch
# instrumentation applied on top; exported afterwards as
patch -V none -p1 -i tools/patches/sortnetopt-instrumentation-v3.patch
cargo build --release            # rustc 1.95.0 (59807616e 2026-04-14) (Homebrew)
```

`sortnetopt-macos-large-read.patch` was not applied: it touches
`checker/snocheck/src/Main.hs` only and is irrelevant to the Rust search.

Host: M4 Mac mini (Mac16,10), 10 cores, 16 GiB, Darwin 25.5.0.
Instrumented binary SHA-256
`7066b9b2b3c6f96f4a6cb8a779c24f4fca40f1ff64956f5babe35903c2452f50`.

**Patch round-trip check.** A second, independent detached worktree was created
from the same pin, the two patches applied in order, and its `src/` tree
compared with the development tree: `diff -r` reported no differences, it built
warning-clean (one pre-existing upstream warning in `output_set/canon.rs`), and
its n=9 run reproduced `result = 25` with the same counter structure. The
worktree was then removed.

## 2. What was instrumented

New leaf module `src/instrument.rs` (relaxed `AtomicU64` statics only) plus four
call sites in `src/search.rs` and `src/search/states.rs`, and one line in
`src/lib.rs`.

| requirement | mechanism |
|---|---|
| total states inserted over the run | `SET_INSERTS`, from the `BTreeMap::insert` return value in `OutputSetMap::set_with_packed` (previously discarded) |
| current / peak `StateMap` entry count | `StateMap::census()` + `PEAK_ENTRIES` (`fetch_max`) |
| per-channel-count histogram of entries | `OutputSetMap::add_len_by_channels` → `Census` (nine O(1) `BTreeMap::len` reads per shard) |
| per-channel-count histogram of packed bytes | `Census::bytes()` = `entries[k] · 2^max(0,k−3)` |
| `StateMap::get` calls / hits / misses | `GET_CALLS`, `GET_HITS`, `GET_MISSES` |
| per bound-iteration states + new-states-added | `record_bound_iteration` in the successive-approximation loop of `Search::search` |

Free extras taken from `docs/sortnetopt-internals.md` §7.1 while the call sites
were open: `SET_UPDATES`, `LOCK_ACQUIRED`/`LOCK_CONTENDED`, `IMPROVE_CALLS`,
`IMPROVE_HUFFMAN_CALLS`, `SUCCESSORS_GENERATED`, `FORCED_PRUNINGS`,
`HUFFMAN_PRUNINGS`.

**Behaviour-preservation argument.** Every recorded value is read from an
already-computed result at a point where no branch depends on it; no counter is
ever read back by the search. The only structural edits are
(a) `set_with_packed` now returns the `BTreeMap::insert` `Option` as a `bool`
(pure; no caller branches on it), and (b) `log_stats` returns the census it
already had to compute, with the `states: N` log line byte-identical to
upstream. Counters are incremented **outside** the shard `RwLock` critical
sections (the guard is a statement temporary, dropped before `record_*`).
No allocation on any hot path.

Output: a plain-text report on **stderr** at search exit (the search's own
`log` target is stdout, so the two never interleave), plus a JSON document when
`SORTNETOPT_INSTRUMENT_JSON` names a path. Both are emitted *before*
`dump_states` consumes the map.

## 3. Validation

### 3.1 Results

| n | expected | instrumented | patch-verification worktree |
|---|---|---|---|
| 9 | 25 | **25** | 25 |
| 10 | 29 | **29** | — |

### 3.2 Bound trajectory

The search is **not deterministic**: it is a work-stealing-free but genuinely
concurrent async DAG search over 10 threads, and the number of states visited
before the interval closes varies run to run. Six baseline (portability-patched,
uninstrumented) runs and six instrumented runs were compared per n.

The **bound sequence is bit-identical** in all 24 runs:

* n=9: `5, 8, 11, 14, 17, 19, 21, 22, 23, 24, 25`
* n=10: `5, 9, 12, 15, 18, 21, 23, 25, 26, 27, 28, 29`

State counts per bound (6 runs each, min–max):

| n | bound | baseline states | instrumented states |
|---|---|---|---|
| 9 | 22 | 38–39 | 38–38 |
| 9 | 23 | 455–464 | 454–498 |
| 9 | 24 | 24,596–25,664 | 24,907–25,672 |
| 9 | 25 | 207,164–208,595 | 207,221–208,694 |
| 10 | 26 | 39–40 | 39–40 |
| 10 | 27 | 446–513 | 445–500 |
| 10 | 28 | 24,175–25,468 | 24,742–25,861 |
| 10 | 29 | 207,750–209,388 | 207,208–207,876 |

The n=10 reference trajectory in `evidence/v3/m0/n10-first-local-run.md`
(38, 479, 25,523, 207,659) lies inside the union of the two bands at every
bound. Baseline and instrumented distributions overlap at every bound. The
first eight iterations of each trajectory are exactly reproducible
(states = 1..8, one new state per iteration) in every run.

**Verdict: not bit-identical, because the unmodified search is not bit-identical
to itself.** Bound sequence, final result, and state-count distribution are
indistinguishable between instrumented and uninstrumented builds.

### 3.3 Independent cross-check of the histogram

For the canonical n=10 run, the in-process per-channel census was compared
against the zero-code-change census of the `dump_states` group files
(`ls -l group_K_B.bin ÷ 2^max(0,K−3)`, §7.0 of the internals doc):

```
k     3    4      5       6        7       8      9   10   total
in-proc  5   57   2143   36036   132614   34048   3741    1   208645
group    5   57   2143   36036   132614   34048   3741    1   208645
```

**Exact agreement in every bucket.** The instrumentation is measuring what it
claims to measure.

## 4. Instrumentation overhead

Six repetitions per configuration, alternating nothing (sequential, otherwise
idle machine). Two metrics, because process wall time is useless here (see the
note below).

| metric | n | baseline | instrumented | overhead |
|---|---|---|---|---|
| search-phase wall (s) | 9 | 0.7987 | 0.8602 | **+7.70 %** |
| search-phase wall (s) | 10 | 0.9173 | 0.9813 | **+6.98 %** |
| process user CPU (s) | 9 | 7.4367 | 7.9617 | **+7.06 %** |
| process user CPU (s) | 10 | 7.7000 | 8.0417 | **+4.44 %** |
| process wall (s) | 9, 10 | 10.04 | 10.04 | **0.00 %** |

Search-phase wall is the timestamp of the final `bounds:` log line. Run-to-run
scatter on that metric is ±8 % within a single configuration, so the honest
statement is **≈5–8 % overhead, call it 7 %**, dominated by the two
`fetch_add`s added to `StateMap::get` (3.54 M calls) and one to `StateMap::set`
(0.43 M calls).

Peak RSS: 44,564,480 B (n=9) and 42,860,544 B (n=10), against ~86 MiB recorded
for the earlier n=10 search+prune stage — no memory regression (the earlier
figure covered the prune stage too).

> **Correction to `evidence/v3/m0/n10-first-local-run.md`.** That run recorded
> "result = 29 at 10.027 s" and this task's brief carried it forward as a 10.0 s
> n=10 baseline. **The 10 s is an artifact, not search time.** `Search::search`
> spawns a stats-logger task that sleeps in 10-second increments
> (`search.rs:47-56`); `ThreadPool::scope` does not tear down until that task
> next wakes, so *every* search has a ~10 s wall floor. Verified directly:
> `sortnetopt -m search 6`, which is instantaneous, also reports
> `result = 12` at `0:10.005` with `real 10.01`. The real n=10 search cost on
> this M4 is **~0.92 s**, and n=9 is ~0.80 s. The M1 scaling law should use
> these figures, not 10 s.

## 5. Measured counters

Canonical runs: `.build/v3-m0b/runs/n{9,10}-instrumented{,.log,.err}`,
JSON at `.build/v3-m0b/json/n{9,10}-final.json`.

| counter | n=9 | n=10 |
|---|---|---|
| `get_calls` | 3,526,927 | 3,541,127 |
| `get_hits` | 2,403,600 (68.2 %) | 2,414,098 (68.2 %) |
| `get_misses` | 1,123,327 (31.8 %) | 1,127,029 (31.8 %) |
| `set_calls` | 426,442 | 428,268 |
| `set_inserts` (states inserted) | 207,881 | 208,645 |
| `set_updates` (bound refinements) | 218,561 | 219,623 |
| `lock_acquired` | 315,146 | 316,478 |
| `lock_contended` | 548 (0.17 %) | 544 (0.17 %) |
| `improve_calls` | 316,960 | 318,227 |
| `improve_huffman_calls` | 305,793 (96.5 %) | 307,016 (96.5 %) |
| `successors_generated` | 729,830 | 733,479 |
| `forced_prunings` | 8,896 | 8,993 |
| `huffman_prunings` | 2,042,228 | 2,049,194 |
| `peak_entries` | 207,881 | 208,645 |
| final entries | 207,881 | 208,645 |
| packed key bytes | 3,732,803 | 3,747,891 |
| key + `State` bytes | 4,564,327 | 4,582,471 |

**Peak equals final, exactly.** `state_shards` has no removal path at all, so
the memo table is monotone: peak entry count is always the final entry count.
Any memory-reduction scheme therefore has to introduce eviction; there is
nothing to reclaim by better timing alone.

Derived ratios (n=10):

* sets generated = 733,479 + 2,049,194 + 8,993 = **2,791,666**; distinct sets
  stored = 208,645 → **13.4× canonicalisation/dedup collapse**.
* **Huffman extremal prunings outnumber comparator successors 2.8 : 1**
  (2.05 M vs 0.73 M). The DP's work is dominated by the extremal-pruning
  recursion, not by successor expansion.
* 2.05 `set` calls per stored entry: each entry is written once on creation and
  refined ~1.05 times.
* 5.4 `get` misses per eventually-stored entry.
* Lock contention 0.17 % — the per-set async lock is not a bottleneck at this
  scale.

Per bound iteration, n=10 (`new_states` = keys created during that iteration):

| iter | lower | upper | elapsed ms | states | new states |
|---|---|---|---|---|---|
| 0–7 | 5→25 | 29 | 0–2 | 1→8 | 1 each |
| 8 | 26 | 29 | 3 | 40 | 32 |
| 9 | 27 | 29 | 5 | 441 | 401 |
| 10 | 28 | 29 | 120 | 25,919 | 25,478 |
| 11 | 29 | 29 | 913 | 208,645 | 182,726 |

**87.6 % of the memo table is created in the final iteration.** The
successive-approximation loop is not a gentle ramp; the last bound step is the
whole computation.

## 6. Where the memo mass sits

### n=10, final `StateMap` population

| channels k | entries | % entries | packed bytes | % bytes | bytes/entry |
|---|---|---|---|---|---|
| 3 | 5 | 0.002 % | 5 | 0.000 % | 1 |
| 4 | 57 | 0.027 % | 114 | 0.003 % | 2 |
| 5 | 2,143 | 1.027 % | 8,572 | 0.229 % | 4 |
| 6 | 36,036 | 17.271 % | 288,288 | 7.692 % | 8 |
| **7** | **132,614** | **63.560 %** | **2,121,824** | **56.614 %** | 16 |
| **8** | **34,048** | **16.319 %** | **1,089,536** | **29.071 %** | 32 |
| 9 | 3,741 | 1.793 % | 239,424 | 6.388 % | 64 |
| 10 | **1** | 0.000 % | 128 | 0.003 % | 128 |
| total | 208,645 | | 3,747,891 | | 17.96 |

### n=9, final `StateMap` population

| channels k | entries | % entries | packed bytes | % bytes |
|---|---|---|---|---|
| 3 | 5 | 0.002 % | 5 | 0.000 % |
| 4 | 57 | 0.027 % | 114 | 0.003 % |
| 5 | 2,137 | 1.028 % | 8,548 | 0.229 % |
| 6 | 35,965 | 17.301 % | 287,720 | 7.708 % |
| **7** | **132,140** | **63.565 %** | **2,114,240** | **56.639 %** |
| **8** | **33,836** | **16.277 %** | **1,082,752** | **29.006 %** |
| 9 | 3,741 | 1.800 % | 239,424 | 6.414 % |
| total | 207,881 | | 3,732,803 | | 

### Conclusion

**The §2.5 inference is confirmed and sharpened.**

1. **Entries** are dominated by **k = 7** (63.6 %), then k = 6 (17.3 %) and
   k = 8 (16.3 %). **Bytes** are dominated by **k = 7** (56.6 %), then
   **k = 8** (29.1 %), then k = 6 (7.7 %), then k = 9 (6.4 %).
   k = 7 and k = 8 together hold **85.7 % of the bytes and 79.9 % of the
   entries.**

2. **The top level holds nothing.** At n = 10 the memo table contains exactly
   **one** 10-channel entry: the root. The n = 10 lower bound is closed entirely
   by the van Voorhis/Huffman rule applied to the root's ten 9-channel
   extremal prunings — the successor layer at width 10 is never expanded at all.
   That is why n = 9 and n = 10 cost almost exactly the same (the earlier
   evidence noted the coincidence; this is the mechanism), and it is why
   `improve_huffman` runs on 96.5 % of `improve` calls and Huffman prunings
   outnumber successors 2.8 : 1.

3. **The mass sits at k = n−3 and k = n−2.** At n = 10 the mean packed key is
   **17.96 bytes**, between `packed_len(7) = 16` and `packed_len(8) = 32`.
   Harder's published n = 11 aggregates give 40.6 bytes/set, between
   `packed_len(8) = 32` and `packed_len(9) = 64`. Two independent measurements,
   the same rule: **the population peaks three channels below the target width
   and the byte mass is carried by widths n−3 and n−2.** Extrapolated to
   n = 13, the mass will sit at **k = 10 and k = 11** (128 and 256 packed bytes
   per key).

4. **Corollary for the n = 13 `MAX_CHANNELS` bump.** `OutputSetMap` needs arms
   for k = 12 and 13 for correctness (`get_with_packed` currently returns a
   *silent* `None`, `set_with_packed` panics — §2.2), but those two buckets will
   hold a negligible share of the population. The engineering effort belongs at
   k = 10, 11.

### What this implies for the on-line subsumption design (M2)

Aim the index at the mid-widths and nowhere else.

The decisive risk identified in §8.1 was that `OutputSet::abstraction` costs
O(k²·2^k/4) and would be ~240× the current `StateMap` key computation if put on
every `get`. That estimate was taken at the top width. The measurement says the
index only ever needs to serve widths where the population actually lives:
at n = 13 that is k = 10 and k = 11, whose abstraction costs are
90·1024/4 ≈ 23 k and 110·2048/4 ≈ 56 k inner iterations, versus 156·8192/4 ≈
320 k at k = 13. Restricting the on-line index to k ∈ {n−3, n−2} — leaving the
tiny top widths and the cheap low widths (k ≤ 6, together 8 % of bytes and 18 %
of entries at n = 10) on the existing exact `BTreeMap` fast path — captures
~86 % of the memory while cutting the worst-case abstraction cost per query by
roughly 6× relative to a uniform design, and it removes the abstraction cost
entirely from the majority of *widths* even though not from the majority of
*queries*.

Two further design consequences fall straight out of the counters. First, the
insertion path is the one to instrument-and-optimise, not the query path:
`set_inserts` is 208,645 against 3.54 M `get` calls, a **17 : 1 ratio**, so
`insert_with_abstraction` (which already does dominated-entry eviction) is
called rarely enough that its cost is affordable, while any per-`get`
abstraction is not — the "query the index only on exact miss, and only for
k ∈ {n−3, n−2}" shape is the only one the numbers support. Second, since 87.6 %
of the table is created in the last bound iteration and peak == final exactly,
subsumption that only fires at the end is worthless; it has to evict *during*
that final iteration, which means the index must be sharded per (channel count,
hash) with short critical sections, exactly as §3.6 invariant 3 requires, and
must be sound under concurrent eviction-plus-insert (invariant 2). The Huffman
path is where the entries come from — `improve_huffman` generates 2.05 M of the
2.79 M candidate sets — so the subsumption query should be placed on the
`StateMap::get` issued from `Edges::add_edge` inside `improve_huffman` first,
and only then considered for the successor path.

## 7. Artifacts

All under `.build/v3-m0b/` (build directory, not committed):

* `source/` — detached worktree at the pin, portability + instrumentation patches applied
* `sortnetopt-baseline` — portability-patched-only binary used for the overhead comparison
* `runs/n9-instrumented*`, `runs/n10-instrumented*` — canonical runs (log = stdout, err = stderr report)
* `runs/bench-{baseline,instr}-n{9,10}-{1..6}.log{,.err}` — the 24 overhead/trajectory runs
* `json/n9-final.json`, `json/n10-final.json` — machine-readable counter dumps

Committed: `tools/patches/sortnetopt-instrumentation-v3.patch`, this report.

## 8. Deviations and open items

* **Certificate checkpoint not run.** Contract §5 rule 3 requires a modified
  search to emit a certificate accepted by the unchanged `snocheck`. This patch
  adds no bound-derivation logic and the certificate pipeline (`prune-all` →
  `gen-proof` → `snocheck`) is untouched by it; `search` mode alone was run per
  the M0b brief. The full `search_and_verify` checkpoint should be run before
  any *behavioural* patch (M2 on-line subsumption) lands, and that run must use
  the Rosetta `snocheck` wrapper (see `n10-first-local-run.md` deviations).
* **Bit-identity is unattainable** for this search as written; the honest
  checkpoint criterion for M2 is "identical bound sequence and final result,
  state counts within the baseline's own run-to-run band", as applied in §3.2.
* During setup a `git worktree add` with a relative path was resolved inside the
  pinned clone, creating `.cache/third_party/sortnetopt/.build/`. It was removed
  immediately and the clone re-verified clean (`git status --porcelain` empty,
  `git worktree prune` run). **No tracked upstream file was ever touched**; the
  aggregate tracked-source hash check in `tools/setup_sortnetopt.py` still
  passes.
