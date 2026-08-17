# n=11 full-search attempt 1: killed by memory pressure (M4)

Date: 2026-08-17. Status: FAILED RUN, preserved per append-only rules.

## What happened

- Launch: full n=11 search, M2b stack binary (`sortnetopt-m2b`),
  `SORTNETOPT_SUBSUME=evict SORTNETOPT_SUBSUME_DIMS=96
  SORTNETOPT_SUBSUME_WIDTHS=8,9`, M4 Mac mini (16 GiB), while Tier-1
  and Tier-2a agent campaigns (cargo builds, validation batches) shared
  the machine.
- Death: at 249:40 wall (4 h 9.7 m), 20,289,501 states, in the final
  bound iteration (34 -> 35, entered at 9:05.9). Log ends mid-stream
  with no panic and no time(1) summary; the `echo exit=$?` never ran ->
  the whole process tree received SIGKILL.
- Post-mortem system state: swap 9,923 MB used of 11,264 MB, pages free
  ~156 MB -> classic macOS memory-pressure kill. Process-visible RSS was
  only ~1.5 GB at 3 h, but total system pressure (search + jemalloc
  retention + concurrent cargo builds + OS) exhausted the 16 GiB box.
- Loss: all in-memory search state (the engine has no checkpointing);
  no dumps had been written (dump happens at search end). ~4 CPU-hours.

## Lessons (fed into the programme)

1. Long prover runs get a dedicated machine. Agent build campaigns and
   the prover must not share a 16 GiB box.
2. Checkpoint/restart support is now a documented Tier-2 requirement —
   at n=13-class scale, multi-day runs without checkpointing are
   unacceptable.
3. The full-run memory footprint at n=11/DIMS=96 exceeds what a loaded
   16 GiB machine can host; the earlier "~6 GB" projection did not
   account for allocator retention + co-tenants. Measure, as always.

## Recovery

Relaunched immediately on the ollama server (47 GiB RAM, quiet, Tier-1
AVX2-native binary validated by the x86 smoke test) at
/data/mericanii_s13_method_v3/n11-full/. Early telemetry: reached bound
33 in 1.4 s with 133k states (M4 M2b baseline took ~9 min to the same
point); this run doubles as the Tier-1 n=11 measurement. The M4 role
swapped to hosting Tier-2a benchmarking.

Partial baseline data preserved at `.build/v3-n11-full/run.log` (M4,
20.3 M states over 4 h 9 m — usable as a rate/memory reference for the
M2b engine at n=11 scale even though incomplete).
