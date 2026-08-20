# Verified-Checker Campaign — prefix certificates now have a VERIFIED core

Date: 2026-08-21. (Persisted by the orchestrating session; condensed
from the agent's final report.)

## Delivered (all four objectives, exceeded)

1. **Four divergences closed, not one**: line-by-line reading of
   Checker.thy vs Check.hs found D1 (bound!=0 Successors — the recorded
   one; permissiveness gap, not soundness hole), D2 (Huffman width!=0),
   D3 (non-empty Huffman witness list — Check.hs CRASHES rather than
   accepts), D4 (vector-fits-width; the frozen binary silently
   REINTERPRETS via truncation rather than rejecting). All guarded in
   cert_v2.py, purely additive diff, 33/33 selftests, zero regressions
   across all campaign certificates and compositions. D1's closure was
   confirmed against the extracted verified core itself.
2. **snocheck_guard.sh**: magic + layout-invariant guard preventing the
   13GB-misread hazard; 6/6 tests. (class_campaign.py never invokes
   snocheck — docstring prohibition added instead.)
3. **Isabelle assessment**: Isabelle2020 installed; upstream session
   builds in 14 s; regenerated Checker.hs matches the frozen copy
   modulo the known patch hunks — extraction pipeline REPRODUCED.
   Structural finding: step semantics already root-parameterized; the
   full cube enters only in the last 35 lines; u64 ids need zero
   Isabelle work (verified int extracts to Integer; the 2^32 cap was
   entirely in unverified Decode.hs).
4. **Prefix_Checker.thy (190 lines, no sorry)**: machine-checked
   corollary — a checked prefix certificate proves
   |prefix @ completion| >= |prefix| + b for any sorting completion.
   Zero edits to the frozen theory files. New binary snocheck2 accepts
   all 8 campaign certificates (bounds match cert_v2.py exactly),
   reproduces Just (9,25)/(10,29) on v1, handles v2 wide, rejects all
   7 corruption cases. The verified core RECOMPUTES X_P and never
   trusts the stored root (strictly stronger than the reference
   checker); the comparator-orientation convention is discriminated by
   acceptance, demonstrated not assumed.

## Checker story for the class programme (adopted)

Run BOTH checkers, record both verdicts (~25 s per campaign): snocheck2
is the authority on the bound ("verified prefix checker with an
unverified decoder" — say it exactly that way); cert_v2.py cross-checks
decode + SHA-256 digests. Frozen snocheck remains the n<=11
full-problem anchor, untouched (hash unchanged).

## Open items

- snocheck2 skips the two SHA-256 digest checks (no GHC lib available)
  — corruption-detection gap only, announced at runtime; cheapest next
  fix.
- Prefix_Checker.thy needs a second reader before any published class
  result leans on it (two statements in its section 3.3).
- The composition argument (Python-checked exhaustiveness/coverage) is
  now the weakest link, ahead of the checker.
- Isabelle2020 lives in the ephemeral session scratchpad — re-download
  or relocate for durability; tools/verified/build.sh is parameterized
  (ISABELLE=) and sources are committed under tools/verified/.
- Pre-existing: class_campaign verify exits 1 on engine-binary sha
  drift (someone rebuilt the engine after manifests were written);
  compositions still VERIFIED 25/25/29/29 — reconcile manifests.

## Files

tools/cert_v2.py (D1-D4), tools/snocheck_guard.sh, tools/verified/
{Prefix_Checker.thy, Prefix_Checker_Codegen.thy, ROOT, build.sh,
crosscheck.py, snocheck2/*}, docs/verified-checker-extension.md,
docs/certificate-format-v2.md updates; binary at
.build/v3-vcheck/snocheck2/snocheck2. Frozen artifacts untouched.
