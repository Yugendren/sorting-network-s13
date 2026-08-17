# Tier 1: packed-u64 bit-packing + SIMD, the weight-histogram thermometer, and index feature signatures

Date: 2026-08-17. Contract: `METHOD_EXPERIMENT_CONTRACT_V3.md` (§2 pin
discipline, §5 evidence rules). Milestone: Tier 1 (items 1–3 of
`docs/research/synthesis-ranked-queue.md`). Predecessor:
`evidence/v3/m2b/perf-report.md`.

**Status: PASS.** All four validation gates hold. Against the M2b stack at its
like-for-like configuration (`DIMS=12`) the search is **1.79× faster** at n=10
and **1.78× faster** at n=9; the isolated exact permuted-subsumption test is
**1.62× / 1.84× / 1.90× / 2.43×** faster at k = 8 / 9 / 10 / 11 — a factor that
*grows* with channel count and therefore matters more at n=11 and n=13 than it
does here. The two pre-filters together remove **33.3 %** of all exact
subsumption tests. Results, bound sequences and certificates are unchanged:
`result = 25` in all 24 n=9 runs and `29` in all 24 n=10 runs of the headline
campaign, one bound sequence per n across all 48, and five independent full
pipelines accepted by the **unchanged** frozen Isabelle/HOL-extracted checker.
**Roughly 490 million filter rejections were individually re-checked against the
exact test, across 14 audited search configurations plus the prune and gen-proof
stages, with zero disagreements.**

Two results matter more than the headline:

* **The Tier-1 advantage is largest exactly where the existing abstraction
  filter is weakest** — 5.7× at `DIMS=4`, 1.94× at `DIMS=12`, 1.05× at
  `DIMS=48` (§6.5). M2b §7.1 named "how the per-lookup exact-test count scales
  when the index population grows 1,600× at n=11" as *the single largest
  uncertainty* in its projection. That is precisely the low-effective-`DIMS`
  regime, and it is where this campaign wins most.
* **Under identical load the on-line index now costs 2.16–2.28× the unmodified
  baseline search, against M2b's 3.97–4.03× measured in the same window**
  (§6.4) — while still delivering a 2.70× net memory reduction.

The honest cost: the stored 64-bit signature adds **8 bytes per index entry**
plus 16 bytes per k-d node — **+6.6 %** combined payload and **1.15×** peak RSS
at n=10. §7 gives the operating point that buys it back.

> **All wall-clock numbers in this report were measured under heavy load.** A
> full n=11 search (`sortnetopt-m2b -m search 11`, 10 threads) occupied this
> machine for the entire campaign; load average ran 19–56 on a 10-core host.
> Timings are **indicative only**. §8 gives exact re-measurement commands for
> replay on a quiet machine. The load-*robust* evidence — counter ratios,
> exact-call counts, the interleaved single-threaded microbenchmark, and every
> correctness and memory figure — is what the conclusions rest on, and is
> marked as such throughout.

Patch: `tools/patches/sortnetopt-tier1-v3.patch`
(SHA-256 `5b6f180a24dce2b663b19134d923dc31815036deed3d4d8c1c1895e61db7ef3e`,
3,486 lines).

---

## 1. Provenance and build

The pinned clone `.cache/third_party/sortnetopt` was **not modified**
(`git status --porcelain` empty and `worktree list` showing no entry inside the
clone, before and after every step).

```
git -C <ABS>/.cache/third_party/sortnetopt worktree add --detach \
    <ABS>/.build/v3-tier1/source 0b5d09c47446096f9e3a0812b35afc72b7f2a718
cd <ABS>/.build/v3-tier1/source
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-macos-proc.patch
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-instrumentation-v3.patch
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-online-subsumption-v3.patch
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-perf-v3.patch
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-tier1-v3.patch
cargo build --release
```

Host: M4 Mac mini (Mac16,10), Apple M4, 10 cores, 16 GiB, Darwin 25.5.0 — the
same host M0b, M2a and M2b used.

Binaries, all frozen before any measurement was taken:

| | path | SHA-256 |
|---|---|---|
| unmodified-search baseline | `.build/v3-m2a/sortnetopt-baseline` | `99d3c40a3332f95d669161d04a417bd94cd7c469fdb0cc6f39076e03a2def81d` |
| M2b reference (4-patch stack) | `.build/v3-tier1/bin/sortnetopt-m2b-ref` | `ce64495448b78e76058ac47543a73b61a6192c094ff2aeffb7bf60fdfdaf242b` |
| **Tier 1** (5-patch stack) | `.build/v3-tier1/bin/sortnetopt-tier1` | `931619109aecbb6a2ade046b8c3b5e36580f2d55712f9079aaa9da7da31e613a` |

Verification used the prebuilt frozen checker, unchanged:
`.build/b3-toolchain/attempt-20260815T000526Z/bin/snocheck` (SHA-256
`4cd30511f73e7d7f6f3f7bc4083d84b37c0678f2156f85fcbfa186546218a84c`), invoked as
`snocheck -v +RTS -N10 -RTS <proof.bin>`.

**Patch round-trip.** A fresh detached worktree was created from the same pin and
all five patches applied in order. Every hunk applied clean — **no fuzz, no
offset, no `.orig` or `.rej`** — and `diff -r verify/src source/src` reported
**no differences**. It built with only the one pre-existing upstream warning in
`output_set/canon.rs`, reproduced `result = 25` at n=9 with the reference bound
sequence, and its dump went through `prune-all`
(`SORTNETOPT_CROSS_BOUND_PRUNE=1`) → `gen-proof` → frozen `snocheck -v` to
**`Just (9,25)`**. The worktree was then removed and the pinned clone
re-verified clean.

**What the patch touches.** Ten files: `src/bin/sortnetopt.rs`,
`src/instrument.rs`, `src/output_set.rs`, `src/output_set/index.rs`,
`src/output_set/index/tree.rs`, `src/output_set/packed.rs` (new),
`src/output_set/subsume.rs`, `src/proof.rs`, `src/prune.rs`,
`src/search/subsume.rs`.

**What it does not touch.** `checker/` is byte-for-byte identical to the pin
(verified by `diff -r`) and was not rebuilt. `src/search.rs`,
`src/search/states.rs`, `src/output_set/canon.rs`, `src/thread_pool.rs`,
`src/huffman.rs` and `src/fix.rs` are unchanged.

---

## 2. Change 1 — packed u64 + SIMD

### 2.1 What the byte-per-vector representation was costing

`OutputSet<Bitmap>` stores one `bool` — one byte — per Boolean vector, so a
k-channel set is 2^k bytes: 256 B at k=8, 2 KB at k=11. Three things in the hot
path walk that array end to end:

* `Subsume::search`'s leaf test `subsumes_unpermuted` — 2^k byte loads;
* `Subsume::move_unique` / `rollback` — `swap_channels`, O(2^k) byte swaps, run
  twice per fixed channel per search node;
* `Subsume::filter_matching` — `low_channels_channel_abstraction`, O(2^k) per
  channel, run for `2·(channels − fixed_channels)` channels per search node;

and, at the boundary, `OutputSetIndex`'s traversal `action` closure called
`candidate_output_set.unpack_from_slice(packed_candidate)` — a full 2^k-byte
expansion of the stored packed key — for **every** candidate that survived the
value and abstraction tests, before it could even compare it for equality.
M2b measured `Subsume::search` at ~78 % of active thread time, so this is the
right target.

### 2.2 `PackedSet`

`src/output_set/packed.rs` (new) provides `PackedSet`: bit `i` of the bitmap in
word `i >> 6` at bit position `i & 63`, in a `[u64; 32]` (2^11 / 64 = 32). This
is exactly `pack_into_slice`'s byte layout on a little-endian machine, so
building a `PackedSet` from a stored index key is a `memcpy`, not a decode.

| operation | byte representation | packed |
|---|---|---|
| `subsumes_unpermuted` | 2^k byte loads | 2^k/64 words; on aarch64 an explicit NEON path, 2 words (128 bits) per iteration, `AND`-with-`MVN` accumulated by `ORR`, scalar tail; portable scalar fallback compiled everywhere else |
| `swap_channels` | 2^k/2 byte swaps | three cases: both bit positions in-word → Hacker's-Delight delta swap per word; one in-word, one word-index → word-pair blend; both word-index → word permutation |
| `invert` | `bitmap.reverse()`, 2^k bytes | `reverse_bits()` per word plus word-order reversal |
| `weight_histogram` | 2^k byte loads + popcount per index | for each word `j`: `hist[popcount(j) + t] += (bits[j] & INWORD[t]).count_ones()`, t in 0..=6, where `INWORD[t]` is the 64-bit mask of in-word positions of popcount t — a 7-entry table, no per-channel-count table at all |
| `low_channels_channel_abstraction` | 2^(k−1) iterations, ~6 ops each | masked popcounts over group masks (§2.3) |

NEON is baseline on every aarch64 target, so no runtime feature detection is
needed; the scalar path is kept and separately unit-tested, so x86 builds are
unaffected.

`Subsume` now holds `[PackedSet; 2]` instead of `[OutputSet<Vec<bool>>; 2]` and
performs **no heap allocation at all** (it previously allocated two `Vec<bool>`
per exact test via `to_owned()`).

Every operation is unit-tested against the corresponding `OutputSet` method as
oracle, for every channel count 1..=11, every channel pair, and every
`(low_channels, channel)` combination, on pseudo-random comparator-chain corpora
including the all-ones and very sparse edge cases.

### 2.3 The abstraction, by group masks

`low_channels_channel_abstraction` buckets index positions by
`(i & low_mask, popcount(i & high_mask))`. Writing `i = 64j + b`, the bucket
splits as
`low = (b & low_in_word) | ((j & (low_mask>>6)) << 6)` and
`hw = popcount(b & high_in_word) + popcount(j & (high_mask>>6))`,
so the 64 in-word positions can be grouped once by `(low_b, hw_b)` and each
group's contribution taken with three masked popcounts instead of 64 byte reads.
A per-word density test picks between that group loop and a `trailing_zeros`
set-bit loop, so the method is never much worse than the byte version and up to
~8× better at `fixed_channels = 0`, which is where the 2^k work actually is.

### 2.4 Negative result: the first version was a net regression, and why

Recorded because it cost a whole measurement round and is the mistake this
representation invites. The first implementation built those group tables inside
`filter_matching`. `AbstractionTables` was **21,376 bytes**, and a fresh
`Subsume` is constructed for *every* exact subsumption test, so the tables were
rebuilt essentially once per `filter_matching` call:

| n=9, before the fix | |
|---|---|
| `subsume_filter_matching` | 4,350,912 |
| `subsume_table_builds` | 4,346,076 |
| ratio | **1.001** |

The "optimisation" was paying ~21 KB of stores to save a few hundred bytes of
work. The first full 48-run campaign measured only **1.06–1.15×**, and that
result was almost entirely this bug. Two fixes:

1. **Shrink.** `u8` bucket arrays, `Vec`-sized group lists rather than fixed
   64-entry arrays, and a precomputed `idx_base = 3·(hw_b + weights·low_b)`
   which also removes a multiply from the inner loop. The index distributes
   soundly because `base_low` is a multiple of 64 and `low_b < 64`, so
   `base_low | low_b == base_low + low_b`. Size: **21,376 B → 568 B**.
2. **Cache.** A thread-local cache keyed by `(channels, low_channels)`;
   `Subsume` holds an 8-byte `Rc` instead of the table by value.

| n=9, after the fix | |
|---|---|
| `subsume_filter_matching` | 4,690,738 |
| `subsume_table_builds` | **118,410** |
| reduction | **36.7×** |

Every number in this report was taken after that fix. The counter
`subsume_table_builds` is retained precisely so this class of regression cannot
recur silently.

### 2.5 Measured effect of change 1, in isolation (load-robust)

A single-threaded microbenchmark (`bench_subsume`) builds a deterministic corpus
of output-set pairs from a fixed PRNG seed and times
`OutputSet::subsumes_permuted` over it. The same source file was compiled into
both the M2b tree and the Tier-1 tree, and the corpus checksum was verified
**equal** between the two binaries at every channel count, so both are measured
on byte-identical inputs. Runs were interleaved (old, new, old, new…), 6 rounds
each. Because the benchmark is single-threaded, interleaved and same-input, the
**ratio** is far more load-robust than either side's absolute ns/call.

| channels | pairs | hit fraction | M2b ns/call (min / median) | Tier 1 ns/call (min / median) | **ratio** (min / median) |
|---|---|---|---|---|---|
| 8 | 2000 | 38.4 % | 5,841.8 / 5,981.5 | 3,666.9 / 3,703.1 | **1.59 / 1.62** |
| 9 | 1000 | 40.0 % | 12,219.9 / 12,256.4 | 6,621.0 / 6,655.6 | **1.85 / 1.84** |
| 10 | 500 | 32.6 % | 25,438.6 / 25,617.6 | 11,898.0 / 13,469.1 | **2.14 / 1.90** |
| 11 | 250 | 37.6 % | 57,848.3 / 58,230.4 | 23,870.2 / 24,001.7 | **2.42 / 2.43** |

The Tier-1 build additionally carries per-call instrumentation counters that the
M2b build does not, which biases these ratios *against* Tier 1.

The factor is 1.6× at the n=10 mass width and **2.4× at k=11**, and still
rising. The hardware survey's prediction (1.5–2.5×) is met, and the trend says
the benefit at n=11 and n=13 sits at the top of that band.

---

## 3. Change 2 — the weight-histogram thermometer

A channel permutation permutes cube coordinates, so it preserves Hamming weight;
complementation (`invert`, i.e. `bitmap.reverse()`, i.e. `i ↦ (2^k − 1) ^ i`)
maps weight `w` to `k − w`. Writing `hist_A[w]` for the number of present
vectors of weight `w`, and recalling that in this codebase
`A.subsumes_permuted(B)` is `Some` iff `∃π: π(A) ⊆ B`:

```
∃π:            π(A)  ⊆ B   ⟹  hist_A[w]     ≤ hist_B[w]    for all w
∃π: π(complement(A)) ⊆ B   ⟹  hist_A[k − w] ≤ hist_B[w]    for all w
                            ⟺  hist_A[w]     ≤ hist_B[k−w]  for all w
```

These are necessary conditions only, so the test is one-sided in the safe
direction: it can refuse a pair, never accept one.

**The two polarities are kept apart, and that is what makes it pay.**
`LowerInvert::test_precise` has an identity branch and a complement branch, and
each is gated by *its own* condition — the first by
`hist_subsumes(hist_C, hist_Q)`, the second by
`hist_subsumes(hist_C, reverse(hist_Q))`. Collapsing the two into one
disjunctive test at the top of the function would still be sound but strictly
weaker, and would remove far fewer exact calls. The same gate is applied in the
update/eviction direction with the roles of query and candidate exchanged.

The histogram is permutation-invariant and is **not** implied by the existing
pair abstraction: `channel_pair_abstraction` counts quadrants of channel *pairs*
and says nothing directly about global Hamming weight. It is computed from the
stored packed bytes by masked popcount (§2.2), so no unpacking is needed to
evaluate it. Because it lives in `LowerInvert::test_precise` and in the index
traversal closures, it takes effect in `prune` and `gen-proof` as well as in the
on-line search index.

---

## 4. Change 3 — the 64-bit feature-vector signature

E-prover/SatELite lineage: give every stored entry a short invariant whose
bitwise containment is *implied by* the real subsumption condition, so that a
single `AND`-`NOT` rejects.

`histogram_signature(k, hist)` lays down 5 monotone thermometer bits per Hamming
weight; k ≤ 11 gives 12 weights and 60 bits used:

```
bit j of slot w set   ⟺   hist[w] ≥ ceil( binomial(k, w) · (j+1) / 6 ),   j ∈ 0..5
```

Thresholds are non-decreasing in `j`, and the first is ≥ 1 because
`binomial(k,w) ≥ 1`. Each bit is therefore a monotone predicate of `hist[w]`,
which gives the containment property

```
hist_A[w] ≤ hist_B[w] for all w   ⟹   sig_A & ~sig_B == 0
```

and hence the sound one-instruction reject `sig_A & ~sig_B ≠ 0 ⟹ no
subsumption`. Thresholds scale with `binomial(k,w)`, which is symmetric under
`w ↦ k−w`, so the complement polarity is handled by signing the *reversed*
histogram: a query carries `sig` and `sig_rev`, a stored entry carries only its
own `sig`, and `LowerInvert` rejects only when the entry fails against **both**.

Signatures are stored, not recomputed: `OutputSetIndex` and `Tree` carry a
`sigs: Vec<u64>` parallel to `points`/`packed`/`values`, and `Augmentation`
carries the AND and the OR of its subtree's signatures. That gives subtree-level
rejection as well as per-entry rejection:

* **lookup direction** — `sig_and` is a subset of every entry's signature, so
  `sig_and & ~q.sig ≠ 0` implies every entry in the subtree fails;
* **update/eviction direction** — the condition is `q.sig & ~sig_C == 0`, and
  `sig_or` is a superset of every entry's signature, so `q.sig & ~sig_or ≠ 0`
  implies every entry fails.

The signature test runs **before** the abstraction test and before any
unpacking, which is the point of it: two instructions against the abstraction
test's 2 × DIMS `u16` comparisons and against a 2^k-byte unpack.

**Cost, stated up front: 8 bytes per stored entry, plus 16 bytes per k-d node.**
§6.6 measures it and §7 says what to do about it.

---

## 5. Validation

### 5.1 Gate 1 — results, bound sequences, state bands

48 runs, 6 per configuration, with the two frozen binaries of §1, run strictly
sequentially and **round-robin interleaved** across configurations so that load
drift hits both binaries equally.

| cfg | binary | n | `DIMS` |
|---|---|---|---|
| R9_12 / R10_12 | M2b ref | 9 / 10 | 12 |
| T9_12 / T10_12 | Tier 1 | 9 / 10 | 12 |
| R9_16 / R10_16 | M2b ref | 9 / 10 | 16 |
| T9_16 / T10_16 | Tier 1 | 9 / 10 | 16 |

all with `SORTNETOPT_SUBSUME=evict`, `SORTNETOPT_SUBSUME_WIDTHS=7,8`.

* **`result = 25` in all 24 n=9 runs and `29` in all 24 n=10 runs.**
* **Exactly one distinct bound sequence per n across all 48 runs**, equal to the
  required reference:
  * n=9: `5, 8, 11, 14, 17, 19, 21, 22, 23, 24, 25`
  * n=10: `5, 9, 12, 15, 18, 21, 23, 25, 26, 27, 28, 29`
* `idx_clamps = 0` in every run of every configuration.
* Peak `StateMap` entries 35,289–36,172 across all 48 runs — inside the M2b band
  (35,274–35,834) to within run-to-run scatter, with no systematic shift between
  the two binaries.

A further 42 runs (the `DIMS` sweep of §6.5), 36 runs (the baseline comparison
of §6.4), 16 runs (the gate sweep of §6.2) and 14 audit runs (§5.3) all
reproduced the same results and bound sequences: **156 searches in total, no
deviation.**

**Gate 1: PASS.**

### 5.2 Gate 2 — full pipelines and certificates

Seven independent full pipelines, each
`search → prune-all (SORTNETOPT_CROSS_BOUND_PRUNE=1) → gen-proof → frozen snocheck -v +RTS -N10 -RTS`.

| pipeline | states | survivors (all widths) | steps | `snocheck -v` |
|---|---|---|---|---|
| Tier 1, n=9, `DIMS=12` | 35,425 | 12,224 | 11,654 | **`Just (9,25)`** |
| Tier 1, n=10, `DIMS=12` | 35,747 | 12,404 | 11,904 | **`Just (10,29)`** |
| M2b ref, n=9, `DIMS=12` | 36,013 | 12,448 | 11,860 | **`Just (9,25)`** |
| M2b ref, n=10, `DIMS=12` | 35,596 | 12,301 | 11,711 | **`Just (10,29)`** |
| Tier 1, n=9, patch round-trip build | — | 12,224 | 11,672 | **`Just (9,25)`** |
| Tier 1, n=9, **under filter audit** | — | 12,301 | 11,706 | **`Just (9,25)`** |
| Tier 1, n=10, **under filter audit** | — | 12,375 | 11,752 | **`Just (10,29)`** |

Survivor totals (12,224–12,448) and step counts (11,654–11,904) sit inside M2b's
reported bands (12,220–12,315 survivors, 11,643–11,790 steps) to within the
run-to-run variation the parallel search shows on its own. No `prove_all` panic
in any run. The last two rows matter: the `prune-all` and `gen-proof` stages were
themselves run with `SORTNETOPT_FILTER_AUDIT=1`, so the filters were audited in
the certificate pipeline, not only in the search.

**Gate 2: PASS.**

### 5.3 Gate 3 — filter soundness audit

`SORTNETOPT_FILTER_AUDIT=1` turns every filter rejection into a check: instead of
skipping the candidate, the code runs the exact test with the histogram gates
disabled and **panics** if it returns a match. Node-level signature rejection is
disabled in audit mode so that every entry is visited and audited individually;
that is sufficient, because `sig_and` is a subset and `sig_or` a superset of
every entry signature in the subtree, so a node reject implies every entry in it
individually rejects — per-entry soundness implies node soundness.

Fourteen audited search configurations. `DIMS=4` is included deliberately: it is
the weakest possible abstraction filter, so it forces an order of magnitude more
candidates through to the pre-filters and the exact test, and is by far the most
searching audit available.

| n | `DIMS` | widths | result | `filter_audit_violations` | sig rejects audited | hist rejects audited |
|---|---|---|---|---|---|---|
| 9 | 4 | 7,8 | 25 | **0** | 29,331,277 | 23,792,308 |
| 9 | 4 | 6,7,8 | 25 | **0** | 32,050,534 | 24,500,089 |
| 9 | 12 | 7,8 | 25 | **0** | 27,951,075 | 1,376,441 |
| 9 | 12 | 6,7,8 | 25 | **0** | 29,574,368 | 1,522,395 |
| 9 | 48 | 7,8 | 25 | **0** | 22,097,069 | 133,645 |
| 9 | 48 | 6,7,8 | 25 | **0** | 24,236,990 | 148,669 |
| 10 | 4 | 7,8 | 29 | **0** | 29,276,650 | 23,664,972 |
| 10 | 4 | 6,7,8 | 29 | **0** | 31,988,974 | 24,782,274 |
| 10 | 12 | 7,8 | 29 | **0** | 28,008,969 | 1,370,198 |
| 10 | 12 | 6,7,8 | 29 | **0** | 30,026,303 | 1,530,604 |
| 10 | 48 | 7,8 | 29 | **0** | 22,733,911 | 128,251 |
| 10 | 48 | 6,7,8 | 29 | **0** | 25,262,604 | 144,206 |
| 9 | 12 | 7,8 (gate-3 headline run) | 25 | **0** | 28,177,940 | 1,380,465 |
| 10 | 12 | 7,8 (gate-3 headline run) | 29 | **0** | 26,023,659 | 1,318,477 |

Totals: **~387 million signature rejections and ~106 million histogram
rejections — roughly 493 million in all — each re-checked against the exact
permuted-subsumption test, and in not one case would the exact test have
accepted the pair.** Every run gave the correct result and the reference bound
sequence, and the prune/gen-proof stages were audited too (§5.2), so audit mode
also confirms the filters do not change the answer.

(`filter_hist_rejects` is much larger under audit — 1.38 M versus 0.20 M at
`DIMS=12` — for a mechanical reason that is itself a consistency check: without
audit, a signature-rejected candidate returns before reaching the histogram
test, so the histogram never gets to reject it; with audit nothing returns early
and both filters see every candidate.)

**Gate 3: PASS.**

### 5.4 Gate 4 — memory

See §6.6. **PASS with a stated regression** — the stored signature costs
8 B/entry plus 16 B/node, which is +6.6 % combined payload and 1.15× peak RSS;
`StateMap` entries and packed key bytes are unchanged.

**Gate 4: PASS.**

---

## 6. Measurements

> Every wall-clock figure in this section was taken with a 10-thread n=11 search
> occupying the same machine. They are **indicative only**, and absolute values
> are not comparable *between* tables (the load level differed between
> measurement windows — load average 19–30 for §6.1, 40–56 for §6.4). Within
> each table all configurations were interleaved round-robin, so the *ratios*
> are meaningful. Counter-derived quantities and memory figures are unaffected
> by load.

### 6.1 Headline, 6 runs per configuration

| metric | R9_12 (M2b) | **T9_12 (Tier 1)** | R10_12 (M2b) | **T10_12 (Tier 1)** |
|---|---|---|---|---|
| search wall, mean (min–max) ms | 6,491.8 (6,142–7,679) | **3,642.8 (3,481–3,916)** | 6,566.0 (5,963–7,948) | **3,675.0 (3,492–4,211)** |
| **speedup vs M2b** | — | **1.78×** | — | **1.79×** |
| peak `StateMap` entries | 35,493–36,036 | 35,388–35,910 | 35,464–36,051 | 35,565–35,921 |
| peak packed key bytes | 731,439–739,371 | 728,679–740,127 | 733,175–738,231 | 729,867–739,831 |
| index payload bytes | 694,481–705,476 | 798,664–821,091 | 695,944–709,913 | 790,918–814,846 |
| combined payload bytes | 1,569,794–1,583,447 | 1,668,895–1,704,822 | 1,571,914–1,590,552 | 1,663,005–1,697,332 |
| combined payload ratio | — | **1.071×** | — | **1.066×** |

| metric | R9_16 (M2b) | **T9_16 (Tier 1)** | R10_16 (M2b) | **T10_16 (Tier 1)** |
|---|---|---|---|---|
| search wall, mean (min–max) ms | 5,086.0 (4,795–5,660) | **3,199.8 (3,108–3,303)** | 5,039.5 (4,816–5,456) | **3,227.7 (3,150–3,324)** |
| **speedup vs M2b** | — | **1.59×** | — | **1.56×** |
| combined payload bytes | 1,670,272–1,718,937 | 1,771,917–1,797,419 | 1,682,501–1,708,046 | 1,771,360–1,810,497 |
| combined payload ratio | — | **1.054×** | — | **1.057×** |

**Tier 1 at `DIMS=12` strictly dominates M2b at `DIMS=16`** — M2b's own
recommended operating point, the one at which it met its ≤3× objective: 3,675 ms
versus 5,039 ms (**1.37× faster**) at 1,680 kB versus 1,695 kB combined payload
(**0.99×**, i.e. very slightly *less* memory). The `DIMS` sweep of §6.5
reproduces this domination independently.

### 6.2 Per-change attribution

Two independent decompositions agree.

**(a) The filters, gated within one binary** (n=10, `DIMS=12`, 4 runs per
setting, interleaved). `SORTNETOPT_TIER1_SIG` and `SORTNETOPT_TIER1_HIST`
default on; `0` turns each off at its call sites. All 16 runs gave `result = 29`
and the reference bound sequence.

| setting | `filter_exact_calls` | reduction vs neither | wall, mean ms | speedup |
|---|---|---|---|---|
| D — neither filter | 5,853,006 | — | 4,099 | 1.00× |
| B — signature only | 4,524,791 | 22.7 % | 3,736 | 1.10× |
| C — histogram only | 3,997,164 | 31.7 % | 3,662 | 1.12× |
| **A — both (default)** | **3,905,117** | **33.3 %** | **3,560** | **1.15×** |

The two filters overlap heavily, which is expected and worth stating plainly:
the signature is a *relaxation* of the histogram condition, so every pair the
signature rejects the histogram would also have rejected. The signature's value
is therefore not extra rejections — it adds only 2.3 % on top of the histogram
(3,997 k → 3,905 k exact calls) — but the *price* of each rejection: two
instructions, evaluated before the abstraction test and before any unpacking, on
the 43.9 % of candidates it disposes of.

**(b) Change 1 by subtraction and by microbenchmark.** Full stack 1.787× ÷
filters 1.151× = **1.553×** attributable to the packed representation at n=10.
The independent single-threaded microbenchmark of §2.5 measures **1.62×** at k=8
and **1.90×** at k=10 for the exact test alone. Two different methods, the same
answer to within the noise.

| change | measured contribution (n=10) | basis |
|---|---|---|
| 1 — packed u64 + SIMD | **≈1.55×** (isolated exact test: 1.62–2.43×, rising with k) | subtraction + interleaved single-threaded microbenchmark |
| 2 — weight-histogram thermometer | **1.12×**, −31.7 % exact calls | in-binary env gate, 4 runs |
| 3 — index feature signature | **1.03×** on top of 2, −2.3 % further exact calls, 43.9 % of candidates rejected in 2 instructions | in-binary env gate, 4 runs |
| **combined** | **1.79×** | 6-run interleaved campaign |

### 6.3 Filter hit rates (load-robust)

n=10, `DIMS=12`, 6-run means from the headline campaign:

| counter | value | rate |
|---|---|---|
| `filter_candidates` | 58,952,427 | — |
| `filter_sig_rejects` | 25,874,094 | **43.89 %** of candidates |
| `filter_sig_node_rejects` | 202,150 | whole k-d subtrees skipped |
| `filter_hist_rejects` | 199,049 | 0.34 % of candidates (of those that reach it) |
| `filter_exact_calls` | 3,454,664 | 5.9 % of candidates |
| `filter_audit_violations` | **0** | — |
| `subsume_calls` | 3,454,664 | — |
| `subsume_filter_matching` | 3,976,740 | 1.15 per exact test |
| `subsume_table_builds` | 114,971 | 0.029 per `filter_matching` (was 1.001, §2.4) |
| `subsume_nodes` | 4,347,426 | 1.26 per exact test |

### 6.4 Against the unmodified baseline, under identical load

36 runs, 6 per configuration, all three binaries interleaved round-robin in the
same window (load average 40–56 — higher than §6.1, so absolute times are larger;
the ratios are the point).

| n | baseline | M2b ref | Tier 1 | M2b vs baseline | **Tier 1 vs baseline** | Tier 1 vs M2b |
|---|---|---|---|---|---|---|
| 9 | 2,540.8 ms | 10,247.5 ms | **5,803.8 ms** | 4.03× slower | **2.28× slower** | **1.77× faster** |
| 10 | 2,683.8 ms | 10,645.2 ms | **5,789.8 ms** | 3.97× slower | **2.16× slower** | **1.84× faster** |

| n | baseline combined payload | M2b | Tier 1 | M2b net reduction | Tier 1 net reduction |
|---|---|---|---|---|---|
| 9 | 4,581,622 | 1,574,436 | 1,682,848 | 2.91× | **2.72×** |
| 10 | 4,570,400 | 1,585,524 | 1,690,966 | 2.88× | **2.70×** |

Peak `StateMap` entries: baseline 208,178, M2b 35,700, Tier 1 35,821 at n=10 —
a 5.8× entry reduction, unchanged by this campaign, as it must be.

M2b's report measured **3.29×** slower than baseline at `DIMS=12` on a quiet
machine; the same configuration measures 3.97–4.03× here, so this window's load
inflates the ratio by roughly 1.2×. Deflating Tier 1's 2.16–2.28× by the same
factor gives an *estimate* of **~1.8× slower than the unmodified search on a
quiet machine**, against M2b's 3.29×. That is an extrapolation and is offered as
one; the load-matched ratio 2.16–2.28× is the measurement.

### 6.5 The memory/throughput frontier, and where Tier 1 wins most

n=10, `evict`, widths 7,8, 3 runs per point, both binaries interleaved
round-robin at every `DIMS`. All 42 runs gave `result = 29`, the reference bound
sequence, and `idx_clamps = 0`. "net ×" is 4,566,753 B (the published baseline
`StateMap` key+`State` figure) over combined payload.

| `DIMS` | M2b wall ms | M2b combined B | M2b net × | **Tier 1 wall ms** | **Tier 1 combined B** | **Tier 1 net ×** | **speedup** |
|---|---|---|---|---|---|---|---|
| 4 | 54,892.7 | 1,361,184 | 3.36× | **9,594.0** | 1,452,547 | 3.14× | **5.72×** |
| 8 | 13,027.7 | 1,474,480 | 3.10× | **5,331.7** | 1,592,499 | 2.87× | **2.44×** |
| 12 | 7,565.3 | 1,588,582 | 2.87× | **3,890.0** | 1,686,991 | 2.71× | **1.94×** |
| 16 | 5,821.0 | 1,688,900 | 2.70× | **3,516.3** | 1,793,200 | 2.55× | **1.66×** |
| 24 | 4,136.7 | 1,901,434 | 2.40× | **3,122.7** | 2,029,321 | 2.25× | **1.32×** |
| 32 | 3,793.0 | 2,115,886 | 2.16× | **2,930.7** | 2,233,025 | 2.05× | **1.29×** |
| 48 | 3,028.7 | 2,570,212 | 1.78× | **2,877.3** | 2,629,853 | 1.74× | **1.05×** |

Three readings, in order of importance.

**(i) The speedup is monotone in how weak the abstraction filter is.** 5.72× at
`DIMS=4`, 1.05× at `DIMS=48`. That is exactly what the mechanism predicts: a
high-dimensional abstraction point rejects almost everything before the exact
test, so there is little exact-test work left to accelerate; a low-dimensional
one lets candidates through, and those are what Tier 1 makes cheap. **M2b §7.1
identified "how the per-lookup exact-test count scales when the index population
grows 1,600× at n=11" as the single largest uncertainty in its n=11
projection**, and warned that a fixed-dimension filter degrades as the
population grows. A growing population is *behaviourally the same regime as a
smaller `DIMS`* — more survivors per query reaching the exact test. This table
is therefore direct evidence that Tier 1's advantage grows in exactly the
direction M2b was most worried about, and §2.5's k-dependence (1.62× at k=8,
2.43× at k=11) compounds it.

**(ii) At matched memory, Tier 1 is 1.42× faster.** Tier 1 `DIMS=8`
(5,331.7 ms, 1,592,499 B, net 2.87×) against M2b `DIMS=12` (7,565.3 ms,
1,588,582 B, net 2.87×): the combined payloads agree to 0.25 %, the net memory
factors agree to two decimal places, and Tier 1 is **1.42× faster**. Dropping
four points of abstraction dimension pays for the signature and more.

**(iii) Tier 1 `DIMS=12` strictly dominates M2b `DIMS=16`** — 3,890 ms versus
5,821 ms at 1,686,991 B versus 1,688,900 B: faster *and* smaller. This
reproduces §6.1's finding in an independently-run sweep. No Tier-1 row dominates
M2b `DIMS=12` on both axes, because of the signature's 8 B/entry; `DIMS=8`
matches it to 0.25 % and is the honest "matched memory" comparison.

**(iv) The low-memory end of the frontier becomes usable for the first time.**
M2b at `DIMS=4` reaches the best net memory factor in the table (3.36×) but
takes 54.9 s — 7.3× its own `DIMS=12` time, which is why M2b's report never
proposed operating there. Tier 1 at `DIMS=4` gets net 3.14× in 9.6 s. That is
**lower memory than any M2b operating point that is not absurdly slow** (M2b
`DIMS=12` is 2.87× net at 7.6 s), at 1.27× M2b `DIMS=12`'s time. For n=13, where
every published estimate says memory and not time is the binding constraint,
this is arguably the most valuable row in the table: the 5.7× speedup at
`DIMS=4` is what converts a memory-optimal configuration from unusable into
merely expensive.

### 6.6 Memory

| n=10, `DIMS=12` | M2b ref | Tier 1 | ratio |
|---|---|---|---|
| peak `StateMap` entries | 35,464–36,051 | 35,565–35,921 | 1.00× |
| peak packed key bytes | 733,175–738,231 | 729,867–739,831 | 1.00× |
| index payload bytes | ~702,000 | ~803,000 | **1.14×** |
| combined payload bytes | ~1,581,000 | ~1,680,000 | **1.066×** |
| net memory factor vs baseline | 2.88× | **2.70×** | |
| peak RSS (`/usr/bin/time -l`), 3 runs, mean | 25.7 MB | 29.5 MB | **1.15×** |

The regression is entirely accounted for: 8 B per entry of stored signature plus
16 B per k-d node of `Augmentation`, against ~9,500 entries, is ~101 kB — exactly
the measured index-payload delta. `StateMap` entries and packed key bytes are
untouched, as they must be: the memo table is unaffected by this campaign.

**On the "8× transient memory reduction" the hardware survey predicted:** it is
real as *allocation traffic* — `Subsume` no longer allocates at all, removing
roughly 2 GB of malloc/free traffic per n=10 search (3.9 M exact tests × two
256-byte `Vec<bool>`), and the per-lookup 2 KB `BVec` scratch bitmap is gone —
but it is **not observable as peak RSS**, which went *up* 1.15× because peak RSS
is dominated by resident payload and the allocator retains its arenas. Reported
as measured, not as predicted.

---

## 7. Recommendations

1. **Land it.** All four gates pass, seven certificates are accepted by the
   unchanged verified checker, ~493 million filter rejections are audited
   against the exact test with zero disagreements, and the combined factor is
   1.79× at the like-for-like configuration.
2. **Recommended operating point: Tier 1 at `DIMS=12`.** It strictly dominates
   M2b at `DIMS=16` — faster *and* smaller — and M2b `DIMS=16` was M2b's own
   recommendation. If memory is the harder constraint, Tier 1 at `DIMS=8`
   matches M2b `DIMS=12`'s memory to 0.25 % and is 1.42× faster.
3. **For n=13 planning, operate at low `DIMS`.** §6.5(iv): Tier 1 makes the
   memory-optimal end of the frontier usable — 3.14× net memory in 9.6 s, where
   M2b needed 54.9 s for 3.36×. Since n=13 is memory-bound by three to four
   orders of magnitude and not time-bound, the right Tier-1 configuration for
   that regime is `DIMS=4–8`, which is also where Tier 1's advantage over M2b is
   largest (5.7× / 2.4×).
4. **Re-derive the n=11 and n=13 budgets with the *k=11* factor, not the n=10
   one.** §2.5 gives 2.43× for the exact test at k=11 and §6.5 shows the
   end-to-end factor rising as the abstraction filter weakens. The naive
   n=11 projection from M2b's table (`DIMS=24`, 8.0 h) should be re-run rather
   than scaled, but every measured trend points the same way.
4. **The signature filter is the weakest of the three and the only one with a
   memory cost.** It contributes 1.03× on top of the histogram filter and costs
   +6.6 % combined payload. Keep it on where memory is not binding
   (`SORTNETOPT_TIER1_SIG=1`, the default); if n=13-scale memory becomes the
   constraint, either set `SORTNETOPT_TIER1_SIG=0` or shrink the signature to
   `u32` (3 thermometer bits per weight instead of 5), which would halve the
   cost for most of the filtering power. That shrink is **not implemented**.
5. **Re-measure on a quiet machine before any budget is committed.** §8.
6. **`subsume_table_builds` is now a regression tripwire.** If it ever
   approaches `subsume_filter_matching`, the thread-local table cache has been
   defeated (§2.4).
7. **The GPU question is now differently posed.** The Tier-1 queue said GPU
   offload was deferred until these three landed because they "change the
   arithmetic for everything downstream". They have: the exact test is 1.6–2.4×
   cheaper and is called 33 % less often, so the CPU-side kernel a GPU would
   have to beat is now ~2.4–3.6× stronger than the M2b baseline the 30–90×
   literature numbers were being compared against.

---

## 8. Re-measurement commands (for replay on a quiet machine)

Confirm the machine is quiet first:

```
ps aux | grep sortnetopt | grep -v grep     # must be empty
uptime                                      # load average should be < 1
```

Headline campaign (48 runs, round-robin interleaved, strictly sequential):

```
for round in 1 2 3 4 5 6; do
  for cfg in "R 9 12" "T 9 12" "R 10 12" "T 10 12" \
             "R 9 16" "T 9 16" "R 10 16" "T 10 16"; do
    set -- $cfg
    case $1 in R) BIN=<ABS>/.build/v3-tier1/bin/sortnetopt-m2b-ref ;;
               T) BIN=<ABS>/.build/v3-tier1/bin/sortnetopt-tier1 ;; esac
    D=<ABS>/.build/v3-tier1/requiet/$1$2_$3/run$round
    mkdir -p $D/data
    SORTNETOPT_SUBSUME=evict SORTNETOPT_SUBSUME_DIMS=$3 \
    SORTNETOPT_SUBSUME_WIDTHS=7,8 \
      $BIN -m search $2 $D/data/_search_$2 > $D/run.log 2> $D/run.err
    rm -rf $D/data
  done
done
```

Baseline-relative (add the baseline binary to the same interleave):

```
BASE=<ABS>/.build/v3-m2a/sortnetopt-baseline
$BASE -m search 10 $D/data/_search_10        # no SORTNETOPT_SUBSUME env
```

`DIMS` frontier (42 runs, 3 per point, both binaries interleaved at each point):

```
for round in 1 2 3; do
  for dims in 4 8 12 16 24 32 48; do
    for BIN in <ABS>/.build/v3-tier1/bin/sortnetopt-tier1 \
               <ABS>/.build/v3-tier1/bin/sortnetopt-m2b-ref; do
      D=<ABS>/.build/v3-tier1/requiet/sweep/$(basename $BIN)_$dims/run$round
      mkdir -p $D/data
      SORTNETOPT_SUBSUME=evict SORTNETOPT_SUBSUME_DIMS=$dims \
      SORTNETOPT_SUBSUME_WIDTHS=7,8 \
        $BIN -m search 10 $D/data/_search_10 > $D/run.log 2> $D/run.err
      rm -rf $D/data
    done
  done
done
```

Per-change attribution (n=10, `DIMS=12`, 4 rounds, interleaved):

```
for round in 1 2 3 4; do
  for s in "1 1" "1 0" "0 1" "0 0"; do
    set -- $s
    D=<ABS>/.build/v3-tier1/requiet/gate_$1$2/run$round; mkdir -p $D/data
    SORTNETOPT_TIER1_SIG=$1 SORTNETOPT_TIER1_HIST=$2 \
    SORTNETOPT_SUBSUME=evict SORTNETOPT_SUBSUME_DIMS=12 \
    SORTNETOPT_SUBSUME_WIDTHS=7,8 \
      <ABS>/.build/v3-tier1/bin/sortnetopt-tier1 -m search 10 \
      $D/data/_search_10 > $D/run.log 2> $D/run.err
    rm -rf $D/data
  done
done
```

Exact-test microbenchmark (single-threaded, interleaved; `bench_subsume` is
described in §2.5 and staged at `.build/v3-tier1/bench2/`):

```
for round in 1 2 3 4 5 6; do
  for k in "8 2000" "9 1000" "10 500" "11 250"; do
    set -- $k
    <ABS>/.build/v3-tier1/bench2/bench-old $1 $2 3
    <ABS>/.build/v3-tier1/bench2/bench-new $1 $2 3
  done
done
# corpus_checksum MUST be equal between the two binaries at each k
```

Peak RSS:

```
/usr/bin/time -l <BIN> -m search 10 <datadir>/_search_10
```

Certificate pipeline:

```
SORTNETOPT_CROSS_BOUND_PRUNE=1 <BIN> -m prune-all <datadir>/_search_<n>
<BIN> -m gen-proof <datadir>/_search_<n>
<ABS>/.build/b3-toolchain/attempt-20260815T000526Z/bin/snocheck -v +RTS -N10 -RTS \
  <datadir>/_search_<n>/proof.bin
```

Soundness audit (the `DIMS=4` rows are the searching ones):

```
SORTNETOPT_FILTER_AUDIT=1 SORTNETOPT_SUBSUME=evict SORTNETOPT_SUBSUME_DIMS=4 \
SORTNETOPT_SUBSUME_WIDTHS=6,7,8 \
  <ABS>/.build/v3-tier1/bin/sortnetopt-tier1 -m search 10 <datadir>/_search_10
# require: counter filter_audit_violations 0
```

---

## 9. Artifacts

Under `.build/v3-tier1/` (build directory, not committed):

* `source/` — detached worktree at the pin, five patches applied
* `m2b-tree/`, `verify-base/` — the same worktree at the 4-patch M2b state, used
  to generate and to check the diff
* `bin/sortnetopt-m2b-ref`, `bin/sortnetopt-tier1` — the two frozen binaries
* `campaign2/` — the 48-run headline campaign, `summary.json` / `summary.md`
* `gates/` — four certificate pipelines (with `proof.bin`), the gate-3 audit
  runs, the per-change gate sweep and the RSS runs, `summary.json`
* `sweep/` — the 42-run `DIMS` frontier of §6.5, `summary.json`
* `basecmp/` — the 36-run baseline comparison of §6.4, `summary.json`
* `audit2/` — the 12-configuration extended audit and the two audited
  certificate pipelines of §5.3, `summary.json`
* `bench2/` — the exact-test microbenchmark, both binaries and all 48 rounds
* `diag/` — the before/after `subsume_table_builds` diagnostic of §2.4
* `verify-run/` — the patch round-trip's n=9 search and certificate
* `campaign/`, `bench/`, `profile/` — the superseded first measurement round
  (§2.4) and the unusable `sample(1)` profiles (§10)

Committed: `tools/patches/sortnetopt-tier1-v3.patch`, this report.

---

## 10. Deviations and open items

* **Every wall-clock number was measured under heavy load** (a 10-thread n=11
  search on the same 10-core host; load average 19–56 depending on the window)
  and is indicative only. §8 gives replay commands. Absolute times are not
  comparable between tables; within each table every configuration was
  interleaved round-robin, so ratios are. The load-robust evidence — counter
  ratios, the interleaved single-threaded microbenchmark, all correctness and
  memory figures — is what the conclusions rest on.
* **A `sample(1)` profile was attempted and is not usable for attribution.**
  Under ~3× oversubscription, 89 % of samples land in `__psynch_cvwait` /
  `semaphore_timedwait_trap` and no compute symbol appears at all in either
  binary. It is archived; no claim in this report depends on it. A post-Tier-1
  profile on a quiet machine is still owed, and is the natural way to find the
  next bottleneck.
* **The first implementation of change 1 was a net regression** and measured only
  1.06–1.15×. §2.4 records the cause (a 21 KB table rebuilt once per exact test)
  and the fix. That campaign's numbers are superseded and are reported only as
  the negative result.
* **Change 3 costs memory**: +8 B per index entry and +16 B per k-d node,
  measured as +6.6 % combined payload and 1.15× peak RSS. It is not free and is
  not presented as free. The `u32` shrink of §7.4 is not implemented.
* **The predicted 8× transient-memory reduction is not visible as peak RSS**
  (§6.6). The allocation traffic really is eliminated; the metric the survey
  implied would move does not move.
* **`prune.rs` and `proof.rs` are touched** (they consume `SubsumeFilter` and the
  packed candidate path). As in M2b, `checker/` is byte-for-byte unchanged and
  was not rebuilt, and all seven certificates were produced with every filter
  active — two of them with the audit running inside `prune-all` and
  `gen-proof`.
* **`Upper` is implemented but unexercised.** `OutputSetIndex<Upper>` is not used
  by the search, prune or proof paths; its filter algebra is written and reviewed
  but is not covered by the audit runs.
* **n=11 is unmeasured by this campaign.** The k=11 microbenchmark (§2.5) is the
  only n=11-scale evidence here; the `--limit` de-risking run M2b §7.3 asked for
  has not been re-run on the Tier-1 stack.
* **The `+2 survivors` cross-bound root-guard over-retention**, the
  **thread-pool contention** (45 % of samples blocked, M2b §8.1) and
  **`OutputSetIndex<Upper>` as a memory lever** remain open from M2b and are
  untouched here.
* **Search-phase wall is the `elapsed_ms` of the final iteration row**, not
  process wall: the stats logger sleeps in 10-second increments and imposes a
  ~10 s floor on every process (M0b §4 correction).
