# Final internal red-team review — publication package

**Date:** 2026-08-22. **Reviewer role:** final internal red team, pre-publication.
**Status:** review only. Nothing in this pass was fixed, corrected, or committed.
No file outside this document was written.

**Scope reviewed:** the v3 arc from `fbb9878` to `70182a4`; `docs/paper/`
(draft + NOTES); the theory set (`van-voorhis-theory-report`,
`kraft-dispute-verdict`, `kraft-repair-report`, `kraft-repair-wave1`,
`kraft-repair-wave2`, `s13-shape-case-split`, `transforms-assessment`,
`endgame-theory`, `ambient-reduction`, `lowmem-endgame-assessment`,
`verified-checker-extension`); `evidence/v3/*`; the nine verifier tools;
governance files (`README.md`, `GOAL_STATE.md`, `SOLUTION_STRATEGY.md`,
`METHOD_EXPERIMENT_CONTRACT_V3.md`).

**Headline.** The mathematics is in good shape and is unusually self-critical.
The package is not. Three structural problems dominate:

1. **A result nobody consumed.** The programme's self-declared decisive
   experiment — the level-6 measurement — landed on 2026-08-22 and no document
   has used it. The go/no-go it was supposed to settle is still the pre-measurement
   one, and a first reading of the measurement suggests the estimates behind that
   go/no-go may be off by more than an order of magnitude. **B-1.**
2. **A paper two theorems behind its own repository.** The draft is a snapshot of
   2026-08-18; its central positive result has since been superseded twice
   (clean → escape-free → (C)∧(D)) and its central negative characterisation
   ("pass-throughs are the sole obstruction") has been explicitly retracted.
   **B-6, B-7.**
3. **An evidence tree outside its own trust boundary.** `evidence/v3/` is
   prose-only, carries no manifests or checksums, and is not touched by
   `evidence_check.py`, so the flagship credential (n = 11 certified) has no
   preserved artifact chain and 11 of 24 cited digests can no longer be
   recomputed. **B-12, B-14, B-15.**

A fourth theme runs through the governance files: the corrected bound
(43 ≤ S(13) ≤ 45) reached `GOAL_STATE.md` and nothing else. `README.md`,
`SOLUTION_STRATEGY.md`, the active contract, the literature survey and the
cross-domain research notes all still assert 44 as the floor. **B-4, B-5, B-9,
B-10, B-11.**

**On the quality of the underlying work:** high, and the review should not be
read as saying otherwise. Almost every defect below is a *propagation* failure —
a correct finding that was recorded in one document and never carried to the
three that depend on it. The theory documents are consistently harder on
themselves than this review is. See Appendix D.

**Counts: 17 BLOCKERS, 27 IMPROVEMENTS, 13 NICE-TO-HAVE.**

**Verifier suite: 9/9 pass in their intended modes (Appendix A). No test failure
is a blocker; the suite's problems are reachability, not correctness.**

**Hard-constraint check — performed first, reported plainly, one item needs your
adjudication.**

Clean: `track_a/ledger/scores.jsonl` (4 records) unmodified; `evidence/` and
`config/frozen/` unmodified; `git status` shows zero modifications to tracked
files; no 13-channel candidate at ≤ 45 comparators was produced or encountered
(the best entry in the Track-A ledger is a valid 13-sorter at **48**
comparators), so the dual-B1-verifier procedure was not triggered.
The live search and learning code is clean — `track_a/evaluator.py:36` uses
`TARGET = 45`, `track_a/pool/*` and `src/` contain no occurrence of 44, and
`tools/patches/sortnetopt-limits-v3.patch:636` seeds **upper** bounds only
(`…,35,39,45`).

**Needs adjudication (see B-2, B-3):** 44 *is* written as a search target and
stopping condition in one frozen config, and is *recommended* as a lower-bound
seed for the proof engine in two documents. Neither is executing. I did not
touch the frozen config. Both are reported below rather than fixed.

---

## BLOCKERS — must fix before submission

### B-1. The programme's decisive experiment has landed and no document has consumed it — the go/no-go may be wrong by orders of magnitude

This is the most consequential finding in the review and it is not a
documentation defect.

`docs/ambient-reduction.md:723-728` states the programme's own decision rule:

> "The 4-order-of-magnitude bracket above collapses to a single number **the
> moment level 6 is measured** … That remains the single most valuable
> experiment in the programme."

`docs/lowmem-endgame-assessment.md:1137-1152` calls it "**Step 0 — measure level 6
(blocking; nothing else should start first)**" and brackets it at 21–607 GB,
81 GB geometric.

**Level 6 was measured on 2026-08-22.** `evidence/v3/n11-certified/report.md:51-55`:

> "**Census facts banked (Level Law anchored).** Level-6 stored census at n = 11
> with evict/DIMS=96/W=8,9: **95.22M states inserted / 13.1 GB peak**. By the
> (now-proven) Chain Collapse theorem this census transfers exactly (+2 states)
> to the n = 13 level-6 question."

Nothing consumed it. The go/no-go at `ambient-reduction.md:702-706` ("**NO** …
the gap is 7.4×–600× in storage") predates it by one day and was never revisited;
`lowmem` still presents Step 0 as unstarted and blocking; `GOAL_STATE.md` does not
know it happened.

**Why this could flip the decision.** Every level-7 and level-8 estimate in the
repo is driven by per-level multipliers bracketed at **8.4× / 33× / 246×**
(`lowmem:97-100`, reused at `ambient-reduction.md:685-688`). Measured level 6 is
95.22M states against a level-5 anchor of 50.92M — a ratio near **1.9×**, which is
*below the optimistic floor by more than 4×*. Measured memory is 13.1 GB against a
predicted floor of 21 GB.

**The executed run is close to lowmem's own Step-0 prescription.** Step 0 asks for
`n=11 --limit 35` on the server, with the fallback "restart with the on-line index
(`evict`, DIMS=24, widths … **w8, w9**)" if RSS crosses ~40 GB
(`lowmem:1148-1151`). The n = 11 run was on the server with
`SUBSUME=evict DIMS=96 **W=8,9**` and returned `result = 35`. So this is not an
unrelated experiment that happens to touch level 6; it is substantially the
prescribed one, at a different DIMS.

**The two measured axes disagree, which is why this needs adjudication rather
than a conclusion.** Memory came in *below* the predicted floor (13.08 GB vs
21 GB); wall came in far *above* the predicted ceiling (71 h vs 0.85 M4-days
≈ 20 h) — on a 6-core Ryzen 3600 rather than the M4, so the wall figure is not
directly comparable either. A model that is 1.6× optimistic on memory and 3.5×
pessimistic on time is not a model anyone should still be quoting a
4-order-of-magnitude bracket from.

**Do not act on 1.9× as stated.** I checked the comparison and it is not
apples-to-apples, in two independent ways:

1. **Regime.** The 95.22M figure comes from a *full* n = 11 search; the 50.92M
   level-5 anchor is an `n=13 --limit 42` run. `transforms-assessment.md:210-216`
   warns these are not comparable, and `ambient-reduction.md:75-78` — while
   withdrawing that caveat's *mechanism* — supplies a replacement reason why full
   runs run **larger** (they must also close the upper bound).
2. **Subsumption.** The n = 11 run used `SUBSUME=evict DIMS=96 W=8,9`; every
   lowmem multiplier is subsumption **OFF** (`lowmem:42`). "States inserted" under
   `evict` is also not obviously the stored census.

**Required before publication of any go/no-go:** re-derive the level-5→6
multiplier under matched regime and matched subsumption settings, then recompute
the level-7 bracket and restate the decision. If the multiplier is anywhere near
2× rather than 33×, "out of reach on owned hardware" is false, and that is a
statement the package currently makes in three documents.

### B-2. 44 is written as a search target and stopping condition in a frozen config, and a test enforces it

`config/experiment-v1/budgets-v1.json:41-48`:

```json
"e5": {
  "enabled_only_after_method_pass": true,
  "target_comparators": 44,
  "aggregate_candidate_evaluations": 100000000,
  "calendar_seconds": 604800,
  "stop_on_first_verified_witness": true,
  "paid_compute": false
}
```

`tests/test_e0_method.py:105` asserts `frontier["target_comparators"] == 44`, so
the test suite *enforces* the value.

**Assessment.** This is a literal target-plus-stopping-condition, which is exactly
the shape the hygiene rule forbids. Three mitigations, all real: `e5` is gated on
`enabled_only_after_method_pass`; the v1 method experiment terminated
`METHOD_REJECTED` (`d72cedf`, `GOAL_STATE.md:23`), so the gate can never open;
and `config/` is frozen and immutable, so it cannot be edited.

**I did not touch it.** It needs your adjudication, not a fix: options are a
documented exception recorded against the freeze, or retiring the v1 config tree
under whatever procedure the freeze permits. What is not acceptable is leaving it
unremarked in a package whose thesis is that 44 is unproven — a reader who greps
the config tree finds it in ten seconds.

### B-3. Two documents recommend seeding the proof engine's *lower* bound at 44, on a precondition that can now never be satisfied

`docs/sortnetopt-internals.md:849-853`:

> "Raise the *lower* seed from the universal `1` to the best known lower bound
> for that width — for the n = 13 root that is **44** (van Voorhis from
> S(11) = 35) … Since S(13) ∈ {44, 45}, seeding `[44, 45]` means a single
> iteration decides the question."

`docs/sota-survey.md:17`, attack surface (ii):

> "starting the successive-approximation DP from the ***44*** lower bound instead
> of 43 (the interval to fathom is half as wide)"

The internals doc's own risk analysis is excellent and correctly gates it
(`:858-865`): "A too-high lower seed produces a **wrong answer silently**:
`improve` can close the interval by upper-bound descent and return the seed. The
seed must be an independently proved bound. The 44 bound is currently *folklore* …
so using it as a seed requires the write-up in `docs/s13-lower-bound-note.md` to
exist and be checked first."

**That gate can now never open.** The write-up does not exist (N-1), and the audit
established that no correct argument for 44 is available — so the precondition is
permanently unsatisfiable. The recommendation is dead but is not marked dead, in
two documents that are cited as anchors by `GOAL_STATE.md:13-14` and
`METHOD_EXPERIMENT_CONTRACT_V3.md:23-25`. An agent implementing the ranked
recommendation without reading the risks section would silently produce a wrong
lower bound for n = 13. Mark both **RETIRED — precondition unsatisfiable**.

*Code is clean:* `tools/patches/sortnetopt-limits-v3.patch:636` seeds upper
bounds only. Nothing implements this.

### B-4. `docs/sota-survey.md` asserts 44 as current status and calls the correct bound "stale"

- `:4` — "**Open problem:** Does a 13-input sorting network require 44 or 45
  comparators? Current status: **44 <= S(13) <= 45.**"
- `:260` — "Wikipedia, 'Sorting network' (n=13 lower bound listed there, **43, is
  stale**)."

The second is inverted: 43 is the proven floor and the *published* bound; the 44
is the entry with no correct argument behind it. The survey carries no correction
banner and is the literature anchor cited by `GOAL_STATE.md:14`,
`METHOD_EXPERIMENT_CONTRACT_V3.md:24-25` and `docs/research-programme.md:3`.

### B-5. `docs/research/xdomain-bound-theory.md` treats 44 as established throughout, with no banner

`:11`, `:20-23`, `:91` ("**This is the current record**: 35 + 9 = 44"), `:250`
("Chain: S(13) >= S(11) + P(2,13) >= … = 44"), `:262-265`, `:297-298`. Zero
occurrences of CORRECTION / SUPERSEDED in the file. This is a research document
that a reader arriving from the survey will hit next.

### B-6. The paper's central theorem has been superseded twice and the draft does not know it

`docs/paper/audit-paper-draft.md` §7.5 Theorem 6 proves eq (8) for **clean**
sorters. Since the draft was written:

- `docs/kraft-repair-wave1.md:155-159` proves **Theorem 6′** for the strictly
  wider **escape-free** class (status `PROVED`, wave1:463).
- `docs/kraft-repair-wave2.md:384-385` proves **Theorem 6″** for `(C) ∧ (D)`,
  strictly wider again (status `PROVED`, wave2:854).
- `docs/kraft-repair-wave2.md:903-905` states explicitly that Theorem 6′ in the
  §3 formalisation "**supersedes the clean-case Theorem 6**".

The draft cites neither wave. `grep -c "escape" docs/paper/audit-paper-draft.md`
returns **0**. Submitting the clean-case theorem as the paper's positive result
would publish a strictly weaker theorem than the project has proved, four days
after proving the stronger one.

### B-7. The paper's central negative characterisation is retracted

The draft asserts in six places that pass-throughs are *the* obstruction —
abstract (line 39, "identifies pass-throughs as the sole obstruction" in §7 line
647), §4.2, §5 "Localisation" (560-566), §8.3 item 2 (1004-1006), §10.2 (1299).
`docs/kraft-repair-wave1.md:435-438` retracts this:

> "`docs/kraft-repair-report.md` §3.1's 'pass-throughs are the sole obstruction'
> is superseded. Pass-throughs are necessary but not sufficient for the
> obstruction; **escapes** are the right notion. Batcher's 12-sorter has a
> pass-through and is provably fine."

Every one of those six passages needs rewriting, not softening.

### B-8. `docs/kraft-repair-report.md` still carries both retracted claims, uncorrected

Two waves issued written instructions to amend this file. Neither was applied
(the file's last commit is 2026-08-18; both waves are 2026-08-20):

| Live text | Location | Instruction that was never applied |
|---|---|---|
| "Pass-throughs are the sole obstruction. This is now a checked statement" | `kraft-repair-report.md:204` | wave1:435-438 |
| "pass-throughs shown to be the sole obstruction" | `kraft-repair-report.md:380` | wave1:435-438 |
| status row "eq (8) for **clean** `N`-sorters (Theorem 6) \| **proved**" | `kraft-repair-report.md:428` | wave1:439-441 *and* wave2:824-827 — **two competing replacement texts are on record and neither was written in** |
| "the sum can reach `1.25`" | `kraft-repair-report.md:202` | wave1:379-384 measured **1.6875** at n = 6 and warns "do not build on a constant bound" |

A referee reading the theory set will find a document asserting as "checked"
something two later documents in the same set call superseded.

### B-9. `README.md` asserts `44 ≤ S(13) ≤ 45` on the front page

`README.md:33` states the research snapshot as `44 \le S(13) \le 45`; `README.md:12`
frames the whole programme as "whether a 13-input sorting network needs 44 or 45
comparators". This is the front door of a repository whose headline paper is
titled "The widely tabulated lower bound S(13) ≥ 44 rests on an invalid proof".
The README is dated 2026-08-15 and names `METHOD_EXPERIMENT_CONTRACT_V1.md` as
authority (superseded by V3). It is the single most damaging stale artifact in
the package.

### B-10. `GOAL_STATE.md` contradicts itself and is five days / fifteen commits stale

- Line 7 sets the goal as "definitively settle S(13) ∈ {44, 45}"; line 34 of the
  *same file* records "proven state is `43 <= S(13) <= 45`". Direct
  self-contradiction.
- "Current truth" (line 55) is `P0 governance in progress`; "Immediate next
  action" (line 79) is "Finish P0". Both were true on 2026-08-18 and are now
  false.
- The gate ledger marks **P1 harness build: NOT STARTED** while
  `track_a/ledger/scores.jsonl` holds 4 scored records and `track_a/pool/` holds
  4 gen-0 programs; **M2/M4: NOT STARTED** while n = 11 is fully certified and
  the class-campaign machinery composes end-to-end at n = 9/10.
- The file's own rule is "Replace stale facts; do not append a diary."

### B-11. `SOLUTION_STRATEGY.md` and `METHOD_EXPERIMENT_CONTRACT_V3.md` carry the same stale bound — and the contract is hash-pinned

- `SOLUTION_STRATEGY.md:9` — "Known (re-audited 2026-08-15): `44 <= S(13) <= 45`".
- `METHOD_EXPERIMENT_CONTRACT_V3.md:45` — "Research snapshot: `44 <= S(13) <= 45`";
  line 12 — "Definitively settle S(13) ∈ {44, 45}".

The contract's SHA-256 is pinned in `GOAL_STATE.md:11`
(`2462f25f…d098`). Correcting the contract breaks the pin. This needs a
governance decision (amend + re-pin, or a dated addendum) rather than a silent
edit, which is why it is a blocker rather than an improvement.

### B-12. The n = 11 credential has no preserved evidence chain

`evidence/v3/n11-certified/report.md` is the "central credential of the v3
programme" (its own line 2). Commit `70182a4` added that report **and nothing
else**. Its only supporting artifact, `.build/n11-cert/verify.log`, is under a
gitignored path and covers only the last of four pipeline stages. Verified
locally:

| stage | evidence |
|---|---|
| verified check (89 m 24 s, 4.35 GB, `Just (11,35)`, cert `672c433f…`) | present, all four numbers MATCH `verify.log`, digest MATCHES `proof_n11_ours.bin` (2,442,317,348 B) |
| search (71 h 06 m, 13.08 GB, 95,221,143 states) | **no artifact anywhere** |
| prune-all (9 h 45 m, 10.47 M survivors) | **no artifact anywhere** |
| gen-proof (~9 h, > 37.9 GB) | **no artifact anywhere** |

If `.build/` is cleared, the programme's flagship result reduces to prose.

### B-13. `verify.log` does not identify the checker, yet "UNCHANGED" is the load-bearing word

The n = 11 report asserts the bound came from "the UNCHANGED formally-verified
checker (frozen `snocheck -v`, exit 0)" but cites no binary path and no binary
hash, and the log records no command line and no checker identity. A frozen
checker matching the committed B3 manifest does still exist
(`.build/b3-toolchain/attempt-20260815T000526Z/bin/snocheck` = `4cd30511…`), but
nothing ties it to this run. Separately the word "unchanged" is imprecise: the
extracted verified core is unchanged, but `tools/patches/sortnetopt-macos-large-read.patch`
edits the Haskell wrapper `checker/snocheck/src/Main.hs`. `docs/trust-boundary.md`
makes this distinction correctly; the n = 11 report and four others do not.

### B-14. The whole v3 evidence tree is exempt from the project's own trust boundary

`docs/trust-boundary.md:20-24` mandates: "Scored evidence is append-only by run
directory. A manifest identifies the source commit… Each run ends with a checksum
inventory. Missing, changed, or unexpected files make the evidence check fail."

- `evidence/v3/` contains **17 markdown files and zero non-markdown artifacts**,
  **zero `manifest.json`, zero `checksums.sha256`**.
- `tools/evidence_check.py`'s `GATES` constant covers `b0..b4` and `e0..e5` only.
  It exits 0 reporting "verified 19 immutable evidence inventories and manifests"
  while touching **nothing** under `evidence/v3/`.

The clean exit is therefore misleading about exactly the material the publication
rests on.

### B-15. Artifact evaporation across most of v3 — 11 of 24 cited digests are now unrecomputable

`.build/v3-limits/` and `.build/v3-zm/` exist but are **empty**;
`.build/v3-m0/`, `-m0b/`, `-m2a/`, `-m2b/`, `-tier1/`, `-tier2a/`, `-tier2b/`,
`-satspike/`, `-n11-full/` **do not exist**. Consequently every binary-identity
claim in m2a, m2b, tier1 and tier2b ("all frozen before any measurement was
taken") is unverifiable. Worst case: `evidence/v3/limits/probe13-43-addendum.md`
states that lines in `run.log` are **FALSE** and that `NOTE-what-actually-happened.txt`
is the disambiguator — and the NOTE is gone, so the correction cannot be
substantiated.

*(What did survive is substantial and should be said: all 10 patch digests MATCH,
all 5 quoted patch line counts MATCH, the frozen `snocheck` still matches its B3
manifest, the pinned clone is clean at `0b5d09c4…` and `git archive`-reproduces
`a243f270…`, and all 8 prefixcert certificates recompute with composition exactly
25/25/29/29.)*

### B-17. Three of the nine verifiers cannot run from a clean checkout

`verify_ambient.py selfcheck`, `cert_v2.py selftest` and
`class_campaign.py --selftest` each require a mandatory artifact — a state dump, a
v1 certificate, and the engine binary respectively — and all three live under
gitignored `.build/`. None has an argument-free self-check. Details and the exact
argument each demands are in Appendix A, note C.

Why this is a blocker rather than an improvement: the package's central
epistemic claim is that its results are machine-checked, and a third of the
checking apparatus is unrunnable by anyone who clones the repository. It also
compounds B-15 — the artifacts these tools need are exactly the ones that have
already evaporated for most of v3.

Cheap fix: commit a small n = 9 certificate fixture and a small ambient dump
(both are kilobytes at n <= 9), and give `class_campaign.py --selftest` a
no-engine mode for the 19 checks that do not need one.

### B-16. `docs/ambient-reduction.md` overclaims its own machine checking

The §0 verdict (`ambient-reduction.md:18`) says Lemma L "follows from three facts,
**all machine-checked here**". The first — Theorem A, ambient-freedom — is **not**
machine-checked; it is a code-reading audit (§2) plus a second-reviewer pass
(113-119). Compounding this:

- **Theorem D (166-179) has no machine check of any kind**, and **Theorem E's
  proof uses it** (211-218). `tools/verify_ambient.py`'s subcommands
  (`census`, `selfcheck`, `compare`, `lemma-l`, `compare-big`, `chain`) touch it
  nowhere. This is the weakest link in the five-theorem chain that the commit
  message calls "PROVEN EXACT".
- §4.4 claims Theorems B and C were checked by comparing keys against
  `canon(cube_w)` over all `C(k,2)` = 15/36/55/78 comparators; `cmd_chain`
  (`tools/verify_ambient.py:339-366`) only checks *count = 1* and
  *bound = C(w)+level* and never compares the key. The §9 reproduction block
  (line 752) shows **3 of the 78 prefixes**. Not reproducible as written.
- Theorem A is **false** under a non-default setting (§5.3, 511-514), which the
  §0 row does not qualify.

Publishing "five theorems, PROVEN EXACT" against this substrate is the kind of
claim a referee closes a paper over.

---

## IMPROVEMENTS — should fix

### I-1. `docs/paper/NOTES.md` §B3 is now factually wrong and contradicts the adjudicated record

NOTES B3 (lines 68-81) concludes "**Code is authoritative: S2 is C2**", reasoning
from `verify_huffman2.py:1444`. Commit `3823132` adjudicated the opposite and
edited `docs/van-voorhis-theory-report.md:498` to S1 = **C2**, with the inline
comment:

> "S1 was mislabeled C1 (adjudicated: the two verifier scripts break the 392-count
> S1/S2 tie in opposite order; `tools/verify_shape_case_split.py` is the designated
> authority: S1 = 6|7 = C2, S2 = 5|8 = C1. `verify_huffman2.py`'s `admissible_13()`
> ordering should be harmonized in its next revision.)"

`docs/s13-shape-case-split.md:229-234` agrees with the adjudication (S1 root split
6|7, S2 root split 5|8). So the *only* remaining wrong statement is in the paper's
own editorial notes. Two consequences: (a) NOTES B3 and open item D-6 must be
rewritten; (b) the paper's §9.5 item 9 currently lists "one shape's class label"
as an open code-vs-prose discrepancy — it is now adjudicated and should say so.

### I-2. `verify_huffman2.py`'s shape ordering is still unharmonised, and harmonising changes a published hash

The correction comment's own TODO is unfinished. Anyone re-running the artifact
and diffing against `s13-shape-case-split.md` sees a mismatch. But
`verify_huffman2.py`'s SHA-256 is published in the paper's §9.1 table and
**currently matches** (`939979b8…`, verified this pass). Decide before submission:
harmonise and re-publish the hash, or document the ordering convention as
deliberate. Do not do it after the hash is in print.

### I-3. `docs/transforms-assessment.md` §2.3 "regime caveat" is contradicted and unbannered — but a blanket withdrawal would overstate the finding

`ambient-reduction.md:68-78` calls the caveat's mechanism a "**misreading**" —
`--limit` never reaches `improve`; the two `improve_next` call sites are
successor-expansion vs Huffman-expansion, not limited vs unlimited — and says
"the 'regime' caveat as stated should be withdrawn". I verified the code claim:
`improve_next` has exactly two call sites in the 11-patch tree
(`search.rs:645` with `Some(state.bounds[0])`, `:738` with `None`); the
`search.rs:461` / `:472` line references in transforms do not correspond to them.

**Precision matters here, and the brief's framing was slightly too strong.**
Ambient withdraws the *mechanism* and supplies a replacement cause
(upper-bound closure), while **endorsing the divergence itself**. The caveat's
operational conclusion — "All budgeting must be done in the `--limit` regime" —
is contradicted nowhere. The right fix is a banner on §2.3 that replaces the
mechanism and keeps the conclusion, not a deletion.

Additionally, `transforms-assessment.md:282-292` (§2.6's proof sketch for Lemma L)
is declared "**incorrect**" at `ambient-reduction.md:220-228` and is likewise
unbannered.

### I-4. `docs/ambient-reduction.md` is orphaned — no document in the repo cites it

`git grep "ambient-reduction"` returns zero hits outside the file itself. The
newest and strongest theory document is unreachable by navigation from
`GOAL_STATE.md`, `README.md`, or any other doc. Same for
`docs/paper/audit-paper-draft.md`, which is referenced only by its own NOTES.

### I-5. `docs/lowmem-endgame-assessment.md`'s banner does not cover the ambient results

The 2026-08-21 correction banner (lines 1-12) downgrades §6b's suffix-theory
PROMOTE to KILL. It does not touch:

- **§0 row 4 and §7 (`:35`, `:558`)** — the "strongest item in this document",
  headlined "Jaccard **0.9936**" and "**99.92 %** of shared keys". `ambient-reduction.md:17`
  states those residuals "were **entirely thread-scheduling noise**; with the
  worker count pinned the residual is zero" and the identity is **exact**. The
  stale figures understate the result the doc is arguing for.
- The level-7 disk floor: lowmem `:1082` says 3.5 TB where `ambient-reduction.md:684`
  says 2.4-3.2 TB for the same scenario (different bytes-per-state assumptions,
  presented as distinct scenarios).
- The Predecessors line (`:23`) still credits `transforms-assessment.md` with "the
  Universal Level Law", which is now proven in `ambient-reduction.md`.

### I-6. Three different values circulate for the level-5 anchor, and all three feed the level-7 arithmetic

| value | location |
|---|---|
| 50,922,864 | `lowmem-endgame-assessment.md:81`, `:109`; used as *the anchor* at `ambient-reduction.md:677` |
| 50,968,542 | `endgame-theory.md:599`, `:613`, `:804`, `:922` (explicitly reconciled: "reproduces the archived 50,922,864 to 0.09 %") |
| 50,602,871 | `ambient-reduction.md:409`, same command `n=13 --limit 42` — **0.63 % off the anchor and never reconciled**, in the very document whose thesis is that such residuals are removable scheduling noise |

### I-7. Level-7 ceiling disk bracket disagrees between two docs, unflagged

`ambient-reduction.md:687`/`:714` — **136-195 TB**. `endgame-theory.md:824` —
**136-179 TB**. Same state count (3.08e12). 179 TB is what endgame's stated
44-58 B/state gives (`endgame-theory.md:818`); 195 TB comes from lowmem's
≈63 B/state (`:1086`). Neither doc flags the discrepancy. This feeds the go/no-go.

### I-8. `transforms-assessment.md:224-228` bakes the unproven 44 into the level ladder

The `D(n)` table gives `S(13) = "44 or 45"` and hence `D(13) = "7 or 8"`. With the
proven floor at 43 this should read 43/44/45 and `D(13) ∈ {6,7,8}`. Because this
table defines the level ladder reused by `endgame-theory.md`,
`lowmem-endgame-assessment.md` and `ambient-reduction.md`, the stale row is load-bearing
for how the whole compute track is framed.

### I-9. `cert_v2.py` has drifted from the checker version recorded in the prefixcert ledgers

Ledgers record `checker_sha256: 19bcddb8…`; `tools/cert_v2.py` today hashes
`02f1b4bc…` (the vcheck campaign's D1-D4 edits). The vcheck report flags *engine*-binary
drift as an open item but not *checker* drift. Re-verification against the recorded
checker version is no longer possible.

### I-10. `evidence/v3/vcheck/report.md` misstates the theory file's size

Claims "Prefix_Checker.thy (190 lines, no sorry)". The file is **241 lines** (201
non-blank). "no sorry" is confirmed (0 occurrences of `sorry`/`oops`). Small, but
it is a line in the one document certifying a formal artifact.

### I-11. "Formalized" is used in two incompatible senses across the wave documents

`kraft-repair-wave1.md:483` prescribes "**Formalize Theorem 6′** (Isabelle/Lean)".
`kraft-repair-wave2.md` is titled "Theorem 6′ **Formalized**" — but §3 opens
"the point of this section is a clean, self-contained, audit-ready statement…"
(`:244-246`). It is pen-and-paper modularisation; **no proof assistant was used**
(zero Isabelle/Lean mentions in the file). A reader — or the architect reading
only commit messages — will conclude Theorem 6′ is machine-checked. It is not.
The paper's §11 item 2 and §10.2 both turn on this distinction.

### I-12. Wave-1 contains an uncorrected numerical error that Wave-2 identified

`kraft-repair-wave1.md:493` states "120/564 still satisfy the per-node step".
`kraft-repair-wave2.md:828-836` shows the machine-checked figure is **36/564**,
cross-checked two ways, and draws a materially different conclusion: at n = 4,
(C) and (D) are **completely disjoint** on escaping sorters, so Theorem 6″ buys
nothing there. Wave 1 was never edited.

### I-13. Wave-2 has an undefined theorem and a mislabelled corollary inside its headline coverage table

- "**Theorem 8′**" appears once, at `kraft-repair-wave2.md:767`, and is **never
  defined anywhere** — yet it contributes to the `structural union` row of the
  §7.7 coverage table.
- `:771` labels `sum_c 2^{-r(c)} <= 1` as "(Cor. 8b)". Corollary 8b (`:614`) is
  `min_c gamma(c) >= log2(N-1)`. The `r`-variant is the "likewise with `r(c)`"
  clause of Theorem 8 (`:219`).

§7.7 is the single most valuable new picture in the wave work (see I-14); it
should not ship with an undefined theorem in it.

### I-14. The §7.7 coverage census — the best new result — is not reproducible by any shipped verifier

The table at `kraft-repair-wave2.md:759-772` (clean 0.183, escape-free 0.223,
structural union 0.224, and the honesty note that **49.6 % of the corpus has no
proof of eq (8) by any route in this project**) is computed over 153,011 networks
in `.build/v3-swarm2/ptrich/`, which is gitignored. `grep` for `coverage|153011|34057`
in `tools/verify_kraft_wave2.py` returns nothing. The same applies to the wave-1
refuter's independent implementation in `.build/v3-swarm/` — the pass that
"audited Theorem 6′ line-by-line" left no artifact in the repo. If the coverage
table goes into the paper, it must be regenerable.

### I-15. `endgame-theory.md`'s Theorem C is labelled PROVEN but rests on a conjecture

`endgame-theory.md:552-564` — "**Theorem C (family ceiling) — PROVEN.**" It
depends on **Prop. C.0** (`:566-574`), whose own status is "machine-checked
exhaustively at `w ≤ 6`, **conjectured in general**". The doc handles this
honestly in place (a violation could only make a filter reach further, so the
*upper* bound on benefit is safe), but the bare "PROVEN" label propagates into
`ambient-reduction.md:672` and into the commit message. Also: Prop. C.0's
cross-reference "see §9" points at Reproduction; the open-items list is §8
(`:854-889`). Separately, `endgame-theory.md:277-282` labels Proposition 3.2
"**PROVEN**" with no *Check:* line, unlike its neighbours.

### I-16. `ambient-reduction.md` contradicts itself on `known_bounds`

`:61` quotes `known_bounds = [0,0,1,3,5,9,12,16,19,25,29,35]` (12 entries) from
`states.rs:43-53`; `:191` of the same document asserts the 14-entry
`[…,39,45]`, which is what the 11-patch tree actually carries
(`.build/v3-endgame/source/src/search/states.rs:50`, `:553`). §2 row 7 and §3.4
contradict each other, and Theorem D's proof depends on this table.

### I-17. Evidence reports flag hazards that were later closed, and nothing records the closure

`evidence/v3/` is correctly append-only, so a report cannot be amended when a
later campaign closes its blocker. The result is that a reader encounters open
hazards that no longer exist:

| flagged as open | where | actually closed by |
|---|---|---|
| "Prefix-rooted gen-proof … class results are not load-bearing without per-job certificates" | `decomp/report.md:48-51` | `prefixcert/report.md:8-15` |
| "A magic-check guard wrapper before snocheck invocations is cheap insurance — **TODO**" | `prefixcert/report.md:35-37` | `vcheck/report.md:17-19` (`snocheck_guard.sh`, 6/6) |
| "verified-checker extension for load-bearing class results" | `prefixcert/report.md:47` | `vcheck/report.md:27-36` (`Prefix_Checker.thy`) |

Fix without mutating anything: add a new `evidence/v3/STATUS.md` mapping every
flagged hazard to its closing campaign, or to "still open".

### I-18. Selftest counts quoted across reports are version-dependent and no longer reproduce

`cert_v2.py` is quoted at "25/25 selftests" (`prefixcert/report.md:55`) and
"33/33 selftests" (`vcheck/report.md:15`); `class_campaign.py` at "13/13"
(`decomp/report.md:26`) and "19/19" (`prefixcert/report.md:27`). Running
`cert_v2.py selftest` today against `.build/v3-endgame/pipeline/n9/proof.bin`
emits **21 PASS lines**, exit 0, 8 s. The counts are all defensible as successive
versions, but a referee diffing the reports sees four different numbers for two
tools. Quote the count with the tool digest.

Related and worse: **`cert_v2.py selftest` requires a v1 certificate argument**
(`usage: cert_v2.py selftest [-h] [--v2p V2P_FILE] v1file`) and every certificate
in the project lives under gitignored `.build/`. The claimed selftests are
therefore not runnable from a clean checkout at all. A small committed n = 9
fixture certificate would close this and I-14-style gaps cheaply.

### I-19. No single command runs the verifier suite, and none of the nine tools has test coverage

`make verify` runs `unittest discover -s tests`, whose 16 test files cover only
the B/E gate machinery of the *rejected* earlier programme. `grep -rl "verify_huffman2\|kraft\|ambient\|cert_v2" tests/`
returns nothing. An artifact evaluator has no documented way to run the suite. Add
a `make verify-theory` target enumerating all nine tools with their expected exit
codes and modes.

### I-27. The n = 11 headline "13.6× less memory" is wrong twice — independently flagged by the external review

`evidence/v3/n11-certified/report.md:31` — "Search memory | 178 GiB | **13.08 GB
(13.6x less)**".

1. **Unit mixing.** 178 GiB / 13.08 GiB = 13.6, but the table labels our figure
   GB. Normalised consistently it is **14.6×**.
2. **Stage scoping.** 13.08 GB is the *search* peak. The same report discloses at
   `:19` and `:38-43` that gen-proof peaked above **37.9 GB** and was OOM-killed
   twice. End-to-end against Harder's pipeline the reduction is far smaller.
3. **Unreported counterweight.** The same table shows 71 h against Harder's
   4 h 51 m — a ~14.6× *slowdown* — presented only as a parenthetical.

Also `verify.log` carries a second memory figure (peak footprint 5.36 GB) beside
the max-RSS 4.35 GB the report quotes, without saying which is which.

Report all three axes in one table. `docs/final-review-external.md` §5.2 reaches
the same conclusion from a different direction (it was checking whether anyone
had a competing reimplementation — nobody has) and calls it a RED FLAG. Two
independent reviews landing on the same number is the strongest signal in either
document.

### I-20. `docs/lowmem-endgame-assessment.md`'s §0 verdict table contradicts its own banner

Three rows of the §0 table still present the position the file's own 2026-08-21
banner retracts twelve lines above them:

| §0 row | still says | banner (`:1-12`) says |
|---|---|---|
| `:38` | "**PROMOTE to the ranked queue**" | DOWNGRADED TO KILL |
| `:38`, `:970`, `:1121` | "**1,440** co-saturated two-layer suffixes at n=13" | "2,892 not 1,440" |
| `:38`, `:974` | "a *measured* **6.5 → 1.5 CPU-years**" | "was a sample estimate dropped from the journal version" |

A reader who lands on the verdict table — which is what a verdict table is for —
gets the refuted version. Banner-plus-unchanged-body is the wrong pattern here;
the rows need striking through in place.

### I-21. `docs/s13-shape-case-split.md` still describes the Plenum chapter as unobtained

`:91` records E1's status as "Plenum 1972, **paywalled, not in hand**"; `:100-123`,
`:143-145` and `:468` frame E1/E2 as "needs the Plenum chapter" and "costs one
library request to find out". The request was made and answered on 2026-08-18,
and the answer was worse than "unverified" — the proof is invalid as written.
`docs/van-voorhis-theory-report.md:13-15` claims to supersede these rows; the
supersession was never applied in place and no banner was added.

### I-22. The S1..S6 numbering is convention-dependent and no document says so

This is the root cause of I-1, not just a symptom. `tools/verify_shape_case_split.py`
assigns shape IDs by `sorted(..., key=lambda kv: (V(kv[0]), render(kv[0])))`
(`:581-582`) — i.e. by (outcome value, canonical rendering string) — and emits **no**
`C1`/`C2`/`C3` vocabulary at all; the C-mapping lives only in
`tools/class_filter.py:296` (`CLASS_MEMBERS = {"C1": ("S2","S3"), "C2": ("S1","S4"), "C3": ("S5","S6")}`,
consistent with the adjudication). `verify_huffman2.py` uses a different ordering
and derives the class from the root split at `:1444`. Two shapes tie at f = 392,
so the tie-break decides the labels. Neither the case-split doc nor either script
states that S-numbering is convention-dependent. Document it at the head of the
shape table; it will otherwise reproduce the same confusion.

### I-23. The S1→C2 correction is recorded as an invisible HTML comment

`docs/van-voorhis-theory-report.md:500-504` carries the adjudication inside
`<!-- CORRECTION 2026-08-18 … -->`, which does not render in Markdown, and it sits
in a table break physically separated from the `S1 | C2` row at `:498`. The most
contested label in the package is documented in text no reader sees.

### I-24. Two live gates encode 44 as a pass predicate over frozen evidence

`tools/b4_gate.py:220` requires the literal string `"44 <= S(13) <= 45"` in the
status audit, and `tools/e0_method_gate.py:323-324` does likewise. These check a
*frozen 2026-08-15 catalog snapshot*, which does say 44…45, so they are internally
correct and re-running them is sound. But they turn a historical catalog reading
into an executable assertion about the value 44, and nothing next to them says
that is what they are doing. Add a comment; do not change the predicate (it would
break the freeze).

### I-25. Stale check counts and runtimes in the two source theory reports

Already itemised in `NOTES.md` §B1/§B2 but never fixed in the sources, and the
paper cites those sources:

| claim | location | ground truth |
|---|---|---|
| `verify_huffman2.py` "36 checks" | `docs/van-voorhis-theory-report.md:11` | **48** |
| `verify_kraft_dispute.py` "32 checks" | `docs/kraft-dispute-verdict.md:11` | **36** |
| "6.2 s" / "~0.6 s" runtimes | `van-voorhis-theory-report.md:11`, `kraft-dispute-verdict.md:11` | 45.98 s / 1.87 s full; 6.2 s is `--fast` |

### I-26. `docs/research-programme.md` mis-frames the 44 write-up and carries an unrecorded M2 miss

- `:52-54` calls the 44 "folklore … never written up rigorously — **a small
  publishable result sitting on the table**". The outcome inverted: the write-up
  became a refutation.
- `:73` sets M2's target at "≥ 50× step/memory reduction on the n=11 replay". The
  measured outcome is **13.6×** (178 GiB → 13.08 GB,
  `evidence/v3/n11-certified/report.md:31`). The miss is not recorded anywhere,
  and the document's own pivot rule ("< 10× → profile where the waste actually
  lives") is not triggered but the margin is thin.
- `:74` M3 includes "incl. **44-seeded intervals**" — same hazard as B-3.
- `:105-111` "Immediate next actions" are all complete.

---

## NICE-TO-HAVE

- **N-1.** `docs/s13-lower-bound-note.md` is referenced from four places
  (`GOAL_STATE.md:75`, `METHOD_EXPERIMENT_CONTRACT_V3.md:66`,
  `docs/sortnetopt-internals.md:865`, `docs/paper/NOTES.md:346`) and **does not
  exist**. It was superseded by the paper draft; retire the row or repoint it.
- **N-2.** `papers/` is untracked (not gitignored). The four primary PDFs the
  paper cites as "In `papers/`" are absent from the repository. Copyright likely
  prevents committing the Plenum volume; commit a `papers/MANIFEST.sha256`
  instead — the digests are recorded in this review's working notes and were
  recomputed cleanly this pass.
- **N-3.** `docs/paper/audit-paper-draft.pdf` and `.pi/` are untracked. The
  claim "everything is committed" is not quite true. `.pi/settings.json` (4 KB,
  tool settings) should be gitignored.
- **N-4.** `docs/current-status-audit.md:6` states the target as
  `44 <= S(13) <= 45`. This is *correct as frozen B0 evidence* — it reports what
  the maintained catalog says, not what is proven — and is immutable. Add a
  forward pointer elsewhere rather than touching it.
- **N-5.** `docs/research-programme.md:60-61` frames Track A as "the 44-hunt" and
  Track B as "Is 44 impossible?". Accurate to the contract, but reads badly beside
  the audit paper. Consider "the 44-conjecture hunt".
- **N-6.** `SOLUTION_STRATEGY.md:44` describes a proposed strategy as
  "SAT-encode 'complete this prefix to 44 total' per prefix slice". Never executed
  (SAT was REJECTED, `5aba92a`), but as written it would use 44 as a search target.
  Mark the row as retired.
- **N-7.** `.cache/third_party/sortnetopt/.build/` is cited by a v3 report and does
  not exist (the real build trees are under repo-root `.build/`).
- **N-8.** The `80 TB – 35 PB` bracket in `transforms-assessment.md:259`,
  `evidence/v3/limits/report.md:72` and `evidence/v3/zm/report.md:44` is a
  **level-8** bracket, easily misread as level-7 given its adjacency to the
  corrected level-7 figures. Label it.
- **N-10.** `AGENTS.md:3, 44` names `METHOD_EXPERIMENT_CONTRACT_V2.md` as the
  active authority; V3 superseded it the same day (`fbb9878`, 09:13 vs
  `45de1f7`, 01:00). `AGENTS.md` is the agent-facing execution scope, so every
  agent is pointed at the parked contract and the parked F0–F5 ladder
  (`:16-25`). Also `AGENTS.md:24` — "F5 runs one bounded **44-comparator
  campaign**" — and `.claude/agents/architect.md:10`, whose goal ladder ends
  "→ a verified 44". Both files also carry the prohibition
  (`AGENTS.md:27`, `architect.md:22`), so these are win-condition framings rather
  than executable targets, but they should be reworded alongside B-2/B-3.
- **N-11.** `docs/research/synthesis-ranked-queue.md:27` still says "only 5 root
  tree-shape classes" although the file's own banner (`:8-17`) corrects 5 → 3 and
  `docs/s13-shape-case-split.md:326-328` explicitly asked for that sentence to
  change. Same 5-vs-3 staleness, unbannered, in
  `docs/research/xdomain-bound-theory.md:262-265`.
- **N-12.** The n = 9 explored-set count differs by 0.5–1.2 % between Harder's
  206,279 (`docs/sortnetopt-internals.md:17`) and our 207,241 / 208,085 / ~208 k
  (`evidence/v3/m2a/prototype-report.md:361, 587`,
  `evidence/v3/m2b/perf-report.md:574`). `ambient-reduction.md:16` explains this
  class of residual as thread-scheduling noise; no document states the
  reconciliation next to the 206,279 anchor.
- **N-13.** Header dates diverge from git dates in two files:
  `docs/lowmem-endgame-assessment.md:16` says 2026-08-18 (git 08-21);
  `evidence/v3/limits/report.md:3` says "2026-08-17/18" (git 08-18). Minor, but it
  defeats date-based staleness triage, which is the main tool anyone will reach
  for on a package this size.
- **N-9.** *Disclosure, not a defect.* The level ladder is defined so that level 7
  at n = 13 is arithmetically `C(13) + 7 = 37 + 7`. The docs are disciplined —
  they never write the number as a target, `verify_shape_case_split.py:629`'s
  `44 - S_EXACT[12]` is the negated hypothesis of a proof by contradiction, and
  `evidence/v3/decomp/report.md:21` records a filter being excluded for "using the
  forbidden constant". Add one explicit sentence to the publication package saying
  so, so a reader does not have to reconstruct it.

---

## Appendix A — verifier suite results

Run 2026-08-22 on the M4 (Darwin 25.5.0) with
`/Users/yugendren/experiments/sorting_network_s13/.venv/bin/python`, **full modes,
no `--fast`**, each under an explicit per-tool timeout. Delegated runs of this
suite disagreed with each other and with these numbers because they silently
substituted `--fast` and mis-guessed several flags; the table below is from a
single controlled sequential run and is the one to trust.

| # | tool | mode | exit | wall | result |
|---|---|---|---|---|---|
| 1 | `verify_shape_case_split.py` | `--corrected` | **0** | 21.4 s | All 33 checks passed |
| 2 | `verify_shape_case_split.py` | *(default)* | **1** | 27.0 s | 1 of 31 FAILED — **by design**, see note A |
| 3 | `verify_huffman2.py` | full | **0** | 103.3 s | all 48 checks PASSED |
| 4 | `verify_kraft_dispute.py` | full | **0** | 1.2 s | 36 checks; VERDICT (A) HOLE CONFIRMED |
| 5 | `verify_kraft_wave1.py` | full | **0** | 206.0 s | 26 checks, 0 failures; ALL CHECKS PASS |
| 6 | `verify_kraft_wave2.py` | full | **0** | 152.8 s | 27 checks, 0 failures; ALL CHECKS PASS |
| 7 | `verify_endgame.py` | default | **0** | 4.3 s | TOTAL FAILURES: 0 |
| 8 | `verify_ambient.py selfcheck <dump>` | on `base_n9_L25` | **0** | 0.0 s | widths [3..9], 207,995 states — see note C |
| 9 | `cert_v2.py selftest <v1cert>` | on n = 9 fixture | **0** | 3.7 s | 21 PASS, 0 FAIL — see note C |
| 10 | `class_campaign.py --selftest --engine <bin>` | with engine | **0** | 30.0 s | All 19 checks passed — see note C |

**Verdict: 9/9 tools pass in their intended modes. No failure is a blocker.**
Total ≈ 550 s. (Wall times were taken with other agents active on the machine and
are upper bounds; item 3 at 103 s against the paper's recorded 45.98 s is load,
not regression — the digest is unchanged.)

**Note A — item 2 is a deliberate failure, and it is the S1/C-label story again.**
Default mode fails exactly one check:

```
[FAIL] documented claim: exactly 5 root shape classes survive
       -- ordered=6, unordered=3, documented=5
```

`--corrected` swaps in three replacement checks (3 unordered / 6 ordered /
84 plane + 6 abstract) and passes 33/33. This is the machine-verified 5→3
correction working as intended, and `docs/s13-shape-case-split.md:475-476`
documents the exit-code contract. **But** it means the default invocation of a
shipped verifier exits non-zero, which any CI or artifact evaluator will read as
a failure. Either make `--corrected` the default and add `--as-documented` for the
historical claim, or state the contract in the tool's `--help`.

**Note B — no tool regressed, and the two paper-cited digests still match.**

**Note C — three of the nine cannot run at all from a clean checkout.** This is
new and it is B-17:

| tool | required argument | where it lives |
|---|---|---|
| `verify_ambient.py selfcheck` | a `dump` directory (positional, mandatory) | `.build/v3-ambient/dumps/` — gitignored |
| `cert_v2.py selftest` | a v1 certificate file (positional, mandatory) | `.build/…/proof.bin` — gitignored |
| `class_campaign.py --selftest` | `--engine PATH` or `SORTNETOPT_BIN` | `.build/…/target/release/sortnetopt` — gitignored |

There is no argument-free self-check for any of the three. `verify_ambient.py` in
particular has no self-check of its *theorems* at all — `selfcheck` validates a
dump's file layout, and the two delegated runs got exit 0 and exit 1 on
*different* dumps, so the result is dump-dependent as well as artifact-dependent.

---

## Appendix B — paper revision map, section by section

What the revision pass must add or change in `docs/paper/audit-paper-draft.md`.
Ordered by section. "ADD" = new material; "REWRITE" = existing text is now wrong;
"UPDATE" = existing text is right but stale.

| § | action | detail |
|---|---|---|
| Title | keep | NOTES §A's reasoning still holds; provenance finding is unchanged and reconfirmed. |
| Abstract, 34-41 | **REWRITE** | "we give a complete proof of equation (8) for clean sorters" → escape-free (Thm 6′) and (C)∧(D) (Thm 6″). Drop "identifies pass-throughs as the sole obstruction". Add the coverage number: the proved class covers **22.4 %** structurally, and **49.6 % of the measured corpus has no proof by any route**. This makes the positive result look *smaller* and the paper more honest; flag for the architect as a deliberate trade. |
| Abstract, 52-54 | **UPDATE** | "two independent stdlib-only Python scripts (48 + 36 checks)" → four scripts. `verify_kraft_wave1.py` (26 checks, `W1a`–`W5d`) and `verify_kraft_wave2.py` (27 checks, `X1a`–`X6e`) must join §9.1. Note that wave2 imports wave1's layer which imports `verify_huffman2.py` primitives — they are *not* independent in the sense V1/V2 are, and the paper must say so. |
| §1.1, table | **ADD** | `S(11) = 35` is now independently re-certified by this project from its own rebuilt engine (`evidence/v3/n11-certified/`), not only cited from Harder. This directly re-verifies the input to the `35 + 9` recombination and is a genuine strengthening — *conditional on B-12/B-13 being fixed first*. |
| §1.3 item 3 | keep | S10 refutation stands. |
| §1.3 item 5 | **REWRITE** | "A complete, correct proof exists for clean sorters" → escape-free / (C)∧(D). |
| §1.3 item 6 | keep, **STRENGTHEN** | Per-node charging is now closed **structurally**, not just by counterexample: `kraft-repair-wave1.md:347-356` proves that on a tight network `sum_c 2^{a(c)-p(2,T)} = 1` exactly, so no per-node exponent derived from `c`'s own pruning can work. This strictly generalises §7.6.1. |
| §1.4 | **UPDATE** | Artifact description: four scripts, and the V1/V2 prefix convention needs a V3/V4 extension. |
| §2 | **ADD** | New vocabulary: escape, escape-free, `eps(c)`, `gamma(c)`, `r(c)`, the (C)/(D) hypotheses. Lemma W1's identity `W*(c) = a(c)+eps(c)+gamma(c)+r(c)` belongs here — it is the exact correction of eq (5) and is cleaner than the paper's `ov(c)` formulation. |
| §4.6 | **UPDATE** | The 27.1 % headline is the 387-sweep figure and is correctly attributed, but `kraft-repair-wave1.md:390-394` reports a pooled **37.1 %**. Cite the stronger figure or explain why the narrower one is used. Also: `kraft-repair-report.md:202`'s 1.25 maximum for the broken Kraft sum is superseded by **1.6875** at n = 6 (wave1:379-384) — the paper's §4.4 should record that the violation grows with n. |
| §5, "Localisation" 560-566 | **REWRITE** | This is the passage B-7 kills. The correct statement is the §7.7 shape: eq (8) is provable at the pass-through-**poor** end (clean/escape-free) *and* at the pass-through-**rich** end (Theorem 8), and the open problem lives **strictly in between**. Include the census excerpt (`wave2:793-796`). This is a better result than what it replaces. |
| §5, exhaustive attack 576-579 | **UPDATE** | Wave-1 §6 item 3 warns that "both `enumerate_sorters` implementations skip inert comparators, which **are** pass-throughs" and demands every exhaustive claim name its universe. I verified `verify_kraft_dispute.py:855-865` `_all_sorters` does **not** prune — it is true brute force, so the 42/912 counts are sound. Say so explicitly and cite wave1 §6.3 as the caution. |
| §7 (whole) | **REWRITE** | Replace Theorem 6 with Theorem 6′/6″. Retain Facts 1-2 and (R1)-(R3) — wave 2 keeps them (Facts 1-3, Lemma W1 are "general"). Lemma B's wave-1 draft had a false justification, corrected at `wave1:115-118` / `wave2:332-336`; use the corrected one-line form ("the second max traverses no branch node after the meeting"). |
| §7.6.1 | keep | LEMMA★ refutation stands and is re-derived at wave-1 check `W4a`. |
| §7.6.3 | **ADD** | Wave 1 §2.1/2.2/2.3 close three more families with explicit counterexamples (global surgery, direct counting, fractional flow) — all `DEAD`, wave1:468. These belong in this table. |
| §8.1 | **REWRITE** | The conjecture is unchanged, but "Known: true for clean `T`" → the wider classes, with the coverage fractions. |
| §8.2 | **UPDATE** | Add wave-1/wave-2 populations (> 180,000 and 152,003 + 32,043). Add wave-1 §6 item 4's methodological rule: "any future claim of the form 'survived adversarial search' must state seeds, steps and restarts, and should assume a single seed is insufficient" — this is a genuine contribution and belongs in the paper's methodology. |
| §8.3 item 2 | **REWRITE** | "must handle pass-throughs" → must handle **escapes**; pass-throughs are necessary, not sufficient. |
| §8.3 | **ADD item** | wave2 §9.4's realizability reframing (§2.4): eq (8) is now known equivalent to a statement about a binary tree decorated with `(eps, gamma, r)`, false for arbitrary decorations — so all of its content is *which decorations a sorter can realise*. That is the sharpest formulation of the open problem the project has produced and it belongs in §8.3 as the recommended attack. |
| §8.4 | keep | Adjacent results unaffected. |
| §9.1 | **UPDATE** | Four scripts; verified this pass that both existing digests still MATCH (`939979b8…`, `76ee6532…`). Add wave1/wave2 digests. Resolve I-2 before printing. |
| §9.5 item 9 | **UPDATE** | "one shape's class label" is now adjudicated (I-1). Record the outcome and the remaining `admissible_13()` ordering TODO. |
| §10.2 | **REWRITE** | "a precise obstruction (pass-throughs)" → escapes; and the formalisation target is now Theorem 6′/6″, which wave1 §8 item 1 notes "replaces rather than adds to the formalization target". |
| §11 item 2 | keep, **CLARIFY** | Still true — no proof assistant has verified any of Theorem 6/6′/6″. Say this explicitly *because* wave 2 is titled "Formalized" (I-11). |
| §11 item 5 | keep | Still true. |
| §11 item 6 | **UPDATE** | §9.5 now lists nine defects for two scripts; recount for four. |
| §11 | **ADD item** | L4-1: proposed in wave 1 at 25-35 % confidence, revised **down to 15-25 %** in wave 2 (`:865`), with the doc's own honest reading — "L4-1 is probably false at some larger `n`, and is unlikely to be provable" (`:898-899`). If any part of the paper's forward-looking discussion cites it, it must carry that verdict. |
| §12 | **UPDATE** | Add the wave documents. Reference list still needs real bibliographic data (NOTES D-5). |

---

## Appendix C — assessment of the five named open flags

**(a) `Prefix_Checker.thy` second-reader requirement.** *Publication impact:
HIGH if any class result is published; LOW for the audit paper.*
`evidence/v3/vcheck/report.md:51-52` — "needs a second reader before any published
class result leans on it (two statements in its section 3.3)". The theory is
241 lines with no `sorry` (verified). The audit paper does not depend on it at
all. Sequencing recommendation: publish the audit paper first; the second-reader
task gates the *class* paper, not this one. Two related items are worse than the
second-reader gap itself: Isabelle2020 lives in an ephemeral scratchpad
(`vcheck` report line 55), and the `snocheck2` binary lives in gitignored
`.build/` — so the verified chain is not rebuildable from a clean checkout. Fix
those with the same effort.

**(b) `snocheck2` missing SHA-256 digest checks.** *Publication impact: LOW,
and the report characterises it correctly.* It is a corruption-detection gap,
not a soundness hole, it is announced at runtime, and `cert_v2.py` cross-checks
the digests (`vcheck` report lines 40-44). The mitigating story — "run BOTH
checkers, record both verdicts; snocheck2 is the authority on the bound
('verified prefix checker with an unverified decoder' — say it exactly that
way)" — is honest and should be reproduced verbatim in any paper. **However**,
I-9 partially breaks it: the cross-checking script has drifted from the version
recorded in the ledgers. Fix I-9 and this flag is genuinely minor.

**(c) The unobtained IEEE TC 1972 note and 1971 dissertation.** *Publication
impact: HIGHEST of the five. Concur fully with §11 item 1 and NOTES D-1: this
should precede submission.* The note is the reference the chapter cites
*specifically* for the false structural claim, so it determines whether the error
is inherited or introduced — a materially different paper either way. The
dissertation could in principle close the gap entirely, in which case the finding
inverts to "the chapter's exposition is invalid but the theorem is proved
elsewhere". This is procurement, not research: two documents, one paywalled
two-pager and one non-digitised Stanford thesis (ProQuest / Stanford library
scan-on-demand / interlibrary loan). It is the cheapest high-value item in the
whole package and it is not blocked on anything.

**(d) Class results' conditionality.** *Publication impact: MEDIUM, and the
condition is currently mislabelled — and there is a second conditionality nobody
has written down.*

*The second one first, because it is larger.* The class campaign's cost model, and
therefore any claim about which classes are exhaustible, inherits the level
multipliers that B-1 puts in question. If the level-5→6 multiplier is near 2×
rather than 33×, the entire ranking of "which class job is affordable" changes.
No document states that the class programme's feasibility is conditional on an
unmeasured multiplier; after 2026-08-22 it is conditional on a *measured* one that
nobody has read. `evidence/v3/decomp/report.md:56-57` — "Class
results C1/C2/C3 remain CONDITIONAL on the case split until the Kraft repair
lands ('ALL' campaigns are unconditional)." Two problems. First, "until the Kraft
repair lands" reads as a scheduled event; wave 2 §9 says eq (8) in general is
"NOT proved, NOT refuted", recommends **SHIP, DO NOT CONTINUE** (`:73-80`), and
L4-1's confidence went *down*. The honest phrasing is "conditional on an
unproved conjecture, indefinitely". Second, the case split itself is derived by
assuming a 44-comparator 13-sorter exists (`verify_shape_case_split.py:625-635`),
which is legitimate proof-by-contradiction but means the class definitions are
44-conditioned — worth one explicit sentence (N-9). Also note `decomp` blocker 1
("prefix-rooted gen-proof") is now closed by the prefixcert campaign; the decomp
report was never updated to say so.

**(e) Unresolved items in `NOTES.md`.** Of the seven items in NOTES §D:
D-1 open (flag c above, highest value); **D-2 open** and now *harder* — the
formalisation target moved from Theorem 6 to Theorem 6′/6″ (I-11); D-3 open (the
four analytic dead routes still have no check IDs — and wave 1 §2 adds three more
that do); D-4 open (citation verification; the four PDFs are present but untracked,
N-2); D-5 open (bibliographic data); **D-6 now actively wrong** (I-1 — the class
label was adjudicated the other way); **D-7 still open** (the dangling
`s13-lower-bound-note.md` row, N-1). Of NOTES §B's 25 discrepancies, **B3 is now
wrong** (I-1) and the rest remain accurately recorded. NOTES §E's three weakest
points all survive; §E-1 ("the central positive result covers a minority of
networks") is now *quantified* at 22.4 % structural coverage and should be
restated with that number rather than left qualitative.

---

## Appendix D — what held up

Recorded because a red-team document that lists only faults misrepresents the
package.

- Both published artifact digests in the paper's §9.1 **match** today:
  `verify_huffman2.py` = `939979b802c6…f694a3e4`,
  `verify_kraft_dispute.py` = `76ee65320e3f…67442de`.
- All 10 sortnetopt patch digests cited across `evidence/v3/` **match**; all 5
  quoted patch line counts **match**.
- The pinned upstream clone `.cache/third_party/sortnetopt` is **clean**, at
  `0b5d09c47446096f9e3a0812b35afc72b7f2a718` exactly as documented, and
  `git archive` of it reproduces the digest the x86 smoke report shipped.
- The frozen `snocheck` still hashes `4cd30511…`, matching the committed B3
  toolchain manifest.
- All 8 prefixcert certificates recompute to their ledger digests, composing to
  exactly 25/25/29/29.
- The n = 11 certificate digest and byte size match exactly, and all four
  verify-stage numbers match `verify.log`.
- `config/frozen/` and `evidence/` are untouched; the working tree has zero
  modifications to tracked files.
- No document claims to supersede a later one: doc dates run
  paper/report/verdict 08-18 → waves 08-20 → ambient/endgame/lowmem 08-21 →
  n11-certified 08-22, monotonically.
- The theory documents are, without exception, harder on themselves than this
  review is. Wave 2 §7.7's note 2 ("the 1.000 for LEMMA★ is a corpus artefact,
  not a result… 49.6 % of the corpus has no proof of eq (8) by any route in this
  project") is the single best paragraph in the package, and the discipline of
  separating *structural* from *computed* sufficient conditions is exactly right.

---

## Appendix E — recommended sequencing

Not a priority list of severities — an execution order, chosen so that each step
makes the next one cheaper or unnecessary.

1. **Re-derive the level-5→6 multiplier under matched settings (B-1).** Everything
   in the compute track's framing, and the class programme's feasibility ranking,
   waits on this one number. It is also the only item here that could change a
   decision rather than a sentence. Cheap: the census exists; what is missing is a
   matched-regime comparison.
2. **Procure the IEEE TC note and the 1971 dissertation (Appendix C, flag c).**
   Pure procurement, no research, and it determines what the paper's central
   section can claim. It should start now because it has the longest lead time of
   anything in the package.
3. **Fix `docs/paper/NOTES.md` §B3 (I-1) before touching the draft.** The paper's
   own editorial notes currently instruct a correction in the wrong direction. Any
   revision pass that follows NOTES will introduce an error.
4. **Reconcile the two governing documents (B-11).** `GOAL_STATE.md` and
   `METHOD_EXPERIMENT_CONTRACT_V3.md` state different lower bounds. This needs a
   governance decision about the pinned contract hash before the doc sweep, not
   during it.
5. **One doc sweep for the stale-44 cluster (B-4, B-5, B-9, B-10, and I-8,
   I-21, I-26, N-10, N-11).** These are mechanical once step 4 has decided the
   canonical wording. Do them together; done piecemeal they will diverge again.
6. **Apply the two waves' unapplied corrections (B-8, I-12, I-13).** Written
   instructions already exist in `wave1` §6 and `wave2` §8; this is transcription.
7. **Rebuild the evidence chain (B-12, B-13, B-14, B-15, B-17).** Extend
   `evidence_check.py` to `evidence/v3/`, add manifests and checksum inventories,
   commit the small n = 9 certificate and ambient-dump fixtures the verifiers need
   (B-17, I-18), and record the checker identity for the n = 11 run. This is the
   largest single piece of work and it gates any claim that the programme's
   results are reproducible. Do the fixtures first — they are kilobytes and they
   unblock a third of the verifier suite immediately.
8. **Revise the paper (Appendix B).** Last, because steps 1–3 and 6 all change
   what it should say.

**On publishing before all of this is done:** the audit paper's *core* — the
counterexample `T1`, the refutation of eqs (5) and (6), the ten steelman defences,
and the provenance finding — is independent of every blocker above except B-6/B-7
and the two archival items. That core is sound, is machine-checked by two scripts
whose published digests still match, and would survive a referee. The package
around it is what is not ready.

---

## Appendix F — relation to the external prior-art review

`docs/final-review-external.md` (commit `f01fc2a`) landed while this pass was in
progress. The two reviews were conducted independently and do not overlap in
scope: it asks *has anyone done this before, and will it publish*; this one asks
*is the package internally consistent and does the evidence hold up*. Its bottom
line — "nothing in the package is anticipated; publish" — is a priority finding
and this review does not disturb it.

**Where the two converge independently (treat these as confirmed):**

| finding | external | internal |
|---|---|---|
| the n = 11 "13.6×" is unit-mixed and stage-scoped | §5.2, "RED FLAG" | **I-27**, reached via digest/artifact audit |
| Theorem A is not the mathematical result it is presented as | §3.2a, "near-tautological in Harder's formalism — reframe as an implementation audit" | **B-16**, reached via "§0 says all machine-checked; Theorem A is a code-reading audit" |
| the IEEE TC note and the 1971 dissertation are still unobtained | §1.2, §1.3 (re-checked the Dec-2025 bitsavers Stanford collection — not there) | Appendix C flag (c), rated highest-value open item |
| `S(13) ≥ 44` appears in no publication; Wikipedia still says 43 | §2.1–§2.4, re-verified today | B-4, which flags that `docs/sota-survey.md:260` says the *opposite* |

The Theorem A convergence is worth dwelling on: two reviewers looking at
different things — prior art versus internal consistency — independently
concluded that the same theorem is overstated. That is the one item in
`ambient-reduction.md` to fix first.

**Where this review adds something the external pass could not see:**

- **B-1** (the unconsumed level-6 measurement) is invisible from outside; it
  requires reading `evidence/v3/n11-certified/report.md` §"Census facts banked"
  against `lowmem` §Step-0 and noticing that the blocking experiment already ran.
- **B-12/B-14/B-15/B-17** (evidence chain, trust boundary, artifact evaporation,
  unrunnable verifiers) are reproducibility failures that a prior-art search
  would never surface, and they bear directly on the external review's own
  recommendation to submit an artifact.
- **B-6/B-7** (the paper is two theorems behind) is a repository-internal
  staleness that looks like nothing from outside — the draft reads as coherent.

**One place to reconcile before acting on either document.** The external review
recommends adding Harder's Lemma 17 to the paper's §6 ("Harder *does* reproduce
the same max-path-tree identification, harmlessly — pre-empt it"). That is a good
addition and it strengthens §10.1's how-errors-survive narrative. But it lands in
exactly the section this review says must be rewritten for escapes (B-7): if
Harder's Lemma 17 identifies max-path comparators with branch nodes, then whether
it is "harmless there" depends on whether his networks are clean or merely
escape-free — which is now a question with a precise answer. Do B-6/B-7 first,
then write the Harder paragraph once, correctly.
