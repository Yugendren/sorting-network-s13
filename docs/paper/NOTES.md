# Editorial notes for `docs/paper/audit-paper-draft.md`

Internal. Everything here is either (a) a discrepancy between the prose reports
and the verifier code, flagged rather than silently resolved, per the drafting
brief; (b) an editorial decision the architect may want to overturn; or (c) an
open item.

**Rule applied throughout: where the reports and the code disagree, the code is
the source of truth, and the draft follows the code.**

Sources read: `docs/van-voorhis-theory-report.md` (incl. §10 addendum),
`docs/kraft-dispute-verdict.md`, `docs/kraft-repair-report.md`,
`tools/verify_huffman2.py`, `tools/verify_kraft_dispute.py`,
`papers/Complexity of Computer Computations …pdf` pp. 119–129 (PDF pp. 124–134),
`docs/transforms-assessment.md`, `GOAL_STATE.md`.

---

## A. Title

**Changed from the suggested title.** Suggested:

> "The published lower bound for 13-channel sorting networks rests on an invalid
> proof: an audit, a counterexample, and a partial repair"

Used:

> "The widely tabulated lower bound S(13) ≥ 44 rests on an invalid proof: an
> audit of van Voorhis (1972), a counterexample, and a partial repair"

Reason: the suggested title contains the very error the paper corrects.
`docs/kraft-dispute-verdict.md` §7 item 7 and §8 item 5 establish that
`S(13) >= 44` has **never been published**; the *published* lower bound is 43 and
is untouched by this work. A title asserting "the published lower bound … rests
on an invalid proof" would be false and is the single easiest thing for a referee
to attack. "Widely tabulated" is accurate and preserves the force. Revert only if
the architect disagrees with the provenance finding.

---

## B. Discrepancies found — reports vs. verifier code

Numbered for reference. "VV" = `docs/van-voorhis-theory-report.md`, "KD" =
`docs/kraft-dispute-verdict.md`, "KR" = `docs/kraft-repair-report.md`.

### B1. Check counts (three separate errors)

| claim | source | actual |
|---|---|---|
| `verify_huffman2.py` "36 checks, ~6.2 s" | VV:11, VV:649 | 48 checks; stale (pre-Parts G/H) |
| `verify_huffman2.py` "now 47 checks" | VV:669 (§10 addendum) | **48** — off by one, probably predates `G6b` |
| `verify_huffman2.py` "48 checks" | KR:7, KR:447 | **correct** |
| `verify_kraft_dispute.py` "32 checks, ~0.6 s" | KD:12, KD:422 | **36 checks** |

The 32 is not traceable to any subset the doc names; eleven checks (A2, B0, C9,
C'0, D1, D2, D3, D'1, D'2, D'4, D'5) are never cited in KD. **Draft uses 48 and
36.**

### B2. Runtimes

VV:10, VV:649–650 give 6.2 s full / 1.7 s `--fast` for `verify_huffman2.py`.
Measured today (Python 3.14.4, this machine): **45.98 s wall full**, 6.2 s
`--fast`. So the doc's headline "6.2 s" now describes `--fast`, not the audit.
KD:12/422 give ~0.6 s for `verify_kraft_dispute.py`; measured **1.87 s** wall
here (a separate agent measured 0.58 s on a warmer run — the difference is
process startup, not work). **Draft reports the measured full-run numbers.**

### B3. Shape S2's class label — a genuine contradiction

VV §5.5 table (VV:499) lists `S2` as class **C1**. The code
(`verify_huffman2.py:1444`) assigns classes by root split
`{(5,8): "C1", (6,7): "C2", (4,9): "C3"}`, and S2's root split is **6|7**, so the
code prints `S2 (C2)`. Verified root splits: S1 5|8, S2 6|7, S3 5|8, S4 6|7,
S5 4|9, S6 4|9. Everything else in VV's row for S2 (f = 392, deficit 120, nc
multiset, threshold 7) agrees.

**Code is authoritative: S2 is C2.** The draft does not print per-shape class
labels, so nothing needed fixing there, but `docs/s13-shape-case-split.md` and
VV §5.5 should be corrected by whoever owns them. **This changes the C1/C2
class populations** and therefore any downstream count of "how many shapes are in
class C1".

### B4. Two different "deficit" columns in the same run

`verify_huffman2.py:905` prints `deficit = 512 - f` (Part D table; S6 → 0);
`:1426` prints `513 - f` (Part H4; S6 → +1). Both are correct for their own
criterion, but a reader diffing the two printed tables against VV §5.5 sees a
mismatch on every row. Worth reconciling in the script.

### B5. `D7` is a vacuous check

`verify_huffman2.py:945-946`: `check("D7  the MIN-dual doubles the structural
constraint …", True)`. Predicate is the literal `True`. KR:368 cites C1/F3 for
the MIN dual (correct); VV:639 lists the MIN-dual doubling as "proved conditional
on eq (8)" without a check ID (fine). **Draft removes the D7 citation** and says
so in §8.4(a) and §9.5.

### B6. `D3` / `D6` evaluate one shape; the prose claims all six

`verify_huffman2.py:891` and `:934` both index `adm["abstract"][0]` (shape S1).
VV:478–479 claims the value is 44 "for every admissible shape"; VV:515–516
claims "a UNIFORM +1 would kill everything (check D6)". The universal statements
are in fact true (independently confirmed for all six shapes), but the checks do
not establish them. **Draft flags this in §8.4(d) and §9.5.**

### B7. `D-2`'s label overstates its own predicate — and there is a real fact behind it

`verify_kraft_dispute.py:701` counts a clean network as bad only if
`(not eq5_le_ok) or kraft > 1 or (not disjoint_all)`. So eq. (5) is tested only
in the fatal `<=` direction and eq. (6) only as `> 1`. Instrumenting the
untested predicate: **5 of the 151 clean sorters have Kraft sum ≠ 1**, i.e.
eq. (6) *as an equality* fails on clean networks too.

This does not damage anything — Theorem 6 needs only `<= 1`, and Batcher-8 is
clean with 0.75 — but KD:249–252 ("the number that violate eq (5), or eq (6), or
MAX/MAX2 disjointness, is zero") reads as a stronger statement than the check
supports. **Draft states the qualified version and calls out the label.**

### B8. Statistics that are printed but never asserted

- KD §5's entire prevalence table (236/61.0 %, 172/44.4 %, 164/42.4 %, 105/27.1 %,
  …) is `print` output. The registered checks over that sweep are only D0, D1,
  D2, D3, D-1, D-2, which assert existence/universality, not counts.
- KD:180 and KD:326 cite "105 of 387 (27 %)" as `(check D0)`. D0 asserts only
  `tight_and_broken > 0`. Number correct, attribution wrong.
- KD:181 cites 233/387 and 232/387 as `(check D-1)`. D-1 asserts only that both
  are `> 0`. Also KD says "60 %" where the code prints 59.9 %.
- VV §3.6's "eq (5) over-states the true p(2,T) | 12 of the 43" rests on `say()`
  output; the corresponding checks are B4b (existence) and B4 (the sound half).
- VV §3.2's "27 of 43 have pass-throughs" is likewise printed, not checked.
- KD:283's "(K) held on all 387 networks of the sweep" — `repair_bad` is printed
  (value 0), never asserted.

**Draft adds an explicit "asserted versus printed" paragraph in §4.6 and §9.5.**
Recommend adding real checks for these counts if the artifact is ever released.

### B9. Steelman rows S3 and S4 have no code behind them

KD:174 (S3, "Kraft = 1.5") and KD:175 (S4, "Kraft >= 1.5"): `MaxTree.q` implements
exactly one q-tracing convention; there is no pruned-network reading and no
MAX2-contraction reading in the file. These two numbers are hand-derived.
**Draft keeps S3/S4 in the table (they are refutations of defences, and the
arithmetic is trivial for `T1`) but they are not machine-backed. If a referee
presses on the steelman table, these are the two soft rows.**

Similarly KD:172 (S1, "with tree nc eq (5) still gives 4 > 3") is printed
(`eq5_tree`, value 4) but never asserted.

### B10. `A5` hand-patches an unproved input

`verify_huffman2.py:239`: `p2tab[11] = 9   # the chapter's MIN-dual result`,
inserted *after* check A4 has established that eq. (12) gives only 8 at N = 11.
VV:210 describes A5 as regenerating the `L(N)` column "from `P(1,N)` and
`P(2,N)`" without noting the patch. The code comments it. **Draft discloses it in
§9.5 item 4.** A5 verifies internal consistency of Table 1 given the chapter's
unproved `P(2,11) = 9`; it does not derive the column from proved inputs.

### B11. `H3` does not identify the shape as S6, nor check cleanliness

`verify_huffman2.py:1402-1411` takes the *first* 13-leaf shape with
`f ∈ {496, 512}` and breaks. KR:352–353 attributes the result to "the clean
realization of shape S6". Values match (512 / 392); the attribution is the doc's,
not the check's. **Draft states the result without the S6 attribution.**

### B12. `~84 %` / `~35 %` in KR §3.1 are not computed by the cited script

KR:205–207: "over 900 constructed sorters, the second max leaves the blue leads
in ~84 % of general sorters and in 0 % of clean ones, and eq (6) fails in ~35 %
of general sorters and 0 % of clean ones." In `verify_huffman2.py:1270-1275`,
both `bad_blue` and `bad_kraft` are computed **only inside `if isclean:`**. The
script never evaluates blue-trapping or the Kraft sum on the 772 non-clean
sorters; G2/G3 print `128/128`. The "~84 % / ~35 % of general sorters" figures
must come from `.build/v3-theory/redblue.py`, which is scratch, not from the
script KR names as its machine check.

**Draft does not use the 84 %/35 % figures.** It uses the 387-network sweep's
42.4 % for eq. (6) instead, which *is* computed by a shipped script.

### B13. Aggregate network totals

VV:315–316 "~5 600 constructed sorting networks"; KR:279/429 "~6 500". Both fold
in `.build/v3-theory/stress.py`. The shipped scripts alone touch ≈1,554
(verifier 1, full mode) and 387 + 954 + 4 fixed (verifier 2). **Draft reports
1,890 across the four main sweeps plus ~60 auxiliary plus 954 exhaustive, and
separates the scratch sweeps explicitly.**

### B14. "No witness network is embedded anywhere" is not literally true

KD:431 and KR:452–457 both say every network is constructed or enumerated and
"no witness network is embedded anywhere". `T1`, `T2` and `T3` are hard-coded
literals (`verify_kraft_dispute.py:577, 631, 778-781`;
`verify_huffman2.py:1294-1295`). `T3`'s own comment says it was found by
`.build/v3-theory-audit/adversarial.py` and is "pinned here as a fixed test".

This is **not** a violation of the project's hygiene rule in substance — none of
the three is a witness for an open case; T1/T2 are the two optimal 3-sorters and
T3 has 15 comparators where `S(6) = 12` — but the wording is wrong and would be
caught. **Draft §9.4 names all four literals explicitly and states that `T3` is
re-verified but not re-derived.**

### B15. `--fast` is offered as a reproduction command without caveats

KD:423 and VV:650 list `--fast` alongside the full run in their Reproduction
sections. Under `--fast` the second verifier's sweep drops 387 → 93 and its
`n = 4` enumeration drops 912 → 12; the first verifier's Parts B/F/G drop
43 → 33, 560 → 150, 900 → 320. Every headline statistic becomes
unreproducible. **Draft adds an explicit warning box in §9.2.**

### B16. `--seed` is undocumented

`verify_kraft_dispute.py:526` defines `--seed` (default `20260818`); KD:428 says
only "fixed seed". Since the 387-network composition is seed-dependent, so is
every percentage in KD §5. **Draft documents the flag and the dependence.**

### B17. `verify_kraft_dispute.py` Part F prints a claim its own doc retracts

`verify_kraft_dispute.py:828` prints "S(13) >= S(11) + P(2,13) = 35 + 9 = the
published bound". KD:339 and KD:394–404 explicitly retract exactly this: the 44
is *not* published. The script that is cited as the doc's evidence still prints
the retracted phrasing. **Draft notes this in §9.5 item 8.** Recommend fixing the
string.

### B18. Module docstring drift

`verify_huffman2.py` lines 27–47 (`WHAT IS CHECKED`) enumerate Parts A, B, C, D,
F only. Parts E, G, H are run and contribute 21 of the 48 checks. Execution order
is A, B, **E**, D, F, G, H, not the header's order. Also line 1461 is dead code
(`print(__doc__.split("USAGE")[0].strip()[:0] or "", end="")` always prints "").

### B19. `G6b` label vs. predicate

Label says the sample "is NOT evidence for the lemma"; predicate is
`bad_best == 0`, i.e. it fails if a violation is found. Deliberate (regression
guard) but reads as self-contradictory. Cosmetic.

### B20. `p(2,T)`: ordered vs. unordered quantification

`verify_huffman2.py:800-812` maxes over **ordered** pairs `(i,j)`, `i != j`
(its docstring says `C(n,2)`, which is wrong). `verify_kraft_dispute.py:142-153`
uses `itertools.combinations`, i.e. **unordered** pairs. The two therefore compute
`p(2,T)` by different quantifications.

They agree because `W(x,y) = W(y,x)`: writing `c = LCA_B(x,y)`, the union is
`(p_x before c) ∪ (p_y before c) ∪ {c} ∪ (max's onward path) ∪ (second max's
onward path)`, and the last two depend only on `c`. This is a one-line argument
but it is **not** in either script and not in any report. **Draft states it in
§9.5 item 7.** If either script is ever changed, this is a place where a silent
divergence could appear.

### B21. `--fast` does not change check counts

Both scripts run the same number of checks in either mode (48, 36). Noted only
because it makes "48 checks passed" a weaker signal than it looks: passing under
`--fast` and passing in full are the same headline.

### B22. Section numbering in the source reports

Both VV and KD jump from §8 to §10; there is no §9 in either. Cosmetic; noted so
that a future reader does not go looking for a missing section.

### B23. `E3`/`E4` enumerate networks, not minimal sorters

`_all_sorters` starts at `k = 1` with no symmetry or redundancy pruning, so the
42 and 912 counts include sequences with redundant comparators. The docstring
claims it starts "at the smallest k that admits one". Harmless for the claim
(the conclusion is tested on a superset) but the counts should not be quoted as
"the number of minimal 3-sorters". **Draft phrases them as "every comparator
sequence of length ≤ k that sorts".**

### B25. The two scripts' check IDs collide

Both define an `A1`, `A2`, `B1`–`B6`, `C1`, `D1`–`D3`, `E3`, `E4` — meaning
entirely different things. E.g. `E3`/`E4` in `verify_huffman2.py` are steps of the
3-sorter counterexample; in `verify_kraft_dispute.py` they are the exhaustive
`n = 3` and `n = 4` enumerations. `D1` is the Huffman identity in one and a
prevalence existence claim in the other. **Both prose reports cite bare IDs, so
several of their citations are ambiguous on their face.**

The draft introduces a `V1:` / `V2:` prefix convention (defined in §1.4, restated
at the head of §9.3) and uses it for every citation. Recommend the same
convention, or renumbering, in the source docs and scripts.

### B24. Part B's "random channel relabellings" family is nearly empty

`verify_huffman2.py:570-573` keeps a relabelling only `if sorts(r, n)`, and
exactly **1 of the 43** Part B networks is a relabelling. VV §8 and KR §9 both
list relabellings among the families exercised, which overstates their
contribution in verifier 1. (In verifier 2 they are substantial: 115 of 387.)
**Draft lists relabellings only for verifier 2's population.**

---

## C. Editorial decisions taken

1. **`LEMMA★` and `(K)` are the same statement.** KR calls it LEMMA★ with
   `W*(c)`; KD calls it `(K)` with `u_j`. The definitions coincide
   (`verify_huffman2.py:1173-1180` vs `verify_kraft_dispute.py:444-451`). The
   draft says so once, in §7.6.1, and then uses both names. Consider unifying
   the terminology in the source docs.
2. **Huffman2 is compressed to one subsection (§8.4(d)).** It is proved modulo
   exactly the same two lemmas, so it adds no independent risk and no independent
   result; giving it more space would dilute the paper. If the architect wants
   the Huffman2 material foregrounded (e.g. because it is the pruning rule the
   Track-B campaign wants), it should be a companion note, not a section here.
3. **The MIN dual, `P(2,11) = 9`, realizability and the MAX/MIN refutation are
   grouped as §8.4 "adjacent results".** They are correct and cheap but they are
   not the paper's finding.
4. **`docs/transforms-assessment.md` contributed almost nothing.** Its only
   bound-landscape content is the `S(n)` table for `n <= 12` and a framing of
   `S(13) >= 44/45` in terms of "levels" of a free-chain ladder, with no
   citations for Juillé, Green or Dobbelaere. Nothing from it is load-bearing in
   the draft. Flagging so nobody re-reads it expecting more.
5. **The AI-methodology paragraph is §10.3, one paragraph, no marketing.** It
   states the division of labour, the one place it produced something (the `T3`
   counterexample from the adversarial role), and then pivots to the only thing
   that matters for a reader: nothing rests on a model's assertion.
6. **The Fig-4 misstatement/gap distinction gets its own subsection (§4.7)** and
   is restated in the abstract, because KD §7 item 5 is right that publishing
   them undifferentiated would be an overreach.

---

## D. Open items before this could go anywhere

1. **The IEEE TC note (C-21(6), 1972, 612–613) and the 1971 Stanford
   dissertation are unobtained.** §11 items 1. This is the highest-value open
   item and it is a procurement task, not a research task. Until it is closed,
   the paper cannot say where the error originates.
2. **Theorem 6 is not formalised.** §7.5 is a human proof. Given §7.6.1's
   cautionary tale, formalising it in Isabelle or Lean is the natural next step
   and is small.
3. **The four dead routes in §7.6.3 (rows 1–4) are analytic, not machine-checked.**
   The "43 at n = 13" and "156 at n = 13" figures in particular are asserted in
   KR §3.5 with no check ID. Either add checks or present them as sketches.
4. **Citation verification.** `S(9) = 25`, `S(10) = 29`, Juillé 1995, and the
   exact Dobbelaere changelog wording/date are carried from project notes and
   background knowledge. Only four PDFs are physically in `papers/`: the 1972
   chapter, STAN-CS-71-238, the STOC '95 asymptotic paper, and arXiv:2511.04107v2.
   Flagged in §11 item 7.
5. **The reference list needs real bibliographic data.** Several entries are
   currently identified by the chapter's own short forms (Green (1970A),
   Batcher (1968A), Floyd and Knuth (1970A)) because that is all that is in hand.
6. **Numbers in `docs/s13-shape-case-split.md` §5/§7 may inherit the S2 class
   error (B3).** Not in scope for this draft; flagged for whoever owns it.
7. **`GOAL_STATE.md`'s "Side quest" row** points at
   `docs/s13-lower-bound-note.md` (the "44 bound write-up"). That row is
   superseded by this draft; someone should decide whether to retire it or point
   it here.

---

## E. The three weakest points, for triage

Restated from the completion report so they live in the repo.

1. **The central positive result covers a minority of networks.** Theorem 6
   assumes cleanliness; 61 % of the audited population is not clean. A referee
   will ask what fraction of *size-optimal* networks is clean — a question the
   artifact does not answer, and the honest reply is that we do not know.
2. **The prevalence figures are generator-dependent.** 61.0 %, 42.4 % and 27.1 %
   are properties of bubble/Batcher/insertion/odd-even/thinned-random-prefix
   generators, not of sorting networks under any measure. The qualitative claim
   ("common, not exotic") is safe; the numbers are not rates.
3. **The literature negative is a search result, not a proof of absence**, and it
   has two named holes (the TC note and the dissertation), one of which is
   precisely where the disputed structural claim is cited from.
