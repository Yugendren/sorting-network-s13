# The Level Law, Generalized — Census Cutoffs for Exhaustive Search

**Date:** 2026-08-23.
**Question this document answers:** is Chain Collapse (`docs/ambient-reduction.md`
Theorem E) a fact about sorting networks, or a reusable METHOD?
**Scope:** read-only with respect to `src/`, `evidence/`, `config/`, `ledger/`
and every other `docs/` file. New files: this document,
`tools/verify_level_law_general.py`, and artefacts under
`.build/v3-generalize/`. No commits. No candidate network was constructed and
no witness exists anywhere in this work. Every statement below is about levels
`ℓ ≤ 6`, where `D(n) = S(n) − C(n)` is known from `S(3..12)`.

---

## 0. Verdict

| question | answer |
|---|---|
| Can the theorem be stated abstractly? | **Yes**, and doing so **splits it into two logically independent halves** that were fused in the sorting-network statement. §1. |
| Which hypotheses does each half need? | Part I (Ambient Collapse) needs H0, H1, H2, **H4**; Part II (Chain Collapse) additionally needs H3 and H5. §1.3. |
| Was any hypothesis invisible in the original? | **Yes — H4, width convexity.** It is free in sorting networks because width never increases along an edge, so nobody noticed it. In general it is the hypothesis that can actually fail, and it is what the second-domain experiment was designed to attack. §1.4. |
| Does it hold in a second domain? | **Yes, in two, exactly.** Boolean chains (levels 3 and 4) and prefix-reversal ("pancake") sorting (levels 5 and 6). Every one of the pre-registered predictions reproduced **key-for-key**, zero discrepancies, across 36 + 6 + 45 + 6 ordered ambient pairs. §4, §5. |
| Could the collapse be an artefact of the implementation? | **No.** In the Boolean domain a raw enumeration with no canonicalisation and no modelling shortcut reproduces `reach()` exactly and shows the canonical form is a **complete** invariant. Two independent external reimplementations, using a different state convention, get different absolute counts but **the same cutoff** — the collapse is convention-independent. §4.2a, §4.2b. |
| Anything weakened under challenge? | **Yes, three things, all recorded in place.** (i) The **novelty claim**: Kaiser–Kroening–Wahl (CAV 2010) Def. 4 already gives a cutoff over a *set of reachable states*, so "first cutoff about a set, not a property" is **false** — §2.1. (ii) The threshold formula `n_stab(ℓ) = ℓ+1` fails at `ℓ = 7` — §5.3. (iii) The Boolean-chain cutoff *is* the folklore bound — §4.5. None touches Part I. |
| Prior-art positioning | A **cutoff theorem** in the Emerson–Namjoshi / Außerlechner *tight-cutoff* sense, for the census of a search space. What survives as new: **a-priori** (not dynamically detected), **combinatorial-optimality search** (not concurrent programs), and a **polynomial growth law** for the census, which has no precedent anywhere. §2.1. |
| Any citation errors found? | **Yes, in other documents.** `[EK07]` is **Namjoshi solo, LNCS 4349 pp. 299–313**, not Emerson & Kahlon pp. 178–192; it propagates through `audit-paper-v2.md` and `final-review-external.md`. Verified directly; flagged, not fixed (read-only scope). §2.6. |
| Does the *whole* theorem generalize? | **No.** Part I generalized to both. Part II — the "exactly one state per width above `n_min`" tail — needs a **gated root tower** and fails in both new domains. §5.4. |
| Is there a replacement for Part II? | **Yes, and it is better.** Three tail regimes: empty, trivial, and **eventually polynomial**. In the polynomial regime the method still works exactly. §1.5, §5.3. |
| Does the sorting-network cutoff beat the folklore explanation? | **Yes, decisively — the folklore bound is vacuous here.** §2.2. This was the single question the whole claim rested on. |
| Is the Boolean-chain cutoff substantive? | **No.** `n_min(ℓ) = 2ℓ` *is* the folklore support bound. Re-graded from "decisive experiment" to **positive control**. §4.5. |
| Method paper or sorting-network fact? | **Method — but a narrower and better-defended one than the brief assumed.** §7. |

---

## 1. The abstract theorem

### 1.1 The class

> **Definition (graded ambient search).** A *graded ambient search* is a tuple
> `(S, w, →, γ, {root_n})` where
>
> * `S` is a set of **canonical states** and `w : S → ℕ` assigns each state an
>   intrinsic **width**. `S` does **not** depend on the ambient parameter `n`.
> * For each ambient `n` there is a **transition relation** `→_n ⊆ S × S`.
> * `γ` assigns each edge a non-negative integer **grade**.
> * `root_n ∈ S` is the ambient-`n` **root**.
>
> The object of study is the **census**
> ```
> Reach(n, ℓ) = { s ∈ S : d_n(root_n, s) ≤ C(n) + ℓ }
> ```
> where `d_n` is the `γ`-weighted distance in `→_n` and `C(n)` is the
> free-chain offset of H3. `ℓ` is the **level** and `W(w, ℓ)` the width-`w`
> **stratum**.

The census is deliberately *the set of states an exhaustive search stores*, not
the abstract solution set. That is what costs money, and it is what
`ambient-reduction.md` Theorem E is about.

**Three-sentence summary of the class.** A graded ambient search is a family of
exhaustive searches indexed by an ambient dimension `n`, whose states are
canonical objects carrying an intrinsic width `w ≤ n` that is *the same name at
every ambient* because canonicalisation quotients the unused dimensions away.
Its transition relation is *ambient-free*: raising `n` may only add edges into
*wider* states and never alters the width-`≤ m` part, and its edge grades never
mention `n`. Its cost budget is reparameterised as a *level* `ℓ = L − C(n)`
above a forced free chain of initial progress `C(n)` given in closed form.

### 1.2 The hypotheses

> **H0 (ambient-free naming).** The canonical name of a state is a function of
> the state alone; canonicalisation **quotients away unused dimensions**, so an
> object occupying `k` of the `n` available dimensions has one and the same
> name at every ambient `n ≥ k`.
>
> **H1 (ambient freedom, stratified).** For every `s` and all `w(s) ≤ m ≤ n`,
> `{ t : s →_n t, w(t) ≤ m } = { t : s →_m t }`. Raising the ambient may only
> add transitions to *wider* states.
>
> **H2 (ambient-free grading).** `γ(s → t)` is a function of `(s, t)` alone.
>
> **H3 (root tower).** `root_n →_n root_{n-1}` with grade `δ(n)` and
> `w(root_n) = n`; `C(n) = Σ_{k ≤ n} δ(k)` is the **free chain**.
> *Degenerate case, explicitly allowed:* `w(root_n) = 0`, so
> `root_n = root_{n-1}` and `C ≡ 0`.
>
> **H4 (width convexity — "no high-width detour").** For every `s` with
> `w(s) ≤ m` and every `n ≥ m`, some `γ`-geodesic `root_n ⇝ s` passes only
> through states of width `≤ max(m, w(root_m))`.
>
> **H5 (gated tail).** There is a computable `n_min(ℓ)` such that for every
> `w > n_min(ℓ)` the stratum `W(w, ℓ)` is the single chain state `root_w`.

### 1.3 The theorem

> **Theorem (Census Cutoff).**
>
> **(I) Ambient Collapse.** Assume H0, H1, H2, H4. Then for all `m ≤ n`,
> ```
> Reach(n, ℓ) ∩ { w ≤ m }  =  Reach(m, ℓ) ∩ { w ≤ m },
> ```
> with equal levels on every shared state. Equivalently
> `Reach(n, ℓ) = ⨆_{w ≤ n} W(w, ℓ)` where each stratum is a function of
> `(w, ℓ)` alone, carrying **no dependence on `n`**.
>
> **(II) Chain Collapse.** Assume in addition H3 and H5. Then for all
> `n ≥ n_min(ℓ)`,
> ```
> Reach(n, ℓ)  =  Reach(n_min(ℓ), ℓ)  ⊎  { root_w : n_min(ℓ) < w ≤ n },
> ```
> so `|Reach(n, ℓ)| = |Reach(n_min(ℓ), ℓ)| + (n − n_min(ℓ))`: the census at
> **every** ambient follows from **one** computation at ambient `n_min(ℓ)`.

*Proof of (I).* Fix `s` with `w(s) ≤ m ≤ n`.

*(one direction)* Let `root_n = s_0 → … → s_r = s` be a `γ`-geodesic at ambient
`n`. By **H4** it may be chosen inside `{ w ≤ max(m, w(root_m)) }`. By **H3**
its initial segment is the root tower `root_n → … → root_m`, of total grade
`C(n) − C(m)` (empty, with `C(n) − C(m) = 0`, in the degenerate case). Every
remaining edge has both endpoints of width `≤ m`, so by **H1** it is an edge of
`→_m`, by **H2** carries the same grade, and by **H0** its endpoints have the
same names at both ambients. Hence
`d_m(root_m, s) ≤ d_n(root_n, s) − (C(n) − C(m))`: the *level* of `s` at
ambient `m` is at most its level at ambient `n`.

*(converse)* Take a geodesic at ambient `m`; every edge joins states of width
`≤ m`, so by **H1** read right to left it is an edge of `→_n`. Prepending the
root tower gives a walk at ambient `n` of grade
`C(n) − C(m) + d_m(root_m, s)`, so the level at ambient `n` is at most the
level at ambient `m`.

Equality of levels follows, hence equality of the width-`≤ m` parts. ∎

*Proof of (II).* By (I) the strata of width `≤ n_min(ℓ)` are those of the
ambient-`n_min(ℓ)` run; by **H5** every stratum above is `{ root_w }`. ∎

**Which hypothesis each step needs.**

| step | H0 | H1 | H2 | H3 | H4 | H5 |
|---|---|---|---|---|---|---|
| geodesic confinable to width ≤ m | | | | | **yes** | |
| initial segment is the root tower, grade `C(n) − C(m)` | | | | **yes** | | |
| remaining edges exist at ambient `m` | | **yes** | | | | |
| grades agree | | | **yes** | | | |
| states have the same *names* at both ambients | **yes** | | | | | |
| converse direction | | **yes** | **yes** | **yes** | | |
| the tail is a chain | | | | **yes** | | **yes** |

**Part I uses neither H3 nor H5.** That split is the main structural finding of
this campaign: the flagship theorem is two theorems.

### 1.4 What the split buys, and what H4 costs

In sorting networks H4 is *free*: `Succ` preserves width and `Prune` lowers it
by one (`ambient-reduction.md` Corollary A2, Width Closure), so the geodesic
descends monotonically. Because it is free there, it was never stated. It is
not free in general: the moment an edge can *raise* the width, a large-ambient
search acquires routes that go up and come back down, and Part I becomes the
genuine claim that **those routes are never shortcuts**. Hence the choice of
second domain in §5: one in which width is neither monotone up nor down.

### 1.5 The three tail regimes

H5 is strong and rare. Measured across three domains, the tail falls into
exactly one of three regimes:

| regime | shape of `W(w, ℓ)` above the front | `|Reach(n, ℓ)|` for large `n` | instance |
|---|---|---|---|
| **T-empty** | nothing above `n_min(ℓ)` | constant | Boolean chains, `n_min(ℓ) = 2ℓ` |
| **T-trivial** (= H5) | one state per width | `const + n` | sorting networks, `n_min(ℓ) = min{n : D(n) ≥ ℓ}` |
| **T-poly** | a polynomial in `w` | polynomial in `n` | prefix reversal, degree `ℓ−1`, exact for `w ≥ ℓ+1` |

> **Corollary (polynomial census cutoff).** Assume H0, H1, H2, H4 and that
> `W(·, ℓ)` agrees with a polynomial of degree `d(ℓ)` for all `w ≥ n_stab(ℓ)`.
> Then `|Reach(n, ℓ)|` is a polynomial in `n` of degree `d(ℓ) + 1` for
> `n ≥ n_stab(ℓ)`, and **one** run at ambient `n_stab(ℓ) + d(ℓ) + 1`
> determines the census at every larger ambient exactly.

T-poly is the regime the method most often lands in, and it still delivers the
payoff (§5.3: a fit at widths ≤ 12 predicted widths 13, 14, 15 exactly).

### 1.6 The three instances against the hypotheses — the finding in one table

| | sorting networks | Boolean chains | prefix reversal |
|---|---|---|---|
| ambient `n` | channels | input variables | pancakes |
| width `w` | channels of the state | essential variables | length after stripping the sorted suffix |
| width along an edge | **non-increasing** | **non-decreasing** | **neither** |
| H0 ambient-free naming | yes | yes | yes |
| H1 ambient freedom | yes (an *implementation audit*; one leak, §5.5) | yes, verified vs. full ambient | yes, verified state by state |
| H2 ambient-free grading | yes | yes | yes |
| **H3 root tower** | **yes, non-degenerate**, `C(n) = B(n)` | degenerate, `C ≡ 0` | degenerate, `C ≡ 0` |
| H4 width convexity | **free** (width closure) | **free** (monotone up) | **the real test — verified, not proved** |
| **H5 gated tail** | **yes** (Theorems C+D) | no — tail empty | no — tail polynomial |
| **Part I holds?** | yes | **yes** | **yes** |
| **Part II holds?** | yes | no | no |
| cutoff vs. folklore support bound | folklore bound **vacuous** (§2.2) | cutoff **is** the folklore bound | no support bound exists |

Read across the H3 and H5 rows: **the only domain with a non-degenerate root
tower is the only domain with a trivial tail.** That is the mechanism, and it
is why Part II does not generalize while Part I does.

---

## 2. Prior-art positioning

### 2.1 A cutoff theorem — and the novelty claim must be weakened

The result is, structurally, a **cutoff theorem**: for all `n ≥ n_min(ℓ)` the
behaviour of the size-`n` instance is determined by the size-`n_min` instance.
That is a mature named concept in **parameterized verification**:

| work | what is preserved above the cutoff | how the cutoff is obtained |
|---|---|---|
| Emerson & Namjoshi, *Reasoning about rings*, POPL '95 85–94, DOI `10.1145/199448.199468`; journal *On Reasoning About Rings*, **IJFCS 14(4) (2003) 527–550**, DOI `10.1142/S0129054103001881` | prenex-indexed CTL\*\X in token rings | a-priori closed form per quantifier prefix (2, 3, 4, 5) |
| Emerson & Kahlon, *Reducing Model Checking of the Many to the Few*, CADE-17, **LNCS 1831 (2000) 236–254**, DOI `10.1007/10721959_19` | indexed LTL\X + global deadlock, guarded protocols | a-priori, `\|B\|+2` / `2\|B\|` / `2\|B\|+1` |
| **Namjoshi (solo)**, *Symmetry and completeness in the analysis of parameterized systems*, VMCAI 2007, **LNCS 4349, 299–313**, DOI `10.1007/978-3-540-69738-1_22` | invariance `AG(φ(n))`; the method is **complete** for invariance | existence result; finding `K` is undecidable |
| **Kaiser, Kroening, Wahl**, *Dynamic Cutoff Detection in Parameterized Concurrent Programs*, CAV 2010, **LNCS 6174, 645–659**, DOI `10.1007/978-3-642-14295-6_55` | **a set of reachable states**: Def. 4, *"a number `c ∈ ℕ` such that, for all `n ≥ c`, `R_n = R_c`"* | **dynamically detected** during the analysis; sufficient runtime test |
| Außerlechner, Jacobs, Khalimov, *Tight Cutoffs for Guarded Protocols with Fairness*, VMCAI 2016, **LNCS 9583, 476–494**, DOI `10.1007/978-3-662-49122-5_23`, arXiv:1505.03273 | k-indexed LTL\X + deadlock, open systems | a-priori closed forms, tight |
| **Jaber, Jacobs, Wagner, Kulkarni, Samanta**, *Parameterized Verification of Systems with Global Synchronization and Guards*, CAV 2020, **LNCS 12224, 299–323**, DOI `10.1007/978-3-030-53288-8_15`, arXiv:2004.04896 | reachability `φ_m(s)` | a-priori `c = m`, conditional on a syntactic amenability check |
| Jacobs & Sakr, *Analyzing Guarded Protocols*, VMCAI 2018, **LNCS 10747, 247–268**, DOI `10.1007/978-3-319-73721-8_12` | — | source of a clean verbatim cutoff definition |
| Bloem, Jacobs, Khalimov, Konnov, Rubin, Veith, Widder, *Decidability of Parameterized Verification*, Morgan & Claypool 2015, DOI `10.2200/S00658ED1V01Y201508DCT013` | — | **the book's verbatim definition was NOT obtained** (paywalled, no arXiv version). Get it from a library; do not paraphrase it. |

> **CORRECTION — the novelty claim as previously written is FALSE and must be
> weakened.** Earlier drafts of this campaign (and `final-review-external.md`
> §3.2b) asserted that no prior cutoff theorem concerns *a set of states*
> rather than *the truth of a property*. **Kaiser–Kroening–Wahl Definition 4 is
> exactly such a theorem** — `∀n ≥ c : R_n = R_c` for the set of reachable
> thread states. It must be cited as the closest prior art and distinguished,
> not omitted.
>
> Three distinctions survive, and they are enough:
> 1. `R_n` is a set of *abstract* thread states (local × shared) under a fixed
>    finite abstraction; our census is the concrete set of states an exhaustive
>    optimality search actually **stores**.
> 2. KKW conclude **exact equality** with no growth term. Part II gives
>    `Reach(n,ℓ) = Reach(n_min,ℓ) ⊎ {root_w}` and the T-poly regime gives
>    genuine polynomial growth in `n`. KKW have no analogue of either.
> 3. KKW's cutoff is **dynamically detected** by a sufficient runtime test;
>    ours is an **a-priori** consequence of H0–H5.
>
> **Safe claim:** *the first a-priori cutoff theorem for the census of an
> exhaustive combinatorial-optimality search, and the first in any setting to
> give a polynomial growth law for that census.* **Not** "the first cutoff
> theorem about a set rather than a property."

**Which sense of "cutoff" is ours.** Two competing definitions are in use.
Ours is the Emerson–Namjoshi / Außerlechner **tight-cutoff** form (*"if `n₀` is
the smallest number such that `∀n ≥ n₀` … then any `c < n₀` is not a cutoff,
any `c ≥ n₀` is"*), **not** the Emerson–Kahlon form. Say so explicitly; it
costs one clause and pre-empts a referee. Recommended framing sentence:

> *Theorem (Census Cutoff) is a cutoff theorem in the sense of
> Emerson–Namjoshi and Außerlechner–Jacobs–Khalimov, with the census of the
> explored state set in place of the truth of a temporal property.*

**Vocabulary rulings.**

| term | ruling |
|---|---|
| **cutoff** | **use it** — matches the quantified form exactly |
| **parameterized family** (of searches) | use it |
| *parameterized system* | **misuse** — we have one search over one `S` with an ambient-dependent `→_n`, not a family of systems with process semantics |
| *process template* | **misuse** — no replicated component, no template |
| *index* | correct but **unnecessary and misleading**; "index" here means process count. Say `n`, "ambient", or "parameter" |
| *small model property* | **borderline — not as a headline.** SMP means "satisfiable ⇒ satisfiable in a bounded model"; ours is stabilisation. Use only inside a sentence that defines the usage |
| *well-structured transition system*, *well-quasi-order* | **misuse.** We have a grading `γ` and a width `w`; H4 is geodesic confinement, not order-monotonicity. Cite WSTS (Finkel–Schnoebelen, *TCS* 256 (2001) 63–92, DOI `10.1016/S0304-3975(00)00102-X`; Abdulla–Čerāns–Jonsson–Tsay, LICS 1996, DOI `10.1109/LICS.1996.561359`) only as **contrast**: WQO+monotonicity gives decidable coverability by a backward fixpoint, with no computable bound and often no cutoff at all |
| *monotonicity* | only as "**width-monotone along geodesics**", defined; never bare |

**Nearest neighbours on the polynomial-census side** (none is prior art, all
worth citing): Bogart, Goodrick & Woods, *Parametric Presburger arithmetic*,
**Discrete Analysis 2017:4**, DOI `10.19086/da.1254` — definable families have
eventually *quasi*-polynomial cardinality, but of a logically definable set,
not of what an algorithm stores; Berthomieu, Le Botlan & Dal Zilio, *Petri Net
Reductions for Counting Markings*, SPIN 2018, LNCS 10869, 65–84 (journal
*STTT* 22(2) (2020) 163–181) — exact polynomial marking counts, but for the
reachable set of a fixed net with no threshold; counter abstraction (Basler,
Mazzucchi, Wahl, Kroening, *FMSD* 36(3) (2010) 223–245) and view abstraction
(Abdulla, Haziza, Holík, *STTT* 18(5) (2016) 495–516) bound the explored object
**by construction**, not by a theorem.

### 2.2 THE BLOCKER, and why it does not bind — the folklore support bound

The obvious deflationary explanation for any census stabilising in `n` is the
**support bound**: an object built from `k` operations touches at most `2k`
coordinates, so up to permutation the census cannot change once `n ≥ 2k`. This
is visible in published sorting-network data: the `|R^n_k|` table of
Codish–Cruz-Filipe–Frank–Schneider-Kamp (ICTAI 2014 §3 / JCSS 82(3):551–563,
2016) has column `k = 3` constant (at 7) from `n = 6` and column `k = 2`
constant (at 3) across the whole published range, which starts at `n = 4` — so
the visible onset is exactly `n = 2k`, unremarked in the paper. A referee will
see it immediately, so print the table yourself.

**If `n_min(ℓ)` were not materially below `2k`, the Level Law would be
folklore.** It is not, and the reason is sharper than a ratio: in our setting
the operation count at level `ℓ` is `L = C(n) + ℓ`, and `C(n) = Θ(n log n)`, so
the support bound demands `n ≥ 2(C(n) + ℓ)` — **which is false for every
`n ≥ 3` and becomes more false as `n` grows.**

| level ℓ | `n_min(ℓ)` observed | comparators `L = C(n_min) + ℓ` | support bound `2L` | is `2L ≤ n_min`? |
|---|---|---|---|---|
| 1 | 5 | 9 | 18 | **no** (3.6× over) |
| 2 | 7 | 16 | 32 | **no** (4.6× over) |
| 3 | 9 | 24 | 48 | **no** (5.3× over) |
| 4 | 9 | 25 | 50 | **no** (5.6× over) |
| 5 | 11 | 34 | 68 | **no** (6.2× over) |
| 6 | 11 | 35 | 70 | **no** (6.4× over) |

> **The support bound is not merely weak here; it is vacuous.** It never
> certifies stabilisation at any ambient the search can actually reach, at any
> level, and the gap widens with `n`. The sorting-network cutoff is therefore
> not an instance of the folklore phenomenon. It comes from Theorems B/C/D —
> the *gated root tower* — which is a different mechanism entirely.

The honest converse, recorded in §4.5: in the Boolean-chain domain
`n_min(ℓ) = 2ℓ` **is** exactly the support bound, so that domain is a positive
control, not independent evidence of a non-trivial cutoff.

**How to cite the folklore.** A sweep found the support bound is **genuinely
uncited in the form used here** — no source states it as a named observation or
lemma, and the FI-module literature never uses support/touching language at
all. So call it folklore explicitly and cite the four places the same argument
does appear, by field:

* **Parameterized complexity — the closest verbatim version of the
  *argument*.** Buss's rule: Buss & Goldsmith, *Nondeterminism within P*,
  **SIAM J. Comput. 22(3) (1993) 560–572**; textbook form in Cygan, Fomin,
  Kowalik, Lokshtanov, Marx, Pilipczuk, Pilipczuk & Saurabh, *Parameterized
  Algorithms*, Springer 2015, **§2.2.1 "Buss's kernel"**. Literally "a solution
  of size `k` touches at most `k` elements" — but about *instance size*, not
  about a count becoming polynomial in `n`.
* **The conclusion, mechanism unnamed.** Farb, *Representation stability*,
  **Proc. ICM 2014, Vol. II, 1173–1196, Thm 4.4** (eventual equality to a
  polynomial, and *"we are claiming eventual equality to a polynomial, not just
  polynomial growth"*); Wilson, *An introduction to FI-modules and their
  generalizations* (2018 lecture notes), Thm XXXV and **Exercise 58(b)**, where
  `dim M(d)_n = n(n−1)⋯(n−d+1)` **is the support bound in disguise** — a basis
  is the injections `[d] ↪ [n]`, each generator touching exactly `d` of the `n`
  points — yet it is left as homework and never named.
* **The threshold form, and it *is* named — in finite model theory.** Hanf
  locality / threshold equivalence: Hanf, in *The Theory of Models* (1965)
  132–145; finite version Fagin, Stockmeyer & Vardi, *On monadic NP vs. monadic
  co-NP*, **Inf. Comput. 120(1) (1995) 78–92**; Libkin, *Elements of Finite
  Model Theory*, Springer 2004, Chs. 3–4.
* **The named bounded-support object: the junta.** Blais, *Testing juntas: a
  brief survey*, LNCS 6390 (2010) 32–40; Fischer, Kindler, Ron, Safra &
  Samorodnitsky, *Testing juntas*, **JCSS 68(4) (2004) 753–787**. The counting
  corollary (`≤ C(n,k)·2^{2^k}`, degree `k` in `n`) is used, never proved as a
  lemma.
* Also relevant for the effective/automatic version in combinatorics:
  Kaiser & Klazar, *On growth rates of closed permutation classes*, **Electron.
  J. Combin. 9(2) (2003) #R10** (Fibonacci Dichotomy); Homberger & Vatter, *On
  the effective and automatic enumeration of polynomial permutation classes*,
  **J. Symb. Comput. 76 (2016) 84–96**.

### 2.3 Three concessions to make in the paper's own words

1. **`C(n)` is classical.** Since `Σ_{k=1}^{3} ⌈log₂ k⌉ = 3`, our
   `C(n) = 3 + Σ_{k=4}^{n} ⌈log₂ k⌉` is identically `Σ_{k=1}^{n} ⌈log₂ k⌉` —
   Knuth's binary-insertion number `B(n)` (*TAOCP* v3 §5.3.1 eq. (3)), **OEIS
   A001855**, closed form `n⌈log₂ n⌉ − 2^{⌈log₂ n⌉} + 1`. It must never be
   presented as new. What is new is (i) exhibiting it as the cost of a *forced
   prefix of the search* and (ii) the reparameterisation `ℓ = L − C(n)`. The
   term *free chain* appears to be ours.
2. **Inert-channel invariance already exists.** Harder (arXiv:2012.04400)
   Lemma 53 (Unique Prunable Channel) states `s(X) = s((X/i)°)`, with an
   explicit `n → n+1` lifting; and his DP already memoises across channel
   counts. Theorem E must be positioned as a *set/census* statement about a
   *level*, explicitly not "Lemma 53 iterated".
3. **Cross-`n` recurrences are prior art.** Codish–Cruz-Filipe–Schneider-Kamp
   (SYNASC 2014, arXiv:1404.0948) Thms 3–4 relate layer counts across `n`
   using "a layer with an extra unused channel". Growth recurrences, not
   stabilisation — but they establish that relating search spaces across `n` is
   not itself novel.

Counterweight worth quoting: Cruz-Filipe & Schneider-Kamp, LPAR-25, EPiC
100:36–50, 2024, §1: *"Progress in this direction has been slow… The only
general theoretical result dates to the 1970s."*

### 2.4 Representation stability — adjacent, and we are **not** an instance

**Citations, with the traps.** Church, Ellenberg & Farb, *FI-modules and
stability for representations of symmetric groups*, **Duke Math. J. 164(9)
(2015) 1833–1910**, DOI `10.1215/00127094-3120274`, arXiv:1204.4533. The
effective statement is **Theorem 3.3.4**, not the more-quoted Theorem 1.5:
taking `σ = id` gives `dim V_n` *exactly* polynomial of degree `≤ weight(V)`
for all `n ≥ stab-deg(V) + weight(V)`. Char-0 is dropped by Church, Ellenberg,
Farb & Nagpal, *FI-modules over Noetherian rings*, **Geom. Topol. 18(5) (2014)
2951–2984**, DOI `10.2140/gt.2014.18.2951`, Thm B — but that version gives
**no threshold**.

Ramos, Speyer & White, *FI–sets with relations*, **Algebraic Combinatorics
3(5) (2020) 1079–1098**, DOI `10.5802/alco.128`, arXiv:1804.04238.
*Four mis-citations to avoid:* the venue is **Algebraic Combinatorics**
(Centre Mersenne), **not** Springer's *Journal of Algebraic Combinatorics* and
not *Journal of Algebra* (that is Ramos's solo paper); the year is **2020**,
not the 2018 arXiv year; and it is not Ramos–White, *Families of nested
graphs…*, **Selecta Math. 25 (2019), Paper 70**, DOI
`10.1007/s00029-019-0520-9`. RSW Theorem A yields, for `n ≫ 0`,
`|X_n| = Σ_i (n)_{m_i}/|H_i|` — an exact polynomial whose leading coefficient
is a sum of reciprocals of stabiliser orders. Def. 3.7 names the limit the
**stable orbits**; borrow that term.

**We are not an instance, and claiming otherwise is an error an FI-literate
referee catches instantly.** Three independent reasons:

1. **Degree.** FI theory gives an *upper* bound (`≤ weight ≤ generating
   degree`) and only after a generation degree is independently exhibited. It
   never yields the equality `deg = ℓ−1`.
2. **Threshold.** The best effective bounds are `max(g,r) + g` (CEF 3.3.4) and
   `r + min{r,d}` (Ramos, **J. Algebra 502 (2018) 163–195**, DOI
   `10.1016/j.jalgebra.2017.12.037`, Thm D). With `r ≈ d ≈ ℓ−1` these give
   roughly `2ℓ−2`, so our measured onset **beats the known effective bounds by
   about a factor of two**. RSW gives no threshold at all.
3. **Leading coefficient.** The only structural prediction anywhere is the RSW
   corollary that it is a positive rational `Σ 1/|H_i|`, which merely *permits*
   the integer `ℓ`. And uniformity in `ℓ` is outside the framework entirely:
   FI theory is one-parameter and treats each `ℓ` as a separate object.

**Decisive caveat, and it kills the obvious model.** There is **no
FI-theoretic treatment of prefix reversal anywhere in the literature**, and
there is an obstruction to constructing one: by RSW Theorem A the cardinality
of a finitely generated FI-set is eventually polynomial, so `S_n` (size `n!`)
is **not** a finitely generated FI-set and the pancake graph is **not**
vertex-stable in the Ramos–White sense — Ramos–White Thm D therefore does
**not** apply to prefix-reversal walks as stated.

**Correct framing.** Eventual polynomiality is the expected qualitative
behaviour, and CEF 3.3.4 / CEFN B / RSW A is the standard framework that
predicts it *if an FI-structure is exhibited*. Our exactness from a threshold
is consistent with a **Nagpal number** of exactly that threshold (Nagpal's
shift theorem, arXiv:1505.04294 — a preprint with no journal version, cite by
arXiv id; characterised by Ramos Thm C via `∂reg`, with regularity bounded in
Church–Ellenberg, **Geom. Topol. 21(4) (2017) 2373–2418**, DOI
`10.2140/gt.2017.21.2373`, Thm A). But **do not write "FI theory predicts
this."** Either exhibit the FI-structure or state plainly that none is known in
this domain. All three sharp features are defensible as new.

Separately, for Chain Collapse itself: RSW gives *eventual constancy* of orbit
counts, while Part II gives constancy **plus an explicit linear tail**, so
`|Reach(n, ℓ)|` is eventually *linear* in `n`, not constant. The honest
sentence is that the core of the census exhibits RSW-style eventual orbit
stability, our family carries an explicitly identified growing tail, and the
content of the theorem is that the tail is exactly that and nothing more — with
an **effectively computable** onset, which all RSW statements lack.

---

### 2.5 Prior art on the two new domains

**Prefix reversal.** The eventual polynomiality of pancake sphere sizes is
**reported to be already published** (§5.3). Good outcome: the abstract theorem
predicts a known theorem in another field. Citations reported but **not yet
verified against primary sources**.

**Boolean chains.** The closest prior art is Adam P. Goucher, *"Searching for
optimal Boolean chains"* (talk transcript, 28 Feb 2023,
`cp4space.hatsya.com/wp-content/uploads/2023/03/sfobc_transcript.pdf`), which
runs **exactly this BFS** over canonicalised sets of truth tables — "*a tt-set
`T` is attainable if it corresponds to at least one chain*", "*the search
becomes much faster if we only store canonical tt-sets*". Differences: his
group is the fixed-`k` NPN group (it includes input/output negation, ours does
not), he does **not** delete unused inputs, and he makes **no stabilisation
claim**. **Cite it as adjacent prior art for the method**; it is a blog-hosted
transcript, not peer-reviewed. Also relevant as a *contrast*:
Haaswijk–Soeken–Mishchenko–De Micheli, *SAT-Based Exact Synthesis*, IEEE TCAD
39(4):871–884, 2020, DOI `10.1109/TCAD.2019.2897703`, §IV-C — their partial
DAGs are "*agnostic with respect to the number of primary inputs*", i.e.
`n`-independent **by construction** because inputs are never bound, which is
not a theorem about essential-support growth. Knuth *TAOCP* §7.1.2
(Pre-Fascicle 0C) was checked and contains **no** chain census.

Stabilisation of NPN class counts under "`n` or fewer variables" is **folklore**
(Harrison, *Introduction to Switching and Automata Theory*, McGraw-Hill 1965,
p. 153; OEIS A000370, A000612, A000616). Restate, do not claim.

Caution: OEIS **A121080** begins 1, 4, 37, 541, 10625, 258661 — the first four
terms coincide with our level-0…3 totals. It counts injective partial
transformations in a symplectic/orthogonal setting (Li–Li–Cao, *Discrete Math.*
306:1781–1787, 2006) and has no circuit connection. **Compute the level-4 total
before publishing the sequence**; if it is 10 625 the coincidence needs real
investigation rather than a footnote.

### 2.6 Two corrections required in OTHER documents

This campaign is read-only outside this file and
`tools/verify_level_law_general.py`, so these are flagged, not fixed. Both were
verified directly against the files.

1. **A wrong citation, propagating.** `docs/paper/audit-paper-v2.md:851-852`
   reads
   ```
   [EK07] E. A. Emerson, V. Kahlon. Symmetry and completeness in the analysis of
   parameterized systems. VMCAI 2007, LNCS 4349, 178–192.
   ```
   **Wrong author and wrong pages.** It is **Kedar S. Namjoshi, solo**, LNCS
   **4349, 299–313**, DOI `10.1007/978-3-540-69738-1_22`. Emerson & Kahlon have
   no VMCAI 2007 paper, and LNCS 4349 pp. 178–192 is not a typo for anything
   (167–181 is Fecher–Huth, 182–198 is Wachter–Westphal). The same wrong
   attribution appears at `docs/final-review-external.md:236` and the key
   `[EK07]` is used at `docs/paper/audit-paper-v2.md:563`. Renaming the key to
   `[Nam07]` would prevent the error recurring.
   This matters beyond tidiness: Namjoshi's Definition 3 (Cutoff Method) is the
   **single most useful citation** for the "is this a real named concept"
   framing, and his Theorem 1 proves the method **complete** for invariance.

2. **A claim to guard.** `docs/paper/audit-paper-v2.md:565` says *"this appears
   to be the first cutoff theorem for a combinatorial-optimality search"*, with
   `[KKW10]` in the citation list but not distinguished. As written that claim
   is **defensible** — Kaiser–Kroening–Wahl is about concurrent programs, not
   combinatorial optimality — so this is a hardening, not a correction. Add one
   sentence noting that KKW10's Definition 4 is itself a cutoff over a *set of
   reachable states* rather than a property, and that the distinctions are
   abstraction vs. stored set, exact equality vs. an explicit growth tail, and
   dynamic detection vs. an a-priori theorem. A referee who knows KKW10 will
   otherwise raise it.

### 2.7 Still open

One item only: the **verbatim cutoff definition from the
Bloem–Jacobs–Khalimov–Konnov–Rubin–Veith–Widder book** could not be obtained
(paywalled; there is **no arXiv version** — the frequently-remembered
arXiv:1509.xxxxx does not exist; the condensed journal summary, *Decidability
in Parameterized Verification*, **ACM SIGACT News 47(2) (2016) 53–64**, DOI
`10.1145/2951860.2951873`, is also blocked). **Get it from a library rather
than paraphrasing a quotation nobody has seen.** Verified substitutes are
available meanwhile: Jacobs & Sakr VMCAI 2018 §2.3, and Aminof–Jacobs–Khalimov–
Rubin, *Parameterized Model Checking of Token-Passing Systems*, VMCAI 2014,
arXiv:1311.4425 §2.4.

Nothing outstanding can change any experimental result.

---

## 3. Method: how the hypotheses are checked

`tools/verify_level_law_general.py` implements the class of §1.1. A domain
supplies five functions — `roots(n)`, `width(key)`, `succ(key, n)`,
`n_min(level)`, `growth()` — and nothing else; keys must be ambient-free byte
strings, which is H0 stated as an API contract.

```
python3 tools/verify_level_law_general.py hypotheses DOM --ambients a,b,c --level L
python3 tools/verify_level_law_general.py census     DOM --ambient N --level L --out F
python3 tools/verify_level_law_general.py predict    DOM --source F --ambients ... --out P
python3 tools/verify_level_law_general.py collapse   DOM --level L --ambients ... --check P
python3 tools/verify_level_law_general.py sortnet-theorems --max-n 6
python3 tools/verify_level_law_general.py bool-fresh-lemma --ambient 6 --level 2
```

`collapse` runs four independent tests: the pre-registered prediction (SHA-256
of the sorted key list), the stratified identity of Part I for every ordered
ambient pair, level agreement on every shared key (H2), and the tail regime.

**Pre-registration protocol and its audit trail.** Each prediction file is
derived by `predict` from a *single* small-ambient census file and records that
file's SHA-256; the prediction file's own SHA-256 is quoted below before the
larger ambients were computed. The file mtimes under `.build/v3-generalize/`
are the audit trail and are monotone in the required order:

| domain | small census | prediction | verification |
|---|---|---|---|
| bool, level 3 | `bool_n6_L3.json` 13:02 | `PREREG_bool_L3.json` 13:03 | `OUT_bool_collapse_L3.txt` 13:13 |
| bool, level 4 | `bool_n8_L4.json` 13:24 | `PREREG_bool_L4.json` 13:24 | (same run, after) |
| pancake, level 5 | `pancake_n7_L5.json` 13:02 | `PREREG_pancake_L5.json` 13:03 | `OUT_pancake_collapse_L5.txt` 13:04 |
| pancake, tail polynomials | (ambient-12 strata) | `PREREG_pancake_R2.json` 13:06 | `OUT_pancake_R2_verify.txt` 13:07 |

The check is on the SHA-256 of the sorted key list, not on counts, so a
coincidence of totals cannot pass it.

### 3.1 Domain 0 — the sorting network, re-derived independently

`sortnet-theorems` re-derives from scratch, with no dependence on the Rust
engine (frozensets of `n`-bit integers, canonicalisation by brute-force
minimisation over `S_n × C_2`), the two facts that give the sorting-network
instance its root tower and its trivial tail:

```
n= 3  Theorem B (prune(cube_n)=cube_{n-1}, 6 images): PASS   Theorem C (unique successor): PASS  |s_n|=6  (want 6):  PASS
n= 4  Theorem B (8 images):  PASS   Theorem C: PASS  |s_n|=12 (want 12): PASS
n= 5  Theorem B (10 images): PASS   Theorem C: PASS  |s_n|=24 (want 24): PASS
n= 6  Theorem B (12 images): PASS   Theorem C: PASS  |s_n|=48 (want 48): PASS
C(3)=3, C(4)=5, C(5)=8, C(6)=11
```

Agrees with `ambient-reduction.md` §4.4 (which checked `k = 6, 9, 11, 13`
against the engine) and reproduces `|s_k| = 3·2^{k−2}` exactly.

The archived engine dumps were also re-verified as a currently-reproducible
baseline (`.build/v3-generalize/OUT_sortnet_ambient_recheck.txt`): the
ambient-13 census at levels 1–4 reproduces `ambient-reduction.md` §4.3 exactly
— totals 41 / 451 / 24 203 / 207 999, with exactly one state at each of widths
10, 11, 12, 13 — and `lemma-l` and `chain` both PASS.

| class item | sorting-network instance |
|---|---|
| `S` | canonical `OutputSet`s |
| `w` | `OutputSet::channels()` |
| `→_n` | `Succ` (comparators, width preserving) and `Prune` (channel deletion, width −1) |
| `γ` | 1 per comparator; `⌈log₂ k⌉` for the Huffman step at `cube_k` |
| `root_n` | `cube_n` |
| H0 | `canon.rs` is width-preserving and ambient-free |
| H1 | Theorem A — **an implementation audit**, whose sole failure is `SUBSUME_WIDTHS` (§6.3) |
| H2 | `improve` takes no `--limit` and no ambient argument |
| H3 | Theorem B: `canon(prune(cube_k)) = cube_{k−1}`; `δ(k) = ⌈log₂ k⌉`; `C(n) = B(n)` = OEIS A001855 |
| H4 | free: Corollary A2, width closure |
| H5 | Theorems C + D: `cube_n` has exactly two out-edges and the non-chain one is gated until level `> D(n−1)` |

---

## 4. Domain A — Boolean chains (positive control)

### 4.1 The domain

A **Boolean chain** (straight-line program) over `{AND, OR, XOR}` starts from
the `n` projections `x_1 … x_n` and adds gates, each combining two distinct
already-available functions. The **state** after `r` gates is the **multiset of
gate outputs** — a gate is recorded even when its output duplicates a function
already computed, so a program with a redundant gate is a distinct state at
that length, which is what an exhaustive program enumeration actually explores.
The **level** is `r`.

*Canonicalisation (H0).* Discard every input variable not in the essential
support of any computed function — literally "quotient the unused dimensions" —
then take the lexicographic minimum over permutations of the rest. **Width** =
number of essential variables.

*What it tests.* Not a sorting network, not a network at all, not a lower-bound
search. Width is **non-decreasing** rather than non-increasing, so Part I's
proof runs in the opposite direction; and the root has width 0, so **H3 is
degenerate** (`C ≡ 0`) — precisely the configuration that tests whether Part I
is really independent of the root tower. Each gate introduces at most two fresh
variables, so `w ≤ 2r` and

> **`n_min(ℓ) = 2ℓ`**, tail **empty**: `Reach(n, ℓ) = Reach(2ℓ, ℓ)` for every
> `n ≥ 2ℓ`, with no chain states at all.

### 4.2 The one modelling assumption, and its check

The implementation materialises only `min(n, w+2)` variables when expanding a
width-`w` state. **That is a lemma, not an axiom**; if false, the experiment
would be rigged. Checked two ways:

1. `bool-fresh-lemma --ambient 6 --level 2 --caps 3,4`: every successor
   recomputed with three and four fresh variables. **37 states tested, 0
   mismatches at cap 3, 0 at cap 4.**
2. The `bool-full` domain sets the cap to 99, i.e. **materialises every one of
   the `n` ambient variables with no shortcut whatsoever**, and reproduces the
   collapse at level 2 for ambients 4, 5, 6, 7, 8: 37 states at every ambient,
   identical key sets, 0 level disagreements, all 10 ambient pairs PASS.

### 4.2a Brute-force validation — the canonical form is a COMPLETE invariant

A canonical form that is too *coarse* would merge distinct states equally at
every ambient and manufacture a false collapse. `bool-bruteforce` rules that
out. It enumerates **every raw gate sequence** at ambient `n` with **no
canonicalisation during the search and no fresh-variable cap**, groups the raw
states into true `S_n` orbits by brute force over all `n!` permutations, and
checks three things independently of the framework:

```
  n   R |    raw | S_n-orbits | canon keys | reach() | invariant | complete | matches
   4  1 |     19 |          4 |          4 |       4 |      True |     True | PASS
   4  2 |    370 |         37 |         37 |      37 |      True |     True | PASS
   4  3 |   7225 |        486 |        486 |     486 |      True |     True | PASS
   5  1 |     31 |          4 |          4 |       4 |      True |     True | PASS
   5  2 |    886 |         37 |         37 |      37 |      True |     True | PASS
   5  3 |  24981 |        531 |        531 |     531 |      True |     True | PASS
   6  1 |     46 |          4 |          4 |       4 |      True |     True | PASS
   6  2 |   1801 |         37 |         37 |      37 |      True |     True | PASS
   6  3 |  67951 |        541 |        541 |     541 |      True |     True | PASS
```

*invariant* = `canon` is constant on orbits; *complete* = `canon` separates
distinct orbits; *matches* = `reach()` reproduces the brute force exactly, key
set **and** levels. All nine cells pass.

Two things follow. First, the canonical form is a **complete** invariant, so no
false collapse is possible. Second, and more usefully, **the brute force
confirms the collapse on its own**, sharing no machinery with the domain
implementation: 4 / 37 orbits at every one of `n = 4, 5, 6`, and the level-3
sequence 486 / 531 / 541 at `n = 4 / 5 / 6` — exactly the pre-registered
restriction predictions of §4.3.

### 4.2b The collapse is convention-independent — and an external cross-check

Two independent external reimplementations of this domain reported the totals
**4 / 34 / 478** where we report **4 / 37 / 541**. The whole difference is the
state convention: they treat the state as a *set of functions* (a gate whose
output is already present is absorbed), we treat it as the *multiset of gate
outputs* (§4.1). Re-running the raw enumeration under the **set** convention
reproduces their numbers exactly:

| ambient `n` | `r ≤ 1` | `r ≤ 2` | `r ≤ 3` |
|---|---|---|---|
| 4 | 4 | 34 | 423 |
| 5 | 4 | 34 | 468 |
| 6 | 4 | 34 | **478** |
| 7 | 4 | 34 | **478** |

Three things follow, and the third is the useful one.

1. The disagreement is fully explained and is not an error on either side.
2. Both external reimplementations are consistent with ours once the convention
   is fixed — a genuine independent replication.
3. **The collapse itself is convention-independent.** Under the set convention
   the census is constant at 34 from `n = 4 = 2·2` and at 478 from
   `n = 6 = 2·3`; under the multiset convention it is constant at 37 and 541
   from the same two ambients. `n_min(ℓ) = 2ℓ` in both. **The absolute
   sequence depends on a modelling choice; the cutoff does not.** Only the
   cutoff is being claimed.

### 4.3 Pre-registration

Small instance first — `.build/v3-generalize/bool_n6_L3.json`,
`sha256 = e6c39014f31bb5b23881d939302cb56c0093fff9c27189ecf3e4849c9e41a744`,
written 2026-08-23T13:02:55Z:

```
ambient 6, level<=3 : 541 states  (67.2 s)
  width 0 : {0: 1}      width 2 : {1: 3, 2: 12, 3: 50}    width 3 : {2: 15, 3: 218}
  width 4 : {2: 6, 3: 181}   width 5 : {3: 45}            width 6 : {3: 10}
```

Prediction derived **from that file alone** and frozen at 13:03:38Z, before any
other ambient was computed —
`.build/v3-generalize/PREREG_bool_L3.json`,
`sha256 = b75229e0cf19f3a593919e2793b3ef6a23bc4c166726caf31063f22e19f9a67a`.

### 4.4 Result — every prediction held, key for key

`collapse bool --level 3 --ambients 2,3,4,5,6,7,8,9,10 --check PREREG_bool_L3.json`:

| ambient | predicted total | observed | key-set SHA-256 | |
|---|---|---|---|---|
| 2 | 66 | 66 | IDENTICAL | PASS |
| 3 | 299 | 299 | IDENTICAL | PASS |
| 4 | 486 | 486 | IDENTICAL | PASS |
| 5 | 531 | 531 | IDENTICAL | PASS |
| **7** | **541** | **541** | **IDENTICAL** | **PASS** |
| **8** | **541** | **541** | **IDENTICAL** | **PASS** |
| **9** | **541** | **541** | **IDENTICAL** | **PASS** |
| **10** | **541** | **541** | **IDENTICAL** | **PASS** |

All 36 ordered ambient pairs PASS the stratified identity with `A\B = B\A = 0`,
and there are 0 level disagreements on every shared key. The width × ambient
census is a perfect step function, and nothing at all exists above width
`6 = n_min(3)`:

| width | n=2 | n=3 | n=4 | n=5 | n=6 | n=7 | n=8 | n=9 | n=10 |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 65 | 65 | 65 | 65 | 65 | 65 | 65 | 65 | 65 |
| 3 | — | 233 | 233 | 233 | 233 | 233 | 233 | 233 | 233 |
| 4 | — | — | 187 | 187 | 187 | 187 | 187 | 187 | 187 |
| 5 | — | — | — | 45 | 45 | 45 | 45 | 45 | 45 |
| 6 | — | — | — | — | 10 | 10 | 10 | 10 | 10 |
| **total** | 66 | 299 | 486 | 531 | **541** | **541** | **541** | **541** | **541** |

### 4.4a The same at level 4, pre-registered again

`n_min(4) = 8`. Small instance `.build/v3-generalize/bool_n8_L4.json`,
`sha256 = 5fa67ca89a910fdc8ff6a70713f82f2cc7c7eaa9288e3bd026df334cf83bb688`
(11 263 states, 235 s); prediction
`.build/v3-generalize/PREREG_bool_L4.json`,
`sha256 = a49960bdda4288dc9d648c724297d350287b8fdfcb2bfe1f25d7e95b680a903e`,
frozen at 13:24:49Z before any other ambient was computed.

| ambient | 8 | 9 | 10 | 11 |
|---|---|---|---|---|
| predicted | — | 11 263 | 11 263 | 11 263 |
| observed | 11 263 | 11 263 | 11 263 | 11 263 |
| keys | — | IDENTICAL | IDENTICAL | IDENTICAL |

All 6 ordered pairs PASS the stratified identity; the width census is identical
column by column (1 / 216 / 2981 / 4833 / 2490 / 637 / 90 / 15 at widths
0, 2…8) and nothing exists above width `8 = n_min(4)`.

### 4.5 Honest re-grading of this domain

`n_min(ℓ) = 2ℓ` here **is** the folklore support bound of §2.2. So this domain
demonstrates that the *framework* is correct and that Part I holds with a
degenerate root tower and an upward-monotone width — but it is **not**
independent evidence that census cutoffs are ever better than folklore. It is a
**positive control**. The substantive test is §5.

---

## 5. Domain B — prefix-reversal (pancake) sorting: the decisive test

### 5.1 Why this is the hard case

A **pancake flip** `f_k` reverses the first `k` entries of a permutation of
`[n]`; the state is a permutation reached from the identity, the level is the
number of flips. **Canonicalisation (H0):** strip the maximal already-sorted
suffix, keeping `π[1 … w]` with `w = max{ i : π(i) ≠ i }`. Width = `w`.

Two properties make this the decisive domain:

1. **No support bound exists.** A single flip `f_n` produces a state of width
   exactly `n`. So the folklore argument of §2.2 gives nothing at all here —
   the trivial bound on width after `ℓ` flips is `n` itself.
2. **Width is neither monotone up nor monotone down.** From a width-`w` state,
   `f_k` with `k > w` drags an already-sorted element to the front and raises
   the width to exactly `k`; a later flip can bring it back down. A search at
   ambient `n` genuinely has routes unavailable at ambient `m < n` that
   nevertheless *end* inside the width-`≤ m` stratum. **Part I is the claim
   that no such high-width detour is ever a shortcut** — the pre-registered
   falsification target.

H3 is degenerate here too (the root is the identity, width 0).

### 5.2 Pre-registration and result — H4 holds exactly

Small instance `.build/v3-generalize/pancake_n7_L5.json`,
`sha256 = 42e49f20aef4449a11f1ceba411b2019ffe1124259b2ed28fe751302f37055e6`
(13:02:55Z). Prediction `.build/v3-generalize/PREREG_pancake_L5.json`,
`sha256 = 6fe702f3f8c750e5132704762660a13ebac33602ed5fd0d5eb31fb64c0fa3dfb`
(13:03:59Z), registering:

> **P-A.** For every ambient `n > 7`,
> `{ s ∈ Reach(n,5) : w(s) ≤ 7 } = Reach(7,5)`, key for key (2086 keys).

**Result: P-A holds exactly.** For **all 45 ordered ambient pairs** in 3…12,
`A\B = 0`, `B\A = 0`, and **0 level disagreements** on every shared key. The
width × ambient census is a perfect step function:

| width | n=3 | n=4 | n=5 | n=6 | n=7 | n=8 | n=9 | n=10 | n=11 | n=12 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 2 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 3 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 |
| 4 | — | 18 | 18 | 18 | 18 | 18 | 18 | 18 | 18 | 18 |
| 5 | — | — | 96 | 96 | 96 | 96 | 96 | 96 | 96 | 96 |
| 6 | — | — | — | 465 | 465 | 465 | 465 | 465 | 465 | 465 |
| 7 | — | — | — | — | 1501 | 1501 | 1501 | 1501 | 1501 | 1501 |
| 8 | — | — | — | — | — | 3687 | 3687 | 3687 | 3687 | 3687 |
| 9 | — | — | — | — | — | — | 7627 | 7627 | 7627 | 7627 |
| 10 | — | — | — | — | — | — | — | 14045 | 14045 | 14045 |
| 11 | — | — | — | — | — | — | — | — | 23785 | 23785 |
| 12 | — | — | — | — | — | — | — | — | — | 37811 |
| **total** | 6 | 24 | 120 | 585 | 2086 | 5773 | 13400 | 27445 | 51230 | 89041 |

`hypotheses pancake --level 5 --ambients 5,7,9,11` separately confirms H1
directly, state by state: 120 / 2086 / 13400 states tested against ambient 11,
**0 mismatches**.

The same at **level 6**, where the detour has two more flips to exploit:
`collapse pancake --level 6 --ambients 8,10,12,14` computes 16 334 / 133 906 /
622 438 / **2 087 574** states and reports **6/6 pairs PASS**,
`A\B = B\A = 0`, 0 level disagreements, peak RSS 565 MB.

**H4 is verified, not proved.** It holds for `ℓ ≤ 5` at every ambient pair in
3…12, and for `ℓ = 6` at ambients 8, 10, 12, 14. Whether a high-width detour
can be a shortcut at some larger level is an open proof obligation; the
plausible argument — that `f_k` with `k > w` displaces `k − w` sorted elements
that must all be restored — is not a proof.

### 5.3 The tail is exactly polynomial, and the method still works

Registered in `.build/v3-generalize/PREREG_pancake_R2.json`,
`sha256 = b019a2fb4dfd1e6de67e5393803d1338292d49878b89a58233a9a05ccd81f427`,
fitted from widths ≤ 12 only:

> **R1.** `W(·, ℓ)` agrees with a polynomial in `w` of degree exactly `ℓ − 1`
> with **leading coefficient exactly `ℓ`**, for all `w ≥ ℓ + 1`:
> ```
> W(w,1) = 1
> W(w,2) = 2w − 4                                          (w ≥ 2)
> W(w,3) = 3w² − 13w + 14                                  (w ≥ 4)
> W(w,4) = 4w³ − (57/2)w² + (111/2)w − 20                  (w ≥ 5)
> W(w,5) = 5w⁴ − (160/3)w³ + (323/2)w² − (217/6)w − 296     (w ≥ 6)
> ```
> **R2.** Out-of-sample values at `w = 13, 14, 15`.
> **R3.** `W(·, 6)` is a degree-5 polynomial with leading coefficient exactly
> 6, exact for `w ≥ 7`; equivalently its 6th forward difference at `w = 7` is 0.

R3 is the strongest of the three: it extrapolates the degree law, the
coefficient law **and** the threshold law to a level that had **not been
computed at all** when the prediction was frozen. The first level-6 pancake run
in this campaign is the one that tested it.

**Every one held exactly.**

| prediction | predicted | observed | |
|---|---|---|---|
| `W(13,3)` / `W(14,3)` / `W(15,3)` | 352 / 420 / 494 | 352 / 420 / 494 | PASS |
| `W(13,4)` / `W(14,4)` / `W(15,4)` | 4 673 / 6 147 / 7 900 | 4 673 / 6 147 / 7 900 | PASS |
| `W(13,5)` / `W(14,5)` / `W(15,5)` | 52 159 / 76 585 / 108 624 | 52 159 / 76 585 / 108 624 | PASS |
| `W(13,6)` from a degree-5 fit at `w = 7…12` | 497 108 | 497 108 | PASS |
| 6th forward difference of `W(·,6)` at `w = 7` | 0 | 0 | PASS |
| leading coefficient of `W(·,6)` | 6 | 6 | PASS |

Forward-difference tables (ambient-15 level-5 run; ambient-13 level-6 run).
All trailing differences are exactly zero — the polynomiality is **exact**, not
asymptotic:

```
level 2, from w=3 : 2, 2, 0, 0, 0, …
level 3, from w=4 : 10, 14, 6, 0, 0, …
level 4, from w=5 : 45, 106, 87, 24, 0, 0, …
level 5, from w=6 : 261, 815, 1033, 580, 120, 0, 0, …
level 6, from w=7 : 1770, 6888, 11908, 10288, 4354, 720, 0
```

**The threshold `w ≥ ℓ+1` is sharp for `ℓ ≤ 6` — and is NOT a law.** Fitting
the degree-`(ℓ−1)` polynomial above the threshold and evaluating it one width
*below* gives the wrong answer at every level where the question is
non-vacuous, so `ℓ+1` is the exact onset in the measured range:

| level ℓ | threshold | polynomial at `w = ℓ` | observed at `w = ℓ` | sharp? |
|---|---|---|---|---|
| 2 | `w ≥ 3` | 0 | 0 | (polynomial already valid at `w = 2`) |
| 3 | `w ≥ 4` | 2 | 1 | **yes** |
| 4 | `w ≥ 5` | 2 | 3 | **yes** |
| 5 | `w ≥ 6` | 19 | 20 | **yes** |
| 6 | `w ≥ 7` | 136 | 133 | **yes** |

> **CORRECTION — the formula `n_stab(ℓ) = ℓ + 1` does not extend to `ℓ = 7`.**
> An independent check reports that the degree-6 polynomial for `W(·,7)`,
> fitted above `w = 8`, evaluates to **13 997** at `w = 8` while the true value
> is **13 995**, so the onset at `ℓ = 7` is `w ≥ 9 = ℓ+2`, not `ℓ+1`. I
> **independently reproduced `W(8,7) = 13 995` exactly** (ambient-13 level-7
> run, 8 223 071 states); the strata are
> `W(8..13, 7) = 13995, 78574, 284278, 796903, 1890022, 3981530`. I could
> **not** independently confirm the fitted value 13 997, because determining a
> degree-6 polynomial above `w = 8` needs widths 9…15, i.e. an ambient-15
> level-7 run, which exceeds this campaign's 5 GB / light-CPU budget.
>
> **Treat `n_stab(ℓ) = ℓ+1` as an empirical fact for `ℓ ≤ 6`, not a law.** What
> survives unqualified is (a) that `W(·, ℓ)` *is* eventually polynomial of
> degree `ℓ−1` with leading coefficient `ℓ`, and (b) that some computable
> `n_stab(ℓ)` exists — which is all the Corollary of §1.5 needs. **Nothing here
> touches Part I**, whose verification (§5.2) is a set identity, not a fit.

This is the polynomial census cutoff of §1.5 in action: **one ambient-13 run
determines the exact census at every ambient, at every level ≤ 6, forever.**

**The citable form.** Summing the strata gives a statement about a classical
object — the pancake sphere size — with no reference to our width machinery:

> **The number of permutations of `[n]` at prefix-reversal distance exactly `ℓ`
> from the identity is a polynomial in `n` of degree exactly `ℓ` with leading
> coefficient exactly `1`, valid exactly for `n ≥ ℓ + 1`.**

Verified for `ℓ ≤ 6` against `n ≤ 14` (ambient-14 level-6 run, 2 087 574
states); each fit is taken from `n ≥ ℓ+1` and reproduces every larger `n`
exactly.

| n | ℓ=1 | ℓ=2 | ℓ=3 | ℓ=4 | ℓ=5 | ℓ=6 |
|---|---|---|---|---|---|---|
| 4 | 3 | 6 | 11 | 3 | 0 | 0 |
| 6 | 5 | 20 | 79 | 199 | 281 | 133 |
| 8 | 7 | 42 | 251 | 1 191 | 4 281 | 10 561 |
| 10 | 9 | 72 | 575 | 3 963 | 22 825 | 106 461 |
| 12 | 11 | 110 | 1 099 | 9 883 | 77 937 | 533 397 |
| 14 | 13 | 156 | 1 871 | 20 703 | 206 681 | 1 858 149 |

(`ℓ=1` is `n−1`; `ℓ=2` is `(n−1)(n−2)`.)

> **This is already published, and that is the best possible outcome.** A
> prior-art sweep reports that eventual polynomiality of pancake sphere sizes
> is known, with pointers to Blanco–Buehrle–Patidar (DMTCS 2019),
> Blanco–Skora (ISSAC 2023), Homberger–Vatter (JSC 2016), Cerbai–Ferrari
> (Discrete Applied Mathematics 2020), Kaiser–Klazar and Huczynska–Vatter.
> **These citations are reported, not verified by me, and must be checked
> against the primary sources before use.** If they hold up, the correct
> framing is: *the abstract theorem of §1.3 predicts, from hypotheses checked
> mechanically in a few seconds, a polynomiality result that was proved
> independently in the permutation-patterns literature.* That is much stronger
> evidence for the method than a novel measurement would have been, and it must
> be presented as a prediction-of-known-result, never claimed as new.

### 5.4 …but H5 fails here, and that is the honest scope statement

The sorting-network tail is one state per width. The pancake tail is
`1, 4, 18, 96, 465, 1501, 3687, 7627, 14045, 23785, 37811, …`. **H5 is false
here while H0–H4 all hold**; in Boolean chains H5 fails the other way, the tail
being empty. So:

> **H5 is logically independent of H0–H4, and Part II is specific to searches
> whose root tower is bound-gated.** In sorting networks the gate is Theorem D
> (the Huffman ceiling at `cube_n` is `S(n−1) + ⌈log₂ n⌉`, so successor
> expansion at the root is not reached until level `> D(n−1)`). Neither new
> domain has anything of the kind, because neither has a non-degenerate root
> tower at all.

**State it in the paper exactly this way.** "Chain Collapse generalizes" is
false. "Ambient Collapse generalizes, and Chain Collapse is the special case in
which a *gated root tower* makes the tail trivial" is true, and is the stronger
claim, because it identifies *why* sorting networks get the clean statement.

### 5.5 The ambient-leak control — the theorem detects a `SUBSUME_WIDTHS` bug

The `bool-leak` domain adds one innocuous-looking pruning heuristic keyed to
the **root width** rather than to the state's own width — states of width
`n−3` or `n−2` are not expanded — which is exactly the shape of the real
`SORTNETOPT_SUBSUME_WIDTHS` leak (`ambient-reduction.md` §5.3). H1 is thereby
violated. The collapse breaks immediately and visibly:

| width | n=6 | n=7 | n=8 | n=9 | n=10 |
|---|---|---|---|---|---|
| 3 | **120** | 233 | 233 | 233 | 233 |
| 4 | **42** | **169** | 187 | 187 | 187 |
| 5 | **0** | 45 | 45 | 45 | 45 |
| 6 | **0** | **0** | 10 | 10 | 10 |
| **total** | **228** | **513** | 541 | 541 | 541 |

`m=6 vs n=7 : A\B = 285, B\A = 0 — FAIL`. This is the cautionary example in
executable form: **the mathematics of Part I can be perfectly true while an
implementation detail destroys its applicability**, and the collapse check is
what finds it. Any deployment of the method must run this check, not assume it.

---

## 6. The method — practical recipe

### 6.1 Seven steps

1. **Find the width.** Identify the intrinsic size `w(s)` and confirm that
   canonicalisation *drops unused dimensions*, so that a state has one name at
   every ambient (H0). If your canonical form still mentions `n` — e.g. keys
   padded to the root width — stop and fix that first; nothing else works until
   it is true.
2. **Find the free chain.** Look for a forced prefix of the search:
   `root_n → root_{n-1}` with a closed-form grade `δ(n)`, giving
   `C(n) = Σ δ(k)`. Reparameterise the cost budget as `ℓ = L − C(n)`. If the
   root has width 0, the tower is degenerate, `C ≡ 0`, and `ℓ = L`; the method
   still applies (Part I).
3. **Check H1 mechanically.** `hypotheses DOM --ambients m,n --level L`
   compares, state by state, the successors at ambient `n` restricted to width
   `≤ m` against the successors at ambient `m`. This is cheap and it is where
   implementation leaks surface.
4. **Check H4 by measurement.** Run two ambients and compare the strata
   (`collapse`). This is the hypothesis that can genuinely fail, and it is
   invisible unless width can increase along an edge. Verify it; do not assume
   it.
5. **Classify the tail.** Compute `W(w, ℓ)` at a moderate ambient and take
   forward differences in `w`. All zeros after `d+1` terms ⇒ polynomial of
   degree `d` (T-poly). All ones ⇒ trivial tail (T-trivial, H5). Nothing above
   the front ⇒ empty tail (T-empty).
6. **Beat the folklore bound, or say you have not.** Compute the support bound
   `2 ×` (number of operations at level `ℓ`) and compare with the observed
   `n_min(ℓ)`. If they coincide, the cutoff is folklore and should be presented
   as such. If the support bound exceeds `n` — as it does for sorting networks
   at every level — say so explicitly: that is the whole argument.
7. **Pre-register, then measure.** Compute the small instance, derive the
   prediction *from that file alone*, hash it, record the hash, and only then
   run the large instance. `predict` and `collapse --check` implement this;
   the check is on the SHA-256 of the sorted key list, not on counts.

### 6.2 What the method buys

Once `n_min(ℓ)` (T-empty/T-trivial) or `n_stab(ℓ) + d(ℓ) + 1` (T-poly) is
known, **one run at that ambient gives the exact census at every larger
ambient**. In this programme that turned the level-6 measurement from a
1.4 %-accurate proxy into an exact identity, moved it to the default
`MAX_CHANNELS = 11` build, and removed the "is `n = 11` representative?" risk
entirely (`ambient-reduction.md` §7). In the pancake domain it compresses an
unbounded family of BFS runs into one degree-`(ℓ−1)` polynomial per level.

### 6.3 Failure modes actually hit

| failure | symptom | fix |
|---|---|---|
| **Ambient-keyed implementation detail** (`SUBSUME_WIDTHS` at widths `{n−3, n−2}`; the `bool-leak` control) | strata differ at small ambients, agree at large ones; `A\B` concentrated at particular widths | pin the policy to **absolute widths**, never to the root width; then re-run `collapse` |
| **Scheduling nondeterminism read as ambient dependence** | Jaccard ≈ 0.99 cross-ambient, *and* ≈ 0.99 for a same-ambient repeat | run the same-ambient control (`ambient-reduction.md` §4.2b); pin the worker count; the residual goes to zero |
| **Missing H4** | a state appears at a strictly smaller level at a larger ambient | there is a high-width detour; the census is *not* ambient-free and the method does not apply |
| **Fitting a tail polynomial through saturated widths** | the fit fails out of sample | exclude widths where the stratum has saturated (in pancake, `w ≤ 5` at level 4 hold *all* `w! − (w−1)!` states) |
| **Claiming a cutoff that is the support bound** | `n_min(ℓ) = 2 ×` operation count | concede it; the domain is a control, not evidence |
| **Unstated state-space convention** | two honest reimplementations get different absolute counts while both reproduce the collapse (here: multiset-of-gate-outputs 4/37/541 vs set-of-functions 4/34/478) | publish the raw-enumeration validator alongside the counts, so the convention is executable rather than prose; the *collapse* is convention-independent, the *sequence* is not |
| **Extrapolating a threshold formula** | a clean law like `n_stab(ℓ) = ℓ+1` fitted on `ℓ ≤ 6` fails at `ℓ = 7` | fit thresholds only where you can over-determine them, and state the verified range explicitly |

---

## 7. Verdict — method or sorting-network fact?

**A method — with a narrower and better-defended perimeter than the brief
assumed.**

*What generalizes.* Part I, Ambient Collapse, is a genuine theorem about a
mechanically checkable class, and it held **exactly** — key for key, with
pre-registered SHA-256 predictions — in two non-sorting domains, one of which
(prefix reversal) has no support bound at all and a non-monotone width that
made the prediction genuinely falsifiable. The practical payoff survives in all
three tail regimes.

*What does not.* Part II, the chain tail, needs a **gated root tower** and is
specific to searches that have one. Neither new domain does. The right
statement is that Chain Collapse is the **T-trivial special case** of a
Census Cutoff theorem, and identifying the gate as its cause is a strengthening,
not a retreat.

*What the campaign added to the sorting-network result itself.* Three things.
(i) The hypothesis **H4**, which was invisible because width is monotone in
sorting networks, and which is the real content in general. (ii) The
**decisive rebuttal of the folklore objection**: because `C(n) = Θ(n log n)`,
the support bound demands `n ≥ 2(C(n)+ℓ)` and is therefore *vacuous* at every
ambient and every level — so the sorting-network cutoff cannot be the trivial
phenomenon visible in the published `|R^n_k|` table. (iii) An executable
**leak detector** for the failure mode the programme already hit once.

*What was corrected under external challenge.* **Three** claims were weakened
during this campaign; all three are recorded in place rather than buried.

1. **The novelty claim.** "No prior cutoff theorem concerns a set of states
   rather than the truth of a property" is **false** —
   Kaiser–Kroening–Wahl (CAV 2010) Def. 4 is exactly that. §2.1. The defensible
   claim is *the first **a-priori** cutoff theorem for the census of an
   exhaustive **combinatorial-optimality** search, and the first in any setting
   to give a **polynomial growth law** for that census.*
2. **The threshold formula** `n_stab(ℓ) = ℓ+1` **fails at `ℓ = 7`**. §5.3.
3. **The Boolean-chain cutoff is** the folklore support bound. §4.5.

None of the three touches Part I, whose verification is a set identity. Two
reflexes to institutionalise: whenever a census stabilises, compute the support
bound first and assume the cutoff is folklore until the arithmetic says
otherwise; and before writing "no prior work does X", have someone hunt
specifically for X stated about a *set* rather than about a *property*.

*What the architect should reconsider.*

1. **Retire "the Level Law is novel" as a headline.** Two separate repairs are
   needed. (a) The cutoff-for-a-set category is **not** empty —
   Kaiser–Kroening–Wahl owns it; use the a-priori / combinatorial-optimality /
   polynomial-growth wording of §2.1 instead. (b) What is non-trivial here is
   that the support bound is **vacuous** (§2.2) — that is the paragraph that
   carries the paper.
2. **Concede `C(n) = B(n) =` OEIS A001855 in the introduction**, not in related
   work. It is Knuth's binary-insertion number and a referee will know it.
3. **Pre-empt Harder's Lemma 53** explicitly, and pre-empt the `|R^n_k|` table
   of Codish et al. by printing it yourself.
4. **Do not claim representation stability as a parent theorem**, and do not
   write "FI theory predicts this". The linear chain tail means the family is
   not an RSW-style finitely generated FI-set; worse, `S_n` is provably not a
   finitely generated FI-set, so Ramos–White does not even apply to the pancake
   domain (§2.4). Borrow *stable orbits*; claim the effective threshold as the
   delta — it beats the best published effective bounds by roughly 2×.
   Also fix the venue: *Algebraic Combinatorics* (Centre Mersenne) 2020, **not**
   Springer's *Journal of Algebraic Combinatorics*.
5. **The pancake polynomial law is reportedly already published** (§5.3). Do
   not write it up as new. Write it up as *the abstract theorem predicting a
   known theorem in another field from mechanically checked hypotheses* — that
   is the single strongest piece of evidence in this document that the class
   definition has content. Verify the reported citations against primary
   sources first.
6. **Cite Goucher (2023) for the Boolean-chain method** and check OEIS A121080
   before publishing the sequence 1, 4, 37, 541 (§2.5).
7. **Adopt the pre-registration + brute-force-validation protocol** (§3, §4.2a)
   as standard for any future census claim in this programme. It caught a
   convention ambiguity (set vs. multiset states) that two external
   reimplementations also hit, and it is what makes the "exactly" in these
   results defensible.

---

## 8. Reproduction

```
# hypotheses of the sorting-network instance, independent of the Rust engine
python3 tools/verify_level_law_general.py sortnet-theorems --max-n 6

# Boolean chains: brute force (canon is a COMPLETE invariant), the modelling
# lemma, and the no-shortcut full-ambient control
python3 tools/verify_level_law_general.py bool-bruteforce --ambients 4,5,6 --level 3
python3 tools/verify_level_law_general.py bool-fresh-lemma --ambient 6 --level 2 --caps 3,4
python3 tools/verify_level_law_general.py collapse bool-full --level 2 --ambients 4,5,6,7,8
python3 tools/verify_level_law_general.py census   bool --ambient 6 --level 3 --out .build/v3-generalize/bool_n6_L3.json
python3 tools/verify_level_law_general.py predict  bool --source .build/v3-generalize/bool_n6_L3.json \
        --ambients 2,3,4,5,7,8,9,10 --out .build/v3-generalize/PREREG_bool_L3.json
python3 tools/verify_level_law_general.py collapse bool --level 3 --ambients 2,3,4,5,6,7,8,9,10 \
        --check .build/v3-generalize/PREREG_bool_L3.json

# the ambient-leak control (models SORTNETOPT_SUBSUME_WIDTHS)
python3 tools/verify_level_law_general.py collapse bool-leak --level 3 --ambients 6,7,8,9,10

# Boolean chains at level 4
python3 tools/verify_level_law_general.py census   bool --ambient 8 --level 4 --out .build/v3-generalize/bool_n8_L4.json
python3 tools/verify_level_law_general.py predict  bool --source .build/v3-generalize/bool_n8_L4.json \
        --ambients 6,7,9,10,11 --out .build/v3-generalize/PREREG_bool_L4.json
python3 tools/verify_level_law_general.py collapse bool --level 4 --ambients 8,9,10,11 \
        --check .build/v3-generalize/PREREG_bool_L4.json

# prefix reversal: H1 directly, then the collapse over 45 ambient pairs
python3 tools/verify_level_law_general.py hypotheses pancake --level 5 --ambients 5,7,9,11
python3 tools/verify_level_law_general.py collapse   pancake --level 5 --ambients 3,4,5,6,7,8,9,10,11,12
python3 tools/verify_level_law_general.py collapse   pancake --level 6 --ambients 8,10,12,14 --cap 4000000
```

Everything above is pure Python 3, single-threaded, and the largest run in this
list (prefix reversal, ambient 14, level 6, 2 087 574 states) peaks at **565 MB**
and 4.5 s. The largest run in the campaign is the ambient-13 level-7 pancake
census of §5.3 (8 223 071 states).

**All fourteen commands above were re-executed end to end from a clean shell
and every one exited 0**, reproducing 541 / 11 263 / 89 041 / 2 087 574 and all
PASS rows (`.build/v3-generalize/OUT_repro_check.txt`; the re-run wrote its
artefacts with a `_repro` suffix so the pre-registration audit trail of §3 is
untouched). The re-run's census files are **byte-identical** to the originals —
e.g. `bool_n8_L4_repro.json` has the same
`sha256 = 5fa67ca8…f83bb688` as `bool_n8_L4.json` — so the whole pipeline is
deterministic, and the prediction files differ only in their embedded
timestamp, with every key-set hash unchanged. That closes the determinism gap
that cost `ambient-reduction.md` §4.2 a whole round of re-measurement.

Artefacts, all under `.build/v3-generalize/`: `bool_n6_L3.json`,
`bool_n8_L4.json`, `pancake_n7_L5.json`, `PREREG_bool_L3.json`,
`PREREG_bool_L4.json`, `PREREG_pancake_L5.json`, `PREREG_pancake_R2.json`,
`OUT_bool_collapse_L3.txt`, `OUT_bool_bruteforce.txt`,
`OUT_pancake_collapse_L5.txt`, `OUT_pancake_collapse_L6.txt`,
`OUT_pancake_R2_verify.txt`, `OUT_sortnet_ambient_recheck.txt`.
