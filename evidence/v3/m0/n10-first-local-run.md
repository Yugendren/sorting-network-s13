# M0 exploratory run: full n=10 lower-bound pipeline, local M4

Date: 2026-08-17. Contract: METHOD_EXPERIMENT_CONTRACT_V3.md. Status:
exploratory M0 profiling (pre-instrumentation); recorded for the M1
scaling law.

## Result

**S(10) >= 29 proved and verified locally, end-to-end, in under a
minute.** Verified checker output: `Just (10,29)`.

## Environment

- Host: M4 Mac mini (Mac16,10), 10 cores, 16 GiB RAM, macOS (Darwin 25.5.0).
- Toolchain: frozen B3 attempt `attempt-20260815T000526Z`
  (sortnetopt pinned `0b5d09c47446096f9e3a0812b35afc72b7f2a718` + two
  portability patches; Rust 1.95.0; snocheck GHC 8.6.5 x86_64/Rosetta).

## Commands and measurements

1. Search + prune (`bash search_and_verify.sh 10 <data>` from the frozen
   toolchain source dir; script's final checker step fails on macOS
   because it calls system `stack` — search and prune-all completed):
   - Search: `result = 29` at 10.027 s; states at final bound
     step 207,659; bound trajectory 26→27→28→29 with states
     38 → 479 → 25,523 → 207,659.
   - Wall for search+prune stage: 15.89 s real, 14.36 s user, 0.90 s sys.
   - Peak RSS: 89,964,544 B (~86 MiB).
2. Certificate generation (`cargo run --release -- -m gen-proof <dir>`):
   ~4 s, peak footprint 42,942,896 B (~41 MiB).
   - `proof.bin`: 1,566,522 B, SHA-256
     `b9785216b52534610da21289fe6a2e20ca208e3bfb7010b23d8dc1e990cbd115`.
3. Verified check (`./bin/snocheck -v +RTS -N10 -RTS <proof.bin>`):
   1.89 s real, 8.84 s user, peak RSS 22,867,968 B (~22 MiB) →
   `Just (10,29)`.

Data directory total: 6.4 MB. Run artifacts under
`.build/v3-m0/n10-explore/` (build dir, not committed; log preserved
there as `run.log`).

## Scaling-law observations (feeds M1)

| n | search wall | peak RSS | result | source |
|---|---|---|---|---|
| 9 | ~13 s (in 15.4 s total gate) | ~95 MiB | 25 | evidence/b3 (M4) |
| 10 | 10.0 s search, 15.9 s stage | ~86 MiB | 29 | this run (M4) |
| 11 | 17,460 s (24-core box) | ~178 GiB | 35 | Harder, docs/sota-survey.md |

The n=10 → n=11 cliff is ~10^3× time and ~2×10^3× memory. n=9 and n=10
are nearly identical in cost — the state explosion begins between 10 and
11. Direct-run n=13 therefore remains ~10^6-10^7× beyond n=11 in memory,
consistent with Harder's >20,000 TB estimate: closing it requires the
M2 memory attack plus restricted-class/interval strategies, not constant
factors alone.

## Deviations

- `search_and_verify.sh` final step invokes system `stack`, which cannot
  provision GHC 8.6.5 on macosx-aarch64. The B3 gate solved this with a
  Rosetta wrapper; here the prebuilt `bin/snocheck` was invoked directly.
  Search, prune, proof generation, and verification all used frozen
  binaries/toolchain; no source was modified.
