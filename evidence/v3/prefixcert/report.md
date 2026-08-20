# Prefix-Certificate Campaign — the class-job certificate blocker is CLOSED

Date: 2026-08-20. (Persisted by the orchestrating session; condensed
from the agent's final report.)

## Delivered

1. **Prefix-rooted gen-proof** (`gen-proof <dir> [-p a b ...]
   [--prefix-root]`): roots the proof at the prefix's output set by
   resolving the root through lookup_witness — the same mechanism as
   every other witness — so NO new proof rule, no new witness kind, no
   changed step payload byte. Handles subsumed-root replacement.
   Legacy path proven untouched: prefix-free gen-proof emits
   byte-identical bytes vs the pre-patch binary (cmp on fixed pruned
   dirs at n=8/n=9).
2. **v2p container** (format_version=3): versioned prefix section;
   stored root is a mirror — the checker RECOMPUTES X_P from the prefix
   and rejects mismatches (a certificate-for-the-wrong-prefix is a
   rejection). v2 readers reject v2p three independent ways;
   cert_v2.py check refuses v2p to prevent bound misattribution.
3. **Composed campaigns validated**: n=9 depth-1/2 and n=10 depth-1/2 —
   8 per-job certificates (11.6k-69.4k steps each), every one
   independently re-verified by cert_v2.py prefix-check, composition
   VERIFIED to exactly 25/25/29/29. class_campaign.py verify now checks
   all three composition obligations (frontier exhaustiveness,
   certificate re-verification with drift detection, coverage);
   19/19 selftests.
4. **wide13 validated on the full 11-patch stack**: 35/35 tests on all
   three builds; frozen snocheck still Just (9,25)/(10,29); n=13
   --limit 42 reproduces (50.29M states, -1.2%; 3.34GB peak; wall
   contaminated by concurrent agent, flagged not alarming).

## Hazards flagged

- Feeding a v2/v2p file to the frozen snocheck makes it misread ASCII
  magic as a 1.13e9 step count (~13GB read attempt). A magic-check
  guard wrapper before snocheck invocations is cheap insurance — TODO.
- **The unverified-checker gap is now load-bearing**: per-job prefix
  certificates are checked only by cert_v2.py (unverified, and
  slightly more permissive than Checker.thy per the recorded bound!=0
  divergence). Extending the VERIFIED checker to v2/v2p is now a
  dependency of the class programme, not a nicety.

## Remaining before a real class job (besides budgets)

Prefix-depth U-curve at n=11; the level-6 measurement (running);
verified-checker extension for load-bearing class results; Kraft
repair for unconditional C1/C2/C3 (root-split --class ALL campaigns
are unconditional already).

## Artifacts

tools/patches/sortnetopt-prefixcert-v3.patch (594 lines, sha256
5722c0d5..., 11-patch stack round-trips byte-identical, 35/35);
docs/certificate-format-v2.md section 9; tools/cert_v2.py (25/25
selftests); tools/class_campaign.py (19/19); builds and campaigns
under .build/v3-prefixcert/.
