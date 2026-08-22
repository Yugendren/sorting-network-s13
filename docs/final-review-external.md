# Final External Prior-Art Review — S(13) Publication Package

**Date:** 2026-08-22.
**Role:** last external novelty check before submission. Read-only; no commits, no
code changed.
**Documents reviewed:** `docs/van-voorhis-theory-report.md`,
`docs/kraft-dispute-verdict.md`, `docs/ambient-reduction.md`,
`docs/paper/audit-paper-draft.md`, `evidence/v3/n11-certified/report.md`.

**Method / tooling caveat (read this).** The session's `WebSearch` quota was
already exhausted when this review began, so *no* general-web keyword search was
possible. All searching below was done with tools that were reachable:
**Google Scholar** (server-rendered HTML, worked), **OpenAlex API** (citation
graphs), **arXiv search UI** (title + full-text search), **GitHub search via
`gh`** (repos, code, forks, issues, users), **DBLP/Semantic Scholar** (rate
limited — unavailable), and **direct fetches** of Dobbelaere's table, Wikipedia,
bitsavers, Stanford SearchWorks and the Harder PDF. Bing, DuckDuckGo, Ecosia,
Startpage and searx were all captcha-walled or geo-broken through `curl`, so the
**non-academic web (blogs, forums, Hacker News, Mastodon, Reddit) was NOT swept
this round.** That is the single largest residual hole in this review; §7 says
what to do about it.

---

## 0. Verdict table

| # | Claim | Verdict as of 2026-08-22 |
|---|---|---|
| 1a | The van Voorhis (1972 Plenum chapter) eqs (5)/(6) are invalid; no erratum exists | **NOVEL** — no erratum, correction, gap-note, blog post or reproof found; citation graph re-checked today, two new citing works since 2024, neither engages |
| 1b | The IEEE TC 1972 note contains only the one-value bound | **CONFIRMED indirectly, still UNCERTAIN on the primary source** — Knuth, Parberry (1989) and Harder (2020) all read the TC note and all report only `S(n) ≥ S(n−1) + ⌈log₂ n⌉`. Full text still not obtained (paywalled) |
| 1c | The 1971 Stanford dissertation is unavailable | **STILL UNAVAILABLE** — Scholar carries it as a bare `[CITATION]`; **not** in the new (Dec-2025) bitsavers Stanford CS-TR scan collection, nor in bitsavers' SEL series, nor surfaced by SearchWorks |
| 2 | No published source proves `P(2,N) ≥ ⌈log₂ F(N)⌉` or `S(13) ≥ 44` | **NOVEL / CONFIRMED** — Dobbelaere's table still shows `44…45` with no citation beyond `[VVoorh72]`; **Wikipedia still shows 43**; no paper anywhere states 44 |
| 3 | Level Law / Chain Collapse (`Reach(n,ℓ) = Reach(n_min(ℓ),ℓ) ⊎ cubes`) | **NOVEL** for sorting networks; **but see §3 for a real framing risk** — Corollary A1 is near-immediate in Harder's own formalism, and the general shape of the result is a *cutoff theorem*, a named concept in parameterized verification that a referee will ask you to cite |
| 4 | Red/blue lead colouring and the escape-free / clean-case theorem | **NOVEL** — no prior colouring argument for sorting-network size lower bounds found in any search |
| 5 | 13.6× memory reduction vs Harder | **NO COMPETING REIMPLEMENTATION EXISTS** (verified today) — but the *claim itself* has an arithmetic/scoping red flag; see §5 |
| 6 | Venue scan | §6 |

**Bottom line: nothing in the package is anticipated. Publish.** The risks that
remain are presentation risks (§5, §7), not priority risks.

---

## 1. The van Voorhis chapter: erratum, the TC note, the dissertation

### 1.1 Erratum / correction / engagement — NOVEL

Re-ran the citation graph today via **OpenAlex** on the chapter
(`W997071912`, *Toward a Lower Bound for Sorting Networks*, 1972): **18 citing
works, complete list retrieved.** Two are new relative to the package's sweep:

| year | citing work | venue | does it engage with eqs (5)–(9)? |
|---|---|---|---|
| 2025 | Vlad, Pascu, Cioata, Raschip, *Identifying Optimal-Size Sorting Networks with Reinforcement Learning* | **ICTAI 2025** (doi 10.1109/ictai66417.2025.00137) | **No.** Q-learning construction; optimal up to n=8, near-optimal 9–10. Cites van Voorhis only for the one-value bound ("subsequent lower bounds for sₙ are derived … based on van Voorhis'") |
| 2024 | Cruz-Filipe & Schneider-Kamp, *Minimizing Sorting Networks at the Sub-Comparator Level* | **LPAR 2024** (EPiC) | **No.** Instruction-level implementation of known networks |

The other 16 are the pre-2018 set the package already lists. **No erratum, no
correction, no gap note, no reproof, no formalisation.** The package's central
negative claim survives a fresh check.

Two more independent checks came back empty:
- **arXiv title search** for `sorting network` (73 hits, all-time) and full-text
  search for `Van Voorhis`: the only size-lower-bound items are Harder
  (2012.04400) and the pre-existing set. The only 2025–26 sorting-network arXiv
  items are Wang's depth paper (2511.04107) and 2603.07579 (QUBO formulations,
  irrelevant).
- **GitHub**: `gh search code "Voorhis sorting"` → 0 hits; `gh search issues
  "Voorhis"` → nothing relevant; no issue on `bertdobbelaere/SorterHunter`
  questioning the lower-bound row.

### 1.2 The IEEE TC 1972 note — triangulated, still not obtained

I could not get the full text (IEEE paywall; no OA copy indexed). But three
independent readers of that note are on record and they agree:

1. **Knuth**, TAOCP v3 answer to ex. 5.3.4–42, cites *only* IEEE TC C-21 (1972)
   612–613 for `S(n) ≥ S(n−1) + ⌈log₂ n⌉`.
2. **Parberry (1989)**: "From Van Voorhis [10], all nine-input sorting networks
   must have at least 23 comparators" — that is exactly `S(8) + ⌈log₂ 9⌉ =
   19 + 4`, the one-value bound.
3. **Harder (2020)**, arXiv:2012.04400v3 — his reference **[26] is the TC note**
   (and *only* the TC note; the Plenum chapter is absent from his bibliography,
   confirming the package's claim). His **Lemma 17** is the one-value bound, and
   he reproduces its proof in full from that source.

**New and directly useful finding.** Harder's rendition of the TC note's
argument contains *the same structural claim the audit attacks*:

> "if we take the union of the pruned paths for all `i` and remove the common
> output `n`, we obtain a binary tree rooted in the comparator gate connected to
> output `n`, where the leaves are all inputs of `c` and all inner vertices are
> comparator gates … the leaf for every input `i` has a depth of `δ(c,i)`."
> — Harder 2020, proof of Lemma 17

That identification of max-path comparators with branch nodes is exactly the
p. 121 premise the audit refutes, and (per the audit's own counterexample `T1`)
it is **literally false whenever pass-throughs exist** — `δ(c,i)` is the literal
comparator count and can exceed the branch-tree depth. **It is harmless here**,
because the one-value bound only needs `max_i δ(c,i) ≥ max_i depth_B(i) ≥
⌈log₂ n⌉` and literal depth dominates branch depth. So:

- This **strengthens** the paper's §10.1 ("how an error survives"): the same
  imprecision was reproduced, unnoticed, in a 2020 paper that is the current
  authority for `S(11)` and `S(12)`, and it survived because in the one-value
  direction the inequality goes the safe way.
- It also **makes it very likely the false identification originates in the TC
  note**, as `kraft-dispute-verdict.md` §7.3 conjectures.
- **Recommendation:** add a short remark to the paper making both points, and
  state explicitly that the one-value bound (hence `S(12) = 39` and hence the
  published `S(13) ≥ 43`) is *unaffected*, with the one-line reason. A referee
  who notices Harder's phrasing on their own will otherwise ask whether your
  audit also breaks `S(12) = 39`. Pre-empt it.
- Related honesty point worth one sentence: Harder's Lemma 17 is a **paper**
  proof; his Isabelle development verifies the certificate checker, not
  van Voorhis's bound. So `S(12) = 39` is not machine-checked either. This is
  consistent with, and sharpens, the package's "there is no machine-checked
  version of the P(2,N) bound".

### 1.3 The 1971 dissertation — still unavailable, and I checked the new place

*Efficient Sorting Networks* (Van Voorhis, Stanford PhD, 1971) appears in Google
Scholar **only as a `[CITATION]` stub** — no indexed full text anywhere.

New this cycle and worth recording: **bitsavers has published a fresh Stanford CS
Technical Report scan collection**,
`http://bitsavers.trailing-edge.com/pdf/stanford/Stanford_CS_TR_Collection_2025-12-12/`
(collection dated 2025-12-12, mirrored 2026-01-26). It contains CS-TR-71-238
(the divide-sort-merge TR you already have). I sampled the whole 1971 and 1972
short-report set (20 PDFs, cover pages extracted) and **no Van Voorhis item other
than 71-238 is present**. bitsavers' separate `sel_techReports/` (Stanford
Electronics Labs) directory does not contain it either. Stanford SearchWorks is
bot-walled to `curl`/WebFetch and could not be queried.

**Verdict: UNCERTAIN, unchanged.** Two archival gaps remain open exactly as the
package states — the TC note full text and the dissertation. Both are correctly
disclosed in the paper's limitations. **Do not let either block submission**; the
paper's claim is about *the published record*, and the published record is now
re-verified as of today. But note the new bitsavers collection is a live, growing
resource: it is worth one re-check at proof stage.

---

## 2. The two-value bound's status in the wild — CONFIRMED, and re-checked today

### 2.1 Dobbelaere's table — unchanged, still uncited

Fetched `https://bertdobbelaere.github.io/sorting_networks.html` and the raw
source from `bertdobbelaere/SorterHunter` today. The n=13 size row reads:

```
| 13 | (45, 10) (46, 9) | 44…45 | depth 9 | [TAOCPv3], Optimal depth proven in [BZ14] |
```

- The **only** reference attached to n=13 is for the *depth* result. The size
  lower bound 44 carries **no citation at all** in the table row.
- The changelog still reads, verbatim: `2025-04-21  Tighter lower bounds for
  size, on suggestion of Jelmer Firet and based on principles in [VVoorh72].`
- `git log` on `sorting_networks.html` shows the last touch was **2025-11-07**
  ("Improved depth upper bound for 27 and 28 inputs, based on networks from
  [Wang25]"). The lower-bound row has not moved since 2025-04-21.
- **No caveat or confidence qualifier anywhere on the page.**

### 2.2 Wikipedia — still 43

`en.wikipedia.org/wiki/Sorting_network`, last edited 2026-08-15 (bot/citation
cleanup only; last substantive edit 2025-11-14, depth bounds for 27–28). The
size-lower-bound row still carries **43** for n=13, with the footnote *"Obtained
by Van Voorhis lemma and the value S(11) = 35"*. **The 44 has not propagated to
Wikipedia.** The package's framing ("43 published, 44 web-table only") is exactly
right as of today.

### 2.3 Jelmer Firet — no publication, confirmed

Scholar's only hit for the name is a 2022 **Radboud University bachelor's
thesis** on Acyclic Push-Relabel (`cs.ru.nl/bachelors-theses/2022/Jelmer_Firet_…`)
— unrelated. GitHub user search and code search turn up nothing on sorting
networks. **No preprint, no note, no repo.** The provenance claim stands.

### 2.4 Nobody else claims 44

Scholar sweeps for 2024+ and 2025+ on `sorting network size lower bound
comparators`, `13 inputs 44 comparators`, and `"Van Voorhis" sorting networks
bound` return: Wang's depth paper, Vlad et al. (ICTAI 2025, RL, upper bounds),
Burca & Raschip (ICAART 2026, deep Q-learning, upper bounds), Tozawa & Sadakane
(IPL 2026, *stable* sorting network lower bounds — a different quantity),
Papaphilippou (Chips 2026, FPGA verification), and Sergeev's lecture notes
*Complexity of sorting and selection* (v1.1e, 2025-03-05 — downloaded and
grepped: **zero occurrences of "Voorhis", no S(13), no two-value bound**).

**Verdict: NOVEL-as-of-today.** No published source claims a valid proof of
`P(2,N) ≥ ⌈log₂ F(N)⌉` or of `S(13) ≥ 44`.

---

## 3. Level Law / Chain Collapse — NOVEL, with a framing risk

### 3.1 No prior art in sorting networks

Searched Scholar for `reachable state set independent of instance size dynamic
programming branch and bound identical subproblems`, `search space identical
across instance sizes memoization transfer`, and full-text arXiv for sorting
networks. **Nothing resembling `Reach(n,ℓ) = Reach(n_min(ℓ),ℓ) ⊎ {cube_w}` exists
in the sorting-network literature.** Harder's paper — the only place the relevant
DP is described — contains no census claim, no `D(n) = S(n) − C(n)` level
structure, no `n_min`, and no statement about the explored set across ambients.
No hits for `sortnetopt` improvements or reimplementations of any kind (§5).

Nothing in the general B&B/DP literature matches either. The closest generic
hits — Buresh-Oppenheim/Davis *A stronger model of dynamic programming
algorithms* (Algorithmica 2010), and the DD-based B&B-with-caching line
(Coppé/Gillard/Schaus, INFORMS JoC 2024) — are about *models* of DP and about
dominance caching, not about an instance-size invariance of the reachable set.

**Verdict: NOVEL. Your flagship theorem is not anticipated.**

### 3.2 Two framing risks a referee will raise — fix these before submission

**(a) Corollary A1 is nearly a tautology in Harder's own formalism, and you
should say so first.** Harder defines the objective as `s(X)` for a *sequence
set* `X ⊆ B` — with the ambient appearing nowhere in the definition — and proves
permutation/complement invariance (his Lemmas 4–6, Cor. 6). Under that
definition, "bounds on `X` are valid at any ambient `n ≥ w(X)`" follows
immediately from the definition, not from an audit of `search.rs`. Your Theorem A
is genuinely an *implementation* result ("the engine actually respects this, and
here is the one place it does not — `SUBSUME_WIDTHS`, §5.3"), which is valuable
and correct, but it is **not** a mathematical novelty and must not be presented as
one. Frame A/A1 as *"the semantic statement is immediate from Harder's
definition; what is new is (i) the exhaustive audit showing the implementation
matches it, (ii) the identification of the sole leak, and (iii) Theorem E, which
does not follow from the definition."*

**(b) Cite the parameterized-verification "cutoff" literature as related work.**
Theorem E is, structurally, a **cutoff theorem**: for all `n ≥ n_min(ℓ)`, the
behaviour of the size-`n` instance is determined by the size-`n_min` instance.
That is a mature named concept — Emerson & Namjoshi; Kaiser–Kroening–Wahl,
*Dynamic cutoff detection in parameterized concurrent programs* (CAV 2010);
Emerson & Kahlon, *Symmetry and completeness in the analysis of parameterized
systems* (VMCAI 2007, explicitly "the set of reachable states of small instances
up to a cutoff size N₀"); Außerlechner–Jacobs–Khalimov, *Tight cutoffs for
guarded protocols* / *Analyzing guarded protocols* (VMCAI 2016/2018);
Jacobs et al., *Parameterized verification of systems with global synchronization
and guards* (CAV 2020). **None of them is about sorting networks and none
anticipates Theorem E** — but a referee from the formal-methods world will
recognise the shape instantly, and citing it *strengthens* the paper (it says:
this is the first cutoff theorem for a combinatorial-optimality search) rather
than weakening it. Add a two-sentence related-work paragraph. If you submit to
ITP/CPP/CAV this is close to mandatory.

---

## 4. Red/blue lead colourings and the clean-case theorem — NOVEL

Searched Scholar for `sorting networks proof coloring red blue wires maximum path
lower bound` and `sorting network lower bound Kraft inequality prefix-free max
path proof`. Results are entirely off-target: max-colouring of paths, rainbow
colouring, VLSI lower bounds with edge colourings, prefix-free source coding.
**No prior art of any kind** on a two-colouring of leads/wire-segments used to
establish an antichain or a Kraft inequality for sorting-network size bounds.

Related-but-different, and worth *not* confusing with yours:
- Cruz-Filipe & Schneider-Kamp's Coq work and Codish et al.'s "filters"/"end
  game" machinery are about generate-and-prune completeness, not path colourings.
- Harder's `1+max`-Huffman algebra is the closest algebraic neighbour, and your
  own §8.4(d) already records the identity
  `max_plus_1_huffman(b₁..bₘ) = ⌈log₂ Σ 2^{b_i}⌉`. Keep that attribution
  prominent — it is the one place where a reader might think you are restating
  Harder.

**Verdict: NOVEL.** The clean-case theorem (Theorem 6) appears to be, as the
draft claims, the first correct proof of any case of the 1972 two-value theorem.

---

## 5. The 13.6× memory claim — no competitor, but the claim itself needs repair

### 5.1 No competing reimplementation exists (verified today)

- `jix/sortnetopt`: **zero forks**, last commit **2020-12-09**. `jix/sortnetopt-gnp`:
  last touched 2024-07-06, and its README points *to* sortnetopt as the newer
  approach.
- GitHub code search for `sortnetopt` returns only: the two jix repos, a vendored
  reference in `tim-janik/anklang`, Dobbelaere's citation entry, and
  clone-corpus/LLM-registry noise. **No reimplementation, no port, no fork with
  work on it.**
- Scholar 2025+ for `sortnetopt … memory reduction reimplementation`: **zero
  results.**
- Adjacent active repos, none of which touch lower bounds:
  `dzhang314/ComparatorNetworks.jl` (Julia, simulated annealing, active
  2026-04), `vmallela0/sorting-networks` (reachable-set greedy/SA construction,
  2026-05 — note it uses "reachable set" for the 0/1-principle image set, an
  unrelated meaning), `jukofyork/SortingNetworks` (beam search, 2026-02),
  `girving/aks` (Lean formalisation of AKS, 2026-06),
  `jonathanpeppers/SortingNetworks` (.NET impl of Wang's depth-13 networks).

**Verdict: no competing work. Priority is safe.**

### 5.2 RED FLAG — the 13.6× figure is unit-mixed and stage-scoped

Verified Harder's numbers directly from arXiv:2012.04400v3 (§9 and its timing
table):

| stage | Harder 2020 | `evidence/v3/n11-certified` |
|---|---|---|
| search | **178 GiB**, 4 h 51 m | 13.08 GB, 71 h 06 m |
| prune-all | 16 GiB, 2 d 5 h | ~8.4 GB, 9 h 45 m |
| gen-proof | **54 GiB**, 19 h 02 m | **> 37.9 GB**, ~9 h |
| verify | 6 GiB, 34 m | 4.35 GB, 89 m |
| certificate | 2926 MiB | 2329 MiB (2.44 GB) |

Three problems with "13.6× less":

1. **Unit mixing.** 178 **GiB** = 191.1 GB. Against 13.08 **GB** the true ratio
   is **14.6×**, not 13.6×. The 13.6 comes from dividing 178 by 13.08 as if both
   were the same unit. Either state "178 GiB → 12.2 GiB (14.6×)" or normalise
   both to GB. As written it is wrong in your *disfavour*, which is at least the
   safe direction, but a referee who recomputes will lose confidence in the rest.
2. **Stage scoping.** The reduction is a **search-stage** result. The pipeline's
   real peak is **gen-proof**, where you used >37.9 GB against Harder's 54 GiB
   (~58 GB) — a factor of roughly **1.5×**, not 13.6×. `report.md` already
   discloses this honestly in "Incidents", but the headline table does not, and
   the headline is what gets quoted. **Say "13.6× (search stage); end-to-end peak
   memory improves ~1.5×, and gen-proof is now the binding constraint."**
3. **The wall-time counterpart is missing from the headline.** 4 h 51 m → 71 h
   06 m is a **14.6× slowdown** on weaker hardware with a memory-frugal config.
   The honest framing is a *memory/time trade at fixed correctness*, which is a
   perfectly good engineering result — but stating the numerator without the
   denominator is exactly the kind of thing that gets a systems-flavoured paper
   desk-rejected.

None of this affects novelty. It affects credibility, and it is cheap to fix.

---

## 6. Venue scan

Confirmed publication venues of the direct predecessors (via OpenAlex, today):

- Codish, Cruz-Filipe, Frank, Schneider-Kamp, *Twenty-Five Comparators Is
  Optimal…* — **ICTAI 2014** (conference).
- Codish, Cruz-Filipe, Frank, Schneider-Kamp, *Sorting nine inputs requires
  twenty-five comparisons* — **JCSS** 2015/2016.
- Codish, Cruz-Filipe, Schneider-Kamp, *Sorting Networks: The End Game* —
  **LATA 2015** (LNCS).
- Codish, Cruz-Filipe, Ehlers, Müller, Schneider-Kamp, *Sorting networks: to the
  end and back again* — **JCSS 2016**.
- Cruz-Filipe, Larsen, Schneider-Kamp, *Formally Proving Size Optimality of
  Sorting Networks* — **Journal of Automated Reasoning 2017**.
- Cruz-Filipe & Schneider-Kamp, *Minimizing Sorting Networks at the
  Sub-Comparator Level* — **LPAR 2024**.
- Vlad, Pascu, Cioata, Raschip — **ICTAI 2025** (so ICTAI is still live for this
  exact topic).
- Tozawa & Sadakane, *Odd-Even Transposition Sort is an Optimal Stable Standard
  Sorting Network* — **Information Processing Letters 2026** (so IPL is
  currently publishing sorting-network *size lower bounds*).
- Harder — **arXiv only, never published**. Worth knowing: the community
  tolerates that, but it is also why the 44 has no peer-reviewed home.

### Recommended venues

| # | Venue | Type | Fit | Rationale / risk |
|---|---|---|---|---|
| **1** | **Journal of Automated Reasoning (JAR)** | journal | **best overall** | Published the direct predecessor (Cruz-Filipe et al. 2017) on *formally proving size optimality of sorting networks*. Takes: a computational audit with two independent verifier artifacts, a new human theorem (clean case), and an Isabelle-checked certified `n = 11` re-derivation — that is precisely JAR's remit (machine-assisted mathematics + artifact). No page pressure, so the audit, the repair and the certification can travel together. **Recommended primary target.** |
| **2** | **Information Processing Letters (IPL)** | journal (short) | **best for the audit alone** | Currently publishing sorting-network size lower bounds (Tozawa–Sadakane 2026). IPL exists for exactly this: a short, sharp, self-contained note saying *the published proof of eq (8) is invalid, here is a 3-comparator counterexample, here is the clean case proved*. ~8 pages. Fastest route to putting a citable correction into the record — which matters, because the 44 is propagating uncorrected. Strong candidate for a **split**: audit → IPL, Level Law + certification → JAR/ITP. |
| **3** | **ITP** (Interactive Theorem Proving) or **CPP** | conference | strong, if you lead with the Isabelle content | Right home for "unchanged formally-verified checker accepts our independently produced certificate", the certificate-composition/tier scheme, and Theorem E framed as a **cutoff theorem** (the ITP/CPP audience knows cutoffs — §3.2b). Risk: ITP/CPP referees will want *more* formalisation than you have — Theorem 6 and Theorem E are human proofs. Mitigate by formalising Theorem 6 (it is short and elementary) before submitting here, or by being explicit that the formal content is the checker, not the new theorems. |
| **4** | **ICTAI** | conference | good, fast, low-risk | The 2014 predecessor's venue and still active on this exact problem in 2025. Accepts computational/AI-adjacent combinatorial-optimality work, short cycle, gets the result cited quickly. Weaker prestige than JCSS/JAR and page-limited, so it suits *either* the audit *or* the engineering story, not both. |
| **5** | **JCSS** (Journal of Computer and System Sciences) | journal | good, but a stretch on its own | Where the 9/10-channel results landed. JCSS wants a *theorem*, and your headline theorem is a **negative** result plus a partial repair. Realistic if you lead with the Level Law + clean-case theorem and treat the audit as motivation; risky if you lead with "a 1972 proof is broken". Consider after JAR/IPL, or as the venue for a combined journal version. |
| **6** | **Experimental Mathematics** *or* **ACM Journal of Experimental Algorithmics (JEA)** | journal | good fallback / good fit for the compute story | Experimental Mathematics is built for "conjecture with massive computational support and an honest open status" — which is *literally* your §8 (eq (8) survives 1,890 sorters and two exhaustive enumerations; status open). JEA is the right home for the memory/time engineering, the 13.6× (once repaired per §5.2), the tier-slicing scheme and the level-7 feasibility analysis. |

**Also do, regardless of venue (highest value-per-minute in the whole package):**
- **arXiv preprint immediately** (cs.DS, cross-list cs.LO). It timestamps
  priority and it is where this community actually reads.
- **Email Bert Dobbelaere** with the audit. His table is the sole vector for the
  44 and it carries no citation for that cell. A one-line caveat or a footnote
  from him is a real-world outcome the paper can cite, and it is the single
  strongest evidence that the finding *mattered*.
- **Email Jannis Harder** (courtesy + the §1.2 observation about Lemma 17's
  phrasing) and **Jelmer Firet** (he is reachable via Radboud; he may have an
  argument that was never written down — if he does, you need to know *before*
  submission, not after).

---

## 7. Competing-work alerts and residual risks

| severity | item |
|---|---|
| **LOW** | `dzhang314/ComparatorNetworks.jl` — actively developed 2026, Julia, simulated-annealing search for comparator networks. Upper bounds only; README explicitly notes optimal size unknown at 13. Not a threat; cite as adjacent tooling. |
| **LOW** | Burca & Raschip, *Finding Minimal-Size Sorting Networks Using Deep Q-Learning*, **ICAART 2026** — same group as the ICTAI 2025 paper. Construction/upper-bound heuristics. Note this group is publishing steadily on n≈9–13 size; they are the most likely people to trip over the 44. |
| **LOW** | Tozawa & Sadakane, **IPL 2026** — new size lower bound for *stable standard* sorting networks. Different quantity, but it is the only 2026 size-lower-bound paper; check it does not use a van Voorhis-style pruning argument before you claim "nobody engages". (Abstract suggests a redundancy/standard-form argument, not pruning.) |
| **MEDIUM** | **Non-academic web not swept this round** (WebSearch quota exhausted; all general engines captcha-walled). A blog post, Mathstodon/Twitter thread, OEIS comment, MathOverflow answer or Hacker News comment noticing the same gap would not appear in any source I could reach. **Action: re-run a plain web sweep in a fresh session before submitting** — queries: `van Voorhis sorting network proof wrong`, `S(13) 44 sorting network lower bound`, `"P(2,N)" sorting network`, `Jelmer Firet sorting network`, plus a MathOverflow/Mathstodon site sweep. This is the one open item I could not close. |
| **MEDIUM** | **`S(13) ≥ 44` claim drift.** Dobbelaere's row is `44…45` with *no citation*. If a third party writes it up first — most plausibly Firet, or the Raschip group — your framing ("never peer-reviewed") expires. This argues for the IPL short note in parallel with the big paper, and for arXiv **now**. |
| **LOW** | **Wikipedia divergence.** Wikipedia says 43, Dobbelaere says 44. Your paper's §6 table already captures this and it is still accurate today — but it is a moving target; re-verify at proof stage. |

### Accuracy corrections to fold into the package

1. **`evidence/v3/n11-certified/report.md`** — fix the 13.6× per §5.2 (unit
   mixing → 14.6× if normalised; scope it to the search stage; state the
   gen-proof peak and the wall-time trade in the same table).
2. **`docs/paper/audit-paper-draft.md` §6.4** — "Harder (2020) … does not cite the
   chapter" is **correct and verified** (his [26] is the TC note only). But add
   the §1.2 observation: Harder *does* reproduce the same max-path-tree
   identification, harmlessly, and the one-value bound is unaffected. This
   pre-empts the obvious referee question.
3. **`docs/ambient-reduction.md` §3.1** — reframe Theorem A / Corollary A1 as an
   implementation audit rather than a mathematical result (§3.2a), and add the
   cutoff-theorem related-work pointer (§3.2b).
4. Optional but cheap: the paper's "roughly nineteen recorded citations" is 18 in
   OpenAlex as of today, of which 2 postdate 2023 and neither engages. Use the
   exact number with the date.

---

## 8. One-line summary

Every novelty claim in the package survives a fresh check on 2026-08-22: the
audit is unanticipated, the 44 remains an uncited web-table entry (Wikipedia
still says 43), the Level Law and the red/blue colouring have no prior art, and
no one has reimplemented or improved sortnetopt. The work to do before submission
is presentational: fix the 13.6× figure, reframe Theorem A as an audit, cite the
parameterized-verification cutoff literature, and run one plain-web sweep that
this session's exhausted search quota made impossible.
