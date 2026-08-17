# Tier 2b: thread-pool descheduling, and checkpoint/restart for the search

Date: 2026-08-17. Contract: `METHOD_EXPERIMENT_CONTRACT_V3.md` (§2 pin
discipline, §5 evidence rules). Milestone: Tier 2, campaign B. Predecessor:
`evidence/v3/tier1/report.md`. Sibling, developed in parallel over disjoint
files: Tier 2a.

**Status: one objective PASS, one objective MEASUREMENT-REFUTED.**

* **Checkpoint/restart: PASS, and it is the deliverable that matters.** Durable,
  versioned, fsynced, globally consistent snapshots, with resume gated on a
  header hash, an identity hash and a payload hash. Eight full pipelines — four
  killed with `kill -9` at 45–75 % of the *final* bound iteration and resumed,
  four unkilled controls — all produced `Just (9,25)` / `Just (10,29)` from the
  **unchanged** frozen Isabelle/HOL-extracted checker. Resume refuses on config
  mismatch, body corruption and header corruption (4/4). At n=11 scale a
  1.98 M-state / 62.8 MB snapshot costs a **372 ms** stall and resumes in
  **321 ms**. End-to-end overhead at n=10: **+0.57 %**, against a ≤2 % target.
* **Thread-pool descheduling: the premise does not reproduce.** The measured
  motivation — "45 % of thread samples blocked in `__psynch_cvwait`", and a
  900 % → 426 % CPU collapse on the killed n=11 run — is not a descheduling
  deficit. Direct CPU sampling shows the **unmodified Tier-1 stack already runs
  the n=10 final iteration at 943 % of a 10-core box, and a deep n=11 iteration
  at 931 %.** There is ~1.06× of headroom at n=10 and none worth chasing at
  n=11. The pool changes landed because they are provably behaviour-preserving
  and cut global-lock traffic **23.0×**, but they buy **~0 %, not 1.8×**: an
  n=11 A/B puts them at **0.995×, inside the within-arm noise**.

Patch: `tools/patches/sortnetopt-tier2b-v3.patch` (SHA-256
`f22fe1750c9b04af5395421632dfb3094afbfd65ce37b75f29a5b6efed9fd9c2`, 2,581
lines), on top of the Tier-1 stack and **independent of Tier-2a** (§1.4).

---

## 1. Provenance and build

The pinned clone `.cache/third_party/sortnetopt` was **not modified**
(`git status --porcelain` empty and `worktree list` showing no entry inside the
clone, before and after every step).

```
git -C <ABS>/.cache/third_party/sortnetopt worktree add --detach \
    <ABS>/.build/v3-tier2b/source 0b5d09c47446096f9e3a0812b35afc72b7f2a718
cd <ABS>/.build/v3-tier2b/source
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-macos-proc.patch
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-instrumentation-v3.patch
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-online-subsumption-v3.patch
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-perf-v3.patch
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-tier1-v3.patch
patch -V none -p1 -i <ABS>/tools/patches/sortnetopt-tier2b-v3.patch
cargo build --release      # rustc 1.95.0 (59807616e 2026-04-14) (Homebrew)
```

Host: M4 Mac mini (Mac16,10), Apple M4, 10 cores, 16 GiB, Darwin 25.5.0
(macOS 26.5.2) — the same host M0b, M2a, M2b and Tier 1 used.

| | path | SHA-256 |
|---|---|---|
| Tier-1 reference (5-patch stack) | `.build/v3-tier2b/bin/sortnetopt-base` | `9ec5c91f9d23845c3c61074dd3af8947d69ef79c8d49468853b140fdd4d23940` |
| **Tier 2b** (6-patch stack) | `.build/v3-tier2b/bin/sortnetopt-tier2b` | `c88477086614c98452aba04d96f318b1d4dd3adb4c3b9b0a47d251c6941d3cc3` |

Verification used the prebuilt frozen checker, unchanged:
`.build/b3-toolchain/attempt-20260815T000526Z/bin/snocheck` (SHA-256
`4cd30511f73e7d7f6f3f7bc4083d84b37c0678f2156f85fcbfa186546218a84c`), invoked as
`snocheck -v +RTS -N10 -RTS <proof.bin>`.

### 1.1 Patch round-trip

A fresh detached worktree was created from the same pin and all six patches
applied in order. Every hunk applied clean — **no fuzz, no offset, no `.rej` or
`.orig`** — and `diff -r verify/src source/src` reported **no differences**. It
built with only the one pre-existing upstream warning in `output_set/canon.rs`,
`cargo test --release` passed 19/19, and an n=9 run with checkpointing active
(10 mid-run snapshots) reproduced `result = 25` with the reference bound
sequence and went through `prune-all` (`SORTNETOPT_CROSS_BOUND_PRUNE=1`) →
`gen-proof` → frozen `snocheck -v` to **`Just (9,25)`**. The pinned clone was
re-verified clean afterwards.

### 1.2 What the patch touches

Seven files: `src/bin/sortnetopt.rs`, `src/instrument.rs`, `src/search.rs`,
`src/search/checkpoint.rs` (new, 1,381 lines), `src/search/states.rs`,
`src/search/subsume.rs`, `src/thread_pool.rs`.

### 1.3 What it does not touch

`checker/` is byte-for-byte unchanged and was not rebuilt. `src/output_set.rs`,
`src/output_set/canon.rs`, `src/output_set/index.rs`,
`src/output_set/index/tree.rs`, `src/output_set/packed.rs`,
**`src/output_set/subsume.rs` — the exact permuted-subsumption matcher, which is
Tier-2a's file** — `src/prune.rs`, `src/proof.rs`, `src/huffman.rs`,
`src/fix.rs` and `Cargo.toml` are unchanged. **No new dependencies**: the
SHA-256 the checkpoint format needs is implemented inside `checkpoint.rs` and
unit-tested against the three standard FIPS 180-4 vectors.

### 1.4 Independence from Tier-2a — verified, not assumed

Tier-2a touches `src/output_set/subsume.rs` and `src/instrument.rs`; Tier-2b
touches `src/instrument.rs` and six files Tier-2a does not. The single shared
file was a conflict risk, so it was tested rather than argued: a fresh worktree
at the pin with **macos-proc → instrumentation → online-subsumption → perf →
tier1 → tier2a → tier2b** applied in that order took every hunk with **no fuzz,
no offset and no rejects**, built with **zero errors**, and its n=9 run with
checkpointing active produced `result = 25`, the reference bound sequence, and
**`Just (9,25)`** from the frozen checker. The two campaigns compose.

---

## 2. Measure first: the premise of objective 1 does not hold

Objective 1 expected "up to ~1.8× on the final iteration where CPU util
collapses (we observed 900 % → 426 % on the M4 run)". Before changing anything,
that was measured directly.

### 2.1 The instrument: sampled CPU utilisation, not `%cpu`

`tools/cpu_sampler.py` (new) launches the search, samples `ps -o cputime,rss` at
10 Hz (1 Hz for the long n=11 runs) and **differentiates** the cumulative CPU
time: `util_pct = 100 · Δcpu/Δwall`, so 1000 % is the whole 10-core box. This
matters: macOS `ps -o %cpu` is a *lifetime average*, so it ramps monotonically
from zero and is useless as a utilisation curve — the first attempt at this
measurement used it and produced a smooth ramp that looked like a warm-up and
was an artefact. Rows are flushed as they are taken, so a deliberately
SIGKILLed run still leaves a usable trace.

### 2.2 n=10: the final iteration is already saturated

At n=10 the final bound iteration (28 → 29) is **3,381 ms of a 3,500 ms search,
96.6 % of it**, so "final iteration" and "the search" are nearly the same
thing — exactly as at n=11, where it was 240 min of a 250 min run.

Mean CPU utilisation over the final iteration, 6 runs per configuration,
interleaved round-robin, quiet machine:

| configuration | binary | per-run mean util (%) | 6-run mean |
|---|---|---|---|
| B10 Tier-1 reference | `sortnetopt-base` | 947, 932, 935, 943, 949, 951 | **943 %** |
| T10 Tier 2b, new pool | `sortnetopt-tier2b` | 950, 943, 922, 939, 949, 945 | **941 %** |
| U10 Tier 2b, `SORTNETOPT_POOL=upstream` | `sortnetopt-tier2b` | 947, 949, 937, 948, 949, 948 | **946 %** |

**All three sit at ~94 % of machine capacity, and are indistinguishable from one
another.** The unmodified upstream scheduler is not leaving cores idle at n=10.
The maximum achievable speedup from a perfect scheduler here is ~1.06×.

### 2.3 n=11: still saturated, 15 minutes into a deep iteration

n=11, `--limit 34`, `DIMS=24`, widths 8,9 — i.e. inside the 33 → 34 iteration,
the structural analogue of the iteration the killed run died in. Sampled live at
15 minutes, 3.1 M states, RSS 235 MB, 24 consecutive 5-second samples:

```
mean 931.0 %   median 931.0 %   min 912.5 %      (10-core box)
```

**93 % of the machine, at 120× the n=10 table size.** Over the 8-minute A/B runs
of §4.2 the per-run means are 784–856 % with medians 927–937 % — dragged down by
a handful of deep dips, not by a sustained collapse.

### 2.4 So what was the 45 % `__psynch_cvwait`, and what was 900 % → 426 %?

Two separate misreadings. Both are worth recording, because the programme has
been steering by them since M2b §8.1.

**The 45 % is a thread-census artefact.** M2b's flat profile sampled **22
threads** on a 10-core box. `num_cpus::get()` is 10, so there are 10 pool
workers; the other ~12 are the `async-std` runtime, the main thread and
jemalloc background threads, and they are *supposed* to be parked. If 10 threads
are busy and 12 are parked, 12/22 = 54.5 % of samples land in a wait primitive
with the machine fully busy. M2b measured
`cvwait` + `mutexwait` + `kevent` + `semaphore_wait` = **58 %**. The counters
confirm it from the other side: over a 2.95 s n=10 search the ten workers spend
**139 ms in total** inside `recv_timeout` — 0.47 % of worker capacity (§4.1).

**The 900 % → 426 % was memory pressure.** `evidence/v3/n11-attempt1-oom.md`
records the machine at death: swap 9,923 MB of 11,264 MB used, ~156 MB pages
free. That is a thrashing box, and utilisation collapse is what thrashing looks
like. Supporting evidence from this campaign: the same n=11 iteration at
`DIMS=24` holds 931 % CPU at **235 MB RSS**, against the ~1.5 GB the killed
`DIMS=96` run carried at 3 h; and the state-exploration rate decays 17× over
8 minutes (39.3 k/s → 2.3 k/s, §4.2) **while CPU utilisation stays flat**, which
is the signature of rising cost per state — the subsumption index growing — and
not of lost parallelism.

**Consequence for the programme:** M2b §8.1's recommendation ("the thread pool
is now the second-largest cost… if the n=11 `--limit` run shows poor scaling on
many cores, this is the thing to fix") should be retired at 10 cores. It may
still be right at 48 threads; nothing here measures that.

---

## 3. What was built

### 3.1 Thread pool (`src/thread_pool.rs`)

Three changes, all env-gated so upstream scheduling is exactly recoverable
(`SORTNETOPT_POOL=upstream`), and all promotion-order-preserving.

**P1 — skip the global lock when it is provably a no-op.** An `AtomicUsize`
mirrors `pending.queue.len()`, published under the write lock. When it reads 0
*and* `pending_receiver.is_empty()`, the whole block is skipped: with both
empty, upstream's ingest loop body never executes and its promote loop never
executes, so the block's only effect is to acquire and release the global write
lock. A stale-high read costs one unnecessary acquisition; a stale-low read
cannot hide work, because the channel is checked too and `add_pending` publishes
there first.

**P2 — batched promotion.** Upstream schedules exactly one pending task per
global-write-lock round trip. Tier 2b schedules up to `SORTNETOPT_POOL_BATCH`
(default `num_cpus`), still strictly in ascending `(Prio, id)` order off the
same `BTreeMap`. Promoting the top-B is what B successive upstream acquisitions
by B different workers would have produced, minus the serialisation; and since
`Schedule::schedule()` sends to the crossbeam ready channel, one worker's
acquisition now becomes wake-ups for several others.

**P3 — no 10 ms park while promotable work exists.** Upstream parks for 10 ms on
an empty ready queue even when pending work is waiting to be promoted, because
`add_pending` only sends on a channel and nothing wakes a parked worker. Tier 2b
uses a 50 µs park (`SORTNETOPT_POOL_SPIN_US`) in that case, capped at
`SORTNETOPT_POOL_SPIN_ROUNDS` = 64 consecutive short parks. It cannot spin a
core: the promote loop *removes* every entry it walks, dead weak refs included,
so a stale map drains to empty in a bounded number of acquisitions.

Plus 14 `pool_*` counters and a search-phase park/wall pair.

### 3.2 Checkpoint/restart (`src/search/checkpoint.rs`, new)

**Captured state.** (1) the `StateMap` memo table —
`(channels, packed bitmap, State)` for every live entry, which is the entire
persistent state of the search; (2) the on-line subsumption index —
`(k, packed bitmap, abstraction point, value)`, the popcount bucket being
derivable from the bitmap; (3) nothing else. The successive-approximation
position is *implicit*: `Search::search` reads the root's state out of the
`StateMap`, so restoring the table restores the iteration position. In-flight
async frames are deliberately not captured — `improve` recomputes them.

**Consistency: a global quiesce, and why not a cheaper tear.** `StateMap::set`
is the only write path (index insert/evict, `remove_state` mirroring, shard
write). It holds a gate `RwLock` in **read** mode for its whole body; the
checkpointer holds it in **write** mode across the snapshot. Lock order is
`gate → {index buckets, state shards}` in both paths, and `set_inner` is a plain
`fn`, not an `async fn`, so the type system — not discipline — guarantees the
gate is never held across a suspension point (internals §3.6 invariant 3).

A shard-by-shard tear would have been cheaper and would still have been
*sound*: every stored interval is valid in isolation, so any subset is a valid
memo table. It was rejected because a tear can retain a parent whose bound was
derived from a child the tear dropped, and `GenProof::prove_all` **panics**
("no valid proof step found") when a retained set has no justification
(internals §3.6 invariant 4). That failure would surface only after a
multi-hour search plus a prune pass. A globally quiesced snapshot needs no new
argument at all: it *is* a state the live run passed through, so everything true
of the running search at that instant is true of the resumed one.

**The gate is striped.** A single shared `RwLock` cost a measured **+1.98 %** at
n=10 — 108 k read acquisitions by ten threads on one cache line. It is now one
`#[repr(align(128))]`-padded `RwLock<()>` per CPU, with each thread choosing its
stripe once (a `thread_local!` over an `AtomicUsize`), so a `set` touches only
its own line. The checkpointer takes **every** stripe in write mode, in
ascending index order, which preserves global consistency exactly (a `set` can
only be in flight while holding some stripe, and all of them are held) and
cannot deadlock (ascending acquisition; a `set` only ever holds one). Measured
overhead fell to **+0.57 %** (§4.4).

**Format.** 128-byte header (magic, `format_version`, flags, 32-byte identity
SHA-256, channels, seq, totals, elapsed, root bounds, FNV-1a header hash over
bytes 0..120), then the identity string verbatim so a refusal can print what
differed, then a STATES section per channel count 3..=11, then an INDEX section
per width, then a 32-byte payload SHA-256 and an end magic. Written to
`checkpoint.bin.tmp`, `flush`ed, `rename`d over `checkpoint.bin` (atomic on
APFS), then the *directory* is fsynced — otherwise a power loss can leave
neither name pointing at the new inode.

**The payload fsync is deliberately outside the quiesce.** `flush()` is the last
operation that must observe the frozen state; `sync_all()` only pushes bytes the
kernel already owns down to the device. Doing it after the guards drop keeps the
stall proportional to the walk rather than to device latency.

**Identity string** (hashed into the header): build id, channels, limit, prefix,
`MAX_CHANNELS`, subsume mode, the sorted `(width, point_dim)` list, and the two
Tier-1 filter flags. Shard count and `num_cpus` are deliberately **excluded** —
shard assignment is recomputed from the packed key on load, so a checkpoint
stays portable between machines.

**Resume** validates in order — magic, `format_version`, header hash, identity
hash, trailer magic, payload hash — each with its own actionable message, and
**nothing is restored until all of them pass**. Any invalid file is fatal: there
is no fall-back-to-fresh and no override flag. Restore bypasses `set` entirely
(no index insert, no eviction), rebuilding the shard key with the same
`FxHasher`-of-`PVec` rule `get`/`set` use.

**Configuration.** `SORTNETOPT_CHECKPOINT_DIR` (unset ⇒ disabled, and then `set`
never touches the gate and no stripes are allocated, so the run is bit-for-bit
the pre-Tier-2b path), `..._INTERVAL_SECS` (default 600, 0 ⇒ final write only),
`..._RESUME`, `..._KEEP_PREV`, `..._FINAL`.

---

## 4. Validation

### 4.1 Gate 1 — results, bound sequences, state bands

36 runs, 6 per configuration, interleaved round-robin, quiet machine, on the
frozen binary of §1.

| cfg | binary | n | pool | result | distinct bound sequences | peak `StateMap` entries |
|---|---|---|---|---|---|---|
| B9 | Tier-1 ref | 9 | upstream | 25 ×6 | 1, = reference | 35,163–35,845 |
| T9 | Tier 2b | 9 | new | 25 ×6 | 1, = reference | 35,196–36,000 |
| U9 | Tier 2b | 9 | upstream | 25 ×6 | 1, = reference | 35,166–35,815 |
| B10 | Tier-1 ref | 10 | upstream | 29 ×6 | 1, = reference | 35,150–35,900 |
| T10 | Tier 2b | 10 | new | 29 ×6 | 1, = reference | 35,524–35,923 |
| U10 | Tier 2b | 10 | upstream | 29 ×6 | 1, = reference | 35,317–35,867 |

* **`result = 25` in all 18 n=9 runs and `29` in all 18 n=10 runs.**
* **Exactly one distinct bound sequence per configuration**, equal to the
  reference: n=9 `5, 8, 11, 14, 17, 19, 21, 22, 23, 24, 25`;
  n=10 `5, 9, 12, 15, 18, 21, 23, 25, 26, 27, 28, 29`.
* Peak entries 35,150–36,000 across all 36 runs, inside the Tier-1 band
  (35,289–36,172) to within run-to-run scatter, with no systematic shift.

A further 18 runs (§4.4), 36 pre-stripe runs, 4 runs at n=11 (§4.2), 8
kill/resume pipelines (§4.3) and 4 patch-provenance runs (§1.1, §1.4) all
reproduced their expected results: **over 100 searches, no deviation.**

**Gate 1: PASS.**

Pool counters, 6-run means at n=10 — the structural effect, load-independent:

| counter | T10 (new) | U10 (upstream) | |
|---|---|---|---|
| `pool_lock_acquires` | **340** | 7,838 | **23.0× fewer** |
| `pool_lock_skipped` | 5,542 | 0 | P1 |
| `pool_promotions / pool_promote_batches` | **8.42** | 1.00 | P2 |
| `pool_park_short` | **1** | 0 | P3 essentially never fires |
| `pool_park_long` | 5,571 | 5,562 | dominated by the post-search idle tail |
| `pool_tasks_run` | 112,735 | 112,636 | |
| `pool_search_park_ns` | 138.7 ms | 125.5 ms | over 10 threads × ~2.95 s |
| `pool_search_utilisation_bp` | 9,952 | 9,957 | 99.5 % *not parked* |

Read together, the diagnosis is complete: P1 and P2 do exactly what they were
designed to do, and **P3 has nothing to fix — the workers were never parking.**
139 ms of park time across 30 thread-seconds is 0.47 %. The gap between that
99.5 % "not parked" figure and the 94 % the sampler measures is lock blocking
elsewhere (index buckets, shards, the per-set async lock) plus OS scheduling —
not the pool's park path. `pool_search_utilisation_bp` is reported as the upper
bound it is; `tools/cpu_sampler.py` is the ground truth.

### 4.2 Objective 1 outcome — the n=11 A/B

Each arm gets a fixed 480 s budget inside the 33 → 34 iteration at n=11
(`--limit 35`, `DIMS=24`, widths 8,9), both with checkpointing on at the same
120 s interval so the comparison isolates the scheduler, and is then SIGKILLed.
The metric is states explored within the budget.

| arm | run 1 | run 2 | mean | within-arm spread |
|---|---|---|---|---|
| new pool | 2,262,257 | 2,237,787 | **2,250,022** | ±1.1 % |
| `POOL=upstream` | 2,236,836 | 2,287,142 | **2,261,989** | ±2.2 % |
| | | | **ratio 0.995×** | |

**The new pool is 0.5 % slower on the mean, and the between-arm difference is
well inside the within-arm spread.** There is no measurable throughput effect at
n=11 on 10 cores, in either direction.

Utilisation and state rate over the same runs, 8 bins:

| minutes | new_r1 util | upstream_r1 util | new_r1 states/s | upstream_r1 states/s |
|---|---|---|---|---|
| 0–1 | 810 % | 934 % | 39,338 (100 %) | 36,162 (100 %) |
| 1–2 | 786 % | 940 % | 5,642 (14 %) | 5,536 (15 %) |
| 2–3 | 790 % | 929 % | 4,912 (12 %) | 4,797 (13 %) |
| 3–4 | 775 % | 896 % | 4,629 (12 %) | 4,078 (11 %) |
| 4–5 | 790 % | 781 % | 4,123 (10 %) | 4,580 (13 %) |
| 5–6 | 773 % | 782 % | 3,249 (8 %) | 3,311 (9 %) |
| 6–7 | 783 % | 785 % | 2,928 (7 %) | 3,031 (8 %) |
| 7–8 | 789 % | 785 % | 2,302 (6 %) | 2,432 (7 %) |

Two things to take from this. First, **the state rate falls 17× while
utilisation stays within a factor of 1.2** — the deep-iteration slowdown is cost
per state, not lost parallelism, which is precisely what a scheduler fix cannot
help. Second, the utilisation difference in the first four bins (786–810 % vs
896–940 %) is the only apparent effect, it points the *wrong* way for the new
pool, and the throughput is identical anyway; with two runs per arm and this
much per-bin variance it is not a result, and it is reported rather than
dropped.

**Objective 1 verdict: the change is retained as a behaviour-preserving
scalability guard with a 23.0× reduction in global-lock traffic, and is
explicitly NOT credited with a speedup. The expected 1.8× does not exist at
10 cores, because the deficit it was meant to recover does not exist.**

### 4.3 Objective 2 outcome — kill/resume, with certificates

Eight full pipelines, every one
`search → prune-all (SORTNETOPT_CROSS_BOUND_PRUNE=1) → gen-proof → frozen snocheck -v +RTS -N10 -RTS`.
The kills are `kill -9` on a running search, with no cleanup and no signal
handler; the resumed run is a fresh process pointed at the same checkpoint
directory.

| case | killed at | as % of the final iteration | resumed from | result | `snocheck -v` | final `StateMap` |
|---|---|---|---|---|---|---|
| n=10 control | — | — | — | 29 | **`Just (10,29)`** | 35,959 |
| n=10 killed→resumed | 28,164 states | **75 %** | seq=2, 1,036,533 B, 5 ms | 29 | **`Just (10,29)`** | 35,808 |
| n=10 control (2) | — | — | — | 29 | **`Just (10,29)`** | 35,733 |
| n=10 killed→resumed (2) | 19,125 states | **45 %** | seq=1, 661,528 B, 3 ms | 29 | **`Just (10,29)`** | 35,960 |
| n=9 control | — | — | — | 25 | **`Just (9,25)`** | 35,830 |
| n=9 killed→resumed | 19,608 states | **47 %** | seq=1, 672,360 B, 3 ms | 25 | **`Just (9,25)`** | 36,115 |
| n=10 control, final binary | — | — | — | 29 | **`Just (10,29)`** | 35,779 |
| n=10 killed→resumed, final binary | 19,388 states | **46 %** | seq=1, 666,628 B, 3 ms | 29 | **`Just (10,29)`** | 36,065 |

Final state counts 35,733–36,115 across controls and resumes alike, inside the
Gate-1 band. **The certificate is accepted in every case, and no `prove_all`
panic occurred in any run** — which is the specific failure the global quiesce
was chosen to prevent.

**Resume refusal, 4/4:**

| injected mismatch | outcome |
|---|---|
| `SUBSUME_DIMS` 12 → 16 | refused, non-zero exit, printed both identity strings (`subsume_index=7:12,8:12` vs `7:16,8:16`) |
| channels 10 → 9 | refused, printed the differing `channels=` line |
| one byte flipped in the body | refused: `payload hash mismatch: stored 436d15ba…, computed 0d350441…` |
| one byte flipped in the header | refused: `header hash mismatch: stored 0xa69fbeb1…, computed 0x331d7f6b…` |

**n=11 scale.** From the §4.2 runs, snapshots of 0.96 M / 1.54 M / 1.98 M states
cost **138 / 220 / 372 ms** of stall and 31.6 / 49.1 / 62.8 MB of file — about
**32 bytes per stored state** and **~0.19 µs of stall per state**. Resuming
1,978,799 states plus 169,074 index entries from the 62.8 MB checkpoint took
**321 ms**, restored the root as
`State { bounds: [33, 35], huffman_bounds: [33, 33] }`, and the resumed process
went on to explore a further ~400 k states at 1,963–2,163 states/s — the same
rate the killed run was achieving at the same depth.

**Gate 2: PASS.**

### 4.4 Objective 2 cost — overhead decomposition

n=10, 6 runs per arm, interleaved round-robin, quiet machine, final binary.
Three arms separate the gate from the I/O.

| arm | search wall, 6-run mean | vs OFF | `ckpt_writes` | `ckpt_gate_acquires` | `ckpt_bytes` | `ckpt_stall_ns` |
|---|---|---|---|---|---|---|
| OFF (`..._DIR` unset) | 2,942 ms | — | 0 | 0 | 0 | 0 |
| GATE (`..._INTERVAL_SECS=0`, final write only) | 2,958 ms | **+0.57 %** | 1 | 107,998 | 1.36 MB | 16.9 ms |
| I1 (`..._INTERVAL_SECS=1`, 10 snapshots in a 3 s search) | 2,954 ms | **+0.44 %** | 10 | 107,747 | 12.6 MB | 140.0 ms |

Before the gate was striped (§3.2) the same three arms measured **+1.98 %** and
+1.87 %; a separate 18-round campaign on the striped build put GATE-vs-OFF at
**+0.58 %** with a 95 % CI of −0.53 % .. +1.70 %, i.e. **the residual overhead is
no longer distinguishable from zero at this sample size.** The honest claim is
"reduced from ~2 % to under 1 %", not "eliminated".

Three further readings:

* **End-to-end overhead is well inside the ≤2 % target**, even in the absurd
  configuration of ten full snapshots during a three-second search.
* **The cost is the gate, not the I/O.** GATE and I1 are within 0.15 % of each
  other despite a 9× difference in bytes written.
* **`ckpt_stall_ns` is an upper bound on lost throughput, not a measurement of
  it.** It runs from the moment the checkpointer asks for the write guards, and
  much of that interval is spent waiting for in-flight `set` calls to drain
  while every other thread is still doing useful non-`set` work. I1's 140 ms of
  "stall" produces no measurable wall-clock cost over GATE, which is the direct
  evidence for that.

At the default 600 s interval and the measured n=11 stall of 372 ms, the
snapshot contribution to runtime is **0.06 %**.

**Gate 3: PASS.**

---

## 5. Verdict against the Tier-2b objectives

| objective | outcome |
|---|---|
| 1. Reduce blocked-thread time in the deep final iteration; expect up to ~1.8× | **Measurement-refuted.** The n=10 final iteration already runs at 943 % of a 10-core box and a deep n=11 iteration at 931 %. Global-lock acquisitions cut **23.0×**, promotion batch factor 1.00 → 8.42, but the n=11 A/B is **0.995×**, inside the noise. Retained as a behaviour-preserving scalability guard, not as a speedup. |
| 2a. Consistent snapshot, deterministic-equivalent resume | **PASS.** Global quiesce; 4 kill-and-resume runs at 45–75 % of the final iteration, all `result` correct and all certificates accepted. |
| 2b. Bounded snapshot cost, <2 % at n=10, configurable interval | **PASS.** +0.57 % end-to-end; +0.06 % at the default 600 s interval; `SORTNETOPT_CHECKPOINT_INTERVAL_SECS`. |
| 2c. Versioned and fsynced format | **PASS.** `format_version`, magic, header FNV-1a, payload SHA-256, tmp → fsync → rename → dir-fsync. |
| 2d. Resume refuses on mismatch | **PASS.** 4/4: config mismatch ×2, body corruption, header corruption. No override flag exists. |
| Certificates | **10/10 accepted by the unchanged verified checker** (8 kill/resume pipelines + 2 patch-provenance pipelines). |
| Independence from Tier-2a | **Verified by construction:** the two patches stack cleanly and the stacked build passes n=9 to `Just (9,25)`. |

---

## 6. What this does for n=13 multi-week runs

The checkpointing is the part that matters, and it changes the risk profile
rather than the compute. A multi-week n=13-class run on hardware that is not
perfectly reliable is otherwise a wager that nothing — an OOM kill, a power
event, a kernel panic, an operator mistake — interrupts it for the whole period;
the killed n=11 run lost 4 CPU-hours to exactly that, and the same failure at
n=13 scale would lose weeks. With a snapshot every 600 s the worst-case loss
becomes 10 minutes, at a measured cost of 0.06 % of runtime for the snapshots
plus under 1 % for the gate. And because the identity hash excludes shard count
and `num_cpus`, a checkpoint is portable between machines, which makes "move the
run to a bigger box" a supported operation for the first time.

The design has a scaling limit that should be stated rather than discovered. The
stall is a global quiesce whose cost is linear in the live table: **~0.19 µs per
stored state** measured at n=11 (372 ms for 1.98 M states), and ~32 bytes per
state on disk. Extrapolating: 10^8 states ⇒ ~19 s stall and a ~3.2 GB file,
which is fine against an hourly interval (0.5 %); 10^9 states ⇒ ~190 s stall and
a ~32 GB file, which needs a ≥3 h interval to stay under 2 % and starts to be
awkward. Beyond that, the global quiesce should be replaced by generational or
per-shard-incremental snapshots — writing only the shards dirtied since the last
checkpoint, with an occasional full snapshot. The format already supports it
(the STATES section is a flat list of independent records and the shard is
recomputed from the key on load), but it is **not implemented**, and it is the
natural Tier-3 follow-on. None of this moves the two real n=13 blockers, which
are unchanged: the memory exponent, and the `u32` certificate step count that
caps a proof at 4.29e9 steps against an n=13 estimate of 1.5e11
(internals §6.3).

The thread-pool work contributes nothing to the n=13 time budget on a 10-core
box and should not be counted in any projection. It may still matter at 48
threads, where the global `pending` lock is taken ~5× more often; the 23.0×
reduction in acquisitions is insurance against that, bought at no measured cost.
**But that is a hypothesis, not a measurement — nothing in this campaign ran on
more than 10 cores**, and if the programme wants the 48-thread question
answered it needs a 48-thread box, not another M4 campaign.

---

## 7. Recommendations

1. **Land it**, primarily for the checkpointing. Run every n≥11 search with
   `SORTNETOPT_CHECKPOINT_DIR` set and `..._INTERVAL_SECS=600`.
2. **Retire M2b §8.1's thread-pool recommendation at 10 cores.** §2.4 shows both
   of its supporting observations were misread. Do not spend further effort on
   the scheduler without a many-core box to measure on.
3. **The n=11 memory story is much better than the killed run suggested.**
   `DIMS=24` holds 931 % CPU at **235 MB RSS for 3.1 M states**, against the
   ~1.5 GB the `DIMS=96` run carried. The OOM was as much a `DIMS` choice as a
   machine-size problem; re-derive the n=11 budget at `DIMS=24` before assuming
   a bigger box is needed.
4. **Generational checkpoints are the Tier-3 item** (§6), needed before the
   table exceeds ~10^8 entries.
5. `pool_search_utilisation_bp` is an upper bound (it counts mutex blocking as
   busy). Quote `tools/cpu_sampler.py` in any future utilisation claim.

---

## 8. Re-measurement commands

Confirm the machine is quiet first: `ps aux | grep sortnetopt | grep -v grep`
must be empty and `uptime` should show a load average below 1.

```
# Gate 1 (36 runs, interleaved round-robin, with CPU sampling)
cd <ABS>/.build/v3-tier2b
python3 campaign.py --config cfg_main.json --rounds 6 --out campaign_final

# Utilisation curve for one run
python3 util_report.py --cpu campaign_final/T10/run1/cpu.csv \
                       --json campaign_final/T10/run1/instrument.json

# Kill/resume + certificate, n=10 (NSNAP=1 kills at ~46% of the final iteration)
NSNAP=1 bash killresume.sh 10 <ABS>/.build/v3-tier2b/kr_final

# Overhead decomposition (18 runs)
python3 campaign.py --config cfg_ovh.json --rounds 6 --out ovh_final

# n=11 scale A/B, 480 s per arm, 2 rounds, plus the n=11 resume test
bash n11ab.sh 480 2 <ABS>/.build/v3-tier2b/n11ab

# Recommended n>=11 invocation
SORTNETOPT_SUBSUME=evict SORTNETOPT_SUBSUME_DIMS=24 SORTNETOPT_SUBSUME_WIDTHS=8,9 \
SORTNETOPT_CHECKPOINT_DIR=<datadir>/ckpt SORTNETOPT_CHECKPOINT_INTERVAL_SECS=600 \
  sortnetopt -m search 11 <datadir>/_search_11
# ... and to resume after a kill, the same line plus:
SORTNETOPT_CHECKPOINT_RESUME=1
```

---

## 9. Artifacts

Under `.build/v3-tier2b/` (build directory, not committed):

* `source/` — detached worktree at the pin, six patches applied
* `base-tree/` — the same tree at the 5-patch Tier-1 state, used to generate the diff
* `verify/` — the patch round-trip worktree (§1.1) and its n=9 certificate
* `verify-ab/` — the stacked Tier-2a + Tier-2b worktree (§1.4) and its n=9 certificate
* `wt-pool/`, `wt-ckpt/`, `wt-stripe/` — the three disjoint development trees
* `bin/sortnetopt-base`, `bin/sortnetopt-tier2b` — the two frozen binaries
* `campaign_final/` (and the superseded pre-stripe `campaign_main/`) — the 36-run Gate-1 campaigns with per-run `cpu.csv` and `summary.json`
* `ovh_final/`, `ovh/` — the overhead decompositions
* `kr_final/`, `kr10/`, `kr10_half/`, `kr9/` — the eight kill/resume pipelines with `proof.bin` and `snocheck.out`
* `n11ab/` — the four 480 s n=11 A/B runs plus `resume11/`, with `cpu.csv` traces
* `n11probe/probe-partial.log` — the 15.5-minute n=11 `--limit 34` probe of §2.3
* `campaign.py`, `util_report.py`, `killresume.sh`, `n11ab.sh` — the drivers

Committed: `tools/patches/sortnetopt-tier2b-v3.patch`, `tools/cpu_sampler.py`,
this report.

---

## 10. Deviations and open items

* **Objective 1's premise was refuted rather than met.** The campaign was
  briefed to expect ~1.8×; it measured ~1.00×. The changes were kept because
  they are provably behaviour-preserving and reduce global-lock traffic 23×, but
  this report deliberately does not dress that up as a win. §2.4 gives the
  reinterpretation of the two observations that motivated the work.
* **Nothing here ran on more than 10 cores.** Every claim about 48-thread
  behaviour is a hypothesis.
* **The n=11 A/B is 2 runs per arm, not 6**, because each run costs 8 minutes.
  The within-arm spread is reported so the reader can see that 2 runs suffices
  to establish "no effect" and would not have sufficed to establish a small one.
* **The n=11 arms are SIGKILLed at the budget**, so they produce no
  end-of-process counter block; states/budget from the 10-second log lines and
  the sampled utilisation curve are the metrics there. Full counters exist only
  at n≤10.
* **The residual gate overhead (+0.57 %) is not statistically distinguishable
  from zero** at 6 rounds (18-round pooled estimate +0.58 %, 95 % CI −0.53 % ..
  +1.70 %). The pre-stripe +1.98 % was well outside the noise; the post-stripe
  figure is a point estimate, and it is reported as one.
* **`ckpt_stall_ns` overstates lost throughput** (§4.4) and is reported as an
  upper bound.
* **`pool_loop_ns` spans each worker's whole lifetime**, which includes the
  ~10 s floor the stats logger imposes on every process (M0b §4), so a
  utilisation figure derived from it measures "busy / 10 s". That is why
  `pool_search_park_ns` / `pool_search_wall_ns` were added and why the report
  quotes the sampler instead.
* **Resume validates the file twice** — once to check the payload hash, once to
  restore — so a resume reads the checkpoint twice. This is deliberate (nothing
  is restored until every check passes) and costs 321 ms at n=11 scale.
* **Stripe assignment is first-come-first-served** over a global counter, so a
  few non-worker threads consume indices before the pool workers do. With 10
  workers and 10 stripes that still produced a collision-free assignment, but
  that is arithmetic luck, not a guarantee; a collision would cost sharing, not
  correctness.
* **Generational/incremental checkpointing is not implemented** (§6), and is the
  stated limit of this design at ~10^8 entries.
* **`KEEP_PREV` retention is implemented but off by default**; the atomic rename
  already makes a torn checkpoint impossible, so the previous file is insurance
  against a bad *good* checkpoint, not against a partial write.
* **Timings were taken on a shared machine.** The Gate-1, overhead and n=11
  campaigns ran in windows where `ps aux` showed no other `sortnetopt` or
  `cargo` process, and every campaign is interleaved round-robin so load drift
  hits all arms equally; §8 gives replay commands. The Tier-2a campaign was
  active on the same host earlier in the session; the §2.3 live probe was taken
  at load average 25, which is why its utilisation is quoted from 24 consecutive
  samples of a single process rather than from a comparison.
