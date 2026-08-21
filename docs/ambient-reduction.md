# Ambient Reduction — Lemma L Proved, Sharpened, and Its Consequences Priced

**Date:** 2026-08-21.
**Scope:** read-only with respect to `src/`, `evidence/`, `config/`, `ledger/`.
New files: this document and `tools/verify_ambient.py`. All engine work was
done in a fresh worktree copy `.build/v3-ambient-source/` carrying one
measurement-only, env-gated patch (§5.1); dumps and logs under
`.build/v3-ambient/`. No commits. No candidate network was constructed and no
witness exists anywhere in this work.

---

## 0. Verdict

| question | answer |
|---|---|
| Is the cross-*n* state identity real? | **Yes — and it is *exact*, not approximate.** Jaccard `1.000000`, zero bound disagreements, at levels 1–4 for every consecutive ambient pair from n = 7 to n = 13. The published `0.9936` / "1.0–1.4 %" figures were **entirely thread-scheduling noise**; with the worker count pinned the residual is zero. At level 5 (50 M states, multi-threaded) both cross-ambient comparisons agree **better** than two runs of the *same* ambient agree with each other (0.9815 and 0.9889 vs a 0.9804 control). |
| Can Lemma L be proved? | **Yes**, and the proof is short. It follows from three facts, all machine-checked here: the transition relation is *ambient-free*; `canon(prune(cube_n)) = cube_{n-1}`; and `canon(cube_n ▷ [i,j])` is a single state independent of `(i,j)`. |
| Is Lemma L the right statement? | **No — it is a corollary of something stronger and more useful.** The DP never refers to the ambient at all. Every bound is a property of the state; every memo entry transports across ambients unconditionally. §3.1. |
| Does ambient reduction move level 7? | **No.** §7. The reason is structural and is itself a theorem: the *minimum* ambient at which level ℓ exists is `n_min(ℓ) = min{n : D(n) ≥ ℓ}`, and `n_min(7) = 13`. There is no smaller ambient to reduce to. Separately, the engine **already** computes every width-`w` subproblem in a width-`w` representation, so the memo has no ambient overhead to remove. |
| Is anything exploitable? | **Yes, three things, all constant-factor.** §6: (a) the shared bound oracle gets an unconditional soundness *proof* replacing its empirical Jaccard; (b) a sound three-tier **build**-slicing (base / wide12 / wide13) that removes the wide13 tax and shrinks transient frames ≈5.8×; (c) `SORTNETOPT_SUBSUME_WIDTHS` must be pinned to absolute widths, because the default policy is the **only** genuine ambient leak in the engine (§5). |
| Does it change any decision? | **One.** §7: the level-6 measurement — the programme's decisive experiment — is `n = 11 --limit 35`, and Theorem E makes it *exactly* the n = 13 level-6 census rather than a 1.4 %-accurate proxy. It also needs only the **default `MAX_CHANNELS = 11` build**, and 11 is provably the minimum ambient at which level 6 exists. |

---

## 1. The framing, corrected

The brief asked which parts of a level-7-at-`n = 13` computation could be run
"at ambient `min(w+2, 13)`". The premise is that a width-`w` state costs more
when it lives inside a larger ambient. **It does not.**

A search node is a canonical `OutputSet` of width `k`, and the memo key is the
packed bitmap of `2^k` bits — `packed_len_for_channels(k) = 2^(k-3)` bytes
(`src/output_set.rs`). `OutputSetMap` is nine-to-eleven *separate* `BTreeMap`s,
one per width, each with a fixed-size key array of exactly the right size
(`src/search/states.rs:786-794`). A width-7 state occupies 16 bytes whether it
was reached from a width-7 root or a width-13 root. **The stored representation
is already width-optimal; there is no ambient padding to remove.**

What ambient `n` does cost is (i) a build-wide constant factor from
`MAX_CHANNELS`-sized *transient* buffers and the `PackedSet` `Copy` type, and
(ii) nothing else. That reframes the deliverable, and §6 prices what is
actually there.

---

## 2. Where ambient `n` enters the engine — exhaustive audit

Reading `Search::search`, `Search::improve`, `Search::improve_huffman`,
`Edges::improve_next` and `StateMap` end to end (line numbers from
`.build/v3-endgame/source`, which is the 11-patch stack):

| # | site | uses ambient? | effect |
|---|---|---|---|
| 1 | `Search::search` root: `let channels = initial.channels()` (`search.rs:49`) | yes | picks the **root object** `cube_n`. This is the only semantically load-bearing use. |
| 2 | root loop stop test `state.bounds[0] as usize >= limit` (`search.rs:135`) | limit only | the `--limit` value **never leaves this line**. `improve` has no `limit` parameter. |
| 3 | extremal-channel scan (`search.rs:311`) | **no** | `for channel in 0..output_set.channels()` |
| 4 | forced-channel reduction (`search.rs:320-361`) | **no** | `OutputSet::all_values(output_set.channels() - 1)` |
| 5 | Huffman child generation (`improve_huffman`) | **no** | prunes the *current* set's extremal channels |
| 6 | successor expansion (`search.rs:560-561`) | **no** | `for i in 0..channels { for j in 0..i }` with `channels = output_set.channels()` |
| 7 | default state seeding `default_upper_bound(channels)` (`states.rs:43-53`) | **no** | indexed by the state's own width; `known_bounds = [0,0,1,3,5,9,12,16,19,25,29,35]` |
| 8 | ordering heuristic `edges.improve_next(..., Some(state.bounds[0]))` (`search.rs:645`) | **no** | the "limit" in `improve_next` is **the node's own lower bound**, not the run's `--limit` |
| 9 | thread-pool priority key `(level, target.len, bounds[0])` (`search.rs:930`) | **depth only** | scheduling only; see §5.2 |
| 10 | `StateMap::new(root_channels)` shard count (`states.rs:191-193`) | yes | hash sharding; no semantic effect |
| 11 | `StateMap::new(root_channels)` **subsumption index widths** `{n-3, n-2}` (`states.rs:217-235`) | **yes, semantically** | **the one real leak.** §5.3 |
| 12 | `MAX_CHANNELS` / `wide12` / `wide13` (`output_set.rs:16-21`) | build gate | capacity only; changes no reachable value |

Item 8 deserves emphasis because the existing assessment
(`transforms-assessment.md` §2.3, "Regime caveat") asserts that `--limit` runs
and full runs use *different ordering heuristics* and are therefore not
comparable. That is a **misreading**. The two call sites are
`improve_next(..., Some(state.bounds[0]))` from the successor fixpoint and
`improve_next(..., None)` from the Huffman loop — successor-expansion versus
Huffman-expansion, not limited versus unlimited. `--limit` does not reach
`improve` at all. The full-run/limit-run census divergence reported there has a
different cause (a full run must also close the *upper* bound, so it keeps
calling `improve` on the root after the lower bound has passed `C(n)+ℓ`), and
the "regime" caveat as stated should be withdrawn.

---

## 3. The theorems

Throughout, a *state* is a canonical `OutputSet`; `w(X)` is its width;
`Succ(X) = { canon(X ▷ [i,j]) : 0 ≤ j < i < w(X), non-redundant }`;
`Prune(X) = { canon(prune_{p,c}(X)) : p ∈ {0,1}, c extremal for p }`, all of
width `w(X) − 1`. `cube_k` is the canonical full cube on `k` channels.
`C(n) = 3 + Σ_{k=4}^{n} ⌈log₂ k⌉`, `D(n) = S(n) − C(n)`.

### 3.1 Theorem A (Ambient Freedom) — the real statement

> **Theorem A.** With the on-line subsumption index disabled (the default),
> `improve(X)` reads and writes only the memo entries of `X`, of `Succ(X)` and
> of `Prune(X)`; its control flow and every value it stores are functions of `X`
> and of those entries alone. No quantity in the recursion depends on the
> ambient `n` or on `--limit`.

*Proof.* By the audit of §2: rows 3–8 exhaust every loop bound, every table
index and every ordering key inside `improve`/`improve_huffman`/`improve_next`,
and each is `output_set.channels()` or a stored bound. Rows 1, 2, 10, 11 are
outside the recursion (row 11 is excluded by hypothesis). ∎

Two auxiliary facts the proof uses, both confirmed by code inspection:
`OutputSet::apply_comparator` (`output_set.rs:683-712`) never assigns
`self.channels`, and `Canonicalize` (`canon.rs:116-144`) is width-preserving —
`used_channels` only *reorders* unconstrained channels within a same-size
bitmap and never shrinks it. Hence `Succ` preserves width exactly. Separately,
`src/instrument.rs` carries an explicit module contract (lines 4-6) that no
counter is ever consulted by the search; the only value it returns into the
recursion is `same_shell_run`, derived from the current edge's own widths and
popcounts.

*Independent check.* This claim was handed to a second reviewer as a
refutation target, with the whole of `search.rs`, `search/states.rs`,
`search/endgame.rs`, `output_set.rs`, `output_set/canon.rs` and
`instrument.rs` in scope. It returned exactly one counterexample — the
subsumption-index width policy of §5.3 — and confirmed every other site. In
particular the `limit`-named local in `endgame.rs:273` is `2·(b−1)` in the
parent's own upper bound and is unrelated to `--limit`.

Two corollaries that are what the programme actually needs:

> **Corollary A1 (Bound Transport).** For any state `X`, the interval
> `bounds(X)` produced by *any* run at *any* ambient `n ≥ w(X)` is a valid
> lower/upper bound on the same quantity — the number of comparators needed to
> sort `X`. Memo entries therefore transport across ambients, roots, prefixes
> and classes **unconditionally**, with no side condition.

> **Corollary A2 (Width Closure).** `Succ` preserves width and `Prune` lowers
> it by one. Hence for every `w`, the set of states of width `≤ w` is
> **forward-closed** under the transition relation. A computation restricted to
> width `≤ w` is self-contained and needs only a `MAX_CHANNELS = w` build.

A1 is the soundness proof that `lowmem-endgame-assessment.md` §6 obtains
empirically (Jaccard 0.9936 and "99.92 % identical bounds"). It is not a
conjecture and needs no merge argument for *soundness*; the `max`/`min` merge
is still required because two runs may have *tightened* an interval by
different amounts. A2 is the basis of the slice scheme in §6.

### 3.2 Theorem B (the root chain)

> **Theorem B.** For every `k ≥ 4`, every polarity `p` and every channel `c`,
> `canon(prune_{p,c}(cube_k)) = cube_{k-1}`. Consequently `Prune(cube_k)` is the
> single state `cube_{k-1}`, and the Huffman rule applied at `cube_k` combines
> `k` identical children.

*Reason.* Every channel of the full cube is extremal for both polarities
(all singletons and all co-singletons are present), and conditioning the full
cube on one channel holding an extreme value and deleting that channel returns
the full cube on the remaining `k−1` channels. Machine-checked in §4 by direct
comparison of the dumped chain keys against `canon-key <k> --prefix ""`.

Since `max_plus_1_huffman([b,…,b])` over `k` copies equals `b + ⌈log₂ k⌉`,
Theorem B is exactly the recursion `C(k) = C(k−1) + ⌈log₂ k⌉`: **the free
van Voorhis chain is the chain of full cubes, and `C` is its bound.**

### 3.3 Theorem C (the cube has one successor)

> **Theorem C.** `canon(cube_k ▷ [i,j])` is independent of `(i,j)`. Hence
> `Succ(cube_k)` is a single state `s_k` of width `k`, with `|s_k| = 3·2^{k-2}`.

*Proof.* `S_k` acts transitively on unordered pairs and fixes `cube_k`
setwise, so all `C(k,2)` images are `S_k`-equivalent and canonicalise
together. ∎ Machine-checked for `k = 6, 9, 11, 13` (§4).

### 3.4 Theorem D (the Huffman ceiling at the root)

> **Theorem D.** At `cube_k`, the Huffman rule can raise the lower bound to at
> most `S(k−1) + ⌈log₂ k⌉ = C(k) + D(k−1)`, and step 5 of `improve`
> (successor expansion) is not reached until `bounds[0]` attains that value.

*Proof.* `improve` reaches successor expansion only when
`huffman_bounds[1] ≤ bounds[0]` (`search.rs:390`). `improve_huffman` sets
`huffman_bounds[1]` to `max_plus_1_huffman` over the children's **upper**
bounds; by Theorem B the children are `k` copies of `cube_{k-1}`, whose upper
bound is seeded at `known_bounds[k-1] = S(k−1)` and can never fall below
`S(k−1)` because `S(k−1)` is optimal. So the ceiling is
`S(k−1) + ⌈log₂ k⌉`, which equals `C(k) + D(k−1)` because
`C(k) = C(k−1) + ⌈log₂ k⌉`. ∎

Theorem D is where the whole level structure comes from. It also explains,
without any appeal to search order, why increasing `n` adds *exactly one*
state per new width.

*Provenance note, and a dependency worth flagging.* The proof needs
`known_bounds[k]` to equal `S(k)` **exactly**, not merely to be a valid upper
bound: if the seed were loose, the Huffman ceiling would start above
`C(n) + D(n−1)` and the root could take the successor branch later than
Theorem D predicts (still sound, but the clean level structure would blur).
The upstream table stopped at `known_bounds[11] = 35`; the LIMITS-V3 patch
extended it to `[0,0,1,3,5,9,12,16,19,25,29,35,39,45]`
(`src/search/states.rs:50, 553`), so index 12 carries `S(12) = 39` — which is
exactly why Theorem D is tight at n = 13 and gives the ceiling `39 + ⌈log₂ 13⌉
= 43 = C(13) + 6`. Without that patch entry, width 12 would fall through to
the quadratic fallback `12·11/2 = 66` and the ceiling at `cube_13` would start
at 70. **Theorem D at n = 13 is therefore a property of the patched engine,
not of upstream `sortnetopt`.** Index 13 (`45`) is an upper-bound seed from a
known 13-channel network and plays no part in any statement here.

### 3.5 Theorem E (Chain Collapse) — supersedes Lemma L

> **Theorem E.** Let `n_min(ℓ) = min{ n : D(n) ≥ ℓ }`. Then for every ambient
> `n ≥ n_min(ℓ)`,
> ```
> Reach(n, ℓ)  =  Reach(n_min(ℓ), ℓ)  ⊎  { cube_w : n_min(ℓ) < w ≤ n }.
> ```
> In particular `|Reach(n, ℓ)| = |Reach(n_min(ℓ), ℓ)| + (n − n_min(ℓ))`, and the
> width census is identical below `n_min(ℓ)` and exactly `1` at every width
> above it.

*Proof.* Induction downwards from `n`. By Theorems B and C the root `cube_n`
has exactly two out-edges, `cube_{n-1}` and `s_n`. If `ℓ ≤ D(n−1)` then by
Theorem D the successor branch is never taken, so `cube_n` contributes itself
and delegates entirely to `cube_{n-1}`; by Theorem A the recursion from
`cube_{n-1}` is bit-for-bit the recursion a run rooted at `cube_{n-1}` would
perform, i.e. `Reach(n−1, ℓ)` (the level is preserved because the Huffman
step contributes exactly `⌈log₂ n⌉ = C(n) − C(n−1)`). Descend until
`ℓ > D(w−1)`, which first happens at `w = n_min(ℓ)`. ∎

> **Lemma L, as originally stated, is the single-step case of Theorem E and is
> TRUE exactly when `ℓ ≤ D(n−1)`.** Its intended proof sketch
> (`transforms-assessment.md` §2.6 — "the width-`n` root has a unique
> polarity-`p` extremal-channel structure … so step 3, forced-channel
> reduction, transfers the whole problem to width `n−1`") is **incorrect**: at
> `cube_n` *every* channel is extremal for both polarities, so the
> `pol_channels.len() == 1` guard at `search.rs:318` never fires at the root.
> The transfer is done by the **Huffman rule** (step 4), not by forced-channel
> reduction (step 3). The conclusion survives; the mechanism does not.

### 3.6 The prediction Theorem E makes, and the value of `n_min`

From the machine-checked table `D(3..12) = 0,0,1,1,2,2,4,4,6,6`:

| level ℓ | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| `n_min(ℓ)` | 5 | 7 | 9 | 9 | 11 | 11 | **13** |

So Theorem E predicts, a priori, that a level-ℓ dump at *any* ambient has its
population front at width `n_min(ℓ)` and exactly one state at every width
above. This was checked *after* being derived — see §4.3.

---

## 4. Machine checks

`tools/verify_ambient.py` operates on `Search::dump_states` output
(`search.rs:197-224`), which writes `group_<width>_<lowerbound>.bin` files of
concatenated fixed-size packed keys. A dump is therefore a complete
`(width, packed key) → lower bound` table and is self-describing; the checker
needs no engine.

```
python3 tools/verify_ambient.py census    DUMP...      # width x level census
python3 tools/verify_ambient.py chain     DUMP...      # Theorem B / E chain claim
python3 tools/verify_ambient.py compare   A B          # key sets + bounds, per width
python3 tools/verify_ambient.py lemma-l   HI LO        # the three Lemma L clauses
python3 tools/verify_ambient.py selfcheck DUMP         # record sizes, duplicates
```

### 4.1 The identity is exact

Deterministic runs (`SORTNETOPT_POOL_THREADS=1`, §5.1), one binary for every
row (`sortnetopt-det-wide13`) so the build is not a confound:

| level ℓ | ambient pairs checked | `|A∩B|` | `|A\B|` | `|B\A|` | Jaccard | bound disagreements | clause 2 |
|---|---|---|---|---|---|---|---|
| 1 | (7,6) (8,7) (9,8) (10,9) (11,10) (12,11) (13,12) | 34…40 | **0** | **0** | **1.000000** | **0** | PASS ×7 |
| 2 | (8,7) (9,8) (10,9) (11,10) (12,11) (13,12) | 445…450 | **0** | **0** | **1.000000** | **0** | PASS ×6 |
| 3 | (10,9) (11,10) (12,11) (13,12) | 24 199…24 202 | **0** | **0** | **1.000000** | **0** | PASS ×4 |
| 4 | (10,9) (11,10) (12,11) (13,12) | 207 995…207 998 | **0** | **0** | **1.000000** | **0** | PASS ×4 |

The intersection sizes increase by **exactly one per channel** — the free-chain
cube, as Theorem E requires. Dump totals (`total_entries`, deterministic):

| level | n=6 | n=7 | n=8 | n=9 | n=10 | n=11 | n=12 | n=13 |
|---|---|---|---|---|---|---|---|---|
| 1 | 34 | 35 | 36 | 37 | 38 | 39 | 40 | 41 |
| 2 | — | 445 | 446 | 447 | 448 | 449 | 450 | 451 |
| 3 | — | — | — | 24 199 | 24 200 | 24 201 | 24 202 | 24 203 |
| 4 | — | — | — | 207 995 | 207 996 | 207 997 | 207 998 | 207 999 |

Every row is an arithmetic progression with common difference **exactly 1**.
Compare the same rows as published in `transforms-assessment.md` §2.3, where
the spreads are quoted as 1.162×, 1.210×, 1.038×, 1.010× — all of that was
scheduling noise.

**Determinism controls:** `det_n10_L29` vs `det_n10_L29_r2` and `det_n13_L41`
vs `det_n13_L41_r2` are **byte-identical** dump directories (`diff -r`).

### 4.2 The published residual was scheduling noise — the control that was missing

The `0.9936` figure in `lowmem-endgame-assessment.md` §6.1 was never compared
against a same-`n` repeat run. It should have been. Multi-threaded, same
binary, level 4:

| comparison | `|A\B|` | `|B\A|` | Jaccard | bound disagreements |
|---|---|---|---|---|
| **control**: n = 9 run *a* vs n = 9 run *b* | 961 | 695 | 0.992081 | 225 |
| **signal**: n = 9 vs n = 13 (four ambient steps) | 1013 | 581 | 0.992373 | 182 |

The cross-ambient comparison is **as good as or better than** the same-ambient
repeat. The residual is entirely thread-scheduling nondeterminism, and it
vanishes when the worker count is pinned (§4.1). The non-shared keys are
unstructured — spread over widths 5–8 in proportion to the population, with no
concentration at any width or bound — which is what noise looks like and is not
what a leak would look like.

The only *structured* difference is the one Lemma L predicts: in the n = 13
dump, widths 10, 11, 12, 13 each carry exactly one extra state.

### 4.2a Level 5, multi-threaded — the same comparison at 50 M states

The published `0.9936` is a level-4 multi-threaded figure, so the directly
comparable level-5 measurement is also multi-threaded
(`compare-big`, n = 13 `--limit 42` vs n = 12 `--limit 38`):

| width | \|A\| | \|B\| | \|A∩B\| | \|A\B\| | \|B\A\| | Jaccard | bnd≠ |
|---|---|---|---|---|---|---|---|
| 5 | 9 884 | 9 893 | 9 878 | 6 | 15 | 0.997879 | 0 |
| 6 | 1 040 363 | 1 045 354 | 1 038 154 | 2 209 | 7 200 | 0.991018 | 330 |
| 7 | 17 441 293 | 17 548 614 | 17 370 309 | 70 984 | 178 305 | 0.985852 | 14 280 |
| 8 | 26 473 582 | 26 636 374 | 26 282 551 | 191 031 | 353 823 | 0.979690 | 22 402 |
| 9 | 5 559 504 | 5 582 093 | 5 500 397 | 59 107 | 81 696 | 0.975040 | 3 474 |
| 10 | 76 699 | 78 318 | 76 699 | **0** | 1 619 | 0.979328 | 14 |
| **11** | **1 444** | **1 444** | **1 444** | **0** | **0** | **1.000000** | 2 |
| 12 | 1 | 1 | 1 | 0 | 0 | 1.000000 | 0 |
| 13 | 1 | 0 | 0 | **1** | 0 | — | — |
| TOT | 50 602 871 | 50 902 191 | 50 279 533 | 323 338 | 622 658 | **0.981533** | 40 502 |

Three things to read off this, in order of importance.

1. **The asymmetry is exactly a work difference, to the state.**
   `|B\A| − |A\B| = 622 658 − 323 338 = 299 320`, and
   `|B| − |A| = 50 902 191 − 50 602 871 = 299 320`. Identical. Run B simply
   explored 0.59 % further before its root bound closed; `|B\A| > |A\B|` at
   *every* width. That is the signature of search progress, not of structure.
2. **The two widths Theorem E pins are pinned exactly.** Width 11 — the
   population front at level 5 — is `1 444` states on both sides with **zero**
   non-shared keys, and width 12 is the single chain cube on both sides.
   Meanwhile widths 6–9, the interior, differ by 0.5–2.5 %. The structural
   content is exact; the noise is confined to the interior, where search order
   decides how far a run got.
3. **Clause 2 of Lemma L holds:** the one key in `A\B` at width 13 is
   `cube_13`.

### 4.2b The level-5 control — the decisive comparison

The control the published figure omitted, run at level 5: the *same* ambient,
the *same* binary, twice.

| level-5 comparison | \|A\B\| | \|B\A\| | **Jaccard** | bound ≠ |
|---|---|---|---|---|
| **control** — n = 13 `-l 42` run *a* vs run *b* | 291 022 | 716 170 | **0.980374** | 33 034 |
| signal — n = 13 `-l 42` vs n = 12 `-l 38` | 323 338 | 622 658 | **0.981533** | 40 502 |
| signal — n = 12 `-l 38` vs n = 11 `-l 34` (front pair) | 435 966 | 128 496 | **0.988939** | 29 167 |

**Both cross-ambient comparisons agree better than two runs of the same
ambient agree with each other.** There is no cross-ambient signal to explain;
the residual is thread-scheduling noise whose size is set by how far each run
happened to get before its root bound closed.

Three further details worth recording:

* The width-10 asymmetry (`|A\B| = 0`, `|B\A| = 1 619`) that looks structural
  in the signal row appears **identically in the control** (`0` vs `2 234`).
  It is an artefact of one run having explored further, not of ambient.
* **Width 11 is `1 444` states with zero non-shared keys in all three
  comparisons**, control included. Theorem E's front is pinned exactly while
  the interior fluctuates by 1–2.5 %.
* Every bound difference is a *weakening*, never a contradiction: the
  histogram is dominated by ±1 and both values are sound lower bounds on the
  same quantity, so the `max`/`min` merge of `lowmem` §6.1 remains correct.

The lower Jaccard at level 5 than level 4 (0.98 vs 0.99) is a multi-threading
effect that grows with run length, not evidence against the identity: §4.1
shows the residual is **zero** once the worker count is pinned.

> **Answer to the brief's question (b) — "are the non-shared keys exactly the
> width-n states Lemma L predicts, or is there leakage?"** Neither. The
> width-n states Lemma L predicts *are* present and correct (clause 2 passes
> everywhere). The remaining non-shared keys are **not leakage**: they are
> reproduced in full by a same-ambient repeat, and they vanish entirely under
> pinned scheduling. Question (c), bound agreement on shared keys, has the
> same answer: 40 502 disagreements cross-ambient against 33 034 for the
> control, all weakenings, all zero when pinned.

### 4.3 Theorem E's a-priori prediction, checked afterwards

`census det_n13_L38 det_n13_L39 det_n13_L40` (ambient 13, levels 1, 2, 3):

| width | ℓ = 1 | ℓ = 2 | ℓ = 3 |
|---|---|---|---|
| 3 | 4 | 4 | 4 |
| 4 | 10 | 29 | 49 |
| 5 | **19** | 101 | 951 |
| 6 | 1 | 161 | 7 548 |
| 7 | 1 | **150** | 14 231 |
| 8 | 1 | 1 | 1 290 |
| 9 | 1 | 1 | **126** |
| 10–13 | 1 each | 1 each | 1 each |
| total | 41 | 451 | 24 203 |

Population front at width **5, 7, 9** for ℓ = 1, 2, 3 — exactly
`n_min(ℓ)` from §3.6, predicted before the census was computed. Every width
above the front holds exactly one state, at lower bound `C(w) + ℓ`
(`chain` subcommand: all OK for n = 6, 9, 13 at level 1 and n = 9…13 at
level 4).

**Level 5, the sharpest instance** (`n = 13 --limit 42`, 50,602,871 states,
9 m 07 s under contention, result 42). `n_min(5) = 11`, so the prediction is:
front at width 11, and widths 12 and 13 hold exactly one state each.

| width | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | **11** | **12** | **13** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| states | 5 | 95 | 9 884 | 1 040 363 | 17 441 293 | 26 473 582 | 5 559 504 | 76 699 | **1 444** | **1** | **1** |

Confirmed: the front is at width 11 and the two widths above it are pure
chain, at bounds `C(12)+5 = 38` and `C(13)+5 = 42`. Note the independent
corroboration: `lowmem-endgame-assessment.md` §6.2 reports, from a separate
campaign, that **1,446** states at level 5 have width ≥ 11 —
and `1444 + 1 + 1 = 1446`, exactly.

The mass peak also moves w7 → w8 between levels 4 and 5, confirming the
travelling-wave mechanism of `transforms-assessment.md` §2.5 directly from a
width census rather than by inference.

### 4.4 Theorems B and C, checked directly

**Theorem C.** For `k = 6, 9, 11, 13`, all `C(k,2)` = 15 / 36 / 55 / 78
comparators applied to `cube_k` give **one** distinct canonical key, of size
`|X| = 48 / 384 / 1536 / 6144 = 3·2^{k-2}`. PASS.

**Theorem B.** The single width-`w` state in the ambient-13 level-4 dump is
byte-equal to `canon-key w --prefix ""` (the canonical full cube) for
`w = 10, 11, 12, 13`, with `|X| = 2^w`; and the width-`w` chain key is
identical across every ambient that contains it (`w = 10` across
n = 10, 11, 12, 13; `w = 11` across n = 11, 12, 13). PASS.

### 4.5 The boundary of Lemma L is non-existence, not disagreement

Theorem E holds for every `n ≥ n_min(ℓ)`. Below `n_min(ℓ)` the level does not
exist, so there is no pair of runs that both reach level ℓ and disagree — the
lemma cannot fail by contradiction, only by unavailability. Checked directly
(deterministic, base build): a run asked for a level above its own `D(n)`
saturates at exactly `C(n) + D(n)`.

| run | asks for | returns | = |
|---|---|---|---|
| `n=6 --limit 13` | level 2 | **12** | `C(6)+1`, `D(6)=1` |
| `n=7 --limit 17` | level 3 | **16** | `C(7)+2`, `D(7)=2` |
| `n=8 --limit 20` | level 3 | **19** | `C(8)+2`, `D(8)=2` |
| `n=7 --limit 16` | level 2 | 16 | reachable |
| `n=8 --limit 19` | level 2 | 19 | reachable |

This is the exact sense in which level 7 is unreachable below width 13, and it
is the whole content of §7.

### 4.6 The `MAX_CHANNELS` build gate changes no reachable value

`sortnetopt-det-base` (`MAX_CHANNELS = 11`) and `sortnetopt-det-wide13`
(`MAX_CHANNELS = 13`) produce **byte-identical dump directories** at
`n = 9 --limit 25` and `n = 11 --limit 33`. The limits campaign established
this for the *final bound* and the *emitted certificate bytes*
(`evidence/v3/limits/report.md` verdict 1); it now holds for the *entire
stored state set and every stored bound*. This is the empirical half of
Corollary A2 and the direct justification for tier-slicing in §6.

---

## 5. Caveats, and the one genuine ambient leak

### 5.1 The measurement patch

`.build/v3-ambient-source/` is a copy of the 11-patch stack with one
measurement-only change in two places
(`src/thread_pool.rs:354`, `src/search/states.rs:192`): the worker count and
the shard count are read from `SORTNETOPT_POOL_THREADS`, falling back to
`num_cpus::get()`. With the variable unset the binary is behaviourally
identical to the unpatched one (verified: same final bound). This is a
12th patch and it exists only to remove scheduling noise from the
measurement; it is not proposed for the stack.

### 5.2 Search order is ambient-dependent in principle, but not in fact

The thread-pool priority key includes the recursion `level`
(`search.rs:930`), and a width-`w` subproblem sits `n − w` levels deeper at
ambient `n`. This is a genuine ambient-dependent influence on **search order**.
Empirically it perturbs nothing: the level-1…4 dumps are bit-identical across
ambients. It is worth restating that Theorem E is a statement about the
*explored set*; Theorems A and A1 — which are what the slice scheme rests on —
are statements about *semantics* and are immune to search order entirely.

### 5.3 The leak: `SUBSUME_WIDTHS` defaults to `{n−3, n−2}`

`StateMap::new(root_channels)` builds the on-line subsumption index at widths
`root_channels − 3` and `root_channels − 2` unless
`SORTNETOPT_SUBSUME_WIDTHS` overrides it (`states.rs:217-235`). The resulting
table is *stored* in the `StateMap` and then read **inside the recursion**, by
two methods `improve` calls on every visit:

* `StateMap::get` (`states.rs:577-593`) — in `WriteRead` mode and above, an
  exact-key miss may **raise `bounds[0]`** from a subsuming entry;
* `StateMap::set_inner` (`states.rs:644-688`) — in `Write` mode and above may
  raise `bounds[0]`, and in `Evict` mode **removes** memo entries.

So the leak is not confined to eviction: it changes *stored values* from
`Write` mode upward. Therefore:

> With the on-line subsumption index enabled under the default width policy,
> **Theorem A is false and Lemma L is false**: at ambient `n` the states
> evicted are those at widths `n−3, n−2`, which is a different set of widths at
> every ambient. Two runs at different ambients then hold genuinely different
> memo tables (still sound — subsumption only removes dominated entries — but
> not equal).

The fix is one line of policy, not code: **pin `SORTNETOPT_SUBSUME_WIDTHS` to
absolute widths** in every job of a sliced campaign. This restores Theorem A
exactly. It also gives a theoretical footing to the limits report's empirical
recommendation that "`SUBSUME_WIDTHS` should follow the bound, not be fixed at
launch" — the correct rule is "follow the *level*, which is ambient-free",
never "follow the root width, which is not".

All results in §4 are in the default `SubsumeMode::Off` regime.

### 5.4 What is *not* claimed

Theorem E is proved for the engine as it stands, given the seeded
`known_bounds` table. It is a statement about `Reach`, the set of states the
engine stores — not about the abstract reachable set of the DP, which is
larger. And `D(13)` is not known; every statement above is about levels
`ℓ ≤ 6`, where `D` is known from `S(3..12)`.

---

## 6. The slice scheme, honestly priced

Corollary A2 (width closure) gives a sound decomposition, and it is *not* the
one the brief anticipated. Since the transition relation never increases width,
the width-`≤ w` part of any computation is forward-closed and can run in a
`MAX_CHANNELS = w` build.

**Three tiers.**

| tier | build | holds | entered from |
|---|---|---|---|
| T13 | `wide13` (`PackedSet = [u64;128]`) | the width-13 cone of `s_13` | root only |
| T12 | `wide12` (`[u64;64]`) | width-12 states | `Prune` edges from T13 |
| T≤11 | default (`[u64;32]`) | everything at width ≤ 11 | `Prune` edges from T12 |

**Boundary exchange.** The only cross-tier edges are width-decreasing
`Prune` edges. Tier `k` hands tier `k−1` a list of canonical width-`(k−1)`
keys; tier `k−1` returns `(key, bounds)` pairs. That is *exactly* the read-only
seed-import path already specified as the one blocking change in
`lowmem-endgame-assessment.md` §6.3(2) — `SORTNETOPT_BOUND_SEED`
(`search.rs:92-105`, `checkpoint::import_bound_seed`), which merges by
`max`/`min` and refuses contradictions. Corollary A1 is its soundness proof.
Volume bound: each width-`k` state has at most `2k` prune-children before
canonicalisation, so `|boundary(k → k−1)| ≤ min(2k·|W_k|, |W_{k-1}|)`.

**Certificate transport — assessed.** The v2/v2p container is
*representationally* ready and *procedurally* not. In its favour: byte 0 of
every step payload is that step's **own** width, sets are never padded to the
root width (`certificate-format-v2.md` §2.1), and the Huffman step already
steps width down (`get_bound(steps, w, channels-1, pruned)`,
`tools/cert_v2.py:321`) — which is precisely the tier-boundary edge. So a
tier-`k−1` sub-DAG is valid verbatim inside a tier-`k` proof. Against it:
witness ids are **file-local** and must satisfy `w < s`
(`certificate-format-v2.md:111-113`), there is no cross-file witness namespace,
and `get_bound` requires witness width to equal target width *exactly*
(`cert_v2.py:287`, `Checker.thy:425-445`) with **no widening rule**. The
consequence for this scheme is mild and worth stating precisely: because the
tiers are naturally topologically ordered (T≤11 before T12 before T13), the
composition is a **concatenation with a constant id offset per tier**, which
preserves `w < s` by construction. No new checker rule is needed — only an
out-of-band merge-and-renumber tool. That is a materially easier obligation
than the general "cite a lemma from another certificate" problem, and it is
worth recording that the tier decomposition is the *one* decomposition shape
the existing format composes without a `Checker.thy` change.

The existing composition machinery (`class_campaign.py verify`, §9.6 of the
format) composes *whole prefix jobs at one fixed `(n, L)` by `min`* and is
unverified Python outside every checker
(`verified-checker-extension.md:438-442`). It is not a transport for
individual memo entries, and the seed-import justification obligation
(`lowmem` §6.3(3)) remains unpaid: nothing in the format expresses "this bound
was imported". Corollary A1 makes the imported bound *sound*; it does not make
it *justified*, and `GenProof::prove_all` panics on unjustified retained sets
(`src/proof.rs:137`). Recording justifications at derivation time remains the
required engine change, exactly as `lowmem` §6.3 says.

**Soundness conditions for composition.** (i) Each tier reports only
`bounds`, never `huffman_bounds` (an internal headroom memo, not a property of
the set) — the existing import path already enforces this. (ii)
`SUBSUME_WIDTHS` pinned per §5.3. (iii) Certificate obligation: imported
bounds have no in-run justification, so per-job certificates must be composed.
This is required regardless — `proof.rs` step ids are `u32`, capping a
certificate at 4.29e9 steps against an n = 13 estimate around 1.5e11, so
composition is on the critical path with or without slicing.

**What it is worth — measured, not estimated.**

| lever | factor | source |
|---|---|---|
| removes the `wide13` build tax from tiers T12 and T≤11 | **1.3 % (evict) – 6.7 % (plain)** | `evidence/v3/limits/report.md` verdict 1 |
| removes the `wide12` tax from tier T≤11 | **2.1 – 2.7 %** | same |
| `Edges` per-frame transient (one dense `2^n`-byte bitmap per successor) | 640 KB @ n=13 → 110 KB @ n=11 = **5.8×** | `sortnetopt-internals.md` §2.5 |
| memo bytes per state | **1.00× (no change)** | §1 — storage is already width-optimal |
| cross-job memo sharing | already ~99.9 % effective; now **proved** rather than measured | §3.1, `lowmem` §6.1 |

So the slice scheme is real, sound, and cheap to build on top of machinery that
already exists — and it is worth a **few per cent of wall time plus up to
5.8× on transient frame memory**, not an order of magnitude. It does not
reduce the state count, which is what binds.

---

## 7. Level 6 — the one place this campaign changes a decision

`n_min(6) = 11`. So Theorem E says, exactly:

> `Reach(13, 6) = Reach(11, 6) ⊎ { cube_12, cube_13 }`.

The level-6 census at n = 13 **is** the level-6 census at n = 11, plus two
states. Three consequences, all actionable:

1. **The decisive experiment is de-risked.** `lowmem` §11 Step 0 and
   `transforms` §2.4(4) both nominate `n = 11 --limit 35` as the cheapest place
   to measure level 6, on the strength of a census that agreed "to within
   1.4 %". It is not an approximation to the n = 13 level-6 cost — it is that
   cost, exactly. The residual risk that "n = 11 might not be representative"
   is now zero, and 11 is provably the *minimum* ambient (level 6 does not
   exist at n ≤ 10; §4.5).
2. **It needs no wide build.** Width ≤ 11 throughout, so `n = 11 --limit 35`
   runs in the **default `MAX_CHANNELS = 11` binary** — no `wide12`/`wide13`
   tax, smaller transient buffers, and §4.6 shows the base build reproduces
   the wide build's state set byte for byte.
3. **It self-checks.** Level 6 is `D(11)`, so the run terminates with
   `result = 35` and the certificate is checkable by the frozen `snocheck`.

Nothing else in this document changes a decision. This does.

---

## 8. The level-7 arithmetic, and the go/no-go

The brief asked whether ambient reduction moves level 7 into "weeks on the
owned server + M4". **It does not**, and Theorem E says why in one line:

> `n_min(7) = 13`. Level 7 does not exist at any ambient below 13.

`D(12) = S(12) − C(12) = 39 − 33 = 6`. Asking ambient 12 for level 7 asks for
a lower bound of 40 on a quantity that is 39; the search closes at 39 and stops
(§4.5 shows exactly this behaviour at n = 6, 7, 8). This is not a limitation
of the method — it is the reason level 7 has never been computed at any width,
restated as a theorem. `transforms-assessment.md` §2.4(1) reached the same
conclusion empirically; Theorem E now identifies the obstruction precisely:

> Level 7 is the single subproblem "**`s_13` needs at least 43 more
> comparators**", where `s_13 = canon(cube_13 ▷ [i,j])` is the unique
> width-13 successor of the full cube, `|s_13| = 6144` (Theorem C). Every
> other part of a level-7 computation has a smaller-ambient counterpart;
> the cone of `s_13` does not.

(That is also, reassuringly, exactly the object the prefix-decomposition
campaigns already target: prefix `1-0` *is* `s_13`.)

### 8.1 What each lever contributes

| lever | factor on level-7 **states** | factor on **wall** | factor on **disk** | status |
|---|---|---|---|---|
| ambient reduction (this document) | **1.00×** | ~0.95–0.99× | **1.00×** | proved |
| suffix / endgame filters | **1.000×** (measured, zero successors excluded) | 1.000× | 1.000× | `endgame-theory.md` §0, §7.2 — KILL |
| shared bound oracle / seeding from level 6 | ≤1.03× (level 6 is 1/33–1/246 of level 7) | same | same | proved sound here |

### 8.2 The composed estimate

Level-7 bracket, taken from the measured level-5 anchor (50,922,864 states at
n = 13 `--limit 42`) times the measured per-level multipliers
(12.49 / 46.11 / 8.36 / 245.89, geometric mean 33.0×), as computed in
`endgame-theory.md` §7.2 and `lowmem` §9.3:

| case | states | disk | M4-days @ 1.5e5 states/s |
|---|---|---|---|
| floor multiplier (33×/level) | 5.55e10 | **2.4 – 3.2 TB** | 4.3 |
| geometric scenario | 5.5e10 | 3.5 TB | 3.8 |
| alternating scenario | 7.6e11 | 48 TB | 52 |
| ceiling multiplier (246×/level) | 3.08e12 | **136 – 195 TB** | 209 – 238 |

Available hardware: the server has **47 GiB RAM and ~324 GiB free disk**
(itself unverified, per `lowmem` §2.3); the M4 has 16 GiB RAM, ~24 GiB free
disk and a **~6 GB practical RSS ceiling** (`probe13-43-addendum`). Throughput
is a hardware constant near 1.5e5 states/s — Harder's 24c/48t EPYC measured
141,059 states/s against the M4's 170,882, so "a 4.8× core count buys nothing"
(`lowmem` §2.1).

**The binding wall is disk, and it is not close.** The floor case needs
2.4 TB against 324 GiB available — short by **7.4×** — and the ceiling case is
short by **600×**. Wall time is comfortable in the floor case (4.3 M4-days)
and prohibitive in the ceiling case (238 M4-days). Applying every factor in
§8.1 moves 4.3 days to 4.1 days and 2.4 TB to 2.4 TB.

> **Go/no-go: NO.** Level 7 is not reachable in weeks on the owned server plus
> the M4, and ambient reduction does not change that by any measurable amount.
> The gap is 7.4×–600× in *storage*, which is the one resource none of the
> promoted families reduce (memo bytes per state are already width-optimal,
> §1). Nothing in this campaign should be read as moving the go/no-go.

### 8.3 A correction to the brief's figures

The brief quotes a level-7 bracket of "3.1–23G states, 150 GB–1.2 TB". **Those
numbers do not appear anywhere in this repository** (a full grep for `3.1e9`,
`2.3e10`, `150 GB`, `1.2 TB` returns nothing). The repo's level-7 state
bracket is **5.55e10 – 3.08e12**, i.e. roughly **20× to 130× larger** than the
brief's low figure, and its disk bracket is **2.4 – 195 TB**, i.e. **16× to
160× larger**. The nearest string in the repo is `3.1e12` — the *pessimistic*
level-7 state count — so the brief's figure may be a garbling of that. Any
planning done against "150 GB – 1.2 TB" should be redone; that range is
smaller than the *floor* case by an order of magnitude, and it is the range in
which the owned hardware would have looked adequate.

### 8.4 What actually decides it

The 4-order-of-magnitude bracket above collapses to a single number the moment
level 6 is measured, and §7 shows that measurement is cheaper and safer than
previously believed (base build, ambient 11, provably exact, self-checking).
That remains the single most valuable experiment in the programme, and this
campaign's contribution to the go/no-go is to make it a theorem-backed
measurement rather than a calibration.

---

## 9. Reproduction

```
# the measurement binary (12th patch, env-gated; see §5.1)
cd .build/v3-ambient-source && cargo build --release --features wide13

# deterministic ladders; C(6..13) = 11,14,17,21,25,29,33,37
export SORTNETOPT_POOL_THREADS=1
for L in 38 39 40 41; do
  .build/v3-ambient/bin/sortnetopt-det-wide13 search 13 -l $L .build/v3-ambient/dumps/det_n13_L$L
done   # ... and likewise for n = 6..12 at C(n)+1 .. C(n)+4

# the checks
python3 tools/verify_ambient.py lemma-l .build/v3-ambient/dumps/det_n13_L41 \
                                        .build/v3-ambient/dumps/det_n12_L37
python3 tools/verify_ambient.py census  .build/v3-ambient/dumps/det_n13_L3{8,9} \
                                        .build/v3-ambient/dumps/det_n13_L40
python3 tools/verify_ambient.py chain   .build/v3-ambient/dumps/det_n13_L41

# Theorem C
for p in 1-0 5-2 12-7; do .build/v3-endgame/bin/sortnetopt-wide13 canon-key 13 --prefix $p; done
```
