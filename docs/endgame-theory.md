# The End Game in the Output-Set DP — what transfers, what does not, and why

**Date:** 2026-08-21.
**Scope:** theory extraction and transfer for the Codish-lineage "end game"
last-layer / saturation / suffix theory, stated for the **output-set DP** that
`sortnetopt` (Harder, arXiv:2012.04400) actually runs, plus the measurements
that decide whether the transfer is worth anything.
**Machine-checkable authority:** `tools/verify_endgame.py`. Every claim below
tagged **PROVEN** has a paper proof here *and* is checked by exhaustion over
**every** canonical output set reachable from the full cube for `w ≤ 6`
(4 / 13 / 57 / 608 states at `w` = 3 / 4 / 5 / 6). Claims tagged
**CONJECTURE** are checked but not proved and, per the campaign rules, are
**not used for pruning anywhere**.
**Predecessors:** `docs/lowmem-endgame-assessment.md` §6b / §8.3 (which
promoted this family), `docs/sortnetopt-internals.md`,
`docs/transforms-assessment.md` (the Universal Level Law, used as the
evaluation instrument), `evidence/v3/limits/report.md`.

---

## 0. Verdict

> **The end-game family does not reduce the state count of the output-set DP,
> and the reason is structural rather than incidental.**
>
> 1. The part of the theory that *does* transfer to a single comparator
>    (last-layer adjacency) is **already fully absorbed by
>    `canonicalize(true)`**; it is not an additional constraint.
> 2. The part that gives the quoted 82,000× / 30× factors is **layer-counting
>    in the depth setting**. Harder's DP does not enumerate layers, so the
>    counts have no referent in it.
> 3. `saturation` / `co-saturation`, translated into this representation,
>    **is exactly subsumption**, which the stack already implements
>    (`sortnetopt-online-subsumption-v3`, `-tier2a-`, `-zm-`).
> 4. The residual, genuinely new, genuinely proven filters (§4: E1, E2, E4)
>    are gated by the *remaining* budget. **They are near-vacuous**: at
>    `w ≤ 6`, exhaustively, they retain **99.7 %** of all successors.
> 5. And the gate itself almost never opens: in the level-4 proxy
>    (`n=9 --limit 25`, 208,389 states, the run that reproduces the n=13
>    level-4 census to 0.6 %) **only 0.199 % of memo states have a remaining
>    bound ≤ 4** and **0.003 % have one ≤ 1**. The mass sits at remaining
>    bound 10–11 on width 7. **There is no "end" in this search that holds
>    appreciable mass.**
>
> 6. And the ceiling is **computable, not estimable** (§5.1, Theorem C): any
>    filter gated on "remaining budget ≤ k" can only ever delete states whose
>    own bound is ≤ k. On the level-4 proxy that caps the *entire family* at
>    **1.0008×** at the deployed gate (once the engine's interval-closure
>    early return is accounted for) and at **1.02×** for a hypothetical
>    *perfect* two-layer-suffix theory. The programme needs `10²–10⁵`.
>
> 7. **Measured in-engine at both levels, not modelled** (§5.2). With the patch
>    on, the filters excluded **zero** successors. The gate opened on
>    **3 of 49,502** expansions at level 4 (0.006 %) and on **5 of 9,723,183**
>    at level 5 (**0.00005 %**, a further 120× collapse). The reason is a new
>    fact worth more than the rest of this document: **99.57 % (level 4) and
>    99.87 % (level 5) of expansions happen at a state whose stored upper bound
>    is still the untightened `known_bounds[width]` seed**, so an upper-bound
>    gate is really a *width* gate — and the gate only opens where the filters
>    cannot bind.
>
> §6b of `lowmem-endgame-assessment.md` should be **downgraded from PROMOTE to
> KILL-as-a-state-reducer**, with the one surviving engineering item recorded
> in §7 and the new engine observation in §5.2 promoted in its place.

Two corrections to §6b's factual content are recorded in §1.3.

---

## 1. The source theory, verbatim, and two corrections

### 1.1 What the papers actually prove

Sources, obtained and text-extracted locally (`pdftotext -layout`) from the
arXiv PDFs rather than from any secondary summary:

* **[LATA15]** Codish, Cruz-Filipe, Schneider-Kamp, *Sorting Networks: The End
  Game*, LATA 2015, arXiv:1411.6408.
* **[JCSS19]** Codish, Cruz-Filipe, Ehlers, Müller, Schneider-Kamp, *Sorting
  networks: to the end and back again*, JCSS 104:184–201 (2019),
  arXiv:1507.01428.

Both papers **define a comparator network to be layered**:

> "A comparator network `C` with `n` channels and depth `d` is a sequence
> `C = L₁; … ; L_d` where each layer `L_k` is a set of comparators `(i, j)`
> for pairs of channels `i < j`. At each layer, every channel may occur in at
> most one comparator." — [LATA15] §2 = [JCSS19] §2.1

> **Redundant comparator.** "Let `C; (i, j); C′` be a comparator network. The
> comparator `(i, j)` is *redundant* if `x_i ≤ x_j` for all sequences
> `x₁…x_n ∈ outputs(C)`." (Knuth TAOCP 5.3.4 ex. 51, credited to Graham.)

> **[LATA15] Lemma 3 = [JCSS19] Lemma 4.** "Let `C` be a non-redundant sorting
> network on `n` channels. Then all comparators in the last layer of `C` are
> of the form `(i, i+1)`."

> **[LATA15] Thm 5 = [JCSS19] Thm 1.** The number of possible last layers is
> `L_n = F_{n+1} − 1` (matchings of the path `P_n`). `L₁₇ = 2,583` against
> `G₁₇ = 211,799,312` general layers.

> **[LATA15] Cor. 10 = [JCSS19] Cor. 2.** Every comparator `(i, j)` in layer
> `d−1` satisfies `j − i ≤ 3`; if `j = i+2` then `(i,i+1)` or `(i+1,i+2)` is in
> the last layer; if `j = i+3` then both `(i,i+1)` and `(i+2,i+3)` are.

> **[LATA15] Thm 11 = [JCSS19] Thm 2** (the papers' self-described main
> contribution). "If `C` is a sorting network without redundant comparators,
> then every comparator at layer `k` of `C` connects adjacent `k`-blocks",
> where a `k`-block is a maximal set of channels connected by comparators in
> layers `> k`.

> **[LATA15] Cor. 12 = [JCSS19] Cor. 3.** "Let `B` be a `k`-block of `C`
> containing `m` comparators. Then `B` consists of at most `m + 1` channels."

> **[LATA15] Def. 17 = [JCSS19] Def. 3 (co-saturation).** A depth-`d` sorting
> network is co-saturated if (i) its last layer is in last-layer normal form,
> (ii) no two consecutive blocks at layer `d−1` have unused channels, and
> (iii) if `(i,i+1)` is in layer `d` and channels `i, i+1` are unused in layer
> `d−1`, then channels `i−1` and `i+2` are used in layer `d`.

> **[LATA15] Thm 14 = [JCSS19] Thm 3.** Last layers in normal form are counted
> by the Padovan sequence, `K_n = P_{n+5}`; `K₁₇ = 86` against `L₁₇ = 2,583`.

### 1.2 The size-setting claim is *not a theorem anywhere*

The 6.5 → 1.5 CPU-year figure that §6b quotes is the **entire** size-setting
content of the literature, and it appears only in the LATA conclusion:

> "While the paper presents detailed results on the end of sorting networks in
> the context of proving optimal depth …, the necessary properties of the last
> layers can also be used to prove optimal size. We experimented on adding
> constraints similar to those in Section 5 for the last three comparators, as
> well as constraints encoding Corollary 12, to the SAT encoding presented in
> [3]. **Preliminary results based on uniform random sampling of more than 10 %
> of the cases** indicate that we can reduce the total computational time used
> in the proof that 25 comparators are optimal for 9 channels from 6.5 years to
> just over 1.5 years." — [LATA15] §6

There is **no numbered lemma, theorem or corollary** for the size setting; no
statement of what "the last three comparators constraints" are; no proof that
the layered lemmas survive de-layering. **[JCSS19] drops the paragraph
entirely** and replaces it with new depth-17 material. So the headline number
in §6b is an extrapolated estimate from a 10 % sample in a SAT encoding, not a
measured speed-up and not a theorem.

### 1.3 Two factual corrections to `lowmem-endgame-assessment.md` §6b / §8.3

1. **"1,440 co-saturated two-layer suffixes at n=13" is wrong.** Table 1 of
   [LATA15] (= Table 3 of [JCSS19]) reads
   `n`: … 11 → 700, **12 → 1,440**, **13 → 2,892**, 14 → 5,676, … So 1,440 is
   the `n = 12` entry; `n = 13` is **2,892**. Verified identically in both
   PDFs.
2. **arXiv:1410.2736 is not the last-layer paper.** It is Ehlers & Müller,
   *Faster Sorting Networks for 17, 19 and 20 Inputs* — a paper about
   hand-crafted **first**-layer (Green) filters, cited by [LATA15] as ref. [7].
   The "381 of 609 prefixes eliminated" claim in §6b should be re-sourced to
   Ehlers & Müller, *New bounds on optimal sorting networks*, CiE 2015
   (LNCS 9136:167–176), whose content was folded into [JCSS19] §§4–6.

Neither correction changes the verdict; both matter for the ledger.

---

## 2. The DP being targeted, stated precisely

Notation follows `src/output_set.rs` and `src/search.rs` of the pinned clone
(`0b5d09c4…`), cross-checked line by line in `docs/sortnetopt-internals.md`.

**States.** An *output set* on `w` channels is a set `X ⊆ {0,1}^w`, held as a
dense `2^w`-entry bitmap. The DP root is `all_values(n)`, the full cube.

**Comparators.** `apply_comparator([i, j])` writes `max` to channel `i` and
`min` to channel `j`. The successor loop (`search.rs:216-227`) runs
`for i in 0..channels { for j in 0..i { … } }`, so the min always lands on the
lower-indexed channel; the sort order is ascending. For an unordered pair
`(lo, hi)` with `lo < hi`, a vector `v` is **out of order** iff
`v_lo = 1 ∧ v_hi = 0` and **strictly in order** iff `v_lo = 0 ∧ v_hi = 1`.

**Redundancy.** `apply_comparator` returns `false` — and the successor is
skipped — iff *no* vector is out of order (a no-op) or *no* vector is strictly
in order (the comparator acts as the transposition `(lo hi)`, a channel
relabelling, hence `G`-equivalent to `X`). **Consequently the enumerated
successors are in bijection with the *unsettled* channel pairs of `X`**, where
a pair is unsettled iff both an out-of-order and a strictly-in-order vector
exist.

**Terminal condition.** `OutputSet::is_sorted` (`output_set.rs:157-175`)
accepts `X` iff `X` has **at most one vector per Hamming weight**.

**Bound.** `bound(X)` = the least `m` such that some sequence of `m`
comparators makes `X` sorted. `State.bounds = [lower, upper]` is a closed
interval on it.

**Symmetry.** `canonicalize(true)` quotients by `G = S_w × C₂` (channel
permutation and complement).

> **Proposition 2.1 (the untangling convention) — PROVEN, machine-checked.**
> On every output set reachable from the full cube, the following three are
> equivalent: (i) `is_sorted(X)` (≤ 1 vector per Hamming weight); (ii) `X` is a
> chain under inclusion; (iii) `X` is a channel permutation of the sorted set
> `{1^k 0^{w−k}}`.
>
> *Why it matters.* (iii) is what licenses quotienting by `S_w`: a network
> whose output set on the full cube is a chain becomes a genuine sorting
> network after renaming the output channels, and renaming the channels of a
> network applied to the (permutation-invariant) full cube is free. This is the
> standard untangling argument ([LATA15] §2; Knuth 5.3.4). Note that
> (i) ⇔ (ii) is *false* on general sets — e.g. `{100, 011}` has one vector per
> weight and is not a chain — so reachability is a genuine hypothesis.
> *Check:* `check_terminal_condition`, exhaustive, `w = 3..6`, 0 mismatches.

> **Validation of the reference model.** `tools/verify_endgame.py` reimplements
> all of the above independently of the engine. Its computed bound for the full
> cube is **3 / 5 / 9 / 12** at `w = 3 / 4 / 5 / 6` — i.e. it reproduces
> `S(3..6) = 3, 5, 9, 12` exactly, from first principles, with no table of
> known optima anywhere in it. Together with Prop. 2.1 that is the evidence
> that the model's comparator convention, redundancy test, terminal condition
> and canonicalisation all match `sortnetopt`'s.

**A sound successor filter** is a rule `F` such that, for every state `X` with
`bound(X) = m ≥ 1`, `F(X)` retains at least one comparator `c` with
`bound(c(X)) = m − 1`. Standard induction then gives `bound_F ≡ bound`: the
filtered DP computes the same bounds, and every successor `F` discards is a
canonicalisation and a memo insertion not performed — which is exactly the
state-count metric.

**Budget-relative filters.** `F` may use `b := state.bounds[1]`, the stored
**upper** bound, which satisfies `m ≤ b`. A test parameterised by `b − 1`
cannot discard an optimal successor `Y`, because `bound(Y) = m − 1 ≤ b − 1`.
All filters in §4 are of this form; this is the precise sense in which they are
"end-game" filters.

---

## 3. What the source theory becomes here

### 3.1 Last-layer adjacency is already `canonicalize(true)` — PROVEN

[LATA15] Lemma 3 constrains the last layer *relative to the fixed channel
indexing of the network*. In the generate-and-prune setting that is a real
constraint because networks are enumerated on labelled channels. In the
output-set DP it is not, for two independent reasons:

1. **The DP never enumerates a layer.** It enumerates one comparator at a
   time; the notion "last layer" has no representation in the state.
2. **The labels are quotiented away.** The `F_{n+1} − 1` count is precisely
   "the number of matchings of the path `P_n`", i.e. the number of layers that
   survive after using a channel permutation to make every last-layer
   comparator adjacent. `canonicalize(true)` quotients by the *whole* of
   `S_w × C₂`, which is strictly more than the untangling used to derive
   `L_n`. The reduction `C(n,2)`-choose → `F_{n+1} − 1` is therefore already
   taken, and taken further.

Empirically, the constraint is also **vacuous where it would apply**: at every
state with `bound(X) = 1` for `w = 4, 5, 6` (2, 2 and 3 states respectively)
the engine's redundancy test already leaves **exactly one** non-redundant
comparator. There is nothing left to prune.

### 3.2 Saturation and co-saturation are subsumption — PROVEN

The Bundala–Závodný notion restated in [JCSS19] §2.2:

> "a two-layer network `L₁; L₂` is saturated if `L₁` is maximal and it is not
> possible to find `L₂′ ⊋ L₂` such that `outputs(L₁; L₂′) ⊊ outputs(L₁; L₂)`."

Note what the definition quantifies over: it asks whether some **strictly
smaller output set, under set inclusion**, is reachable by adding comparators
to the layer. The soundness of preferring it is the subsumption lemma, which
the DP already has (`internals` §2.4, `Checker.thy:442`):

> `A ⊆ B ⟹ bound(B) ≥ bound(A)`, and modulo `G`, `A ⊑ B ⟹ bound(B) ≥ bound(A)`.

Stated precisely, the relationship is a strict containment of scopes:

> **Proposition 3.2 — PROVEN.** Saturation is the special case of subsumption
> in which the subsuming set is `c(X)` for a single comparator `c` on channels
> unused by the current layer, *and* `c(X) ⊆ X` (equivalently: every
> out-of-order vector's swap is already present, so `c` merges without
> introducing anything). The DP's subsumption test is strictly more general —
> it compares `X` against **every** stored state under **every** element of
> `G = S_w × C₂`, with no restriction to one comparator, to one layer, or to
> the suffix.

So co-saturation does not add a constraint the stack lacks; it is a weaker
instance of one the stack already implements three ways
(`sortnetopt-online-subsumption-v3`, `-tier2a-v3`, `-zm-v3`, plus the offline
`prune-all`), and which is measured at a 160× compression factor at `n = 11`
(`lowmem-endgame-assessment.md` decisive-action 2) — against co-saturation's
30×, which is in any case a *depth*-setting count (below).

One asymmetry is worth recording: co-saturation is a **depth**-setting
normalisation. Adding a comparator to the last layer is free in depth and
costs one in size. So the [LATA15] Def. 17 conditions (ii) and (iii) — which
force extra comparators into the suffix — are **not** sound in the size
setting at all, and neither is the `K_n = P_{n+5}` count. The `30×` in §6b is
a depth-setting number that has no size-setting analogue.

### 3.3 The `k`-block theorems do not localise — the structural obstruction

[LATA15] Thm 11 and Cor. 12 are the parts that are genuinely
comparator-counting rather than layer-counting, and they are the only real
candidates. Both are statements about a **whole suffix**: a `k`-block is
defined by "the comparators in layers `> k`", i.e. by the network that has not
been chosen yet.

> **Theorem N1 (localisation obstruction) — PROVEN by counterexample,
> machine-checked.**
> Consider the literal transfer "keep only successors on channel pairs that are
> adjacent in the canonical labelling". For each of four natural canonical
> forms — lexicographic-minimum (which is the model's), lexicographic-maximum,
> and column-population-sum ascending / descending — the rule is **unsound**,
> with explicit counterexamples at `w = 6`:
>
> | canonical form | states audited (`w=6`) | successors kept | unsound on |
> |---|---|---|---|
> | lex-min | 607 | 2,471 / 4,399 (56.2 %) | **1** |
> | lex-max | 607 | 2,435 / 4,399 (55.4 %) | **6** |
> | column-sum ascending | 607 | 2,502 / 4,399 (56.9 %) | **2** |
> | column-sum descending | 607 | 2,504 / 4,399 (56.9 %) | **2** |
>
> Smallest lex-min counterexample (`w = 6`, `bound = 4`):
> `X = {0, 1, 3, 5, 7, 9, 11, 13, 15, 19, 23, 29, 31, 63}` — the **only**
> optimal first comparator is the pair `(1, 3)`; the adjacent pairs
> `(1,2), (2,3), (3,4)` are all non-redundant and all sub-optimal.
>
> **And yet the normal form exists.** For every reachable state at
> `w = 4, 5, 6` there is *some* labelling in its `G`-orbit under which an
> optimal comparator is adjacent — 0 hopeless states out of 12 / 56 / 607.
>
> *Reading.* The adjacency normal form is a **global** statement ("an optimal
> network can be relabelled so that…"). The DP needs a **local** rule
> computable from `X` alone. The relabelling that realises adjacency is
> determined by the suffix, which is precisely the unknown. That is why the
> theory does not transfer, and it is not a defect of any particular canonical
> form.
>
> *Check:* `check_filter(..., "canonical_adjacent")` and the orbit sweep in the
> §8 reproduction commands.

**Corollary 12 / 3 specifically is refuted.** It is the one result in the two
papers that counts *comparators* rather than layers ("a `k`-block with `m`
comparators uses at most `m+1` channels"), so it is the natural candidate for a
size-setting transfer, and §8.3 of the assessment names it as the constraint
Codish et al. added to the `S(9) = 25` encoding. Its direct analogue here is
"the channels that must be touched form few enough components that
`bound(X) ≥ |L(X)| − 1`", strengthening E4's `⌈|L(X)|/2⌉`. It is **false**:

| `w` | states | `bound ≥ ⌈|L|/2⌉` (E4) | `bound ≥ |L| − 1` | `bound ≥ |L|` |
|---|---|---|---|---|
| 4 | 12 | holds | **1 violation** | 8 violations |
| 5 | 56 | holds | **4 violations** | 25 violations |
| 6 | 607 | holds | **25 violations** | 158 violations |

The mechanism of the failure is the same as N1: Cor. 12/3 constrains a block of
the *chosen* network, and the DP does not know the network. E4's factor of two
— "each comparator touches two channels" — is all that survives without
knowing the suffix's connectivity.

The weaker Cor. 10 transfer ("span ≤ 3") is *sound* at `w ≤ 6` but keeps
**97.1 %** of successors, i.e. it is worth nothing, and it is sound here only
because it is nearly the identity — it is recorded as a CONJECTURE, unused.

---

## 4. What is left: three proven budget-relative filters

These are new (they have no counterpart in [LATA15]/[JCSS19]) and they are the
only things in this document that may be deployed.

> ### Theorem E1 (the last comparator is unique) — PROVEN
> Let `X` be an output set with `bound(X) = 1`, and let `c` be a comparator
> with `c(X)` sorted. Then:
> (a) every Hamming weight class of `X` has at most 2 vectors;
> (b) if `u ≠ v` lie in the same class then `u ⊕ v` has popcount exactly 2, and
>     the two set bits are the channels of `c`;
> (c) all classes of size 2 yield the *same* pair, so `c` is uniquely
>     determined and computable in one pass over `X`.
>
> *Proof.* A comparator preserves Hamming weight, so it maps `X_l` onto
> `c(X)_l`, which is a singleton because `c(X)` is sorted. The fibres of `c`
> have size ≤ 2: `c(u) = c(v)` with `u ≠ v` forces one of them out of order and
> the other to be its swap on the comparator pair. Hence (a) and (b). The pair
> named in (b) is the comparator's own pair, so it is the same for every class,
> giving (c). ∎
>
> *Filter form.* When `b = 1`, enumerate only that one pair; if any class has
> more than 2 vectors, or two classes name different pairs, then no successor
> is admissible, which proves `bound(X) ≥ 2`.
>
> *Measured power: none.* At `w ≤ 6` every `bound = 1` state already has
> exactly one non-redundant comparator, so E1 removes **0** successors. It is
> implemented because it is the only filter that is *tight*, and because it
> makes the `b = 1` case `O(|X|)` instead of `O(w²·|X|)`.

> ### Theorem E2 (weight-class halving) — PROVEN
> For every output set `X`, comparator `c` and weight `l`:
> `|c(X)_l| ≥ ⌈|X_l| / 2⌉`. Consequently
> **`bound(X) ≥ ⌈log₂ max_l |X_l|⌉`**.
>
> *Proof.* Comparators preserve Hamming weight, so `c` maps `X_l` into
> `c(X)_l`. If `c(u) = c(v)` with `u ≠ v` then, since `c` only alters vectors
> that are out of order on its pair, one of `u, v` is out of order and the
> other is its swap; so every fibre has size ≤ 2 and `|c(X)_l| ≥ |X_l|/2`.
> Sorted means every class is a singleton, so `m` comparators require
> `max_l |X_l| ≤ 2^m`. ∎
>
> *Filter form.* At budget `b`, a successor `Y` is admissible only if
> `max_l |Y_l| ≤ 2^{b−1}`.
>
> *Measured power: none at `w ≤ 6`* — 4,399 / 4,399 successors kept. The
> binding condition is `2^{b−1} < max_l |Y_l|`; at the states that actually
> populate the memo, `max_l |Y_l|` is 3–5 while `b ≥ 5`, so the test can only
> ever fire at `b ≤ 3`.

> ### Theorem E4 (live support) — PROVEN
> For an output set `Z`, define the **live support**
> ```
> L(Z) = { p : ∃ u, v ∈ Z with |u| = |v| and u_p ≠ v_p }
> ```
> — the channels on which two equal-weight vectors of `Z` disagree. Then every
> comparator network sorting `Z` contains a comparator on **every** channel of
> `L(Z)`, and therefore
> **`bound(Z) ≥ ⌈|L(Z)| / 2⌉`**.
>
> *Proof.* Suppose no comparator of `N` touches channel `p`; then
> `N(v)_p = v_p` for every `v`. Pick `u, v ∈ Z` with `|u| = |v|` and
> `u_p ≠ v_p`. Comparator networks preserve Hamming weight, so `N(u)` and
> `N(v)` have the same weight; if `N(Z)` is sorted it has at most one vector of
> each weight, so `N(u) = N(v)`. But `N(u)_p = u_p ≠ v_p = N(v)_p`.
> Contradiction. Each comparator touches two channels. ∎
>
> `L(Z)` is computed in a single pass: for each weight `l` take `OR_l` and
> `AND_l` of the class, then `L(Z) = ⋁_l (OR_l ∧ ¬AND_l)`.
>
> *Filter form.* At budget `b`, a successor `Y` is admissible only if
> `|L(Y)| ≤ 2(b − 1)`.
>
> *Measured power: 0.3 %.* At `w ≤ 6`, exhaustively, 4,385 / 4,399 successors
> kept — 14 excluded, all at `b ≤ 4`. The binding condition is
> `2(b−1) < |L(Y)| ≤ w`, i.e. `b < w/2 + 1`: at width 7 it can only fire at
> `b ≤ 3`, at width 8 at `b ≤ 4`.
>
> *Related conjecture, NOT used.* Replacing `L(Z)` by "channels incident to an
> unsettled pair" also satisfies `|·| ≤ 2·bound` at `w ≤ 6`, and is a strictly
> larger set (so a stronger filter), but I have no proof. It is checked and
> reported by `verify_endgame.py` and **must not be deployed**.

**The composite filter** (E1 at `b = 1`, `E2 ∧ E4` above) keeps
**99.7 %** of all successors at `w ≤ 6`, exhaustively, with 0 soundness
violations.

### 4.1 The seeding form of E2 and E4, evaluated and rejected

E2 and E4 are also *lower bounds* on `bound(X)`, and unlike their filter forms
they are **not budget-gated** — so Theorem C does not apply to them and they
could in principle have been the way out. `StateMap::get`
(`search/states.rs:48-89`) seeds an unvisited state at `bounds = [1, ·]`;
seeding instead at

```
bounds[0] = max( 1, ceil(log2 max_l |X_l|), ceil(|L(X)| / 2) )
```

is sound by E2 and E4. Measured against the true bound over every reachable
state:

| `w` | states | mean true bound | mean seed | seed exact | free chain `C(w)` |
|---|---|---|---|---|---|
| 5 | 56 | 4.20 | 2.55 | 17.9 % | 8 |
| 6 | 607 | 5.74 | **2.92** | 3.3 % | 11 |

The seed is **weaker than the van Voorhis / Huffman bound the engine already
derives for free** (`improve_huffman`, `search.rs:261-347`, which is what
produces `C(n)` = 37 at n=13 in 3 ms), so it can never raise a stored lower
bound above what the existing machinery already produces. **Rejected**; not
implemented. Recorded because "seed the interval better" is the obvious next
idea and this closes it.

---

## 5. Where the states actually are — the measurement that decides it

The Universal Level Law (`transforms-assessment.md` §2.3) says the
per-`(width, level)` memo census is independent of `n`, so `n=9 --limit 25`
(level `ℓ = 25 − C(9) = 4`) reproduces the n=13 level-4 census. It does:
measured widths `w5/w6/w7/w8/w9 = 2,137 / 36,027 / 132,408 / 34,014 / 3,741`
against the archived n=13 values `2,137 / 35,921 / 131,683 / 33,549 / 3,741`.

Memo census of `n=9 --limit 25` by **remaining lower bound** `b`, from the
engine's own `group_<channels>_<bound>.bin` dump (208,389 states):

| `b` | w3 | w4 | w5 | w6 | w7 | w8 | w9 | total |
|---|---|---|---|---|---|---|---|---|
| 1 | 2 | 3 | 2 | | | | | **7** |
| 2 | 2 | 5 | 7 | 13 | 44 | 14 | | 85 |
| 3 | 1 | 17 | 25 | 21 | 10 | 3 | | 77 |
| 4 | | 26 | 108 | 99 | 12 | | | 245 |
| 5 | | 6 | 470 | 421 | 86 | 3 | | 986 |
| 6 | | | 819 | 1,950 | 373 | 15 | | 3,157 |
| 7 | | | 641 | 5,939 | 1,712 | 63 | | 8,355 |
| 8 | | | 64 | 12,610 | 6,789 | 188 | | 19,651 |
| 9 | | | 1 | 10,392 | 19,169 | 618 | | 30,180 |
| 10 | | | | 3,869 | 37,184 | 1,810 | | 42,863 |
| **11** | | | | 702 | **39,913** | 4,124 | | **44,739** |
| 12 | | | | 11 | 21,157 | 6,801 | 11 | 27,980 |
| 13–25 | | | | | 5,959 | 20,375 | 3,730 | 30,064 |

Cumulative, the number that matters:

| remaining bound ≤ | states | share |
|---|---|---|
| 1 | 7 | **0.003 %** |
| 2 | 92 | 0.044 % |
| 3 | 169 | 0.081 % |
| 4 | **414** | **0.199 %** |
| 6 | 4,557 | 2.187 % |
| 8 | 32,563 | 15.6 % |

The distribution is unimodal at `b = 11`, width 7. **The DP's mass is in the
middle of its subproblems, not at either end**, and the reason is already in
the record: the van Voorhis / Huffman free chain reaches bound `C(n)` (37 at
n=13) with `n−2` states in 3 ms, so the branch-and-bound only ever descends
`ℓ` levels below it before the free bound closes the branch. The "end game" —
`b ≤ 4` — is `0.199 %` of the search, and the proven filters exclude only a
fraction of successors even there.

**Note on the gate, which sharpens the figure by a further 2.5×.** Deployed,
the filters gate on `state.bounds[1]` (the **upper** bound), which is ≥ the
lower bound tabulated above — so `0.199 %` is already a strict upper bound on
the reachable fraction at `ENDGAME_BUDGET = 4`, not an estimate. But
`Search::improve` (`search.rs:134-146`) **returns before the successor loop
whenever the interval is closed**. So the loop is reached only when
`bounds[0] < bounds[1] ≤ 4`, i.e. `bounds[0] ≤ 3`. The true ceiling at the
deployed gate is therefore the `b ≤ 3` row: **169 / 208,389 = 0.081 %**,
a best-possible speed-up of **1.0008×**.

The same argument kills Theorem E1 outright as an engine feature. E1 requires
`bounds[1] = 1`; an unsorted state is seeded with `bounds[0] ≥ 1`, so
`bounds[1] = 1` forces `bounds[0] = bounds[1]`, the interval is closed, and
`improve` returns before ever reaching the successor loop. **E1 is not merely
empirically vacuous — it is structurally unreachable**, because the engine's
interval bookkeeping already resolves every `bound = 1` state without
enumerating anything. That is the sharpest possible statement of §3.1: the
last comparator is not a place where this search spends time.

### 5.1 The ceiling on the entire family, computed rather than estimated

The cumulative table above is not merely suggestive; it is a **hard upper bound
on what any budget-gated end-game technique can ever achieve here**, and the
argument is short.

> **Theorem C (family ceiling) — PROVEN.**
> Let `F` be any sound successor filter that is inert unless the remaining
> budget is `≤ k` (this is what "end game" means: the rule reads only the last
> `k` comparators). Then the set of memo states `F` can possibly eliminate is
> contained in `{X : bound(X) ≤ k}`.
>
> *Proof.* By Prop. C.0 below, `bound` never increases along a DP edge, so
> every successor of a state with `bound ≤ k` again has `bound ≤ k`; hence
> every state `F` removes lies in `{bound ≤ k}`. Conversely, a state with
> `bound > k` is reached only along a path all of whose vertices have
> `bound > k` (same proposition, read backwards), so no gate on such a path
> ever opens. `F` is sound, so no stored bound changes anywhere, so no state
> outside `{bound ≤ k}` is created or destroyed. ∎
>
> **Prop. C.0 — machine-checked exhaustively at `w ≤ 6`, conjectured in
> general.** For every reachable `X` and every non-redundant comparator `c`,
> `bound(X) − 1 ≤ bound(c(X)) ≤ bound(X)`. The left inequality is the DP
> recursion itself. The right one is checked over every edge of the reachable
> canonical graph: the observed differences are exactly `{−1, 0}`
> (`w = 6`: 2,916 edges at `−1`, 1,483 at `0`, **0 increases**). Since Theorem
> C is used only to *bound the benefit from above*, and a violation of C.0
> could only make an end-game filter reach further, this hypothesis is flagged
> rather than assumed away — see §9.
>
> *(Second-order caveat: the engine memoises only states it
> actually improves, so run-to-run scheduling noise — measured at a few percent
> in `transforms-assessment` §2.3 — can move the population slightly in either
> direction. That noise is larger than the effect being bounded.)*

Evaluating the ceiling on the level-4 proxy (208,389 states):

| gate `k` | what it corresponds to | states removable | **best possible speed-up** |
|---|---|---|---|
| 1 | the last comparator ([LATA15] Lemma 3) | 7 | **1.00003×** |
| 4 | the deployed `ENDGAME_BUDGET` | 414 | **1.002×** |
| 6 | a *perfect* two-layer suffix theory at width 7 | 4,557 | **1.022×** |
| 8 | a perfect two-layer suffix theory at width 8 | 32,563 | **1.19×** |
| 10 | — | 105,606 | 2.03× |

So even a **flawless, fully sound, zero-cost** transfer of the whole
Codish end-game programme — one that deleted *every* state within two layers
of sorted — is worth **1.02×** at level 4. The programme needs `10²–10⁵`.
This is the same shape of finding as `lowmem-endgame-assessment.md` §3.2
("the layered-memory ceiling is 1.9×"): the technique is not wrong, the object
simply does not have the mass where the technique acts.

**And the trend runs against the technique.** The same census, taken at the
real target level — `n=13 --limit 42`, level 5, **50,968,542 states**, measured
this session (it reproduces the archived 50,922,864 to 0.09 %) — is an order of
magnitude *worse*:

| gate `k` | level 4 (`n=9 -l 25`) | **level 5 (`n=13 -l 42`)** |
|---|---|---|
| 1 | 0.003 % → 1.00003× | 0.00003 % → **1.000000×** |
| 4 | 0.199 % → 1.002× | **0.019 % → 1.0002×** |
| 6 | 2.19 % → 1.022× | **0.083 % → 1.0008×** |
| 8 | 15.6 % → 1.185× | 1.40 % → 1.014× |
| 10 | 50.7 % → 2.03× | 13.8 % → 1.16× |
| 12 | 85.6 % → 6.93× | 46.8 % → 1.88× |

*The level-5 A/B, completed.* At `n=13` the baseline arm ran
(`result = 42`, 50,968,542 states, 8 m 29 s, peak RSS 2.74 GB, every
`endgame_*` counter zero — inertness confirmed at the target width), but the
filtered arm was **deliberately terminated at 29.2 M states** when free memory
fell to 2.80 GB and swap reached 4.9 GB (the 5 GB / free-page guardrail; the
same call `evidence/v3/zm/report.md` made for its `n=11 --limit 34` point). It
is not reported as a measurement; the replay command is in §9.

The A/B was instead completed at **`n=11 --limit 34`**, which is level 5 by the
Level Law and is the cheapest terminating level-5 run:

| | result | states | `gate_reached` | E2 rej | E4 rej | audit viol |
|---|---|---|---|---|---|---|
| no env | 34 | 50,933,133 | — (all counters 0) | 0 | 0 | 0 |
| `SORTNETOPT_ENDGAME=1` | 34 | 50,957,489 | **5 / 9,723,183** | **0** | **0** | **0** |

**The gate opened on 5 of 9.72 M successor expansions — 0.00005 %**, a further
**120× collapse** from level 4's 0.006 %, and the filters rejected nothing. The
+0.048 % state difference is scatter, since the filters demonstrably removed no
successors. The seed-spike structure is *stronger* here than at level 4:
**99.87 %** of expansions sit on an untightened `known_bounds[width]` value
(spikes at 3, 5, 9, 12, 16, 19, 25, 29, 35 — exactly `known_bounds[3..11]`),
only 0.134 % were ever tightened.

*One reported number is rejected.* The wall times (643.8 s off vs 476.1 s on)
were initially summarised as a "26 % speedup from ENDGAME". **That is
spurious.** With `e2_rejected = e4_rejected = e1_states = 0` the filters
performed no work-avoiding action whatsoever, so they cannot have caused a
wall-clock effect; the two arms simply ran under different machine memory
pressure (the off arm overlapped a concurrent 2.7 GB n=13 job). Recorded here
because it is exactly the kind of causal claim this campaign must not make.

The modal remaining bound moves from 11 to **12**, and the width mass from
`w7` to `w8` (26.7 M of 50.97 M at width 8, 17.6 M at width 7) — the search
gets *further* from the sorted end as the level rises, which is exactly the
direction level 7 lies in. **Whatever the end-game family is worth, it is worth
less at every level the programme actually needs.** Extrapolating the level-4 →
level-5 collapse (2.19 % → 0.083 % at `k = 6`, a factor of 26), the two-layer
ceiling at level 7 is indistinguishable from 1.000×.

### 5.2 The in-engine measurement, and a new fact about the upper bound

The patch records `state.bounds[1]` and `state.bounds[0]` at **every** successor
expansion. On `n=9 --limit 25` (49,502 expansions) the upper-bound histogram is
not smooth — it is concentrated on seven spikes:

| `bounds[1]` | expansions | share | is it `known_bounds[w]`? |
|---|---|---|---|
| 3 | 3 | 0.006 % | **yes** — width 3 |
| 5 | 44 | 0.089 % | **yes** — width 4 |
| 9 | 1,859 | 3.76 % | **yes** — width 5 |
| 12 | 18,283 | 36.9 % | **yes** — width 6 |
| 16 | 25,117 | 50.7 % | **yes** — width 7 |
| 19 | 3,619 | 7.31 % | **yes** — width 8 |
| 25 | 362 | 0.73 % | **yes** — width 9 |
| 6,7,8,10,11,13,14,15,17 | 215 total | **0.43 %** | no — genuinely tightened |

> **Observation 5.2 (new, and not about end-game theory at all).** In the
> `--limit` regime **99.57 % of successor expansions happen at a state whose
> stored upper bound is still the untightened `known_bounds[width]` seed**
> (`search/states.rs:76`). The lower-bound race essentially never improves an
> upper bound, because improving one requires exhibiting an actual network.

The consequence is severe and general: **any filter gated on an upper bound is
gated, in practice, on `known_bounds[width]`** — i.e. on the *width* alone. At
`ENDGAME_BUDGET = 4` the gate is "width ≤ 3", which is why
`endgame_gate_reached = 3` out of 49,502. To reach even 4 % of expansions the
budget would have to be raised to 9, and at budget 9 neither E2
(`max_l |Y_l| ≤ 256`) nor E4 (`|L(Y)| ≤ 16 > w`) can ever bind. **The two
constraints are mutually exclusive**: the gate only opens where the filters are
useless, and the filters only bite where the gate is shut.

Measured A/B on the level-4 proxy, three runs each (the search is
nondeterministic; scatter is a few tenths of a percent):

| config | states | mean |
|---|---|---|
| no env | 208,518 / 208,062 / 208,349 | 208,310 |
| `SORTNETOPT_ENDGAME=1` | 209,134 / 208,631 / 208,105 | 208,623 |

`endgame_e2_rejected = endgame_e4_rejected = endgame_e1_states =
endgame_empty_fallback = 0` in every run. **The filters excluded zero
successors, so the 0.15 % difference between the columns is entirely
scheduling noise, not an effect.** `filter_audit_violations = 0` throughout.

**The gate is not the only thing that is inert — the filters are too.** Opening
the gate progressively, with the audit on (so the answer is always taken from
the unfiltered successor set), `n=9 --limit 25`:

| `SORTNETOPT_ENDGAME_BUDGET` | expansions | gate reached | E2 rejected | E4 rejected | audit violations | result |
|---|---|---|---|---|---|---|
| 1 | 49,580 | 0 | 0 | 0 | 0 | 25 |
| 4 (default) | 49,521 | 3 | 0 | 0 | 0 | 25 |
| 6 | 49,668 | 48 | 0 | 0 | 0 | 25 |
| 9 | 49,568 | 1,922 | 0 | 0 | 0 | 25 |
| **25 (gate fully open)** | **49,733** | **49,733** | **0** | **0** | **0** | **25** |

The gate plumbing is live and monotone, and **even with the gate removed
entirely — every one of 49,733 successor expansions offered to the filters —
E2 and E4 reject nothing.** The reason is the same one: the filters are
parameterised by the state's own `bounds[1]`, which is the `known_bounds[width]`
seed, so their caps are `2^{15}` and `30` at width 7 while the quantities they
cap are at most 5 and at most 7. This is a complete in-engine negative result,
not a sampling estimate.

*Caveat, stated plainly:* because the filters reject nothing, the **in-engine**
audit is correspondingly thin — it verifies plumbing, not soundness. The
substantive soundness evidence for E1/E2/E4 is the exhaustive model audit of
§4 (`w ≤ 6`, all 607 reachable states at `w = 6`, all 4,399 successors, every
budget, 0 violations), where the filters *do* fire. A useful negative control
for a future session would be to deliberately gate on `bounds[0]` instead of
`bounds[1]` — that is unsound and the audit should catch it; it was not run.

**It is the same at n = 13, measured not extrapolated.** Running the instrument
at the *actual target width* (`n=13 --limit 41`, level 4, 46 MB — the cheap
point, not the 3.35 GB one) gives an expansion histogram that is the n=9 one to
within run-to-run scatter:

| bucket | 3 | 5 | 9 | 12 | 16 | 19 | 25 | (all others) |
|---|---|---|---|---|---|---|---|---|
| `n=9 --limit 25` | 3 | 44 | 1,859 | 18,283 | 25,117 | 3,619 | **362** | 215 |
| `n=13 --limit 41` | 3 | 44 | 1,866 | 18,318 | 25,238 | 3,657 | **362** | 217 |

Same seven spikes, same widths, `gate_reached = 3` in both, `e2_rejected =
e4_rejected = 0` in both, and bucket 25 agrees *exactly*. State counts:
209,034 (off) vs 208,544 (on) — the ON run is 0.23 % **smaller**, which since
the filters rejected nothing is again pure scatter. This is the Universal Level
Law showing up in a new instrument, and it means the n=9 measurement is not a
proxy for the n=13 conclusion — at this level it *is* the n=13 conclusion.

`endgame_e1_states = 0` was reproduced independently by the implementation,
with the same explanation derived independently: E1 needs `bounds[1] = 1`,
which forces `bounds[0] = bounds[1]` and the early return. **E1 is a dead
branch in this engine** — correct, sound, unit-tested, and unreachable.

### 5.3 The other end is also closed

Symmetrically: the *first*-layer theory (Parberry's canonical first layer, and
[JCSS19] Cor. 4's first/last duality) is likewise already absorbed — at the
root, all first comparators are `G`-equivalent, so `canonicalize(true)` reduces
the entire first layer to a single successor. Both ends of the network are
handled by canonicalisation; the theory has nothing to say about the middle,
which is where 99.8 % of the states live.

---

## 6. Why "it reduces `N`" was the wrong reading

§6b promoted this family as "the only family that attacks `N`". The
82,000× and 30× are reductions in **the number of syntactic layer objects an
enumerator must write down**. Harder's DP does not enumerate layer objects; its
`N` is the number of **reachable canonical output sets**, and no bijection
between the two counts exists. In the generate-and-prune setting the two
coincide because the enumerated object *is* the network prefix; that is exactly
the representational difference the assessment's own §6a identified as
decisive. The end-game theory is a constraint on the **forward network**; the
DP's state is the **output set**, which forgets which network produced it —
and forgetting it is the entire source of the DP's advantage.

---

## 7. The one surviving engineering item (not a state reducer)

Recorded so it is not lost, and consistent with `internals` §8.4:

**Orbit-quotiented successor enumeration.** Let `Aut(X) ≤ S_w` be the setwise
stabiliser of `X`. If pairs `p, q` lie in the same `Aut(X)`-orbit then `c_p(X)`
and `c_q(X)` are channel permutations of each other, hence have the same
canonical form and the same bound; one representative per orbit suffices.
**PROVEN, trivially.** This does *not* reduce the state count (`Edges::add_edge`
already de-duplicates by canonical set) but it does remove redundant
`to_owned` + `apply_comparator` + `canonicalize` work on the hottest path, and
`canonicalize` is the expensive call. This is the correct home for Harder's own
remark that his implementation "does not use orbits of the automorphism group
for pruning". It belongs to the throughput queue, not here.

---

### 7.1 Validation of the patch

| check | result |
|---|---|
| `cargo test --release` | **45 pass / 0 fail** (34 pre-existing + 11 new); baseline tree passes the same 34 |
| round-trip: apply patch to an independently rebuilt 11-patch tree | **byte-identical** source tree, no fuzz, no offset, no `.rej`/`.orig` |
| inertness: all `endgame_*` counters with the env unset | **all zero** |
| results, 3 configs × 4 problems (`n=7/8/9/10`, `-l 16/19/25/29`) | **16 / 19 / 25 / 29 exact, 12/12** |
| reference bound sequences, all 3 configs | **identical**, e.g. `n=9 -l 25`: `5,8,11,14,17,19,21,22,23,24,25` |
| `filter_audit_violations`, audit mode, budgets 1/4/6/9/25 | **0** in every run |
| `"endgame audit violation"` log lines | **0** |
| full pipeline `search → prune-all → gen-proof → snocheck`, `SORTNETOPT_ENDGAME=1` on all three stages, n=9 | frozen snocheck (`4cd30511…a84c`): **`Just (9,25)`** |
| same, n=10 | **`Just (10,29)`** |
| level-5 A/B, `n=11 -l 34`, both arms | **34 / 34**; 0 rejections; 0 audit violations |
| level-5 baseline at target width, `n=13 -l 42` | **42**, 50,968,542 states (archived anchor to 0.09 %), all counters 0 |
| exhaustive model audit, `w ≤ 6`, every reachable state, every budget | **0 soundness violations** (`.build/v3-endgame/verify_w6_final.log`) |

The three configurations are: no env; `SORTNETOPT_ENDGAME=1`;
`SORTNETOPT_ENDGAME=1 SORTNETOPT_ENDGAME_AUDIT=1`.

---

### 7.2 What this does to the level-7 arithmetic

Level 7 is the level whose computation is the goal (`transforms-assessment`
§2.4: `D(13) = 7 or 8`, and no level 7 has ever been computed at any width).
From the measured n=13 level-5 anchor (50,922,864 states) and the measured
per-level multipliers (geometric mean 33.0×, observed maximum 245.9×), at the
hardware constant of 1.5×10⁵ states/s and 44–58 B/state:

| | states | M4-days | TB |
|---|---|---|---|
| level 7, floor multiplier | 5.55 × 10¹⁰ | **4.3** | 2.4 – 3.2 |
| level 7, ceiling multiplier | 3.08 × 10¹² | **238** | 136 – 179 |

Applying end-game theory:

| | floor case | ceiling case |
|---|---|---|
| today | 4.3 d | 237.6 d |
| with the deployed filters (**measured** factor 1.000) | 4.3 d | 237.6 d |
| with the deployed gate's *theoretical ceiling* (1.0008×) | 4.3 d | 237.4 d |
| with a **perfect** two-layer-suffix theory (1.022×) | 4.2 d | 232.5 d |

**Nothing moves.** And the reason is structural, not a matter of a better
implementation: to turn months into weeks you need ≈10×, and by Theorem C that
requires a sound filter whose gate reaches a remaining budget `k` covering
≥ 90 % of the memo:

| gate `k` | removable share | best possible speed-up |
|---|---|---|
| 4 (deployed) | 0.2 % | 1.002× |
| 6 (a perfect two-layer suffix at width 7) | 2.2 % | 1.022× |
| 8 (perfect two-layer suffix at width 8) | 15.6 % | 1.185× |
| 10 | 50.7 % | 2.03× |
| **12** | 85.6 % | **6.93×** |

Even deleting *every* state within **twelve** comparators of sorted — three to
four times the reach of anything in the end-game literature — falls short of
10×. Suffix theory does not move the level-7 computation from months toward
weeks; it does not move it at all.

---

## 8. Open items, conjectures, and what would change the verdict

Recorded so the negative verdict is falsifiable rather than merely asserted.

1. **Prop. C.0** (`bound` never increases along a DP edge) is machine-checked
   exhaustively at `w ≤ 6` and unproven in general. It is the one hypothesis
   Theorem C rests on. A proof, or a counterexample at `w = 7, 8`, is a small
   self-contained problem. A counterexample would *widen* the reach of
   end-game filters and would need this section rewritten.
2. **The unsettled-pair strengthening of E4** (§4) holds at `w ≤ 6` and is
   unproven. If proved it strictly strengthens E4 — but E4's binding condition
   is `2(b−1) < w`, so it cannot escape the §5.1 ceiling.
3. **The adjacency normal form might localise under some canonical form I did
   not try.** §3.3 refutes four natural ones. Since every reachable state at
   `w ≤ 6` does have *some* good labelling, the question "is there a
   state-computable canonical form under which adjacency is sound?" is open.
   It is worth **56 % → 44 % of successor expansions**, i.e. real throughput,
   but by Theorem C it still cannot reduce the state count outside
   `{bound ≤ k}` unless it is sound at *every* budget — which is exactly what
   would have to be proved. This is the single highest-value open question in
   this document and it should be posed as such, not deployed as a heuristic.
4. **What would actually change the verdict** is not a better filter but a
   different gate: a sound rule keyed on something other than the remaining
   budget. Theorem C bites only on budget-gated rules. Subsumption, for
   instance, is not budget-gated, which is why it is worth 160× at `n = 11`
   and end-game theory is worth 1.002 ×.
5. **Observation 5.2 is the item worth taking forward from this campaign**,
   and it is independent of end-game theory. If the engine ever ran a cheap
   upper-bound-improving pass — greedily constructing *some* network for a
   state and storing its length in `bounds[1]` instead of leaving the
   `known_bounds[width]` seed — then every budget-gated technique, this one
   included, would become reachable at a real fraction of expansions, and the
   `--limit` regime's `combined_upper_bound` path would stop being inert.
   Whether that pays for itself is unmeasured and is a separate campaign; it
   is recorded here because this campaign is what made the inertness visible.
   Note that it is a *throughput/ordering* question, not a soundness one.

---

## 9. Reproduction

Archived output of the exhaustive audit:
`.build/v3-endgame/verify_w6_final.log` (`TOTAL FAILURES: 0`).

```bash
# Theory: exhaustive soundness audit of every filter, all reachable states w<=6
python3 tools/verify_endgame.py --max-width 6 --census

# The measurement: level-4 proxy memo census by (width, remaining bound)
.build/v3-endgame/bin/sortnetopt-base search 9 --limit 25 <outdir>
#   state_count(group_<w>_<b>.bin) = filesize / (((1<<w)+7)/8)

# In-engine confirmation (patch): the budget histogram at every expansion
SORTNETOPT_ENDGAME=1 SORTNETOPT_INSTRUMENT_JSON=eg.json \
  .build/v3-endgame/bin/sortnetopt-eg search 9 --limit 25
#   -> eg.json .endgame_upper_hist / .endgame_lower_hist

# Gate sweep: shows the gate plumbing is live and the filters still never fire
for B in 1 4 6 9 25; do
  SORTNETOPT_ENDGAME=1 SORTNETOPT_ENDGAME_AUDIT=1 SORTNETOPT_ENDGAME_BUDGET=$B \
  SORTNETOPT_INSTRUMENT_JSON=eg_b$B.json \
    .build/v3-endgame/bin/sortnetopt-eg search 9 --limit 25
done

# The one measurement deferred to a server (needs ~6 GB headroom, ~9 min):
#   the SORTNETOPT_ENDGAME=1 arm of the level-5 probe
SORTNETOPT_ENDGAME=1 SORTNETOPT_INSTRUMENT_JSON=c2.json \
  .build/v3-endgame/bin/sortnetopt-eg-wide13 search 13 --limit 42 c2_out
#   baseline arm (already measured here): result 42, 50,968,542 states
```

Engine patch: `tools/patches/sortnetopt-endgame-v3.patch`
(1,137 lines, SHA-256
`75fcd8273858e3e7509ccd225b0f23089931526264c518b71ab3d08d536adef9`), twelfth on
the v3 stack, base pin `0b5d09c47446096f9e3a0812b35afc72b7f2a718`. Three files
change — `src/search.rs`, `src/instrument.rs`, and the new
`src/search/endgame.rs`; `Cargo.toml` is unchanged and `checker/` is untouched.
Round-trip verified: applied to an independently rebuilt 11-patch tree
(`.build/v3-endgame/ref`) it produces a **byte-identical** source tree with no
fuzz, no offset, no `.rej`/`.orig`. Inert unless `SORTNETOPT_ENDGAME=1`.
