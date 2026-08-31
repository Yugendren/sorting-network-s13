# Length calibration: what papers in this genre actually run to, and what ours should

**Date:** 2026-08-31. **Scope:** measurement and recommendation only. No paper text
was edited; no commits. Writes: this file and `.build/v3-calib/`.

**Method.** Every page count below marked **[M]** was measured directly: the PDF was
downloaded and `pdfinfo` read, or the publisher's page range was taken verbatim.
Word counts marked **[M]** come from `pdftotext | wc -w` on the same file. Anything
not so marked is flagged as unverified in place.

**The one methodological point that governs everything else.** Pages are not a stable
unit in this literature. The *same* Codish et al. result was published at **8 pp**
(ICTAI 2014, IEEE two-column), **13 pp** (JCSS 2016, journal two-column) and **18 pp**
(arXiv preprint, single-column). Density ranges from 321 to 858 words/page across the
sample. **Words are the stable unit**; the working conversion for a single-column
preprint in this genre is **≈ 555 words/page**, which is what Harder's body, Bundala
& Závodný, Codish et al. (arXiv) and the JAR paper all independently land on.

---

## 0. The answer in one screen

**The distribution.** Papers in our exact area run **6 to 54 pages / 1,900 to 24,600
words, median ≈ 16 pp / 7,500 words**; correction papers whose whole contribution is
"a published proof is wrong" run **2 to 24 pages, median 4.5 pp / ~2,400 words**, and
**10 pp / ~5,300 words** when they also carry a repair; cutoff/method papers in
verification run **10 to 25 pages with an LNCS mode of exactly 15**; IPL short notes
run **1 to 14 pages, median 5, with 98.7 % at or under 9** (n = 1,636, DBLP;
cross-validated against Crossref); and the journal-erratum channel has a **median of
2 pages** (n = 31, Crossref).

**The verdict.** Two papers. A correction of **6,000–6,500 words / 11–12 pp** carrying
the audit, the twenty-entry finding and the partial repair; and a method paper of
**8,000–8,700 words / 15–16 pp** carrying the machine-checked collapse theorem, the
certified `S(11)`, and the priced negatives — with a documented fallback to a 6–8 pp
experimental note if the collapse theorem's surviving novelty is judged too thin to
headline.

**The uncomfortable finding.** The current 8,300-word draft is not over-written in
total. It is **misallocated**: its best result (the audit) gets 2.9 pages where the
genre pays 4–5, its weakest (the priced negatives) gets 1.6 where the genre pays 0.5,
and its abstract is 274 words against a genre band of 75–155. Meanwhile ~10,000
words of *stronger, newer* material — the twenty-entry table, the Isabelle
mechanization, the second-domain generalization, the corrected level-7 position — is
not in the draft at all.

---

## 1. The measured sample

### A. Computational-proof papers in exactly our area

| paper | venue | pages | words | w/pp | refs | the novel claim | pp on the claim |
|---|---|---|---|---|---|---|---|
| Ehlers & Müller, *Faster Sorting Networks for 17, 19 and 20 Inputs*, arXiv:1410.2736 | preprint (LNCS style) | **6** [M] | **1,928** [M] | 321 | ~12 | three new depth upper bounds | ~1 pp method, 0.5 pp results; the rest is the networks themselves |
| Bundala & Závodný, *Optimal Sorting Networks*, arXiv:1310.6271 | LATA 2014 | **12** [M] | **6,658** [M] | 555 | ~15 | optimal depth settled for n ≤ 16 | ~4 pp (the two-layer symmetry reduction, pp. 4–8); 2 pp SAT encoding; 1 pp experiments |
| Codish, Cruz-Filipe, Frank & Schneider-Kamp, *Twenty-Five Comparators is Optimal…*, arXiv:1405.5754 | preprint | **18** [M] | **10,045** [M] | 558 | 12 | S(9)=25, S(10)=29 — closes two open instances | ~1.5 pp for the result; ~7 pp for the machinery that produced it |
| — same, JCSS preprint | JCSS **82(3):551–563** (2016) | **17** pre [M] / **13** pub | **11,161** [M] | 656 pre / 858 pub | 33 | as above | as above |
| — same, conference version | ICTAI 2014, **pp. 186–193** | **8** | — | — | — | as above | — |
| Cruz-Filipe, Larsen & Schneider-Kamp, *Formally Proving Size Optimality of Sorting Networks* | **JAR 59:425–454** (2017) | **31** pre [M] / **30** pub | **17,151** [M] | 553 | 53 | Coq formalization of the S(9) proof; extracted checker | **19 pp** (§4, pp. 10–29) on the formalization alone |
| Codish, Cruz-Filipe & Schneider-Kamp, *The Quest for Optimal Sorting Networks: Efficient Generation of Two-Layer Prefixes*, arXiv:1404.0948 | SYNASC 2014 | **8** [M] | **7,472** [M] | 934 (2-col) | — | two cross-`n` layer recurrences + a generation method | ~3 pp |
| Marinov & Gregg, *Sorting Networks: The Final Countdown*, arXiv:1502.05983 | preprint | **16** [M] | **7,375** [M] | 461 | — | new pruning for depth search | ~5 pp |
| Cruz-Filipe & Schneider-Kamp, *Formalizing Size-Optimal Sorting Networks: Extracting a Certified Proof Checker*, arXiv:1502.05209 | ITP 2015 | **16** [M] | **7,300** [M] | 456 | — | a Coq-extracted certified checker for the S(9) proof | ~8 pp |
| Harder, *An Answer to the Bose–Nelson Sorting Problem for 11 and 12 Channels*, arXiv:2012.04400v3 | **arXiv only, never published** | **54** [M] (44 body + 3 refs + 7 appendix) | **24,560** [M] | 558 body | 29 | S(11)=35, S(12)=39 | **2 pp of 54** (§9, pp. 42–44) |

**The 54 pp figure our earlier campaign recorded is confirmed [M].** Its internal split
is worth having exactly:

| Harder section | pages | share |
|---|---|---|
| 1 Introduction (related work woven in, no separate section) | 1–3 | 4 % |
| 2 Preliminaries | 3–6 | 6 % |
| 3 Partial sorting networks, incl. **3.2 the generalized Van Voorhis bound** | 6–15 | 17 % (the generalization itself: **3 pp**) |
| 4 Well-behaved sequence sets | 15–18 | 6 % |
| 5 The algorithm | 18–29 | **20 %** |
| 6 Implementation | 29–31 | 4 % |
| 7 Certificates | 31–36 | 9 % |
| 8 Formal verification (8.2 *Trusted Base*, p. 40) | 36–42 | **11 %** |
| **9 Computing s(11) and s(12) — the headline** | 42–44 | **4 %** |
| 10 Conclusion + Future Work (8 lines) | 44–45 | 2 % |
| References (29) | 45–47 | 6 % |
| Appendix A: parallel pseudocode | 48–54 | **13 %** |

Read that column again. **Harder spends 4 % of the paper on the number and 20 % on
why the algorithm that produced it is right, plus 11 % on the trust argument.** The
JAR paper is the same shape at a different ratio: 63 % of it is the formalization.

### B. Correction / erratum / audit papers — the sub-genre our headline belongs to

Ten real examples, page counts measured from the PDF or taken from the publisher's
page range.

| paper | venue | pages | words | refs | repair? |
|---|---|---|---|---|---|
| Johnson-Freyd, *Erratum in "A combinatorial universal ⋆-product"*, arXiv:1307.2940v3 | arXiv (replaces the original) | **2** | 743 | 4 | no |
| Jarnicki & Pflug, *A counterexample to a theorem of Bremermann on Shilov boundaries* | **Proc. AMS 143 (2015) 1675–1677** | **3** | 1,240 | 3 | no |
| Heisel & Lauritzen, *A note on a paper by Hashemi and Kapur*, arXiv:2510.05103 | arXiv (2025) | **3** | 1,224 | 2 | no |
| Goldberg & Jerrum, *A counterexample to rapid mixing of the Ge–Štefankovič process* | **Electron. Comm. Probab. 17 (2012) 1–6** | **6** | 3,593 | 9 | no |
| Elkin & Kurlin, *Counterexamples expose gaps in the proof of time complexity for cover trees…* | **IEEE TopoInVis 2022, pp. 9–17** | **9** | 10,275 | **38** | deferred to a separate paper |
| Neeman, *A counterexample to a 1961 "theorem" in homological algebra* | **Invent. Math. 148 (2002) 397–420** | **24** | 8,973 | 4 | no |
| Holmgren & Wein, *Counterexamples to the Low-Degree Conjecture*, arXiv:2004.08454 | arXiv | **10** | 5,246 | 22 | **yes** — a modified conjecture that survives |
| Willard, *Refuting Feder, Kinne and Rafiey*, arXiv:1707.09440 | arXiv | **12** | 5,287 | 11 | **yes, then withdrawn** — §3 patches, §4 defeats the patch |
| Sadhu et al., *Corrigendum to "Linear time algorithm to cover and hit…"* | **TCS 806 (2020) 632–640** | **9** pub (15 arXiv) | 6,324 | 1 | **yes, full** — algorithm repaired, O(n) → O(n²) |
| Ishizuka, *Corrigendum: PLS is contained in PLC*, arXiv:2312.04051v2 | arXiv | **1 pp of new content** (+14 pp original reprinted) | 491 | 1 | downgraded to "Conjecture 1" |

**The two numbers that matter most in this whole document:**

- **Pure correction, no repair: median 4.5 pp / ~2,400 words** (2, 3, 3, 6, 9, 24;
  drop the Neeman outlier and the median is **3 pp**).
- **Correction *with* a repair: median 10 pp / ~5,300 words** (9, 10, 12). That is
  **2.2× the pure-correction median on both pages and words** — the two measures
  agree independently.

For contrast, the *journal-erratum channel* is much shorter still. Crossref, all
corrigenda/errata with resolvable page ranges: SIAM J. Comput. n=9 median **1 pp**;
TCS n=17 median **2 pp**; IPL n=3 median 3 pp; JACM n=2 median 2 pp. **Pooled n=31,
median 2 pp, range 1–11.**

**When does a correction paper get long?** The sample gives a clean rule: only when
(i) the counterexample needs new mathematical objects built to host it (Neeman, 24 pp
— §3 the counterexample is 7 of 24 pp; the other 17 are machinery and Deligne's
appendix), (ii) it audits a whole *downstream literature* rather than one theorem
(Elkin & Kurlin, 9 pp, 38 refs, because four downstream results inherit the gap), or
(iii) it ships a repair (Willard, Holmgren–Wein, Sadhu et al.). **Our paper is
(ii) + (iii) simultaneously**, which is the strongest length justification available
in this sub-genre — and it caps out around 10–12 pp, not 15.

**Where the pages go.** The correction proper occupies 85 %, 77 %, 67 %, 50 %, 61 %,
29 %, 46 %, 7 % of the respective papers — a sharp inverse relation with total
length. Short notes are nearly all counterexample; long ones are nearly all scaffolding.

**Conventions specific to this sub-genre:**

- **The abstract states the error in the first sentence: 10 of 10.** Willard's entire
  abstract is one sentence: *"I give an example showing that the recent claimed
  solution by Feder, Kinne and Rafiey to the CSP Dichotomy Conjecture is not
  correct."*
- **The target is named bluntly, and 6 of 10 name it in the title.** *"Refuting Feder,
  Kinne and Rafiey"*; *"…a theorem of Bremermann"*; *"A note on a paper by Hashemi and
  Kapur"*. Neeman puts scare quotes on "theorem" in his own title and names Roos in
  sentence one, adding the motive: *"This is a 'theorem' that many people since have
  known and used… The idea is to make the counterexample easy to read for all the
  people who have used the result in their work."* **That sentence is the model for our
  §1.** Softening appears only in *self*-corrections.
- **Contributions list: 0 of 10.** Consistent with genre A.
- **Reference count: median 4** for pure corrections. The two outliers (38, 22) are
  high precisely because those papers also survey the affected literature — **which is
  what our twenty-entry table does**, and it justifies our list growing past 19.
- **Standalone vs erratum: roughly even.** 4 of 10 standalone peer-reviewed (Invent.
  Math., Proc. AMS, ECP, IEEE TopoInVis), 4 arXiv-only, 2 formal errata. **A
  standalone correction paper is a normal, respectable object** — this is not a
  second-class publication route.

*Caveat recorded: publication status for the Heisel–Lauritzen, Holmgren–Wein and
Willard items is "no `journal_ref` in arXiv metadata at query time", which is not
proof they were never published.*

**One thing the search did not find, and it matters:** there is **no
correction-genre precedent inside the sorting-network literature itself**. If we
write this, it is the first.

### C. Method / cutoff papers in verification — how a reusable-method claim is packaged

Page ranges cross-verified against DBLP **and** OpenAlex; page counts from `pdfinfo`
on the actual PDFs; section budgets computed from PDF text-block y-coordinates
(±0.05 pp), except the 1995/1998/2003 scans, which needed OCR and use line-index as a
vertical proxy (±0.1 pp).

| paper | venue | page range | **pp** | refs | contrib. list | experiments | appendix |
|---|---|---|---|---|---|---|---|
| **Kaiser, Kroening & Wahl**, *Dynamic Cutoff Detection in Parameterized Concurrent Programs* | CAV 2010, LNCS 6174 | **645–659** | **15** | 19 | prose | **2.67 pp, 2 tables** | none |
| **Namjoshi**, *Symmetry and Completeness in the Analysis of Parameterized Systems* | VMCAI 2007, LNCS 4349 | **299–313** | **15** (preprint 20) | 43 | **§1.1 "Contributions"** | 1.07 pp, 1 table | 2.85 pp (preprint only) |
| Emerson & Namjoshi, *Reasoning about Rings* | POPL 1995 | **85–94** | **10** | ~41 | none | none (§5 Applications) | none |
| — journal version, *On Reasoning About Rings* | IJFCS 14(4) 2003 | **527–550** | **24** | 33 | none | none | **4.98 pp** |
| Emerson & Namjoshi, *On Model Checking for Non-Det. Infinite-State Systems* | LICS 1998 | **70–80** | **11** | 36 | none | none (§5 Applications) | 0.92 pp |
| Emerson & Kahlon, *Reducing Model Checking of the Many to the Few* | CADE-17 2000, LNAI 1831 | **236–254** | **19** | 25–27 ⚠ | ⚠ | ⚠ | ⚠ |
| Jaber, Jacobs, Wagner, Kulkarni & Samanta, *Param. Verification of Systems with Global Synchronization and Guards* | CAV 2020, LNCS 12224 | **299–323** | **25** | **55** | none | 0.98 pp, 1 table | 0.91 pp |
| Horn & Sangnier, *Deciding the Existence of Cut-Off in Param. Rendez-vous Networks* | CONCUR 2020, LIPIcs 171 | **46:1–46:16** | **16** (arXiv 20) | 31 | run-in ¶ | **none** | none |
| Bhat & Nagar, *Automating Cutoff-based Verification of Distributed Protocols* | FMCAD 2023 | **75–85** | **11** (arXiv 27) | 28 / 19 | numbered 1)2)3) | 0.18 pp pub / 4.2 pp arXiv | 1.17 pp (arXiv) |

⚠ *Emerson & Kahlon is the one gap: Springer blocks the full text and no author copy
survives. The 19 pp range is double-verified; the internal structure is unmeasured.*

**Where the pages go (measured, fractional pages):**

| section | KKW '10 (15pp) | Namjoshi '07 (20pp pre) | E&N POPL'95 ext | E&N LICS'98 (11pp) | E&N IJFCS'03 (24pp) | CAV'20 (25pp) | CONCUR'20 (20pp) |
|---|---|---|---|---|---|---|---|
| Intro | 1.62 | 1.84 | 1.20 | 1.24 | 1.64 | 2.15 | 1.78 |
| Preliminaries | 2.00 (13 %) | ~0.70 | **4.00 (21 %)** | 1.24 | **5.14 (21 %)** | 4.14 (17 %) | 2.02 |
| **Method + theorems** | **5.52 (37 %)** | **9.94 (50 %)** | 5.07 (27 %) | 3.20 (29 %) | 5.36 (22 %) | **10.63 (43 %)** | **12.61 (63 %)** |
| Applications / experiments | 2.67 (18 %) | 1.07 (5 %) | 1.39 | 2.01 (18 %) | 1.32 | 0.98 (4 %) | 0 |
| **Negative results** | ~0.15 | ~0.40 | **0.83 (§6)** | — | **1.43 (§6)** | ~1.2 | headline |
| Related work | 0.99 (6.6 %) | 1.14 (5.7 %) | 0.66 | 0.49 | 1.16 | 1.00 (4.0 %) | **0** |
| References | 1.26 | 2.58 | 1.51 | 1.54 | 2.32 | **4.36 (17 %)** | 2.40 |
| Appendix | 0 | 2.85 | 3.98 | 0.92 | 4.98 | 0.91 | 0 |

**The five findings that bear on us:**

1. **The LNCS cutoff-paper mode is exactly 15 pages** — CAV 2010 and VMCAI 2007 hit
   645–659 and 299–313 precisely. Range across the sub-genre is 10–25 pp, and the
   split is by venue template, not by content: ACM/IEEE two-column 10–11 pp; LIPIcs
   16 pp; LNCS single-column 15–25 pp.
2. **Journal expansion buys proofs, not method.** POPL'95 → IJFCS'03 is 10 → 24 pp
   (2.4×; words 7,495 → 20,024), of which **5.0 pp is a proof appendix** and the
   method section grew only 5.07 → 5.36 pp. A single-column LNCS paper grows only
   25–35 % on the way to arXiv, almost entirely appendix.
3. **The method section is 37–63 % of the paper.** That is where a reusable-method
   claim lives, and nothing else in the paper is allowed to crowd it.
4. **Related work: median 0.99 pp, 4–7 %, stable across 28 years and every venue
   format.** KKW packs its 0.99 pp into three labelled buckets — *"Cutoffs:"*,
   *"Petri nets:"*, *"Tools:"* — and opens with an explicit primacy claim. That is
   the exact device we need for the KKW-vs-us distinction.
5. **Experiments are small, and bibliography routinely outweighs them.** Median ~1.0
   pp (4–5 %); **three of eight papers have no experiments at all**, substituting a
   hand-worked "Applications" section. CAV 2020 spends 4.36 pp on references against
   0.98 pp of evaluation — a 4.4:1 ratio. Only KKW invests heavily (2.67 pp, 17.8 %),
   and it is the one paper whose abstract promises *efficiency* rather than
   decidability.

**And the finding that changes our plan for the negatives.** **All eight papers report
cases where the method does not apply, and it is load-bearing rather than
apologetic.** Emerson & Namjoshi give undecidability its own numbered §6 in both
versions — and **the journal version *grew* the negative result by 72 %**, 0.83 pp →
1.43 pp. CAV 2020 spends ~1.2 pp on a worked quadratic-cutoff lower bound and concedes
the general cutoff "may be too large to be of practical value". KKW puts its failures
in the data: a `Kanban … mem-out` row explained in three lines, and a row class for
the 54 of 852 programs (6 %) that time out. Namjoshi turns failure into a feature —
because his invariant is provably strongest, *"a failure indicates that there is no
inductive invariant of the particular shape."*

**This is the one sub-genre in the whole sample that pays for a negative result, and
it pays 0.8–1.4 pp when the negative delimits the method.** Our level-7 and
decomposition results belong in Paper 2, written in exactly that register — not as a
project status report, but as the boundary of the collapse theorem's practical reach.

*Counter-example worth recording:* Bhat & Nagar's arXiv preprint has a failure column
with 3 of 7 protocols failing and ~2 pp explaining why; the **published** FMCAD
version removes the failure column entirely and cuts experiments to 0.18 pp. Whatever
one concludes from that, it is a real data point about what survives review.

**The abstract convention here differs from genres A and B** — it is
*problem → concede undecidability/intractability → state the reduction → claim a
class, not an instance*, and it closes on a generalization sentence. Emerson & Kahlon:
*"…We reduce model checking for systems of arbitrary size n to model checking for
systems of size up to (of) a small cutoff size c… **The results generalize to systems
comprised of multiple heterogeneous classes of processes.**"* Jaber et al. claim
reusability as model subsumption — *"Our model generalizes many existing models in the
literature"* — and pay for that sentence with 55 references.

### D. Short notes — Information Processing Letters

**Stated limit.** IPL's own description: manuscripts are *"generally limited in length
to nine pages when they appear in print"*, and the journal exists as *"a forum for
timely dissemination of short, concise and focused research contributions."*
(Elsevier's guide-for-authors page returns 403 to every automated fetch we attempted
from two independent directions, so this is quoted from the search index rather than
the publisher page.)

**Actual practice, measured twice from two independent databases.**

| | Crossref (ISSN 0020-0190) | DBLP volume indices, vols 110–150 |
|---|---|---|
| n | 85 with resolvable page ranges | **1,636** |
| **median** | **5** | **5** |
| mean | — | 5.29 |
| Q1 / Q3 | 4 / 6 | 4 / 6 |
| p90 / p95 | — | 7 / 8 |
| range | 2 – 12 | 1 – 14 |
| median references | **8** (n = 83) | — |

Two databases, two extraction methods, overlapping-but-distinct windows, **same
median and matching quartiles**. Treat **median 5, p95 = 8** as settled. The
cumulative distribution is the useful form: **82.3 % of IPL papers are ≤ 6 pages,
98.7 % are ≤ 9 pages, and 0.24 % (4 of 1,636) exceed 12** — all four of those in
soft computing, none in algorithms/combinatorics/complexity.

*Pagination note:* IPL used page ranges through **vol. 150 (2019)** and switched to
article numbers at **vol. 151 (Nov 2019)**, which is why post-2019 items yield no
page counts from metadata.

**Six publisher-typeset exemplars** (exact printed page counts read off the Elsevier
PDF footers, not preprint proxies):

| paper | vol / article | **pp** | sections | refs | appendix |
|---|---|---|---|---|---|
| **Shallit & Vandomme**, *Running maximum of a k-regular sequence* | 194 (2026), 106641 | **3** | **2** | 16 | none |
| Zhang, Quweider, Khan & Lei, *Splitting NP-complete sets infinitely* | 186 (2024), 106472 | 7 | 3 | 12 | none |
| Dillencourt & Goodrich, *Simplified Chernoff bounds with powers-of-two probabilities* | 182 (2023), 106397 | 7 | 4 (+2 sub) | 14 | none |
| Grossi, Iliopoulos, Jansson, Lim, Sung & Zuba, *Finding the cyclic covers of a string* | 191, 106594 | 7 | 4 (+11 sub) | 40 | none |
| van Iersel, Moulton & Murakami, *Polynomial invariants for cactuses* | 182 (2023), 106394 | 8 | 6 | 20 | none |
| ten Cate, Funk, Jung & Lutz, *On the non-efficient PAC learnability of conjunctive queries* | 183 (2024), 106431 | 11 | 7 (+5 sub) | 30 | none |

**Shallit & Vandomme is the sharpest calibration point in this whole document: 3
pages, 2 numbered sections, 16 references, one claim** — a simpler counterexample
replacing an intricate Stern-sequence argument. That is precisely the shape of our
audit's core, and it is what a clean IPL note looks like.

**Appendix convention: there is none.** The string "appendix" occurs **zero times** in
all six publisher PDFs. Combined with 82 % of the corpus being ≤ 6 pages, an IPL note
puts everything in the body or in an external artifact.

*Selection-bias caveat, recorded:* the six-paper exemplar set is drawn from the ~109
gold-OA IPL papers of 2022–2026 and has a median of 7 pages against the corpus median
of 5. **Do not quote the 7.** Read it only as "IPL will accept 8–11 pages in the
current era."

**Tozawa & Sadakane, confirmed.** *Odd-even transposition sort is an optimal stable
standard sorting network*, **Information Processing Letters vol. 195, article 106659**,
DOI `10.1016/j.ipl.2026.106659`, **9 references** [M, Crossref]. **The page count is
not recoverable** — IPL assigns article numbers now, and neither of two independent
attempts obtained the PDF. Two things matter and both are already in
`final-review-external.md` §6: it is a **different quantity** (stable *standard*
networks, not `S(n)`), and it establishes that **IPL is currently publishing
sorting-network size lower bounds**, which makes it a live venue for our correction.

**What this means for Paper 1.** Our correction at 6,000–6,500 words is roughly
**2× the median IPL paper** and above the nine-page ceiling that 98.7 % of the corpus
respects. IPL is reachable only by cutting the repair (§5) to its statement plus the
coverage figure. That is a real option — it lands at ~5,300 words, exactly sub-genre
B's correction-with-repair median — but it costs the strongest positive result in the
package.

---

## 2. The writing conventions, quantified

Measured across the five closest papers (Harder; Codish et al. arXiv + JCSS;
Cruz-Filipe et al. JAR; Bundala & Závodný; Ehlers & Müller).

### 2.1 The abstract

**75–155 words, median ≈ 130 [M].** Harder 129, Codish 154, Bundala 113, Ehlers ~75.
All four state the *number* in the first sentence and the *method* in the last. None
hedges, none previews section structure, none contains a bulleted list.

Harder's, verbatim, as the template:

> "We show that 11-channel sorting networks have at least 35 comparators and that
> 12-channel sorting networks have at least 39 comparators. This positively settles
> the optimality of the corresponding sorting networks given in *The Art of Computer
> Programming* vol. 3 and closes the two smallest open instances of the Bose–Nelson
> sorting problem. We obtain these bounds by generalizing a result of Van Voorhis…
> From this we derive a dynamic programming algorithm… From an execution of this
> algorithm we construct a certificate… which we check using a program formally
> verified using the Isabelle/HOL proof assistant."

Four sentences: **result, significance, mechanism, trust.** That is the whole genre.

Genre B's abstracts are shorter still and state the error in sentence one, 10 of 10.
Genre C's are longer and structurally different — *problem → concede
undecidability/intractability → state the reduction → claim a class, not an instance*,
closing on an explicit generalization sentence. **The three sub-genres want three
different abstracts, which is itself an argument that our five clusters do not belong
under one.**

**Our v2 abstract is 274 words (306 with the title block) — roughly 2× the genre
maximum.** This is the single cheapest and most certain cut in the package.

### 2.2 Contributions lists

**8 of the 9 genre-A papers have no "Contributions" heading, and 0 of 9 has a "Limitations" heading [M]** (grepped for the headings directly; the one exception is Marinov & Gregg). **But genre C splits**: Namjoshi has an explicit §1.1 "Contributions" and Bhat &
Nagar use a numbered 1)2)3) list, while Emerson–Namjoshi, Emerson–Kahlon and Jaber et
al. use prose. So the convention is domain-specific, and it maps cleanly onto our
split: **a correction paper does not get a contributions list; a formal-methods method
paper may.**

In the sorting-network genre it is the opposite
of the current CS-conference default. What Harder does instead is a **roadmap
paragraph** at the end of §1 that names each section in order and embeds exactly one
sentence of self-assessment:

> "…and develop a theory of partial sorting networks and their optimal sizes… Then,
> **as our main contribution to the theory of sorting networks**, we generalize Van
> Voorhis's bound to partial sorting networks."

It costs five lines and does the same work. **Verdict for us:** our §1.2 numbered
ladder (328 words) is a genre departure. It is defensible *only* because our paper
has heterogeneous contribution types (a refutation, a theorem, a computation, a
negative) that a narrative roadmap cannot keep straight. If we split the paper, the
short one should drop the list and use Harder's roadmap paragraph; the method paper
may keep a 3-item list.

### 2.3 How computational results are reported

Two registers, both present, and they are **not** interchangeable.

**(a) The narrative proof** — Harder's §9 / Theorem 61. Prose, with the numbers
inline, closed by one sentence of logic:

> "The computation took 4 hours and 51 minutes with a peak memory usage of 178 GiB…
> The resulting certificate has a storage size of 2926 MiB and contains 12,659,079
> steps… It took 34 minutes with a peak memory usage of 6 GiB and returned
> `Some (11, 35)`, indicating a successful verification. **From the machine checked
> formal correctness proof of the certificate verification routine (Lemma 60) we get
> that s(11) ≥ 35**, matching the known upper bound s(11) ≤ 35."

Numbers first, one logical sentence last. Never the reverse. He quotes exactly one
string of literal tool output in 54 pages.

**(b) The scaling table** — used only for *comparison across configurations or
against prior work*, never for the flagship run. Codish/JCSS has 5 tables [M];
Harder has one timing table (§9) plus the certificate figures.

Neither register uses logs, per-check identifiers, or process narrative. Certificates
and code are **bibliography entries** (Harder cites his Zenodo deposit as reference
[13], inline, at the point of use). **Harder has no "Availability" section.**

### 2.4 The trust story

This is where the genre spends its money and it is the convention we should copy
hardest.

- **Harder: 6 pp (11 %) on formal verification, of which §8.2 *Trusted Base* is a
  9-row, 3-column table (Component | Trusted Base | Notes), 4 Yes / 5 No.** He
  *disclaims* bug-freeness rather than claiming correctness, and scopes the claim to
  the single run: the goal is "to verify a specific single result of a computation.
  Therefore only bugs that are triggered during that verification are relevant."
  He deliberately places his own eleven pages of §5 theory **outside** the trusted
  base — they could be wrong without the number moving.
- **Codish et al.: ~1.5 pp (10 %)**, and their move is to **concede the shared
  dependency before claiming independence**: "While it is reassuring to have two
  alternative proofs, they both share the computation of R¹⁴₉ … there is always the
  potential for errors in computer programs." Their conclusion then claims "four
  validations… beyond any reasonable doubt."
- **JAR: 63 % of the paper is the trust argument**, because there the formalization
  *is* the contribution.

**None of the nine genre-A papers has a "Limitations" section [M], and none of the ten in genre B does either.** The trusted-base table is where a
limitation goes in this genre. Our v2 has §9 (436 w) + §10 (732 w) = 1,168 w ≈ 2.1 pp
≈ 14 %, which is in-band by total — but §10 is a *list of limitations*, which is a
software-engineering convention, not this one. Fold it into a trusted-base table.

### 2.5 Negative results

**Essentially zero space [M].** Ehlers & Müller: none. Codish et al.: none. Bundala
& Závodný: none. Harder: an 8-line "Future Work" that names two things he could not
make work ("Currently, I do not consider this approach to be practical"). The JAR
paper is the only one that reports a failure at length, and it does so because the
failure *is* the result (the naive extracted checker was infeasible; the
preprocessing improved it "by several orders of magnitude" — that comparison is in
the abstract).

**Genre C is the exception, and it is decisive for us.** All eight cutoff papers
report where the method fails, at **0.8–1.4 pp**, and Emerson & Namjoshi *grew* their
undecidability §6 by 72 % (0.83 → 1.43 pp) going from POPL to the journal version.
KKW reports failures inside its results tables (a `mem-out` row; 54 of 852 programs
timing out).

**The rule the whole sample supports:** a negative result earns space when it is *the*
claim, when it is *the* reason the positive claim is believable, or when it
**delimits a reusable method**. It never earns space as a project status report. Our
level-7 and decomposition results qualify under the third clause — but only inside
Paper 2, attached to the collapse theorem, never inside the correction.

### 2.6 Related work

**No separate related-work section in 4 of 5 [M].** Harder weaves it through §1
(~1.5 pp), naming every predecessor result with its value and citation. The JAR paper
is the exception: an explicit "§2 Background and related work" at **1 pp of 30 (3 %)**.
Genre C independently confirms the band: **median 0.99 pp, range 0–1.16 pp, 4–7 % of
the paper, stable across 28 years and every venue format**. KKW's device is worth
copying exactly — three labelled buckets (*"Cutoffs:"*, *"Petri nets:"*, *"Tools:"*)
opened by an explicit primacy claim.

**Budget: 0.5–1.5 pp, and prefer woven-into-intro.**

### 2.7 Appendices vs external artifact

Harder's rule, which we have already adopted in `STYLE.md` and should keep:
*anything a reader must audit to believe the result stays in the paper; anything they
would only re-run goes to the deposit.* In practice he keeps the full inference system
and the Isabelle problem statement in the body, puts **7 pp of parallel pseudocode**
in Appendix A (13 % of the paper), and exports the Rust, the proofs, the certificate
format and the 2.9 GB certificate.

**Genre D has no appendix at all**: the string "appendix" occurs zero times in six
publisher-typeset IPL PDFs. At 5 pages there is nowhere to put one.

**Genre C sharpens this into a rule about journal versions.** Emerson & Namjoshi's
POPL'95 → IJFCS'03 expansion is 10 → 24 pp, of which **5.0 pp is a proof appendix**
while the method section grows only 5.07 → 5.36 pp. **Journal expansion buys proofs,
not method.** So if either of our papers later gets an extended version, the extra
pages are the deferred proofs and the Isabelle listings — not more exposition.

### 2.8 References

**12, 15, 29, 33, 53 [M]** — median **29** in genre A. Genre B pure corrections:
median **4**. Genre D (IPL): median **8** across the corpus, 12–40 in the
publisher-typeset exemplars. The conference/preprint versions run 12–15;
the journal versions run 29–53. A journal-length paper here is expected to carry
**~30+ references**. Our v2 reference list is 409 words, which at this genre's
formatting is roughly 30 entries — in-band.

---

## 3. Our material, priced against the sample

### 3.1 Where v2 actually is

`docs/paper/audit-paper-v2.md`: **8,314 words [M]**. It renders at **13 pp** in our
current LaTeX [M] — but that is **640 words/page**, denser than every single-column
paper in the sample. At the genre's own density it is **≈ 15 pp**. Reference list:
**19 entries [M]**, below the journal median of 29–33. Abstract: **306 words
including the title block, 274 for the abstract paragraph alone [M]** — against a
genre band of 75–155.

Current allocation, in words and in genre-pages:

| cluster | v2 sections | words | pp @ 555 w/pp | share |
|---|---|---|---|---|
| title + abstract | — | 306 | 0.6 | 4 % |
| introduction (incl. contributions ladder) | §1.1–1.3 | 768 | 1.4 | 9 % |
| preliminaries | §2 | 385 | 0.7 | 5 % |
| **(1) audit + the record** | §3 + §4 | 1,615 | 2.9 | 20 % |
| **(2) partial repair** | §5 | 1,264 | 2.3 | 16 % |
| **(3) collapse theorem** | §6 | 830 | 1.5 | 10 % |
| **(4) certified S(11)** | §7 | 484 | 0.9 | 6 % |
| **(5) priced negatives** | §8 | 867 | 1.6 | 11 % |
| trust | §9 | 436 | 0.8 | 5 % |
| limitations | §10 | 732 | 1.3 | 9 % |
| references | — | 409 | 0.7 | 5 % |
| **total** | | **8,096** | **14.7** | |

### 3.2 What v2 does *not* yet contain — every item would add, not subtract

This is the part of the calibration that cannot be dodged. Five results postdate the
draft, and four of them are among the strongest things in the package:

| missing from v2 | source | cost to add |
|---|---|---|
| the **twenty-entry** table (`N = 13…32`), the first written derivation of Dobbelaere's published lower bounds, and the three-way public inconsistency it adjudicates | `docs/novel-facts.md` §4.2 | ~450 w (its own estimate: "one paragraph and one table") |
| the collapse theorem is now **machine-checked in Isabelle** — both parts, level agreement, growth law, no `sorry`, 1,095 lines. v2 claims only "machine-checked foundations (Lemmas 10, 11)" | `docs/mechanized-collapse.md` | ~350 w |
| the growth law is **affine, not polynomial**, in the sorting-network case; plus three corrections the mechanization forced (Part I needs H3; H4 ill-formed as printed; H5 belongs at the small ambient) | `docs/mechanized-collapse.md` §3, §5.1 | ~300 w |
| the **second-domain generalization** (Boolean chains as positive control; prefix-reversal as the real test; every pre-registered prediction reproduced key-for-key) | `docs/level-law-general.md` | 1,200–2,000 w if it is a contribution at all |
| **v2 §8 quotes a retracted bracket.** It says level 7 is "2.4–195 TB beyond reach". The measured position is a **~17× combined gap** (≈45–190 d wall, ≈1.5 TB) at the best known operating point, C910 | `docs/level7-redecision.md` | net ~0 (a replacement), but it changes the claim from *impossible* to *17× short*, which is a different sentence |
| the **decomposition negative** — 146 runs, best peak per-job memory 0.990× against a required 0.095× | `docs/decomposition-economics.md` | 250–600 w |

**So the honest baseline is not 8,300 words. It is ~10,000–11,000 words of material
that has a claim to being in a paper, and it is spread across five clusters that do
not share a thesis.** That is the real problem, and length is only its symptom.

### 3.3 The five clusters, weighed honestly

**(1) The audit + the twenty-entry finding.** Unconditional, machine-checked,
prior-art-clean as of 2026-08-22, and it adjudicates a live disagreement between the
two most-consulted public tables. It is the only cluster with a *deadline* — the
external review rates "claim drift" MEDIUM, since Dobbelaere's row is uncited and a
third party could write it up first. **This is the paper.** Everything else in the
package is either supporting or a different paper.

**(2) The partial repair theorems.** Genuinely proved (Theorems 6′, 6″, 7, 8;
Lemmas W1–W3), and the coverage picture — provable at the pass-through-poor end and
again at the rich end, open strictly in between — is the most useful single figure the
repair produced. But `novel-facts.md` §4.1 states it plainly: **the repair theorems
give no new numerical bound at any n.** Coverage is 22.4 % structural; 49.6 % of the
census has no proof by any route. This is a real result of modest size: *the first
correct proof of any case of the 1972 theorem*, plus a localization of the open
problem.

**(3) The machine-checked collapse theorem and its generalization.** The strongest
*technical* artifact in the package (Isabelle2020, no `sorry`/`oops`/`axiomatization`,
two non-vacuous interpretations). But its own documents impose five concessions that
a calibration must price in:

- Kaiser–Kroening–Wahl (CAV 2010) Def. 4 **already** gives a cutoff over a set of
  reachable states; `level-law-general.md` §2.1 records the earlier novelty claim as
  **FALSE and to be weakened**. What survives: *a-priori* rather than dynamically
  detected, a combinatorial-optimality search rather than concurrent programs, and the
  census growth law, which has no precedent.
- The external review (§3.2a) holds that **Corollary A1 is near-tautological in
  Harder's own formalism** and must be framed as an implementation audit.
- `mechanized-collapse.md` §4.2 concedes that the formalized class "does not literally
  model the engine — **a real gap**", and §4.1 that the sorting-network search being an
  instance is **not mechanized**.
- Part II does **not** generalize to either new domain.
- The Boolean-chain domain was re-graded from "decisive experiment" to **positive
  control**, because its cutoff *is* the folklore support bound.

Net: a genuine, defensible, well-verified *method* contribution — and one that reads
as a footnote when compressed into 830 words inside a paper about a 1972 error.

**(4) The independently certified `S(11) = 35`.** A **reproduction of a known value**,
not a new bound. Its credential is real — our own rebuilt engine's certificate is
accepted by an *unmodified* extraction of Harder's verified checker — and so is the
14.6× search-memory reduction (191 GB → 13.08 GB). But the honest statement, per the
external review §5.2, is a **memory/time trade**: 14.6× less search memory bought with
14.6× more wall time on weaker hardware, end-to-end peak improving only ~1.5×, and
gen-proof now the binding constraint. In genre terms this is exactly Harder's §9: a
**2-page narrative-proof** result.

**(5) The priced negatives.** Both are clean and well-measured — level 7 is NO-GO at a
~17× combined gap; prefix decomposition FAILS across 146 runs and moves both axes the
wrong way. Genre A pays nothing for them. **Genre C pays 0.8–1.4 pp — but only for a negative
that delimits a reusable method**, which is what Emerson & Namjoshi's §6 does and what
KKW's `mem-out` row does. Rewritten in that register — *this is how far the collapse
theorem's practical reach extends, and here is the measured wall* — they earn ~700
words inside Paper 2. Written as they currently stand, as a project go/no-go and a
failed engineering lever, they earn nothing anywhere. **13,600 internal words, ~700 of
which reach print.**

---

## 4. The recommended budget

### 4.1 What the sample says a claim of each weight is worth

Matching each of our clusters to the closest measured precedent:

| our cluster | closest precedent in the sample | what the precedent spends | our honest allocation |
|---|---|---|---|
| **(1) audit + twenty entries** | Elkin & Kurlin (9 pp, 38 refs — counterexample *plus* an audit of the downstream literature that inherited the gap) | ~5.5 of 9 pp on the counterexamples, 2 pp intro/prior work | **4–5 pp** |
| **(2) partial repair** | Willard (12 pp; §3 patch + §4 defeat = 4 of 12 pp); Sadhu et al. (9 pp, repair is most of it) | 2–4 pp when the repair is partial | **2–2.5 pp** |
| **(3) machine-checked collapse theorem + generalization** | Cruz-Filipe & Schneider-Kamp ITP 2015 (16 pp / 7,300 w for one certified checker); Harder §3.2, the generalized Van Voorhis bound, **3 pp of 54** | a mechanized theorem is worth 3 pp *as a section*, 15 pp *as a paper* | **3 pp as a section, or ~8 pp as the spine of its own paper** |
| **(4) certified S(11) = 35** | Harder §9 (**2 pp of 54** for the flagship computation, narrative-proof register) | 2 pp | **1.5–2 pp** |
| **(5) priced negatives** | genre A: Harder's Future Work **8 lines**, Ehlers/Bundala/Codish **zero**. Genre C: Emerson & Namjoshi §6 Undecidability, **0.83 pp → 1.43 pp** in the journal version | 0 in genre A; 0.8–1.4 pp in genre C | **1.3 pp in Paper 2 only, written as a method boundary; 0 in Paper 1** |

Two of those rows are the whole argument. **Cluster (1) is worth 4–5 pp and currently
gets 2.9. Cluster (5) is worth 0 pp in a correction paper and currently gets 1.6.**
The draft is not uniformly over-written — it is misallocated, and its best result is
the one being starved by its weakest.

Note also what row (3) says: the same theorem is worth **3 pp as a section and ~15 pp
as a paper**, and there is no useful value in between. A machine-checked cutoff theorem
either gets the 37–63 % of a paper that genre C gives a method claim, or it gets a
three-page section. Our current 1.5 pp is below both.

### 4.2 One paper or two — the verdict

**Two.** The evidence, not the preference:

1. **Sub-genre B caps a correction-plus-repair at ~10 pp / ~5,300 words (median of
   3), and only lets you past that for a downstream-literature audit (Elkin & Kurlin,
   9 pp) or a repair (Willard, 12 pp).** We are both, which earns the top of the band
   — **11–12 pp** — and our audit cluster alone fills it. Clusters (3)–(5) have no
   room inside that envelope.
2. **Compressed into one paper, clusters (3), (4) and (5) get 1.5, 0.9 and 1.6 pages.
   In this genre that is a remark, not a contribution.** A machine-checked Isabelle
   theorem presented in 830 words will be read as an aside — and it is currently the
   strongest technical artifact in the package.
3. **The abstract cannot carry five claims.** The genre band is 75–155 words and every
   abstract in the sample states one result, its significance, its mechanism and its
   trust story. Ours is **274 words** and promises five things. That is a structural
   symptom of the wrong number of papers, not a writing defect.
4. **Only one half has a deadline.** The external review rates claim drift on
   `S(13) ≥ 44` as MEDIUM: Dobbelaere's row is uncited and a third party could write
   it up first. The correction should go out now; the method paper does not decay.
5. **The three sub-genres want three different abstracts.** Genre A: result →
   significance → mechanism → trust. Genre B: the error, in sentence one, target named.
   Genre C: problem → concede intractability → state the reduction → claim a class,
   closing on a generalization sentence. No single abstract can be all three, and ours
   is currently trying.
6. **Disjoint referee populations.** The audit is read by cs.DS/combinatorics; the
   collapse theorem is read by formal methods, who will want the cutoff literature
   cited and will judge the mechanization by ITP standards. No single referee pool
   is competent to evaluate both halves, and a paper that asks them to will be judged
   on its weakest half.

**And the blunt part.** The split makes the *total* longer, not shorter — roughly
6,500 + 8,500 = 15,000 words against today's 8,300 — and that is the correct
direction only because §3.2 shows the package genuinely contains ~10,000–11,000 words
of unwritten material, not because the writing should expand. Three things must
shrink regardless of the split, and they should shrink today:

- **The abstract, from 274 words to ~140.** Non-negotiable; it is outside the genre
  band by a factor of two.
- **§10 Limitations, 732 words, deleted as a section.** No paper in the sample has
  one. Its content becomes rows in a Harder-style trusted-base table in §9.
- **§8's priced negatives: out of the correction entirely, and ~700 words in the
  method paper.** The 13,600 words in `level7-redecision.md` and
  `decomposition-economics.md` are a research-programme record; genre C pays 0.8–1.4 pp
  for a negative that *delimits a method*, and nothing at all for one that reports
  project status. So about 700 of those 13,600 words reach print, and only when
  attached to the collapse theorem. **That is the place where the honest answer is
  that our material supports far fewer pages than we have written.**

### 4.3 Paper 1 — the correction. **Target 6,000–6,500 words / 11–12 pp**

Sits at the top of sub-genre B's correction-with-repair band (median 10 pp / 5,287 w)
and just below genre A's median (7,472 w) — which is right: our result is worth less
than "we determined S(9)", and more than a three-page note.

| section | words | pp | note |
|---|---|---|---|
| Abstract | **140** | 0.25 | error in sentence one; Willard/Heisel–Lauritzen register |
| 1 Introduction | 900 | 1.6 | the two tables in circulation by p. 2; Neeman's motive sentence ("many people have used this"); Harder's roadmap paragraph **instead of** a contributions list; one artifact paragraph |
| 2 Preliminaries | 400 | 0.7 | only the vocabulary §3–§5 actually use |
| 3 The audit | 1,400 | 2.5 | chain, the 3-comparator counterexample, prevalence (61.0 %), the strongest defence refuted, misstatement vs gap |
| 4 The record **and the twenty entries** | **1,000** | 1.8 | grows from 559 w; absorbs `novel-facts.md` §4.2 — the `N = 13…32` table, the first written derivation of Dobbelaere's column, the Wikipedia/Dobbelaere/OEIS three-way inconsistency, and which column is defensible |
| 5 The partial repair | 1,300 | 2.3 | Theorems 6′/6″/7/8, the identity, and the coverage picture (22.4 % structural, 49.6 % uncovered, the open zone is intermediate) |
| 6 What we trust | 700 | 1.3 | Harder-style trusted-base table; **absorbs today's §10** |
| 7 The status of `S(13)` | 300 | 0.5 | one paragraph; the computational route is priced in Paper 2 and cited out |
| References (~30) | 450 | 0.8 | up from 19 — Elkin–Kurlin's 38 is the precedent for a downstream audit |
| **total** | **6,590** | **11.8** | |

**Cut entirely from Paper 1:** the collapse theorem, the level-7 pricing, the
decomposition negative. **Kept as one 150-word remark:** that the whole table bottoms
out on `S(11) = 35`, which we independently re-certified — cited to Paper 2.

**Venue note.** IPL's stated limit is **nine printed pages**, and its *measured* median is
**5 pages** with 8 references, cross-validated across Crossref and DBLP (n = 1,636),
with **98.7 % of the corpus at or under 9 pp** — so this budget is ~2× the median IPL
paper and outside the envelope 98.7 % of its authors respect. If IPL is the target for speed, §5 must be cut to its
statement plus the coverage figure (~600 w), landing at **~5,300 w**, exactly sub-genre
B's correction-with-repair median. That is a real option and it costs the strongest
positive result in the package. Otherwise the 11–12 pp version goes to a standalone
venue, for which sub-genre B shows ample precedent — Invent. Math., Proc. AMS, ECP and
IEEE TopoInVis all published standalone corrections. **The 11–12 pp version is the
better paper; IPL is the faster one.**

### 4.4 Paper 2 — the method paper. **Target 8,000–8,700 words / 15–16 pp**

Two independent comparators agree on this number. Cruz-Filipe & Schneider-Kamp,
ITP 2015: **16 pp / 7,300 words** for one certified checker. And genre C's **LNCS
cutoff-paper mode is exactly 15 pp** (CAV 2010 and VMCAI 2007 both). A 15–16 pp method
paper is the centre of this distribution, not its tail.

| section | words | pp | note |
|---|---|---|---|
| Abstract | 140 | 0.25 | |
| 1 Introduction | 950 | 1.7 | cutoff literature woven in, not a separate section; **KKW CAV 2010 Def. 4 cited as closest prior art and distinguished on three points** |
| 2 The abstract class, H0–H5 | 1,050 | 1.9 | including H4 (width convexity), the hypothesis that was invisible in the sorting-network statement |
| 3 The theorem + the growth law | 1,200 | 2.2 | Parts I and II, level agreement; **affine, not polynomial**, in the T-trivial case |
| 4 The mechanization | 1,300 | 2.3 | the locale, both interpretations, the **three corrections the mechanization forced**, and an explicit statement of what is *not* mechanized |
| 5 The sorting-network instance | 700 | 1.3 | framed as an **implementation audit** per the external review, incl. the one leak |
| 6 Second domains | 800 | 1.4 | Boolean chains as a **positive control** (its cutoff is the folklore support bound — say so), prefix reversal as the real test |
| 7 The certified `S(11) = 35` | 800 | 1.4 | Harder's narrative-proof register; memory/time on all three axes, **14.6× search-stage, ~1.5× end-to-end, gen-proof now binding** |
| 8 The scaling boundary | **700** | **1.3** | level 7 at ~17× combined; decomposition fails across 146 runs. Written as Emerson & Namjoshi's §6, not as a status report — genre C pays 0.8–1.4 pp for exactly this |
| 9 Trusted base | 600 | 1.1 | |
| 10 Conclusion | 250 | 0.45 | Codish-length: one paragraph |
| References (~35) | 500 | 0.9 | |
| **total** | **8,990** | **16.2** | trim §6 to land at 8,300–8,700; **15–16 pp is the LNCS cutoff-paper mode measured in genre C**, so this is on target rather than over |

**Fallback, and it should be decided before drafting.** If the concessions in
`level-law-general.md` §2.1 and `mechanized-collapse.md` §4.2 are judged too heavy to
headline — KKW already has a set-of-reachable-states cutoff; the formalized class
"does not literally model the engine"; Part II does not generalize; the Boolean domain
is folklore — then Paper 2 has no theorem to lead with. In that case it becomes a
**6–8 pp / 3,500–4,500 word experimental note** (ACM JEA register) on the certified
`S(11)` and the memory/time trade, with the collapse theorem as a 2 pp section and the
negatives as 1 pp. **Do not write the 16 pp version until that call is made** — the
difference between the two is entirely a judgement about how much of the novelty
survives §2.1's own retraction.

### 4.5 Line-item edits the measurements demand, independent of the split

| edit | from | to | why, in one measured fact |
|---|---|---|---|
| Abstract | 274 w | **~140 w** | genre band is 75–155 (Harder 129, Codish 154, Bundala 113) |
| §1.2 Contributions ladder | 328 w numbered list | roadmap paragraph (Paper 1) / 3-item list (Paper 2) | **8 of 9 genre-A** and **10 of 10 genre-B** papers have no contributions heading |
| §10 Limitations | 732 w section | rows in the §9 trusted-base table | **0 of 9 genre-A papers** has a Limitations heading [M]; Harder's §8.2 table is where a limitation goes |
| §8 priced negatives | 867 w | **~700 w, and only in Paper 2** | genre A pays ~0 (Harder's Future Work is 8 lines); genre C pays 0.8–1.4 pp *if* the negative delimits the method — E&N grew their undecidability §6 by 72 % for the journal version |
| §9's closing methodology paragraph (LLM agent protocol) | ~90 w | **1 sentence** | `STYLE.md`'s own rule, and the sample carries no process narrative at all |
| §4 The record | 559 w | **~1,000 w** | the twenty-entry table is the largest single upgrade available and is currently absent |
| References | 19 | **~30** | journal versions in the sample run 29–53; Elkin & Kurlin carry 38 for exactly our kind of downstream audit |
| §7 certified `S(11)` | "13.6× less" | **"14.6× (search stage); ~1.5× end-to-end; gen-proof now binding; 14.6× slower wall"** | external review §5.2: the current figure mixes GiB with GB and quotes a stage-scoped ratio as end-to-end |
| §8's "2.4–195 TB beyond reach" | retracted bracket | **~17× combined at C910 (≈45–190 d, ≈1.5 TB)** | `level7-redecision.md` §0 |

---

## 5. What in this calibration is unverified

Recorded so the numbers above can be trusted differentially.

- **Verified by direct measurement [M]:** every genre-A page count and word count
  (PDFs downloaded, `pdfinfo` + `pdftotext`); Harder's 54 pp and its section map;
  the JAR (31 pp / 17,151 w) and JCSS (17 pp / 11,161 w) figures; the abstract word
  counts; the contributions/limitations heading grep across all nine genre-A papers;
  the genre-C page counts for KKW, Namjoshi, Emerson–Namjoshi (three versions),
  Jaber et al.; the IPL distribution (Crossref n = 85 in this session, cross-validated against an
  independent DBLP extraction of vols 110–150, n = 1,636 — both median 5, matching
  quartiles 4/6);
  the Tozawa–Sadakane citation and its 9 references; and all of our own word counts.
- **Verified by publisher page range, not by PDF:** ICTAI 2014 (pp. 186–193), JCSS
  82(3):551–563, JAR 59:425–454, and the genre-C conference page ranges.
- **Not verified:** Emerson & Kahlon (CADE-17) internal structure — Springer blocks
  the full text and no author copy survives; the page range (236–254) is
  double-verified but the section split is unmeasured. The Emerson & Namjoshi POPL'95
  section proportions come from a 19-page *extended* preprint, not the 10-page
  camera-ready; the IJFCS 2003 row is the trustworthy long-form data point. OCR-derived
  reference counts for the 1995/1998/2003 scans may be off by 1–2. Publication status
  for three genre-B items (Heisel–Lauritzen, Holmgren–Wein, Willard) is "no
  `journal_ref` in arXiv metadata at query time", which is not proof they were never
  published. Tozawa & Sadakane's page count is not recoverable — IPL assigns article
  numbers from vol. 151 (Nov 2019), and two independent attempts failed to obtain the
  PDF. IPL's nine-page limit is quoted from the search index, not the publisher page:
  Elsevier returned 403 to every automated fetch from two independent directions. The
  six IPL exemplars are drawn from the gold-OA subset and have a median of 7 pages
  against the corpus median of 5 — **selection bias, not a finding; do not quote the
  7.** Neither of us measured appendix frequency corpus-wide; the zero-appendix result
  is a six-paper sample.
- **Genre-B word counts** are `pdftotext` extractions of the full PDF including
  headers and bibliography — measured, but not body-only, so they run slightly high.
- **Density conversion.** The 555 words/page figure used throughout is the mean of the
  single-column papers in genre A (Harder body 558, Bundala 555, Codish 558, JAR 553).
  It does not apply to two-column formats, where the sample ranges to 934 w/pp.
