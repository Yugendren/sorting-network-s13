# Repairing van Voorhis's Kraft Step, and the MIN-Side Route

**Date:** 2026-08-18
**Companion to:** `docs/van-voorhis-theory-report.md` (which established that the
chapter's proof of eq (8) is invalid as written). This document does not rewrite
that report; §6 records the one correction it forces.
**Machine check:** `tools/verify_huffman2.py` — now 48 checks, exit 0.
**Independent corroboration:** `tools/verify_kraft_dispute.py` (written
separately, from the chapter text, importing none of my code) reaches the same
verdict on eqs (5), (6), (8) and supplied the counterexample of §3.2.
Parts **G** (repair) and **H** (MIN side) are new. Exploratory scratch:
`.build/v3-theory/redblue.py`, `.build/v3-theory/kraft_repair.py`,
`.build/v3-theory/minside.py`.

---

## 0. Verdicts

> **1. A COMPLETE, CORRECT PROOF OF eq (8) NOW EXISTS FOR A LARGE CLASS.**
> Call an `N`-sorter **clean** if every comparator its max-paths traverse is a
> branch node (equivalently `|MAX(T)| = N-1`, i.e. no pass-throughs). For clean
> sorters I prove eq (8) outright — §2. The proof supplies the antichain step van
> Voorhis assumed, and weakens his Kraft *equality* (6) to the *inequality* the
> argument actually needs. **This is, as far as I can establish, the first
> correct proof of any case of the 1972 theorem.**
>
> **2. The general case is NOT repairable by per-node charging — I refuted my
> own candidate lemma.** I isolated what pass-throughs break and proposed
> **LEMMA★** (`sum_c 2^{a(c) - W*(c)} <= 1`), which implies eq (8) and which
> survived 900 constructed sorters with supremum exactly 1. **It is false.** An
> explicit 15-comparator 6-sorter gives `33/32 > 1` under the *best*-choice
> pairing, and a 7-channel sorter breaks the deepest-leaf version. Since
> LEMMA★ was only ever *sufficient* for eq (8), **eq (8) is untouched** — but the
> entire family of per-node charging repairs is now closed off, and any valid
> proof must be **global**. §3.
>
> **3. The MAX/MIN incompatibility route is REFUTED in its shape-only form.**
> I had ranked it #3 in `docs/van-voorhis-theory-report.md` §6.4. Batcher's
> **8**-sorter has `f(MAX) = f(MIN) = 96 = F(8)`, and Batcher's **12**-sorter has
> `f(MAX) = f(MIN) = 288 = F(12)` (also `n = 3,4,6,7`). At `n = 13` a constructed
> 13-sorter has `f(MAX) = 512` and `f(MIN) = 392`, **both admissible**. So no
> theorem of the form *"both trees cannot be admissible"* exists. Any MAX/MIN
> argument at `n = 13` **must use the size hypothesis**, not shapes alone. §5.
>
> **4. `P(2,11) = 9` reduces to a statement about exactly ONE shape.**
> `F(11) = 256 = 2^8` is attained by a **unique** abstract shape (8 plane
> shapes); the next attainable value is **272**, and `ceil(log2 272) = 9`. So the
> whole of van Voorhis's unproved claim is: *every 11-sorter whose MAX branch
> tree is that one shape admits a pruning of ≥ 9 comparators.* §4.
>
> **5. New and useful: every admissible shape is REALIZABLE.** All 6 admissible
> `n = 13` shapes, and the unique `n = 11` minimiser, are the MAX branch tree of
> an explicitly constructed, **clean** sorter (§7). So none of C1, C2, C3 is
> structurally empty, and `P(2,11) = 9` cannot be dodged by unrealizability.

---

## 1. Setup: the exact decomposition

Fix an `N`-sorter `T`. A **lead** is a wire segment (a channel between two
consecutive comparators on it, including the input and output segments).

For an ordered pair `(x,y)` of distinct input channels, run the scenario *max at
`x`, second max at `y`*, all other inputs smaller. Let `W(x,y)` be the set of
comparators touched by either value; `p(2,T) = max_{x,y} |W(x,y)|`, and
`|T| >= S(N-2) + p(2,T)` (chapter eq (2), machine-verified by path contraction,
check **B5**).

`MAX(T)` is the set of comparators traversed by some max-path. A comparator is a
**branch node** iff max-paths reach it on *both* of its input leads; `B` denotes
the **branch tree** — `N` leaves (the input channels), `N-1` branch nodes. Write

```
a(c) := lp(L(c)) + lp(R(c)) + depth_B(c) + 1       f(B) = sum_c 2^{a(c)}
```

which is exactly Theorem 1's recursion (checks **A1**, **A2**).

**Fact 1 (first meeting).** The max and second max first meet at
`c = LCA_B(x,y)`. *Proof.* The second max is larger than everything except the
max, so until they meet it takes the high output at every comparator — i.e. it
follows `y`'s max-path. Two max-paths first share a comparator at their branch
tree LCA. ∎

**Fact 2 (decomposition).** With `c = LCA_B(x,y)`,

```
|W(x,y)| = δ(x) + e(y,c) + r(c)
```

where `δ(x)` = number of comparators on `x`'s max-path; `e(y,c)` = number of
comparators strictly between `y` and `c` on `y`'s max-path; and `r(c)` = number
of comparators the second max traverses after `c` that the max does *not*.
Crucially **`r(c)` depends only on `c`**: after `c` the max is on `c`'s high
output and the second max on `c`'s low output, a state independent of `x, y`.
Also `δ(x) = e(x,c) + g(c)`, `g(c)` = comparators from `c` to `o_N` inclusive.

This decomposition is exact and is where van Voorhis's eq (5) went wrong: he
wrote `|W| = nc(c) + nc(q_c)`, which double-counts the `ov(c)` comparators the
two values share **after** `c`, i.e. `r(c) = nc(q_c) - ov(c)`.

---

## 2. The repair, part 1: a complete proof for clean sorters

### 2.1 Red and blue leads

> **Definition.** A lead is **red** if some one-hot max scenario puts the maximum
> on it, and **blue** otherwise.

**(R1) Every low output lead is blue.** *Proof.* The maximum is strictly greater
than the other input of any comparator it enters, so it leaves on the high
output. It therefore never occupies a low output lead. ∎

**(R2) A high output lead is red iff the comparator has at least one red input
lead.** *Proof.* (⇐) If an input is red, in that scenario the max enters and
exits high. (⇒) If the high output is red, the max is on it, and it got there by
traversing the comparator, so an input was red. ∎ *(All `N` input leads of the
network are red.)*

**(R3) A comparator is a branch node iff both its input leads are red.** A
comparator traversed by a max path with only **one** red input is precisely a
**pass-through**. *Proof.* An input lead is red exactly when some max-path
arrives on it. ∎

All three are machine-checked with zero violations (check **G1**).

> **Definition.** `T` is **clean** if it has no pass-throughs, i.e. every
> traversed comparator is a branch node, i.e. `|MAX(T)| = N-1` — precisely the
> claim the chapter makes for *all* sorters (p. 121) and which is false in
> general (`docs/van-voorhis-theory-report.md` §3.2).

### 2.2 Blue trapping

> **Lemma 1.** Let `T` be clean. In the scenario `(x,y)` with first meeting at
> `c`, the second max occupies only **blue** leads after `c`.

*Proof.* Immediately after `c` it is on `c`'s low output, blue by (R1). Suppose
it is on a blue lead `ℓ` and enters comparator `d` on `ℓ`. Since `ℓ` is blue, `d`
does not have two red inputs, so by (R3) `d` is not a branch node; since `T` is
clean, `d` is not traversed by any max-path. Then `d` cannot have a red input at
all — a red input would make `d`'s high output red by (R2), i.e. traversed.
So both of `d`'s outputs are blue by (R1) and (R2), and the second max leaves on
a blue lead either way. ∎ *(Check **G2**: 0 violations.)*

> **Corollary 2 (no re-meeting).** In a clean `T` the two values never meet
> again after `c`; hence `ov(c) = 0`, `r(c) = nc(q_c)`, and **eq (5) is exact**.

*Proof.* A meeting at `d` puts the max at `d`, so `d` is traversed, so (clean)
`d` is a branch node, so both inputs are red — contradicting Lemma 1. ∎

> **Corollary 3.** In a clean `T`, after `c` the second max occupies only **high
> output** leads (it never meets anything larger), and `nc(c) = a(c)` (no
> pass-throughs, so literal counts equal branch-tree depths).

### 2.3 The tree, the antichain, and Kraft

> **Lemma 4.** In a clean `T`, define `succ(ℓ)` = the high output lead of the
> next comparator touching `ℓ`. By Lemma 1 and Corollary 3 the second max's
> motion after `c` is exactly `succ`, **independently of the scenario**. The
> leads reachable from the `ℓ_c` therefore form an in-tree rooted at `o_{N-1}` in
> which every node has at most two predecessors (the two input leads of the
> comparator producing it) — a binary tree.

> **Lemma 5 (the antichain — the step the chapter omits).** In a clean `T` the
> `N-1` sources `ℓ_c` (the low output leads of the branch nodes) are pairwise
> non-ancestral in that tree.

*Proof.* After leaving `ℓ_j` the second max moves only onto **high** output leads
(Corollary 3). Every `ℓ_k` is a **low** output lead. So no `ℓ_k` can lie on the
path from `ℓ_j`. ∎

> **THEOREM 6 (eq (8) for clean sorters).** For every clean `N`-sorter `T`,
> ```
> p(2,T) >= ceil( log2 f(B) )     and hence     |T| >= S(N-2) + ceil(log2 f(B)).
> ```

*Proof.* By Lemmas 4 and 5 the `ℓ_c` form an antichain of `N-1` nodes at depths
`nc(q_c)` in a binary in-tree, so **Kraft** gives `sum_c 2^{-nc(q_c)} <= 1`.
By Corollaries 2 and 3, for the canonical pair `(x_c, y_c)` (deepest leaf of each
side) `a(c) + nc(q_c) = |W(x_c,y_c)| <= p(2,T)`. Hence

```
1 >= sum_c 2^{-nc(q_c)} >= sum_c 2^{-(p(2,T) - a(c))} = 2^{-p(2,T)} f(B).  ∎
```

Note what changed relative to the chapter: **(6) is an inequality, not an
equality** — that is why Batcher's own 8-sorter gives `0.75`, not `1`
(check **E8**) — and the antichain is *proved*, not assumed.

---

## 3. The repair, part 2: exactly what is still missing

### 3.1 Where cleanliness is used, and how pass-throughs break it

Lemma 1's induction fails at a **pass-through** `d`: `d` has exactly one red
input, so by (R2) its high output is red. A blue-carried second max entering `d`
beats the ordinary value on the red input (the max being elsewhere) and exits
**high onto a red lead**. From there it may re-meet the max (`ov(c) > 0`,
breaking eq (5)) and may traverse another branch node's low output (breaking
Lemma 5, hence Kraft — the sum can reach `1.25`, check **E4**).

> **Pass-throughs are the sole obstruction.** This is now a checked statement,
> not an impression: over 900 constructed sorters, the second max leaves the blue
> leads in **~84 %** of general sorters and in **0 %** of clean ones, and eq (6)
> fails in **~35 %** of general sorters and **0 %** of clean ones.

### 3.2 LEMMA★ — a candidate repair, and its refutation

For a branch node `c` put `W*(c) := max{ |W(x,y)| : LCA_B(x,y) = c }`.

> **LEMMA★ (slack-Kraft).**  For every `N`-sorter `T`,
> ```
> sum over branch nodes c of  2^{ a(c) - W*(c) }   <=   1.
> ```

**LEMMA★ ⟹ eq (8).** Since `W*(c) <= p(2,T)`,

```
f(B) = sum_c 2^{a(c)} = sum_c 2^{W*(c)} · 2^{a(c)-W*(c)}
     <= 2^{p(2,T)} · sum_c 2^{a(c)-W*(c)} <= 2^{p(2,T)}.  ∎
```

**LEMMA★ holds for clean sorters** — it is Theorem 6's proof, since
`W*(c) >= |W(x_c,y_c)| = a(c) + nc(q_c)`.

> **LEMMA★ IS FALSE IN GENERAL (check G5).** The 6-sorter
> ```
> T3 = [(2,3),(1,2),(0,4),(3,5),(2,4),(1,2),(4,5),(2,3),
>       (0,3),(3,4),(1,3),(1,2),(0,3),(0,1),(1,2)]
> ```
> (15 comparators; `S(6) = 12`; one pass-through) has branch-node exponents
> `a = {3,3,3,3,5}` and, **taking the maximum over all admissible pairs at each
> branch node**, `W* = {6,5,6,8,6}`. The slack-Kraft sum is
> `1/8 + 1/4 + 1/8 + 1/32 + 1/2 = 33/32 > 1`.
>
> *Provenance and independence.* `T3` was produced by
> `tools/verify_kraft_dispute.py`, an **independent adversarial re-derivation of
> the disputed steps written from scratch against the chapter text**, which does
> not import any of my code. That verifier independently reaches the same verdict
> on eqs (5), (6), (8) as `docs/van-voorhis-theory-report.md` §3 — a genuine
> corroboration — and it refutes the union-based repair. I re-verified `T3` inside
> `tools/verify_huffman2.py` from scratch (checks **G5**, **G6**).

**This refutes my own proposed reduction, and I withdraw it.** Note carefully
what does and does not follow:

- **eq (8) is NOT refuted.** On `T3`, `f(B) = 64` and `p(2,T3) = 8`, so
  `ceil(log2 64) = 6 <= 8` comfortably (check **G6**). LEMMA★ was *sufficient*
  for eq (8), never necessary: it compares each `a(c)` against that node's *own*
  best pair `W*(c)`, which can be far below the global maximum `p(2,T)`.
- **My sampling was not evidence.** 900 random constructed sorters gave 0
  violations and a supremum of exactly 1 (check **G6b**, retained as a caution).
  An adversarial search found a counterexample immediately. Recorded so that the
  same mistake is not repeated with the next candidate lemma.
- **What is now closed off:** every repair of the form "charge each branch node
  `c` against a pruning that meets at `c`" — because the strongest member of that
  family (best-choice `W*`) is false. A valid proof of eq (8) must be **global**:
  it must use the fact that the branch nodes cannot *all* have small slack
  simultaneously, not a term-by-term bound.

### 3.3 The pairing is load-bearing too

Replace `W*(c)` by `|W(x_c,y_c)|` for van Voorhis's *own* deepest-leaf pairing.
The resulting statement is **FALSE**: check **G7** exhibits a constructed
7-channel sorter (19 comparators) with slack-Kraft sum `1.078125 > 1` under the
deepest-leaf pairing, while its best-choice sum is `0.671875`. So a repair *must*
take the maximum over admissible pairs at each branch node; the chapter's habit
of fixing "the longest path through `L(c_j)`" is not merely a convenience.

### 3.4 What the formalization target actually is now

With LEMMA★ dead, the honest statement of the remaining gap is the bare theorem:

> **OPEN.** For every `N`-sorter `T` with MAX branch tree `B`,
> `p(2,T) >= ceil(log2 f(B))`.
> Known: true for **clean** `T` (Theorem 6); true in ~6 500 constructed sorters;
> consistent with all exact `S(3..12)`; and exhaustively true for `n = 3, 4` over
> all sorters up to the size caps checked by `tools/verify_kraft_dispute.py`.

Two things are now known about *how* it must be proved, and both are negative
results worth their cost:

1. It cannot be proved by per-node charging (§3.2).
2. It cannot be proved by the "fix one channel `x` and use Kraft on `MAX(T/x)`"
   route, nor by pair counting (§3.5) — those are short by a factor `2^{depth(c)}`.

The clean case (§2) is nonetheless a genuine, self-contained, formalization-ready
theorem: Facts 1–2, (R1)–(R3), Lemmas 1–5 and Theorem 6 involve no arithmetic
beyond Kraft and would transcribe to Isabelle/Lean directly. **That is what I
recommend formalizing first** — it is real, it is correct, and it fixes the
vocabulary (red/blue leads, branch tree, pass-through) that any general proof
will need.

### 3.5 What is *not* claimed

I do not have a proof of LEMMA★ in general, and I did not find one. The routes I
tried and why they fail, so nobody repeats them:

| route | outcome |
|---|---|
| Kraft on `MAX(T/x)` for a fixed `x` | sound and unconditional, but it only "sees" the `lp(B)` ancestors of `x`, not all `N-1` branch nodes. Yields `p(2,T) >= lp(B) + ceil(log2(N-1))` = **43** at `n=13`, not 44. |
| summing that over all `x` (pair counting) | gives the clean `sum_{(x,y)} 2^{-|W(x,y)|} <= 1`, but the per-node consequence is short by a factor `2^{depth(c)}`: it yields `N(N-1) = 156` at `n=13` where `f = 392` is needed. |
| dropping non-antichain sources from van Voorhis's sum | the surviving mass collapses (`2^{a-ov}` on a strict subset); on the 3-sorter counterexample it gives `p >= 1`. |
| eliminating pass-throughs by rewriting `T` | impossible in general: the optimal 3-sorter `[(0,1),(0,2),(1,2)]` has one, and no comparator is redundant. |

---

## 4. `P(2,11) = 9`: the exact reduction

The chapter beats its own `F`-bound exactly once (p. 127), and gives no proof
(*"It turns out that…"*). Machine-checked reduction (check **H1**):

- `F(11) = 256 = 2^8` **exactly**, so eq (12) yields only `P(2,11) >= 8`
  (check **A4**).
- `256` is attained by **exactly one abstract shape** (8 plane shapes):
  ```
  (((* *) (* *)) ((* (* *)) ((* *) (* *))))
  root split 4|7,  height 4,  leaf depths 3,3,3,3,3,4,4,4,4,4,4
  ```
- The **next attainable value is 272**, and `ceil(log2 272) = 9`.

> **Therefore `P(2,11) >= 9` is equivalent to a statement about a single shape:**
> *every 11-sorter whose MAX branch tree is `S*(11)` admits a pruning of two
> input leads removing ≥ 9 comparators* (on the MAX side or, as van Voorhis
> says, the MIN side).

The statement is **not vacuous**: `S*(11)` is realizable, by an explicit clean
construction (§7, check **G8**). And it is **consistent**: `9 <= S(11) - S(9) = 10`
(check **A8**).

This is the whole of the missing argument, and it is now a concrete finite-ish
target rather than a sentence in a paper. Reconstructing it is self-validating
(the answer is known) and would supply the only known technique for beating
`ceil(log2 F(N))` — which is exactly what `S(13) >= 45` needs.

---

## 5. The MAX/MIN incompatibility route is refuted in its shape-only form

`docs/van-voorhis-theory-report.md` §4.2 proposed, as the highest-value theory
item: *"show that for a 13-sorter, `f(MAX(C)) <= 512` forces `f(MIN(C)) >= 513`."*
**As stated — a claim about shapes, quantified over all 13-sorters — it is
false.**

- **Check H2.** Batcher's `n`-sorter has `f(MAX) = f(MIN) = F(n)` for
  `n = 3, 4, 6, 7, 8, 12`. In particular Batcher's 8-sorter (the chapter's own
  worked example, Figs. 3–5) has **both** trees minimising, at `96 = F(8)`; and
  Batcher's 12-sorter has both at `288 = F(12)`. There is no obstruction in
  principle to a network's MAX and MIN trees both being extremal.
- **Check H3.** At `n = 13` directly: the clean realization of shape `S6`
  (`f(MAX) = 512`) has `f(MIN) = 392` — **both admissible**.

**What survives.** The refutation uses networks of size 54 (and Batcher's 19, 42),
not 44. So the *size-conditioned* statement

> *no 13-sorter with 44 comparators has both `f(MAX) <= 512` and `f(MIN) <= 512`*

remains open — but it **cannot be proved by reasoning about shapes alone**, since
the shape combination is realizable. Any such argument must consume the
comparator budget. That is a materially different, and harder, target than the
one I ranked #3, and the ranking should change accordingly (§6).

**What is still free and correct.** The MIN *dual bound* itself
(`docs/van-voorhis-theory-report.md` §4.1) is unaffected: a 44-comparator
13-sorter must have both trees admissible, so all case-split filters apply twice
(check **C1**, **F3**: 0 violations). That remains a genuine 2× structural
constraint for the campaign.

---

## 6. Correction to `docs/van-voorhis-theory-report.md`

That report's §6.4 queue is amended as follows (the report itself is left intact,
per protocol):

| # | item | change |
|---|---|---|
| 1 | repair eq (5)/(6) | **partially done.** Proved for clean sorters (§2); pass-throughs shown to be the sole obstruction. My candidate reduction (LEMMA★) is **refuted** (§3.2), and with it every per-node charging repair. A general proof must be global. Still **blocking** for any claim resting on the 44. |
| 2 | reconstruct `P(2,11) = 9` | **sharpened**, not changed: reduced to one explicit shape `S*(11)` (§4). Still recommended, still self-validating. |
| 3 | MAX/MIN incompatibility at `n = 13` | **DEMOTED — refuted in its shape-only form** (§5). Only the size-conditioned version survives, and it needs a fundamentally different (budget-consuming) argument. Do not spend theory time on the shape version. |
| 4 | one residual bound `b_j >= 36` for shape `S6` | **unchanged, and now the best-ranked search-adjacent target** (still `+1` on `512`, a 0.20 % tightening). |
| 5 | close the ILL items | unchanged (done). |
| 6 | Huffman2 partial-network DP | unchanged; gated on #1, which is now much closer. |
| **7** | **NEW: all admissible shapes are realizable** (§7) | consequence: no class of the 3-class split is structurally empty. Removes a possible cheap win, and confirms the split is not vacuous. |

---

## 7. Realizability (new)

> **Proposition.** Every binary tree shape `S` with `n` leaves is the MAX branch
> tree of some **clean** `n`-sorter.

*Construction.* Assign the leaves of `S` to channels `0..n-1` left to right. Run
the tournament described by `S`, each comparator being `(min(w_a,w_b),
max(w_a,w_b))` on the two subtree-winner channels, so the winner always moves to
the higher channel and the overall winner lands on channel `n-1`. Then apply any
`(n-1)`-sorter to channels `0..n-2`.

*Proof.* Each tournament comparator's two inputs are subtree-winner leads, and
each is red (put the global max at a leaf of that subtree), so by (R3) every
tournament comparator is a branch node and there are no pass-throughs. The
max-path from leaf `i` is exactly its ancestor chain in `S`. The appended sorter
never touches channel `n-1`, so no max-path is extended. The network sorts:
after the tournament channel `n-1` holds the maximum and the rest are sorted
among themselves. ∎

Machine-verified (check **G8**) for the unique `n = 11` minimiser and for **all
6** admissible `n = 13` shapes: each realization sorts, its MAX branch tree
canonicalises to the target, and it is clean.

**Consequences.**
1. Classes **C1, C2, C3 are all non-empty at the shape level** — the 3-class
   split is not vacuous, and no class can be eliminated by unrealizability.
2. `P(2,11) = 9` cannot be established by showing `S*(11)` is unrealizable.
3. Theorem 6 applies to all of these realizations, so they are legitimate test
   objects for any future MIN-side argument.

---

## 8. Honest status

| claim | status |
|---|---|
| (R1)–(R3), the red/blue lead structure | **proved** (§2.1) and machine-checked (G1) |
| Fact 1, Fact 2 (the exact decomposition) | **proved** (§1), machine-checked (B4, B5) |
| eq (8) for **clean** `N`-sorters (Theorem 6) | **proved** (§2.3), machine-checked (G2, G3) |
| eq (8) in general | **NOT proved, NOT refuted.** 0 counterexamples in ~6 500 constructed sorters, plus exhaustive `n = 3,4`. |
| **LEMMA★** (my proposed reduction) | **REFUTED** by an explicit 6-sorter (G5). Withdrawn. |
| LEMMA★ with van Voorhis's deepest-leaf pairing | **REFUTED** (explicit 7-channel sorter, G7) |
| any per-node charging repair | **closed off** — the strongest member of the family is false |
| `S(13) >= 44` | still **conjecture**; proved floor remains **43** |
| Huffman2 | still proved **modulo** eq (5)+(6); LEMMA★ would make it sound |
| `P(2,11) >= 9` reduces to one shape | **proved** (§4), machine-checked (H1) |
| shape-only MAX/MIN incompatibility | **REFUTED** (§5, H2/H3) |
| every admissible shape is realizable, cleanly | **proved** (§7), machine-checked (G8) |

No search was run, no candidate network was produced, and no comparator count was
used as a target. The 44 appears only as the published bound under audit.

---

## 9. Reproduction

```
python3 tools/verify_huffman2.py           # 48 checks, exit 0
python3 tools/verify_huffman2.py --fast    # smaller samples
python3 tools/verify_huffman2.py --quiet   # verdicts only
```

Deterministic, stdlib only, read-only, fixed seeds. Every network is
**constructed** — Batcher, bubble, odd-even transposition, insertion-extension,
the tournament construction of §7, and random comparator prefixes in front of a
bubble network followed by randomised redundant-comparator removal. The only
comparator lists that appear literally are counterexamples the script re-derives
and re-verifies from scratch; no known witness network is embedded.
