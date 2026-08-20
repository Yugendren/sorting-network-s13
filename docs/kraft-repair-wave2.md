# Kraft Repair, Wave 2: Theorem 6′ Formalized, the Identity, and L4-1 Half-Proved

**Date:** 2026-08-20
**Companion to:** `docs/kraft-repair-wave1.md` (Theorem 6′ and the four attack
lines), `docs/kraft-repair-report.md` (the clean-case proof and the LEMMA★
post-mortem), `docs/kraft-dispute-verdict.md` (the ten failed steelman
defenses). This document does not rewrite any of them; §8 records the
corrections they take.
**Machine check:** `tools/verify_kraft_wave2.py` — **27 checks, 0 failures,
exit 0**, ~5 min (`--fast` ~1 min, `--quiet` for verdicts only,
`--only x1,x4` to select parts). It extends, and does not duplicate,
`tools/verify_kraft_wave1.py`, whose analysis layer it imports.
**Method:** four independent workers plus the lead. Exploratory scratch under
`.build/v3-swarm2/{core.py, overlap, exhaust, adversary, ptrich}`.
**Scope note.** This is a pure-mathematics audit of a 1972 lower-bound proof.
No search for a sorting network was run, no candidate network was produced, and
no comparator count for any specific `n` appears as a target, bound, feature or
stopping condition anywhere in this wave.

---

## 0. VERDICT: **PARTIAL — with one line materially stronger than wave 1**

> **1. AN EXACT IDENTITY REPLACES THE INEQUALITY CHAIN.** For *every*
> `N`-sorter and every branch node `c`,
> ```
> W*(c) = a(c) + eps(c) + gamma(c) + r(c) ,    p(2,T) = max_c W*(c)
> ```
> with `eps, gamma, r >= 0`, `gamma(c)` literally the number of pass-throughs on
> the maximum's stem from `c` to `o_N`. §2. This is unconditional; it is the
> first exact expression for `p(2,T)` in terms of branch-tree data plus named
> non-negative corrections; and it reduces eq (8) to a statement with no
> scenarios in it at all (§2.4).
>
> **2. CONJECTURE L4-1'S FALSIFICATION CRITERION IS PROVED ON THE CLASS WHERE
> THEOREM 6′ LIVES — with margin 0, not the 1 it needs.** On a *tight* sorter
> (`f(B) = 2^{p(2,T)}`) satisfying the two hypotheses Theorem 6′ actually
> consumes, `W*(c) = p(2,T)` at **every** branch node, and the network is rigid:
> `nq(c) = m(c) = p(2,T) - a(c)`, `eps(c) = 0`, `gamma(c) = ov(c)`. **THEOREM
> 7**, §5. So the entire content of L4-1 now sits in a strictly smaller place
> than wave 1 left it, and any counterexample is forced to break one of two
> named steps. That is the wave's headline.
>
> **3. THE HYPOTHESIS OF THEOREM 6′ IS IDENTIFIED EXACTLY, AND WEAKENED.**
> Escape-freeness **is** the local condition "the second maximum never re-meets
> the maximum at a branch node" (**LEMMA W3**, §3.3, proved and machine-checked
> with 0 disagreements). And escape-freeness is consumed only through two
> statements, (C) and (D); **THEOREM 6″** (§4) proves eq (8) from those alone,
> and (C)∧(D) is **strictly wider** — escaping sorters satisfying both exist and
> are exhibited. This is wave 1's prescription item 3, answered.
>
> **4. eq (8) IS PROVED AT THE PASS-THROUGH-RICH END TOO.** `f(B) <= 2^{p(2,T)}
> · sum_c 2^{-gamma(c)}` unconditionally, so eq (8) holds whenever pass-throughs
> are dense on the stems (**THEOREM 8**, §6) — wave 1's prescription item 4.
> Honest caveat: that regime is *slack*, and of little use for size-optimal
> networks. It is recorded because it completes the picture, not because it is
> powerful.
>
> **5. L4-1 IS NOT REFUTED AND NOT PROVED — AND ITS CONFIDENCE GOES *DOWN*, TO
> 15–25 %.** Its falsification criterion was attacked by exhaustive enumeration
> (`n = 4, 5`, both universes, plus inert-augmentation), by construction
> (`n = 6, 8`) and by deterministic multi-seed adversarial search (`n = 6, 7`),
> with all budgets stated in §5.3; it also gained a quantitative localization
> (**LEMMA W2**). But the same work produced the trend: the quantity L4-1 claims
> is bounded by 1 is `0, 0, 0, 1` at `n = 4, 5, 6, 7`. Every constant bound this
> project has tried has been crossed at large enough `n`. **The honest reading
> is that L4-1 is probably false at some larger `n`.** §9.2.
>
> **6. eq (8) ITSELF REMAINS NEITHER PROVED NOR REFUTED IN GENERAL.** The proved
> floor is unchanged by this wave. Nothing here touches the published lower
> bound under audit, which remains a conjecture.
>
> **7. RECOMMENDATION: SHIP, DO NOT CONTINUE.** §§2–6 are publishable audit
> mathematics and should go into the audit paper as they stand. The remaining
> gap is not narrowing at a rate that justifies further waves: wave 1 widened the
> proved class from *clean* to *escape-free*, wave 2 widened it again by 0.55 %
> and added the pass-through-rich end, and the open zone (§7.7) is still roughly
> half of every corpus measured. The one live conjecture, L4-1, ends this wave
> **less** credible than it began it. Effort should return to the compute track.
> §9.4 records the single target worth naming if anyone ever comes back.

---

## 1. Vocabulary

Unchanged from `docs/kraft-repair-report.md` §1–§2 and
`docs/kraft-repair-wave1.md` §1; restated here only so this document is
self-contained.

Fix an `N`-sorter `T = (c_1, …, c_M)`, comparator `c_i = (a_i, b_i)` with
`a_i < b_i`, minimum to `a_i`. Outputs ascend, so `o_N` is channel `N-1` and
`o_{N-1}` is channel `N-2`. A **lead** is a wire segment: a channel between two
consecutive comparators on it, including the input and output segments.

In the **one-hot max scenario at `x`**, input `x` carries a value strictly larger
than all others; its **max-path** is the comparator sequence it traverses,
always exiting high. A lead is **red** if some one-hot max scenario puts the
maximum on it, **blue** otherwise.

* **(R1)** every low-output lead is blue;
* **(R2)** a high-output lead is red iff its comparator has a red input lead;
* **(R3)** a traversed comparator is a **branch node** iff both input leads are
  red, and a **pass-through** iff exactly one is.

The **MAX branch tree** `B` has the `N` input channels as leaves and the `N-1`
branch nodes as internal nodes. For a branch node `c`, `L(c)` and `R(c)` are its
subtrees, `lp_B(·)` the height, `depth_B(c)` the depth from the root, and
```
a(c) = lp_B(L(c)) + lp_B(R(c)) + depth_B(c) + 1 ,      f(B) = sum_c 2^{a(c)} .
```

In the **pair scenario `(x,y)`** the maximum enters at `x`, the second maximum
at `y`, all other inputs smaller; `W(x,y)` is the set of comparators traversed by
either, and `p(2,T) = max_{x != y} |W(x,y)|`. Chapter eq (2), machine-verified
by path contraction, gives `|T| >= S(N-2) + p(2,T)`; **eq (8)** is the claim
`p(2,T) >= ceil(log2 f(B))`.

---

## 2. The exact identity

### 2.1 Three facts, all general

> **FACT 1 (first meeting).** The maximum and the second maximum first meet at
> `c = LCA_B(x,y)`.

*Proof.* Until they meet, the second maximum exceeds everything it can encounter,
so it exits high everywhere — it follows `y`'s max-path, while the maximum
follows `x`'s. Two max-paths first share a comparator at their branch-tree LCA. ∎

> **FACT 2 (state determinacy).** Immediately after `c` the maximum occupies
> `hi(c)` and the second maximum `lo(c)`, and from there the trajectories of both
> are determined by the network and by the pair of occupied leads alone —
> independently of `x`, `y`, and of the other `N-2` values. Hence
> ```
> g(c)  = comparators the maximum traverses from c to o_N inclusive
> nq(c) = comparators the second maximum traverses strictly after c
> ov(c) = those of them the maximum also traverses      r(c) = nq(c) - ov(c)
> ```
> are functions of `c` alone.

*Proof.* The maximum exits high at every comparator whatever the other input is.
The second maximum exceeds every value but the maximum, so it exits high unless
the maximum is on the other input lead, in which case it exits low; either way
its motion is a function of the two occupied leads. Induct on comparator
index. ∎

> **FACT 3 (exact decomposition).** With `c = LCA_B(x,y)` and `e(z,c)` the number
> of comparators strictly between input `z` and `c` on `z`'s max-path,
> ```
> |W(x,y)| = e(x,c) + e(y,c) + g(c) + r(c) .
> ```

*Proof.* By Fact 1 the two pre-meeting paths are the `e(x,c)` and `e(y,c)`
comparators before `c` on the two max-paths; they are disjoint because `c` is the
first shared comparator, and all have index `< c`. From `c` onward the union has
`1 + (g(c)-1) + nq(c) - ov(c)` elements. Add. ∎

This is the correction of chapter eq (5), which double-counts `ov(c)`.

### 2.2 The identity

Write `W*(c) = max{ |W(x,y)| : LCA_B(x,y) = c }`. In Fact 3 the two inputs range
independently over `leaves(L(c))` and `leaves(R(c))`, so with
`E_S(c) = max_{z in leaves(S)} e(z,c)`,
```
W*(c) = E_L(c) + E_R(c) + g(c) + r(c) ,
```
and since every ordered pair meets at some branch node,
`p(2,T) = max_c W*(c)`.

> **LEMMA W1 (the identity).** For every `N`-sorter `T` and every branch node `c`,
> ```
> W*(c) = a(c) + eps(c) + gamma(c) + r(c)
> ```
> where
> ```
> eps(c)   = (E_L(c) - lp_B(L(c))) + (E_R(c) - lp_B(R(c)))   >= 0
> gamma(c) = g(c) - depth_B(c) - 1                            >= 0
> r(c)     = nq(c) - ov(c)                                    >= 0
> ```
> and `gamma(c)` is **exactly** the number of pass-throughs on the maximum's stem
> from `c` to `o_N`. Consequently
> ```
> p(2,T) = max_c [ a(c) + eps(c) + gamma(c) + r(c) ] .
> ```

*Proof.* Substitute the definitions into `W*(c) = E_L + E_R + g + r`; the
identity is then arithmetic. For the signs: let `z` be a leaf of `L(c)` at
distance `k` below `L(c)` in `B`. The branch nodes strictly between `z` and `c`
on `z`'s max-path are exactly `z`'s `B`-ancestors that lie strictly below `c` —
namely `L(c)` and the `k-1` nodes between it and `z` — so `e(z,c) >= k`, actual
comparator counts being at least branch-node counts. Taking `z` a deepest leaf
of `L(c)` gives `E_L(c) >= lp_B(L(c))`, and likewise on the right, so
`eps(c) >= 0`. The
maximum's stem from `c` to `o_N` consists of `g(c)` comparators, every one of
them traversed by a max-path; those among them that are branch nodes are exactly
`c` and the `depth_B(c)` ancestors of `c` in `B` (a branch node on `x`'s
max-path is by definition an ancestor of the leaf `x`), and by (R3) every other
comparator on the stem is a pass-through. So the stem carries exactly
`g(c) - depth_B(c) - 1 = gamma(c) >= 0` pass-throughs. Finally `ov(c) <= nq(c)`
by definition. ∎

Write `m(c) := W*(c) - a(c) = eps(c) + gamma(c) + r(c) >= 0` and
`d(c) := p(2,T) - a(c) >= m(c) >= 0`.

**Machine check X1c/X1d:** the identity, the three sign conditions and
`p(2,T) = max_c W*(c)` hold with **0 failures** on the wave-2 audit corpus
(exhaustive `n = 4` in both universes, `n = 5` minimal to the stated cap,
constructed families to `n = 11`, inert-augmented families, random `n = 6,7`).

### 2.3 What the identity buys immediately

> **THEOREM 8 (upper bounds on `f(B)`).** For every `N`-sorter,
> ```
> f(B) = sum_c 2^{W*(c) - m(c)} <= 2^{p(2,T)} * sum_c 2^{-m(c)}
>                               <= 2^{p(2,T)} * sum_c 2^{-gamma(c)}
> ```
> and likewise with `r(c)` or `eps(c)` in place of `gamma(c)`.

The middle expression is LEMMA★, which is false in general; the outer ones are
the weakest and therefore the safest. §6 develops the `gamma` branch — it is the
one whose ingredients are computable from the MAX subnetwork alone, with no pair
scenarios.

### 2.4 eq (8) restated with the scenarios removed

Substituting `p(2,T) = max_c [a(c)+eps(c)+gamma(c)+r(c)]` into eq (8):

> **eq (8)** `<=>` `sum_c 2^{a(c)} <= 2^{ max_c [ a(c) + eps(c) + gamma(c) + r(c) ] }`.

So the theorem is entirely a statement about a binary tree `B` decorated with
three non-negative integer functions `eps, gamma, r`. It is **false** for
arbitrary decorations — set `eps = gamma = r = 0` and any `B` with two or more
internal nodes refutes it. Therefore **the whole content of eq (8) is a
realizability constraint**: which decorated trees `(B, eps, gamma, r)` arise from
an actual sorter. That is a cleaner target than anything wave 1 left, and it is
recommended in §9 as the shape of any future attempt.

---

## 3. THEOREM 6′, formalized

Wave 1 proved this; the point of this section is a clean, self-contained,
audit-ready statement with the corrected Lemma B, a modular proof that separates
the two places the hypothesis is spent, and a local characterization of the
hypothesis itself.

### 3.1 The hypothesis

> **Definition (escape-free).** `T` is **escape-free** if for every ordered pair
> `(x,y)` the second maximum occupies no red lead at or after the low output of
> the meeting comparator `c = LCA_B(x,y)`.

`lo(c)` is blue by (R1), so including or excluding the meeting lead is
immaterial (wave 1 checked zero sensitivity over the full `n = 5` universe).
Clean `⟹` escape-free, strictly (wave 1 §1.3): Batcher's 12-sorter has a
pass-through, so Theorem 6 of `docs/kraft-repair-report.md` does not cover it,
while Theorem 6′ does.

### 3.2 The two statements the hypothesis is spent on

> **(C) the Kraft step.** `sum_c 2^{-nq(c)} <= 1`.
> **(D) the per-node step.** `gamma(c) >= ov(c)` for every branch node `c`.

Everything else in the chain is general (Facts 1–3, Lemma W1). Isolating them is
what makes §4 possible.

### 3.3 Escape-freeness is a local condition

> **LEMMA W3.** `T` is escape-free **if and only if** the second maximum never
> re-meets the maximum at a **branch node**; equivalently, iff every re-meeting
> comparator is a pass-through.

*Proof.* (`⟸`, contrapositive) Suppose the second maximum occupies a red lead at
some point after the meeting. From a red lead `l` it enters a comparator `e`. If
`e`'s other input lead is blue then the maximum is not there (the maximum
occupies only red leads), so the second maximum wins and exits on `e`'s high
output, which is red by (R2). If `e`'s other input is red and the maximum is not
there, again the second maximum wins and exits red. So **the second maximum can
leave the red set only by losing a comparison, and it loses only to the
maximum** — i.e. only at a re-meeting, at a comparator both of whose inputs are
then red, which by (R3) is a **branch node**. But the second maximum must finish
on the output lead of channel `N-2`, which is blue (the maximum finishes on
channel `N-1`). So it does leave the red set, hence it re-meets the maximum at a
branch node.
(`⟹`) If a re-meeting occurs at a branch node `e`, then `e` has two red inputs
and the second maximum arrives on one of them, so it was on a red lead — an
escape. ∎

**Machine check X2f: 0 disagreements** between the two predicates over the audit
corpus. This is a strict sharpening of wave 1's definition: the hypothesis of
Theorem 6′ is a *local* statement about re-meetings, not a global statement about
lead colours.

### 3.4 The lemmas

> **LEMMA A (deterministic exit).** Let `T` be escape-free, let the second
> maximum sit after the meeting on a blue lead `l`, and let `e` be the next
> comparator on `l`'s channel. If `e`'s other input lead is red the second
> maximum exits on `e`'s **low** output; if that other input is blue, on `e`'s
> **high** output.

*Proof.* Suppose the other input is red. Then `e`'s high output is red by (R2).
The second maximum exceeds every value but the maximum; if the maximum were not
on that other input, the second maximum would win and exit high onto a red lead
— an escape, excluded. So the maximum is there and the second maximum exits low.
Now suppose the other input is blue. The maximum occupies only red leads, so it
is not there; the second maximum beats whatever is and exits high. ∎

> **COROLLARY A′.** Post-meeting motion is a function `succ` **of the lead
> alone**, independent of the scenario, and its value is always blue (by (R1) for
> a low output, by (R2) for the high output of a comparator with two blue
> inputs).

This is exactly where escape-freeness is spent, and it is not available in
general: in an arbitrary sorter the lead-level successor is **not** a function
(wave 1 §2.3; re-derived at wave-1 check **W3e**).

> **LEMMA B (antichain), corrected one-line form.** In an escape-free `T` the
> second maximum traverses **no branch node at all** after the meeting; in
> particular the `N-1` sources `l_c` (the low output leads of the branch nodes)
> are pairwise non-ancestral under `succ`.

*Proof.* By Lemma A the second maximum sits on a blue lead and enters a
comparator `e`. If `e`'s other input is red then `e` has **exactly one** red
input — the second maximum's own lead is blue — so by (R3) `e` is not a branch
node. If the other input is blue, `e` has no red input, so again not a branch
node. Since `l_{c'}` is produced by the branch node `c'`, no `l_{c'}` is ever
reached. ∎

*Note (kept from wave 1, because it is the kind of error this project exists to
catch).* An earlier drafting justified the red case by "the low output of a
comparator having a red input, which by (R3) is not a branch node", which is
**false as written** — a branch node does have red inputs. The corrected form
above is what is proved and what is machine-checked (**X2a**, wave 1 **W2b**).

> **LEMMA C (Kraft) ⟹ (C).** `succ` strictly increases the comparator index, so
> it is acyclic, and every lead has at most two `succ`-preimages (the two input
> leads of the comparator producing it). The leads visited after a meeting
> therefore form a **binary in-tree** rooted at `o_{N-1}`, in which `l_c` sits at
> depth `nq(c)`. With Lemma B the `l_c` are an antichain, so Kraft's inequality
> gives `sum_c 2^{-nq(c)} <= 1`. ∎

> **LEMMA D ⟸ LEMMA W3, hence ⟸ escape-freeness ⟹ (D).** If every re-meeting
> comparator is a pass-through then `gamma(c) >= ov(c)`.

*Proof.* Each of the `ov(c)` re-meeting comparators lies on the maximum's stem
from `c` to `o_N` and is distinct from `c`; by hypothesis each is a
pass-through; and by Lemma W1 the stem carries exactly `gamma(c)`
pass-throughs. ∎

This is the step that **pays for the re-meeting**: pass-throughs inflate the
literal stem by exactly enough to cover `ov(c)`. It is why escape-freeness does
not need to imply `ov(c) = 0`, and indeed it does not (wave 1 **W2g**).

> **LEMMA E.** Under (D), `p(2,T) >= W*(c) >= a(c) + nq(c)` for every `c`.

*Proof.* `W*(c) = a + eps + gamma + r >= a + gamma + r >= a + ov + r = a + nq`
by Lemma W1 and (D). ∎

### 3.5 The theorem

> **THEOREM 6′.** For every **escape-free** `N`-sorter `T`,
> ```
> 1 >= sum_c 2^{-nq(c)} >= sum_c 2^{-(p(2,T) - a(c))} = 2^{-p(2,T)} f(B) ,
> ```
> hence `p(2,T) >= ceil(log2 f(B))` and `|T| >= S(N-2) + ceil(log2 f(B))`. ∎

The first inequality is Lemma C, the second Lemma E. Both are strict
consequences of escape-freeness *only through* (C) and (D) — which is the whole
point of §4.

**Machine checks X2a–X2e:** (C), (D0), (D) and eq (8) hold with **0 failures**
on every escape-free sorter of the audit corpus; out of class (C) and (D0) fail
in large numbers, so the hypothesis is load-bearing and not decorative; and
eq (8) itself never failed anywhere, in class or out — the theorem is untouched,
only the proof is class-restricted.

---

## 4. THEOREM 6″ — weakening the hypothesis (wave 1, prescription item 3)

> **THEOREM 6″.** If an `N`-sorter satisfies **(C)** and **(D)**, then eq (8)
> holds: `p(2,T) >= ceil(log2 f(B))`.

*Proof.* Verbatim §3.5, which uses escape-freeness nowhere else. ∎

Wave 1's prescription observed that among escaping `n = 4` sorters the Kraft step
and the per-node step "fail on largely different networks, and only the
conjunction is needed". Theorem 6″ is that observation turned into a theorem.
The remaining question is empirical: how much wider is `(C) ∧ (D)`?

**Machine check X3a/X3b.** Over the verifier's 32 043-sorter audit corpus,
`(C) ∧ (D)` holds on 7 214 against 7 167 escape-free — **47 sorters escape yet
satisfy both** — and eq (8) holds on every one of the 7 214, with 0 failures.
The smallest witnesses are 9-comparator `n = 5` sorters with 2 pass-throughs,
`p(2,T) = 6`, `f(B) = 36`, `lb = 6`, `sum_c 2^{-nq(c)} = 0.9375`; the verifier
prints them. §7.3 gives the exhaustive `n = 5` count.

**Honest assessment of the size of the gain.** The widening is real but *small*
in the corpora measured — of order one per cent of the escape-free class, not a
multiple of it (§7). Theorem 6″'s value is therefore mostly structural: it names
the two steps, and it tells any future attempt that it needs to re-establish
exactly those two and nothing else.

---

## 5. Conjecture L4-1 (wave 1, prescription item 2 — the highest-value item)

Recall the conjecture and its exact falsification criterion (wave 1 §5):

> **CONJECTURE L4-1.** `sum_c 2^{a(c) - min(W*(c)+1, p(2,T))} <= 1`.
> **Falsification criterion.** A sorter with `f(B) = 2^{p(2,T)}` (**tight**) and
> some branch node with `W*(c) <= p(2,T) - 2`.

In the notation of §2 the criterion is: a tight sorter with `d(c) - m(c) >= 2` at
some branch node. Note `d(c) >= m(c)` always, since `p(2,T) >= W*(c)`.

### 5.1 THEOREM 7 — the criterion is proved on the Theorem-6″ class

> **THEOREM 7.** Let `T` be **tight** (`f(B) = 2^{p(2,T)}`) and satisfy **(C)**
> and **(D)**. Then at **every** branch node `c`
> ```
> nq(c) = m(c) = d(c) = p(2,T) - a(c) ,   W*(c) = p(2,T) ,
> eps(c) = 0 ,   gamma(c) = ov(c) ,   and   sum_c 2^{-nq(c)} = 1 .
> ```

*Proof.* Tightness says `sum_c 2^{-d(c)} = 2^{-p(2,T)} f(B) = 1`. Lemma E (which
needs only (D)) says `d(c) >= nq(c)`, so `2^{-nq(c)} >= 2^{-d(c)}` termwise, and
therefore
```
1 = sum_c 2^{-d(c)} <= sum_c 2^{-nq(c)} <= 1
```
the last step by (C). Both inequalities are equalities, and because the first was
termwise, `nq(c) = d(c)` at every `c`. Now `m(c) = eps + gamma + r >= gamma + r
>= ov + r = nq = d` by (D), while `m(c) <= d(c)` always; so `m(c) = d(c)`, which
forces `eps(c) = 0` and `gamma(c) = ov(c)`, and `W*(c) = a(c) + m(c) = a(c) +
d(c) = p(2,T)`. ∎

> **COROLLARY 7a.** On the class of Theorem 6″ — in particular on every
> **escape-free** sorter — L4-1's falsification criterion holds with margin
> **0**: `p(2,T) - W*(c) = 0`, not merely `<= 1`. Contrapositively, **every**
> tight sorter with `p(2,T) > W*(c)` at some branch node must fail (C) or fail
> (D), and hence must escape.

This is a strictly stronger statement than wave 1 needed, on a class wave 1 had
already proved eq (8) for; and it is consistent with wave 1 §3.1, whose tight
7-sorter with non-constant `W* = {6,7,7,7,7,7}` must therefore escape — a sharp
prediction, machine-confirmed (**X5c**).

Theorem 7 also explains the "`>= 1` is real but `>= 2` is never seen" asymmetry
wave 1 flagged: on a tight sorter the excess `d(c) - m(c)` is exactly the amount
by which the network fails (C) or (D) at `c`, and those failures are what escapes
buy.

### 5.2 LEMMA W2 — a quantitative localization of any counterexample

> **LEMMA W2.** Let `T` be tight. Then
> **(i)** `sum_c 2^{-m(c)} >= 1` (this is wave 1 §3.1's structural closure of
> per-node charging, restated);
> **(ii)** the multiset `{d(c)}` is the leaf-depth multiset of a *full* binary
> tree with `N-1` leaves, so `sum_c 2^{-d(c)} = 1` and `0 <= d(c) <= N-2`;
> **(iii)** for every branch node `c0`,
> ```
> sum_c 2^{-m(c)} >= 1 + (2^{d(c0)-m(c0)} - 1) * 2^{-d(c0)} .
> ```
> Consequently **any counterexample to L4-1's falsification criterion forces**
> ```
> LEMMA-star sum  =  sum_c 2^{-m(c)}  >=  1 + 3 * 2^{-d(c0)}  >=  1 + 3 * 2^{-(N-2)} .
> ```

*Proof.* (ii) is Kraft's converse plus the fact that a full binary tree with `L`
leaves has height at most `L-1`. (iii): `sum_c 2^{-m(c)} = sum_c 2^{-d(c)}
2^{d(c)-m(c)} >= sum_c 2^{-d(c)} + (2^{d(c0)-m(c0)}-1) 2^{-d(c0)}`, using
`d >= m` termwise and (ii). (i) is (iii) with `c0` arbitrary. The consequence is
`d(c0)-m(c0) >= 2`, so `2^{d-m}-1 >= 3`, and `d(c0) <= N-2`. ∎

This converts the hunt for a counterexample into the measurement of a single
number. The thresholds are

| `N` | 5 | 6 | 7 | 8 | 9 | 13 |
|---|---|---|---|---|---|---|
| `1 + 3·2^{-(N-2)}` | 1.375 | 1.1875 | 1.09375 | 1.046875 | 1.0234375 | 1.0014648 |

against wave 1's *measured* LEMMA★ search maxima 17/16 = 1.0625 (`n=6`),
9/8 = 1.125 (`n=7`), 73/64 = 1.140625 (`n=8`). At `n = 6` the measured maximum is
**below** the threshold and at `n = 7` it is **above** it, which localizes the
first possible counterexample and tells the refuter where to spend budget. The
maxima quoted are search maxima, not proven suprema; §7 records what exhaustive
enumeration says.

**Machine checks X4a–X4f:** across the audit corpus's 2 667 tight sorters,
Lemma W2(i)–(iii) hold with 0 violations, and on the 282 of them satisfying
(C)∧(D) Theorem 7 holds with 0 violations **including the full rigidity**
`nq = m = d`, `eps = 0`, `gamma = ov` at every branch node of every one.

### 5.3 The refutation attempt

Two independent refuters, one enumerative and one adversarial, plus the
verifier's own hunt. **Budgets are stated in full**, as wave 1 §6 item 4
demands; every network was constructed or enumerated by code.

**Exhaustive enumeration.** Scratch: `.build/v3-swarm2/exhaust/`.

| universe | sorters | tight | gap distribution over tight | `max star` over tight | Lemma W2 threshold |
|---|---|---|---|---|---|
| `n=4` minimal, exhaustive | 708 | 12 | `{0: 12}` | 1.000000 | 1.75 |
| `n=4` inert-allowed, exhaustive | 840 | 12 | `{0: 12}` | 1.000000 | 1.75 |
| `n=4` inert-allowed to 7 comparators | 12 240 | 12 | `{0: 12}` | 1.000000 | 1.75 |
| `n=4` inert-allowed to 8 comparators | 115 560 | 12 | `{0: 12}` | 1.000000 | 1.75 |
| `n=5` minimal, **exhaustive** | 149 040 | 13 080 | `{0: 13080}` | 1.000000 | 1.375 |
| `n=5` + 1 inert insertion (all positions) | 721 520 | 9 216 | `{0: 9216}` | 1.000000 | 1.375 |
| `n=5` + 2 inert insertions (seed 20260817) | 50 000 | 101 | `{0: 101}` | 1.000000 | 1.375 |
| `n=5` + 3 inert insertions (seed 20260818) | 50 000 | 16 | `{0: 16}` | 1.000000 | 1.375 |

`max star` over tight sorters is exactly `1.000000` in every row, and by Lemma
W2 that is *equivalent* to `gap ≡ 0`; it is recorded separately because it is the
quantity the threshold column is comparable with. **At `n = 4` and `n = 5` the
falsification criterion is definitively not met**, in the inert-allowed universe
as well as the minimal one — which matters, because wave 1 §6 item 3 showed the
minimal universe systematically deletes pass-through-rich networks.

**The criterion holds far outside the class where Theorem 7 proves it.** Of the
13 080 tight `n = 5` sorters, only 1 200 are escape-free (equivalently, satisfy
(C)∧(D)); the other **11 880 fail both (C) and (D)** — and every one of them
still has `gap = 0`. Theorem 7 explains 9 % of the phenomenon; 91 % is
unexplained.

**Adversarial search.** Scratch: `.build/v3-swarm2/adversary/`. Four
structurally different score functions (`soft` = `100·f/2^{p2} + min(gap,5)`;
`star_tight`; `gap_pen`; `hard_gate`), seeds `101…108` (8 seeds), per-seed bests
recorded so the luck-dependence is visible rather than hidden by a maximum.

| `n` | steps × restarts | evaluations | best `gap` on a tight sorter | `Sstar(n)` on tight | threshold `1+3·2^{-(n-2)}` |
|---|---|---|---|---|---|
| 6 | 2500 × 6 | 300 051 | 0 | 1.000000 | 1.1875 |
| 7 | 2500 × 6 | 245 921 | **1** | 1.062500 | 1.09375 |
| 8 | 1500 × 5 | 144 063 | — *(no tight sorter reached)* | — | 1.046875 |
| 9 | 600 × 3 | 38 465 | — *(no tight sorter reached)* | — | 1.0234375 |

> **THE HONEST LIMIT OF UNGUIDED SEARCH.** At `n = 8` and `n = 9` the hunt did
> not reach **a single tight network**, across 308 573 evaluations and four score
> functions. So those rows are **not** evidence of non-refutation; they are
> evidence that hill-climbing cannot find the search region at all. Wave 1's
> "274 000 evaluations searching for this configuration" should be read with the
> same caution. What fixes this is *construction*, below.

At `n = 7` the hunt does reach a tight sorter with `gap = 1` — the configuration
wave 1 §3.1 exhibits — so the adversary is validated on a known positive
(**X5a**), and that witness fails both (C) and (D), exactly as **Corollary 7a**
requires (**X5b**). The verifier's own shipped hunt (8 seeds × 3 restarts × 1200
steps over `n = 6,7`) reaches `gap = 1` and no further (**X5c**).

**Constructive attack — this is what reaches `n = 8`.** Fix a branch-tree shape
whose `f` is a power of two; realise it as a *clean tournament prefix* (which
provably fixes `B`, hence `a(c)` and `f(B)`, since tail comparators are never on
a max-path — verified, 40/40 random tail mutations left `a(c)` and `f(B)`
unchanged and kept the network clean); then hill-climb **on the tail only**,
driving `f/2^{p2}` to 1 while trying to keep `W*(c0)` low at a chosen node `c0`
with a large `a`-deficit. The baselines have exactly the configuration one wants
— e.g. the `n = 6` baseline has `d(c0) - m(c0) = 2` at `c0` — but they are *not
tight* (`p(2,T) = 8` against `lb = 6`), and:

| `n` | tail-hunt budget | tight networks reached | best `gap` over them | best `gap` at `c0` |
|---|---|---|---|---|
| 6 | 6 seeds × 10 restarts × 4000 steps, 239 939 evals | **53 262** | 0 | 0 |
| 7 | 6 seeds × 10 restarts × 4000 steps, 239 906 evals | 0 | — | — |
| 8 | 6 seeds × 8 restarts × 2000 steps, 95 955 evals | **25 070** | 0 | 0 |
| 9 | 6 seeds × 6 restarts × 1000 steps, 35 975 evals | 0 | — | — |

Plus a stage-3 sweep (adding a comparator among `c0`'s sibling leaves so that
`a(c0)` is preserved): 69 000 attempts across `n = 6,7,9`, `a(c0)` preserved in
all of them, **0 tight**, 0 positive gaps.

So **78 332 tight networks at `n = 6` and `n = 8` were reached constructively,
every one with `gap = 0`**, which materially repairs the `n >= 8` hole in the
unguided search. **Caveat, and it is not small:** each row explores a *single*
branch-tree shape (one tournament prefix per `n`), so this is deep coverage of a
narrow slice, not broad coverage. The structural obstruction encountered is the
one Theorem 7 names: the baseline *does* have a node with `d - m = 2`, but it is far from
tight, and every tail edit that drives `f/2^{p2}` to 1 also raises `m(c0)`.

**Pass-through-rich `n = 6, 7` families contain no tight networks at all.**
17 408 constructed inert-augmented 6- and 7-sorters spanning pass-through counts
0–21 (`.build/v3-swarm2/exhaust/cache/e4_n67_construction.json`) yielded **zero**
tight networks. Combined with §7.5's finding that tightness *rises* with
pass-through count at `n = 5`, this says the relationship is not monotone in `n`
and should not be extrapolated.

**Grand total.** Across the whole wave, `989 516` networks were examined by the
enumerative refuter alone, of which `22 437` were tight; adding the constructive
families gives well over `100 000` tight networks examined. **`max gap = 1`,
attained only at `n = 7`; `gap = 2` never observed.**

**Verdict on item 1: NOT REFUTED, NOT PROVED.** Proved on the (C)∧(D) class
with margin 0 (Theorem 7); exhaustively verified at `n = 4, 5` including
pass-through-rich universes; adversarially verified at `n = 6, 7`; **unexplored
at `n >= 8`.**

---

## 6. THEOREM 8 — the pass-through-rich end (wave 1, prescription item 4)

Wave 1 §2.1's surgery post-mortem established that pass-throughs are the padding
that lets `B` stay unbalanced without paying for it in `p(2,T)`, and asked for
the contrapositive: bound `f(B)` **above** using the pass-through count and
`p(2,T)`. Lemma W1 delivers it in one line.

> **THEOREM 8.** For every `N`-sorter,
> `f(B) <= 2^{p(2,T)} · sum_c 2^{-gamma(c)}`, where `gamma(c)` is the number of
> pass-throughs on the maximum's stem from `c` to `o_N`.
> **COROLLARY 8a.** If `sum_c 2^{-gamma(c)} <= 1` then eq (8) holds.
> **COROLLARY 8b.** If `min_c gamma(c) >= log2(N-1)` then eq (8) holds.
> **COROLLARY 8c.** If the root's stem carries at least one pass-through and
> every edge of `B` carries at least two, then eq (8) holds.

*Proof.* `f(B) = sum_c 2^{a(c)} = sum_c 2^{W*(c)-m(c)} <= 2^{p(2,T)} sum_c
2^{-m(c)} <= 2^{p(2,T)} sum_c 2^{-gamma(c)}`, using `m >= gamma >= 0`. 8b:
`sum_c 2^{-gamma(c)} <= (N-1) 2^{-min gamma}`. 8c: `gamma(c) >= gamma(root) +
2·depth_B(c)`, and there are at most `2^k` internal nodes at depth `k`, so
`sum_c 2^{-gamma(c)} <= 2^{-gamma(root)} sum_k 2^k 4^{-k} = 2^{1-gamma(root)}`. ∎

Unlike (C) and (D), the hypothesis of Corollary 8a is computable from the **MAX
subnetwork alone** — no pair scenarios enter — which makes it the most
structural of the sufficient conditions in this project.

**Non-vacuity, and the honest caveat.** The class is non-empty and is **not**
contained in escape-free: appending `k = ceil(log2(N-1))` copies of the
comparator `(N-2, N-1)` to any sorter is inert (every reachable vector is already
sorted there), so it preserves sorting; each copy is traversed by the maximum and
has a blue other input, hence is a pass-through on the stem of *every* branch
node; so `f(B)` is unchanged and `gamma(c)` rises by `k` everywhere, forcing
Corollary 8b. Applied to escaping bases this produces escaping sorters that
Corollary 8a covers and Theorem 6′ cannot (**X6a–X6d**, thousands of instances).

**But**: padding raises `p(2,T)` while leaving `f(B)` fixed, so the sorters
Corollary 8a reaches are exactly the ones with large slack `p(2,T) - lb` — the
witnesses the verifier prints have `p(2,T) = 7` against `lb = 5`. **For the
size-optimal networks that matter to the `S(13)` question this corollary is of
little use.** It is recorded because it completes the picture — eq (8) is now
provable at *both* ends of the pass-through spectrum, and the open zone is the
middle — not because it is powerful. Anyone quoting it should quote this
paragraph too.

---

## 7. MEASURED FACTS

Scratch: `.build/v3-swarm2/{overlap, exhaust, adversary, ptrich}`; every number
below comes from a script left in place, and the load-bearing ones are
re-derived by `tools/verify_kraft_wave2.py`.

### 7.1 The identity is not an artefact

`152 003` sorters audited (exhaustive `n = 4` in both universes, **exhaustive**
`n = 5` minimal, constructed `n = 3..11`, random `n = 6..9`): **0** violations of
Lemma W1, **0** sign violations, **0** violations of either Theorem 8 bound, and
**0** networks on which Fact 2 failed to apply. Independently re-derived by the
verifier on its own corpus (**X1c–X1e**).

### 7.2 Class sizes

| corpus | total | clean | escape-free | (C) | (D) | **(C)∧(D)** | escaping |
|---|---|---|---|---|---|---|---|
| `n=4` minimal, exhaustive | 708 | 132 | 144 | 288 | 180 | 144 | 564 |
| `n=4` inert-allowed, exhaustive | 840 | 162 | 276 | 420 | 312 | 276 | 564 |
| `n=5` minimal, **exhaustive** | 149 040 | 27 540 | 32 850 | 83 610 | 35 400 | **33 030** | 116 190 |
| `n=5` inert-augmented (500, seed 20260817) | 500 | 9 | 112 | 346 | 286 | 227 | 388 |
| `n=6` random, npt-stratified | 1 218 | 150 | 154 | 571 | 186 | 164 | 1 064 |
| `n=7` random, npt-stratified | 1 442 | 150 | 152 | 797 | 199 | 171 | 1 290 |
| `n=8` random, npt-stratified | 1 700 | 150 | 154 | 1 049 | 191 | 176 | 1 546 |

**eq (8) failed on 0 networks in every corpus and every class.**

### 7.3 The overlap — how much Theorem 6″ actually buys

Restricted to **escaping** networks, the `(C) × (D)` contingency table:

| corpus | C1 D1 (**the gain**) | C1 D0 | C0 D1 | C0 D0 |
|---|---|---|---|---|
| `n=4` minimal | **0** | 144 | 36 | 384 |
| `n=4` inert-allowed | **0** | 144 | 36 | 384 |
| `n=5` minimal, exhaustive | **180** | 50 580 | 2 370 | 63 060 |
| `n=5` inert-augmented | **115** | 119 | 59 | 95 |
| `n=6` random | **10** | 407 | 22 | 625 |
| `n=7` random | **19** | 626 | 28 | 617 |
| `n=8` random | **22** | 873 | 15 | 636 |

All 346 overlap witnesses satisfy eq (8) — 0 violations, as Theorem 6″ requires.

So the widening is **real but small**: at `n = 5` it is `33 030` against `32 850`
escape-free, **+0.55 %**; and at `n = 4` it is **empty in both universes** —
there, (C) and (D) are *completely disjoint* on escaping networks. The
pass-through-rich `n = 5` corpus is where it bites hardest (115 of 388 escaping
networks). Anyone tempted to describe Theorem 6″ as a large generalisation
should read this table first.

### 7.4 Four candidate weakenings of escape-freeness, all dead

Tested as *sufficient* conditions for (C)∧(D) over the corpora of §7.2:

| candidate predicate | networks on which it holds among escaping | verdict |
|---|---|---|
| every escape stays on the maximum's own stem | **0**, every corpus | never true |
| no escape at a branch node (wave 1's `nobr`) | **0**, every corpus | never true |
| every re-meeting comparator is a pass-through | **0**, every corpus | never true |
| at most one escaping ordered pair | **0**, every corpus | never true |
| at most two escaping ordered pairs | 46 050 / 116 190 at `n=5` | necessary at `n=5`, fails at `n>=6` |

The first three are **explained, not merely measured**: by **LEMMA W3** each of
them is *equivalent* to escape-freeness, so of course none of them holds on an
escaping network. This is a useful negative: the three most natural
"slightly-weaker-than-escape-free" hypotheses are not weaker at all, they are the
same hypothesis. The overlap class of §7.3 is therefore characterised by
something genuinely weaker than any of them — on those 180 `n = 5` witnesses
escapes do leave the maximum's stem and re-meetings do occur at branch nodes,
yet Lemma D's *inequality* `gamma(c) >= ov(c)` survives for an unrelated reason.
**No simple characterising predicate was found.**

### 7.5 Tightness

| corpus | tight | tight ∧ escape-free | tight ∧ (C)∧(D) | `gap != 0` | `max star` |
|---|---|---|---|---|---|
| `n=4` minimal | 12 | 12 | 12 | 0 | 1.0 |
| `n=4` inert-allowed | 12 | 12 | 12 | 0 | 1.0 |
| `n=5` minimal, exhaustive | 13 080 | 1 200 | 1 200 | 0 | 1.0 |
| `n=5` inert-augmented | 2 | 0 | 0 | 0 | 1.0 |
| `n=6` random | 4 | 2 | 2 | 0 | 1.0 |
| `n=7`, `n=8` random | 0 | 0 | 0 | — | — |

Two facts worth recording:

* **Tightness is *positively* correlated with pass-throughs**, not negatively as
  one might guess from the padding mechanism. Over the exhaustive `n = 5`
  universe the tight fraction by pass-through count is
  `0 pt: 1200/27540 = 4.4 %`, `1 pt: 3000/55320 = 5.4 %`,
  `2 pt: 5160/41790 = 12.3 %`, `3 pt: 3720/24390 = 15.3 %`.
* **`max star` over tight sorters is `1.000000` in every corpus that contains a
  tight sorter at all**, which by Lemma W2 is exactly the statement `gap ≡ 0`.
  The only `gap = 1` witness found anywhere in this wave required targeted
  adversarial search at `n = 7`.

### 7.6 The pass-through-rich end

Corollary 8a's hypothesis is satisfiable at every `n` tested by end-padding
(**X6a–X6c**: 6 819 constructed instances, 5 871 of them escaping, 0 eq (8)
failures). The sharper Corollary 8c is satisfiable by *comparator duplication*
— repeating every comparator `k >= 3` times, each repeat being inert and hence a
pass-through (**X6d–X6e**: 36 instances at `n = 4..9`, 18 escaping, 16 failing
(C) or (D), 0 eq (8) failures). So the pass-through-rich theorems do reach
sorters that **both** Theorem 6′ and Theorem 6″ miss.

**And they are of little practical use**, for the reason §6 records: padding
raises `p(2,T)` and leaves `f(B)` alone, so these sorters carry large slack. The
escaping Corollary-8c witness the verifier prints has `p(2,T) = 15` against
`lb = 4`.

### 7.7 Coverage: what fraction of sorters does eq (8) now have a proof for?

Over 153 011 networks (`.build/v3-swarm2/ptrich/`), which condition fires:

| sufficient condition | count | fraction | kind |
|---|---|---|---|
| clean | 27 986 | 0.183 | structural |
| escape-free (= Theorem 6′) | 34 057 | 0.223 | structural |
| Theorem 8′/8c hypothesis | 536 | 0.0035 | structural |
| **structural union** | **34 265** | **0.224** | |
| (C)∧(D) (= Theorem 6″) | 34 255 | 0.224 | computed |
| `sum_c 2^{-gamma(c)} <= 1` (Cor. 8a) | 850 | 0.0056 | computed |
| `sum_c 2^{-r(c)} <= 1` (Cor. 8b) | 77 047 | 0.503 | computed |
| LEMMA★ `<= 1` | 153 011 | **1.000** | computed |

Two honesty notes, both load-bearing:

1. **The distinction between *structural* and *computed* conditions must not be
   blurred.** "Escape-free" and the Theorem 8 hypotheses are properties one can
   state and check about the network's shape. `(C)`, `(D)`, `Gsum <= 1`,
   `Rsum <= 1` and LEMMA★ are numbers one computes per network; a per-network
   computation is not a theorem.
2. **The 1.000 for LEMMA★ is a corpus artefact, not a result.** Wave 1 refuted
   LEMMA★ (`33/32` at `n = 6`, re-derived at wave-1 check **W4a**) by *targeted
   adversarial* search. The corpus here is natural, random, constructed and
   padded, and simply never wanders into the failure region. Excluding LEMMA★,
   the computed union is 0.504 and **49.6 % of the corpus has no proof of
   eq (8) by any route in this project.**

**The uncovered zone is intermediate in pass-through count**, at every `n`
tested. Fraction of networks with *no* covering condition, against pass-through
count (excerpt; full table in `.build/v3-swarm2/ptrich/out/p3_p4_census.log`):

```
n=4:  npt=0: 0.00   1: 0.32   2: 0.99   3: 0.92   >=13: 0.00
n=5:  npt=0: 0.00   1: 0.35   2: 0.73   3: 1.00   >=13: 0.00
n=7:  npt=0: 0.00   3: 0.37   5: 0.84   7: 0.55   >=13: 0.00
n=9:  npt=0: 0.00   4: 0.59   7: 0.83   9-12: 0.71 >=13: 0.00-0.08
```

A clean rise-then-fall at every `n`: eq (8) is provable at the pass-through-poor
end (clean / escape-free) and again at the pass-through-rich end (Theorem 8),
and the open problem lives strictly in between. That is the single most useful
picture this wave produces, and it is exactly the picture wave 1 could not see,
because wave 1 had no theorem at the rich end.

---

## 8. CORRECTIONS TO THE RECORD

1. **`docs/kraft-repair-wave1.md` §1's definition of escape-freeness** should be
   accompanied by its local form, **LEMMA W3** (§3.3): escape-freeness *is* "the
   second maximum never re-meets the maximum at a branch node". The two
   predicates are equivalent, proved and machine-checked. Lemma D is then
   immediate rather than argued.
2. **`docs/kraft-repair-wave1.md` §1's Theorem 6′** is superseded in scope by
   **THEOREM 6″** (§4): the proof uses escape-freeness only through (C) and (D),
   and (C)∧(D) is strictly wider. Wave 1's status table row "Lemmas A–E;
   THEOREM 6′" should read "… ; THEOREM 6′, generalised to Theorem 6″
   (`docs/kraft-repair-wave2.md` §4)".
3. **`docs/kraft-repair-wave1.md` §5's confidence statement for L4-1** should be
   updated: the conjecture's falsification criterion is now **proved** on the
   escape-free / Theorem-6″ class with margin 0 (Theorem 7), and any
   counterexample is confined by Lemma W2 to networks whose LEMMA★ sum exceeds
   `1 + 3·2^{-(N-2)}`. The revised confidence is recorded in §9.
4. **`docs/kraft-repair-report.md` §8's status row** "eq (8) for **clean**
   `N`-sorters" should read "for sorters satisfying (C) and (D) (Theorem 6″,
   `docs/kraft-repair-wave2.md` §4)", which subsumes both the clean case and
   Theorem 6′.
5. **`docs/kraft-repair-wave1.md` §8 item 3 mis-states one count.** It says that
   among escaping `n = 4` sorters "144/564 still satisfy the Kraft step and
   120/564 still satisfy the per-node step". The 144 is correct. **The 120 is
   wrong: the machine-checked figure is 36/564** (cross-checked two ways, via
   this wave's layer and via wave 1's own `lemma_report()['D']`, with 0
   mismatches over all 708 `n = 4` minimal sorters). The qualitative claim is
   not merely correct but *understated*: at `n = 4`, in **both** universes, (C)
   and (D) are **completely disjoint** on escaping sorters, so the conjunction
   buys nothing at all there. It first buys something at `n = 5` (§7.3).
6. The enumerator flaw recorded in wave 1 §6 item 3 (both `enumerate_sorters`
   implementations skip *inert* comparators, which **are** pass-throughs) is
   repaired constructively here: `tools/verify_kraft_wave2.py` supplies
   `inert_insertions`, `inert_augment` and `append_inert`, which generate
   pass-through-rich sorters from any base while provably preserving sorting.

---

## 9. HONEST STATUS

### 9.1 The table

| claim | status |
|---|---|
| **LEMMA W1** — `W*(c) = a(c)+eps(c)+gamma(c)+r(c)`, all three `>= 0`; `p(2,T) = max_c W*(c)` | **PROVED**; 0 violations over 152 003 sorters + the verifier's own 32 043 |
| **LEMMA W3** — escape-free `<=>` no re-meeting at a branch node | **PROVED**; 0 disagreements over 32 043 sorters |
| **THEOREM 6′** — escape-free `⟹` eq (8) | **PROVED** (wave 1); re-proved here modularly, with the two consumption points isolated |
| **THEOREM 6″** — (C)∧(D) `⟹` eq (8) | **PROVED**; strictly wider, but only by **+0.55 %** at `n = 5` and by **nothing at all** at `n = 4` |
| **THEOREM 7** — tight + (C)∧(D) `⟹` `W*(c) = p(2,T)` everywhere, with full rigidity | **PROVED**; 0 violations |
| **COROLLARY 7a** — L4-1's falsification criterion, margin **0**, on the Theorem-6″ class | **PROVED** |
| **LEMMA W2** — the excess bound and `d(c) <= N-2` on tight sorters | **PROVED**; 0 violations |
| **THEOREM 8, Corollaries 8a–8c** — the pass-through-rich end | **PROVED**; non-vacuous, with escaping witnesses; **low practical value** (§6) |
| eq (8) restated without scenarios (§2.4) | **PROVED** — a reformulation, not a result |
| **L4-1's falsification criterion in general** | **NOT PROVED, NOT REFUTED.** Exhaustive at `n = 4, 5` (both universes, plus inert-augmentation); constructive at `n = 6, 8`; adversarial at `n = 6, 7`; `max gap = 1`, first seen at `n = 7`, `gap = 2` never |
| **CONJECTURE L4-1** | still a **CONJECTURE**; confidence **revised DOWNWARD**, §9.2 |
| **eq (8) in general** | **NOT proved, NOT refuted.** The proved floor is unchanged by this wave |
| the published lower bound under audit | still a **conjecture**; nothing here touches it |

### 9.2 L4-1: confidence revised **downward**, to 15–25 %

Wave 1 recorded 25–35 %. This wave produced *both* a proof of the criterion on
the escape-free class and a large body of non-refutation — and it also produced
the reason to be **less** confident, which is the trend:

| `n` | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|
| best `max_c (p(2,T) - W*(c))` over tight sorters | 0 | 0 | 0 | **1** | 0 | — |
| how it was searched | exhaustive | exhaustive | 53 262 tight nets (one shape) + 300 k evals | 246 k evals | 25 070 tight nets (one shape) | none reached |

(The `n = 8` entry is a `0` only within a single branch-tree shape; unguided
search reached no tight `n = 8` network at all. Read the row as "no evidence
either way at `n >= 8`".)

`gap` is 0 for every `n <= 6` we can reach and becomes 1 at `n = 7`. **L4-1 is
exactly the assertion that this quantity is bounded by the constant 1.** Wave 1
§4's own warning — "the suprema rise with `n`; do not build on a constant
bound" — applies to `gap` with full force, and every other constant bound tried
in this project (LEMMA★'s `1`, eq (6)'s `1.25`) has been crossed once a large
enough `n` was reached. The "+1" remains, as wave 1 said, a fitted constant with
no structural motivation; Theorem 7 explains why `gap = 0` on the escape-free
class but says nothing about why `2` should be unreachable off it.

**Against L4-1:** the `0,0,0,1` trend; the absence of any mechanism capping the
constant; the fact that Theorem 7's proof gives margin 0 and therefore cannot be
"stretched by one" to cover the escaping case — it simply stops.
**For L4-1:** the criterion now holds on a proved class rather than by luck;
`gap = 1` was reached only by targeted `n = 7` search and never doubled despite
~100 000 tight networks; and Lemma W2 shows a counterexample must simultaneously
be tight and push the LEMMA★ sum above `1 + 3·2^{-(N-2)}`, a genuinely
constrained configuration.

The honest reading is: **L4-1 is probably false at some larger `n`, and is
unlikely to be provable.** It should not be the subject of further work.

### 9.3 What is publishable, and what is not

**Publishable in the audit paper, as proved mathematics:** Lemma W1 and the
scenario-free restatement of eq (8) (§2); Lemma W3 (§3.3); Theorem 6′ in the
clean formalization of §3, which supersedes the clean-case Theorem 6; Theorem 6″
(§4); Theorem 7 and Lemma W2 (§5.1–5.2); Theorem 8 with its honest caveat (§6);
and the coverage picture of §7.7, which is the first statement in this project of
*where* the open problem lives.

**Not publishable as anything but a measurement:** every "survived adversarial
search" claim, including this wave's. §5.3 states the budgets; the `n >= 8` rows
of the unguided hunt are worthless and are labelled as such.

### 9.4 If anyone ever returns to this

Do not retry anything in wave 1 §3.2, and do not retry L4-1. The one target
worth naming is **§2.4's realizability reframing**: eq (8) is now known to be
equivalent to a statement about a binary tree decorated with three non-negative
integer functions `(eps, gamma, r)`, false for arbitrary decorations, so *all*
of its content is which decorations a sorter can realise. Two concrete
sub-questions fall straight out and are finite-flavoured:

1. Which multisets `{(a(c), eps(c), gamma(c), r(c))}` are realisable? In
   particular, is there a realisability constraint linking small `a(c)` (a
   shallow node with small subtrees) to large `r(c)` (a long private journey for
   the second maximum)? That is the exact shape of the missing lemma.
2. The constructive tail-search method of §5.3 reaches tight networks at `n = 6`
   and `n = 8` where hill-climbing reaches none. Pointed at `n = 9, 10, 11` with
   shapes chosen so that `f` is a power of two and one node has a large
   `a`-deficit, it is the only search that stands a real chance of producing a
   `gap = 2` witness — i.e. of *refuting* L4-1, which on the evidence above is
   the likelier outcome.

---

## 10. REPRODUCTION

```
python3 tools/verify_kraft_wave2.py            # full
python3 tools/verify_kraft_wave2.py --fast     # reduced budget
python3 tools/verify_kraft_wave2.py --quiet    # verdicts only
python3 tools/verify_kraft_wave2.py --only x4  # one part
python3 tools/verify_kraft_wave1.py            # the predecessor, unchanged
python3 tools/verify_huffman2.py               # its predecessor, unchanged
python3 tools/verify_kraft_dispute.py          # the independent verifier, unchanged
```

Deterministic (fixed seeds, multi-seed hunts), stdlib only, read-only. Every
network is **constructed** — Batcher, bubble, odd-even transposition,
insertion-extension, random comparator prefixes thinned to a sorter, and
inert-comparator augmentation — or **brute-force enumerated**. The only literal
comparator lists in the verifier are counterexamples, which it re-derives and
re-verifies from scratch; **no known witness network is embedded anywhere**.
