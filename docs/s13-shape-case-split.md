# The S(13) Root Tree-Shape Case Split — Formal Statement and Audit

**Date:** 2026-08-17
**Machine check:** `tools/verify_shape_case_split.py` (pure stdlib, deterministic,
~5 s). Every number in this document is produced by that script; nothing here is
copied from the survey.
**Audits:** `docs/research/xdomain-bound-theory.md` §6.2 and the headline of
`docs/research/synthesis-ranked-queue.md`.

---

## 0. Verdict

> **The claim "only 5 root tree-shape classes are consistent with a
> 44-comparator 13-sorter" is MODIFIED, not confirmed and not destroyed.**
>
> The counting mathematics reproduces *exactly* — F(13) = 392, log2 F(13) =
> 8.6147, the whole F table for N = 3..17, and the published lower-bound chain
> 44/48/53/57/63. The substance of the claim (a tiny finite case split exists,
> and it is far smaller than anyone would guess) is verified and is in fact
> **stronger** than stated.
>
> The number **5 is wrong**. Under every well-defined convention the count is
> something else:
>
> | granularity | surviving | total |
> |---|---|---|
> | root split, unordered (leaf-count, height) pairs | **3** | 53 |
> | root split, ordered | **6** | 106 |
> | complete tree shape, plane (ordered) | **84** | 208 012 |
> | complete tree shape, up to reflection | **6** | 983 |
>
> The documented list of 5 enumerates *both* orientations of the two height-4
> splits but only *one* orientation of the height-5 split `(4,2 | 9,4)`; the
> recursion is symmetric under exchanging subtrees, so `(9,4 | 4,2)` is equally
> admissible with the identical count 496 and was dropped. It is an enumeration
> slip, not a mathematical disagreement.
>
> **Programme impact: none negative.** The case-split strategy survives intact
> with 3 classes instead of 5, and gains a much sharper form: only **6 abstract
> tree shapes** and only **4 leaf-depth profiles** survive, and the surviving
> shapes are exactly *all* minimum-height shapes plus 24 of the 5976 height-5
> shapes.

A second, more serious caveat is unchanged from the survey and is restated in
§3: the *semantics* of the tree (what it is a tree of, in terms of a network)
is not verifiable from any source in hand. Everything below is a theorem about
the counting function; binding it to networks needs the Plenum 1972 chapter.

---

## 1. Definitions

**Shape.** A *shape* is a finite rooted binary tree in which every internal node
has exactly two children. Its *leaves* are its childless nodes; `h(T)` is the
height (edges on the longest root-to-leaf path; a single leaf has height 0);
`depth(u)` is the distance from the root to `u`. A *plane* shape distinguishes
left from right; an *abstract* shape is a plane shape up to reflection at any
subset of nodes. A shape with `s` leaves has `ceil(log2 s) <= h <= s-1`.

**Outcome count.** Define `V` on shapes by

```
V(leaf) = 0
V(T)    = 2 * ( V(T_l) + V(T_r) + 2^( h(T_l) + h(T_r) ) )
```

(the recursion `v = 2*(fl + fr + 2^(dl+dr))` of Dobbelaere's gist, transcribed in
`docs/research/xdomain-bound-theory.md` §1.4).

**F.** `F(N) = min { V(T) : T a shape with N leaves }`.

**Admissibility.** A shape `T` with 13 leaves is *admissible* iff
`V(T) <= 2^9 = 512`. Rationale: by (E1) below, `S(13) >= S(11) + P` with
`2^P >= V(T)`; so `V(T) >= 513` forces `P >= 10` and hence `S(13) >= 35+10 = 45`.
Shapes with `V(T) <= 512` are exactly those not excluded by this argument.

**Convention warning.** The survey writes `minf(size, depth)`, and its numbers
`minf(13,4)=392, minf(13,5)=496, minf(13,6)=856` are the minima over shapes of
*exactly* that height. Under a "height at most d" reading, `minf(13,5)` would be
392, not 496. The script checks both readings and confirms the exact-height one
(`[PASS] the same numbers are NOT the height-budget minima`). All shape classes
below use exact heights.

---

## 2. External inputs (asserted, not proved here)

| tag | statement | status |
|---|---|---|
| **E1** | Van Voorhis two-channel: `S(N) >= S(N-2) + P(2,N)`, `P(2,N) >= ceil(log2 F(N))` | Plenum 1972, **paywalled, not in hand** |
| **E1'** | the *shape-wise* form of E1: for a network `C` with induced shape `T(C)`, the deleted-comparator count satisfies `P >= ceil(log2 V(T(C)))`, and E1 is the minimisation of this over shapes | **stronger than the published statement; assumed, unverified** |
| **E2** | The `V` recursion above is the correct transcription of van Voorhis's `F` | validated indirectly, §4 |
| **E3** | `S(1..12) = 0,1,3,5,9,12,16,19,25,29,35,39` | Knuth; Codish et al. 2014 (n=9,10); Harder arXiv:2012.04400 (n=11); n=12 by van Voorhis + known network |

Everything else in this document is re-derived from scratch by the script.

---

## 3. The trust boundary — read this before building on the case split

The script verifies a theorem about **shapes**. It cannot verify the bridge

> *for a 13-sorter `C`, the two-channel pruning structure of `C` is a shape `T(C)`
> with 13 leaves, and the number of comparators deleted, `P`, satisfies
> `2^P >= V(T(C))`.*

That bridge is exactly what the Plenum chapter contains and no retrievable
source states. Until it is in hand, the case split is a **conditional** finite
programme: sound as arithmetic, unbound to networks.

**The case split needs E1', which is strictly stronger than E1.** The published
statement bounds `P(2,N)` by `ceil(log2 F(N))` where `F` is already a *minimum
over shapes*. The case split needs the un-minimised, per-network form: the shape
`T(C)` induced by a *particular* network must satisfy `P >= ceil(log2 V(T(C)))`,
so that a network whose shape has `V >= 513` is excluded individually. That is
almost certainly how the recursion arises (a min over shapes is the natural
closure of a shape-wise bound), and §6.2 of the survey assumes it silently, but
it is an assumption and it carries the entire case split. **If E1 turns out to be
provable only in its minimised form — e.g. if the shape is not a function of `C`
but of the proof — then the case split collapses and nothing in §5 can be used
against networks.** Confirming E1' is the single highest-value question to put to
the primary source, ahead of the exact definition of the shape itself.

**Partial evidence about the semantics, obtained here.** Two independent
findings constrain the interpretation and both are consistent with
`T(C)` being the **max-path tree**: leaf `i` at depth `delta(C,i)`, where
`delta(C,i)` is the number of comparators on the path traced by the single 1 of
the one-hot input `e_i`, root at the max output.

1. *The height restriction is independently derivable.* Van Voorhis's
   **one-channel** theorem gives `|C| >= S(12) + delta(C,i)` for every channel
   `i`. A 44-comparator 13-sorter therefore has `delta(C,i) <= 44 - 39 = 5` for
   all `i`, so its max-path tree has height `<= 5`; and any 13-leaf binary tree
   has height `>= ceil(log2 13) = 4`. So heights `{4,5}` — precisely what the
   shape enumeration produces from the *unrelated* `V`-counting argument
   (§5, "no shape of height >= 6 survives"). This is a non-trivial coincidence.
2. *Closed forms.* `V` on a perfect tree of height `h` is `h * 2^(2h-1)`, i.e.
   `(N^2 log2 N)/2` for `N = 2^h` leaves — the shape of a count over *pairs* of
   channels weighted by depth, which is what a two-channel argument should
   produce.

This is evidence, not proof. **Do not put per-class campaign compute behind this
until E1/E2 are confirmed from the primary source** (the ILL request already
tracked in `docs/research/synthesis-ranked-queue.md`).

---

## 4. Validation of the transcription (E2)

The script performs every external cross-check reachable without the chapter,
and all pass:

- **Reproduces the documented F table** for N = 3..17 exactly:
  8, 16, 36, 52, 80, 96, 168, 200, 256, 288, **392**, 424, 480, 512, 784.
- **Never contradicts a known exact value:** `ceil(log2 F(N)) <= S(N)-S(N-2)`
  for every N = 3..12 (slack 0,0,0,1,0,0,1,2,2,1). A single violation would have
  refuted E1+E2 outright.
- **Reproduces the published lower-bound chain** (Dobbelaere, SorterHunter
  2025-04-21) for N = 13..17: 44, 48, 53, 57, 63.
- **Arithmetic of the 13 case:** `F(13) = 392`, `log2 392 = 8.614710`,
  `ceil = 9`, `S(11) + 9 = 44`. Closing the last unit needs a count of `513`,
  i.e. a **30.9 %** strengthening (`513/392 = 1.3087`).
- **One-channel recurrence** `S(n) >= S(n-1) + ceil(log2 n)` is consistent with
  S(1..12); the shifted "Codish form" is confirmed never stronger (the citation
  trap noted in `docs/sota-survey.md`).
- **S(11) = 35** is consistent with its neighbours under one-channel
  (`29 + 4 = 33 <= 35`, and `35 + 4 = 39 = S(12)`, tight).

Two internal identities are also machine-checked, and are new:

- **Node-sum identity.** `V(T) = sum over internal nodes u of
  2^( depth(u) + 1 + h(left(u)) + h(right(u)) )`.
  *Proof:* induction. For a leaf both sides are 0. For `T = (T_l, T_r)`, the
  outer factor 2 multiplies every subtree term by 2, i.e. increments each
  internal node's `depth` by one — which is exactly its new depth in `T` — and
  the extra `2 * 2^(h_l + h_r)` is the root's own term at `depth = 0`. ∎
  This makes `V` a *local* sum over comparator-like objects, which is what makes
  the class constraint enforceable (§7).
- **Perfect-tree closed form.** `V(perfect of height h) = h * 2^(2h-1)`
  (2, 16, 96, 512, 2560 for h = 1..5).

---

## 5. The theorem

Let `Shapes(13)` be the 208 012 plane shapes with 13 leaves (Catalan(12)); up to
reflection there are 983 (Wedderburn–Etherington A001190, re-derived by the
script as a check on its canonicalisation).

> **Theorem (machine-checked, conditional on E1–E3).**
> Exactly **84** of the 208 012 plane shapes with 13 leaves satisfy
> `V(T) <= 512`; up to reflection these are exactly **6** abstract shapes.
> They are:
>
> **(a)** *all 60* plane shapes of minimum height 4 — values 392, 400, 416; and
> **(b)** exactly *24 of the 5976* plane shapes of height 5 — values 496, 512.
>
> Every other shape has `V(T) >= 528`. No shape of height `>= 6` is admissible.

**Corollary 1 (root split).** The root of an admissible shape splits the 13
leaves as **5+8, 6+7 or 4+9** — never 1+12, 2+11 or 3+10, at any height
assignment. With heights, the surviving unordered root classes are exactly

| class | root split | min count | max count | plane shapes | abstract shapes |
|---|---|---|---|---|---|
| **C1** | `{(5 leaves, h3), (8 leaves, h3)}` | 392 | 400 | 12 | 2 |
| **C2** | `{(6 leaves, h3), (7 leaves, h3)}` | 392 | 416 | 48 | 2 |
| **C3** | `{(4 leaves, h2), (9 leaves, h4)}` | 496 | 512 | 24 | 2 |

**Corollary 2 (leaf-depth profile).** Only 4 multisets of leaf depths are
admissible (each satisfies Kraft equality `sum 2^-d = 1`, as it must):

| profile | multiset | shapes | counts |
|---|---|---|---|
| **P1** | `3,3,3` + `4`×10 | S1, S2, S4 | 392, 416 |
| **P2** | `2` + `4`×12 | S3 | 400 |
| **P3** | `3,3,3,3` + `4`×7 + `5,5` | S5 | 496 |
| **P4** | `3`×5 + `4`×4 + `5`×4 | S6 | 512 |

For comparison, the one-channel theorem alone (height `<= 5`) permits **13**
profiles; the shape count cuts that to **4**.

**The six abstract survivors,** in the script's rendering (`*` = leaf, children
in canonical order):

| id | count | height | root | plane mult. | shape |
|---|---|---|---|---|---|
| S1 | 392 | 4 | 6\|7 | 16 | `(((* *) ((* *) (* *))) ((* (* *)) ((* *) (* *))))` |
| S2 | 392 | 4 | 5\|8 | 8 | `(((* *) (* (* *))) (((* *) (* *)) ((* *) (* *))))` |
| S3 | 400 | 4 | 5\|8 | 4 | `((* ((* *) (* *))) (((* *) (* *)) ((* *) (* *))))` |
| S4 | 416 | 4 | 6\|7 | 32 | `(((* (* *)) (* (* *))) ((* (* *)) ((* *) (* *))))` |
| S5 | 496 | 5 | 4\|9 | 16 | `(((* *) (* *)) (((* *) (* *)) ((* *) (* (* *)))))` |
| S6 | 512 | 5 | 4\|9 | 8 | `(((* *) (* *)) ((* ((* *) (* *))) ((* *) (* *))))` |

Plane multiplicities sum to 84.

### 5.1 Proof

The proof is finite exhaustion, performed twice by independent methods that must
agree:

1. **Brute force.** Enumerate all 208 012 plane shapes with 13 leaves and
   evaluate `V` directly from its definition. This alone is the proof.
2. **DP.** `g(s,h)` = min `V` over shapes with exactly `s` leaves and exactly
   height `h`, via
   `g(s,h) = min over s1+s2=s, max(h1,h2)=h-1 of 2*(g(s1,h1)+g(s2,h2)+2^(h1+h2))`,
   `g(1,0)=0`. The script checks that the per-height minima of the brute-force
   enumeration equal `g(13,h)` for every `h`.

The DP table is small enough to check by hand. `g(s,h)` for `s <= 13`:

```
  s | h=0   h=1   h=2   h=3   h=4   h=5   h=6
  1 |   0     -     -     -     -     -     -
  2 |   -     2     -     -     -     -     -
  3 |   -     -     8     -     -     -     -
  4 |   -     -    16    24     -     -     -
  5 |   -     -     -    36    64     -     -
  6 |   -     -     -    52    84   160     -
  7 |   -     -     -    80   108   196   384
  8 |   -     -     -    96   140   236   452
  9 |   -     -     -     -   168   284   524
 10 |   -     -     -     -   200   328   604
 11 |   -     -     -     -   256   376   680
 12 |   -     -     -     -   288   440   760
 13 |   -     -     -     -   392   496   856
```

Root-level verdicts follow by one line of arithmetic each, e.g.

```
 (5,h3 | 8,h3): 2*( 36 +  96 + 2^6) = 392  <= 512   admissible   [C1]
 (6,h3 | 7,h3): 2*( 52 +  80 + 2^6) = 392  <= 512   admissible   [C2]
 (4,h2 | 9,h4): 2*( 16 + 168 + 2^6) = 496  <= 512   admissible   [C3]
 (3,h2 |10,h4): 2*(  8 + 200 + 2^6) = 544  >= 513   excluded
 (2,h1 |11,h4): 2*(  2 + 256 + 2^5) = 580  >= 513   excluded
 (1,h0 |12,h4): 2*(  0 + 288 + 2^4) = 608  >= 513   excluded
 (5,h4 | 8,h3): 2*( 64 +  96 + 2^7) = 576  >= 513   excluded
 (6,h3 | 7,h4): 2*( 52 + 108 + 2^7) = 576  >= 513   excluded
 (4,h2 | 9,h5): 2*( 16 + 284 + 2^7) = 856  >= 513   excluded
```

The bottom row of the table also shows why nothing of height `>= 6` survives:
`g(13,6) = 856` already, and `g(13,h)` rises monotonically thereafter
(856, 1592, 3112, 6172, 12300, 24580, 49152).

### 5.2 Robustness

The largest surviving count is 512; the smallest excluded count is **528**. The
classification is therefore stable under any restatement of the counting
function that moves values by less than **3.12 %**. Sensitivity table
(script output):

| ceiling | plane shapes | abstract shapes | unordered root classes |
|---|---|---|---|
| 392 | 24 | 2 | 2 |
| 400 | 28 | 3 | 2 |
| 416 | 60 | 4 | 2 |
| 496 | 76 | 5 | 3 |
| **511** | 76 | **5** | 3 |
| **512** (derived) | **84** | **6** | **3** |
| 528 | 100 | 7 | 3 |

**Trap flagged deliberately:** a *strict* reading of the ceiling (`V < 512`)
would give exactly 5 abstract shapes. That is a numerical coincidence — the
documented claim counts root splits, not shapes, so this is not its provenance —
but it is exactly the kind of coincidence that produces a false "confirmation".
The script asserts it explicitly so it can never be mistaken for one.

---

## 6. Where the "5" came from

`docs/research/xdomain-bound-theory.md` §6.2 lists:

```
- d=4: (5,3 | 8,3), (6,3 | 7,3), (7,3 | 6,3), (8,3 | 5,3)  — all = 392
- d=5: (4,2 | 9,4)                                          — = 496
```

Four of these are two mirror pairs; the fifth is one half of a third mirror
pair. `V` is symmetric under exchanging `T_l` and `T_r`, so `(9,4 | 4,2)` has
count 496 and belongs on the list. The correct ordered count is 6 and the
correct unordered count is 3. No downstream number in the survey depends on the
value 5, so nothing else in the programme is affected; the sentence in
`docs/research/synthesis-ranked-queue.md` ("5 independent restricted
exhaustions") should read **3**.

---

## 7. The classes as engine constraints

Under the working interpretation of §3 (leaf `i` at depth `delta(C,i)`), each
class is enforceable on a candidate network, and — crucially — the enforcement
is **prefix-monotone**: appending comparators can only lengthen a max-path, so
`delta` is non-decreasing along a forward search and an upper bound on it is a
sound prune at every prefix.

**Filter 0 (free, class-independent).** `max_i delta(C,i) <= 5` and
`>= 4`. Follows from the one-channel theorem alone and needs no shape theory.

**Filter 1 (profile).** For a *complete* network the multiset `{delta(C,i)}` must
be one of P1–P4 (Corollary 2). Cost: one linear pass tracing 13 one-hot inputs,
`O(13*|C|)`.

*Prefix form (the version the engine actually wants).* Let `d_i` be the current
max-path length of channel `i` in a prefix. Because `delta` is non-decreasing
under extension, any completion has `delta_i >= d_i`, so a profile `P` is still
reachable from the prefix iff `d` can be matched into `P` channel-by-channel with
`d_i <= P_{sigma(i)}`. By the standard exchange argument this is decidable by
sorting: **sort `d` and `P` ascending and require `d_(k) <= P_(k)` for all k.**
If no surviving profile passes, the prefix is dead. This is O(13 log 13) per
prefix, sound at every depth, and strictly stronger than Filter 0. It is the
single cheapest useful consequence of this document and is independent of which
class campaign is running.

**Filter 2 (class).** The merge structure of the 13 max-paths — i.e. the shape
itself — must be one of S1–S6. Checking this is again a linear pass (build the
tree of path merges, canonicalise, compare against 6 stored shapes). Unlike
Filter 1 this has no useful prefix form: merges can still occur arbitrarily late,
so Filter 2 is a completion test, used to route a found network to its class
rather than to prune.

**Class definitions for campaign purposes:**

- **C1** — the max-path tree splits at the root into a 5-leaf height-3 subtree
  and an 8-leaf height-3 subtree. Profiles P1 (count 392) or P2 (400). Its
  8-side, in the 392 case, is the *perfect* depth-3 tree.
- **C2** — root splits 6-leaf height-3 / 7-leaf height-3. Profile P1 only
  (counts 392 and 416).
- **C3** — root splits 4-leaf height-2 / 9-leaf height-4; tree height 5.
  Profiles P3 (496) or P4 (512).

`C1 ∪ C2 ∪ C3` is exhaustive over admissible shapes; the classes are disjoint
(distinct root splits).

### 7.1 Win-win property

For each class, a complete exhaustion has exactly two possible outcomes:

- **No 44-comparator 13-sorter whose max-path tree lies in the class** — the
  class is refuted. Refuting C1, C2 and C3 proves `S(13) >= 45`, and by the
  propagation in `docs/research/xdomain-bound-theory.md` §0 also improves the
  published table entries at N = 14, 15, 16, 17.
- **A network is found** — then `S(13) = 44` and the open problem is settled the
  other way, with an explicit witness.

There is no third outcome and no wasted campaign. This is what makes the split
worth building even under the E1/E2 uncertainty: the *search* is meaningful
regardless of whether the bridge lemma holds; only the *completeness* of the
three-way split (hence the lower-bound conclusion) depends on it.

**Protocol note (non-negotiable).** Any candidate network at `<= 45` comparators
emitted by any class campaign goes through *both* frozen B1 verifiers by the
documented procedure, is reported immediately, and that line of work stops
pending review. No class campaign may encode a comparator count as a search
target, feature or stopping condition; the class constraint above is a
*structural* filter on max-path geometry and must be implemented as such.

### 7.2 Estimated relative class sizes — ROUGH, FLAGGED AS ESTIMATES

There is no validated cost model for a per-class exhaustion, and there cannot be
one until the semantics are pinned and one class is actually run. What follows
is ordinal, not cardinal.

| | C1 | C2 | C3 |
|---|---|---|---|
| plane shapes in class | 12 | 48 | 24 |
| abstract shapes | 2 | 2 | 2 |
| profiles | P1, P2 | P1 | P3, P4 |
| slack below the 512 ceiling | 112–120 | 96–120 | **0–16** |
| fraction of its height stratum | 20 % of h=4 | 80 % of h=4 | **0.40 % of h=5** |
| channels forced to `delta = 5` | 0 | 0 | **2 (P3) or 4 (P4)** |
| best 12-sorter forced by pruning | 40 comparators | 40 | **39 = S(12), optimal** |

Rough size ordering, most to least constrained (hence cheapest to exhaust
first): **C3 < C1 < C2**. Treat the gap between C1 and C2 as within noise; the
gap between C3 and the others is structural and I expect it to be large.

### 7.3 Engine prerequisites

The class constraint lives on the *forward* object (a network prefix and its
max-path geometry), **not** on the backward object (an output set `X`). The
Track-B set-DP state `X` does not determine `delta(C,i)`, so this case split
cannot be pushed into the Harder-style DP as-is. Consequences for the ranked
queue in `docs/research/synthesis-ranked-queue.md`:

- **Tier-2 #6 (D(9)-pattern canonical 2/3-layer prefix decomposition) is a hard
  prerequisite.** It is the only planned mechanism that is prefix-indexed and
  forward, which is what Filters 0–2 need in order to prune rather than merely
  post-filter. Per-class campaigns should be organised as (class × canonical
  prefix) jobs.
- **Tier-2 #5 (structured duplicate detection / external-memory sharding) is a
  soft prerequisite** — needed for the per-job memory envelope, not for
  correctness.
- **Tier-2 #4 (Glasgow-style exact matcher)** is orthogonal; it speeds every
  job uniformly and is not on the critical path for the case split.
- **Tier-1 #1–#3** land first regardless; they change the arithmetic of every
  budget estimate in §7.2.
- **New requirement, not currently in the queue:** a *max-path tracer* in the
  engine — maintain, per prefix, the 13 one-hot propagation paths and their
  merge tree incrementally. This is cheap (13 integers plus a union structure
  per node) and is the mechanism behind all three filters. It should be added as
  a Tier-1-sized item.
- **Certificate story:** each class run produces an M4-style replayable
  certificate; the *only* new trusted-base obligation for the whole case split
  is the shape-completeness lemma, whose finite part is exactly
  `tools/verify_shape_case_split.py` and whose infinite part is E1+E2.

---

## 8. What would collapse the case split entirely

- **A 30.9 % strengthening of the count** (`F(13) >= 513`) proves `S(13) >= 45`
  with no search at all and makes all three classes vacuous. This is the
  F-audit item (#4 in `xdomain-bound-theory.md` §6.4).
- **A 3.2 % strengthening applied to C3's shapes alone** (496 → `> 512`) kills
  C3 without any search, leaving only C1 and C2 — both at count 392, needing
  30.6 %. So C3 is the cheapest possible *theory-side* win in the whole
  programme, and it is also the class I recommend attacking first by search;
  those two facts reinforce each other.
- **A negative bridge result** — either the E1/E2 semantics do not define a
  13-leaf tree per network, or E1 holds only in its minimised form and E1' fails
  — would leave §5 as a true but inapplicable theorem about shapes, and would
  redirect effort to Huffman2 (#1 in `xdomain-bound-theory.md` §6.4) as the only
  remaining route through the two-channel theorem. This is the most likely way
  the programme item dies, and it costs one library request to find out.

---

## 9. Reproduction

```
python3 tools/verify_shape_case_split.py             # audits the documented claim; exits 1
python3 tools/verify_shape_case_split.py --corrected # audits this document's claim; exits 0
python3 tools/verify_shape_case_split.py --quiet     # verdicts only
```

Runtime ~5 s, no dependencies, no network, no randomness, no environment
sensitivity (checked under multiple `PYTHONHASHSEED` values). The default
invocation exits **nonzero by design**: the claim as documented in the survey is
false, and the script is the record of that.

The script is a verification tool only. It performs no search, constructs no
network, contains no witness, and is not imported by the Track-A harness.
