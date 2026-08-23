# n=11 Full Certification — COMPLETE: engine certified end-to-end

Date: 2026-08-22. The central credential of the v3 programme.

## The result

Our rebuilt engine (Tier-1 5-patch stack, AVX2-native x86 build)
independently re-derived S(11) >= 35 and produced a proof certificate
accepted by the UNCHANGED formally-verified checker:

    Just (11,35)    (frozen snocheck -v, exit 0)

## The pipeline, measured

| Stage | Machine | Wall | Peak memory | Output |
|---|---|---|---|---|
| Search (SUBSUME=evict DIMS=96 W=8,9) | ollama server (Ryzen 3600, 47GB) | 71 h 06 m | 13.08 GB | result = 35; 95,221,143 states |
| Prune-all (CROSS_BOUND_PRUNE=1) | server | 9 h 45 m | ~8.4 GB | 10.47M survivors (2.69M w8 / 5.60M w9 / 2.09M w10 / 102,966 w11) |
| Gen-proof | server | ~9 h (attempt 3) | >37.9 GB (see below) | proof.bin 2,442,317,348 B |
| Verified check | M4 | 89 m 24 s | 4.35 GB | **Just (11,35)**, exit 0 |

Certificate SHA-256:
672c433fb5f7a85602c937acfcd2135fd8a9f64d63c7ea3075706156d2c08e38
(2.44 GB — smaller than Harder's 2.9 GB original, consistent with
stronger pruning.)

## Comparison with the 2020 original

| | Harder 2020 | This run |
|---|---|---|
| Search memory | 178 GiB | **13.08 GB (13.6x less)** |
| Search hardware | 24c/48t server | 6-core home server |
| Search wall | 4 h 51 m | 71 h (weaker cores + memory-frugal config) |
| Certificate | 2.9 GB, verified | 2.44 GB, verified by the same unchanged checker |

## Incidents (full disclosure)

- Gen-proof was OOM-killed twice: kernel log records the kill at
  anon-rss 37.9 GB (the box had 47 GB RAM and ZERO swap). Root cause:
  n=11 certificate assembly needs ~40+ GB transient. Fix: a 96 GB NVMe
  swapfile armed under the live third attempt (passwordless sudo),
  which then completed. Lesson: gen-proof memory is the hidden peak of
  the pipeline — budget it separately from search; keep swap armed.
- The M4 verification run was once killed by a session-tool timeout
  (operator error, 10-min cap on a 90-min job); relaunched detached.
- The search ran on the pre-checkpointing 5-patch binary (launched
  before Tier-2b landed) — a deliberate keep-vs-restart decision
  (documented in session); all future long runs use the checkpointed
  stack.

## Census facts banked (Level Law anchored)

Level-6 stored census at n=11 with evict/DIMS=96/W=8,9: 95.22M states
inserted / 13.1 GB peak. By the (now-proven) Chain Collapse theorem
this census transfers exactly (+2 states) to the n=13 level-6 question.

---

## CORRECTION ADDENDUM (2026-08-23, machine-checked)

An independent recount of the certificate itself (read-only mmap over
proof_n11_ours.bin; tools/verify_novel_facts.py, .build/v3-novelty/
cert_census.py) supersedes the survivor figures above:

- Certificate steps: **10,275,769** (not "10.47M").
- Per-width survivors above are OVERSTATED: w8 by 172,383, w9 by
  319,716, w10 by 74,524. Use the recount.
- The "95,221,143 states" figure is ambiguous between insertions and
  stored census (these differ by ~7.2% at level 5) because the run log
  is no longer available. The derived n=13 level-6 census
  |Reach(13,6)| = 95,221,145 inherits that ambiguity in its base term;
  the "+2" is proven.

Nothing above about the VERDICT changes: result = 35, certificate
accepted by the unchanged verified checker, Just (11,35), exit 0.

## ADDENDUM 2 (2026-08-23) — two corrections to Addendum 1

1. **The run log SURVIVES**: /data/mericanii_s13_method_v3/n11-full/run.log
   (999 KB; copy at .build/v3-level7/n11-certified-run.log.gz). Addendum 1
   and the body twice claim otherwise. It carries the per-iteration table.
2. **The insertions-vs-census ambiguity is CLOSED by that log**:
   103,343,397 insertions − 8,122,254 = **95,221,143 stored census**.
   |Reach(13,6)| = 95,221,145 stands on a measured base term.
3. From the same log, the cost fact that decides level 7: the
   **level-5 → level-6 iteration WALL multiplier is 418.4x** against a
   stored-state multiplier of 22.3x. Index lookup is 79.4% of user time.
   See docs/level7-redecision.md.
