# Decomposition Machinery Campaign — all four objectives built and validated

Date: 2026-08-20. (Persisted by the orchestrating session; condensed
from the agent's final report — full details in the patch header,
tools/class_filter.py, tools/class_campaign.py, .build/v3-decomp/.)

## Delivered

1. **Shell/chain counters** (SORTNETOPT_SHELL_STATS, default off):
   exact same-shell chain measurement + per-(width,popcount) census in
   instrument.json; flag-off byte-band-identical; census cross-checked
   against an independent dump histogram (0 mismatches).
2. **Shared bound oracle** (SORTNETOPT_BOUND_SEED): read-only,
   bounds-only, equal-width, max/min merge, hash-enforced, contradiction
   abort (exit 4; measured 0). Seeded n=10-from-n=9 produced result 29 +
   accepted certificate.
3. **Class-restriction hooks**: branch-tree max-path tracer (per the
   van Voorhis correction) + exact prefix-monotone class filter; two
   independently written tracers agree 4000/4000; 0 false rejects on
   6000 constructed class members; Filter 0 excluded (out-of-domain +
   redundant + uses the forbidden constant).
4. **Job manifests + runner** (tools/class_campaign.py): plan/seed/run/
   status/compose/verify/export, per-job checkpoints, sharding,
   SHA-256 hash-chained ledger, 13/13 selftests. Composition validated
   END-TO-END: full n=9 and n=10 campaigns at depths 1 and 2 compose to
   exactly 25 and 29 (ESTABLISHED, verify clean); canonical dedup
   collapses 5184->3 jobs (1728x).

## Findings that reorder the plan

- **Low-level seeding saves nothing** (measured: iterations 17->2 with
  identical final-iteration work) — 99.6% of the memo is built by the
  final iteration, so the oracle's real value is job-to-job propagation
  of the TOP-level memo (measured 45x on a sibling job; 12->1
  iterations cross-n) — which requires the external-memo work first.
  Step 2 is gated by Step 3, not parallel to it.
- **Class filters prune nothing below ~depth 4** (exhaustive check);
  survival 54-69% at depth 8, 10-20% at depth 20 — class jobs must be
  generated at substantial prefix depth; splitting-cost U-curve still
  unmeasured.
- **The 4-7% same-shell tie rate in the endgame assessment is a
  walk-depth artifact**: the engine's real DAG has 0.0016% ties,
  chain_max=1 — one pass per shell suffices in the external scheme at
  this scale (re-measure at n=11 -l 34 before locking sizing).

## Blockers before a first real class job

1. **Prefix-rooted gen-proof** (proof.rs hardcodes the full-cube root;
   prefix jobs cannot emit their own certificates yet — bounded fix,
   same work item as the u32 cap). Hard prerequisite: class results are
   not load-bearing without per-job certificates.
2. wide13 build validation of the merged patch (validated at
   MAX_CHANNELS=11 only so far).
3. Prefix-depth decision (measure the U-curve at two depths at n=11).
4. The level-6 measurement (the running n=11) for budgets.
5. Class results C1/C2/C3 remain CONDITIONAL on the case split until
   the Kraft repair lands ('ALL' campaigns are unconditional).

## Operational warnings

- **Engine quirk**: with SORTNETOPT_CHECKPOINT_DIR set and RUST_LOG set
  to anything but info, the engine SILENTLY EXITS 0 with no output.
  class_campaign.py unsets RUST_LOG unconditionally. Never launch a
  long server run without checking this.
- Safety tripwire armed from n>=13 only (at n<=10 it fires vacuously
  and trains reflexive dismissal).

## Artifacts

tools/patches/sortnetopt-decomp-v3.patch (1,866 lines, 11c085e2...,
round-trips byte-identical, 35/35 tests); tools/class_filter.py;
tools/class_campaign.py; validated campaign at
.build/v3-decomp/campaigns/final-n9-d2. Certificates: unseeded and
seeded pipelines Just (9,25)/(10,29) via the unchanged frozen checker.
