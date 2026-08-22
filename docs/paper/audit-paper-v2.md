# The tabulated lower bound S(13) ≥ 44 rests on an invalid proof: an audit of van Voorhis (1972), a partial repair, and the cost of the alternative

**INTERNAL DRAFT — v2.0, 2026-08-22.** Supersedes `audit-paper-draft.md` (v0.1).
Not for circulation. Style brief: `STYLE.md`. Artifact plan: `ARTIFACT.md`.

---

The minimum size `S(13)` of a 13-channel sorting network is unknown. Since April
2025 the most widely consulted table of sorting-network bounds has listed
`S(13) ≥ 44`, obtained as `S(11) + P(2,13) = 35 + 9`, the second summand coming
from a two-value pruning theorem published by David Van Voorhis in 1972. We
audit that proof. Two of its structural steps, equations (5) and (6), are false:
we exhibit a size-optimal three-comparator network on which (5) overstates the
quantity it claims to compute and (6)'s Kraft sum equals 5/4, and equation (7),
the only route from them to the result, rests on them alone. The fault is one
premise — that the MAX subnetwork of an `N`-sorter consists of `N−1` comparators
— which ignores *pass-through* comparators, present in 61 % of an audited
population. We then prove the theorem for two classes, *escape-free* networks
and networks satisfying two isolated hypotheses, and prove a complementary bound
at the pass-through-rich end; together these cover 22.4 % of a 153,011-network
census, 49.6 % of which has no proof by any route in this work, and the
uncovered case is intermediate in pass-through count. Per-node charging repairs
are closed structurally. For the computational alternative we prove a collapse
theorem — the explored set of the deciding search at a given *level* is
independent of the channel count above a threshold — and use it to show that our
independently certified computation of `S(11) = 35` *is*, exactly, the level-6
computation at `n = 13`, while the next level exists at no smaller channel count
and is 2.4–195 TB beyond reach. `S(13) ≥ 44` has never appeared in a
peer-reviewed publication; the best published bound is 43, and nothing here
disturbs it.

---

## 1. Introduction

### 1.1 The quantity, and the two bounds in circulation

A *comparator* `(a,b)` with `a < b` on `n` channels replaces the values on
channels `a` and `b` by their minimum on `a` and maximum on `b`. An *`n`-sorter*
is a comparator sequence that sorts every input; `S(n)` is the least size of one.
`S(n)` is known exactly only for `n ≤ 12`:

| n | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 |
|---|---|---|---|---|---|---|---|---|---|----|----|----|----|
| S(n) | 0 | 1 | 3 | 5 | 9 | 12 | 16 | 19 | 25 | 29 | 35 | 39 | **?** |

Values through `n = 8` are due to Floyd and Knuth [FK73], `S(9)` and `S(10)` to
Codish, Cruz-Filipe, Frank and Schneider-Kamp [CCFS16], `S(11)` and `S(12)` to
Harder [Ha20]. At `n = 13` the best construction remains Juillé's 45-comparator
network of 1995 [Ju95]. Two lower bounds are in circulation.

**The one-value bound**, `S(n) ≥ S(n−1) + ⌈log₂ n⌉`, gives `S(13) ≥ 43`. It is
Van Voorhis's *IEEE Transactions* note [VV72a], Knuth's exercise 5.3.4–42 with a
three-line answer [Kn73], and Harder's Lemma 17, proved there in full. **This is
the best published lower bound and nothing here disturbs it** (§4.3).

**The two-value bound**, `S(N) ≥ S(N−2) + P(2,N)` with `P(2,N) ≥ ⌈log₂ F(N)⌉`
for an explicitly computable `F`, is the content of the Plenum chapter [VV72].
With `F(13) = 392` and the modern `S(11) = 35` it gives 44. The chapter's own
Table 1 printed `L(13) = 42`, since in 1972 the best available `S(11)` was 33;
the 44 is a modern recombination. It appears to have entered the record on
2025-04-21 through a changelog entry in Dobbelaere's table [Do25] — *"Tighter
lower bounds for size, on suggestion of Jelmer Firet and based on principles in
[VVoorh72]"* — and we could locate no publication behind it (§4).

### 1.2 Contributions

Items 1–3 are unconditional mathematics; 4 is a computational credential; 5 is
an open status.

1. **The chapter's proof of `P(2,N) ≥ ⌈log₂ F(N)⌉` is invalid as written** (§3).
   Equations (5) and (6) are false in the direction that destroys the
   derivation, and (7) rests on them alone. The failure is common — 61.0 % of an
   audited population has the enabling structure — and is not confined to
   networks with slack: 27.1 % of that population, and 37.1 % of a larger pooled
   corpus, is simultaneously tight and Kraft-broken. The strongest available
   defence is refuted.
2. **Two partial repairs, unconditional** (§5). Equation (8) holds for every
   *escape-free* `N`-sorter (Theorem 6), a class strictly wider than the
   pass-through-free one, and under two isolated hypotheses (Theorem 7); a
   complementary bound holds at the pass-through-rich end (Proposition 8).
   **These cover 22.4 % of a 153,011-network census; 49.6 % of it has no proof
   by any route in this work**, and the uncovered zone is intermediate in
   pass-through count. Per-node charging is closed structurally (Proposition 9).
3. **A collapse theorem for the deciding computation** (§6). With
   `C(n) = 3 + Σ_{k=4}^{n} ⌈log₂ k⌉` the bound the search gets for free and
   `D(n) = S(n) − C(n)`, a level-`ℓ` search satisfies
   `Reach(n,ℓ) = Reach(n_min(ℓ),ℓ) ⊎ {cube_w : n_min(ℓ) < w ≤ n}` for all
   `n ≥ n_min(ℓ) = min{n : D(n) ≥ ℓ}` (Theorem 12), on machine-checked
   foundations (Lemmas 10, 11).
4. **An independently certified `S(11) = 35`** (§7), from our own rebuilt engine,
   accepted by an unmodified extraction of Harder's verified checker, with the
   memory/time trade reported on all three axes.
5. **The status of `S(13)`, priced** (§8). Our `n = 11` computation *is* the
   `n = 13` level-6 computation; the next level exists at no channel count below
   13 and is 2.4–195 TB away. We claim nothing about the truth of `S(13) ≥ 44`,
   only that it is not currently supported by a correct argument, while
   `S(13) ≥ 43` is.

### 1.3 Artifact and roadmap

Six standard-library Python programs accompany this paper, deterministic,
read-only and dependency-free, running in about nine minutes in total. The two
carrying the audit were written independently: one alongside the first reading
of the chapter, the other afterwards from the page images by an author whose
brief was to defend the chapter. Every numerical claim names the script that
recomputes it; check-level indexes, known script defects and reference output
are in the artifact repository [Art], and the certificate of §7 is deposited at
[Cert].

§2 fixes vocabulary, §3 is the audit and §4 the literature record, §5 the
repair, §6 the collapse theorem, §7 the certified computation, §8 the status of
`S(13)`; §9 states what we trust and §10 what we do not.

---

## 2. Preliminaries

We match the verifier code, because several distinctions below are what the 1972
argument elides. A *lead* is a wire segment: a channel's input segment or a
comparator's output segment.

> **Definition 1 (max-paths, branch tree, pass-throughs).** Give input channel
> `k` a value strictly greater than all others. It leaves every comparator it
> enters on the high output, tracing a unique *max-path* `p_k` to `o_N`; put
> `MAX(T) = ⋃_k p_k`. A comparator is a *branch node* if max-paths reach it on
> **both** input leads, and a *pass-through* if it lies in `MAX(T)` but is not a
> branch node. The branch nodes form the *branch tree* `B`: `n` leaves, `n−1`
> internal nodes, rooted at the last branch node before `o_N`. `T` is **clean**
> if it has no pass-through.

For a branch node `c` with branch-tree subtrees of heights `lp(L(c))`, `lp(R(c))`
and depth `depth_B(c)`, put

```
a(c) := lp(L(c)) + lp(R(c)) + depth_B(c) + 1,        f(B) := Σ_c 2^{a(c)}.
```

`f` satisfies the chapter's Theorem 1 recursion, and `F(N) = min_B f(B)`
reproduces its Table 1 exactly for `N ≤ 16` under two independent
implementations (`verify_huffman2.py`, `verify_kraft_dispute.py`). For channels `x ≠ y`, run the scenario *max at `x`, second max
at `y`* and let `W(x,y)` be the comparators either value touches; removing them
leaves an `(N−2)`-sorter, so with `p(2,T) := max_{x,y}|W(x,y)|` we have
`|T| ≥ S(N−2) + p(2,T)`. Write `W*(c) = max{|W(x,y)| : LCA_B(x,y) = c}`.

> **Definition 2 (escapes; the hypotheses (C) and (D)).** In scenario `(x,y)` the
> two values first meet at `c = LCA_B(x,y)`. Call a lead *red* if some one-hot
> scenario puts the maximum on it. `T` is **escape-free** if for every admissible
> pair the second maximum occupies no red lead at or after `c`'s low output;
> equivalently, it never re-meets the maximum at a branch node. Writing `nq(c)`
> for the comparators the second maximum traverses strictly after `c`, `ov(c)`
> for those the maximum also traverses, and `γ(c)` for the pass-throughs on the
> maximum's stem from `c` to `o_N`:
>
> **(C)** `Σ_c 2^{−nq(c)} ≤ 1`  ·  **(D)** `γ(c) ≥ ov(c)` for every branch node.

Every clean network is escape-free and the converse fails; the gap is not
cosmetic, since Batcher's 12-sorter has a pass-through and is escape-free.

---

## 3. The audit

### 3.1 The chain, isolated

The section of [VV72] bounding `P(2,N)` opens with the premise

> "The MAX subnetwork of `T`, `MAX(T)`, includes `N−1` comparators, which we
> label `c_1, c_2, …, c_{N−1}`." — p. 121

attributed to [VV72a]. For a branch node `c_j`, `nc(c_j)` counts the comparators
from the two deepest leaves of its subtrees to `c_j` and on to `o_N`; `q_j` is
the second maximum's onward path to `o_{N−1}`. Then

> "… the two paths … together include `nc(C_j) + nc(q_j)` comparators.
> Therefore, `p(2,T) = max_j [nc(C_j) + nc(q_j)]`." — p. 122, eq. (5)
>
> "MAX2(T) is a binary tree, so the path lengths `nc(q_j)` satisfy
> `Σ_j 2^{−nc(q_j)} = 1`." — p. 124, eq. (6)

and from these alone follows (7) `Σ_j 2^{−[p(2,T)−nc(C_j)]} ≤ 1`, hence (8)
`p(2,T) ≥ ⌈log₂ f(MAX(T))⌉`, hence `P(2,N) ≥ ⌈log₂ F(N)⌉` and `S(13) ≥ 35 + 9`.
Step (7) needs only the *inequalities*; the failures below are in the fatal
direction anyway.

### 3.2 The counterexample

> **Proposition 3.** Let `T1 = [(0,1),(0,2),(1,2)]`, the Batcher 3-sorter, with
> `|T1| = 3 = S(3)`. Then `|MAX(T1)| = 3`, not `N−1 = 2`; equation (5) returns 4
> for a quantity whose value is 3; equation (6)'s sum is `5/4`; and under the
> literal reading of eq. (9), equation (8) itself is false on `T1`.

*Proof.* `MAX(T1) = {c_0,c_1,c_2}`, and `c_1 = (0,2)` is a pass-through: the
maximum enters and leaves it on channel 2, and no other max-path arrives on
channel 0 there. The branch nodes are `{c_0,c_2}` — two, as claimed. What fails
is their identification with the comparators of `MAX(T)`.

Take `c_0` with the pair (ch 0, ch 1). The max path is `c_0,c_2`, the second-max
path `c_0,c_1,c_2`, and `nc(c_0) = nc(q_0) = 2`, so (5) asserts the two paths
together include 4 comparators. Their union is `{c_0,c_1,c_2}`: **three** —
after separating at `c_0` the values **meet again** at `c_2`. Since `|T1| = 3`,
`p(2,T1) = 3`, confirmed by brute force. So (5) *exceeds* `p(2,T)`, exactly the
direction that invalidates (7). The MAX2 "leaves" are the low output leads of
`c_0` and `c_2`, at depths 2 and 0 — the low output of `c_2` **is** `o_{N−1}` —
giving `Σ_j 2^{−nc(q_j)} = 5/4`; the cause is structural, since `q_0` passes
through `c_2`'s low output lead, so the claimed leaves are not an antichain.
Finally, with `nc` read literally as defined on p. 122, `f = 2² + 2³ = 12` and
(8) asserts `p(2,T1) ≥ 4 > 3`; with `f` computed by the chapter's Theorem 1 on
the branch tree, `f = 8` and (8) holds with equality. ∎

Both verifiers recompute this independently, and it is checkable by hand. The
*tree* reading of `nc` is forced by Fig. 5, whose printed values are exactly the
branch-tree quantities, and is the reading under which the chapter's conclusion
is empirically unrefuted; it rescues neither (5) nor (6). The exact statement is
`|W(x,y)| = nc(c) + nc(q_c) − ov(c)`, and eq. (5) claims `ov(c) = 0`.

### 3.3 The failure is common, and not confined to slack

Over 387 constructed sorters (bubble, insertion, odd-even transposition and
Batcher, `n = 3..10`; thinned random prefixes; relabellings), each verified a
sorter by the 0/1 principle (`verify_kraft_dispute.py`, seed `20260818`):

| statement | count | share |
|---|---|---|
| `MAX(T)` has a pass-through | 236 | 61.0 % |
| eq. (5) RHS strictly exceeds `p(2,T)` (fatal) | 172 | 44.4 % |
| eq. (6) sum `> 1` (fatal) | 164 | 42.4 % |
| eq. (8) fails, literal `nc` | 102 | 26.4 % |
| eq. (8) fails, **tree** `nc` | **0** | 0.0 % |
| conclusion `p(2,T) ≥ ⌈log₂ F(n)⌉` fails | **0** | 0.0 % |
| **tight conclusion *and* eq. (6) broken** | **105** | **27.1 %** |

The last row answers the natural dismissal, that this is a technicality biting
only where the bound has slack. Over the complete set of 149,040 optimal
5-sorters, eq. (8) is tight in 100 % and eq. (6) broken in 43.9 %, so **37.1 %**
is simultaneously tight and Kraft-broken (`verify_kraft_wave1.py`). Nor is the violation bounded:
adversarial search reaches Kraft sums of 1.6875 at `n = 6` and 1.8125 at
`n = 7`, so the suprema rise with `n`. These percentages are properties of the
generators and seeds, not rates (§10.3); the shipped scripts *assert* the
corresponding existence and universality statements and *print* the counts.

### 3.4 The strongest defence, and its refutation

Ten steelman defences were attempted under an adversarial brief and are in
[Art]. That the failure occurs only in slack-rich networks is false, by the
table above. The other that matters is the argument a sympathetic reader
reconstructs first, and, we believe, what the chapter had in mind:

> **`MAX(T)` and `MAX2(T)` are comparator-disjoint.** Every comparator of
> `MAX(T)` has both inputs on MAX-edges; `q_j` starts on `c_j`'s *lower* output,
> which is not a MAX-edge; induct.

Disjointness would make (5) an exact union and force every `q_j` onto high leads
throughout — hence prefix-free, hence Kraft — repairing (5) and (6) at one
stroke. It fails because its premise is precisely what pass-throughs violate. On
`T1` the two subnetworks share two comparators, one the root branch node; across
the sweep they meet in 60.2 % of networks and at a branch node in 59.9 %.
Disjointness **does** hold on Batcher's 8-sorter, which is why the chapter's own
example cannot expose it. With no pruning at all, every comparator sequence on 3
channels of length ≤ 4 that sorts (42) and every one on 4 channels of length ≤ 6
(912) satisfies the conclusion (`verify_kraft_dispute.py`); its enumerator prunes
nothing, inert comparators included.

### 3.5 A misstatement is not a gap

The chapter's only worked example is Batcher's odd-even 8-sorter. Its `MAX(T)`
has seven comparators, seven branch nodes and **no pass-through**; its `nc`
multiset `{3,3,3,3,4,4,5}` matches the printed values and `f = 96 = F(8)`
(`verify_huffman2.py`). But
its MAX2 depths give `Σ_j 2^{−nc(q_j)} = 0.75 ≠ 1`, so eq. (6) is not even an
equality in the chapter's own example. The two must be separated, since
conflating them would overstate the finding: 0.75 is *below* 1, step (7) needs
only `≤ 1`, and the derivation goes through there unharmed, whereas `T1` gives
1.25. This also suggests how the error survived — the single example in the
paper fails on the safe side, and its MAX subnetwork is clean, so it cannot
discriminate the literal and tree readings of `nc` either.

---

## 4. The record

### 4.1 No erratum, and no reader

We searched for any erratum, correction, gap-note, reproof or formalisation of
equations (5)–(9): OpenAlex and Google Scholar citation graphs, arXiv title and
full-text search, DBLP, GitHub code and issue search, Knuth's Vol. 3 and its
errata, the Stanford technical-report indexes, Dobbelaere's table with its
Wayback history, and Harder's Isabelle sources. **Nothing exists**, and the
reason is stronger than "nobody found the bug": nobody has engaged with the
argument. The chapter has **18 recorded citing works** as of 2026-08-22, two
since 2024, neither engaging; the modern ones cite it for the *one-value* bound.
A grep for `P(2,`, `MAX2`, `MAX subnetwork` and `Kraft` across some twenty-five
modern papers returns zero hits. Knuth carries no two-value exercise and never
cites the chapter. **There is no machine-checked version of the `P(2,N)` bound.**

### 4.2 The provenance of 44

| value | where it appears | basis |
|---|---|---|
| 43 | Wikipedia (still, as of 2026-08-15); Dobbelaere before 2025-04-21 | `S(12) + ⌈log₂ 13⌉` |
| **44** | Dobbelaere since 2025-04-21 only | `S(11) + P(2,13)` |

Dobbelaere's `n = 13` size row reads `44…45` and carries **no citation for the
lower bound**; the only reference on that row is for the depth result. We found
no publication, preprint or repository by the person credited in the changelog.

> **`S(13) ≥ 44` has never appeared in a peer-reviewed publication.** The best
> *published* lower bound is **43**. The 44 is a web-table entry sixteen months
> old, resting on a fifty-four-year-old argument nobody has re-derived,
> re-proved or machine-checked, whose two structural lemmas are false.

This *lowers* the stakes — no peer-reviewed result is overturned — and
correspondingly raises the value of recording the finding, since the number is
propagating with no correct argument behind it.

### 4.3 Why the one-value bound is unaffected

A reader who checks Harder's paper finds the same identification we attack. His
Lemma 17 reproduces the classical bound with a full proof, and in it:

> "if we take the union of the pruned paths for all `i` and remove the common
> output `n`, we obtain a binary tree rooted in the comparator gate connected to
> output `n`, where the leaves are all inputs of `c` and all inner vertices are
> comparator gates … the leaf for every input `i` has a depth of `δ(c,i)`."
> — [Ha20], proof of Lemma 17

Identifying max-path comparators with branch nodes is exactly the p. 121
premise, and by Proposition 3 it is false whenever pass-throughs exist: `δ(c,i)`
is a literal comparator count and can exceed the branch-tree depth. **It is
harmless there**, for a one-line reason — the one-value bound needs only
`max_i δ(c,i) ≥ max_i depth_B(i) ≥ ⌈log₂ n⌉`, and literal depth *dominates*
branch depth, so the inequality goes the safe way. `S(12) = 39` and the published
`S(13) ≥ 43` stand. We record this because it pre-empts the obvious question and
because it strengthens §3.5: the same imprecision was reproduced, unnoticed, in a
2020 paper that is the current authority for `S(11)` and `S(12)`. Two smaller
points. Harder's Lemma 17 is a paper proof — his Isabelle development verifies
the certificate checker, not Van Voorhis's bound — so `S(12) = 39` is not
machine-checked either; and the literature disagrees with itself about which Van
Voorhis paper proves the one-value bound, Harder citing the *Transactions* note
and Codish et al. the Plenum chapter, though it is derived in both.

---

## 5. The partial repair

The gap is the missing antichain step. We supply it for two classes, give a
complementary bound at the opposite extreme, and then say how much that leaves.

### 5.1 The exact correction of equation (5)

> **Lemma 4 (exact decomposition).** With `c = LCA_B(x,y)` and `e(z,c)` the
> comparators strictly between input `z` and `c` on `z`'s max-path,
> `|W(x,y)| = e(x,c) + e(y,c) + g(c) + r(c)`, where `g(c)` counts the
> comparators from `c` to `o_N` inclusive on the maximum's onward path and
> `r(c) = nq(c) − ov(c)` those the second maximum traverses after `c` that the
> maximum does not. In particular `r(c)` depends only on `c`.

This is the correction of eq. (5), which double-counts `ov(c)`. Aggregating over
the admissible pairs at a node gives the identity that replaces it.

> **Lemma 5 (the identity).** For every `N`-sorter and branch node `c`,
> `W*(c) = a(c) + ε(c) + γ(c) + r(c)`, where `ε(c) ≥ 0` measures how far the
> maximum's pre-meeting paths exceed the branch-tree heights. Hence
> `p(2,T) = max_c [a(c) + ε(c) + γ(c) + r(c)]`.

Verified with zero violations over 152,003 sorters and, independently, over
`verify_kraft_wave2.py`'s own 32,043-sorter corpus. One consequence deserves
separate statement: equation (8) is *equivalent* to
`Σ_c 2^{a(c)} ≤ 2^{max_c[a(c)+ε(c)+γ(c)+r(c)]}`, a statement about a binary tree
decorated with three non-negative integer functions — and it is **false** for
arbitrary decorations, since `ε = γ = r = 0` refutes it on any tree with two or
more internal nodes. **The entire content of equation (8) is therefore a
realizability constraint: which decorated trees arise from an actual sorter.**
That is the sharpest formulation this work has produced (§10.5).

### 5.2 The escape-free case

> **Theorem 6 (equation (8) for escape-free sorters).** For every escape-free
> `N`-sorter `T` with branch tree `B`,
> ```
> 1 ≥ Σ_c 2^{−nq(c)} ≥ Σ_c 2^{−(p(2,T) − a(c))} = 2^{−p(2,T)} f(B),
> ```
> hence `p(2,T) ≥ ⌈log₂ f(B)⌉` and `|T| ≥ S(N−2) + ⌈log₂ f(B)⌉`.

The proof is elementary and is in [Art], its lemmas checked by
`verify_kraft_wave1.py` and `verify_kraft_wave2.py`; the two steps the chapter
omits are these. In the red/blue colouring of Definition 2, every low output lead is blue,
a high output lead is red iff its comparator has a red input, and a comparator is
a branch node iff both its inputs are red, a pass-through iff exactly one is. In
an escape-free network the second maximum therefore traverses **no branch node**
after the meeting, so the `N−1` sources — the low output leads of the branch
nodes — are pairwise non-ancestral under its successor map. That is the
antichain, and Kraft's inequality applies; the per-node inequality
`nq(c) ≤ p(2,T) − a(c)` is Lemma 4 with the deepest-leaf pairing. Two things
change relative to the chapter, both essential: equation (6) becomes an
**inequality**, which is why Batcher's own 8-sorter gives 0.75 and the argument
is unharmed, and the antichain is **proved** rather than assumed. (An earlier
drafting justified the red case by "the low output of a comparator having a red
input, which is therefore not a branch node" — false as written, since a branch
node does have red inputs. The corrected argument turns on there being *exactly
one* red input.)

### 5.3 Isolating the hypotheses

Escape-freeness enters Theorem 6 only through (C) and (D). Isolating them widens
the class.

> **Theorem 7 (equation (8) under (C) and (D)).** If an `N`-sorter satisfies (C)
> and (D) then `p(2,T) ≥ ⌈log₂ f(B)⌉`.

The gain is small and we say so. On the same 32,043-sorter corpus (C)∧(D) holds on
7,214 networks against 7,167 escape-free ones — 47 sorters escape yet satisfy
both, a widening of 0.7 %; at `n = 5` it is 0.55 % and at `n = 4` the difference
is empty. Equation (8) holds on all 7,214, with zero failures. Theorem 7's value
is not its coverage but that it names the two things a general proof must supply.

### 5.4 The pass-through-rich end

> **Proposition 8.** For every `N`-sorter, `f(B) ≤ 2^{p(2,T)} · Σ_c 2^{−γ(c)}`.
> In particular equation (8) holds whenever `Σ_c 2^{−γ(c)} ≤ 1`, and whenever
> the root's stem carries at least one pass-through and every edge of `B`
> carries at least two.

**This must be quoted with its caveat.** Padding raises `p(2,T)` while leaving
`f(B)` fixed, so the sorters it reaches are exactly those with large slack — the
witnesses have `p(2,T) = 7` against a bound of 5. *For the size-optimal networks
that matter to the `S(13)` question it is of little use.* It is recorded because
it completes the picture from the opposite direction.

### 5.5 Coverage: where the open problem lives

This is the most useful new fact here, and the most uncomfortable. Over a census
of 153,011 networks:

| sufficient condition | fraction | kind |
|---|---|---|
| clean | 0.183 | structural |
| escape-free (Theorem 6) | 0.223 | structural |
| Proposition 8's hypothesis | 0.0035 | structural |
| **structural union** | **0.224** | |
| (C)∧(D) (Theorem 7) | 0.224 | computed |
| `Σ_c 2^{−γ(c)} ≤ 1` | 0.0056 | computed |
| `Σ_c 2^{−r(c)} ≤ 1` | 0.503 | computed |

*Structural* and *computed* conditions must not be blurred: a per-network
computation is not a theorem. Excluding one condition that holds on the whole
corpus but is known false in general (Proposition 9), **49.6 % of this corpus
has no proof of equation (8) by any route in this work.**

The uncovered zone is *intermediate* in pass-through count at every `n` tested:
the fraction with no covering condition rises from zero at zero pass-throughs to
0.99–1.00 at two or three, then falls back to zero at thirteen or more.
**Equation (8) is provable at the pass-through-poor end and again at the
pass-through-rich end, and the open problem lives strictly in between.** These
two figures come from a corpus no currently shipped verifier regenerates; the
coverage on the shipped 32,043-sorter corpus agrees (22.4 % escape-free, 22.5 %
for (C)∧(D)), but the census must be re-implemented before release, and [Art]
records this as a release blocker.

### 5.6 What is closed off

> **Proposition 9 (per-node charging is impossible).** On any `T` with
> `f(B) = 2^{p(2,T)}`, `Σ_c 2^{a(c)−p(2,T)} = 1` exactly. Hence for any per-node
> exponent `X(c) ≤ p(2,T)`, `Σ_c 2^{a(c)−X(c)} ≥ 1`, with equality iff
> `X(c) = p(2,T)` at every branch node — and tight sorters with non-constant
> `W*(c)` exist (an 18-comparator 7-sorter with `f = 2^{p(2,T)} = 128` and
> `W* = {6,7,7,7,7,7}`). **No certificate built from each node's own pruning can
> prove equation (8).**

This closes the family structurally, generalising an earlier refutation by
counterexample: the strongest member, charging each node against its own `W*(c)`,
is false — an adversarially found 15-comparator 6-sorter gives
`Σ_c 2^{a(c)−W*(c)} = 33/32` — though equation (8) itself is not refuted there.
Four further families are closed with explicit counterexamples in [Art]:
disjointness (§3.4), extremal surgery, direct information-theoretic counting, and
fractional Kraft via flow, which is ill-posed on leads because the pre-meeting
quantity `ε(c)` cannot be expressed as a capacity. One conjecture, proposed at
25–35 % confidence, we now assess at 15–25 %: *probably false at some larger `n`
and unlikely to be provable.* Without the Kraft step the argument yields only
`p(2,T) ≥ max_j nc(c_j)`, which for the `f`-minimising 13-leaf trees is 42.
**The Kraft step carries the entire 44, and the Kraft step is the broken one.**

One methodological rule this work had to learn: the landscape has a large plateau
at exactly 1.0, and single-seed hill-climbing found one refutation under a small
budget and missed it under a larger one. **Any claim that something "survived
adversarial search" must state seeds, steps and restarts.**

---

## 6. A collapse theorem for the deciding computation

The only known route to a bound of 44 other than the two-value theorem is
exhaustive search of the kind that settled `n = 9..12`: a dynamic program over
canonical output sets with a Huffman-style bound. This section concerns the
structure of that search; §8 its cost.

Write `C(n) = 3 + Σ_{k=4}^{n} ⌈log₂ k⌉` — the bound the search obtains before any
successor expansion, which is exactly the one-value chain — and
`D(n) = S(n) − C(n)`. A run with bound target `L` sits at **level**
`ℓ = L − C(n)`. Then `C(13) = 37`, `D(3..12) = 0,0,1,1,2,2,4,4,6,6`, and the
highest level a width-`n` search can reach is `D(n)`.

> **Lemma 10 (the free chain is the chain of cubes).** For every `k ≥ 4`, every
> polarity and every channel, pruning the full cube on `k` channels yields the
> full cube on `k−1` channels. The cube's prune set is thus the single state
> `cube_{k−1}`, and the Huffman rule at `cube_k` combines `k` identical children
> — which is exactly `C(k) = C(k−1) + ⌈log₂ k⌉`.

> **Lemma 11 (the cube has one successor).** `canon(cube_k ▷ [i,j])` is
> independent of `(i,j)`; the cube has a single successor `s_k`, of size
> `3·2^{k−2}`. *Proof.* The symmetric group acts transitively on unordered pairs
> and fixes `cube_k` setwise, so all `C(k,2)` images canonicalise together. ∎

Both are machine-checked by `verify_ambient.py`: Lemma 11 at `k = 6, 9, 11, 13`,
where all 15/36/55/78
comparators give one canonical key of size 48/384/1536/6144; Lemma 10 at
`w = 10..13`, byte-equal to the independently computed cube key.

> **Theorem 12 (Chain Collapse).** Let `n_min(ℓ) = min{n : D(n) ≥ ℓ}`. For every
> `n ≥ n_min(ℓ)`,
> ```
> Reach(n, ℓ) = Reach(n_min(ℓ), ℓ) ⊎ { cube_w : n_min(ℓ) < w ≤ n },
> ```
> so the width census is identical below `n_min(ℓ)` and exactly 1 above it. From
> `D(3..12)`, `n_min(1..7) = 5, 7, 9, 9, 11, 11, 13`.

*Proof sketch.* By Lemmas 10 and 11 the root `cube_n` has exactly two out-edges.
If `ℓ ≤ D(n−1)` the successor branch is never taken, so `cube_n` contributes
itself and delegates to `cube_{n−1}`; the recursion from `cube_{n−1}` is
bit-for-bit what a run rooted there would perform, the level being preserved
because the Huffman step contributes exactly `C(n) − C(n−1)`. Descend until
`ℓ > D(w−1)`, first at `w = n_min(ℓ)`. ∎

**Three scopings belong to the theorem, not to a later caveat.** `Reach` is the
set of states the *engine stores*, not the abstract reachable set, which is
larger. The delegation step rests on an *ambient-freedom* property of the
implementation — no quantity in the recursion depends on the channel count —
established by exhaustive reading of the three recursive procedures plus a second
reviewer's independent audit, **not by machine check**; and that property is
*false* under one non-default setting, since the on-line subsumption index
defaults to widths `{n−3, n−2}`, a different set at every ambient. The fix is one
line of policy, pinning those widths absolutely, and every measurement below is
in the default regime where the index is off. Finally `D(13)` is unknown, so
every statement here concerns `ℓ ≤ 6`.

Empirically the theorem is exact: across 21 pairs of ambients at levels 1–4 the
stored key sets agree **exactly** below the front — Jaccard 1.000000, zero
symmetric difference, zero bound disagreements — with intersection sizes rising
by exactly one per channel, the free-chain cube. At level 5 the `n = 13` census
is 1,444 states at width 11
plus exactly one each at widths 12 and 13, matching to the unit an independently
measured 1,446 states of width ≥ 11 from a separate campaign. Two runs at the
*same* ambient agree slightly less well than two runs at different ambients,
which retires four previously reported cross-ambient "spreads" as noise.

**Relation to prior work.** That a bound proved for a state is valid at any
ambient at least its width is *immediate* from Harder's definition of the
objective, a function of a sequence set with no ambient in it; we claim no
novelty there. New are the audit showing the implementation respects it, the one
place it does not, and Theorem 12, which does not follow from the definition.
Structurally Theorem 12 is a **cutoff theorem** — above a threshold size the
large instance is determined by the small one — a mature notion in parameterized
verification [EN95, EK07, KKW10]. None of that work concerns sorting networks and
none anticipates Theorem 12, but the shape will be familiar to that audience, and
this appears to be the first cutoff theorem for a combinatorial-optimality
search.

---

## 7. An independently certified `S(11) = 35`

> **Theorem 13.** `S(11) = 35`, re-derived from an independently rebuilt search
> engine and certified by an unmodified extraction of a formally verified
> checker.

*Proof.* We rebuilt Harder's pipeline from the pinned upstream commit with a
five-patch stack, none of it touching the checker, on a six-core AMD Ryzen 3600
with 47 GB of memory. Search completed in 71 h 06 m at a peak of 13.08 GB, inserting
95,221,143 states and returning 35; pruning all bounds took 9 h 45 m at about
8.4 GB, leaving 10.47 M survivors; certificate generation took about 9 h and
peaked above 37.9 GB — killed twice by the kernel at exactly that footprint
before a 96 GB swapfile was armed — producing 2,442,317,348 bytes, SHA-256
`672c433f…`. That certificate was checked on an Apple M4 in 89 m 24 s at a peak
of 4.35 GB by the frozen checker, which returned `Just (11,35)` and exited 0.
Since the checker's core is an unchanged extraction of an Isabelle/HOL-verified
program, `S(11) ≥ 35`, matching the known upper bound. ∎

Checking the deposited certificate [Cert] requires no part of our engine.

### 7.1 The memory/time trade, on all three axes

| stage | Harder [Ha20] | this work | memory | wall |
|---|---|---|---|---|
| search | 178 GiB (191 GB), 4 h 51 m | 13.08 GB, 71 h 06 m | **14.6× less** | **14.7× more** |
| prune-all | 16 GiB, 2 d 5 h | ~8.4 GB, 9 h 45 m | 2.1× less | 5.4× less |
| gen-proof | 54 GiB (58.0 GB), 19 h 02 m | > 37.9 GB, ~9 h | **1.5× less** | 2.1× less |
| verify | 6 GiB, 34 m | 4.35 GB, 89 m | 1.5× less | 2.6× more |
| certificate | 2926 MiB | 2329 MiB | 1.26× smaller | — |
| **total wall** | **77.5 h** | **91.3 h** | — | 1.18× more |

Four things must be said together. (i) The 14.6× is a **search-stage** result,
and it is 14.6× only when both figures are normalised: 178 GiB is 191 GB, and
dividing 178 by 13.08 as though the units matched gives a spurious 13.6×.
(ii) The reduction did **not** carry to the pipeline. Our peak moved to
certificate generation, where the improvement is about **1.5×**, and that stage
now binds; peak against peak the pipeline improved 191 GB → 37.9 GB, but 1.5× is
the operationally relevant figure. (iii) The search-stage memory was bought with
a **14.7× wall-time increase** at that stage. (iv) Hardware differs between the
columns and between our own stages, so no wall-time ratio here is a controlled
measurement. The honest summary is a memory/time trade at fixed correctness with
the binding constraint relocated rather than removed — and one operational
lesson that cost two OOM kills: **certificate generation, not search, is the
hidden peak, and must be budgeted separately.**

---

## 8. The status of `S(13)`, priced

### 8.1 What remains

Equation (8) is **neither proved nor refuted**. It is an open conjecture with
substantial empirical support: zero violations across the 1,890 constructed
sorters of `verify_huffman2.py` and `verify_kraft_dispute.py`, two exhaustive small-`n` enumerations, roughly 15,000
adversarially searched networks aimed directly at it, and consistency with every
exact `S(n)` known — the slacks `S(N) − S(N−2) − ⌈log₂ F(N)⌉` for `N = 3..12`
are `0,0,0,1,0,0,1,2,2,1`, and a single negative entry would have refuted it.
§5.6 is a cautionary tale about exactly this kind of evidence: 900 samples with
supremum exactly 1.000000 preceded an immediate adversarial counterexample. A
full repair must be **global**, must **handle** pass-throughs rather than exclude
them, must survive the **tight** regime, and must reach `⌈log₂ f(B)⌉` rather than
`max_j nc(c_j)`. Failing that, the honest state of the record is
`43 ≤ S(13) ≤ 45`.

### 8.2 The computational alternative, measured

Theorem 12 turns the cost question into a question about one number, and two
consequences are immediate.

**Our `n = 11` computation is the `n = 13` level-6 computation.** Since
`D(11) = 6`, the certified run of §7 is a level-6 run, and by Theorem 12 its
census transfers to `n = 13` exactly, plus two cube states. It is not an
approximation to that cost; it is that cost.

**The next level exists nowhere cheaper.** `n_min(7) = 13`, so no smaller channel
count has a level-7 computation at all and it cannot be rehearsed. By Lemma 11
it is a *single* subproblem: the unique width-13 successor of the full cube must
be shown to need at least 43 further comparators. The free chain reaches
`C(13) = 37` in 3 ms; level 5 at `n = 13` is measured at **50,922,864 states,
3.35 GB, 299 s** on a ten-core M4; level 6 at `n = 13` is the first level a
16 GiB machine cannot hold — a probe reached ~89.7 M states at 6.45 GiB before
the operating system killed it at 9 m 10 s, establishing a practical ceiling near
6 GB rather than the nominal 8 GB, because memory compression makes resident size
understate pressure exactly when it matters.

Above that everything is extrapolation and we mark it so. Per-level state
multipliers measured on the `n = 12` ladder are 12.5 / 46.1 / 8.4 / 245.9,
geometric mean 33; applied to the level-5 anchor, **level 7 costs 5.6 × 10¹⁰ to
3.1 × 10¹² states, 2.4–195 TB and 3.8–238 machine-days** of pure touch time
before a byte is stored, and level 8 costs 59 machine-days at its most optimistic
and of order 140 years at its measured ceiling. The disk bracket is wide because
of a disagreement about bytes per state, not state count: the census is a
travelling wave in channel width, so bytes per state *rises* with level. A full
`n = 13` run we estimate at 1.8 × 10¹² to 7.4 × 10¹⁴ states, **80 TB to 35 PB**,
a measurement-anchored derivation that brackets Harder's own informal estimate of
"over 20,000 TB".

**One caveat is live and we do not paper over it.** The multiplier bracket was
measured with on-line subsumption *off*, in the bounded-target regime, whereas
the `n = 11` run of §7 used eviction-mode subsumption and was a full run. Its
95.2 M inserted states against the 50.9 M level-5 anchor would imply a
level-5→6 multiplier near 1.9×, far below the optimistic floor of 8.4× — but the
figures are not comparable, and their two axes disagree in opposite directions:
memory came in 1.6× *below* the predicted floor while wall time came in 3.5×
*above* the predicted ceiling. Re-deriving the multiplier under matched settings
is the single measurement that would most change this picture, and it has not
been done. Until it is, the level-7 bracket is provisional.

### 8.3 What does not work

Eight techniques were implemented and instrumented before being rejected; all are
reported with their measurements in [Art], since a negative result at this scale
is expensive to reproduce. Cost *per state* can be reduced — an abstraction
rewrite is worth 45× at width 13, unconditionally. The *number* of states cannot:
on-line subsumption nets 2.7× after its index; an end-game filter family is
capped at 1.0008× by a theorem and measured at 1.000×; a SAT hybrid was 4–5
orders of magnitude *slower* on the unsatisfiable instances exhaustion needs,
because "this state needs at least `b` more comparators" is a statement about a
function of the assignment and no clause can learn it; ambient reduction is
exactly 1.00×, there being no smaller ambient to reduce to; and
checkpoint-and-recompute withholds at most 1/33 of the footprint, since 99.6 % of
the memo is created by the final bound iteration. Throughput is a hardware
constant: 170,882 states/s on ten M4 cores against 141,059 on a 24-core server.

**Every technique here reduces bytes per state or bytes held at once; none
reduces the number of states, and that is what binds.** Every exhaustive
computation in the literature that reached 10¹² states did so at one bit to four
bytes per state via a bijective rank function. We are at 30–90 bytes and provably
cannot have one, since a minimal perfect hash needs the complete key set in
advance. That gap, not the partitioning scheme, separates this problem from its
precedents.

---

## 9. What we trust

Following Harder, we enumerate the trusted base rather than claim correctness.
We do not require, or expect, it to be free of bugs; only that no bug was
triggered in the runs reported.

| component | trusted? | note |
|---|---|---|
| hardware, OS, Python 3.14 | **yes** | general-purpose |
| GHC and runtime; Isabelle extraction and kernel | **yes** | general-purpose; §7 only |
| the checker's formal problem statement | **yes** | the only trusted problem-specific component |
| the six verifier scripts | no | short, stdlib-only; two are mutually independent |
| the search engine and its patch stack | no | its result is independently certified |
| Theorems 6, 7, 12 | no for §7; **yes** for §§5–6 | no proof assistant has checked them |
| certificate generator and parser | no | the checker re-derives the bound |
| the coverage census of §5.5 | **yes** — a defect | not regenerable by a shipped tool |

Three points follow. **Independence is not uniform:** the two audit scripts share
no code, but the two wave verifiers carrying §5 *import* the first script's
primitives, so they are extensions rather than independent re-derivations. **We
meet the de Bruijn criterion for §7 and not for §§5–6:** the certified
computation is checkable by an independent small program, whereas the new
theorems are human proofs whose lemmas are tested on samples — and given
Proposition 9's history, sample agreement is weak evidence we do not offer as
more. **"Unchanged" is scoped:** the checker's extracted verified core is
unchanged, but one patch edits its Haskell wrapper to permit large reads, so the
accurate description is *a verified prefix checker with an unverified decoder*,
and the protocol is to run both available checkers and record both verdicts.

Reproduction is tiered in [Art]: the counterexample by hand in five minutes; all
of §§3 and 5 in about nine minutes on a laptop with no dependencies; the
certificate in 95 minutes given 8 GB; regenerating it in four days given 48 GB
and swap. Reduced-population modes of the verifiers exist and do **not**
reproduce the percentages here.

The audit was carried out by language-model agents under a fixed protocol: one
read the primary source, a second was instructed to defend the chapter and refute
the first, a third attempted repairs and refuted its own candidate lemma. We
claim no methodological result; what matters is that no mathematical claim rests
on a model's assertion. Every quantitative statement is produced by one of the
six scripts, and the central counterexample is a three-comparator network
checkable on paper.

---

## 10. Limitations

**10.1 Two archival items were not obtained, and one may be the origin of the
error.** The *Transactions* note [VV72a] is what the chapter cites *specifically*
for the false structural claim. If it states the claim correctly — with a
cleanliness hypothesis, say — the chapter's error is introduced rather than
inherited, and the note may hold the missing argument; if it states it in the
same false form, the error originates there. Either way `S(13) ≥ 43` is
unaffected (§4.3). The 1971 Stanford dissertation [VV71a] is not digitised and is
absent from the Stanford technical-report collection released in December 2025,
which we checked. Obtaining either is the highest-value next step, and is
procurement rather than research.

**10.2 No theorem here is machine-checked as a proof.** Theorems 6, 7 and 12 are
human proofs whose lemmas and conclusions are tested on samples; the Isabelle
content we rely on verifies a certificate checker, not our mathematics.
Formalising Theorem 6 is small and is the natural next step.

**10.3 The prevalence percentages are generator-dependent.** 61.0 %, 42.4 % and
27.1 % are properties of the generators and of a fixed seed, not rates under any
measure on sorting networks. They establish that the failure is common in
ordinary networks; they do not establish a rate. We also do not know what
fraction of *size-optimal* networks is escape-free, and a referee is entitled to
ask.

**10.4 The coverage census of §5.5 is not regenerable by a shipped tool.** Its
22.4 % and 49.6 % agree with the shipped corpus where the two overlap, but until
the census is re-implemented they are measurements we have not made reproducible.

**10.5 The open problem, stated precisely.** By Lemma 5, equation (8) is a
realizability question: which multisets `{(a(c), ε(c), γ(c), r(c))}` arise from
an actual sorter, and in particular is there a constraint linking small `a(c)` —
a shallow node with small subtrees — to large `r(c)`, a long private journey for
the second maximum? That is the shape of the missing lemma. We recommend nothing
else: the routes in §5.6 are closed and Theorem 7 widened Theorem 6 by 0.7 %.

**10.6 Cost figures are provisional and partly analytic.** The level-7 bracket is
provisional for the reason in §8.2, and its disk figure rests on a
bytes-per-state model on which two of our own analyses disagree (136–179 TB
versus 136–195 TB at identical state counts); three measurements of the level-5
anchor circulate, spanning 0.7 %, and we quote the archived one. Two closed
routes in §5.6 — the fixed-channel Kraft route yielding 43 at `n = 13`, and the
pair-counting route yielding 156 where 392 is needed — are elementary but are not
in the artifact.

**10.7 Known artifact defects.** [Art] lists them; three affect what can be
cited. One registered check has the literal predicate `True`. Two others
establish for one admissible tree shape what the surrounding prose asserts for
six (the universal statements are true and were confirmed separately). And two
strings printed by the shipped audit script are themselves retracted: it calls
`35 + 9` "the published bound", which §4.2 shows it is not, and it labels one
check "pass-through comparators are the sole obstruction", which §5 supersedes —
escapes are the right notion, and that check in any case tests only the fatal
directions. The strings must be corrected before release; doing so changes a
published digest, which is why it is bundled with the one other pending source
change. One script's shape ordering also disagrees with the adjudicated authority
on which of two equal-`f` shapes is listed first; this paper prints no per-shape
class labels.

**10.8 Configuration provenance.** Configuration files under
`config/experiment-v1/` in the research repository are frozen historical
artifacts of a predecessor method experiment that terminated `METHOD_REJECTED`;
one records a 44-comparator search target, gated behind a pass that can never
occur. Nothing reported here executed under those configurations, and no
computation in this paper uses 44 as a target, bound, feature or stopping
condition. The number appears only as the tabulated value under audit.

**10.9 `S(13) ≥ 44` is not refuted.** Nothing here suggests it is false; our
claim is exactly and only about the status of its proof. Van Voorhis closed his
chapter by predicting that the next improvement in the lower bound for `S(N)`
would come from an approximation of `P(3,N)`. Fifty-four years on, `P(2,N)` is
still open.

---

## References

[Art] The authors. *Artifact repository: verifiers, patches, theory documents,
evidence manifests.* To be deposited; layout in `ARTIFACT.md`. Cited throughout
for check-level indexes, full proofs, refuted routes and measurement records.

[Ba68] K. E. Batcher. Sorting networks and their applications. *AFIPS Spring
Joint Computer Conference*, 1968, 307–314.

[BZ14] D. Bundala, J. Závodný. Optimal sorting networks. *LATA 2014*, LNCS 8370,
236–247. arXiv:1310.6271.

[CCFS16] M. Codish, L. Cruz-Filipe, M. Frank, P. Schneider-Kamp. Sorting nine
inputs requires twenty-five comparisons. *JCSS* 82(3), 2016, 551–563. Conference
version ICTAI 2014; arXiv:1405.5754.

[Cert] The authors. *Certificate of the minimal size of 11-channel sorting
networks, independently regenerated.* 2,442,317,348 bytes, SHA-256 `672c433f…`.
To be deposited.

[CLS17] L. Cruz-Filipe, K. F. Larsen, P. Schneider-Kamp. Formally proving size
optimality of sorting networks. *J. Automated Reasoning* 59, 2017, 425–454.

[Do25] B. Dobbelaere. *Smallest and fastest sorting networks for a given number
of inputs.* `bertdobbelaere.github.io/sorting_networks.html`; changelog entry of
2025-04-21; consulted 2026-08-22.

[EK07] E. A. Emerson, V. Kahlon. Symmetry and completeness in the analysis of
parameterized systems. *VMCAI 2007*, LNCS 4349, 178–192.

[EN95] E. A. Emerson, K. S. Namjoshi. Reasoning about rings. *POPL 1995*, 85–94.

[FK73] R. W. Floyd, D. E. Knuth. The Bose–Nelson sorting problem. In *A Survey of
Combinatorial Theory*, North-Holland, 1973, 163–172.

[Ha20] J. Harder. *An answer to the Bose–Nelson sorting problem for eleven and
twelve elements.* arXiv:2012.04400v3, 2022. Artifacts: `jix/sortnetopt`,
doi:10.5281/zenodo.4139152; certificate, doi:10.5281/zenodo.4108365.

[Ju95] H. Juillé. Evolution of non-deterministic incremental algorithms as a new
approach for search in state spaces. *ICGA 1995*, 351–358.

[KKW10] A. Kaiser, D. Kroening, T. Wahl. Dynamic cutoff detection in
parameterized concurrent programs. *CAV 2010*, LNCS 6174, 645–659.

[KLM+95] N. Kahale, T. Leighton, Y. Ma, C. G. Plaxton, T. Suel, E. Szemerédi.
Lower bounds for sorting networks. *STOC 1995*, 344–353.
doi:10.1145/225058.225178.

[Kn73] D. E. Knuth. *The Art of Computer Programming, Vol. 3.* Addison-Wesley,
1973. §5.3.4, exercise 42 and its answer.

[VV71a] D. C. Van Voorhis. *Efficient sorting networks.* Ph.D. dissertation,
Stanford University, 1971. **Not obtained** — §10.1.

[VV71b] D. C. Van Voorhis. *A lower bound for sorting networks that use the
divide-sort-merge strategy.* Stanford DSL TR 17, STAN-CS-71-238, 1971.

[VV72] D. C. Van Voorhis. Toward a lower bound for sorting networks. In
R. E. Miller, J. W. Thatcher (eds.), *Complexity of Computer Computations*,
Plenum, 1972, 119–129. Equation numbers, Theorem 1, Table 1 and Figs. 1–5 cited
here are the chapter's own; page numbers are book pages.

[VV72a] D. C. Van Voorhis. An improved lower bound for sorting networks. *IEEE
Trans. Computers* C-21(6), 1972, 612–613. **Not obtained** — §10.1.
