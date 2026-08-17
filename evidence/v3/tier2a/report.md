# Tier-2a: Glasgow-Matcher Campaign — Correctness PASS, Speed Objective NOT MET

Date: 2026-08-17. (Report persisted by the orchestrating session; the
campaign agent's configuration blocked writing markdown reports.
Content condensed verbatim from its final report; full measurement
detail is in the patch header and .build/v3-tier2a/ artifacts.)

## Verdict

Correctness: **PASS**. Speed objective (2-5x on the exact matcher):
**NOT MET** — delivered 1.19-1.35x isolated kernel, **1.126x
end-to-end** (n=10, 12 rotating-order rounds, paired t=12.15).

**The premise was wrong, and proving that is the campaign's real
result:** profiling 8.84M real matcher input pairs BEFORE writing code
showed the matcher's search tree averages 1.058 nodes on rejecting
tests (94.5-94.8% finish in a single node; max 47 nodes across all
8.84M pairs). Glasgow/Django techniques attack search-tree size; there
is no search tree. The actual cost was per-node arithmetic (eager
abstraction computation), attacked with a depth-0 cache + laziness:
subsume_abstractions fell 15.78 -> 4.58 per test (3.44x) with the
node count provably unchanged.

## Validation

- Differential test: **17,949,584 pairs, zero verdict mismatches,
  zero invalid witness permutations**, four configurations, witness
  permutations independently validated. Exhaustive k! brute-force
  passes in all eight gate combinations.
- Certificates: five pipelines, all Just (9,25) / Just (10,29) from
  the unchanged frozen checker; filter_audit_violations = 0.
- Patch round-trip: six patches, no fuzz, byte-identical, clone clean.
- One runner mislabel (a gates-off run labeled default) was caught by
  the abstraction counter and re-run correctly — counters as tripwires
  worked as designed.

## Techniques rejected WITH measurement (preserved for the record)

- Nogoods/restarts, component decomposition: no tree to attack.
- Hall-set + full Regin all-different: fully implemented, verified
  against brute force on 217k configurations; catches 1-in-16,000
  extra infeasibilities at ~equal cost to its budget — not worth it;
  code preserved at .build/v3-tier2a/rejected/alldiff.rs.
- Minimum-domain-first ordering: ~1% negative, defaulted off.
- Partition-refinement pre-filter: belongs in index.rs, out of scope.

## Findings the programme must absorb

1. **~6% instrumentation tax in the stack since Tier-1** (7 contended
   global fetch_adds per exact test). Fixed here via counter batching
   (worth 1.056x alone). Tier-1's published 1.79x is understated —
   nearer 1.9x.
2. **Benchmark methodology**: fixed-order round-robin confounds config
   with position (flipped a result from -4.7% to +6.7%); rotating
   order is now the protocol standard.
3. **n=13 is memory-bound by 3-4 orders of magnitude, not time-bound.**
   Kernel speedups are not on the n=13 critical path; memory (SDD),
   distribution (canonical-prefix decomposition), the u32 certificate
   cap, and two newly-flagged hard engine limits — **MAX_CHANNELS = 11
   and PackedSet's [u64; 32]** — must all be raised before any n>=12
   run happens at all.
4. The kernel win is largest exactly in the low-DIMS regime Tier-1
   identified as memory-optimal for n=13 — the one place it compounds.

## Artifacts

- tools/patches/sortnetopt-tier2a-v3.patch (1,091 lines, SHA-256
  aa3e3c4362e3e76f2a42002eda65c6f2987cdc2f7c891dc84e480421752de726),
  touches only src/output_set/subsume.rs and src/instrument.rs.
- Binary, 17.9M-pair corpus (1.28 GB), bench harness, validation and
  timing trees under .build/v3-tier2a/.

Caveats: in-stack timings shared the M4 with Tier-2b (load ~23;
control drift measured at 2.7%) — a quiet-machine n=11 confirmation is
owed and queued behind the current server run.
