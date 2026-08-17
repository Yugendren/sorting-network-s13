# v3 Engine Limits Campaign — All Objectives PASS; first measured n=12/n=13 data

Date: 2026-08-17/18. (Persisted by the orchestrating session; the
campaign agent's harness forbade writing report markdown. Content
verbatim-condensed from its final report; full detail in the patch
header, docs/certificate-format-v2.md, and .build/v3-limits/.)

## Verdicts

1. **MAX_CHANNELS / packed storage raise: PASS.** Feature-gated
   (`wide12`/`wide13`); the default n<=11 build is provably unchanged
   (identical constants and emitted bytes; 0.99x measured). wide12
   costs 2.1-2.7%; wide13 1.3% (evict config) / 6.7% (plain, only paid
   when width 13 is actually needed).
2. **u32 -> u64 certificate step space: PASS.** Dual-format emitter:
   legacy v1 whenever step count fits (byte-identical on a fixed
   pruned input across pre-patch/default/wide13 binaries, accepted by
   the frozen checker); versioned SNOCERT2 v2 for future n>=12 scale,
   spec in docs/certificate-format-v2.md, independent Python reference
   checker (tools/cert_v2.py) cross-validated: Rust-emitted v2 ==
   Python-transcoded v2 byte-for-byte at n=8/9/10; 13/13 corruption
   self-tests rejected. Known divergence recorded: Check.hs (and thus
   cert_v2.py) omits Checker.thy's bound!=0 Successors guard — close
   before the reference checker is ever an authority.
3. **n=12 probe: PASS and over-delivered — first measured n=13 data.**

## Three blockers actually found (beyond the flagged constant)

- AVec hard-coded ArrayVec<[T;512]> (needs 528 at n=12, 624 at n=13).
- **histogram_signature u64 shift overflow at channels>=12** (silently
  scrambles the Tier-1 thermometer filter above n=11; misses subsumers
  -> prove_all panics after the search is paid). Fixed by
  hist_sig_bits(c)=min(5,64/(c+1)) — bit-identical for c<=11.
- OutputSetMap missing arms: silent total memoization loss at new
  widths (get returned None while set panicked). Arms + width test.

Control finding: proof.bin is NOT byte-reproducible across runs of the
same binary (nondeterministic search order); emitter byte-identity must
be tested on a fixed pruned directory. All regression bars met: 18
runs/arm, results/bounds/bands unchanged, pipelines Just (9,25)/(10,29)
on all arms, checkpoint kill/resume passes on limits and wide13,
cross-width checkpoint correctly refused.

## Measured trajectories (subsumption off unless stated)

n=12: --limit 36 -> 24.8k states/19MB; 37 -> 207.9k/44MB/0.74s;
38 -> 50.79M/2.75GB/326s; 39 capped at 135.1M/5.57GB (30-min cap
mid-iteration). Per-level growth 13x -> 46x -> 8.4x -> 244x.

n=12 with online index (evict/DIMS=24/widths 8,9 census-chosen):
>=9x memory for >=5.5x wall; the 5.4-min iteration did not finish in
30 — **wall, not memory, binds at n=12 on this machine**; index needs
re-justification for n>=12 long runs. Census drifts upward one width
per 1-2 bound levels (35:{6,7} -> 38:{8,9}) — SUBSUME_WIDTHS should
follow the bound, not be fixed at launch.

**n=13 (first measured points ever):** --limit 37 -> 11 states/3ms;
40 -> 24.8k/20MB; 41 -> 207k/46MB/0.77s; **42 -> 50.92M/3.35GB/298s.**
The n=13 ladder is the n=12 ladder shifted by exactly 4 bound levels
(state counts within 0.3%); memory +22% at equal states (wider sets).

## Implications

- **The free van Voorhis/Huffman chain reaches bound 37 at n=13 in
  3 ms.** All cost is in the last levels; restricted-exhaustion
  campaigns should be budgeted from bound 37 upward, and the shape
  case-split's value is now directly measurable as "how many of the
  last levels it removes."
- Memo cost at ladder top: 44-58 B/state. Reaching 45 needs 3 more
  levels above the measured 5.1e7 @ 42; geometric-floor/ceiling
  multipliers (33x/244x per level) give **1.8e12-7.4e14 states ~=
  80 TB-35 PB** — now anchored to measurement, bracketing both prior
  extrapolations. Monolithic n=13: 4-6 orders out of reach on one
  machine; decomposition remains the route, and each decomposed job is
  now a runnable five-minute experiment instead of a thought
  experiment.
- Next cheap probe: n=13 --limit 43 under 8GB/30min caps (the analogue
  of the n=12 --limit 39 point) — pins the first level where memory
  binds.
- fix.rs not updated for v2 (not in pipeline; noted).

## Artifacts

tools/patches/sortnetopt-limits-v3.patch (982 lines, SHA-256
6d30602f0985f6e650624ad3dbe362db9ed99e88d7b94d96623389524041d928, on
top of tier2b; 8-patch stack round-trips with no fuzz, 22/22 tests,
Just (9,25)); docs/certificate-format-v2.md; tools/cert_v2.py;
binaries/drivers under .build/v3-limits/.
