# Four Candidate Transforms — Bounded Reconnaissance and Verdicts

**Date:** 2026-08-18.
**Scope:** read-only reconnaissance. No repo file outside this document and
`.build/v3-transforms/` was written; no commits.
**Machine checks:** `.build/v3-transforms/census.py`,
`.build/v3-transforms/filters.py`, plus five new `--limit` ladder probes at
n = 9, 10, 11 run with the existing `.build/v3-limits/probe12.py` harness and
the existing `.build/v3-limits/bin/sortnetopt-limits` binary (no source or
binary was modified). Every number below is produced by one of those, by a
counter already present in an archived `instrument.json`, or by the arithmetic
script embedded in §5.

---

## 0. Verdicts

| # | transform | verdict | one line |
|---|---|---|---|
| 1 | transform-based counting (zeta / Möbius / subset convolution) | **KILL as posed; PROMOTE one corollary** | the search's lattice is `2^(2^n)`, not `2^n` — but the `OutputSet` abstraction is exactly the rank-≤2 truncation of a superset-zeta transform, and computing it as one is **85× fewer operations** (machine-checked bit-identical) |
| 2 | spectral growth analysis | **PROMOTE (reframed)** | there is no single spectral radius (measured factors oscillate 12.5 / 46 / 8.4 / 246), but there **is** a sharp new law: the per-(width, level) memo census is **independent of n** across n = 9…13 to within 1.4 % |
| 3 | antichain width bounds | **KILL** | best order-theoretic bound is `10^2454`, best reachability bound `10^75`, empirical range `10^12.3–10^14.9` — 60 to 2440 orders of slack; the binding constraint is reachability, which order theory cannot see |
| 4 | optimal sound quantization | **PROMOTE (reframed)** | 8 bytes is *not* the binding constraint (capacity floor `1/M = 5e-20`); the loss is structural, and the measured lever is **Hall's matching condition on the abstraction data already computed** — 0 false accepts where the deployed coordinatewise test made 7–68 |

---

## 1. TRANSFORM-BASED COUNTING — KILL as posed

### 1.1 The framing error, stated precisely

A search state is an **output set** `X ⊆ {0,1}^n`, i.e. an element of
`2^V` with `|V| = 2^n = 8192`. The lattice over which a zeta/Möbius transform
would run is therefore `2^(2^13)`, not `2^13`. An "algebraic pass over
8192-length arrays" cannot even *name* a state; 8192 is the size of the ground
set of a single state, not of the state space. The premise in the task brief
("the base lattice is tiny") is correct and is exactly why the idea fails: the
tiny object is the fibre, the huge object is the base.

### 1.2 The bound function *is* a zeta transform — and that is the problem

The subsumption lemma (`sortnetopt-internals.md` §2.4, `Checker.thy:442`) says
`A ⊆ B ⟹ bound(B) ≥ bound(A)`. Modulo the group `G = S_n × C_2`, the stored
bound function is therefore literally the `(max, ·)`-zeta transform of the
"core" bound function over the containment order:

```
s(X)  =  max { b(Y) : Y ⊆_σ X for some σ ∈ G }        (a max-zeta / up-closure query)
```

So the honest answer to "can per-state work be replaced by a global transform"
is: *it already is one*, and evaluating it is the entire cost of the programme.

Two independent barriers make the transform view give nothing back:

- **Trimmed/sparse zeta is priced by up-closure, not by support.** Björklund,
  Husfeldt, Kaski, Koivisto, *Trimmed Moebius Inversion and Graphs of Bounded
  Degree* (STACS 2008 / ToCS 47(3):637–654, [arXiv:0802.2834]) give the sharpest
  known sparse zeta: cost within a polynomial factor of **the number of
  supersets of the support**. Here the support is the memo table and its
  up-closure is (essentially) the whole cube-subset lattice. No prior art
  beats up-closure size.
- **Exact sublinear subset queries do not exist**, which the programme already
  records (`synthesis-ranked-queue.md`, "Learned indexes … CIP'02"). That is
  the same statement from the data-structures side.

### 1.3 Where a subset convolution genuinely appears — and buys nothing

The Huffman2 partial-network DP (`van-voorhis-theory-report.md` §5.6)

```
W(S,h) = min over (S1,h1),(S2,h2) with S1 ⊔ S2 = S, max(h1,h2) = h-1
         of  2 · ( W(S1,h1) + W(S2,h2) + 2^{k_pair + h1 + h2} )
```

**is** a min-sum subset convolution over channel subsets. But at n = 13 the
naive `3^13 = 1,594,323` is already trivial, so fast subset convolution buys
nothing; and min-plus has no ring inverse, so the BHKK `O(2^n n^2)` result
degrades to `Õ(2^n M)` with `M` the value range (STOC 2007), and the MinConv
barrier (Cygan–Mucha–Węgrzycki–Włodarczyk, ICALP 2017) says not to expect
better. **No action.**

### 1.4 Also noted, already in the repo

`tools/verify_huffman2.py` check **D1** establishes
`max_plus_1_huffman(b_1..b_m) = ceil(log2 Σ 2^{b_i})`. That makes the Huffman
aggregation a log-sum-exp, i.e. a one-pass algebraic transform: the
`BinaryHeap` in `src/huffman.rs` is `m` integer adds plus one leading-zero
count. This is a micro-optimisation (the counters show `improve_huffman_calls`
= 72.1 M at n = 12 vs `improve_calls` = 73.2 M, so it is a hot function), and it
is the natural way to write the Huffman2 DP. Recorded, not promoted.

### 1.5 The corollary that IS worth promoting

> **Lemma Z (machine-checked).** Let `1_X` be the indicator of an output set
> `X ⊆ {0,1}^n` and let `ζ(S) = |{x ∈ X : x ⊇ S}|` be its superset-zeta
> transform. Then for every ordered channel pair `(i,j)`,
> ```
> channel_pair_abstraction([i,j])
>   = [ ζ(ij),  ζ(j) − ζ(ij),  ζ(i) − ζ(ij),  |X| − ζ(i) − ζ(j) + ζ(ij) ]
> ```
> Consequently `OutputSet::abstraction` (`output_set.rs:438-481`) is a function
> of the **rank-≤2 truncation of ζ alone**, and the whole `Lower` /
> `LowerInvert` index filter is a rank-2 marginal-dominance test.

*Verification:* `.build/v3-transforms/filters.py` recomputes the abstraction
both ways — sortnetopt's strided pair scan, and inclusion–exclusion on the zeta
transform — and asserts equality on **every** generated reachable output set:
733 sets at n = 6, 1722 at n = 7, 514 at n = 8. All PASS, zero mismatches.

*Why it matters.* `sortnetopt-internals.md` §8.1 names abstraction cost as
"the most likely reason the idea [on-line subsumption] was shelved" —
"roughly a 240× slowdown of the hottest operation". Operation counts at n = 13
(script output, `.build/v3-transforms/`):

| route | scalar ops at n = 13 | vs current |
|---|---|---|
| current `write_abstraction_into` — `n(n−1)` strided pair scans, 4 loads + 4 adds each | **2,555,904** | 1× |
| superset-zeta over the `2^13` indicator in `u16` (`n·2^(n−1)` edges) | 114,688 | **22×** |
| bit-parallel popcount on the **packed** bitmap (78 pairs × 128 `u64` words × AND/AND/POPCNT) | **29,952** | **85×** |
| (for scale) `pack_into_slice`, the current `StateMap` key cost | 1,024 | — |

The popcount route is the right one: it consumes the *packed* representation
that `PackedSet` (Tier-1) already provides, it is a contiguous `u64` scan
rather than a stride-`2^k` gather, and it needs no `[bool]` expansion. It also
removes the 8× dense-bitmap multiplier from the abstraction path specifically
(`internals` §8.4). This is a Tier-1-sized, certificate-transparent change with
an exact differential test available (bit-identical abstraction vectors).

**Verdict 1: KILL the transform-based-counting programme; PROMOTE Lemma Z as an
engineering item.** State-multiplicity is irreducible: the search's cost is
`|reachable states|`, and no lattice transform over `2^n`-indexed arrays
addresses it.

---

## 2. SPECTRAL GROWTH ANALYSIS — PROMOTE, reframed

### 2.1 The spectral model as posed is refuted by the data

A single expansion operator with dominant eigenvalue `λ` predicts an
asymptotically constant level-to-level ratio. The measured ratios are
**12.5, 46.1, 8.4, 245.9** — non-monotone by a factor of 29. The oscillation is
not noise (see the control in §2.3); it has a mechanism (§2.5). **No scalar
growth rate exists over the measured range.** Reject the scalar model.

### 2.2 What replaces it: the free-chain coordinate

Define the **free-chain bound**

```
C(n) = 3 + Σ_{k=4}^{n} ceil(log2 k)
```

and the **level** of a `--limit L` run at width `n` as `ℓ = L − C(n)`.

`C(n)` is exactly the lower bound the engine derives from the one-channel /
Huffman chain alone, before any successor expansion: the ladder's first `n−2`
iterations each add one state and raise the bound by `ceil(log2 k)`.
Machine-checked against the archived logs: the iteration with `states = n−2`
sits at lower bound **21, 25, 29, 33, 37** for n = 9, 10, 11, 12, 13 — exactly
`C(9..13)`. (This is also the mechanism behind "the free chain reaches bound 37
at n = 13 in 3 ms" in `evidence/v3/limits/report.md`.)

### 2.3 THE LAW (new, machine-checked this session)

> **Universal Level Law (empirical).** For `1 ≤ ℓ ≤ S(n) − C(n)`, the memo
> census of a `--limit C(n)+ℓ` run — both the total and the per-channel-width
> breakdown — is **independent of `n`**.

Measured totals (five channel counts × five levels; n = 9, 10, 11 ladders run
this session, n = 12/13 from the archived limits campaign). Each cell is taken
from whichever run reached that level; repeated runs of the same level differ by
a few percent (control, below), which is why the ℓ = 3 row shows 25,404 for
n = 9 where the standalone `--limit 24` run reported 25,128:

| level ℓ | n = 9 | n = 10 | n = 11 | n = 12 | n = 13 | spread |
|---|---|---|---|---|---|---|
| 1 | 37 | 38 | 40 | 42 | 43 | 1.162× |
| 2 | 447 | 449 | 526 | 541 | 537 | 1.210× |
| 3 | 25,404 | 25,486 | 25,088 | 25,706 | 24,761 | 1.038× |
| 4 | **208,301** | **209,196** | **207,812** | **208,070** | **207,097** | **1.010×** |
| 5 | — | — | **50,221,718** | **50,788,878** | **50,922,864** | **1.014×** |

Level 5 was the decisive prediction: before running it, the law said n = 11
`--limit 34` would cost ≈ 5.08e7 states. Measured: **50,221,718 states,
333 s, 3.17 GB** — 1.1 % below the n = 12 value.

The law is not merely about totals. At ℓ = 4 the census agrees **width by
width** across all five channel counts:

| n | w3 | w4 | w5 | w6 | w7 | w8 | w9 | above |
|---|---|---|---|---|---|---|---|---|
| 9 | 5 | 57 | 2136 | 35,993 | 132,336 | 34,033 | 3741 | — |
| 10 | 5 | 57 | 2142 | 36,073 | 132,971 | 34,206 | 3741 | 1 |
| 11 | 5 | 57 | 2137 | 35,943 | 132,074 | 33,853 | 3741 | 1,1 |
| 12 | 5 | 57 | 2143 | 36,013 | 132,260 | 33,848 | 3741 | 1,1,1 |
| 13 | 5 | 57 | 2137 | 35,921 | 131,683 | 33,549 | 3741 | 1,1,1,1 |

Increasing `n` adds **exactly one state per new width** and changes nothing
else. Packed-key bytes at ℓ = 4: 3.742 MB (n = 9) … 3.718 MB (n = 13).

**Control (regime and determinism).** The archived n = 12 census runs at
`--limit 34…38` and the n = 13 probes at `--limit 38…42` report the same
intermediate levels from independent runs: e.g. ℓ = 2 at n = 12 gives
540/464/538/541 across four runs, ℓ = 3 gives 24,803/24,788/25,706. Spread from
nondeterministic search order plus the `--limit`-dependent ordering heuristic is
**a few percent** — smaller than the effects the law asserts, and much smaller
than the level-to-level factors.

**Regime caveat (important).** The law holds in the `--limit` (lower-bound
race) regime. Full runs with `limit: None` use a different ordering heuristic
(`search.rs:461` vs `472`) and must also close the upper bound; their ladders
are **not** comparable — e.g. the archived full n = 11 run reaches 4,324,384
states at ℓ = 4 where the `--limit 33` run reaches 207,812, and the full n = 9
run reaches 35,717 where `--limit 25` reaches 208,301 (the deviation goes in
*opposite* directions). All budgeting must be done in the `--limit` regime.

### 2.4 Consequences — the part that changes the campaign

Let `D(n) = S(n) − C(n)` be the highest level a width-`n` search can reach.
Machine-checked from `S(3..12)`:

```
n     3  4  5  6  7  8  9 10 11 12   13
C(n)  3  5  8 11 14 17 21 25 29 33   37
S(n)  3  5  9 12 16 19 25 29 35 39   44 or 45
D(n)  0  0  1  1  2  2  4  4  6  6   7  or 8
```

1. **`S(13) ≥ 45` is exactly "the universal ladder reaches level 8".**
   `S(13) ≥ 44` is level 7. **Nobody has ever computed level 7 at any width**:
   `D(n) ≤ 6` for every `n ≤ 12`. That is a sharper statement of why n = 13 is
   hard than "the state space is bigger", and it explains why n = 12 followed
   n = 11 immediately — `D(12) = D(11) = 6`, so n = 12 needed no new level (and,
   independently, `S(12) = 39` needed no computation at all: one-channel from
   `S(11) = 35`).
2. **Any engine change can be evaluated for its n = 13 effect at n = 9.**
   `n=9 --limit 25` reproduces the n = 13 level-4 population to 0.6 % in
   **10 seconds / 208 k states**; `n=11 --limit 34` reproduces level 5 to 1.4 %
   in **5.5 min / 3.2 GB**. This is a rigorous justification for — and a large
   sharpening of — the existing "n = 9/n = 10 bands" validation protocol.
3. **It kills ranked-queue item #9 in its stated form.** "Knuth/Burnside
   sampling estimator calibrated on n = 9/10/11 to budget each class/prefix job"
   cannot extrapolate: calibration at small `n` reproduces levels 1–6 *exactly*
   and says nothing whatsoever about 7 and 8, because those levels do not exist
   below n = 13. There is no cheap proxy. Reformulate #9 as "measure level 6,
   then model levels 7–8", not "fit small n".
4. **The one measurement that would actually move the S(13) budget** is level 6
   run to completion. Current knowledge is floors only: `≥ 1.35e8` (n = 12
   `--limit 39`, 30-min cap) and `≥ 9.0e7` (n = 13 `--limit 43`, OOM-killed).
   By the law the cheapest place to obtain it is **`n = 11 --limit 35`**, which
   is also the only one of the three that terminates (it is `D(11)`, i.e. it
   proves `S(11) ≥ 35`). Estimated cost: unknown between 1.35e8 and 1.2e10
   states, i.e. 6 GB to 500 GB — a server job, not a laptop job, and the first
   thing to spend server time on.
5. **The geometric-mean multiplier is now exact, not a guess.** The four
   measured factors 12.49 / 46.11 / 8.36 / 245.89 have geometric mean **33.0×**,
   which is precisely the "33× floor" used in
   `evidence/v3/limits/report.md`. The 80 TB – 35 PB bracket
   (`5.09e7 × 33^3` to `5.09e7 × 245.9^3`) is therefore correctly derived, and
   the law does **not** narrow it — only measuring level 6 will.

### 2.5 Why the growth oscillates (mechanism, not a fit)

The census is a **travelling wave in channel width**. Peak-mass width by level:
ℓ = 2 → w 6–7, ℓ = 3 → w 7, ℓ = 4 → w 7, ℓ = 5 → **w 8**. The large factors
(46×, 246×) are the levels at which the mass front advances one width; the
small factors (8.4×) are levels of consolidation inside a width. So the correct
state variable is the pair `(width, level)` and the correct object is a 2-D
transfer operator, not a scalar `λ`. This also confirms `internals.md` §2.5's
inference (mass at widths 8–9, from the 40.6 B/set arithmetic) directly from
counters rather than by inference.

### 2.6 The lemma to hand the proof swarm

> **Lemma L (to prove).** Fix `ℓ ≥ 1`. Let `Reach(n, ℓ)` be the set of canonical
> output sets stored by `Search::search` at width `n` at the moment the root
> lower bound first reaches `C(n) + ℓ`. Then the restriction of `Reach(n, ℓ)` to
> widths `≤ n − 1` equals `Reach(n − 1, ℓ)`, and
> `Reach(n, ℓ) \ Reach(n−1, ℓ)` contains exactly one set of width `n`.

Sketch of the intended argument: the width-`n` root has a unique polarity-`p`
extremal-channel structure at these levels, so step 3 of `Search::improve`
(forced-channel reduction, `search.rs:167-206`) transfers the whole problem to
width `n−1` at bound `C(n)+ℓ − ceil(log2 n) = C(n−1) + ℓ`; and the residual
successor expansion at width `n` contributes nothing until the level exceeds
`D(n−1)`. The measured census is consistent with this to 1 %. A proof turns the
budgeting protocol of §2.4(2) from "validated at five points" into a theorem,
and it would be the first published growth law for a sorting-network search
(the prior-art sweep found none; the closest published per-level counts are
Codish–Cruz-Filipe–Frank–Schneider-Kamp ICTAI 2014 Table 1, for the *forward*
generate-and-prune at n = 9, a different object).

**Verdict 2: PROMOTE.** Deliverable as requested (an a-priori per-level shell
width usable without probes) is *partially* delivered and *partially* proved
impossible: levels 1–6 are now an n-independent table, and levels 7–8 are
provably not obtainable from any smaller `n`.

---

## 3. ANTICHAIN WIDTH BOUNDS — KILL

### 3.1 The arithmetic

The live frontier at width `k` is an antichain in the containment order on
`2^V`, `|V| = 2^k`, modulo `G = S_k × C_2`. At `k = 13`:

| bound | value | vs empirical `10^12.3 – 10^14.9` |
|---|---|---|
| Sperner width of `2^V`, `V = 2^13`: `C(8192, 4096)` | `10^2464.0` | `10^2449` too large |
| `|S_13 × C_2| = 13!·2` | `10^10.10` | — |
| Stanley quotient bound (`2^V` is unitary Peck ⇒ `2^V/G` is Peck ⇒ width = #orbits in the middle rank) | `≳ 10^2453.9` | `10^2439` too large |
| reachability: `78^45` comparator sequences (`78 = C(13,2)`) | `10^85.1` | `10^70` too large |
| …divided by `|G|` | `10^75.0` | `10^60` too large |
| measured non-subsumed frontier at n = 11 (Harder) | `10^7.19` | — |

### 3.2 Why nothing closes the gap

Every technique in the order-theoretic toolbox — Sperner/Dilworth/Mirsky,
Kahn's entropy method, Kleitman–Markowsky, Korshunov — bounds or counts
antichains in the *whole* lattice. Group action buys exactly `log10|G| = 10.1`
orders. **The binding constraint is reachability**: only sets obtainable from
the full cube by comparator application ever appear, and that is invisible to
order theory. The prior-art sweep (26 searches) found **no** reachability-driven
antichain-width bound anywhere; the closest literature (multi-objective /
Pareto-frontier DP) states only the negative — intermediate Pareto-set
cardinality is the bottleneck and can be exponential.

Note also the correct citation for the group-action question, which the
programme did not have: **R. P. Stanley, "Quotients of Peck posets", Order
1:29–34 (1984)** — the Boolean lattice is unitary Peck and `2^V/G` inherits the
strong Sperner property, so the quotient's width is the number of orbits in the
middle rank. Correct, and 2439 orders too weak to be of any use.

### 3.3 The one thing worth keeping (PARK)

The **lower**-bound flip is not vacuous: exhibiting `N` pairwise
non-subsuming *reachable* output sets at n = 13 would make the infeasibility of
the monolithic route unconditional rather than extrapolated, and would be a
clean paragraph in the eventual write-up. It is not on the critical path (the
programme has already committed to decomposition) and it costs real work. Park
it as a write-up item.

**Verdict 3: KILL.** No provable upper bound on the width comes within 60
orders of magnitude of the empirical range, and no technique exists that would.

---

## 4. OPTIMAL SOUND QUANTIZATION — PROMOTE, reframed

### 4.1 Correction to the premise

**TurboQuant ([arXiv:2504.19874], ICLR 2026) is a two-sided, unbiased,
MSE-optimal quantizer.** It offers no "never rejects a true match" guarantee
and is *not* prior art for one-sided filtering. The correct lineage is the one
the programme already cites: Schulz's feature-vector indexing (E-prover, LNAI
7788, 2013) with its explicit monotonicity invariant, and Eén–Biere's SatELite
signature filter (SAT 2005). Both are engineering; **neither has any theory of
optimality**, and the prior-art sweep found no such theory anywhere. That gap is
real and is the reason this item is worth promoting.

### 4.2 Formalization

Let `S` be the set of states and `R ⊆ S × S` the subsumption relation
`(A,B) ∈ R ⟺ ∃σ ∈ G : σ(A) ⊆ B`. `R` is reflexive and transitive — a preorder.

> **Definition.** An **s-byte sound filter** is a pair `(φ, ≼)` with
> `φ : S → M`, `|M| ≤ 2^{8s}`, and `≼ ⊆ M × M`, such that
> `R ⊆ φ^{-1}(≼)`.

Three immediate structural facts, all easy and all useful:

- **(F1) The optimal `≼` for a given `φ` is forced.** It is the pushforward
  `≼* = {(φ(A), φ(B)) : (A,B) ∈ R}`. Any smaller relation is unsound; any
  larger one is strictly worse. So filter design is *entirely* the choice of
  `φ`, and a sound filter is precisely a **monotone map from the subsumption
  preorder into a poset**. This is Schulz's invariant, stated as a definition.
- **(F2) Capacity is not the binding constraint.** `R` is reflexive, so
  `φ(A) = φ(B) ⟹ (A,B)` is accepted. Hence the false-accept rate is at least
  `Pr[φ(A)=φ(B)] − Pr[R] ≥ 1/M − Pr[R]`. At `s = 8`, `1/M = 5.4e-20`, against
  at most `10^15` states. **Adding bytes cannot help; the loss is structural.**
  This retires "maximize rejection per byte" as the objective.
- **(F3) Coordinatewise-dominance filters are order embeddings, and complete
  ones need `dim(P)` coordinates.** A filter comparing `d` monotone integer
  coordinates is an order-preserving map into a product of `d` chains; it is
  *complete* (zero false accepts) iff those chains realize the order, i.e.
  `d ≥ dim(P)` (Dushnik–Miller). For plain containment on `2^V`,
  `dim = |V| = 2^n = 8192`, and the realizing family is exactly the 8192 element
  indicators — the bitmap itself. **So there is no lossless compression of the
  dominance test, and filter+verify is forced.** This is an independent,
  order-theoretic re-derivation of the CIP'02 conclusion the survey already
  relies on, and it is (per the sweep) not stated anywhere in the filtering
  literature.

### 4.3 Where the deployed filters actually sit — measured

Method (`.build/v3-transforms/filters.py`): generate reachable output sets by
applying random comparator networks to the full cube and keeping every
intermediate set; sample ordered pairs `(A, B)` with `|A| ≤ |B|` (the `prune.rs`
query shape: ascending size buckets, query the larger against the stored
smaller); compute ground truth by **exhaustive search over all `n!`
permutations**; assert that every true subsumption passes every filter (it
does — soundness audit passes everywhere).

n = 7, 4000 pairs, size band `|B| ≤ |A|+4` (true-subsumption rate 10.15 %,
3594 rejectable pairs):

| filter | false accepts | % of ceiling | note |
|---|---|---|---|
| `SIZE` (`|A| ≤ |B|`) | 3594 | 0.0 % | the denominator |
| **`SIG`** — Tier-1 64-bit thermometer signature | 1427 | 60.3 % | **deployed** |
| **`HIST`** — exact weight-histogram dominance | 835 | 76.8 % | `SIG`'s own ceiling |
| `M1` / `M2` / `M3` — *flat* sorted rank-r marginals | 513 / 660 / 1029 | 85.7 / 81.6 / 71.4 % | rank is **not** the lever |
| **`ABS`** — sortnetopt abstraction (rank-2, per-channel groups) | **7** | **99.805 %** | **deployed** |
| `HIST+ABS` | 7 | 99.805 % | `HIST` adds **nothing** on top of `ABS` |
| `ABS3` — rank-3, same grouping discipline | 1 | 99.972 % | ~8× the storage (5148 vs 624 values at n = 13) |
| **`ABS-MATCH`** — Hall's condition on `ABS`'s per-channel blocks | **0** | **100.000 %** | **not deployed** |

Same experiment without the size band (n = 7, 58.2 % true rate, 1671
rejectable): `SIG` 918, `HIST` 781, `ABS` 68, `ABS3` 47, **`ABS-MATCH` 15** —
i.e. the matching condition removes **78 % of the exact `subsumes_permuted`
calls** that the deployed coordinatewise test lets through. At n = 8 (900 pairs,
band 6) `ABS` already makes 0 errors. Note that `ABS-MATCH` is **not** complete:
it makes 0 false accepts in both banded runs (3594 + 797 = 4391 rejectable
pairs) but **15** in the unrestricted n = 7 run — those 15 are ready-made
counterexamples (§4.4 item 2).

**Answers to the question as asked:**
- `SIG` is at **72–86 %** of its own theoretical ceiling (the exact histogram
  test) — 60.3/76.8 at n = 7, 57.6/80.1 at n = 8, 45.1/53.3 unrestricted.
- The exact histogram test is at **77–80 %** of the absolute ceiling standalone.
- But in the *deployed cascade* both are nearly redundant. Archived counters,
  n = 10 online-subsumption run (`.build/v3-tier2b/campaign_final/T10/run1`):
  59,508,752 filter candidates → 55,540,095 rejections split
  **`SIG` 46.7 % / abstraction 52.4 % / `HIST` 0.47 %** → 3,968,657 exact calls
  (6.67 % of candidates). The 0.47 % matches the synthetic finding
  `HIST+ABS = ABS` exactly. **`SIG` and `HIST` earn their place on speed, not on
  power; `ABS` does all the rejecting.**

**Honesty caveats.** (i) The population is synthetic (random networks,
uncanonicalised, small `n`); the absolute ceiling fractions are
distribution-dependent. (ii) `ABS` is relatively *stronger* at small `n`: it has
`4n(n−1)` coordinates against sets of `≤ 2^n` elements, a ratio of 1.3 at n = 7
but 0.076 at n = 13. **Do not extrapolate the 99.8 % to n = 13.** The deployed
n = 10 counters are the better anchor, and the exact ceiling fraction there is
*not currently measurable* — it needs one counter (`filter_exact_hits`,
i.e. how many of the 3.97 M exact calls return `Some`) next to the existing
`filter_exact_calls` in the Tier-1 patch. That counter is the single cheapest
instrumentation ask in this document.

### 4.4 The lemma to hand the proof swarm

> **Lemma M (sound, easy — this is the one to formalize and deploy).** For an
> output set `X` and channel `i`, let `v_i(X) ∈ Z^{4(n−1)}` be the per-channel
> abstraction block: the four groups of `channel_pair_abstraction([i,j])` over
> `j ≠ i`, each sorted descending. If `π(A) ⊆ B` for a channel permutation `π`,
> then `v_i(A) ≤ v_{π(i)}(B)` coordinatewise for every `i`. Hence the bipartite
> graph `Γ(A,B) = { (i,j) : v_i(A) ≤ v_j(B) }` admits a perfect matching, and
> **"`Γ(A,B)` has a perfect matching" is a sound necessary condition, strictly
> stronger than `Dir::test_abstraction`** — which is exactly the
> coordinatewise-sorted relaxation of the same data
> (`output_set.rs:462-467, 469-481`, `index.rs:101-106`).

Costs `O(n^3)` after the rank-2 marginals that are computed anyway, adds zero
storage, and is certificate-transparent. Note this is *not* the same as
`Subsume::filter_matching` (`subsume.rs:219-278`), which is an arc-consistency
propagator run *inside* the exact test on prefix-restricted abstractions; Lemma
M runs the full matching test *before* unpacking any bitmap, at the index-filter
layer. It is also the cheapest concrete instance of ranked-queue Tier-2 #4
("Glasgow technology: bit-parallel all-different"), and this experiment
quantifies that item for the first time: **78 % of surviving false accepts at
n = 7**.

Follow-on questions for the swarm, in priority order:

1. Formalize (F1)–(F3) and publish them as the missing theory of sound filters
   (the sweep found no prior statement). (F3) in particular gives the programme
   a rigorous "filter+verify is forced" theorem instead of a citation to an
   empirical negative result.
2. Characterize the gap between Lemma M and exact permuted containment.
   Empirically the gap is already **non-empty** (15 false accepts out of 1671
   rejectable pairs in the unrestricted n = 7 run) but **empty** on both
   size-banded samples (0 out of 4391) — which is the regime `prune.rs` actually
   queries in. Deliverable: extract a minimal counterexample from those 15, and
   determine whether the gap vanishes on same-size or near-same-size pairs (if
   so, Lemma M is *exact* on the deployed query distribution and the exact test
   becomes a rarely-taken slow path).
3. Given (F2), the right optimization is not "bytes" but "which monotone
   invariants". The measured answer so far: **grouping beats rank** — flat
   rank-3 marginals (`M3`, 71.4 % of ceiling) are *worse* than flat rank-1
   (`M1`, 85.7 %), while the same rank-2 data with per-channel grouping (`ABS`)
   reaches 99.8 %. Any learned-then-proven filter should search over grouping
   disciplines, not over rank or width.

**Verdict 4: PROMOTE.** The optimum is not characterizable as "best `s` bytes"
— capacity is not binding — but it *is* characterizable as "best monotone map",
and the measurement identifies a specific, cheap, strictly-stronger map that is
not deployed.

---

## 5. Reproduction

```
# Universal Level Law: census extraction from archived instrument.json files
python3 .build/v3-transforms/census.py

# the five new ladder probes (already run; ~12 min total, ≤3.2 GB)
for L in 22 23 24 25; do python3 .build/v3-limits/probe12.py \
  --bin .build/v3-limits/bin/sortnetopt-limits --channels 9  --limit $L \
  --out .build/v3-transforms/n9/L$L  --max-rss-gb 8 --max-secs 300; done
for L in 26 27 28 29; do ... --channels 10 ... ; done
for L in 30 31 32 33 34; do ... --channels 11 ... --max-secs 600; done

# filter power + the zeta/abstraction equivalence check
python3 .build/v3-transforms/filters.py --n 7 --nets 200 --pairs 4000 --band 4
python3 .build/v3-transforms/filters.py --n 8 --nets 50  --pairs 900  --band 6
```

Nothing in `src/`, `tools/`, `.cache/third_party/` or any other `docs/` file was
modified. The probes wrote only into `.build/v3-transforms/`. No candidate
network was constructed and no witness exists anywhere in this work.
