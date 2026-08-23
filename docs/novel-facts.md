# Novelty Extraction — New, Provable Facts Not Yet Claimed

**Date:** 2026-08-23.
**Machine check:** `tools/verify_novel_facts.py` (pure stdlib, deterministic,
~5 s, 44 checks, exit 0). Certificate census: `.build/v3-novelty/cert_census.py`
(stdlib, mmap, read-only, ~13 s). Engine A/B ladder:
`.build/v3-novelty/ladder/*.log`.
**Scope:** read-only with respect to `src/`, `evidence/`, `config/`, `ledger/`.
New files: this document, `tools/verify_novel_facts.py`, and scratch under
`.build/v3-novelty/`. No commits.

**Scope note (mirrors `audit-paper-v2.md` §10.8).** No search for a sorting
network was run for the *mathematical* results below, no candidate network was
constructed, and no witness exists anywhere in this work. The integer 44 appears
only as the tabulated value under audit, used to instantiate hypotheses of the
form "suppose such a network existed; what must it look like". It is never a
target, bound, feature or stopping condition of any search or learning
procedure. The engine runs reported in §1 are census measurements at `n = 11`
and terminate at `C(11)+ℓ` for `ℓ ≤ 5`.

---

## 0. Ranked summary

| # | fact | status | where it goes |
|---|---|---|---|
| **1** | **Twenty entries, not one.** The eq(8) chain reproduces Dobbelaere's published lower bounds at every `N = 13..32` exactly (first written derivation of a table published with no proof); every one of the 20 strictly exceeds the unconditional one-value floor, so every one depends on the equation the audit breaks; and Wikipedia's table prints the one-value column instead, so the two public tables contradict each other at every `N = 13..20` and this work adjudicates. | **PROVEN** | §4.2, as a table; it generalises the paper's headline from one entry to the whole tail |
| **2** | Theorem 6 **is** assumption E1′. The three-class shape case split (C1/C2/C3, 84 plane / 6 abstract shapes) is therefore *unconditional* on the escape-free class — no Plenum chapter required. | **PROVEN** (on that class) | new subsection after §5.2; a positive corollary of the repair |
| **3** | The matched-configuration level-5→6 multiplier is **20.20×**, not the 1.88× the unmatched figures suggest. This is the measurement §8.2 names as "the single measurement that would most change this picture, and it has not been done". It removes the paper's stated anomaly. | **EMPIRICAL** | §8.2, replacing the "provisional" paragraph |
| **4** | The published level-7 bracket is a *plain-configuration* bracket. Recomputed in the memory-frugal configuration the certified run actually used, level 7 is 6.8e8–4.0e9 states — 82× below the old floor, 763× below the old ceiling, and roughly 250 GB against ~324 GiB free. **The standing "Go/no-go: NO" should be reopened.** | **EMPIRICAL** | §8.2 |
| **5** | Unconditional structure of a hypothetical minimum-size 13-sorter: both branch trees Kraft-tight with 13 leaves, height in {4,5}, 13 admissible depth profiles, a forced size-optimal 12-sorter minor, and depth-5 leaves forced pass-through-free. | **PROVEN** | new §8.1a, "what such a network must look like" |
| **6** | `|Reach(13,6)| = 95,221,145`, and the complete `n = 13` level ladder for `ℓ = 1..6`. | **PROVEN** (the +2) / **EMPIRICAL** (the base) | §8.2, printed as a table |
| **7** | The certified certificate's true width census, and a correction to the prune-all survivor figures (10,275,769, not 10.47 M; every per-width figure overstated). | **PROVEN** (recomputed from the deposited certificate) | §7, correcting the pipeline table |
| **8** | The quoted per-level multipliers are the `n = 13` column, not "the `n = 12` ladder", and their level-1..4 inputs are the census figures the project later retracted as scheduling noise. | **PROVEN** (arithmetic) | §8.2 footnote |
| **9** | The extremes-pair deletion bound `|C| ≥ S(N−2) + |maxpath(i) ∪ minpath(j)|`, the max/min analogue of `p(2,T)`. Both objects it involves are genuine trees, so it routes around `MAX2` — the exact object whose tree-ness is the audited false premise. | **PROVEN** (the bound); novelty **UNVERIFIED** pending prior-art check | §10.5, as a direction |
| **10** | The shape case split is *not* measurable on the backward census; the DP state does not determine max-path geometry. | **PROVEN** (negative) | §8.3, with the other negative results |

---

## 1. What the certified level-6 data gives at n = 13

### 1.1 The exact census (fact 6)

By Theorem 12, `Reach(13, ℓ) = Reach(11, ℓ) ⊎ {cube_12, cube_13}` for `ℓ ≤ 6`,
since `n_min(ℓ) ≤ 11` there. The `+2` is **PROVEN**. The base measurement is
what it is.

| level ℓ | `\|Reach(11,ℓ)\|` | `\|Reach(13,ℓ)\|` = base + 2 | measured at 13 | agree |
|---|---|---|---|---|
| 1 | 39 | **41** | 41 | yes |
| 2 | 449 | **451** | 451 | yes |
| 3 | 24,201 | **24,203** | 24,203 | yes |
| 4 | 207,997 | **207,999** | 207,999 | yes |
| 5 | 50,594,721 | **50,594,723** | — | — |
| 6 | 95,221,143 | **95,221,145** | — | — |

Levels 1–4 are single-threaded deterministic runs and the agreement is exact —
four independent confirmations of Theorem 12 at the level of the whole stored
key set. Levels 5 and 6 are multithreaded, where the stored census is
run-dependent at the 1–2 % level; those two rows are **EMPIRICAL**.

`|Reach(13,6)| = 95,221,145` has never been computed at `n = 13` by any means,
and the paper currently only implies it. It should be printed.

**Honesty item the paper must carry.** Under `SUBSUME=evict` the engine's
reported figure is an *insertion* counter, while the stored census is
insertions minus evictions (`IDX_EVICTIONS`). The certified run's log does not
survive, so which quantity 95,221,143 is cannot be determined from artifacts.
Our A/B ladder shows the gap is real and grows fast with level: at `n = 11`,
inserts − entries is 0 at levels 1–2, 172 at level 3, 3,214 at level 4 and
**339,364 at level 5** (7.2 % of that level's insertions). At level 6 it will be
larger still, so the two candidate readings of 95,221,143 differ by something on
the order of ten per cent — enough to matter for a printed census figure and not
enough to affect any conclusion here.

### 1.2 The matched-configuration measurement (fact 3)

`audit-paper-v2.md` §8.2 states: *"Re-deriving the multiplier under matched
settings is the single measurement that would most change this picture, and it
has not been done. Until it is, the level-7 bracket is provisional."*

It has now been done, at `n = 11`, four threads, same binary
(`.build/v3-ambient/bin/sortnetopt-det-base`), two configurations:

* **A (plain)** — no `SORTNETOPT_*` beyond the thread pin. This is the regime
  the published multipliers were measured in.
* **B (certified-matched)** — `SUBSUME=evict`, `SUBSUME_DIMS=96`,
  `SUBSUME_WIDTHS=8,9`. This is the regime the certified level-6 run used.

| level | A inserts | B inserts | B/A | B entries | evictions | A peak RSS | B peak RSS |
|---|---|---|---|---|---|---|---|
| 1 | 41 | 40 | 0.976 | 40 | 0 | | |
| 2 | 452 | 454 | 1.004 | 454 | 0 | | |
| 3 | 23,960 | 19,241 | 0.803 | 19,069 | 172 | | |
| 4 | 210,051 | 136,789 | 0.651 | 133,575 | 3,214 | | |
| **5** | **50,400,015** | **4,714,517** | **0.094** | 4,375,153 | 339,364 | 2.81 GB | **438 MB** |
| 6 | — | 95,221,143 (certified) | — | — | — | — | 13.08 GB |

**The correction is not a small constant, and this is exactly why the
measurement was worth making.** It is ~1.0 at levels 1–2, 1.25× at level 3,
1.54× at level 4 — and then **10.7× at level 5**. We initially extrapolated the
shallow-level trend and predicted a correction near 1.5–2×; the measurement
refuted that by a factor of five. Any reasoning from levels 1–4 alone about this
configuration is unsafe, in either direction.

> **The matched multiplier, which is the number §8.2 asks for:**
> `95,221,143 / 4,714,517 = ` **20.20×**.

The unmatched reading of 1.88× was wrong by 10.7×. Two consequences the paper
should state:

* **The paper's worry does not survive.** §8.2 flags 1.9× as "far below the
  optimistic floor of 8.4×". The matched value, 20.2×, is comfortably *above*
  that floor and below the 33× geometric mean. There is no anomaly to explain.
* **The two configurations have different growth rates**, and that is the real
  finding:

| ladder | per-level multipliers | geometric mean |
|---|---|---|
| config A (plain) | 11.02 / 53.01 / 8.77 / 239.94 | **33.30×** |
| config B (frugal) | 11.35 / 42.38 / 7.11 / 34.47 / 20.20 | **18.85×** |

Config A reproduces the published 33.0× — confirming that **the published
level-7 bracket is a config-A bracket**. Config B, the configuration the
certified run actually used, grows at 18.85×, and its level-4→5 multiplier is
34× where config A's is 240×.

### 1.3 What that does to the level-7 bracket (fact 4)

A level-7 run would be run in config B or something like it — that is the whole
point of the memory-frugal stack, and it is what the certified run used. So the
operationally relevant estimate is a config-B estimate, anchored on the measured
config-B level-6 census and scaled by config-B's own observed multipliers:

| case | multiplier | level-7 states |
|---|---|---|
| floor | 7.11× | **6.8e8** |
| geometric | 18.85× | **1.8e9** |
| ceiling | 42.38× | **4.0e9** |

against the standing bracket of **5.55e10 – 3.08e12** states, which carries the
"Go/no-go: NO" on a disk wall short by 7.4× at the floor. The new floor is
**82× below** the old floor; the new ceiling is **763× below** the old ceiling.

At the certified run's measured 137 bytes per stored state, 1.8e9 states is of
order **250 GB**, against ~324 GiB free on the owned server. The binding wall
was disk, and on these numbers it is no longer binding.

**The finding is not that the old extrapolation was arithmetically wrong.** It
is that it was computed in a configuration nobody would use for a level-7 run.
Config A was chosen for the multiplier study because it is the clean,
subsumption-free regime; but subsumption's state reduction grows sharply with
level, so a config-A extrapolation systematically overstates the cost of a run
that would be done in config B, and overstates it by more the deeper you go.

**Caveats, both live.**

* This is EMPIRICAL and extrapolated. The 6→7 multiplier is not measured and
  cannot be — level 7 exists at no ambient below 13 (`n_min(7) = 13`), so there
  is no cheaper rehearsal. We are using config B's own measured spread as the
  bracket, which is the best available but is still a guess about one number.
* Config B's reduction factor *grew* across the ladder (1.0, 1.0, 1.25, 1.54,
  10.69). If it keeps growing at 6→7, level 7 is cheaper still. If it saturates
  — subsumption is pinned to widths 8 and 9, and the mass front moves to wider
  states as the level rises — the config-B multiplier at 6→7 could be larger
  than anything in the table above. Pinning `SUBSUME_WIDTHS` to the widths where
  the mass actually sits at level 6/7 is now an obvious and untried lever.
* One further datum in the same direction: config B cost only **18 % more wall
  time** than config A at level 5 (930 s vs 789 s) while using **6.4× less
  memory** (438 MB vs 2.81 GB). The paper's §8.3 figure "on-line subsumption
  nets 2.7×" is a shallow-level measurement; at level 5 the state reduction
  alone is 10.7×.

**Recommendation to the architect: the standing "Go/no-go: NO" on level 7 should
be reopened.** It is the single most consequential thing in this document after
fact 1.

### 1.4 The certificate's true census (fact 7)

The deposited certificate is on disk
(`.build/n11-cert/proof_n11_ours.bin`, 2,442,317,348 B, SHA-256
`672c433f…c08e38`) and its step table is a complete `(width, bound)` record of
every obligation. Recomputed directly:

| width | steps | report.md claim | delta |
|---|---|---|---|
| 3 | 2 | — | |
| 4 | 14 | — | |
| 5 | 291 | — | |
| 6 | 14,166 | — | |
| 7 | 344,956 | — | |
| 8 | 2,517,617 | "2.69 M" | −172,383 |
| 9 | 5,280,284 | "5.60 M" | −319,716 |
| 10 | 2,015,476 | "2.09 M" | −74,524 |
| 11 | 102,963 | 102,966 | −3 |
| **total** | **10,275,769** | "10.47 M survivors" | **−194,231** |

Every published per-width survivor figure is overstated, by 1.9 % in total.
`evidence/v3/n11-certified/report.md` and `audit-paper-v2.md` §7 both carry the
wrong numbers; both are unsourced prose (the prune-all log does not survive).
The certificate is the authority and it disagrees. Either gen-proof drops steps
relative to prune-all survivors, or the prose was never right; the paper should
quote the certificate-derived figures and say which quantity it means.

The full width × bound joint distribution is now available (widths 3–11, bounds
2–35): 10,275,769 output sets, each with a bound accepted by an unchanged
extraction of a formally verified checker, and each — by the bound-transport
corollary — valid at every ambient `n ≥ w`. **This is not a first**; Harder's
2.9 GB certificate is the same kind of object and is larger. What is new is that
the *distribution* has, as far as we can tell, never been reported for either
certificate, and that this one is independently generated. The claim to make is
"a second, independent such library, whose census we publish", not "the first".

### 1.5 Two things the level-6 data does *not* give (fact 10)

* **The shape-class composition is not measurable.** A census state is a
  canonical `OutputSet`; the max-path depths `δ(C,i)` are not functions of it
  (different prefixes with different max-path geometry share a state, and
  canonicalisation discards the channel labelling). `s13-shape-case-split.md`
  §7.3 says the same thing prospectively; we confirm it. No class is shown
  depleted or empty by the census, and none can be.

  *Refinement worth recording.* The state does determine the max tree's **size**
  even though it does not determine its shape. Comparators preserve Hamming
  weight, so the weight-1 elements of `X` are exactly the images of the 13
  one-hot inputs, and two of them coincide precisely when the corresponding
  max-paths have merged. Hence `#{v ∈ X : |v| = 1}` is the number of unmerged
  max-tree blocks, and `13 − that` is the number of merge comparators so far;
  the weight-`(w−1)` elements give the dual count. This is a genuine, cheap,
  forward-monotone bridge between the set-DP state and max-tree geometry, and it
  sharpens §7.3's blanket "the state does not determine `δ`". **Flagged as
  unverified against the engine's canonicalisation**, which may identify a set
  with its complement and does reduce width on prune edges; both would need
  checking before this is used.
* **No useful lower bound on `|Reach(13,7)|`.** Monotonicity in the root limit
  would give `|Reach(13,7)| ≥ 95,221,145`, three orders below the extrapolation;
  it is not worth stating.

### 1.6 The multiplier provenance error (fact 8)

`audit-paper-v2.md` §8.2 attributes the multipliers 12.5 / 46.1 / 8.4 / 245.9 to
"the `n = 12` ladder". They are the **`n = 13`** column of
`transforms-assessment.md` §2.3 (43 / 537 / 24,761 / 207,097 / 50,922,864). The
`n = 12` ladder gives 12.88 / 47.52 / 8.09 / 244.10.

Worse, the level-1..4 inputs to that column are exactly the multithreaded
figures the same project later retracted as thread-scheduling noise
(`ambient-reduction.md` §4.1–4.2 — the deterministic values are 41 / 451 /
24,203 / 207,999). Recomputed deterministically the multipliers are 11.00 /
53.67 / 8.59 / 243.25. The individual factors move by up to 16 %; the geometric
mean moves only from 32.99× to 33.38×, so the bracket is not materially
affected — but the paper prints four figures to four significant digits that are
noise at the second, and attributes them to the wrong ladder.

The reason the geometric mean is robust while its factors are not is worth one
line, because it also says which quantity to trust: the product telescopes to
`|Reach(ℓ=5)| / |Reach(ℓ=1)|`, so the geometric mean depends **only on the two
endpoints** and is insensitive to everything between them. Conversely, any
argument that leans on the *individual* factors — including the alternating /
travelling-wave reading used to choose a 6→7 multiplier — is leaning on numbers
that move by 16 % under a scheduling change. That is a caveat the level-7
extrapolation in §1.3 must carry, and it cuts against the tidier reading.

---

## 2. The unconditional structure theorem (fact 5)

`audit-paper-v2.md` contains **nothing** about the structure of a hypothetical
minimum-size 13-sorter; the v0.1 draft's material was conditional on eq (8) and
was dropped. Everything below is unconditional. It uses only:

* **(F1)** deleting a channel at either polarity from an `N`-sorter removes
  exactly the comparators on that channel's extremal path and leaves an
  `(N−1)`-sorter, so `|C| ≥ S(N−1) + δ(C,i)` for every `i` and both polarities;
* **(F2)** the branch tree `B` of the max computation has `N` leaves and `N−1`
  internal nodes, and `δ(C,i) = depth_B(i) + pt(C,i)` where `pt` counts
  pass-throughs on `i`'s max-path — this is Proposition 3 of the paper, used in
  the safe direction exactly as §4.3 does;
* **(F3)** Kraft equality on a full binary tree;
* **(F4)** the duals for the min computation.

No step uses eq (8). Write `m` for the tabulated size and reserve `B` for the
branch tree throughout.

> **U1 (path ceiling).** Every extremal path of such a network, at either
> polarity, has at most `m − S(12) = 5` comparators. Hence for every channel
> `i`: `depth_B(i) + pt(C,i) ≤ 5`.
>
> **U2 (pass-through exclusion).** A leaf at branch-depth 5 has a
> **pass-through-free** max-path. This links the audit's central object —
> pass-throughs — to the `n = 13` question directly, and unconditionally.
>
> **U3 (heights).** Both branch trees have height in `{4,5}`.
>
> **U4 (profiles).** The leaf-depth multiset of either branch tree is one of
> exactly **13** Kraft-tight profiles with all depths ≤ 5 (enumerated by the
> verifier). If a branch tree has height 4 there are only **2**.
>
> **U5 (forced optimal minor).** If any extremal path has length 5, deleting
> that channel leaves a **size-optimal 12-sorter** (`m − 5 = 39 = S(12)`), in
> which every extremal path has length ≤ 4, both branch trees have height
> exactly `⌈log₂ 12⌉ = 4`, and the depth profile is one of exactly 2.
>
> **U6 (deletion slack).** Over any iterated channel deletion from 13 down to
> `k`, the total number of removed comparators is at most `m − S(k)`; and one
> may always remove at least `⌈log₂ j⌉` at the step from `j` channels, by
> deleting a deepest leaf. The chain is tightest at `k = 12` and `k = 11`, where
> the slack is exactly **1**. Concretely: such a network has a one-channel
> deletion minor that is a 12-sorter with **39 or 40** comparators, and a
> two-channel deletion minor that is an 11-sorter with **35 or 36** — in both
> cases within one comparator of optimal. Every deeper `k` has slack ≥ 3, so
> `k = 11, 12` are the only places the chain binds.
>
> **U7 (extremes pair).** For all `i ≠ j`,
> `|maxpath(i) ∪ minpath(j)| ≤ m − S(11) = 9`, because feeding `+∞` to `i` and
> `−∞` to `j` determines every comparator on either path and all of them may be
> deleted by rewiring, leaving an 11-sorter.
> *Corollary (dichotomy, with hypothesis).* If the deepest max-path and the
> deepest min-path are comparator-disjoint, then `h(B_max) + h(B_min) ≤ 9`, so
> they cannot both be 5 — at least one branch tree has minimum height 4. The
> two paths *can* share comparators, so this is stated with its hypothesis and
> the hypothesis is not hidden.

U7 is the max/min analogue of the chapter's max/second-max quantity `p(2,T)`,
and it deserves a paragraph of its own, because of *why* it is interesting.

The chapter's two-channel deletion removes the maximum and the **second**
maximum. Its Kraft step (eq (6)) needs `MAX2(T)` to be a binary tree, and the
entire content of this project's audit is that `MAX2(T)` **is not a tree** — the
lead-level successor map is not even a function (`N4`, the minimal `n = 4`
witness). The one broken object in the argument is the second-maximum structure.

The max/min deletion removes the maximum and the **minimum**. Both of the
objects it involves — `B_max` and `B_min` — are honest binary trees with `N`
leaves, by the same elementary argument, and both are Kraft-tight. The variant
therefore avoids precisely the object whose tree-ness is the false premise.

> **Direction for §10.5.** Is there a Kraft-style lower bound on
> `min_C max_{i≠j} |maxpath_C(i) ∪ minpath_C(j)|`? At `N = 13` a value of 10
> would settle the question, and the argument would run entirely through two
> genuine trees. The obstruction is the overlap term: the two paths can share
> comparators (they meet, separate at the shared comparator's two outputs, and
> can meet again), so a bound needs a handle on `|maxpath(i) ∩ minpath(j)|` that
> the height arguments alone do not supply.

We make no claim about its difficulty, and we flag one caveat honestly: we have
not found this variant treated in the sources in hand, but the max/min deletion
is elementary enough that a prior-art check is required before claiming it as
new. What is new with confidence is the *observation* that it routes around the
audited defect.

---

## 3. The case split, made unconditional (fact 2)

This is the sharpest positive consequence of the repair, and it is not in the
paper.

`s13-shape-case-split.md` §3 states its own trust boundary in the strongest
terms: the split needs **E1′**, the *per-network*, un-minimised form

> for a 13-sorter `C` with induced branch tree `T(C)`, the deleted-comparator
> count satisfies `P ≥ ⌈log₂ V(T(C))⌉`

and records: *"That is … an assumption and it carries the entire case split.
… Confirming E1′ is the single highest-value question to put to the primary
source."*

**Theorem 6 of the paper is E1′.** It states, for every escape-free `N`-sorter,
`|T| ≥ S(N−2) + ⌈log₂ f(B)⌉` — per-network, un-minimised, over the network's own
branch tree. Two machine checks close the identification:

* `f(B) = Σ_c 2^{a(c)}` (the paper's §2 definition) equals `V(T)` (the shape
  literature's recursion) on **all 208,012** plane shapes with 13 leaves, and on
  every shape with ≤ 11 leaves. They are the same function. (Checks C1, C2.)
* At `N = 13` and the tabulated size, Theorem 6 forces `⌈log₂ f(B)⌉ ≤ 9`, i.e.
  `f(B) ≤ 512` — exactly the admissibility condition. (Check C3.)

> **New corollary (PROVEN, no appeal to eq (8), no appeal to the Plenum
> chapter).** Let `C` be an escape-free 13-sorter of the tabulated size. Then
> its max branch tree is one of the **84 admissible plane shapes** (6 up to
> reflection), its root splits the 13 leaves as 5+8, 6+7 or 4+9, and its
> leaf-depth profile is one of exactly 4. Equivalently: `C` lies in `C1 ∪ C2 ∪
> C3`, and that trichotomy is exhaustive and disjoint.
>
> **Dual.** If `C` and its reverse-and-flip dual are both escape-free, then
> *both* branch trees are admissible — two independent shape constraints.

*Inherited caveat.* Theorem 6 is a human proof, not machine-checked as a proof
(`audit-paper-v2.md` §10.2), so the corollary inherits exactly that status. What
*is* machine-checked here is the identification `f = V` and the finite shape
enumeration — i.e. everything except Theorem 6 itself. Formalising Theorem 6,
which §10.2 already calls "small and the natural next step", would make this
corollary fully machine-checked; that raises its value considerably and is now a
better-motivated task than it was.

The verifier reproduces the case-split document's numbers independently:
84 plane / 6 abstract / 3 root classes, heights exactly `{4,5}`, smallest
excluded count 528 (a 3.1 % robustness margin), class sizes 12 / 48 / 24.

Two further consequences that only appear once the two documents are joined:

* **Node budget.** For an escape-free network at the tabulated size,
  `p(2,T) ≤ 9`, and by Lemma 5 `p(2,T) = max_c[a(c) + ε(c) + γ(c) + r(c)]`. Every
  admissible shape has `max_c a(c) = 7` — uniformly, across all three classes —
  so **at the worst branch node, `ε(c) + γ(c) + r(c) ≤ 2`.** That is a very
  tight local constraint on exactly the three decorations the paper identifies
  as the whole content of eq (8) (§5.1, §10.5).
* **Rigidity inside C3.** Exactly 8 plane shapes have `f(B) = 512`, and all 8
  lie in class C3 (they are the `S6` orbit). A network on one of them is
  *tight*, since `f(B) = 2^9 = 2^{p(2,T)}`. The rigidity theorem then applies
  with margin 0: at **every** branch node `ε(c) = 0`, `γ(c) = ov(c)`,
  `W*(c) = p(2,T)`. Combined with U2 this forces a network with no
  pass-throughs anywhere on the deepest paths and two or four channels at
  extremal-path length exactly 5.

  *Citation warning.* That rigidity statement is **Theorem 7 of
  `kraft-repair-wave2.md` §5.1**, which is a different result from **Theorem 7
  of `audit-paper-v2.md` §5.3** (the `(C)∧(D)` form of eq (8)). The numbering
  diverged between the wave documents and the paper — wave2's 6′ → paper 6,
  wave2's 6″ → paper 7, wave2's 8 → paper Proposition 8 — and wave2's rigidity
  theorem was **not carried into paper v2 at all**. If this corollary goes into
  the paper, that theorem has to be carried in with it, or the sentence has no
  referent.

**What this changes for the programme.** The case split was parked behind an
inter-library loan. It no longer needs one, on a class the project can define,
check, and has already measured (escape-free is 22.3 % of the audit census, and
the paper's own §10.3 asks precisely the right follow-up question: what fraction
of *size-optimal* networks is escape-free). The honest limitation is exactly
that: the split is now proved on the escape-free class and remains conditional
off it, so refuting C1/C2/C3 by search would establish the bound only for
escape-free networks. That is strictly more than the case split had before,
which was nothing unconditional at all.

---

## 4. Consequences for other `n` (fact 1)

### 4.1 The repair theorems give no new numerical bound at any `n`

Checked and negative. Theorems 6, 7 and Proposition 8 are indexed by a
*structural hypothesis on the network*, not by `N`. No hypothesis among them is
known to hold for an arbitrary size-optimal `n`-sorter, and none can be checked
without the network in hand. There is therefore no `n` at which they yield an
unconditional numerical bound, including `n = 13`. Nor do they give a cleaner
proof of any known value: the two-value inequality has slack
`0,0,0,1,0,0,1,2,2,1` at `N = 3..12`, never negative, so no known value is even
near the boundary where the escape-free case could bite.

### 4.2 The audit's scope is twenty entries, not one — and the two public tables disagree

The paper says only that `S(13) ≥ 43` is unaffected. It does not say what
follows for `N ≥ 14`, whose entries are in the same table and derive from the
same equation. It follows for all of them.

`F(N)` was regenerated to `N = 32` by exact-shape minimisation (not by the
chapter's relaxation (19), which is only known to agree for `N ≤ 16`), and
cross-checked two ways: it reproduces van Voorhis's Table 1 for `N ≤ 16`, and
brute-force enumeration of all 208,012 thirteen-leaf shapes agrees with the
height DP at `N = 13`.

| N | F(N) | ⌈log₂F⌉ | **one-value (PROVED)** | eq(8) chain | Dobbelaere | Wikipedia | deficit |
|---|---|---|---|---|---|---|---|
| 13 | 392 | 9 | **43** | 44 | 44 | 43 | 1 |
| 14 | 424 | 9 | **47** | 48 | 48 | 47 | 1 |
| 15 | 480 | 9 | **51** | 53 | 53 | 51 | 2 |
| 16 | 512 | 9 | **55** | 57 | 57 | 55 | 2 |
| 17 | 784 | 10 | **60** | 63 | 63 | 60 | 3 |
| 18 | 848 | 10 | **65** | 68 | 68 | 65 | 3 |
| 19 | 960 | 10 | **70** | 73 | 73 | 70 | 3 |
| 20 | 1024 | 10 | **75** | 78 | 78 | 75 | 3 |
| 21 | 1232 | 11 | **80** | 84 | 84 | — | 4 |
| 22 | 1296 | 11 | **85** | 89 | 89 | — | 4 |
| 23 | 1408 | 11 | **90** | 95 | 95 | — | 5 |
| 24 | 1472 | 11 | **95** | 100 | 100 | — | 5 |
| 25 | 1872 | 11 | **100** | 106 | 106 | — | 6 |
| 26 | 1936 | 11 | **105** | 111 | 111 | — | 6 |
| 27 | 2048 | 11 | **110** | 117 | 117 | — | 7 |
| 28 | 2112 | 12 | **115** | 123 | 123 | — | 8 |
| 29 | 2320 | 12 | **120** | 129 | 129 | — | 9 |
| 30 | 2384 | 12 | **125** | 135 | 135 | — | 10 |
| 31 | 2496 | 12 | **130** | 141 | 141 | — | 11 |
| 32 | 2560 | 12 | **135** | 147 | 147 | — | 12 |

Three separate results are in that table.

**(a) The first written derivation of Dobbelaere's 2025 lower bounds.** The
eq (8) chain reproduces the published column at **every one of `N = 13..32`,
exactly, 20 of 20**. Dobbelaere's page carries those numbers with a one-line
changelog — *"2025-04-21 Tighter lower bounds for size, on suggestion of Jelmer
Firet and based on principles in [VVoorh72]"* — no derivation, no citation on
the row, and (per §4.2 of the paper) no locatable publication. We can now say
exactly what they are: `S(N) ≥ max(S(N−1) + ⌈log₂ N⌉, S(N−2) + ⌈log₂ F(N)⌉)`
seeded at `S(11) = 35`. That is a provenance result of the same kind the paper
already does for `n = 13`, extended to the whole table and *confirmed
constructively* rather than by absence of evidence.

**(b) Every one of those 20 entries depends on eq (8).** Each strictly exceeds
the one-value floor, and the only route to the excess in the literature is the
equation the paper shows is unproved and whose published derivation it shows is
invalid. The audit does not bear on `S(13)` alone; it bears on `S(13)` through
`S(32)`.

**(c) The two most-consulted public tables disagree at every `N` from 13 to 20,
and the audit adjudicates.** Wikipedia's "Size, lower bound" row is exactly the
one-value column — 43, 47, 51, 55, 60, 65, 70, 75 — and footnotes itself
*"Obtained by Van Voorhis lemma and the value S(11) = 35"*. Dobbelaere's is the
eq (8) column. OEIS A003075, which Dobbelaere's column header credits, lists no
lower bound at all for any `N ≥ 13` and has no b-file. So the record is
three-way inconsistent, and this work says which column is defensible: **the
Wikipedia one.** The deficit grows from 1 comparator at `N = 13` to 12 at
`N = 32`.

> **The statement for the paper.** The published lower-bound table has no
> unconditional support at any `N ≥ 13`. The unconditional table is 43, 47, 51,
> 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130, 135 for
> `N = 13..32`, and it is the one Wikipedia already prints.

This is the largest single upgrade available to the paper's value. It turns "one
web-table entry rests on a broken argument" into "twenty entries rest on it, the
two public tables contradict each other, and here is the machine-checked
adjudication". It costs one paragraph and one table and refutes nothing that was
proved.

*What is not new:* the twenty numbers themselves. They are all already published
by Dobbelaere, `N = 18..32` included. What is new is the derivation, the
dependency finding, and the adjudication.

### 4.3 The whole table bottoms out on S(11) = 35

Both chains reduce to `S(11) = 35` and to no other computed value: `S(12) = 39`
is one-value from it, and every entry at `N ≥ 13` is a chain above `S(11)` or
`S(12)`. Machine-checked (A8, A9), including the sensitivity: replacing
`S(11) = 35` by 34 lowers every entry `N ≥ 12` by at least 1.

`S(11) = 35` had exactly one machine proof — Harder's 2.9 GB certificate. This
project produced the second, independent one, from a rebuilt engine, accepted by
an unchanged extraction of the same verified checker. The paper presents this as
a reproduction. It is better described as **the independent confirmation of the
single deepest computational input to every published lower bound above
`n = 11`**, and that framing is both accurate and materially more valuable.

---

## 5. Reproduction

```
python3 tools/verify_novel_facts.py              # 44 checks, exit 0, ~5 s
python3 tools/verify_novel_facts.py --section C  # the case-split corollary
python3 .build/v3-novelty/cert_census.py         # certificate census, ~13 s
```

The A/B ladder is reproduced by, for `L` in 30..34 and each config:

```
export SORTNETOPT_POOL_THREADS=4
# config A: nothing further
# config B:
export SORTNETOPT_SUBSUME=evict SORTNETOPT_SUBSUME_DIMS=96 \
       SORTNETOPT_SUBSUME_WIDTHS=8,9
.build/v3-ambient/bin/sortnetopt-det-base search 11 -l $L <outdir>
```

Logs are under `.build/v3-novelty/ladder/`.
