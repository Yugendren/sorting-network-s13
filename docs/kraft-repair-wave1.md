# Kraft Repair, Wave 1: the Escape-Free Theorem, and Four Attack Lines Resolved

**Date:** 2026-08-20
**Companion to:** `docs/kraft-repair-report.md` (the clean-case proof and the
LEMMA★ post-mortem) and `docs/kraft-dispute-verdict.md` (the ten failed steelman
defenses). This document does not rewrite either; §6 records the corrections
they take.
**Machine check:** `tools/verify_kraft_wave1.py` — 26 checks, ~2 min, exit 0
(`--fast` ~20 s, `--quiet` for verdicts only). It extends, and does not
duplicate, `tools/verify_huffman2.py`, whose primitives it imports.
**Method:** five independent workers — four attack lines plus a dedicated
refuter whose only mandate was to destroy the strongest candidate. Exploratory
scratch under `.build/v3-swarm/{core.py, adversary.py, lead, line1..line5}`.

---

## 0. VERDICT: **PARTIAL**

> **1. THE PROVED CASE OF eq (8) IS WIDENED, FROM *CLEAN* TO *ESCAPE-FREE*.**
> `T` is **escape-free** if, for every ordered pair `(x,y)`, the second maximum
> occupies no **red** lead after its first meeting with the maximum.
> Clean ⟹ escape-free, strictly. **THEOREM 6′: every escape-free `N`-sorter
> satisfies eq (8)** — §1, proved, with the proof audited line-by-line by a
> dedicated refuter who failed to break it. Batcher's **12-sorter** has a
> pass-through, so Theorem 6 does *not* cover it; Theorem 6′ does.
>
> **2. THE OBSTRUCTION IS RE-IDENTIFIED. It is ESCAPES, not pass-throughs.**
> `docs/kraft-repair-report.md` §3.1 says "pass-throughs are the sole
> obstruction". That is now too coarse: pass-throughs are *harmless on their
> own*. What breaks the argument is the second maximum **escaping onto a red
> lead**, which a pass-through *permits* but does not *force*. This is the main
> conceptual gain of the wave, and it is what made Theorem 6′ findable.
>
> **3. THREE OF THE FOUR LINES ARE DEAD, each with explicit counterexamples**
> — global surgery (§2.1), direct information-theoretic counting (§2.2), and
> fractional/flow Kraft (§2.3). None of the three should be retried in the forms
> described. Each nevertheless yielded a durable structural object (§4).
>
> **4. PER-NODE CHARGING IS NOW CLOSED *STRUCTURALLY*, not by a lone
> counterexample.** On any network with `f(B) = 2^{p(2,T)}` the identity
> `sum_c 2^{a(c)-p(2,T)} = 1` holds **exactly**; hence any per-node exponent
> `X(c) <= p(2,T)` yields `sum_c 2^{a(c)-X(c)} >= 1`, with equality **iff
> `X(c) = p(2,T)` at every branch node**. Tight sorters with non-constant
> `W*(c)` exist. So no certificate built from a node's own pruning can ever
> work — LEMMA★ was not unlucky, it was impossible. §3.1.
>
> **5. ONE CANDIDATE SURVIVED EVERYTHING** (`L4-1`, §5), with a one-line
> falsification criterion. It is **NOT PROVED** and is recorded as a conjecture
> with explicit confidence, in the format the LEMMA★ post-mortem demands.
>
> **6. eq (8) ITSELF REMAINS NEITHER PROVED NOR REFUTED IN GENERAL.** It
> survived every attack in this wave, including direct adversarial maximisation
> that reaches exact tightness and stops. The proved floor is unchanged.

---

## 1. THEOREM 6′ — eq (8) for escape-free sorters

Vocabulary is `docs/kraft-repair-report.md` §1–§2 throughout: leads; **red**
lead (some one-hot max scenario puts the maximum on it) and **blue** otherwise;
(R1) every low output is blue; (R2) a high output is red iff the comparator has
a red input; (R3) a comparator is a branch node iff **both** inputs are red, and
a traversed comparator with exactly **one** red input is a **pass-through**.
For a branch node `c`: `a(c) = lp_B(L(c)) + lp_B(R(c)) + depth_B(c) + 1`;
`f(B) = sum_c 2^{a(c)}`; `e(x,c)` = **actual** comparator count strictly between
input `x` and `c` on `x`'s max-path; `g(c)` = **actual** comparator count from
`c` to `o_N` inclusive; `nq(c)` = comparators the second max traverses after the
meeting; `ov(c)` = those of them the max also traverses (re-meetings).

> **Definition (escape-free).** `T` is **escape-free** if for **every**
> admissible ordered pair `(x,y)`, the second maximum occupies no red lead at or
> after the low output of the meeting comparator `c = LCA_B(x,y)`.

Note `lo(c)` is blue by (R1), so including or excluding the meeting lead itself
is immaterial (checked: zero sensitivity over the full `n = 5` universe).
Lemma 1 of `docs/kraft-repair-report.md` is exactly the statement *clean ⟹
escape-free*; §1.3 below shows the converse fails.

### 1.1 The lemmas

> **LEMMA A (deterministic exit).** Let the second max sit, after the meeting,
> on a blue lead `ℓ`, and let `e` be the next comparator on `ℓ`'s channel. If
> `e`'s **other** input lead is red, the second max exits on `e`'s **low**
> output; if that other input is blue, on `e`'s **high** output.

*Proof.* Suppose `e`'s other input is red. Then `e`'s high output is red by
(R2). The second max exceeds every value except the max; so if the max were
**not** on that other input, the second max would win and exit high — onto a red
lead, an escape, excluded by hypothesis. Hence the max **is** there, and the
second max exits low. Now suppose `e`'s other input is blue. In scenario
`(x,y)` the max's leads are exactly the red leads of `x`'s one-hot max-path
(the max's trajectory is independent of all other values, and it always takes
the high output), so the max is not on a blue lead; the second max therefore
beats whatever is there and exits high. ∎

> **Corollary A′.** `succ` — the second max's post-meeting motion — is a
> **function of the lead alone**, independent of the scenario; and its value is
> always **blue** ((R1) for a low output, (R2) for the high output of a
> comparator with two blue inputs).

This is the exact point where escape-freeness is spent, and it is *not*
available in general: in an arbitrary sorter the lead-level successor is **not**
a function (§2.3, and check **W3e** re-derives a minimal witness).

> **LEMMA B (antichain).** In an escape-free `T` the `N-1` sources `ℓ_c` (the
> low output leads of the branch nodes) are pairwise non-ancestral under `succ`.

*Proof.* By Lemma A the second max, sitting on a blue lead, enters a comparator
`e` whose other input is red or blue. If red, `e` has **exactly one** red input
(the second max's own lead is blue), so by (R3) `e` is **not** a branch node.
If blue, `e` has no red input, so again not a branch node. Either way **the
second max post-meeting never traverses a branch node at all**; in particular it
never emerges on `ℓ_{c'}` for any branch node `c'`. ∎

*Note.* An earlier drafting of this lemma justified the red case by "the low
output of a comparator having a red input, which by (R3) is not a branch node" —
which is **false as written**, since a branch node has red inputs. The refuter
caught it. The corrected form above (*exactly one* red input; equivalently, the
one-line statement that no branch node is traversed post-meeting) is what is
proved and what is machine-checked (**W2b**).

> **LEMMA C (Kraft).** `succ` is acyclic (the comparator index strictly
> increases) and every lead has at most two `succ`-preimages (the two input
> leads of the comparator that produces it), so the leads visited after a meeting
> form a **binary in-tree** rooted at `o_{N-1}`, in which `ℓ_c` sits at depth
> `nq(c)`. With Lemma B, `sum_c 2^{-nq(c)} <= 1`.

> **LEMMA D (re-meetings are stem pass-throughs).** If the two values meet again
> at `e` after `c`, then `e` lies on the max's stem from `c` to `o_N`; the second
> max enters `e` on a blue lead, so `e` has exactly one red input, so by (R3) `e`
> is a **pass-through**, not a branch node. The stem carries exactly
> `depth_B(c)+1` branch nodes (namely `c` and its ancestors in `B`), and the
> `ov(c)` re-meeting comparators are distinct from all of them. Hence
> ```
> g(c)  >=  depth_B(c) + 1 + ov(c).
> ```

This is the step that **pays for the re-meeting**: pass-throughs inflate the
literal stem by exactly enough to cover `ov(c)`. It is why escape-freeness does
**not** need to imply `ov(c) = 0` — and indeed it does not (§1.3).

> **LEMMA E.** For every branch node `c`, choosing `x, y` to attain `lp_B(L(c))`
> and `lp_B(R(c))`,
> ```
> p(2,T) >= |W(x,y)| = e(x,c) + e(y,c) + g(c) + nq(c) - ov(c)
>                   >= lp_B(L) + lp_B(R) + depth_B(c) + 1 + ov(c) + nq(c) - ov(c)
>                    = a(c) + nq(c).
> ```

The middle equality is Fact 2 of `docs/kraft-repair-report.md` §1 (exact, no
off-by-one); `e(x,c) >= lp_B(L(c))` because actual comparator counts include
pass-throughs, which branch-tree depths do not; and `g(c)` is bounded below by
Lemma D.

> **THEOREM 6′.** For every **escape-free** `N`-sorter `T`,
> ```
> 1 >= sum_c 2^{-nq(c)} >= sum_c 2^{-(p(2,T) - a(c))} = 2^{-p(2,T)} f(B),
> ```
> hence `p(2,T) >= ceil(log2 f(B))`, and `|T| >= S(N-2) + ceil(log2 f(B))`. ∎

### 1.2 Machine check

`tools/verify_kraft_wave1.py` Part **W2**, over **4 019** escape-free sorters
(exhaustive `n = 4`; exhaustive `n = 5` up to the minimal-universe cap;
constructed Batcher/bubble/OET/insertion families to `n = 11`; random
prefix-plus-thinning at `n = 6,7`) and **17 189** out-of-class controls:

| lemma | in-class failures | out-of-class failures |
|---|---|---|
| Corollary A′ (`succ` is a function) + Lemma B | **0** | 17 189 |
| no branch node traversed post-meeting (**W2b**) | **0** | — |
| Lemma C (`sum 2^{-nq} <= 1`), max observed **1.000000** | **0** | 9 860 |
| Lemma D (`g >= depth_B + 1 + ov`) | **0** | — |
| Lemma E (`p2 >= a(c) + nq(c)`) | **0** | — |
| **eq (8)** | **0** | **0** |

The hypothesis is **load-bearing, not decorative**: every lemma fails, often
universally, outside the class. And eq (8) itself never failed *anywhere* —
in class or out — which is the point: **the theorem is untouched; only the proof
is class-restricted.**

The refuter's independent from-scratch implementation (importing none of this
project's code) reached the same conclusion, additionally verifying: Fact 1
(`meet = LCA_B`) on 32 884 networks; that both escape-freeness predicates agree
on 4 185 networks with zero disagreements; that Lemma D's margin is **tight**
(max `depth_B+1+ov-g = 0`, never positive); and that in-class stress witnesses
reach 36 pass-throughs with `sum ov = 221` while satisfying everything.

### 1.3 The class boundary — three facts that keep the theorem honest

- **Escape-free is strictly larger than clean** (**W3a–c**). The margin is
  **universe-dependent**, and it is only fair to say so:

  | universe (`n = 4`) | sorters | clean | escape-free | ratio |
  |---|---|---|---|---|
  | minimal (no inert comparator, no sorting proper prefix) | 708 | 132 | 144 | 1.09 |
  | inert-allowed (only: no sorting proper prefix) | 840 | 162 | 276 | 1.70 |

  Exhaustive `n = 5`, minimal universe: **149 040** sorters, **27 540** clean,
  **32 850** escape-free — **5 310 networks strictly gained** (+19 %).
- **Batcher's 12-sorter is the headline witness** (**W3d**): 42 comparators,
  exactly **one pass-through**, so **not clean** and outside Theorem 6 — but it
  **is** escape-free, with `f(B) = 288 = F(12)`, `lb = 9`, `p(2,T) = 10`.
  Theorem 6′ covers a canonical, structured, optimal-`f` network that Theorem 6
  cannot.
- **Escape-free does NOT imply `ov(c) = 0`** (**W2g**), so Lemma D is genuinely
  load-bearing and the theorem is not a disguised restatement of Corollary 2 of
  the clean-case proof. In-class networks carry pass-throughs.

---

## 2. THE FOUR LINES

### 2.1 Global / extremal surgery — **DEAD**

Minimal-counterexample induction under three well-orderings (`(|T|, #pt)`,
`(#pt, |T|)`, and `(#escaping nodes, |T|)`) requires a surgery at a pass-through
that reduces the measure, does not increase `p(2,T)`, and does not decrease
`f(B)`. Every family tried — delete, substitute, move, insert, append,
delete-and-rebuild, adjacent-swap, relabel — fails, and **condition (iii),
`f(B)` must not decrease, is the one that fails systematically**.

The mechanism, which is the transferable insight: **pass-throughs are the
padding that lets the MAX branch tree stay unbalanced without paying for it in
`p(2,T)`.** Remove one, the max-paths re-route, and `B` rebalances *toward* the
`f`-minimising shape — `f` drops (`24 → 16` at `n = 4`, `64 → 40` at `n = 5`)
while `p(2,T)` holds. The modal single-edit outcome is `Δp2 = +1`,
`Δlog2 f = 0`: exactly backwards.

Decisive experiment: among **tight** (`f = 2^{p2}`) `n = 5` sorters with a
pass-through, **28 %** are **rigid** under `(#pt, |T|)` and **42 %** under the
escape measure — *every* measure-reducing neighbour strictly worsens the ratio.
An explicit rigid, size-optimal witness:
`R = [(0,1),(0,2),(1,3),(1,4),(0,1),(2,3),(2,4),(1,2),(3,4)]` (`n = 5`,
`f = 64`, `lb = p2 = 6`, tight); its 10 pass-through-reducing neighbours have
ratios topping out at `0.625`, a deficit of 0.68 bits. Bounded-loss relaxations
also fail (best `Δlog2 f − Δp2` reaches `−2.0`; 17/576 networks have **no**
measure-reducing neighbour at all).

Also established, and worth recording because it is easy to assume otherwise:
**inserting a comparator into a sorting network does not preserve sorting**
(1 362 exhaustive counterexamples at `n = 3,4`).

### 2.2 Direct information-theoretic counting — **DEAD**

The correct object is the **pair-state merge DAG** (states `(channel of max,
channel of second max)`, every fibre of size `<= 2`), which supports a genuine
potential/Kraft argument: for any antichain `A` of source states,
`2^{p(2,T)} >= sum_{s in A} 2^{Wmax(s) - b_A(s)}`. Instantiated at all pairs
this gives `2^{p(2,T)} >= sum_{(x,y)} 2^{φ(x,y)}`, **strictly stronger than
naive pair counting** (which is the `φ ≡ 0` case), and on Batcher's 8-sorter it
is exact. Instantiated at the branch-node states it re-derives the clean case.

It cannot reach the general case. The framework's optimum over antichains is
degenerate — `(V₁+V₂)/2 <= max(V₁,V₂)` forces the supremum to be attained by a
*single* source, i.e. `2^{p(2,T)}`, circularly — so all content lies in the only
expressible lower bound `Wmax(s_c) >= a(c) + r(c)`, which forces the full
branch-node source set, which is refuted. Minimal witness: an **optimal**
5-sorter, `[(0,1),(3,4),(0,4),(1,2),(1,3),(2,4),(0,1),(2,3),(1,2)]`, one
pass-through, eq (8) **tight** (`f = 36`, `lb = p2 = 6`); the second max re-meets
the max at the root, so the root source must be dropped from the antichain,
losing `2^a = 16` of the 36 and yielding only `p >= 5`.

**Why pair counting loses exactly `2^{depth(c)}` — the exact answer** (proved
for clean `T`, `<=` in general):
```
sum_{(x,y)} 2^{-|W(x,y)|}  =  sum_c 2^{-(depth_B(c) + r(c))}
```
while eq (8) needs `sum_c 2^{-r(c)} <= 1`. The subtree mass
`sum_{x in L_c} 2^{-δ(x)} = 2^{-depth(c)-1}` **independently of balance**, so the
loss is *not* a balance artefact: after meeting at `c` the max still climbs
through `depth_B(c)` branch nodes, at each of which both input leads are red and
the fibre genuinely has two occupied preimages. Those are the same comparators
for every pair meeting at `c`, but scenario-counting pays for them once per
pair. The clean proof escapes only by conditioning on the max's route, which
fragments the source set into one root-path at a time — precisely the known-short
`p >= lp(B) + log2(N-1)` bound.

**What `f(B)` counts** (machine-checked): with `h(·)` the subtree height,
`f(B) = sum_c 2^{depth(c)} · P̂(c)` where `P̂(c)` is the number of ordered leaf
pairs whose LCA is `c` in the **perfect completion** of `B`; equivalently
`f = 2^{h_L+h_R+1} + 2(f(L)+f(R))`. So `f` is the ordered-leaf-pair count of the
completed tree weighted by `2^{depth of LCA}`, whereas pair counting delivers the
*unweighted* count `N(N-1)`. The entire gap between them is the weight
`2^{depth(LCA)}`.

### 2.3 Fractional / weighted Kraft via flow — **DEAD**

**The formulation is ill-posed on leads.** The lead-level successor map is
**not a function** in general — minimal witness (exhaustively minimal at
`n = 4`, re-derived at check **W3e**):
```
N4 = [(0,1), (2,3), (0,2), (1,2), (1,3), (2,3)]
```
From lead 9 the second max goes low in one scenario and high in another,
according to whether the max is present. Found independently, with the *same*
minimal witness, by two workers. So "the MAX2 subnetwork" is not a well-defined
graph on leads at all. `N4` is **not** escape-free — exactly as Lemma A
predicts, which is a nontrivial consistency check on Theorem 6′.

The deterministic replacement is the **joint-state tree** `J` on states
`(lead of max, lead of second max)`: proved deterministic, uniquely rooted, and
of in-degree `<= 2` — a genuine binary in-tree, and the honest version of the
chapter's p. 122 claim. But `depth_J(σ_c) = g(c) + r(c)`, so Kraft on `J`
**over-charges by exactly `2^{depth_B(c)}`** — the same factor §2.2 identifies.
The loosest necessary condition of any flow on `J` is false, with an explicit
9-comparator 5-sorter on which eq (8) holds with **equality** (margin `5/4`,
pushed to `3/2` at `n = 6`) — and that network **satisfies** LEMMA★, so the flow
route is strictly weaker than the per-node route it was meant to replace.

**Why fractional splitting cannot help, structurally:** the only term that keeps
the certificate near 1 is `ε(c)`, the pass-throughs on the two max-path arms
strictly **below** `c` — a **pre-meeting** quantity. Those comparators lie on no
root-to-`σ_c` path of the post-meeting network, so **no capacity assignment on
the flow network can express `ε`**. Splitting shared segments only reduces what
reaches a source; the deficiency is in total mass, not congestion.

**The escape trade-off, measured.** Escaping is not free — but it is **not** paid
for in the currency a flow can see. Per branch node, grouped by escape count,
mean slack rises (2.91 → 5.45) driven entirely by `r(c)` (2.41 → 5.18) while the
pass-through credit `ε+γ` *falls* (0.50 → 0.26). The payment is in the quantity
the flow already halves on, and it is insufficient.

### 2.4 Automated conjecture refinement — **PRODUCTIVE**

Corpus: **181 301** networks, all constructed or brute-force enumerated —
exhaustive minimal `n = 4` (708) and `n = 5` (149 040, every one size-optimal),
450 constructed `n = 3..9`, and 31 103 random `n = 6..9` **stratified by
pass-through count** (buckets 0..18). Feature dumps are per-branch-node and
re-minable without recomputation. **2 078 999** adversarially-guided evaluations,
every visited network re-verified a sorter.

Roughly two dozen candidate invariants were tested. All per-node forms
`sum_c 2^{a(c)-X(c)} <= 1` that imply eq (8) were **refuted**, including the six
most principled designs (`W*+min(ov,def)`, `W*+min(esc,def)`, …) and every
"max over a neighbourhood" global variant (ancestors, descendants, parent, root)
— all die at `17/16`. Candidates that survive (`W*+esc`, `W*+ov+lh`,
antichain-restricted forms) **do not imply eq (8)** and are therefore useless as
certificates. Exactly one eq (8)-implying candidate survived: §5.

---

## 3. WHAT IS NOW CLOSED

### 3.1 Per-node charging — closed structurally

On any `T` with `f(B) = 2^{p(2,T)}` (a *tight* network),
`sum_c 2^{a(c)-p(2,T)} = 1` **exactly**. Hence for any per-node exponent
`X(c) <= p(2,T)`, `sum_c 2^{a(c)-X(c)} >= 1`, with equality **iff `X(c) = p(2,T)`
at every branch node** (checks **W5a**, exact rationals). Tight sorters with
**non-constant** `W*(c)` exist — check **W5b** re-derives one by adversarial
search, an 18-comparator 7-sorter with `f = 128 = 2^{p2}`, `p2 = 7` and
`W* = {6,7,7,7,7,7}`. Therefore **no certificate built from each node's own
pruning can prove eq (8)**, for a structural reason and not by accident. This
strictly generalises `docs/kraft-repair-report.md` §3.2, which closed the family
by a single counterexample.

### 3.2 The register of closed routes

Do not respend effort on any of these; each has an explicit machine-checked
witness in this wave or its predecessors.

| route | status |
|---|---|
| per-node charging (LEMMA★ class), any `X(c)` from `c`'s own pruning | **closed structurally** (§3.1) |
| "max `W*` over a neighbourhood" global repairs | refuted, `17/16` |
| naive union repair (K); MAX/MAX2 disjointness; shape-only MAX/MIN | refuted previously |
| `sum_c 2^{-r(c)} <= 1`; `sum_c 2^{-(depth+r)} <= 1`; `X = W*+ov` | refuted (`1.25`, `1.625`, `33/32`) |
| local surgery in any of three measures; comparator insertion as a free move | refuted, rigid witnesses (§2.1) |
| flow/min-cut on **leads** | ill-posed — successor is not a function (`N4`) |
| flow/min-cut on the **joint tree**; any fractional split | over-charges by `2^{depth_B(c)}`; loosest necessary condition false (§2.3) |
| branch-node-antichain direct counting; the `S(T)` bound | refuted, tight optimal 5-sorter (§2.2) |
| "the broken Kraft sum is bounded by a small constant" | **not supported** — see §4 |

---

## 4. MEASURED FACTS

- **The broken eq (6) sum is much worse than recorded, and grows with `n`.**
  `docs/kraft-repair-report.md` records `1.25`. Adversarial search reaches
  **1.6875** at `n = 6` (check **W4c**) and **1.8125** at `n = 7`
  (`.build/v3-swarm/lead/kraft_sup.txt`); the related `sum_c 2^{-r(c)}` reaches
  **2.875**. The suprema rise with `n` (LEMMA★'s own sum: `17/16`, `9/8`,
  `73/64` at `n = 6,7,8`). **Do not build on a constant bound.**
- **eq (8) is tight almost everywhere at small `n`.** Every minimal 5-sorter of
  size `<= 9` has margin exactly 0 (149 040/149 040). Adversarial maximisation of
  `f/2^{p2}` reaches exactly `1.000000` at `n = 4..8` and never exceeds it
  (check **W4b**) — the search reaches the boundary and stops, which is what
  makes the non-refutation meaningful rather than merely unsuccessful.
- **Tightness and broken Kraft coincide far more often than recorded.** The
  dispute verdict reports 27 %; over the complete set of 149 040 optimal
  5-sorters eq (8) is tight in **100 %** and eq (6) broken in **43.9 %**; pooled,
  **37.1 %** of the corpus is simultaneously tight and Kraft-broken. The broken
  lemma is not confined to slack-rich networks.
- **eq (6) breaks in 0.0 % of clean networks at every `n`**, with failure rate
  rising monotonically in pass-through count.

---

## 5. THE SURVIVING CANDIDATE (NOT PROVED)

> **CONJECTURE L4-1.** For every `N`-sorter `T` with MAX branch tree `B`,
> ```
> sum over branch nodes c of  2^{ a(c) - min( W*(c) + 1 , p(2,T) ) }  <=  1.
> ```

It **implies eq (8)** (since `min(W*+1, p2) <= p2`) and reduces to Theorem 6 on
clean sorters. Reading: *LEMMA★, except every branch node whose own best pruning
falls short of the global optimum is charged one extra bit, capped at the
optimum.*

**Status: validated on 181 301 corpus networks and ~595 000 adversarial
evaluations; supremum exactly 1, attained on 13 201 networks (7.28 %) including
the very networks that break LEMMA★. NOT PROVED.**

> **Exact falsification criterion.** Any sorter with `f(B) = 2^{p(2,T)}` and some
> branch node with `W*(c) <= p(2,T) - 2` refutes it immediately. Equivalently,
> L4-1 is essentially the claim: *on a tight network, `p(2,T) - W*(c) <= 1` for
> every branch node.*

That configuration was searched for directly (274 000 evaluations by the mining
worker, plus check **W5d** here) and never found. Note the contrast with §3.1,
which needs only `p(2,T) - W*(c) >= 1` on a tight network — that **does** occur.
The whole of L4-1 is the gap between `>= 1` and `>= 2`.

**Honest confidence: 25–35 %.** Against: the "+1" is a fitted constant with no
structural motivation, and this is epistemically the position LEMMA★ occupied
before it fell. For: the refutation condition is a single crisp configuration
that has been heavily and specifically searched.

---

## 6. CORRECTIONS TO THE RECORD

1. **`docs/kraft-repair-report.md` §3.1's "pass-throughs are the sole
   obstruction" is superseded.** Pass-throughs are necessary but not sufficient
   for the obstruction; **escapes** are the right notion. Batcher's 12-sorter has
   a pass-through and is provably fine.
2. **`docs/kraft-repair-report.md` §8's status row** "eq (8) for **clean**
   `N`-sorters" should read "for **escape-free** `N`-sorters (Theorem 6′,
   `docs/kraft-repair-wave1.md` §1)", which subsumes it.
3. **Methodological — a flaw in this project's own enumerators.** Both
   `enumerate_sorters` implementations skip *inert* comparators (`if ns == state:
   continue`). An inert comparator is still traversed by max-paths and **is
   exactly a pass-through**, so this pruning systematically deletes
   pass-through-rich networks from every "exhaustive" universe used here. It
   *understates* the size of the escape-free class (`n = 4`: ratio 1.09 in the
   minimal universe vs 1.70 inert-allowed). Any future exhaustive claim must
   name its universe. `tools/verify_kraft_wave1.py` now checks both.
4. **Adversarial search on this landscape is genuinely luck-dependent.** There
   is a large plateau at exactly 1.0; single-seed hill-climbing re-derived the
   LEMMA★ refutation under one budget and failed under a larger one. The
   verifier therefore uses deterministic **multi-seed** hunts. Any future claim
   of the form "survived adversarial search" must state seeds, steps and
   restarts, and should assume a single seed is insufficient.

---

## 7. HONEST STATUS

| claim | status |
|---|---|
| Lemmas A–E; **THEOREM 6′** (eq (8) for escape-free sorters) | **PROVED**; refuter-audited; 0 violations over 4 019 in-class networks |
| escape-free ⊋ clean; Batcher-12 in the gap | **PROVED** + machine-checked (size is universe-dependent, §1.3) |
| escape-free ⇏ `ov(c) = 0` (Lemma D load-bearing) | **PROVED** by witness |
| lead-level successor is a function | **FALSE in general** (`N4`); **true in-class** (Lemma A) |
| per-node charging cannot prove eq (8) | **PROVED** structurally (§3.1) |
| global surgery / direct counting / fractional flow | **DEAD**, explicit counterexamples (§2) |
| what `f(B)` counts combinatorially | **PROVED** (§2.2) |
| joint-state tree is a binary in-tree | **PROVED** (§2.3) |
| **eq (8) in general** | **NOT proved, NOT refuted.** 0 counterexamples in >180 000 networks plus targeted adversarial attack that reaches exact tightness |
| **L4-1** | **CONJECTURE**, validated not proved, confidence 25–35 % (§5) |
| the published lower bound under audit | still **conjecture**; the proved floor is unchanged by this wave |

No search for a sorting network was run, no candidate network was produced, and
no comparator count was used as a target, bound, feature or stopping condition
anywhere in this wave.

---

## 8. WAVE-2 PRESCRIPTION

1. **Formalize Theorem 6′** (Isabelle/Lean). It is formalisation-ready, uses
   only Kraft plus (R1)–(R3), and subsumes the clean case, so it replaces rather
   than adds to the formalization target. Use the one-line form of Lemma B
   (*the second max traverses no branch node after the meeting*).
2. **Attack L4-1 at its falsification criterion.** Either prove
   *`f(B) = 2^{p(2,T)}` ⟹ `p(2,T) - W*(c) <= 1` for all `c`*, or find the sorter
   that breaks it. This is a crisp, self-contained, finite-flavoured target, and
   §3.1 shows the `>= 1` case is real, so the question is exactly why 2 is
   unreachable. **Highest-value item.**
3. **Widen Theorem 6′ by weakening escape-freeness.** Among escaping `n = 4`
   sorters, 144/564 still satisfy the Kraft step and 120/564 still satisfy the
   per-node step, and *these fail on largely different networks*. Only the
   conjunction is needed. A hypothesis strictly weaker than escape-freeness that
   still delivers both would widen the theorem immediately. Candidate direction:
   bound the number of escapes rather than forbidding them, and pay for each
   escape out of the `r(c)` growth measured in §2.3.
4. **Follow the surgery post-mortem's contrapositive** (§2.1): rather than
   removing pass-throughs, **bound `f(B)` above in terms of the pass-through
   count and `p(2,T)` directly**. The measured mechanism — pass-throughs are the
   padding permitting an unbalanced `B` — is a quantitative statement waiting to
   be made.
5. **Do not retry** anything in §3.2.

---

## 9. REPRODUCTION

```
python3 tools/verify_kraft_wave1.py            # 26 checks, ~2 min, exit 0
python3 tools/verify_kraft_wave1.py --fast     # ~20 s
python3 tools/verify_kraft_wave1.py --quiet    # verdicts only
python3 tools/verify_huffman2.py               # the predecessor, unchanged
python3 tools/verify_kraft_dispute.py          # the independent verifier, unchanged
```

Deterministic (fixed seeds, multi-seed hunts), stdlib only, read-only. Every
network is **constructed** — Batcher, bubble, odd-even transposition,
insertion-extension, random comparator prefixes in front of a bubble network
followed by randomised redundant-comparator removal — or **brute-force
enumerated**. The only literal comparator lists in the verifier are
counterexamples, which it re-derives and re-verifies from scratch; **no known
witness network is embedded anywhere**.
