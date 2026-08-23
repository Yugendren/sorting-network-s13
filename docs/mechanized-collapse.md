# The Collapse Theorem, Mechanized — exactly what is and is not machine-checked

**Date:** 2026-08-23.
**Artefact:** `tools/verified/Ambient_Collapse.thy` (1 095 lines, Isabelle2020,
**no `sorry`, no `oops`, no `axiomatization`**), session `Ambient_Collapse`
declared in `tools/verified/ambient/ROOT`, built by
`tools/verified/build_ambient.sh`. Session build time **≈ 2 s** on top of a
prebuilt HOL heap.
**Scope:** read-only with respect to `src/`, `evidence/`, `config/`, `ledger/`,
`checker/`, the pinned clone, and every frozen theory. New files: this
document, `tools/verified/Ambient_Collapse.thy`,
`tools/verified/ambient/ROOT`, `tools/verified/build_ambient.sh`, one inert
comment appended to `tools/verified/ROOT`, and scratch under `.build/v3-mech/`.
No commits. No candidate network was constructed and no witness exists
anywhere in this work.

---

## 0. Verdict in one table

| claim | status | where |
|---|---|---|
| The abstract class of `level-law-general.md` §1.1 can be formalized | **YES**, as an Isabelle locale | `graded_ambient_search` |
| **Part I (Ambient Collapse)** | **MACHINE-CHECKED** | `graded_ambient_search.ambient_collapse` |
| Equality of *levels* on shared states | **MACHINE-CHECKED** | `graded_ambient_search.level_agree` |
| "Each stratum is a function of `(w, ℓ)` alone, no dependence on `n`" | **MACHINE-CHECKED** | `graded_ambient_search.census_stratified` |
| **Part II (Chain Collapse)** | **MACHINE-CHECKED** | `gated_ambient_search.chain_collapse` |
| `\|Reach(n,ℓ)\| = \|Reach(n_min,ℓ)\| + (n − n_min)` | **MACHINE-CHECKED** | `gated_ambient_search.chain_collapse_card` |
| **Corollary of §1.5 (polynomial census cutoff)** | **MACHINE-CHECKED** | `graded_ambient_search.census_growth_law` |
| T-trivial ⇒ census eventually affine with slope 1 | **MACHINE-CHECKED** | `gated_ambient_search.census_affine` |
| Newton expansion (vanishing differences ⇒ a polynomial) | **MACHINE-CHECKED** | `newton_expansion` |
| The hypotheses are satisfiable and the theorems non-vacuous | **YES — two interpretations, all obligations discharged** | `Words`, `Tower`/`Gated` |
| **Part I needs H3** (contrary to `level-law-general.md` §1.3's summary line) | **ESTABLISHED by the mechanization** | §3.1 below |
| **H4 as printed in §1.2 is ill-formed for a non-degenerate tower** | **ESTABLISHED**; repaired form used | §3.2 below |
| The sorting-network search satisfies H0–H5 | **NOT MECHANIZED. Unchanged.** | §4.1 |
| The abstract census `d_n(root,·) ≤ C(n)+ℓ` models the engine's stored set | **NO — and this is a real gap in the class definition** | §4.2 |
| Boolean-chain / prefix-reversal instances | **NOT MECHANIZED** (Python-checked only) | §4.3 |
| Pancake polynomiality (degree `ℓ`, leading coefficient `1`) | **NOT PROVED**; upper bound proved, lower bound open | §5 |

**One-sentence summary for the paper.** *The abstract collapse theorem — both
parts, the level-equality clause, and the polynomial growth corollary — is now
machine-checked in Isabelle2020 with no `sorry`, together with two
interpretations that discharge every hypothesis; what is **not** machine-checked
is that the sorting-network search is an instance, which continues to rest on
the implementation audit of `ambient-reduction.md` §2–§3.*

---

## 1. What the theory contains

`tools/verified/Ambient_Collapse.thy` is self-contained: it `imports Main` and
nothing else. It never reads, imports, or rebuilds `Checker.thy`,
`Huffman.thy`, `Sorting_Network.thy`, `Sorting_Network_Bound.thy`,
`Checker_Codegen.thy` or `Prefix_Checker.thy`. `tools/verified/ROOT` is
byte-identical apart from an appended comment, so `tools/verified/build.sh`
and the `snocheck2` pipeline are unaffected (verified: §6).

### 1.1 Graded walks

```isabelle
inductive pathg  :: "('s ⇒ 's ⇒ bool) ⇒ ('s ⇒ 's ⇒ nat) ⇒ 's ⇒ 's ⇒ nat ⇒ bool"
inductive pathgB :: "('s ⇒ 's ⇒ bool) ⇒ ('s ⇒ 's ⇒ nat) ⇒ ('s ⇒ bool)
                     ⇒ 's ⇒ 's ⇒ nat ⇒ bool"
```

`pathg E G s t g` is a walk of total grade exactly `g`; `pathgB` adds a
predicate every state on the walk must satisfy (used for width confinement).
The census is defined by an *inequality* on the grade, so the γ-weighted
distance never has to be constructed and there is no partiality:

```isabelle
Reach n l = {s. ∃g. pathg (edge n) grade (root n) s g ∧ g ≤ C n + l}
```

This is definitionally equal to `{s : d_n(root_n, s) ≤ C(n) + ℓ}` whenever the
distance exists, and is total when it does not.

### 1.2 The locale

```isabelle
locale graded_ambient_search =
  fixes width :: "'s ⇒ nat"
    and edge  :: "nat ⇒ 's ⇒ 's ⇒ bool"
    and grade :: "'s ⇒ 's ⇒ nat"
    and root  :: "nat ⇒ 's"
    and C     :: "nat ⇒ nat"
  assumes H1:       "⟦width s ≤ m; m ≤ n⟧ ⟹
                       {t. edge n s t ∧ width t ≤ m} = {t. edge m s t}"
      and H3_width: "width (root m) ≤ m"
      and H3_mono:  "m ≤ n ⟹ C m ≤ C n"
      and H3_tower: "m ≤ n ⟹ pathg (edge n) grade (root n) (root m) (C n - C m)"
      and H4:       "⟦m ≤ n; width s ≤ m; pathg (edge n) grade (root n) s g⟧ ⟹
                       ∃g'. pathgB (edge n) grade (λt. width t ≤ m) (root m) s g'
                            ∧ (C n - C m) + g' ≤ g"
```

**H0 and H2 are discharged structurally and cannot be violated by any
interpretation.** H0 (ambient-free naming) is the fact that the states inhabit
one type `'s` that does not mention `n`: a state has one and the same name at
every ambient *by construction*. H2 (ambient-free grading) is the fact that
`grade` has type `'s ⇒ 's ⇒ nat` — it takes no ambient argument. This is
stronger than a hypothesis: it is a signature constraint, and it is the honest
formal content of "canonicalisation quotients away the unused dimensions".

**H1 is transcribed verbatim** from §1.2 as a set equality. The mechanization
extracts its three consequences separately (`H1_down`, `H1_up`, `H1_bound`);
note that `H1_bound` — "an ambient-`m` edge out of a width-`≤ m` state lands in
width `≤ m`" — is *implied* by the set equality and was never stated explicitly
in the prose, but is used twice.

### 1.3 The theorems, verbatim

```isabelle
theorem ambient_collapse:              (* Part I *)
  "m ≤ n ⟹ Reach n l ∩ {s. width s ≤ m} = Reach m l"

corollary level_agree:
  "⟦m ≤ n; width s ≤ m⟧ ⟹ level n s = level m s"        (* level = LEAST l. s ∈ Reach n l *)

theorem census_stratified:
  "Reach n l = (⋃v≤n. stratum v l)"                     (* stratum v l = {s ∈ Reach v l. width s = v} *)

theorem chain_collapse:                (* Part II *)
  "nmin l ≤ n ⟹ Reach n l = Reach (nmin l) l ∪ root ` {v. nmin l < v ∧ v ≤ n}"

theorem chain_collapse_card:
  "⟦nmin l ≤ n; finite (Reach (nmin l) l)⟧ ⟹
     card (Reach n l) = card (Reach (nmin l) l) + (n - nmin l)"

theorem census_growth_law:             (* Corollary of §1.5 *)
  "⟦⋀v. finite (stratum v l);
    ⋀v. v0 ≤ v ⟹ (fdiff ^^ Suc d) (λv. strat_size v l) v = 0⟧ ⟹
     ∃c. ∀t. census (v0 + t) l = (∑j≤Suc d. c j * int (t choose j))"

theorem census_affine:                 (* T-trivial regime *)
  "⟦⋀v. finite (stratum v l); nmin l ≤ n⟧ ⟹ fdiff (λn. census n l) n = 1"
```

`census_stratified` is the mechanized form of Part I's "equivalently" clause:
`Reach(n,ℓ)` is the disjoint union of strata each of which is *defined* at its
own ambient and therefore carries no `n` at all. That is the statement a
referee will want, and it is a one-line consequence of `ambient_collapse`
applied at `m := width s`.

### 1.4 The growth law is stated in forward-difference form, then converted

`fdiff f n = f (Suc n) − f n` over `ℤ`. `census_growth_law` says: if the
`(d+1)`-st forward difference of the width strata vanishes from `v0` on, then
the census agrees, from `v0` on, with

```
census (v0 + t) = ∑_{j ≤ d+1} c_j · C(t, j)
```

for integer constants `c_j`. The binomial basis `C(t,j)` *is* a polynomial
basis (`C(t,j)` has degree exactly `j` in `t`, leading coefficient `1/j!`), so
this is exactly "the census agrees with a polynomial of degree `≤ d+1`". The
conversion is `newton_expansion`, proved constructively by telescoping and the
hockey-stick identity `∑_{u<t} C(u,j) = C(t, j+1)`.

Two reasons for the difference form rather than `HOL-Computational_Algebra`
polynomials. First, "eventually polynomial of degree `≤ d`" and "the `(d+1)`-st
forward difference eventually vanishes" are equivalent, and the difference form
is what `verify_level_law_general.py` and `level-law-general.md` §5.3 actually
measure — the forward-difference tables. Second, the difference form makes
`census_affine` (T-trivial) literally the `d = 0` case of `census_growth_law`,
which is the unification the paper wants: **T-trivial and T-poly are one
theorem at two degrees.**

---

## 2. The two interpretations (non-vacuity)

Both discharge **every** locale obligation. Neither is a formalization of any
real domain; both are the smallest honest models that exercise the hypotheses.

### 2.1 `Words` — degenerate tower, non-monotone width

States are `nat list`; the ambient `n` is the alphabet size; `wwidth xs` is the
least alphabet containing `xs`. Two moves, each of grade 1: **append** a letter
`a < n`, and **drop** the last letter. `wroot n = []`, `wC ≡ 0` (degenerate
tower). Machine-checked:

```isabelle
Words.Reach n l = {xs. set xs ⊆ {..<n} ∧ length xs ≤ l}
Words.Reach 2 (Suc 0) ⊂ Words.Reach 3 (Suc 0)      (* the ambient really matters *)
wedge 3 [] [2] ∧ wwidth [] < wwidth [2]            (* an edge that RAISES width *)
wedge 3 [2] [] ∧ wwidth [] < wwidth [2]            (* an edge that LOWERS width *)
```

The point of this interpretation is that **H4 has content here and is a
theorem, not a triviality**: width is neither monotone up nor monotone down, so
an ambient-`n` search genuinely has routes unavailable at a smaller ambient
that nevertheless end inside the width-`≤ m` stratum. H4 is discharged from the
fact that every move changes the length by exactly one and costs exactly one,
so a word of length `k` cannot be reached in fewer than `k` moves however far
the walk climbs in between — the "no high-width detour is a shortcut"
statement, proved.

`Words` is also the T-poly regime in miniature: its width-`v` stratum at level
`l` is `∑_{k≤l} (v^k − (v−1)^k)`, a polynomial in `v` of degree `l−1` with
leading coefficient `l`. **That is exactly the degree and leading coefficient
the pancake domain exhibits** (`level-law-general.md` §5.3). See §5.2.

### 2.2 `Tower` / `Gated` — non-degenerate gated root tower, Part II

`datatype tstate = Tow nat | Off nat`, both of width equal to their index. The
chain `Tow n → Tow (n−1) → …` has grades `δ(k)`, giving the free chain
`C n = ∑_{k≤n} δ k`. Each `Tow k` has exactly one off-chain successor `Off k`
of the *same* width, reachable only at grade `C k + D k + 1`. With `D` monotone
and unbounded, `nmin l = (LEAST k. l ≤ D k)` and H5 holds. Machine-checked:

```isabelle
Tower.Reach n l = Tow ` {..n} ∪ Off ` {j. j ≤ n ∧ l > D j}
card (Tower.Reach n l) = card (Tower.Reach (tnmin l) l) + (n - tnmin l)
fdiff (λn. Tower.census n l) n = 1        for n ≥ tnmin l
```

This is the abstract skeleton of the sorting-network instance: a
non-degenerate root tower with a closed-form free chain, and a *bound-gated*
off-chain successor. `tower_data` is shown consistent by the interpretation
`TowerEx` (`δ ≡ 1`, `D = id`, giving `tnmin l = l`).

**It is a model of the hypotheses with the same chain structure as the
sorting-network search. It is not, and does not claim to be, a formalization of
that search.** In particular the gate is *postulated* here (by giving the
off-chain edge grade `C k + D k + 1`); in the real search it is *derived*
from the Huffman ceiling (`ambient-reduction.md` Theorem D), and that
derivation is not mechanized.

---

## 3. Three corrections the mechanization forced

These are findings, not cosmetics. All three should be applied to
`docs/level-law-general.md` and to `audit-paper-v2.md` §6.

### 3.1 Part I needs H3. The summary sentence in §1.3 is wrong.

`level-law-general.md` §0 and §1.3 both assert *"Part I uses neither H3 nor
H5"* and *"Part I (Ambient Collapse) needs H0, H1, H2, **H4**"*. **That
contradicts the document's own step table five lines above**, which attributes
two Part-I steps to H3 ("initial segment is the root tower, grade `C(n) − C(m)`"
and "converse direction: H1, H2, **H3**"). The mechanization settles it: H3 is
genuinely required, and in both directions.

*Why.* Part I relates the ambient-`n` distance from `root_n` to the ambient-`m`
distance from `root_m`. Without a hypothesis saying how to get from `root_n` to
`root_m` and at what cost, the two roots are unrelated objects and the two
distances cannot be compared. In the mechanization H3 appears twice: as
`H3_tower` in the converse direction (prepend the tower) and inside the
statement of H4 in the forward direction (the tower prefix is what the `C n −
C m` term accounts for).

*What survives, and how to say it.* The correct statement is not "Part I is
independent of H3" but **"Part I is independent of H5, and holds with a
*degenerate* root tower"** — which is what the Boolean-chain and pancake
experiments actually demonstrate, and what the `Words` interpretation
machine-checks (`wC ≡ 0`, `wroot n = []`, H3 discharged trivially). Recommended
replacement wording:

> Part I needs H0, H1, H2, H3 and H4, but H3 may be *degenerate* (`root_n` of
> width 0 and `C ≡ 0`), in which case it is vacuous. Part II additionally needs
> H3 to be *non-degenerate* and H5 to hold. The split is therefore between the
> hypotheses that make the tail trivial (H3-non-degenerate + H5) and everything
> else, not between H3 and the rest.

### 3.2 H4 as printed is ill-formed when the tower is non-degenerate.

§1.2 reads:

> **H4 (width convexity).** For every `s` with `w(s) ≤ m` and every `n ≥ m`,
> some `γ`-geodesic `root_n ⇝ s` passes only through states of width
> `≤ max(m, w(root_m))`.

When the tower is non-degenerate, `w(root_n) = n > m`, and `root_n` is itself a
state on every geodesic `root_n ⇝ s`. So the condition as written is
**unsatisfiable in exactly the case the sorting-network instance is in** — the
only case in which the whole document says the hypothesis is interesting for
Part II. (It is satisfiable in the two degenerate-tower domains, which is why
the Python checks never caught it.)

The mechanized repair is the *decomposition* form quoted in §1.2 above: every
ambient-`n` walk to a state of width `≤ m` can be replaced, **at no greater
grade**, by (the root tower down to `root_m`, of grade `C n − C m`) followed by
(a walk confined to width `≤ m`). This is precisely what the informal proof of
Part I does in its first two steps, fused into one hypothesis. Print the
decomposition form; the `max(m, w(root_m))` form is not repairable by adjusting
the bound.

**Be candid about what this costs.** H4-as-decomposition is the hypothesis that
carries the mathematical weight of Part I. The mechanization proves the
*transport* (that a width-confined ambient-`n` walk is an ambient-`m` walk of
the same grade, and conversely) and the *bookkeeping* (that the levels line up
under `C n − C m`); it does not prove H4 for any real domain. In the two
interpretations H4 is discharged, and in `Words` it is discharged
non-trivially. In sorting networks it is asserted to be free from width
closure; in prefix reversal `level-law-general.md` §5.2 states plainly that it
is "verified, not proved". None of that changes.

### 3.3 H5 is better stated at the small ambient.

§1.2 states H5 as a property of the stratum `W(w, ℓ)`, which reads as a
property of the *large* search. The mechanization states it at ambient `v`
itself —

```isabelle
H5: "nmin l < v ⟹ stratum v l = {root v}"      (* stratum v l = {s ∈ Reach v l. width s = v} *)
```

— and lets Part I lift it to every larger ambient. This is strictly weaker as a
hypothesis and strictly stronger as a theorem, and it makes the mechanized
Part II a genuine derivation rather than a restatement. It also exposes a
consequence that was implicit: **H5 forces `w(root v) = v` above the
threshold**, i.e. H5 cannot hold with a degenerate tower unless the strata are
empty — which is exactly the "the only domain with a non-degenerate root tower
is the only domain with a trivial tail" observation of §1.6, now derived rather
than observed.

---

## 4. What is NOT mechanized, and why

### 4.1 That the sorting-network search is an instance. Unchanged.

**This campaign does not close the weakness recorded in
`docs/final-review-internal.md` and `audit-paper-v2.md` §6.** Theorem 12's
delegation step still rests on the ambient-freedom property of the
implementation, established by exhaustive reading of `Search::improve`,
`improve_huffman` and `Edges::improve_next` plus a second reviewer's audit —
**not by machine check**. Mechanizing that would require formalizing
`OutputSet`, `canon.rs`, the Huffman bound and the DP's control flow, which is
out of scope by an order of magnitude.

What *has* changed is the shape of the residual risk. Before: "an abstract
theorem, proved on paper, resting on an unverified implementation property."
After: "a machine-checked abstract theorem, plus an unverified claim that one
concrete search satisfies its five hypotheses." The second is a much smaller
and much better-localised obligation, and it is stated as five checkable
properties rather than as one prose argument. Say exactly that; do not say the
collapse theorem "is now verified for sorting networks".

### 4.2 The class definition does not literally model the engine — a real gap.

This is the most important thing found, and it should be fixed in the paper
rather than left for a referee.

`level-law-general.md` §1.1 defines the census as a **ball in the γ-weighted
distance**:

```
Reach(n, ℓ) = { s ∈ S : d_n(root_n, s) ≤ C(n) + ℓ }
```

The sorting-network `Reach` is **the set of states the engine stores**, which is
not that ball. Concretely: `γ` is 1 per comparator, so `d_13(cube_13, s_13) = 1`
where `s_13 = canon(cube_13 ▷ [i,j])` is the unique width-13 successor
(Theorem C). Under the ball definition `s_13 ∈ Reach(13, 1)`. But the measured
level-1 census at `n = 13` (`ambient-reduction.md` §4.3) has **exactly one**
state at width 13, namely `cube_13`. So `s_13 ∉ Reach(13,1)`, and the ball
definition and the engine's census disagree at level 1.

The reason is that `improve` tries the Huffman branch first and reaches
successor expansion only when `huffman_bounds[1] ≤ bounds[0]` — the gate of
Theorem D. The engine's census is the reachable set of a **bound-gated**
recursion, and the gate depends on the level, which the class definition
forbids (an `n`-free, ℓ-free `→`).

**Consequences, in order of importance.**

1. The abstract theorem, as mechanized, is a theorem about distance-ball
   censuses. It is exactly right for the Boolean-chain and prefix-reversal
   domains, whose Python implementations *are* BFS balls.
2. For the sorting-network instance the abstract theorem is a *guide*, not a
   proof: Theorem E is proved separately in `ambient-reduction.md` §3.5 by an
   argument that uses the gate directly. The paper must not present Theorem 12
   as a corollary of the abstract theorem. As far as I can tell it currently
   does not — but §6 places them adjacently and a reader will assume it.
3. The `Tower` interpretation is the honest bridge: it reproduces the gate by
   pricing the off-chain edge at `C k + D k + 1`, which turns a level-dependent
   *control-flow* gate into a level-independent *grade*. That is a faithful
   encoding of the gate's effect on the census, and it is why `Tower` satisfies
   H5. Whether the real engine's gate admits such a re-grading in general is
   **not established**; it is established for the two out-edges of `cube_k`,
   which is all Theorem E needs.

Recommended sentence for the paper: *the abstract class models an exhaustive
search whose stored set is a ball in a level-independent grading; the
sorting-network search stores a bound-gated subset of that ball, and Theorem 12
is proved directly from the gate rather than as an instance of the abstract
theorem.*

### 4.3 The two second-domain instances.

Boolean chains and prefix reversal are checked by
`tools/verify_level_law_general.py` (Python, with a brute-force validator for
the Boolean domain) and are **not** formalized. Formalizing prefix reversal
would in particular require proving H4 for it, which
`level-law-general.md` §5.2 records as an open proof obligation.

### 4.4 Finiteness.

`chain_collapse_card`, `census_step`, `census_growth_law` and `census_affine`
all take finiteness of the strata as an explicit hypothesis. It is discharged
in both interpretations (`Words_stratum_finite`, `Tower_stratum_finite`).
Nothing in H0–H5 implies it.

---

## 5. The growth law — verdict

Two different statements travel under the name "polynomial growth law" in
`level-law-general.md` §2.1 and `audit-paper-v2.md` §6 (line 568, *"and in
supplying a polynomial growth law"*). **They must be separated in the paper.**
A third reading — growth in the *level* — is not a law at all.

All numbers below are machine-checked in exact rational arithmetic by
`.build/v3-mech/check_growth.py` against every census figure in the repository
(sorting networks `n = 6…13`, `ℓ = 1…6` including the certified `n = 11`
level-6 figure 95 221 143; pancake `ℓ ≤ 7`; Boolean chains `ℓ ≤ 4`).

### 5.1 Growth in the ambient `n`, T-trivial (sorting networks): **PROVEN, and it is affine, not polynomial**

`|Reach(n,ℓ)| = |Reach(n_min(ℓ),ℓ)| + (n − n_min(ℓ))` is **derived** — Theorem E
of `ambient-reduction.md` §3.5, Theorem 12 of the paper — subject to that
theorem's three scopings. The abstract half is now machine-checked
(`chain_collapse_card`, `census_affine`).

Machine-checked against all data: at levels 1, 2, 3, 4 the census over
`n = 6…13`, `7…13`, `9…13`, `9…13` is an arithmetic progression with common
difference **exactly 1** (second difference identically 0), and every ambient in
range satisfies `n ≥ n_min(ℓ)`. At levels 1–5 the width census at `n = 13` has
**exactly one** state at every width strictly above `n_min(ℓ)`.

Two honest caveats the paper must carry:

* **Levels 5 and 6 have exactly one measured ambient each** (`n = 13` and
  `n = 11`). A single point cannot exhibit a common difference. The affine law
  at those levels is supported only by the width-stratum evidence (widths 12
  and 13 hold one state each at level 5) — which is strong, but is not the same
  test.
* `|Reach(13,6)| = 95 221 145` is a **prediction** of Theorem E from the single
  `n = 11` measurement, not a measurement.

**Wording.** Degree 1 is a polynomial, so "polynomial growth law" is not false,
but it oversells. Write **"an explicit *affine* growth law: `const + (n −
n_min)`"** for the sorting-network case, and reserve "polynomial" for §5.2.
The distinction from KKW10 (*exact equality with no growth term*) is fully
carried by "affine with slope exactly 1"; nothing is lost.

### 5.2 Growth in the ambient `n`, T-poly (prefix reversal): **FITTED, with a proven upper bound and an explained leading term**

The claim of `level-law-general.md` §5.3 is that the width stratum `W(·, ℓ)` is
a polynomial in `w` of degree exactly `ℓ−1` with leading coefficient exactly
`ℓ`, for `w ≥ ℓ+1`; summing gives `|Reach(n,ℓ)|` of degree `ℓ` in `n`. The
citable form is that the number of permutations of `[n]` at prefix-reversal
distance exactly `ℓ` from the identity is a polynomial in `n` of degree exactly
`ℓ` with leading coefficient exactly `1`.

**Status: fitted, not derived.** What is now established:

| statement | status |
|---|---|
| `census_growth_law`: strata polynomial of degree `d` from `v0` ⟹ census polynomial of degree `d+1` from `v0` | **MACHINE-CHECKED** (Isabelle) |
| the fits themselves reproduce every out-of-sample point exactly | **MACHINE-CHECKED** (exact rationals) |
| `sphere_ℓ(n) ≤ (n−1)^ℓ`, hence degree `≤ ℓ` and leading coefficient `≤ 1` | **PROVED** (trivially: a distance-`ℓ` permutation is a word of `ℓ` non-identity prefix reversals, of which there are `n−1`); holds at every data point |
| `sphere_ℓ(n) ≥ n^ℓ − O(n^{ℓ−1})`, hence leading coefficient `≥ 1` | **OPEN** |
| eventual polynomiality itself | **OPEN here**, and reportedly already published elsewhere (§5.3 of `level-law-general.md`) |

**Residuals and range, precisely.** Per-level strata `W(w,ℓ)` are available only
for `w ≤ 7` from the ambient-7 level-5 census, so:

| level `ℓ` | fit points | out-of-sample points | residuals | degree | leading coeff |
|---|---|---|---|---|---|
| 1 | 1 (`w=2`) | 5 (`w=3…7`) | all 0 | 0 ✓ | 1 ✓ |
| 2 | 2 (`w=3,4`) | 3 (`w=5,6,7`) | all 0 | 1 ✓ | 2 ✓ |
| 3 | 3 (`w=4,5,6`) | 1 (`w=7`) | 0 | 2 ✓ | 3 ✓ |
| 4 | — | — | not fittable from `w ≤ 7` | — | — |
| 5 | — | — | not fittable from `w ≤ 7` | — | — |

The degree/leading-coefficient law is therefore **out-of-sample confirmed only
for `ℓ ≤ 3`** from the strata I could re-derive here; levels 4–6 rest on the
wider-ambient runs reported in `level-law-general.md` §5.3 (whose forward
difference tables I reproduce below and which are internally consistent).

Cumulative checks over the full width range *are* decisive and are all exact:

* level `≤ 5`, widths 6…12: 5th forward difference `0, 0`; 4th difference
  constant `120 = 5·4!` ⇒ degree 4, leading coefficient 5.
* level `≤ 5`, totals `n = 6…12`: 6th difference `0`; 5th difference constant
  `120 = 1·5!` ⇒ degree 5, leading coefficient 1. This is `census_growth_law`
  happening on real data.
* level `≤ 6`, widths 7…14: 6th difference `0, 0`; 5th difference constant
  `720 = 6·5!` ⇒ degree 5, leading coefficient 6.
* the strata re-sum to the reported totals 16 334 / 133 906 / 622 438 /
  2 087 574 exactly.

Sphere sizes: for `ℓ = 1,2,3` the degree-`ℓ` leading-coefficient-1 fit
reproduces every out-of-sample `n` exactly (4/3/2 points respectively); for
`ℓ = 4` the five available even ambients exactly determine the degree-4
polynomial with leading coefficient 1 but leave **zero** out-of-sample points,
so `ℓ = 4` is *fitted, not tested*; `ℓ = 5, 6` cannot be fitted from `n ≤ 14` at
even `n` only. The ratio `sphere_ℓ(n)/(n−1)^ℓ` rises monotonically toward 1 at
every level (e.g. `ℓ = 3`: 0.4074, 0.6320, 0.7318, 0.7888, 0.8257, 0.8516 at
`n = 4…14`), consistent with — and the only evidence for — leading coefficient
exactly 1.

**The `Words` interpretation explains the degree and the leading coefficient,
and this is worth a paragraph in the paper.** In the trivial word model — `ℓ`
operations, each introducing at most one fresh dimension, `n` choices per
operation — the width-`v` stratum at level `ℓ` is `∑_{k≤ℓ}(v^k − (v−1)^k)`,
a polynomial of degree `ℓ−1` with leading coefficient exactly `ℓ`, and the
sphere at distance exactly `ℓ` has size `n^ℓ`, of degree `ℓ` with leading
coefficient exactly `1`. **These are the pancake law's degree and leading
coefficient, produced by a model with no pancake content whatsoever.** The
correct reading is therefore *deflationary and should be stated as such*: the
degree and the leading coefficient are what you get from counting `ℓ`-letter
words over an `n`-letter alphabet, and the content of the pancake result is the
much sharper claim that the count is *exactly* that polynomial *from a
threshold*, with only `O(n^{ℓ−1})` words colliding. The upper bound `(n−1)^ℓ`
proves the "at most" half; the "at least" half is the open part and is where any
real theorem would live.

**Wording.** *"a polynomial growth law for the census"* is defensible **only**
for the prefix-reversal domain and **only** as a conjecture supported by exact
out-of-sample fits, not as a theorem. What is a theorem is the *conditional*:
polynomial strata ⇒ polynomial census, one degree higher — and that is now
machine-checked. Recommended:

> The census obeys a growth law that is affine in the ambient in the gated case
> (Theorem 12) and, conditionally on the width strata being eventually
> polynomial, polynomial of one degree higher in general (Corollary, machine-
> checked). In the prefix-reversal domain the strata are observed to be exactly
> polynomial of degree `ℓ−1` with leading coefficient `ℓ` from `w ≥ ℓ+1`
> (`ℓ ≤ 6`; the threshold formula fails at `ℓ = 7`); we prove the matching upper
> bound and leave the lower bound open.

Do **not** write "the first in any setting to give a polynomial growth law for
that census" without this qualification: the only *proved* growth law is affine.

### 5.3 Growth in the level `ℓ`: **not a law, and must never be conflated with the above**

`|Reach(n_min(ℓ), ℓ)|` for `ℓ = 1…6` is

```
33,  445,  24 199,  207 995,  50 602 869,  95 221 143
```

with successive ratios `13.48, 54.38, 8.60, 243.29, 1.88` — a spread of 241×.
No forward difference of orders 1–5 vanishes anywhere in the measured range.
The alternation is structural (the ratio is large exactly when `n_min` jumps and
small when it does not), but it is emphatically **not polynomial**, and no
bound better than the existing 33×–246× per-level bracket
(`ambient-reduction.md` §8.2) follows from anything in this campaign. Any
sentence about "polynomial growth of the census" must say *in the ambient*.

### 5.4 The `n_stab(ℓ) = ℓ+1` sharpness table reproduces exactly

"The threshold `w ≥ ℓ+1` is sharp" means the fitted polynomial, evaluated one
width *below* its stated range, **disagrees** with the observed value.
`check_growth.py` reproduces `level-law-general.md` §5.3's table cell for cell
on the two levels evaluable from the ambient-7 data:

| level `ℓ` | threshold | polynomial at `w = ℓ` | observed at `w = ℓ` | sharp? |
|---|---|---|---|---|
| 2 | `w ≥ 3` | 0 | 0 | NOT SHARP (polynomial already valid at `w = 2`) |
| 3 | `w ≥ 4` | 2 | 1 | **SHARP** |

Both rows match `level-law-general.md` §5.3 exactly. Levels 4–6 need
wider-ambient strata than I could re-derive here, and the `ℓ = 7` failure
recorded there is outside the data available in this campaign. Note the
polarity: a *disagreement* at `w = ℓ` is the desired outcome; an early draft of
the checker asserted equality and flagged `ℓ = 3` as a failure. It is not.

---

## 6. Verification and reproduction

```bash
# 1. the mechanized theorem  (~2 s on a prebuilt HOL heap)
ISABELLE=/path/to/Isabelle2020/bin/isabelle tools/verified/build_ambient.sh

# 2. the growth-law checks against every census figure in the repo
python3 .build/v3-mech/check_growth.py
```

`build_ambient.sh` greps the theory for `sorry`, `oops`, `axiomatization` and
`quick_and_dirty` before invoking Isabelle, and fails if any is present.

`check_growth.py` reports **107 PASS, 0 FAIL, exit 0** over the data set
described in §5.

**The frozen pipeline is unaffected — verified, not assumed.**
`tools/verified/ROOT` differs from `HEAD` only by an appended comment block (6
inserted lines, 0 deleted; `git diff --stat` = `1 file changed, 6
insertions(+)`). `Ambient_Collapse` is declared in a separate
`tools/verified/ambient/ROOT` because Isabelle forbids two sessions sharing one
directory and `build.sh` copies `tools/verified/ROOT` verbatim into the
`snocheck2` build tree. `build.sh` steps 1–2 were re-run twice under
`.build/v3-mech/frozencheck/` — once with the modified ROOT and once with
`git show HEAD:tools/verified/ROOT` — and the extracted
`Verified/PrefixChecker.hs` is **byte-identical**, 18 493 bytes,
`sha256 = 8601a4884c80e3f9a02b4b830571971ead7f955c24bc4a13316558e2ad8d4a07`
in both cases. Both builds exit 0 in ~3 s.

Isabelle2020 itself had to be re-downloaded (it had lived in an ephemeral
scratchpad); the 426 MB macOS bundle is at
`.build/v3-mech/Isabelle2020_macos.tar.gz` and unpacks to
`.build/v3-mech/Isabelle2020.app/`. The HOL, `Sorting_Networks` and
`Sorting_Networks_Prefix` heaps from the previous campaign survived in
`~/.isabelle/Isabelle2020/heaps/`, so no HOL bootstrap was needed. **That
directory is still outside the repository and is still the durability risk
recorded in `evidence/v3/vcheck/report.md`.**

---

## 7. What the architect should reconsider

1. **Change the Part I hypothesis list** (§3.1). "Part I uses neither H3 nor
   H5" is false; "Part I holds with a *degenerate* root tower" is true and is
   what the experiments show.
2. **Reprint H4** in the decomposition form (§3.2). The published form is
   unsatisfiable exactly when the tower is non-degenerate.
3. **Add the §4.2 paragraph.** The class definition is a distance ball; the
   sorting-network census is a bound-gated subset of one. This is the kind of
   gap a formal-methods referee finds in five minutes, and conceding it costs
   two sentences while claiming it as understood costs the section.
4. **Downgrade "polynomial growth law" to "affine growth law" for sorting
   networks**, and keep "polynomial" for the conditional corollary and the
   prefix-reversal conjecture (§5.2). The KKW10 distinction survives intact.
5. **Say what is mechanized in one sentence and link this file.** The
   defensible claim is: *the abstract theorem is machine-checked with two
   non-vacuous interpretations; the claim that the sorting-network search is an
   instance is not, and rests on the implementation audit.*
6. **Relocate Isabelle2020 into the repository cache**, or record its download
   URL and SHA-256 in `config/`. This is the second campaign in a row to lose
   it.
