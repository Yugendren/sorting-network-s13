# Z+M Engine Campaign — Z lands unconditionally; M lands width-gated

Date: 2026-08-18. (Persisted by the orchestrating session; agent harness
forbids report .md writes. Condensed from the agent's final report —
full measurement tables in the agent transcript and .build/v3-zm/.)

## Verdicts

- **Lemma Z (zeta abstraction): PASS, land unconditionally.**
  Bit-identical on 1.38M sets (widths 3-13, zero mismatches; negative
  control verified non-vacuous) plus ~10^8 in-engine abstractions across
  277 runs. Speedup grows with width: 4.7x (w8), 19.5x (w11), 29.1x
  (w12), **45.3x (w13)**. Never loses in any configuration. The
  internals-doc "abstraction 240x too costly" objection — the likely
  reason on-line subsumption was shelved in 2020 — is RETIRED.
- **Lemma M (matching filter): PASS on soundness and power; land gated.**
  **372,748,784 audited rejections, 0 violations** (audit active inside
  prune-all and gen-proof included). Removes 91-99% of surviving exact
  calls; exact-test precision rises 1.8% -> 93%; with M on,
  exact-call volume becomes independent of DIMS (~350k across a 12x
  DIMS range) — M subsumes the coordinatewise filter's discriminating
  power. BUT in-engine it is a wall LOSS at indexed widths <= 8 (it
  duplicates what Tier-2a's root filter already does cheaply) and a
  wall WIN from width 9 up (measured crossover; -648 ns/call at w9).
  New knob SORTNETOPT_MATCH_FILTER_MIN_WIDTH; **recommended value 9**
  (measured: 5.0% faster than the 8-patch baseline and 5.7% faster
  than M-everywhere at n=11 -l 33 w8,9).
- New counter filter_exact_hits: ceiling fraction now measurable
  (1.8-8.4% pre-M; ~93% with M).

## Key findings

1. Level Law independently reproduced on this stack (level-4 census
   matches assessment to 0.16%; two-width confirmation at n=10).
2. Z+M does NOT revive evict mode at n<=10 — and the measured reason is
   that Tier-2a already made the exact test cheap at the widths those
   proxies exercise. The payoff is a width>=9 phenomenon: it arrives
   exactly at n=12/13 census widths (travelling-wave logic) and not
   before. Attribution note: the low-DIMS wall penalty collapse
   (M2b 7.3x -> Tier-1 2.47x -> this stack 1.53x) is prior campaigns'
   work, not Z+M.
3. n=13 arithmetic: Z+M cut cost-per-state (~2-3x effective at n=13
   widths), not state count. "$100 becomes $35 for the same
   computation; 35 PB moves nowhere." Value lands on the decomposed
   subproblems the programme is committed to.
4. Recommended level-6 measurement config: MATCH_FILTER_MIN_WIDTH=9,
   SUBSUME_WIDTHS tracking the census upward — first configuration
   where the on-line index is not a net wall tax.

## Validation

277 runs: results 25/29/33 everywhere; one bound sequence per (n,limit);
peak entries inside Tier-1 bands; idx_clamps=0; 6 full pipelines
accepted by the unchanged frozen snocheck (Just (9,25)/(10,29)),
including two with the audit active in all three stages; 9-patch
round-trip clean (35/35 tests, byte-identical tree, certificate OK).

## Deviations / open items

- The n=11 --limit 34 (3.2GB) measurement was SKIPPED locally per the
  memory guardrail (6.2GB swap in use at decision time); server replay
  commands provided in the agent transcript — the single measurement
  worth server time next: -l 34, one indexed width at 9 and 10, M
  on/off, 4 runs (~25 min).
- One non-reproducible post-search hang (1 of 277; after result,
  in dump/pool shutdown; 282 repeats clean) — flagged for long server
  jobs; cannot be attributed to or exonerated from Z+M.
- Pre-existing DEBUG-mode test failure in tier2b's checkpoint test
  (present on unmodified 8-patch stack; release 35/35) — belongs to
  tier2b, noted.
- abstraction_prefix_from_packed exists but unused (~25% further
  abstraction saving at n=13 available by threading PackedSet through
  from search/prune call sites — out of scope here).
- Upper-index guards written for M but never exercised by an audit.

## Artifacts

tools/patches/sortnetopt-zm-v3.patch (3,199 lines, SHA-256
de4eb72954d447abcec1b4c29f7f0a78e6d7cb35cd635a99c5f8239f93a4c4f9);
binaries + zeta_diff/zm_bench harnesses + all run logs under
.build/v3-zm/. checker/ and pinned clone untouched.
