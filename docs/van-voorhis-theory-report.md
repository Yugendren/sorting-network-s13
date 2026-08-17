# The van Voorhis Chapter, Read: E1′, the Proof Audit, and Huffman2

**Date:** 2026-08-18
**Primary source, now in hand:** David C. Van Voorhis, *"Toward a Lower Bound for
Sorting Networks"*, in R. E. Miller & J. W. Thatcher (eds.), **Complexity of
Computer Computations**, Plenum Press, New York 1972, **pp. 119–129**
(`papers/Complexity of Computer Computations …pdf`, PDF pages 124–134).
All equation numbers `(1)`–`(19)`, `Theorem 1`, `Table 1` and `Fig. 1`–`Fig. 5`
below are the chapter's own. Page numbers in citations are **book** pages.
**Machine check:** `tools/verify_huffman2.py` (pure stdlib, deterministic, 6.2 s,
36 checks, exit 0). Every number in this document is produced by that script.

This document does **not** edit `docs/s13-shape-case-split.md`,
`docs/research/xdomain-bound-theory.md` or `docs/research/synthesis-ranked-queue.md`;
it supersedes their §"external inputs" rows and their ILL action items.

---

## 0. Verdicts

> **1. The 2025 arXiv paper is irrelevant to us.** `2511.04107v2` is Chengu Wang,
> *"Depth-13 Sorting Networks for 28 Channels"* — a **depth** result for
> **n = 27, 28**. It touches neither `S(13)` nor any size bound. Our research
> snapshot is unchanged. It does not duplicate any planned work.
>
> **2. E1′ is CONFIRMED-WITH-MODIFICATION.** The chapter states the per-network,
> un-minimised bound *as its main result* — eq (8) — and derives the minimised
> form (10)/(12) **from** it, in one sentence, exactly as the case split assumed.
> The tree is exactly the max-path tree the case split guessed. The modification
> is real but benign: `f` must be read as **Theorem 1's recursive function of the
> branch tree**, not as eq (9)'s literal sum over actual comparator counts. The
> two readings differ, and only the tree reading is true (§3.4).
>
> **3. A LARGER PROBLEM, NOT PREVIOUSLY KNOWN TO US: the chapter's proof of
> eq (8) is not valid as written.** Two of its structural steps — eq (5) and
> eq (6) — are **refuted** by an explicit **optimal 3-sorter**. The failure is
> not exotic: it occurs in **34 %** of 560 randomly constructed sorters, and
> eq (6) is not even an equality in the chapter's own worked example (Fig. 4,
> Batcher's 8-sorter: the sum is 0.75, not 1). The **conclusion** eq (8) survives
> every test — **0 violations in ~5 600 constructed sorters** and consistency
> with all known `S(3..12)` — but it is, as of this reading, **an unproved
> conjecture**, and `S(13) >= 44` rests on it. See §3 and §7.
>
> **4. Huffman2 is PROVEN — relative to exactly the same two lemmas, and no
> further.** The unequal-leaf generalization goes through verbatim (§5.2). It is
> not independently broken; it is *exactly as sound as the published 44*. **At
> the n=13 root it gives nothing:** with `b_j ≡ S(11) = 35` it reproduces 44 and
> **kills no class** (§5.4). What it buys is a precise, cheap kill criterion
> (§5.5) and a partial-network pruning rule (§5.6).
>
> **5. A genuinely new, fully sourced strengthening: the MIN dual.** The chapter
> states it (p. 127) and uses it to prove `P(2,11) = 9 > 8 = ceil(log2 F(11))` —
> the *only* place in the chapter where the F-bound is beaten. Consequence: a
> 44-comparator 13-sorter must have **both** `f(MAX(C)) <= 512` **and**
> `f(MIN(C)) <= 512`. The case split's filters apply **twice**, free (§4).

---

## 1. Triage of the four PDFs

### 1.1 `2511.04107v2.pdf` — URGENT ITEM, verdict: no impact

Chengu Wang, *"Depth-13 Sorting Networks for 28 Channels"*, arXiv:2511.04107v2,
22 Nov 2025. Abstract (p. 1): *"We establish new depth upper bounds for sorting
networks on 27 and 28 channels, improving the previous best bound of 14 to 13."*

- **Object:** *depth* (layers), not *size* (comparator count). `S(n)` is a size
  quantity. The paper's own Table 1 (p. 2) is a table of **depth** bounds; its
  n = 13 row reads `depth LB 9 [BZ14] / depth UB 9 Van Voorhis` — the *depth* of
  a 13-sorter, which has been settled since Knuth. It says nothing about the 44.
- **The "13" in the title is the depth, and the channel count is 28.** This is a
  name collision with our problem, nothing more.
- **Does it change `44 <= S(13) <= 45`?** No. Nothing in it bears on size lower
  bounds, on van Voorhis's two-channel theorem, or on `S(13)`.
- **Does it duplicate planned work?** No. Method is reflection-symmetric
  generate-and-prune on prefixes plus a SAT completion (Ehlers-style), for
  **even** n; n = 13 is odd, so its central symmetry device does not even apply.
- **Anything worth stealing?** Marginal. Its Corollary 2 (p. 5) restricts prefix
  pruning to the centralizer `C(ρ_n) ≅ C_2 ≀ S_{n/2}`, and §2 has a cheap
  row-sum/column-sum subsumption filter *(p. 4)* that is a standard technique we
  already have. **Recommendation: cite in the survey as adjacent-but-orthogonal;
  do not queue any work.**

### 1.2 `225058.225178.pdf` — asymptotic lower bounds, no impact on n = 13

**Nabil Kahale, Tom Leighton, Yuan Ma, C. Greg Plaxton, Torsten Suel, Endre
Szemerédi, "Lower Bounds for Sorting Networks", STOC '95, Las Vegas** (ACM
0-89791-718-9/95/0005; 10 pp.; sha256 `4260d278…1427`). *(The OCR garbles the
author/affiliation pairing — one block reads "Torsten Suel … yuan@cs.stanford.edu"
— so the list above is the canonical one for this paper.)* From p. 1:

> *"We prove a lower bound of (1.12 − o(1)) n log n for [the size of any n-input
> sorting network] … We also prove a lower bound of (c − o(1)) log n, where
> c ≈ 3.27, on the depth of any sorting network; the best previous result of
> approximately (2.41 − o(1)) log n was established by Yao in 1980."*

**Verdict: asymptotic, not exact — no impact.** At n = 13, `(1.12 − o(1)) n log n`
is vacuous: the `o(1)` is unquantified and the claim is asymptotic. Its value to
us is as the right citation for *why* exact small-n techniques are the only route
to `S(13)`, and as evidence that the strongest asymptotic machinery available
(potential functions over the Ajtai–Komlós–Szemerédi line) does not descend to
this range. **No action.**

### 1.3 `CS-TR-71-238.pdf` — the adjacent TR, no impact

**David C. Van Voorhis, "A Lower Bound for Sorting Networks that Use the
Divide-Sort-Merge Strategy", Stanford Digital Systems Laboratory Technical Report
No. 17, STAN-CS-71-238 / SEL-71-051, August 1971** (15 pp.; sha256
`58ae3c83…dc55`). Abstract: bounds the merge cost `M_g^(k+1)` and concludes that
*"an N-sorter network which uses the g-way divide-sort-merge strategy must contain
at least order N (log₂ N)² comparators."*

**Verdict: no impact.** It is a lower bound for a *restricted class* of networks
(those built by divide-sort-merge) and says nothing about unrestricted `S(13)`;
its `N(log N)²` rate is above the true `Θ(N log N)`, which is precisely why the
restriction matters. It is **not** the source of the two-channel theorem — the
Plenum chapter is. Already identified in
`docs/research/xdomain-bound-theory.md` §1.4. **No action.**

### 1.4 The Plenum volume — the blocking item, now unblocked

`docs/research/xdomain-bound-theory.md` §1.4 and
`docs/research/synthesis-ranked-queue.md` both carry an open **USER ACTION /
inter-library-loan** item for this chapter. **It is closed.** The chapter is in
`papers/`, pp. 119–129, fully legible.

---

## 2. What the chapter actually says (verbatim)

### 2.1 The pruning operation and eq (1)–(2)

> *"If we assign to any input lead `i_j` a value higher than all other inputs,
> then this input value follows a unique path `p_j` from `i_j` to `o_N`, becoming
> the higher output of all comparators traversed."* — p. 120

> *"Let `p(k,T)` represent the greatest number of comparators that can be pruned
> from N-sorter `T` for any of the `(N choose k)` different choices of `k` input
> leads. Then we define `P(k,N) = min_T p(k,T)` … It follows immediately that
> `S(N) >= S(N-k) + P(k,N)`."* — p. 121, eqs (1), (2)

So `p(2,T)` is a **per-network** quantity and `P(2,N)` is its minimum. This
already settles half of question (a): the un-minimised object is named and used.

### 2.2 The tree — question (c)

> *"For any N-sorter network `T`, the paths `p_j`, `1<=j<=N`, from `i_j` to `o_N`
> together form a subnetwork of `T`, which we call the MAX subnetwork. … It has
> been observed [Van Voorhis (1972A)] that the MAX subnetwork of any N-sorter is
> a binary tree with `N` leaves (the input leads) and `N-1` branch nodes (the
> comparators) rooted at `o_N`."* — p. 121

**This is exactly the max-path tree of `docs/s13-shape-case-split.md` §3**:
leaf `i` = input channel `i`, root = the maximum output, path traced by the
largest value (equivalently the single 1 of the one-hot input `e_i`). Question
(c): **confirmed, no modification.** The doc's working interpretation was right.

### 2.3 `nc`, eq (5), MAX2, eq (6)

> *"Let `p_{j1}` be the longest path in MAX(T) that traverses `L(C_j)`, and let
> `p_{j2}` be the longest path in MAX(T) that traverses `R(C_j)`. We define
> `nc(C_j)` to be the number of comparators from `i_{j1}` to `c_j`, plus the
> number from `i_{j2}` to `c_j`, plus the number from `c_j` to `o_N`. (Comparator
> `c_j` itself is counted exactly once.)"* — p. 122

> *"… `T` must include a path `q_j` from the lower output lead of `c_j` to
> `o_{N-1}`. The paths `q_j`, `1<=j<=N-1`, together form a binary tree rooted at
> `o_{N-1}`, which we call the MAX2 subnetwork."* — p. 122

> *"… then the two paths from `i_{j1}` and `i_{j2}` through `c_j` to `o_N` and
> `o_{N-1}` together include `nc(C_j) + nc(q_j)` comparators. Therefore,*
> `p(2, T) = max_{1<=j<=N-1} [nc(C_j) + nc(q_j)]`*"* — p. 122, eq (5)

> *"MAX2(T) is a binary tree, so the path lengths `nc(q_j)`, `1<=j<=N-1`,
> satisfy* `sum_{1<=j<=N-1} 2^{-nc(q_j)} = 1`*."* — p. 124, eq (6)

### 2.4 The per-network bound — question (a)/(b), the heart of E1′

> *"Since `p(2, T)` is integral, we conclude that*
> `p(2, T) >= ceil(log2(f(MAX(T))))`*, where* `f(MAX(T)) = sum_{1<=j<=N-1} 2^{+nc(C_j)}`*."*
> — p. 124, eqs (8), (9)

> *"**Given any N-sorter the bound derived for `p(2, T)` depends only upon the
> structure of the subnetwork MAX(T); therefore, we may use (8) and (9) in (1) to
> obtain** `P(2, N) >= min_B ceil(log2(f(B)))`, where `B` ranges over the binary
> trees with `N` leaves. Also, defining `F(N) = min_B f(B)`, we can replace (10)
> with `P(2, N) >= ceil(log2(F(N)))`."* — p. 124, eqs (8)–(12)

This is decisive for the question that was put. The **published statement is the
per-network one**; the minimised form is derived *from* it by one line, and the
chapter says so explicitly. `docs/s13-shape-case-split.md` §2 records E1′ as
*"stronger than the published statement; assumed, unverified"*. That is now
**wrong in our favour**: E1′ *is* the published statement, and E1 is its corollary.

### 2.5 Theorem 1 and Table 1

> *"If we define `f(∅) = lp(∅) = 0`, where `∅` is the binary tree with one leaf,
> then* **Theorem 1**: `f(B) = 2[f(L(B)) + f(R(B)) + 2^{lp(L(B)) + lp(R(B))}]`*."*
> — p. 125, eq (13)

This is **verbatim** the `V` recursion of `docs/s13-shape-case-split.md` §1, with
`lp` = height in comparators. **E2 is confirmed directly against the primary
source, not merely against Dobbelaere's gist.**

`Table 1` (p. 128) prints `F(N)` for `N <= 16`:
`0, 2, 8, 16, 36, 52, 80, 96, 168, 200, 256, 288, 392, 424, 480, 512`.
`tools/verify_huffman2.py` check **A1** regenerates that column exactly from
Theorem 1 by an exact (leaves, height) DP. **`F(13) = 392` is confirmed from the
source.** Check **A5** additionally regenerates the chapter's whole `L(N)` column
`0,1,3,5,9,12,16,19,24,28,33,37,42,46,51,55` from `P(1,N)` and `P(2,N)`.

*Note for the F-audit:* Corollary 1's recurrence (19) (p. 126) replaces
`lp(L(B))` by `ceil(log2 k)`, so **(19) is a relaxation and only an upper bound
on the true minimum**. The verifier deliberately does **not** use (19); it
minimises over genuine shapes. The two happen to agree for `N <= 16`.

---

## 3. PROOF AUDIT — the part that matters most

Reading the proof rather than the statement turned up a problem. Everything in
this section is machine-checked (`tools/verify_huffman2.py`, Parts B, E, F) and
the counterexample is small enough to check by hand.

### 3.1 The counterexample

Take the **3-sorter produced by Batcher's construction**:

```
T = [(0,1), (0,2), (1,2)]          # (a,b): min -> a, max -> b;  o_N = channel 2
```

`|T| = 3 = S(3)`, and it sorts (check **E0**). Trace the largest value:

| entered on | comparators traversed | ends at |
|---|---|---|
| ch 0 | c0, c2 | ch 2 ✓ |
| ch 1 | c0, c2 | ch 2 ✓ |
| ch 2 | **c1**, c2 | ch 2 ✓ |

### 3.2 Gap 1 — the MAX subnetwork has N comparators, not N−1

The union of the three max-paths is `{c0, c1, c2}` — **3 comparators**, but the
chapter asserts `N-1 = 2` (p. 121, quoted in §2.2). `c1 = (0,2)` is a
**pass-through**: the largest value enters and leaves it on the same lead, and no
other max-path reaches its other lead, so it is *on* the MAX subnetwork but is
not a *branch node*. (Check **E1**.) In the full sweep, **27 of 43** constructed
sorters at `n = 3..12` have pass-throughs (Part B).

This is not fatal by itself — the *branch tree* still has N leaves and N−1 nodes
— but it breaks the identification of `nc` with a tree depth, which is what
Theorem 1's proof (eqs (14)–(18), p. 125) silently assumes. See §3.4.

### 3.3 Gap 2 — eq (5) is false, and over-states `p(2,T)`

For the branch node `c_0` the realising pair is `(i_{j1}, i_{j2}) = (ch0, ch1)`:

- max path: `c0, c2`
- second-max path: `c0, c1, c2`
- `nc(c_0) = 0 + 0 + 2 = 2`, `nc(q_0) = 2`  ⇒ eq (5) claims the two paths
  *"together include `nc(C_j) + nc(q_j)` = 4 comparators"*.
- **They actually include 3** — the union is `{c0, c1, c2}` — because the max and
  the second max **meet again** at `c2` after separating at `c0`.

So eq (5) yields `p(2,T) = 4`, while the true `p(2,T) = 3` (brute force over all
ordered pairs; and trivially `p(2,T) <= |T| = 3`). **eq (5) exceeds the quantity
it claims to compute.** (Checks **E2**, **E3**.) In the sweep, eq (5) exceeds the
true `p(2,T)` in **12 of 43** constructed sorters.

### 3.4 Gap 3 — eq (6)'s Kraft equality is false, and can exceed 1

The MAX2 "leaves" for this network are the low outputs of `c_0` and `c_2`, at
depths `nc(q_0) = 2` and `nc(q_2) = 0` (the low output of `c_2` **is** `o_{N-1}`).
Hence

```
sum_j 2^{-nc(q_j)} = 2^{-2} + 2^{0} = 1.25  >  1
```

so MAX2 is **not** a binary tree with `N-1` leaves, and eq (6) fails — in the
direction that **breaks** the proof, because step (7) needs `<= 1`. (Check **E4**.)
Root cause (check **B3**): `q_0` *passes through* the low output lead of `c_2`,
so the sources are not an antichain. In the randomised sweep this happens in
**34 % of 560 sorters** (check **F4**) — it is the common case, not a corner case.

**Even the chapter's own worked example fails eq (6) as an equality.** For
Batcher's 8-sorter (its Fig. 3/4/5) the depths are `nc(q_j) = 4,4,4,4,3,3,2` and

```
sum_j 2^{-nc(q_j)} = 4/16 + 2/8 + 1/4 = 0.75  ≠ 1
```

(check **E8**). There the sum is `< 1`, which is harmless — steps (7)–(8) only
need `<= 1` — so the example does not expose the bug. That is presumably how the
error survived.

### 3.5 Gap 4 — eq (9) literally read contradicts eq (8)

With `nc` computed **as the chapter defines it** (actual comparator counts,
§2.3), our 3-sorter gives `nc(c_0) = 2`, `nc(c_2) = 3`, so
`f = 2^2 + 2^3 = 12` and eq (8) would assert `p(2,T) >= ceil(log2 12) = 4`,
contradicting `p(2,T) = 3`. (Check **E5**.) With `f` computed by **Theorem 1 on
the branch tree**, `f = 8` and eq (8) asserts `p(2,T) >= 3`, which holds with
equality (check **E6**). In the sweep the literal reading is violated by **16 %**
of sorters; the tree reading by **none**.

**Therefore `f` must be read as Theorem 1's recursive function of the branch
tree.** That is the reading `docs/s13-shape-case-split.md` already uses (`V`), so
the case split's arithmetic is untouched — but see §6.2 for a concrete engine
correction that follows.

### 3.6 What survives

`tools/verify_huffman2.py` Parts B/F plus `.build/v3-theory/stress.py` over five
seeds exercise **~5 600 constructed sorting networks** (`n = 3..12`; Batcher,
bubble, odd-even transposition, insertion-extension, random-prefix-plus-thinning,
random channel relabellings). Across all of them:

| statement | violations |
|---|---|
| eq (8) with the **tree** reading of `f` | **0** |
| **(E1′)** `\|T\| >= S(n-2) + ceil(log2 f(MAX(T)))` | **0** |
| MIN dual (§4) | **0** |
| eq (5) over-states the true `p(2,T)` | 12 of the 43 structured sorters (28 %) |
| eq (6) Kraft (`sum 2^-nc(q_j) <= 1`) | ~34 % of the 560 randomised sorters |
| eq (9) literal reading of `f` | ~16 % of the 560 randomised sorters |

Plus (check **A6**) `ceil(log2 F(N)) <= S(N) - S(N-2)` for every `N = 3..12`,
slack `0,0,0,1,0,0,1,2,2,1` — a single violation would have refuted the theorem
outright.

**Honest status of eq (8):** *very probably true, currently unproved.* The two
lemmas it is derived from are false; I do not have a repair. The natural repairs
I tried all lose the Kraft step, and **without the Kraft step the argument gives
only** `p(2,T) >= max_j nc(c_j)`, which at n = 13 is `35 + 7 = 42` — i.e. it does
not reach 44. So the Kraft step carries the entire 44 and the Kraft step is the
broken one.

**This is a research finding about the published record, not about our code.** It
should be treated as such: it is the strongest argument yet for
`xdomain-bound-theory.md` §6.4 item 4 (the "F-audit / rigorous write-up the
programme owes the record"), which is hereby promoted from *"low cost, uncertain
gain"* to **blocking for any claim that rests on the 44**.

---

## 4. The MIN dual — new, fully sourced, immediately usable

The chapter, p. 127, on how it proved `P(2,11) = 9`:

> *"Our bound for `p(2,T)` is derived under the assumption that we prune `T` by
> removing paths followed by the largest two input values to `o_N` and `o_{N-1}`.
> Clearly it works equally well to prune paths followed by the smallest two input
> values to `o_1` and `o_2`. It turns out that if `T` is an 11-sorter such that
> `f(MAX(T)) = F(N) = 256`, then we can prune two paths to `o_1` and `o_2` that
> together include 9 comparators."*

Two consequences.

### 4.1 The dual bound (immediate, checked)

Define `MIN(T)` as the union of the paths followed by the **smallest** value from
each input to `o_1` — a binary tree with `N` leaves rooted at `o_1`, dual in
every respect. Then

> **(D)** `|T| >= S(N-2) + max( ceil(log2 f(MAX(T))), ceil(log2 f(MIN(T))) )`

Check **C1**/**F3**: 0 violations in ~5 600 constructed sorters.

**Consequence for S(13).** A 44-comparator 13-sorter must satisfy **both**
`f(MAX(C)) <= 512` **and** `f(MIN(C)) <= 512`. Both its MAX tree **and** its MIN
tree must lie in the 6 admissible abstract shapes of
`docs/s13-shape-case-split.md` §5. This is a **free doubling** of Filters 1 and 2
of that document's §7 — it costs nothing beyond E1′, which we now have.

### 4.2 The proof template we should be copying

`ceil(log2 F(11)) = ceil(log2 256) = 8`, but van Voorhis proves `P(2,11) = 9`
(check **A4**). He gets the extra unit **exactly** by showing that an 11-sorter
whose MAX tree is minimising is forced into a MIN-side prune of 9. That is the
*only* place in the chapter where the F-bound is beaten, and it is structurally
identical to what S(13) needs:

> **Target (new, highest-value theory item):** show that for a 13-sorter,
> `f(MAX(C)) <= 512` forces `f(MIN(C)) >= 513` (or symmetrically). This proves
> `S(13) >= 45` **with no search at all**, and it is precisely the move van
> Voorhis already made at `N = 11`.

The chapter gives no proof of the `N=11` case (*"It turns out that…"*), so the
mechanism must be reconstructed. Reconstructing it at `N = 11`, where the answer
is known, is a cheap, self-validating first step and I recommend it as the next
theory task. Note one free structural hook: every channel's **first** comparator
lies in `MAX(T) ∩ MIN(T)`, so the two trees are not independent —
`|MAX(T) ∩ MIN(T)| >= ceil(N/2)`.

---

## 5. Huffman2

### 5.1 What Harder's bound actually is (and the closed form)

Harder's Theorem 26 generalizes the **one-channel** theorem: for `X ⊆ B^n` with
prunable channels, `s(X) >= H_{1+max}{ s(X/i) }`, computed by
`max_plus_1_huffman` (sortnetopt `src/huffman.rs`): pop the two smallest `x<=y`,
push `1+max(x,y)`, return the survivor.

**Identity (check D1, exhaustive for `k<=5, b<=6` plus 40 000 random multisets):**

```
max_plus_1_huffman(b_1..b_m)  ==  ceil( log2 sum_i 2^{b_i} )
```

Both equal `min { max_i (b_i + d_i) : d Kraft-feasible }`. So Harder's Huffman
algebra and the Kraft form of van Voorhis's argument are **the same function**,
and Huffman2 can be written in closed form rather than as a greedy run.

### 5.2 Statement and proof

> **Theorem (Huffman2 — the two-channel bound with unequal leaves).**
> Let `T` be an `N`-sorter, `N >= 3`, with MAX branch tree `B` and branch nodes
> `c_1..c_{N-1}`. For each `j`, let `(i_{j1}, i_{j2})` be the pair of input leads
> realising `nc(c_j)`, and let `R_j` be the `(N-2)`-sorter left by pruning the two
> corresponding paths. Let `b_j` be **any** lower bound on `|R_j|`. Then
>
> ```
> |T|  >=  ceil( log2  sum_{j=1}^{N-1} 2^{ b_j + nc(c_j) } )
>       =  H_{1+max} { b_j + nc(c_j) }.
> ```

*Proof.* Pruning at `c_j` removes exactly `nc(c_j) + nc(q_j)` comparators and
leaves `R_j` [eq (5)], so

```
|T| = |R_j| + nc(c_j) + nc(q_j) >= b_j + nc(c_j) + nc(q_j),
```

hence `nc(q_j) <= |T| - b_j - nc(c_j)` for every `j`. By the MAX2 Kraft relation
[eq (6)],

```
1 >= sum_j 2^{-nc(q_j)} >= sum_j 2^{-(|T| - b_j - nc(c_j))}
   = 2^{-|T|} sum_j 2^{b_j + nc(c_j)},
```

and `|T|` is integral. ∎

**Reduction (check D2, verified over all shapes `n <= 11`).** With `b_j ≡ b`
constant the statement collapses to `b + ceil(log2 f(B))`, i.e. exactly
eq (8) + eq (2). So Huffman2 is a strict generalization and reproduces van
Voorhis at equal leaves — the same relationship Harder's Theorem 26 has to the
one-channel theorem.

### 5.3 Status — where it is stuck, precisely

The proof uses **eq (5)** and **eq (6)**, and only those, beyond the exact
decomposition `|T| = |R_j| + (pruned)` — which *is* independently verified
(check **B5**, by path contraction, on every network tested).

**Both eq (5) and eq (6) are refuted (§3.3, §3.4).** Therefore:

> **Huffman2 is proven modulo van Voorhis's two structural lemmas, and no
> further. It is not independently broken: it is exactly as sound as the
> published `S(13) >= 44`.** Repairing eq (5)/(6) repairs both at once.

An **unconditional** but much weaker form does survive, using only the verified
decomposition and `u_j >= nc(c_j)`:

```
|T| >= max_j ( b_j + nc(c_j) )        (unconditional)
```

At the n=13 root with `b_j ≡ 35` this gives `35 + 7 = 42`. It does not reach 44.

### 5.4 At the n = 13 root, Huffman2 gives nothing (check D3)

At the root the residual of every pruned pair is an arbitrary 11-sorter, so the
best available leaf bound is `b_j ≡ S(11) = 35` for all 12 branch nodes —
**uniform**. By §5.2's reduction the value is exactly `35 + ceil(log2 f(B))`,
i.e. **44**, for every admissible shape. **Huffman2 kills no class at the root.**
`docs/research/xdomain-bound-theory.md` §6.4 item 1 anticipated this
(*"At the root with equal leaves it reproduces 44"*); it is now confirmed rather
than expected.

### 5.5 What non-uniformity would be needed (check D4/D5) — the useful part

Write `b_j = 35 + e_j`. Huffman2 forces `S(13) >= 45` iff

```
sum_j 2^{nc(c_j)} (2^{e_j} - 1)  >  512 - f(B).
```

The verifier prints the `nc` multiset of every admissible shape and the exact
threshold. Because `f(B)` is so close to 512 for class C3, the requirement there
is startlingly weak:

| shape | class | `f(B)` | deficit `512-f` | `nc(c_j)` multiset | smallest `nc` for which **one** pair with `b_j >= 36` suffices |
|---|---|---|---|---|---|
| S1 | C1 | 392 | 120 | 3,4,4,4,4,4,4,5,5,5,6,**7** | 7 (the root pair only) |
| S2 | C1 | 392 | 120 | 3,4,4,4,4,4,4,5,5,5,6,**7** | 7 (root pair only) |
| S3 | C1 | 400 | 112 | 4,4,4,4,4,4,4,5,5,5,6,**7** | 7 (root pair only) |
| S4 | C2 | 416 | 96 | 4,4,4,4,4,4,4,4,5,6,6,**7** | 7 (root pair only) |
| S5 | **C3** | 496 | 16 | 3,3,4,4,4,4,**5,5,5,6,7,7** | **5** (6 of the 12 pairs qualify) |
| S6 | **C3** | 512 | **0** | 3,3,4,4,4,5,5,5,5,6,7,7 | **3 — i.e. ANY of the 12 pairs** |

Reading this table:

- **`S6` (the `f = 512` shape, class C3) dies the instant *any single one* of its
  12 pruned pairs is shown to leave an 11-sorter needing 36 comparators.** That
  is the cheapest theory-side kill anywhere in the programme — cheaper than the
  3.2 % tightening `docs/s13-shape-case-split.md` §8 identifies, because it needs
  no tightening of `F` at all, only one structural fact about one residual.
- **`S5` (also C3) dies** if any of its six `nc >= 5` pairs does.
- **C1 and C2 die** only via their unique root pair (`nc = 7`), i.e. the pair
  consisting of the deepest leaf on each side of the root split.
- A **uniform** `+1` would kill everything (check D6) — but it asserts
  `S(11) >= 36`, which is **false** (`S(11) = 35`). So uniformity is exactly what
  cannot be had, and that is the honest obstruction.

**Where it is stuck, in one sentence:** `b_j >= 36` says a *particular* pruned
11-sorter is not size-optimal, and `S(11) = 35` means that cannot be obtained
from `n` alone — it needs the residual's inherited structure, which the current
formulation discards at the moment of pruning.

### 5.6 The form that is actually implementable (partial networks)

The non-uniformity Huffman2 wants exists **inside** a search, not at the root.
In the Track-B/Harder setting the state is a set `X ⊆ B^n`, and the natural
statement is: for a network `C` sorting `X`, with `k_{i,j}` a lower bound on
`s(X / {i,j})`,

```
s(X) >= min over (B, leaf-labelling)  ceil( log2 sum_{c in B} 2^{ k_{pair(c)} + nc_B(c) } )
```

where the min is over binary trees `B` with `n` leaves labelled by channels and
`pair(c)` = (deepest leaf of `L(c)`, deepest leaf of `R(c)`). This is a *sound
relaxation* for any way of evaluating the min. A tractable exact evaluation is a
DP over `(channel subset S, height h, deepest leaf ℓ)` with

```
W(S,h) = min over (S1,h1),(S2,h2), max(h1,h2)=h-1, of
         2 * ( W(S1,h1) + W(S2,h2) + 2^{ k_{pair} + h1 + h2 } )
```

— about `2^13 · 6 · 13 ≈ 6.4 × 10^5` states at n = 13, entirely feasible. **I have
not implemented or validated this**; it is a design, and it inherits the eq (5)/(6)
gap. Flagging it rather than claiming it.

**Practical note for anyone prototyping in sortnetopt** (from
`docs/sortnetopt-internals.md` §2.2): `MAX_CHANNELS = 11`, `AVec<u16>` is
hard-coded to 512 against `MAX_ABSTRACTION_SIZE = 624` at n = 13, and
`OutputSetMap` has hand-written arms only for widths 3..11 with a **silent** miss
otherwise. A Huffman2 prototype at n = 13 will hit all three.

---

## 6. What changes for the 3-class campaign

### 6.1 The good news — E1′ is not an assumption any more

`docs/s13-shape-case-split.md` §3 says:

> *"**The case split needs E1′, which is strictly stronger than E1.** … it is an
> assumption and it carries the entire case split. … Confirming E1′ is the single
> highest-value question to put to the primary source."*

**Answer: E1′ is the chapter's own statement (eq (8)), and E1 is derived from
it.** Also:

- **E2 confirmed at the source** — Theorem 1 (eq 13) is verbatim the `V`
  recursion; `Table 1` gives `F(13) = 392` directly (checks A1, A5).
- **The tree is the max-path tree**, root at the max output, exactly as §3 of the
  case-split document guessed (its two pieces of "partial evidence" were right).
- The `{4,5}` height window that §3 derived independently is correct.
- The "5 classes → 3 classes" correction stands unaffected.

**So the 3-class campaign is on solid ground *as a reduction*: conditional on
eq (8), the three classes are exhaustive.** What is *not* solid is eq (8) itself
(§3), and that was never a case-split-specific risk — it is the risk under the
published 44.

### 6.2 A concrete engine correction (act on this)

`docs/s13-shape-case-split.md` §7 defines the filters using
*"`delta(C,i)` … the number of comparators on the path traced by the single 1 of
the one-hot input `e_i`"* — the **literal** comparator count.

**That is the wrong depth for Filters 1 and 2.** By §3.2/§3.5, `f` is a function
of the **branch tree**, whose depths ignore pass-through comparators. Literal
depth `>=` branch depth, and the two differ in **27 of 43** networks tested. So:

- **Filter 0** (`max_i delta(C,i) <= 5`) is **still sound** with the literal
  count — it comes from the one-channel theorem, where the literal count is
  exactly what gets pruned. Leave it.
- **Filter 1 (leaf-depth profile P1–P4)** and **Filter 2 (shape ∈ S1..S6)** must
  be computed on the **branch tree**: build the tree whose nodes are the
  comparators at which two max-paths *merge*, and take depths there. Using the
  literal `delta` will reject valid networks (unsound as a prune).
- The max-path tracer requested in §7.3 must therefore maintain, per prefix, the
  **merge** structure (a union-find over max-path identities), not just 13
  integers. This is still cheap, but it is a different data structure from the
  one specified.

### 6.3 Free strengthening available today

Apply every filter of §7 **twice** — once to `MAX(C)`, once to `MIN(C)` (§4.1).
Sound under exactly the same hypotheses, no extra theory.

### 6.4 Recommended queue changes

| # | item | why |
|---|---|---|
| 1 | **Repair or refute eq (5)/(6)** — the rigorous re-proof of `p(2,T) >= ceil(log2 f(MAX(T)))` | `S(13) >= 44` currently rests on a proof with a hole; everything else is downstream. Promote `xdomain-bound-theory.md` §6.4 item 4 to **blocking**. |
| 2 | **Reconstruct van Voorhis's `P(2,11) = 9` argument** (§4.2) | self-validating (answer known); it is the *only* known technique for beating `ceil(log2 F(N))`, and it is what S(13) needs. |
| 3 | **MAX/MIN incompatibility at n = 13** (§4.2) | would give `S(13) >= 45` with no search. |
| 4 | **One residual bound `b_j >= 36` for shape S6** (§5.5) | kills half of C3 outright; the weakest sufficient condition anywhere in the programme. |
| 5 | Close the ILL/USER-ACTION items for the Plenum chapter in `xdomain-bound-theory.md` §1.4 and `synthesis-ranked-queue.md` | source is in hand. |
| 6 | Huffman2 partial-network DP (§5.6) | still the right long-term pruning rule, but gated on #1. |

Note that **#1–#4 are all theory tasks costing no compute**, and three of them
did not exist before this reading.

---

## 7. Honest summary of what is and is not proved here

| claim | status |
|---|---|
| E1′ is the chapter's own statement, per-network, un-minimised | **proved** (quoted, §2.4) |
| the tree is the max-path tree with root at the max output | **proved** (quoted, §2.2) |
| `V` = Theorem 1's `f`; `F(13) = 392` | **proved from the source** (checks A1, A5) |
| `f` must be read on the **branch** tree, not via literal `nc` | **proved** (counterexample, check E5/E6) |
| eq (5) is false | **proved** (explicit optimal 3-sorter, check E2/E3) |
| eq (6) is false | **proved** (same network, check E4; and Fig. 4's own example, check E8) |
| eq (8) / E1′ / the MIN dual are *true* | **NOT proved.** 0 counterexamples in ~5 600 constructed sorters and consistent with `S(3..12)`; the published proof does not establish them. |
| Huffman2 (§5.2) | **proved modulo eq (5) + eq (6)** — i.e. exactly as sound as the 44 |
| Huffman2 kills class C3 | **NO.** At the root it reproduces 44 and kills nothing (check D3). |
| Huffman2 kills any class | only given a residual bound `b_j >= 36`, which is not available (§5.5) |
| the MIN dual doubles the case-split filters | **proved conditional on eq (8)**, which is the same condition the case split already needs |

**Nothing in this document produces a candidate network, and no search was run.**
The number 44 appears only as the published bound under audit.

---

## 8. Reproduction

```
python3 tools/verify_huffman2.py          # 36 checks, ~6.2 s, exit 0
python3 tools/verify_huffman2.py --fast   # ~1.7 s, smaller stress sample
python3 tools/verify_huffman2.py --quiet  # verdicts only
```

Pure stdlib, no network, no randomness beyond a fixed seed, no environment
sensitivity. Read-only. Exploratory scratch (larger stress sweeps, five seeds,
~5 040 additional networks) is in `.build/v3-theory/stress.py`; it is not part of
the audit's exit status.

Every network the script touches is **constructed** — Batcher odd-even mergesort,
bubble/insertion, odd-even transposition, insertion-extension, and random
comparator prefixes in front of a bubble network followed by randomised
redundant-comparator removal. No known witness network is embedded anywhere.
