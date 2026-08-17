# Adversarial verification of the van Voorhis (1972) dispute

**Role:** independent adversarial verifier. Brief: *defend van Voorhis, refute the
refutation.*
**Date:** 2026-08-18
**Source read from scratch:** D. C. Van Voorhis, "Toward a Lower Bound for Sorting
Networks", in R. E. Miller & J. W. Thatcher (eds.), *Complexity of Computer
Computations*, Plenum Press 1972, **pp. 119-129** = PDF pp. 124-134 of
`papers/Complexity of Computer Computations ....pdf`. All page numbers below are
**book** pages. Equations quoted from the rendered page images, not from OCR.
**My machine check:** `tools/verify_kraft_dispute.py` (stdlib only, ~0.6 s,
32 checks, exit 0). It shares no code with `tools/verify_huffman2.py`,
`.build/v3-theory/vv_core.py` or `.build/v3-theory/stress.py`.

---

## VERDICT: **(A) HOLE CONFIRMED**

The prior campaign read the chapter correctly. Equations (5) and (6) are false as
written, they are false under *every* reading of the chapter's definitions that I
can construct, and equation (7) — the only route from them to the result — is
derived from them and from nothing else. Therefore (8), (10) and (12), hence
`P(2,13) >= 9`, hence `S(13) >= 44`, are **not proved by this chapter**.

They are also **not refuted**. I could not break (8) or (12) with ~15 000
networks including a hill-climbing search that targeted them directly.

I attempted the steelman defences below and each one failed. I also constructed
a candidate repair, verified it rescues the disputed 3-sorter — **and then broke
it** with a 6-sorter found by adversarial search. That is the single most useful
new fact in this document: the *natural* repair does not work either.

---

## 1. The chapter's definitions, as I read them

Verbatim, from the page images:

> "If we assign to any input lead `i_j` a value higher than all other inputs,
> then this input value follows a unique path `p_j` from `i_j` to `o_N`, becoming
> the higher output of all comparators traversed." — **p. 120**

> "Pruning the comparators traversed by these paths separates the N-sorter into
> `k` wires and an `(N-k)`-sorter. Let `p(k,T)` represent the greatest number of
> comparators that can be pruned from N-sorter `T` for any of the `(N choose k)`
> different choices of `k` input leads." — **p. 121**

So `p(2,T)` counts the **union** of the two traced paths. It must: eq (2)
`S(N) >= S(N-k) + P(k,N)` is only valid if the residual network has
`|T| - (pruned)` comparators.

> "It has been observed [Van Voorhis (1972A)] that the MAX subnetwork of any
> N-sorter is a binary tree with `N` leaves (the input leads) and `N-1` **branch
> nodes (the comparators)** rooted at `o_N`." — **p. 121**

> "Let `T` be any N-sorter. The MAX subnetwork of `T`, `MAX(T)`, **includes `N-1`
> comparators**, which we label `c_1, c_2, ..., c_{N-1}`." — **p. 121**

> "We define `nc(C_j)` to be the number of comparators from `i_{j1}` to `c_j`,
> plus the number from `i_{j2}` to `c_j`, plus the number from `c_j` to `o_N`.
> (Comparator `c_j` itself is counted exactly once.)" — **p. 122**

> "Since the second largest input value takes the lower output lead from `c_j`,
> `T` must include a path `q_j` from the lower output lead of `c_j` to `o_{N-1}`.
> **The paths `q_j`, `1<=j<=N-1`, together form a binary tree rooted at
> `o_{N-1}`**, which we call the MAX2 subnetwork." — **p. 122**

> "... then the two paths from `i_{j1}` and `i_{j2}` through `c_j` to `o_N` and
> `o_{N-1}` **together include `nc(C_j) + nc(q_j)` comparators.** Therefore,
> `p(2,T) = max_{1<=j<=N-1} [nc(C_j) + nc(q_j)]`" — **p. 122, eq (5)**

> "MAX2(T) is a binary tree, so the path lengths `nc(q_j)`, `1<=j<=N-1`, satisfy
> `sum_{1<=j<=N-1} 2^{-nc(q_j)} = 1`." — **p. 124, eq (6)**

> "Equation (5) implies that `nc(q_j) <= p(2,T) - nc(C_j)`, so that
> `sum_{1<=j<=N-1} 2^{-[p(2,T)-nc(C_j)]} <= 1`." — **p. 124, eq (7)**

> "Since `p(2,T)` is integral, we conclude that `p(2,T) >= ceil(log2(f(MAX(T))))`,
> where `f(MAX(T)) = sum_{1<=j<=N-1} 2^{+nc(C_j)}`." — **p. 124, eqs (8), (9)**

There are **no** side conditions anywhere: no standard-form restriction, no
first-comparator normalisation, no minimality hypothesis, no restriction on `N`.
The starred footnote on p. 121 says only *"In this section we assume several
properties of binary trees which are derived, for example, in Knuth(1968A)."*

### 1.1 The load-bearing chain, isolated

```
(6) MAX2 Kraft = 1        (5) p(2,T) = max_j [nc(c_j)+nc(q_j)]
              \                /
               ->   (7)   <---
                     |
                    (8)  p(2,T) >= ceil(log2 f(MAX(T)))
                     |
                (10),(11),(12)  P(2,N) >= ceil(log2 F(N))
                     |
      P(2,13) >= ceil(log2 392) = 9,  S(13) >= S(11)+9 = 35+9 = 44
```

`F(13) = 392` and `ceil(log2 392) = 9` are confirmed independently — my own
exact DP over binary-tree shapes reproduces the chapter's whole Table 1 column
`F(N)`, `N = 1..16` (check **A1**). So the 44 is exactly `S(11) + ceil(log2 F(13))`
and the "9" comes from (12), i.e. from (7), i.e. from (5) and (6).

Note what (7) actually needs: only `sum_j 2^{-nc(q_j)} <= 1`, and only
`nc(c_j) + nc(q_j) <= p(2,T)`. The equalities in (5) and (6) are stronger than
required. **The failures below are in the fatal direction anyway.**

---

## 2. The counterexample, recomputed by hand against those definitions

`T1 = [(0,1), (0,2), (1,2)]` on channels `0,1,2`, min to the low lead, so
`o_N = ch 2`, `o_{N-1} = ch 1`. `|T1| = 3 = S(3)`; it sorts (check **C0**).

**Max paths.** Largest value entered at each lead, always leaving on the high
lead:

| entered at | traverses | ends |
|---|---|---|
| ch0 | `c_a=(0,1)`, `c_c=(1,2)` | ch2 |
| ch1 | `c_a=(0,1)`, `c_c=(1,2)` | ch2 |
| ch2 | `c_b=(0,2)`, `c_c=(1,2)` | ch2 |

**`MAX(T1) = {c_a, c_b, c_c}` — three comparators.** The chapter says
`MAX(T)` "includes `N-1` comparators" = 2. Its premise is already false here.
`c_b=(0,2)` is a *pass-through*: the max enters and leaves it on lead 2 and no
other max-path reaches lead 0 at that time, so `c_b` is on the subnetwork but is
not a branch node. The branch nodes are `c_1 = c_a`, `c_2 = c_c`, and there are
indeed `N-1 = 2` of them (checks **C1**, **C2**).

**`nc`.** For `c_1 = c_a`: `L(c_1) = {ch0}`, `R(c_1) = {ch1}`, so
`0 + 0 + |{c_a,c_c}| = 2`.
For `c_2 = c_c`: longest left arm `ch0 -> c_a` (1 comparator before `c_c`),
longest right arm `ch2 -> c_b` (1 comparator before `c_c`), stem `{c_c}` (1).
Literal `nc(c_2) = 1+1+1 = 3`; counting only branch nodes, `1+0+1 = 2`.

**`q_j`.** Put the largest at `ch0` and the second largest at `ch1`; they meet at
`c_a`; the max goes to ch1, the second max to ch0. At `c_b=(0,2)` the second max
meets only the smallest value, so it rises to ch2. At `c_c=(1,2)` it meets **the
largest value again**; the largest takes ch2 `= o_N`, the second largest takes
ch1 `= o_{N-1}`. So `q_1 = (c_b, c_c)`, `nc(q_1) = 2`.
For `c_2 = c_c`: its lower output lead **is** `o_{N-1}`, so `q_2` is empty and
`nc(q_2) = 0`.

**Eq (6):** `2^{-2} + 2^{-0} = 0.25 + 1 = 1.25 > 1`. **FALSE, fatally.**
MAX2 is not a binary tree with `N-1` leaves: the "leaf" of `q_2` *is* the root,
and it lies on `q_1`. The leaves are not an antichain (check **C5**).

**Eq (5):** it claims the two traced paths "together include
`nc(c_1)+nc(q_1) = 2+2 = 4` comparators". They include **3** — the union is
`{c_a,c_b,c_c}` — because the two values re-meet at `c_c`. And `p(2,T1) = 3`
(forced: `|T1| = 3`). So eq (5) returns 4 for a quantity that is 3: it **exceeds**
`p(2,T)`, which is the direction that kills (7) (checks **C3**, **C4**).

**Eq (7)/(8):** with the literal `nc`, `f = 2^2 + 2^3 = 12` and (8) asserts
`p(2,T) >= ceil(log2 12) = 4 > 3`. **Eq (8) itself is false for T1** under the
literal reading of eq (9) (checks **C6**, **C7**). With `nc` on the branch tree,
`f = 2^2 + 2^2 = 8` and (8) asserts `>= 3`, which holds with equality (**C8**).

**Control.** The *other* optimal 3-sorter `T2 = [(0,1),(1,2),(0,1)]` has no
pass-through, `nc(q_j) = 1,1`, Kraft `= 1` exactly, eq (5) exact, eq (8) fine
(check **C'1**). So the fault is a property of the network, not an artefact of
`N = 3` being too small.

---

## 3. The steelman defences I tried, and why each fails

| # | defence | outcome |
|---|---|---|
| S1 | *"`nc` means branch-node depth, not literal comparator count" (Fig. 5 is captioned "**Symmetric** MAX Subnetwork", i.e. a redrawn tree).* | This **is** the right reading of (9) — it is the only one consistent with Fig. 5 and Table 1, and it makes eq (8) survive every test. **It does not rescue (5) or (6).** With tree `nc`, eq (5) still gives `2+2 = 4 > 3 = p(2,T1)`; and `nc(q_j)` is unaffected, so eq (6) is still 1.25. |
| S2 | *"eq (6) only needs `<= 1`, and the equality claim is a slip."* | Correct that only `<=` is needed — and this fully excuses the chapter's own Fig. 4 example (see §4). But T1 gives `> 1`, which is the fatal side. |
| S3 | *"Read `q_j` in the pruned `(N-1)`-sorter, i.e. drop the comparators shared with the max path."* | Makes it **worse**: `q_1` shortens to 1 comparator, `q_2` stays 0, Kraft `= 1.5`. |
| S4 | *"Contract MAX2 to a tree and use tree depths for `nc(q_j)`."* | Makes it worse: the `q_2` leaf is the root, depth 0; contraction cannot move it. Kraft `>= 1.5`. |
| S5 | *"Exclude the root branch node from the `q_j` family."* | Then eq (7) loses the `2^{nc(c_{N-1})}` term but eq (9) keeps it; the two sums no longer match and (8) does not follow. Also `f` would no longer be Theorem 1's `f`, so `F(N)` and Table 1 would be wrong. |
| S6 | *"A hidden standard-form / normalisation hypothesis."* | The chapter states none, and `T1` is already a standard (uncrossed, `a<b`, min-low) network. |
| S7 | *"A hidden minimality hypothesis."* | `T1` is size-optimal: `|T1| = 3 = S(3)`. Also `P(2,N) = min_T p(2,T)` explicitly ranges over **all** N-sorters (eq (1), p. 121), so a single bad `T` is enough. |
| S8 | *"`p(2,T)` might be a sum, not a union."* | Then eq (2) `S(N) >= S(N-k)+P(k,N)` would be invalid, since the residual has `|T| - |union|` comparators. p. 121's "the greatest number of comparators that can be pruned" is unambiguous. |
| S9 | *"The failure only happens in slack-rich, non-extremal networks, so it can't threaten the bound."* | **False, and this is the most important finding.** In my sweep, **105 of 387** networks (27 %) simultaneously have `p(2,T) = ceil(log2 f_tree(MAX(T)))` *exactly* (zero slack) **and** eq (6) failing with sum `> 1`. The broken lemma fails precisely in the regime where the theorem is tight (check **D0**). |
| **S10** | **the strongest defence: *"`MAX(T)` and `MAX2(T)` are comparator-disjoint"*.** Sketch: every comparator of `MAX(T)` has both inputs on MAX-edges; `q_j` starts on `c_j`'s *lower* output, which is not a MAX-edge; a comparator with a non-MAX input is not in `MAX(T)`; induct. Disjointness would make eq (5) an exact union with nothing double-counted **and** force every `q_j` to take high leads throughout, hence prefix-free, hence Kraft — repairing (5) and (6) at one stroke. | **REFUTED.** The premise "every comparator of `MAX(T)` has both inputs on MAX-edges" is exactly what pass-through comparators violate. On `T1`, `MAX(T1) = {c_a,c_b,c_c}` and `MAX2(T1) = {c_b,c_c}` — they share **two** comparators, one of them the **root branch node** `c_c` (check **C10**). Across the sweep, `MAX2` meets `MAX` in **233 / 387 (60 %)** networks and meets a **branch node** of `MAX` in **232 / 387 (60 %)** (check **D-1**). Disjointness *does* hold for Batcher's 8-sorter (check **C11**) — which is again why Fig. 4 does not expose it. |

**Conclusion of §3: there is no reading, and no available structural lemma,
under which (5) and (6) are true.** S10 is worth recording in detail because it
is the argument a sympathetic reader reconstructs first, it is exactly the
argument van Voorhis must have had in mind, and it is false for the same single
reason everything else is: **pass-through comparators**, which the chapter's
`N-1`-comparator premise denies exist.

---

## 4. The chapter's own worked example (Fig. 4) — the 0.75 claim

I reconstructed Batcher's odd-even 8-sorter (19 comparators) from the standard
algorithm, not from any table, and verified it sorts.

- `MAX(T)` has **7 comparators, 7 branch nodes, 0 pass-throughs** — so Figs. 3
  and 5 agree and the example cannot discriminate the literal and tree readings
  of `nc`.
- `nc(c_j)` multiset `= {3,3,3,3,4,4,5}`, exactly the numbers printed in
  parentheses in **Fig. 5**; `f(MAX(T)) = 96 = F(8)` (checks **B1**, **B2**).
  This is a strong confirmation that my reading of `nc` is the chapter's.
- `nc(q_j) = 4,4,4,4,3,3,2` and
  `sum_j 2^{-nc(q_j)} = 4/16 + 2/8 + 1/4 = **0.75**`.

**The prior campaign's Fig. 4 claim is confirmed** (check **B3**): eq (6) is not
an equality even in the chapter's own worked example. The reason is benign —
MAX2 has pass-through comparators of its own, so `nc(q_j)` exceeds the MAX2 tree
depth and the sum drops below 1 — and it is **harmless**, because (7) needs only
`<= 1` (check **B4**). Eq (5) and eq (8) both hold on this example (**B5**,
**B6**).

So Fig. 4 exposes that (6) is misstated but not that it is dangerous. That is
very likely how the error survived: the one example in the paper fails the
equation on the safe side.

---

## 5. How common, and where it bites

387 constructed networks (bubble, insertion, odd-even transposition, Batcher for
`n = 3..10`; randomised prefix + thinning for `n = 3..8`; random channel
relabellings), every one verified a sorter by the 0/1 principle:

| statement | violations |
|---|---|
| `MAX(T)` has `>= 1` pass-through comparator | 236 (61.0 %) |
| some `q_j` re-meets the max path after `c_j` | 233 (60.2 %) |
| eq (5) **exceeds** `p(2,T)` (fatal direction) | 172 (44.4 %) |
| eq (6) `sum > 1` (fatal direction) | 164 (42.4 %) |
| `MAX2(T)` shares a comparator with `MAX(T)` | 233 (60.2 %) |
| `MAX2(T)` shares a **branch node** with `MAX(T)` | 232 (59.9 %) |
| eq (7) fails, literal `nc` | 102 (26.4 %) |
| eq (8) fails, literal `nc` | 102 (26.4 %) |
| eq (7) fails, **tree** `nc` | **0** |
| eq (8) fails, **tree** `nc` | **0** |
| conclusion `p(2,T) >= ceil(log2 F(n))` fails | **0** |
| zero slack **and** eq (6) broken | **105 (27.1 %)** |

Independently of the prior campaign's population (they report 34 % of 560), I
get 42 % of 387 — same order, same phenomenon.

### 5.1 The fault is localised exactly: pass-through comparators

Call an N-sorter **clean** if every comparator its max-paths traverse is a branch
node — i.e. if the chapter's premise *"`MAX(T)` includes `N-1` comparators"* is
actually true of it.

> Among the **151 clean** sorters in the sweep, the number that violate eq (5),
> or eq (6), or `MAX`/`MAX2` disjointness, is **zero** (check **D-2**). Among the
> 236 with pass-throughs, eq (6) breaks in 164.

So the chapter is *correct for the networks it thinks it is talking about*. The
whole defect is that pass-through comparators exist and the chapter's premise
denies them. This is the sharpest available statement of the gap, and it is also
the natural boundary for any repair: **eq (8) for clean sorters is a separate,
apparently true statement; the general case is what is missing.** Note that
`61 %` of the sweep is *not* clean, so this is not a small residual case.

Exhaustive brute force, no pruning at all: every sorting network on 3 channels
with `<= 4` comparators (42 of them) and on 4 channels with `<= 6` comparators
(912 of them) satisfies the conclusion (checks **E3**, **E4**).

---

## 6. A candidate repair — and its refutation

The chapter's mistake is that `nc(c_j) + nc(q_j)` double-counts the comparators
where the two values re-meet. The obvious fix is to replace the sum by the union
from the start. Define

> `u_j` := the number of comparators actually pruned by the best pair of input
> leads whose max-paths merge at `c_j`. By definition `u_j <= p(2,T)`, with no
> re-meeting hazard, since it is a union.

Then eq (8) in the branch-tree reading follows immediately from

> **(K)** `sum_{j=1}^{N-1} 2^{-(u_j - nc_tree(c_j))} <= 1`

because `2^{nc_tree(c_j)} = 2^{u_j - m_j} <= 2^{p(2,T)} 2^{-m_j}`.

**(K) rescues the disputed 3-sorter exactly:** `u = (3,3)`, `nc_tree = (2,2)`,
sum `= 2^{-1}+2^{-1} = 1`. It also held on all 387 networks of the sweep.

**But (K) is false.** Hill-climbing (`.build/v3-theory-audit/adversarial.py`,
~14 500 networks) produced this 6-sorter:

```
T3 = [(2,3),(1,2),(0,4),(3,5),(2,4),(1,2),(4,5),(2,3),
      (0,3),(3,4),(1,3),(1,2),(0,3),(0,1),(1,2)]
```

`nc_tree = {3,3,3,3,5}`, `u = {6,5,6,8,6}`, `p(2,T3) = 8`, so
`m = {3,2,3,5,1}` and `sum_j 2^{-m_j} = 33/32 > 1` (check **D'3**).
Eq (8) still holds on `T3` with room to spare (`ceil(log2 64) = 6 <= 8`), so this
refutes the *repair*, not the *theorem*.

**This is why the verdict is (A) and not (C).** The gap is not a notational
ambiguity that a careful restatement closes; the first natural correct-by-
construction substitute for the Kraft step is itself false.

---

## 7. Where I disagree with, or would sharpen, the prior campaign

1. **The prior report is substantively correct**, and its own §7 status table is
   appropriately hedged ("eq (8) ... **NOT proved**. 0 counterexamples ... the
   published proof does not establish them"). I found no arithmetic error in it.
   Its numbers for T1 (`nc = 2,3`; `nc(q) = 2,0`; Kraft 1.25; `f = 12`;
   `p(2,T) = 3`) and for Fig. 4 (`nc(q_j) = 4,4,4,4,3,3,2`; 0.75) reproduce
   exactly under my from-scratch implementation.
2. **A commissioned independent code audit of `tools/verify_huffman2.py` and
   `.build/v3-theory/stress.py` found no bug capable of fabricating the
   violation.** It did find a real bug in `.build/v3-theory/vv_core.py`
   (`build_tree` aligns leaf paths by position-from-the-end, which is wrong
   whenever pass-throughs exist, and it crashes on `batcher(3)`), but that file
   is orphaned — nothing imports it and no reported number comes from it.
3. **Sharpening — the fault is one sentence, and it is a citation.** The
   proximate error is p. 121's *"`N-1` branch nodes **(the comparators)**"* and
   its restatement *"`MAX(T)` includes `N-1` comparators"*. Identifying branch
   nodes with comparators is exactly the bug; everything downstream inherits it.
   The chapter attributes that structural claim to **[Van Voorhis (1972A)] = "An
   improved lower bound for sorting networks", IEEE Trans. Computers 21(6),
   1972** (bibliography, back matter, "to appear"). Anyone repairing this must
   check the TC note first, not the chapter.
4. **Sharpening — the failure is not confined to slack.** 27 % of my sample has
   zero slack *and* a broken Kraft sum. The prior report does not make this
   point, and it is the strongest answer to "surely it's a harmless typo".
5. **Correction of emphasis on Fig. 4.** The prior report lists eq (6)'s failure
   on Fig. 4 as a gap. It is a *misstatement*, not a *gap*: at 0.75 the example
   is on the safe side and (7) still goes through. The load-bearing failure is
   `> 1`, and Fig. 4 does not exhibit it. Publishing should separate these.
6. **New negative results to add:** the union-based repair (K) is false (§6),
   and the `MAX`/`MAX2` comparator-disjointness lemma — the natural thing a
   sympathetic reader reconstructs, and almost certainly what van Voorhis had in
   mind — is false in 60 % of networks tested (S10). Both should be recorded
   before anyone spends time re-deriving them.
7. **Correction of provenance (§8).** The prior report treats `S(13) >= 44` as
   "the published bound". It is not published: the chapter's own Table 1 gives
   `L(13) = 42`, and the 44 exists only in Dobbelaere's table since April 2025.
   This substantially lowers the stakes of the finding — no peer-reviewed result
   is being overturned — while *raising* the value of writing it up, since the
   number is being propagated with no correct argument behind it.

---

## 8. Literature record and novelty

Independently searched (Google Scholar/Semantic Scholar citation lists, arXiv,
DBLP, Knuth's TAOCP Vol. 3 and his errata files, Stanford InfoLab TR index, DTIC,
Dobbelaere's table plus its Wayback history, Harder's Isabelle sources).

**1. No erratum, correction, gap-note or repair of this chapter's eqs (5)-(9)
exists anywhere I could reach.** The reason is stronger than "nobody found the
bug": **nobody has engaged with the argument at all.** Of ~19 recorded citations
of the chapter, the modern ones (Codish-Cruz-Filipe-Frank-Schneider-Kamp
arXiv:1405.5754; arXiv:1507.01428; arXiv:1502.08008) all cite it for a *different*
result — the one-value bound `S(n+1) >= S(n) + ceil(log2 n)`, which is actually
the content of the IEEE TC note. Grep for `P(2,`, `MAX2`, `MAX subnetwork`,
`Kraft`, `S(N-2)` across ~25 modern papers: **zero hits.**

**2. Knuth does not carry this bound.** TAOCP Vol. 3, 5.3.4 **exercise 42**
(p. 240) is *"(D. Van Voorhis.) Prove that `S(n) >= S(n-1) + ceil(lg n)`"*, and
the answer (p. 671) is Knuth's own three-line proof citing **only** IEEE Trans.
Computers C-21 (1972), 612-613. There is **no** two-value-pruning exercise, and
Vol. 3 never cites the Plenum chapter. No entry in Knuth's errata touches it.
So TAOCP provides **no independent support** for `P(2,N)`.

**3. Van Voorhis's own other works do not contain the argument.**
The IEEE TC note (C-21 (1972) 612-613) and its precursor Stanford TR
(DTIC AD0721701) are the **one**-value bound only. `papers/CS-TR-71-238.pdf`
(STAN-CS-71-238, *"A Lower Bound for Sorting Networks that Use the
Divide-Sort-Merge Strategy"*) is unrelated. **Not verified:** his 1971 Stanford
dissertation *"Efficient Sorting Networks"* is not digitized; if a fuller proof
exists anywhere, that is the one remaining place to look. The chapter cites
[Van Voorhis (1972A)] = the **IEEE TC note** for the *MAX-is-a-binary-tree* fact
specifically, so the false "`N-1` branch nodes (the comparators)" identification
may originate there; the 2-page TC full text is paywalled and was not obtained.
**These two items are the only unclosed archival gaps.**

**4. No later restatement, reproof, or formalization.** Harder (2020), the source
of `S(11) = 35` and `S(12) = 39`, does not cite the chapter; his Isabelle/HOL
development contains zero occurrences of "Voorhis". The Cruz-Filipe &
Schneider-Kamp Coq formalization covers generate-and-prune only. **There is no
machine-checked version of the `P(2,N)` bound.**

**5. The provenance of `S(13) >= 44` is far weaker than assumed — this changes
the framing of the whole dispute.**

| value | where | basis |
|---|---|---|
| 43 | Wikipedia; Dobbelaere's table **before 2025-04-21** | `S(12) + ceil(log2 13) = 39 + 4` |
| **44** | Dobbelaere's table **since 2025-04-21 only** | `S(11) + P(2,13) = 35 + 9` |

The chapter's own Table 1 (p. 128) gives `L(13) = **42**`, not 44. The 44 is
`S(11) = 35` (Harder 2020) plus `ceil(log2 F(13)) = 9` (this chapter). It entered
the record via Dobbelaere's changelog entry *"2025-04-21 Tighter lower bounds for
size, on suggestion of Jelmer Firet and based on principles in [VVoorh72]"*; no
publication or preprint by Firet was found.

> **`S(13) >= 44` has never appeared in a peer-reviewed publication.** The best
> *published* lower bound is **43**. The 44 is a 16-month-old web-table entry
> resting on a 54-year-old argument that no one has re-derived, re-proved, or
> machine-checked — and whose two structural lemmas are, per §2-§3, false.

**Novelty assessment.** Nothing found anywhere anticipates this finding. If the
result is written up, the correct claim is narrow and defensible: *the published
proof of `P(2,N) >= ceil(log2 F(N))` is invalid as written; the statement itself
is neither proved nor refuted; consequently the widely-tabulated `S(13) >= 44` is
not currently supported by a correct published argument, while `S(13) >= 43`
is.* Claiming more than that would overreach. Two caveats to state in any
write-up: (i) the dissertation and the TC note were not obtained; (ii) the
chapter's own `P(2,11) = 9` is likewise asserted without proof (*"It turns
out that..."*, p. 127) and does **not** follow from (5)-(9), since
`ceil(log2 F(11)) = 8` — but `P(2,13) >= 9` does not depend on it.

---

## 10. Reproduction

```
python3 tools/verify_kraft_dispute.py            # 32 checks, ~0.6 s, exit 0
python3 tools/verify_kraft_dispute.py --fast
python3 .build/v3-theory-audit/adversarial.py    # the (K) refutation search
```

Stdlib only, fixed seed, read-only, no network. Every network is **constructed**
(Batcher odd-even mergesort, bubble, insertion, odd-even transposition, random
prefix + thinning, random relabelling) or brute-force enumerated. No witness
network is embedded anywhere, and no target, bound or stopping condition in this
file refers to any specific comparator count for `n = 13`.
