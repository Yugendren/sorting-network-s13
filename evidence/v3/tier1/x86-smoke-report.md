# Tier 1 cross-platform smoke test: x86-64 Linux (scalar fallback)

Date: 2026-08-17. Contract: `METHOD_EXPERIMENT_CONTRACT_V3.md` (§2 pin
discipline, §5 evidence rules). Predecessor: `evidence/v3/tier1/report.md`
(the arm64/NEON validation on the M4).

**Status: PASS.** The five-patch Tier-1 stack applies, builds and runs
correctly on x86-64 Linux with **no source changes of any kind**. All PASS
criteria hold: `result = 25` (n=9) and `29` (n=10), both reference bound
sequences reproduced exactly, `idx_clamps = 0`, `filter_audit_violations = 0`.
Two certificates generated entirely on x86-64 were shipped to the Mac and
**accepted by the unchanged frozen Isabelle/HOL-extracted checker**:
`Just (9,25)` and `Just (10,29)`.

**The primary finding is a negative one, and that is the good outcome: there is
no Tier-1 portability defect.** The NEON path is correctly compile-gated, the
portable scalar fallback is selected on x86-64, and its 7 oracle unit tests pass
against the `OutputSet` reference at every channel count. The single item worth
recording is a cosmetic patch-application difference (§2).

---

## 1. Environment

| | |
|---|---|
| host | SSH alias `ollama` |
| OS | Ubuntu 24.04.1 LTS, kernel `6.8.0-124-generic` |
| arch | `x86_64` |
| CPU | AMD Ryzen 5 3600 6-Core, **exposed as 10 vCPUs under a hypervisor** |
| RAM | 47 GiB |
| rustc | `1.97.1 (8bab26f4f 2026-07-14)` |
| cargo | `1.97.1 (c980f4866 2026-06-30)` |
| toolchain | stable, `minimal` profile, installed by `rustup-init -y --no-modify-path` |
| gcc | 13.3.0 (present; not used by the Rust build) |
| baseline `target_feature` | `fxsr`, `sse`, `sse2` — **no AVX2** |

Two deployment notes, both deliberate:

* **The root disk was at 99 % (1.4 GiB free), so the Rust toolchain was
  installed onto `/data`**, not into `~/.cargo` / `~/.rustup`, via
  `RUSTUP_HOME` / `CARGO_HOME` / `TMPDIR` pointed at
  `/data/mericanii_s13_method_v3/tier1-smoke/toolchain/`. `CARGO_TARGET_DIR`
  likewise. Root-disk free space was 1.4 GiB before and after the entire
  campaign — nothing spilled onto it. Total workspace footprint: 2.4 GiB.
* **The default x86-64 target has only SSE2**, so the headline build exercises
  the *pure scalar* fallback, not an auto-vectorised one. This is the strictest
  available portability test, and is the configuration all §4 results use. A
  supplementary `-C target-cpu=native` (AVX2 + BMI2) build is reported in §6.

Workspace: `/data/mericanii_s13_method_v3/tier1-smoke/`. Nothing was written on
the server outside it. The local pinned clone was not modified
(`git status --porcelain` empty before and after).

## 2. Source shipment and patch application

Source was exported from the pinned clone without touching it:

```
git -C .cache/third_party/sortnetopt archive --format=tar \
    0b5d09c47446096f9e3a0812b35afc72b7f2a718 > <scratch>/ship/sortnetopt-pin.tar
```

`sortnetopt-pin.tar` SHA-256 `a243f270e7bffc77580b9a4d445966ee395cee4f85763aafc161a927ce0a020f`.
Patch SHA-256s were verified equal on both ends after `scp`; the Tier-1 patch
hash `5b6f180a24dce2b663b19134d923dc31815036deed3d4d8c1c1895e61db7ef3e` matches
`report.md` §1. All five applied with `patch -V none -p1` in the documented
order. **No `.rej`, no `.orig`, no failed hunk, no skipped patch.**

**The one difference from the M4 run.** `sortnetopt-macos-proc.patch` applied
with `Hunk #1 succeeded at 42 with fuzz 2`, where the M4 run recorded no fuzz.
This is a `patch(1)` implementation difference, not a content difference. It was
resolved rather than assumed: every `.rs` file in the patched server tree was
SHA-256'd and compared against the M4-validated tree at
`.build/v3-tier1/source/`. **Every per-file hash is identical**, including
`src/logging.rs`; the only diff was `sort` collation order between macOS and
Linux (`src/output_set.rs` ordering relative to `src/output_set/`). The server
tree is therefore byte-for-byte the tree the M4 campaign validated, and no
skip-the-macOS-patch contingency was needed.

For the record, the macOS patch is behaviourally inert on Linux: it replaces an
unconditional `.unwrap()` on `read_to_string("/proc/self/status")` with a match
returning `(0, "?")` on error. Linux always has `/proc/self/status`, so the new
branch is never taken.

## 3. Build outcome: **clean, no fix required**

```
cargo build --release      # 31.58 s wall, 744 % CPU
```

Exactly one warning — `unnecessary trailing semicolon` in
`src/output_set/canon.rs:86`, the same pre-existing upstream warning `report.md`
§1 records on the M4. No arch-specific compilation error, no `cfg` gap, no
linker issue. Binary SHA-256
`92396ddabe15d5e91e0302ea54e582cce887fa3d45a911833433d5edf1ae9486`
(85,197,832 B, at `<workspace>/target/release/sortnetopt`).

**No portability fix was needed, so no fix diff is attached.**

### 3.1 Unit tests — the scalar path validated against the oracle

`cargo test --release`: **14 passed, 0 failed.** Seven of these are the
Tier-1 `PackedSet` tests, which are exactly the ones that matter here, because
on this host they run the scalar fallback rather than the NEON path they
exercised on the M4:

```
output_set::packed::test::subsumes_unpermuted_matches_reference               ok
output_set::packed::test::swap_channels_matches_reference                     ok
output_set::packed::test::roundtrip_and_len_and_histogram_and_invert          ok
output_set::packed::test::low_channels_channel_abstraction_matches_reference  ok
output_set::packed::test::low_channels_channel_abstraction_with_matches_reference   ok
output_set::packed::test::low_channels_channel_abstraction_with_matches_standalone  ok
output_set::packed::test::hist_subsumes_signature_implication_random          ok
output_set::packed::test::hist_subsumes_and_signature_match_real_subsumes_permuted  ok
output_set::subsume::test::subsumes_permuted_packed_matches_brute_force       ok
```

`report.md` §2.2 asserts "the scalar path is kept and separately unit-tested, so
x86 builds are unaffected". That claim is now discharged **on an actual x86
build** rather than by cross-compilation reasoning.

## 4. Search results

All runs: `SORTNETOPT_SUBSUME=evict SORTNETOPT_SUBSUME_DIMS=12
SORTNETOPT_SUBSUME_WIDTHS=7,8`, 10 threads, output leaf dirs pre-created.

| run | result | bound sequence | matches reference | `idx_clamps` | `filter_audit_violations` | search wall | peak RSS | peak entries |
|---|---|---|---|---|---|---|---|---|
| n=9 scalar | **25** | `5,8,11,14,17,19,21,22,23,24,25` | **yes** | **0** | **0** | **2,464 ms** | 26,112 kB | 35,234 |
| n=10 scalar | **29** | `5,9,12,15,18,21,23,25,26,27,28,29` | **yes** | **0** | **0** | **2,488 ms** | 26,240 kB | 35,348 |
| n=9 scalar, `FILTER_AUDIT=1` | **25** | `5,8,11,14,17,19,21,22,23,24,25` | **yes** | **0** | **0** | — | — | — |
| n=9 AVX2 (`target-cpu=native`) | **25** | `5,8,11,14,17,19,21,22,23,24,25` | **yes** | **0** | **0** | 2,243 ms | — | 35,269 |
| n=10 AVX2 (`target-cpu=native`) | **29** | `5,9,12,15,18,21,23,25,26,27,28,29` | **yes** | **0** | **0** | 2,372 ms | — | 35,917 |

Bound sequences are character-for-character the required references. Search wall
is the `elapsed_ms` of the final iteration row, per `report.md` §10; process wall
was 10.01–10.02 s in every case, the stats-logger floor.

### 4.1 Filter soundness audit on x86-64

`SORTNETOPT_FILTER_AUDIT=1` at n=9, `DIMS=12`, widths 7,8:

| counter | audit run | non-audit n=9 |
|---|---|---|
| `filter_candidates` | 59,621,795 | 57,540,609 |
| `filter_sig_rejects` | 26,982,071 | 25,188,242 |
| `filter_sig_node_rejects` | **0** (disabled in audit, as documented) | 198,542 |
| `filter_hist_rejects` | 1,340,998 | 256,888 |
| `filter_exact_calls` | 5,360,864 | 3,833,899 |
| **`filter_audit_violations`** | **0** | **0** |

**~28.3 million filter rejections were individually re-checked against the exact
permuted-subsumption test on x86-64, with zero disagreements.** The
`filter_hist_rejects` inflation under audit (257 k → 1.34 M) reproduces the
mechanical effect `report.md` §5.3 documents and explains on arm64 (0.20 M →
1.38 M): without audit a signature-rejected candidate returns before the
histogram test can see it. That the *same* artefact appears with the *same*
magnitude on a different architecture is a small independent consistency check
on the filter wiring.

### 4.2 Counter block — first x86 data point, against the M4 reference

n=10, `DIMS=12`. M4 column is `report.md` §6.3 (6-run means).

| counter | **x86-64 scalar** | M4 / NEON | ratio |
|---|---|---|---|
| `filter_candidates` | 57,848,715 | 58,952,427 | 0.98 |
| `filter_sig_rejects` | 25,280,433 (**43.70 %**) | 25,874,094 (43.89 %) | 0.98 |
| `filter_sig_node_rejects` | 192,145 | 202,150 | 0.95 |
| `filter_hist_rejects` | 258,316 | 199,049 | 1.30 |
| `filter_exact_calls` | 3,893,106 (6.7 %) | 3,454,664 (5.9 %) | 1.13 |
| `subsume_calls` | 3,893,106 | 3,454,664 | 1.13 |
| `subsume_filter_matching` | 4,405,819 (1.13 / exact) | 3,976,740 (1.15 / exact) | — |
| **`subsume_table_builds`** | **114,873** (0.026 / `filter_matching`) | 114,971 (0.029) | 1.00 |
| `subsume_nodes` | 4,767,640 (1.22 / exact) | 4,347,426 (1.26 / exact) | — |
| `idx_clamps` | 0 | 0 | — |

The filter *rates* — the architecture-independent quantities — agree closely:
signature rejection 43.70 % vs 43.89 %, `filter_matching` per exact test 1.13 vs
1.15, `subsume_nodes` per exact test 1.22 vs 1.26. **`subsume_table_builds`, the
§7.6 regression tripwire, reads 114,873 against the M4's 114,971 — a 0.1 %
agreement, and nowhere near `subsume_filter_matching`.** The thread-local
abstraction-table cache works identically on x86.

The absolute counts differ by ~13 % on the exact-call axis. This is run-to-run
scatter of the parallel search, not an architectural effect: `report.md` §6.2
reports 3,905,117 exact calls for this same configuration in a different
campaign, which brackets the x86 figure.

Memory, n=10: `index_payload_bytes` 789,097, `combined_payload_bytes`
1,659,288, `peak_key_bytes` 728,799 — against the M4 Tier-1 bands of
790,918–814,846 / 1,663,005–1,697,332 / 729,867–739,831. x86 sits at or just
below the low edge of each, i.e. consistent. (n=9: 779,816 / 1,646,987 /
726,235.)

## 5. Certificates generated on x86-64, verified on the Mac

`prune-all` (`SORTNETOPT_CROSS_BOUND_PRUNE=1`) → `gen-proof` were run **on the
server**; the resulting `proof.bin` was `scp`'d to the Mac (SHA-256 verified
equal across the transfer) and checked with the frozen, unchanged checker
`.build/b3-toolchain/attempt-20260815T000526Z/bin/snocheck` (SHA-256
`4cd30511f73e7d7f6f3f7bc4083d84b37c0678f2156f85fcbfa186546218a84c`, matching
`report.md` §1), invoked `snocheck -v +RTS -N10 -RTS <proof.bin>`.

| n | survivors (all widths) | steps | `proof.bin` size | `proof.bin` SHA-256 | **`snocheck -v`** |
|---|---|---|---|---|---|
| 9 | 12,115 | 11,590 | 1,476,783 B | `70b0d5e845e9b272f428b720504d19018aa51679774d732cccefb74bd8aeb38d` | **`Just (9,25)`** |
| 10 | 12,169 | 11,595 | — | `3d3b0c503c7cd7ba4a6e81fec891b82f67130171dcd17e0fd4e3987aaf1eba9a` | **`Just (10,29)`** |

Per-width survivor breakdown (`gen-proof`), n=9 / n=10 by channel count:
3→4/4, 4→14/14, 5→82/82, 6→751/752, 7→3215/3208, 8→6100/6153, 9→1949/1955,
10→—/1.

**A certificate constructed end-to-end on x86-64 Linux by the scalar fallback
path is accepted by the arm64-built, Isabelle/HOL-extracted verified checker.**
The Haskell checker was not built on the server, as instructed.

**One honest deviation.** Survivor and step counts sit slightly *below* the M4
Tier-1 bands (`report.md` §5.2: 12,224–12,448 survivors, 11,654–11,904 steps):
12,115–12,169 and 11,590–11,595. The gap is ~0.5–0.9 % and both figures move together,
which is the signature of ordinary parallel-search nondeterminism in how many
states survive pruning — the same source of variation §5.2 already reports
across its own seven pipelines. It is not a correctness concern, because the
certificate is *checked*, not trusted, and both were accepted. It is recorded
because it is outside the previously published band and a future run should not
be surprised by it.

## 6. Timing: x86-64 vs the M4 reference — read the caveats first

**This is not a clean hardware comparison and must not be quoted as one.**

* Every M4 wall-clock number in `report.md` was taken **under heavy load** (a
  concurrent 10-thread n=11 search; load average 19–56). `report.md` says so
  repeatedly and calls its own timings "indicative only".
* This server was **quiet** (load average settling to ~0.7; one background
  process at ~17 % of a core).
* The server is a **VM exposing 10 vCPUs backed by a 6-core/12-thread Ryzen 5
  3600** — the vCPU count is not 10 physical cores, and is oversubscribed
  relative to the physical core count.

So the numbers below compare a quiet, virtualised Ryzen against a heavily loaded
M4. They bound the Ryzen advantage from above and almost certainly overstate it.

| n | x86-64 scalar, quiet | M4 / NEON, loaded (`report.md` §6.1) | apparent ratio |
|---|---|---|---|
| 9 | **2,464 ms** | 3,642.8 ms (3,481–3,916) | 1.48× |
| 10 | **2,488 ms** | 3,675.0 ms (3,492–4,211) | 1.48× |
| 10 | — | 3,890.0 ms (§6.5 sweep, `DIMS=12`) | 1.56× |

The defensible conclusions are narrow and negative, which is what a smoke test
should produce:

1. **There is no scalar-fallback performance cliff.** Losing the explicit NEON
   path does not put x86 in a different performance class. A naive expectation
   that the byte-per-vector → packed-u64 win is NEON-dependent is not supported;
   most of that win is representational (fewer loads, no `Vec<bool>`
   allocation), and it survives without hand-written SIMD.
2. **A like-for-like M4-vs-Ryzen comparison does not exist yet** and will not
   until the M4 numbers are re-taken on a quiet machine (`report.md` §8 gives the
   replay commands and §10 lists this as owed). Until then the honest statement
   is "same order, x86 no worse".

### 6.1 AVX2 supplementary point

A `-C target-cpu=native` build (enabling `avx2`, `bmi2`) also compiles clean and
gives identical results and bound sequences (§4). It is **1.10× faster at n=9**
(2,243 vs 2,464 ms) and **1.05× at n=10** (2,372 vs 2,488 ms).

The small size of this gain is itself informative: it confirms there is **no
hand-written AVX2 path** in the patch — `report.md` §2.2 specifies an explicit
NEON path and "portable scalar fallback compiled everywhere else" — so the
speedup is only LLVM auto-vectorisation of the scalar word loops. **A
hand-written AVX2/AVX-512 counterpart to the NEON path is therefore an
unexploited opportunity**, and given that the NEON path bought 1.6–2.4× on the
exact test (§2.5), it is plausibly worth more than 1.05–1.10×. This is not on
the critical path for correctness and is noted as an option, not a
recommendation.

## 7. Verdict

**PASS.** Every stated criterion holds:

| criterion | status |
|---|---|
| five patches apply, none skipped | **PASS** (byte-identical tree to M4) |
| `cargo build --release` succeeds | **PASS** (clean, 1 pre-existing warning) |
| `result = 25` (n=9) / `29` (n=10) | **PASS** |
| bound sequences exactly as required | **PASS** (both, all five runs) |
| `idx_clamps = 0` | **PASS** (all runs) |
| zero filter-audit issues | **PASS** (`filter_audit_violations = 0`, ~28.3 M rejections audited) |
| wall times and counter block recorded | **PASS** (§4.2, §6) |
| certificate accepted by frozen checker | **PASS** (`Just (9,25)`, `Just (10,29)`) |

## 8. Open items

* **The M4 timings remain load-inflated**, so the Ryzen/M4 comparison of §6 is
  not yet a hardware comparison. This is inherited from `report.md` §10, not
  introduced here.
* **Survivor/step counts are ~0.5–0.9 % below the published M4 bands** (§5). Both
  certificates were accepted; recorded so the band can be widened rather than
  treated as violated.
* **No hand-written x86 SIMD path exists** (§6.1). AVX2 buys only 1.05–1.10×
  through auto-vectorisation.
* **n=11 and above are untested on x86.** This smoke test covers n=9 and n=10
  only, and memory behaviour at n=13 scale is unprobed here; the server's 47 GiB
  and 324 GiB of `/data` make it a plausible host for larger runs, which is a
  reason to keep this workspace.
* **The server toolchain lives on `/data`, not in `~/.cargo`**, because the root
  disk has 1.4 GiB free. Any future work on this host must set `RUSTUP_HOME`,
  `CARGO_HOME`, `CARGO_TARGET_DIR` and `TMPDIR` accordingly or it will fill the
  root filesystem.
* **The Haskell checker is not built on the server** (deliberately). Certificate
  verification requires a round trip to the Mac.

## 9. Artifacts

On the server, under `/data/mericanii_s13_method_v3/tier1-smoke/`:

* `ship/` — the pinned source tar and the five patches, as transferred
* `source/` — extracted pin with all five patches applied
* `target/release/sortnetopt` — the frozen scalar build (SHA-256 `92396dda…`)
* `target-native/release/sortnetopt` — the supplementary AVX2 build
* `toolchain/` — relocated `rustup` / `cargo` roots
* `runs/n9/`, `runs/n10/` — searches, `prune-all`, `gen-proof`, logs, `proof.bin`
* `runs/n9audit/` — the `SORTNETOPT_FILTER_AUDIT=1` run
* `runs/native-n9/`, `runs/native-n10/` — the AVX2 searches

Locally: this report. The two `proof.bin` files were verified from the session
scratchpad and are not committed.
