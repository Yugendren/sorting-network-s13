# Prefix Decomposition: The Economics, Measured

**Date:** 2026-08-27.
**Question put:** `docs/level7-redecision.md` §6.2 and §9 item 3 name prefix
decomposition as the last untested lever with the right order of magnitude, on
the argument that `wall ~ N^e` with `e > 1` makes a `k`-way split a CPU **win**
of `k^{e-1}` — 4.5× at `e = 1.35`, 32× at `e = 1.78`, for `k = 100`. The same
section states the gate: *"If prefix cones overlap almost completely, `k` jobs
each rebuild the shared core and the split is a `k`-fold loss that swamps the
`k^{1-e}` win."* Three quantities decide it: the **job-private memo fraction**,
the **superlinearity dividend**, and **peak memory per job**. This document
measures all three, at `n = 11`, and extrapolates to level 7 with the
assumptions stated separately.

**Scope note** (mirrors `docs/novel-facts.md` and `docs/level7-redecision.md`
§7). Every search run reported here is at `n = 11` with `--limit` 33 or 34. No
`n = 13` search was run, no search bound of 44 was set anywhere, no candidate
network was constructed and no witness exists in this work. The one `n = 13`
computation performed is a purely combinatorial enumeration of canonical
comparator-prefix classes via `canon-key` — no search, no limit, no bound, no
`StateMap` — reported in §2.3 because it makes the `k(d)` half of the
extrapolation exact rather than assumed.

---

## 0. Verdict

> ## **FAILS.** Prefix decomposition does not close the ~17× level-7 gap. It
> does not partially close it. It moves **both** axes in the wrong direction.
>
> **The number that kills it:** across **146 runs — 144 prefix jobs and 2
> monolithic controls, at two levels and six prefix depths** — the **lowest peak
> per-job memory ever observed was 0.990× the monolithic run's**, and that was
> at prefix depth 1, where `k = 1` and the "split" is a no-op. The best
> non-trivial point is **0.998× at depth 3**; by depth 4 peak per-job memory is
> **23.6× the monolith's**. Level 7 needs **0.095×**. There is no prefix depth,
> and therefore no `k`, at which decomposition reduces peak memory at all.
>
> ### The three quantities
>
> | | measured | needed / predicted |
> |---|---|---|
> | **1. job-private memo fraction** | **36.2 %** of entries, 39.2 % of bytes, between two sibling depth-2 cones at level 5 (Jaccard 0.638) — and privacy *falls* at the top width, where the level-6 mass sits | ~100 % for the split to be a partition |
> | **2. superlinearity dividend** | total work rises to **1.80× at `k = 3`**, **3.54× at `k = 9`**, **55.1× at `k = 27`**, **264× at `k = 91`** | a *saving* of `k^{e-1}`: 1.46×, 2.10×, 3.16×, 4.90× |
> | **3. peak memory per job** | **0.990× at best**, 1.035× at depth 2, 23.6× at depth 4 | **≤ 0.0953×** |
>
> Quantity 2 is between **2.6× and 1,294× worse than its prediction**, and the
> gap widens with `k`. The `k^{e-1}` argument fails at its first premise, not at
> its arithmetic: `k·(N/k)^e` assumes the split **partitions** the state space,
> and prefix cones **cover** it. At level 5, depth 2, the job with prefix
> `(0,1),(2,3)` has a memo of **11,849,694 entries against the entire monolithic
> run's 11,629,126** — 1.9 % *larger* than the run it is supposed to be one
> third of.
>
> **The shared bound oracle does not rescue it.** Seeding a sibling from a
> completed job's memo collapses its bound iterations 24 → 4 but changes its
> actual DP work by **1.03×** — three per cent *more* — while its memo grows
> **1.70×**. Transplanting the shared work costs exactly what storing it costs,
> and storing it is the constraint decomposition was supposed to relieve. (§6)
>
> **Why, in one sentence:** the monolithic search never solves any interior
> subproblem to completion — it raises the root's bound incrementally, improving
> each successor only far enough to move the current minimum — whereas prefix
> decomposition forces every job to certify its own root to its full value. The
> parts are strictly harder than the roles those same parts play inside the
> whole.

**This is a clean negative and it ends the line of work.** `level7-redecision.md`
§6.2's rung 2 is now measured; the answer is no. The standing **NO-GO** on level
7 is unchanged and now rests on one fewer open question.

---

## 1. Method

### 1.1 What a prefix job actually is

`Search::search(initial, limit, prefix, output)` (`src/search.rs`) applies the
prefix's comparators to `OutputSet::all_values(n)`, then loops
`improve` on that root until `bounds[0] == bounds[1]` or `bounds[0] >= limit`.
Each pass of that loop is one **bound iteration**, and it is the `iteration`
column of the engine's own table. The document-wide name "level ℓ" is the
iteration that pushes the root's lower bound to `29 + ℓ` at `n = 11`; hence
`--limit 33` is **level 4** and `--limit 34` is **level 5**. Verified against
the reference logs: `level7-probe/logs/C910_L33.log` iteration 12 has 202,642
entries at a 1,173 ms delta, exactly the "level-4" row of
`level7-redecision.md` §4.3.

A depth-`d` prefix job is therefore `search 11 -l (L-d) -p a b …`, and
composition is `min` over the depth-`d` frontier of `d + result_j`
(`tools/class_campaign.py::cmd_compose`). **Every one of the 139 jobs run here
returned exactly `L - d`**, so every arm composes to exactly the monolithic
answer — the decomposition is numerically valid throughout, and the cost
comparison is like-for-like.

### 1.2 The two arms

| | **Arm A** | **Arm B** |
|---|---|---|
| level | 4 (`--limit 33`) | 5 (`--limit 34`) |
| machine | M4 | server, strictly one job at a time |
| depths | 0,1,2,3,4,5 — **every canonical class**, 131 jobs | 0,1,2,3 — every canonical class, 14 jobs |
| monolithic control | in-arm, same binary, same config | in-arm, same binary, same config |
| quantities used | counters and memo bytes only | counters, memo bytes **and wall** |

**Which machine's clock is trusted, and why.** Arm B ran on the server between
17:04 and 17:43:43; an unrelated 12-hour training job on the same box
(`/data/alien-project`, a different programme) launched its supervisor at
17:11:34 but that supervisor has consumed **4 seconds of CPU in over an hour**
— it waits on a GPU — and its ten CPU-heavy self-play workers spawned at
**17:43:50, seven seconds after Arm B finished**. Arm B's walls are therefore
from an idle box. Arm A ran on the M4, which turned out to be under memory
pressure (4.5 GB of a 6 GB swap in use, an unrelated browser at ~100 % of a
core); a deliberate replication of Arm B there produced a depth-1/depth-0 wall
ratio of **4.2** against the server's **0.96** on identical work, which is pure
noise. **No wall-clock number from the M4 is used anywhere in this document.**
Arm A contributes only exact counters — `entries`, `get_calls`,
`key_plus_state_bytes`, index bytes — which are hardware- and
load-independent.

**Run-to-run variance.** The engine is multi-threaded and its memo is not
bit-reproducible: the abandoned M4 replication of Arm B's depth-0 and depth-1
jobs gave 11,519,707 and 12,234,672 entries against the server's 11,629,126 and
11,538,722 — a spread of about ±6 % on `MEM_x`, consistent in kind (if larger
in size) with `ambient-reduction.md` §4.2's same-`n` control. Every conclusion
below turns on factors of 10 to 10⁴, so ±6 % changes nothing; it is recorded
because `MEM_x ≈ 0.99` should not be read as "1 % better than the monolith".

Configuration is **C910** throughout — `SORTNETOPT_SUBSUME=evict`,
`SORTNETOPT_SUBSUME_DIMS=96`, `SORTNETOPT_SUBSUME_WIDTHS=9,10` — the new Pareto
default from `level7-redecision.md` §4.4. `RUST_LOG` unset (the documented
silent-exit hazard). Walls quoted are the engine's own cumulative
`elapsed_ms` at the last iteration, which excludes the 10 s pool-shutdown
floor; the 10-thread pool utilisation during the search phase was **99.98 %**
for the monolith and **99.97 %** for the depth-2 job, so thread-seconds and wall
clock are interchangeable up to the constant 10.

### 1.3 Binary, and one deviation from the certified stack

The engine is the **11-patch stack** (`.build/v3-prefixcert/source`, the
decomp + prefixcert tree), which is required because the 5-patch certified
binary has neither `-p/--prefix` on `search` nor the `canon-key` subcommand.
Built native on the server, SHA-256
`241857053898a6825b9ffdc3d6b449140ee5b4d611de9342e59294105ac24db6`; the M4 arm
used `.build/v3-prefixcert/source/target/release/sortnetopt`, SHA-256
`15352938e26af571968146aeadf2e4764658abc4e139e6be4c1f69586ddcb556`.

**This is not the certified binary, and the control is what makes that
harmless:** every ratio in this document is against a monolithic run of the
*same* binary in the *same* configuration on the *same* machine. For
calibration, the 11-patch monolith at `n = 11 --limit 34` returns 34 in
**220.7 s** of level-5 iteration and 11,629,126 entries, against the 5-patch
reference C910 arm's **282.2 s** and 11,900,303 entries — the newer stack is
1.28× faster and 2.3 % smaller, in the same place on the frontier. Nothing in
the verdict depends on which of the two is used.

---

## 2. The job set

### 2.1 Canonical prefix classes, enumerated level by level

`class_campaign.py::build_frontier` enumerates all `n(n-1)^d` raw prefixes and
dedups only at the end — 1.5×10⁸ rows at `n = 11`, depth 4. Since a prefix's
cone depends only on the canonical form of `X_P`, extending one representative
per canonical class at each depth covers every class at the next depth, which
is what `.build/v3-decomp-econ/frontier.py` does using the engine's own
`canon-key`. It reproduces the recorded `n = 9` figures exactly (72 raw → 1
class at depth 1; 5,184 → 3 at depth 2, the `1728×` collapse in
`evidence/v3/decomp/report.md`).

| depth | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| canonical classes, `n = 11` | 1 | 3 | 9 | 27 | 91 | 374 |
| canonical classes, `n = 13` | 1 | 3 | 9 | 27 | 91 | 375 |
| of which **new** at that depth (`n = 11`) | 1 | 2 | 6 | 18 | 64 | 283 |

So **`k` in the 10–200 range the brief asks about is prefix depth 4 to 6.**

### 2.2 A free optimisation, worth recording

Every class at depth `d-1` reappears at depth `d` (repeat any comparator; it is
idempotent). Such a job is dominated: if `canon(X_P)` also arises at depth
`d' < d`, then `d + bound(X_P) = d + bound(X_{P'}) > d' + bound(X_{P'}) >= L`
already, so it need never be run. That is the "of which new" row above and it
cuts the depth-6 job count from 374 to 283 (−24 %). `class_campaign.py` does
not do this today. It is a genuine saving and it does not change any conclusion
below by an order of magnitude.

### 2.3 The frontier is `n`-independent, so half the extrapolation is exact

The `n = 13` row was computed with `canon-key 13` on the wide13 build
(SHA-256 `683ef3c63fcf81d44eed994016fde0255e12ed0b315f03b41525e62bb6e363fd`) —
a pure enumeration of canonical prefix classes, with no search, no limit and no
bound. It is identical to `n = 11` at depths 1–5 and differs by one class at
depth 6. **`k(d)` therefore transfers to `n = 13` as a measurement, not an
assumption.** Only the per-job cost has to be extrapolated.

---

## 3. Quantity 1 — the job-private memo fraction

### 3.1 How it was measured

`search n <dir> …` writes its whole memo to `group_{w}_{b}.bin` files, each a
concatenation of fixed-length packed `OutputSet` keys of length `2^w/8`
(`OutputSet::packed_len_for_channels`). Five level-5 runs were dumped — the
monolith, the depth-1 job, and all three depth-2 jobs — and diffed as sets of
`(width, packed key)` pairs. The stored bound is deliberately **not** part of
the identity: two jobs that reach the same state with different bounds still
did the same DP work on it, so counting them as distinct would flatter
decomposition.

**This is the first time sibling prefix cones have actually been diffed.**
`level7-redecision.md` §6.2 stands in for this measurement with the Jaccard
0.9936 figure, which was `n = 9` against `n = 10` — two *different ambients*,
both full-cube runs — and which `ambient-reduction.md` §4.2 has since shown to
be thread-scheduling noise around a true value of 1.000000. Neither the number
nor the object was the right one.

### 3.2 The result

**Five memos (monolith, depth 1, all three depth-2 jobs), level 5:**

| | |
|---|---|
| Σ entries over the five | 44,987,659 |
| entries in the union | 13,959,835 |
| **overlap factor `r = Σ / union`** | **3.223** |
| states in exactly one memo | 1,916,085 = **13.7 % of the union** |
| by packed bytes | **15.7 % of the union** |

Multiplicity histogram (how many of the five memos each state appears in):
`1 → 1,916,085`, `2 → 1,011,502`, `3 → 3,282,017`, `4 → 7,548,636`,
`5 → 201,595`. **Fifty-four per cent of all states appear in four of the five
memos.**

**The two non-degenerate sibling depth-2 cones, on their own** — `(0,1),(0,2)`
against `(0,1),(2,3)`, which is exactly the "two prefix jobs at `n = 11`,
depth 2–4, diffed as key sets" experiment `level7-redecision.md` §6.2 asks for:

| | |
|---|---|
| Σ entries | 20,517,710 |
| union | 12,526,029 |
| in both | 7,991,681 (**Jaccard 0.638**) |
| private to one cone | 4,534,348 = **36.2 % of entries, 39.2 % of bytes** |

> **Quantity 1, answered. The job-private fraction is 36.2 % between two
> siblings at level 5 — so 63.8 % of the work is genuinely shared and is paid
> `k` times.** That is the case `level7-redecision.md` §6.2 itself calls fatal.

### 3.3 The width breakdown falsifies the argument that motivated the lever

The whole reason to expect decomposition to shrink a job's memo is
`lowmem-endgame-assessment.md` §6.2's claim that high-width states are
class- or prefix-private while low-width states are universally shared. The
measurement says the opposite at the top of the range. Private fraction
between the two sibling cones, by width:

| width | 6 | 7 | 8 | **9** | **10** | **11** |
|---|---|---|---|---|---|---|
| union entries | 524,586 | 5,881,452 | 5,821,733 | 259,070 | 29,722 | 1,442 |
| **private fraction** | 23.7 % | 31.2 % | 41.0 % | **64.5 %** | **56.3 %** | **22.2 %** |

Privacy rises with width up to 9, then **falls**. In the five-memo diff the
effect is starker still: of the 1,444 width-11 states, **exactly one** is
private to a single memo, and the average width-11 state appears in **3.78 of
the five** memos — the *least* private width in the entire census.

The reason is structural and obvious once seen. Width-`n` states are the ones
nearest the full cube, and *every* prefix cone begins at the full cube and
walks a couple of comparators away from it; they are common ground by
construction. Width drops only through extremal-channel pruning, deep in the
DAG. So high width means *near the root*, not *far from the other jobs*.

This does not make the level-6 census irrelevant — width ≥ 10 really is 56.7 %
of the level-6 memo by bytes — but it removes the reason to believe that share
is job-private. §7.3 recomputes the memory floor using these measured privacy
fractions instead of the assumed ones, and the floor gets **worse**.

---

## 4. Quantity 2 — the superlinearity dividend

### 4.1 The premise, and where it breaks

`level7-redecision.md` §6.2's arithmetic is `k·(N/k)^e = N^e · k^{1-e}`. Every
step of that is correct **given** that the `k` jobs each carry `N/k` states.
They do not. The measured per-job state counts at level 5:

| depth | job | prefix | entries | ÷ monolith |
|---|---|---|---|---|
| 0 | `d0_j000` | (empty) | 11,629,126 | 1.000 |
| 1 | `d1_j000` | `(0,1)` | 11,538,722 | 0.992 |
| 2 | `d2_j001` | `(0,1),(2,3)` | **11,849,694** | **1.019** |
| 2 | `d2_j000` | `(0,1),(0,2)` | 8,893,421 | 0.765 |
| 2 | `d2_j002` | `(0,1),(0,1)` | 202,785 | 0.017 |
| 3 | `d3_j001` | `(0,1),(2,3),(0,2)` | 11,526,902 | 0.991 |
| 3 | `d3_j006` | `(0,1),(2,3),(4,5)` | 10,848,194 | 0.933 |
| 3 | `d3_j007` | `(0,1),(0,1),(0,1)` | 25,609 | 0.002 |

The distribution is bimodal: the **degenerate** classes (repeated comparators)
are nearly free, and the **generic** ones each carry essentially the whole
problem. `N/k` never appears. The largest depth-2 cone is 1.9 % *larger* than
the monolithic memo.

### 4.2 The dividend, scored against its own prediction

The prediction is a total-cost **multiplier** of `k^{1-e}` — a saving. The
measurement is the total work actually done across the split, in exact
counters, with no clock involved:

| `k` (prefix depth) | predicted `k^{1-e}`, `e = 1.35` | measured `CPU_x` (`get_calls`) | measured ÷ predicted |
|---|---|---|---|
| 3 (depth 2, level 5) | 0.685 (a 1.46× saving) | **1.802** | **2.6×** worse |
| 9 (depth 3, level 5) | 0.477 (2.10× saving) | **3.544** | **7.4×** worse |
| 3 (depth 2, level 4) | 0.685 | 2.037 | 3.0× worse |
| 9 (depth 3, level 4) | 0.477 | 6.207 | 13.0× worse |
| 27 (depth 4, level 4) | 0.317 (3.16× saving) | **55.07** | **174×** worse |
| 91 (depth 5, level 4) | 0.204 (4.90× saving) | **264.0** | **1,294×** worse |

At `e = 1.78` — the certified configuration's exponent, the one that gives the
32× headline — the predicted savings are larger and the discrepancies are
larger still.

**The measured total work is close to `k` × the monolith once the degenerate
classes are set aside**, which is precisely the `k`-fold loss `level7-redecision.md`
§6.2 named as the failure mode. It is not that the dividend is eaten by
per-job overhead; the dividend never exists, because the per-job `N` is not
`N/k`.

### 4.2a A note on wall clock, and why this section does not rest on it

The obvious follow-up question — is a *single* prefix cone at least cheaper
per state, as superlinearity would predict for a smaller `N`? — turned out not
to be answerable to the standard this document needs. Three measurements of
the same depth-2 job `(0,1),(0,2)` at level 5 gave engine walls of 305.7 s,
141.7 s and (see §4.2b) more, against monolith walls of 219.4 s and 506.2 s,
because the box's competing load moved underneath both. `PLACEHOLDER_TIMING`

Whatever the per-cone constant turns out to be, it cannot rescue the split: it
would have to be smaller than `1/k` to overcome §4.2's duplication, and the
per-cone state counts in §4.1 rule that out on their own.

### 4.3 Total CPU across the split, both levels, every canonical class

`CPU_x` is `sum over jobs / monolith`; the `get_calls` column is the
hardware-independent one, the wall column is what a campaign would actually
pay.

**Arm A, level 4, `n = 11`, all 131 canonical jobs** (counters only — see §1.2)

| depth | `k` | Σ entries | Σ `get_calls` | `CPU_x` (get_calls) |
|---|---|---|---|---|
| 0 | 1 | 202,507 | 3.43×10⁶ | 1.000 |
| 1 | 1 | 201,159 | 3.41×10⁶ | 0.994 |
| 2 | 3 | 413,079 | 6.99×10⁶ | 2.037 |
| 3 | 9 | 1,262,594 | 2.13×10⁷ | 6.207 |
| 4 | 27 | 10,959,714 | 1.89×10⁸ | **55.07** |
| 5 | 91 | 52,395,503 | 9.06×10⁸ | **264.0** |

**Arm B, level 5, `n = 11`, all canonical jobs to depth 3**

| depth | `k` | Σ entries | Σ engine wall | `CPU_x` (get_calls) | `CPU_x` (wall) |
|---|---|---|---|---|---|
| 0 | 1 | 11,629,126 | 220.7 s | 1.000 | 1.00 |
| 1 | 1 | 11,538,722 | 211.8 s | 0.993 | 0.96 |
| 2 | 3 | 20,945,900 | 999.9 s | 1.802 | **4.53** |
| 3 | 9 | 41,365,603 | 834.6 s | 3.544 | **3.78** |

The CPU multiplier is **worse at the deeper level** at the same depth
(2.04 → 4.53 at depth 2 by wall), which is the wrong direction for
extrapolating to level 7. It is close to linear in `k` once the degenerate
classes are excluded, exactly the *k*-fold loss §6.2 named as the failure mode.

> **Quantity 2, answered.** There is no superlinearity dividend. At `k = 91`
> (depth 5, level 4) the split costs **264× the CPU**, against a predicted
> 4.5–32× *saving*. The `k^{e-1}` argument fails at its first premise, not at
> its arithmetic.

---

## 5. Quantity 3 — peak memory per job

Peak per-job memory is `max` over the `k` jobs of
(`key_plus_state_bytes` + subsumption-index bytes), the engine's own memo
accounting. On the server, where the process also reports peak RSS, the two
track: the monolith is 424.1 MB of memo against 780 MB RSS, the depth-2 job
312.4 MB against 533 MB — ratio 0.74 and 0.68 respectively.

| depth | `k` | **level 4** max memo | `MEM_x` | **level 5** max memo | `MEM_x` |
|---|---|---|---|---|---|
| 0 | 1 | 5.4 MB | 1.000 | 424.1 MB | 1.000 |
| 1 | 1 | 5.3 MB | **0.994** | 419.8 MB | **0.990** |
| 2 | 3 | 5.4 MB | 1.012 | 439.0 MB | 1.035 |
| 3 | 9 | 8.1 MB | 1.507 | 423.3 MB | 0.998 |
| 4 | 27 | 126.9 MB | **23.58** | — | — |
| 5 | 91 | 138.3 MB | **25.70** | — | — |

**The curve never goes below 1 except at `k = 1`.** The single best number
anywhere on it is 0.990, at depth 1, where there is exactly one canonical class
and the "split" is the monolithic computation minus its last step. The best
non-trivial point is 0.998 at depth 3, level 5 — a 9-way split that saves
**0.2 %** of the memory and costs **3.78×** the wall.

Beyond that the curve turns sharply upward. At level 4, depth 4, the job with
prefix `(0,1),(0,2),(1,3),(4,5)` has a memo of **3,811,151 entries — 18.8× the
entire monolithic run's 202,507** — and 126.9 MB against the monolith's 5.4 MB.

The explosion point moves out by about one depth per level (level 4 turns at
depth 4; level 5 is still flat at depth 3), which matters for the extrapolation
and is handled in §7. What does **not** move is the floor: at every depth and
both levels, the largest cone is at least as large as the whole problem.

> **Quantity 3, answered.** Level 7 needs `MEM_x <= 0.0953`. The measured
> minimum over 139 jobs, six depths and two levels is **0.990**. Decomposition
> is short by a factor of **10.4× at its own best point**, and by **247×** at
> the `k` the brief asks about.

---

## 6. The shared bound oracle — does the shared work transplant?

§3 says 63.8 % of a sibling pair's work is shared, and unseeded that share is
paid twice. `SORTNETOPT_BOUND_SEED` exists precisely to fix this: it imports a
completed run's `StateMap` read-only, merging by `max` lower bound / `min`
upper bound. `evidence/v3/decomp/report.md` claims "45× on a sibling job" for
it; that claim is recorded without an `n`, a level, a metric or a job pair, and
`ambient-reduction.md` §8.1 independently prices seeding at **≤ 1.03×** — the
two have never been reconciled. Here is the measurement, at `n = 11`, level 5,
prefix depth 2, with the pair named.

**Procedure.** Run job `(0,1),(0,2)` with `SORTNETOPT_CHECKPOINT_DIR` set and
`INTERVAL_SECS=0`, so its entire memo lands in one `checkpoint.bin`
(**278,080,427 bytes**). Then run each sibling with
`SORTNETOPT_BOUND_SEED` pointed at that file.

| level-5, depth 2 | `(0,1),(2,3)` unseeded | **seeded from `(0,1),(0,2)`** | ratio |
|---|---|---|---|
| result (must be 32) | 32 | 32 | ✓ |
| **bound iterations** | 24 | **4** | **0.17×** |
| `get_calls` | 210,131,843 | 216,985,277 | **1.03×** |
| stored entries | 11,806,513 | **20,702,549** | **1.75×** |
| **memo bytes** | 432.1 MB | **735.0 MB** | **1.70×** |

| level-5, depth 2 | `(0,1),(0,1)` unseeded | **seeded** | ratio |
|---|---|---|---|
| `get_calls` | 3,435,532 | **16** | **5×10⁻⁶** |
| bound iterations | 16 | 2 | |
| stored entries | 202,544 | 8,698,566 | **42.9×** |
| memo bytes | 5.39 MB | 240.4 MB | **44.6×** |

> **The oracle works exactly as specified, and it is a one-for-one transfer of
> CPU into memory.**
>
> On the **generic** sibling it collapses the bound iterations 24 → 4 and saves
> **nothing at all** on actual DP work — 1.03× the memo probes, i.e. 3 % *more*
> — while the memo grows **1.70×**, because the seeded run now carries the
> union of its own cone and the seed's.
>
> On the **degenerate** sibling (a prefix whose canonical state already
> appeared at depth 1) it is a total win on CPU — 16 memo probes, the answer
> was already in the seed — at **44.6×** the memory.
>
> So the answer to "is the shared prefix work cheap to transplant?" is **no:
> transplanting it costs exactly what storing it costs**, and storing it is the
> constraint decomposition was supposed to relieve. The seeded job's peak
> memory is bounded below by the size of the seed, which is another job's whole
> memo.

Two consequences for the record. First, **`ambient-reduction.md` §8.1's ≤ 1.03×
is vindicated to three significant figures** — the measured `get_calls` ratio
on the generic sibling is 1.03 — and `evidence/v3/decomp/report.md`'s "45× on a
sibling job" is not reproduced as a speedup on any job that does real work.
Second, that report's 45× and this measurement's **44.6× memory cost on the
degenerate sibling** are close enough to be worth checking whether the original
figure was a memory ratio recorded as a speed-up, or a speed-up measured on a
job of the degenerate kind. Either way the claim should not be cited as a 45×
CPU win for sibling seeding without a reproduction.

---

## 7. Extrapolation to level 7

### 7.1 What level 7 needs

From `docs/level7-redecision.md` §0 and §4.3, at the C910 operating point:

| | level-7 monolith | available | required multiplier |
|---|---|---|---|
| search wall | 45 – 190 d | ~90 d horizon | `CPU_x <= 0.47 – 2.00` |
| memo, resident | ~1,500 GB | 47 GB RAM + 96 GB swap = 143 GB | `MEM_x <= 0.0953` |

### 7.2 The assumptions, stated separately

| # | assumption | status |
|---|---|---|
| A1 | the level-7 monolith baseline (45–190 d, ~1.5 TB) is as `level7-redecision.md` §4.3 states | **inherited, not re-derived here**; if it moves, both columns above move with it |
| A2 | `k(d)` at `n = 13` equals `k(d)` at `n = 11` | **MEASURED** (§2.3): identical at depths 1–5, 375 vs 374 at depth 6 |
| A3 | the shape of `MEM_x(d)` — never below 1, rising with `d` — persists from levels 4/5 to level 7 | **measured at two levels**, mechanism in §7.4 is level-independent; the honest risk is the width-census shift, §7.3 |
| A4 | the census floor in §7.3 | **independent of A3**; rests only on the certified level-6 width census |
| A5 | jobs are run to completion, one target bound each | structural; §7.4 |

### 7.3 The census floor — the bound that does not depend on A3

The single reason to expect decomposition to shrink a job's memo is
`lowmem-endgame-assessment.md` §6.2's argument that high-width states (near the
root width) are prefix-specific while low-width states are reachable from
essentially every prefix. Grant that argument **in full and at its strongest** —
that *every* width-≥10 state is perfectly job-private and splits `k` ways, and
that the low-width remainder is free. Then per-job memo bytes are
`S + P/k`, and as `k → ∞` they tend to `S`, the shared low-width share.

From the certified `n = 11` level-6 run's own per-width census
(`/data/mericanii_s13_method_v3/n11-full/run.log`, packed bytes = `2^w/8`
exactly):

| width | 3–6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|
| share of entries | 2.381 % | 46.522 % | 19.930 % | 10.320 % | 20.635 % | 0.212 % |
| share of packed bytes | 0.399 % | 15.648 % | 13.406 % | 13.884 % | 55.523 % | 1.140 % |

width ≥ 10 is **20.847 % of entries and 56.663 % of packed bytes**, so
`S = 1 − 0.56663 = 0.4334`.

> **Even a perfect prefix decomposition with `k → ∞` and zero CPU cost leaves
> the level-7 memo at `0.4334 × 1,500 GB = 650 GB` against 143 GB of RAM plus
> swap — 4.5× short before a single comparator is examined.**

That is an upper bound on what decomposition could ever be worth on the memory
axis, and it is already a failure. The measured curve (§5) is 10.4× worse than
this idealisation at its best point, because the premise it grants is false.

**Redo the floor with the measured privacy instead of the assumed privacy.**
§3.3 gives the private fraction between sibling cones at every width. Applying
those to the certified level-6 byte census — i.e. asking "what share of the
level-6 memo would every job still have to hold, at the privacy actually
observed?" — gives:

| width | 6 | 7 | 8 | 9 | 10 | 11 | **total** |
|---|---|---|---|---|---|---|---|
| level-6 share of bytes | 0.40 % | 15.65 % | 13.41 % | 13.88 % | 55.52 % | 1.14 % | 100 % |
| measured private fraction | 23.7 % | 31.2 % | 41.0 % | 64.5 % | 56.3 % | 22.2 % | |
| **shared, paid by every job** | 0.30 % | 10.76 % | 7.91 % | 4.93 % | 24.29 % | 0.89 % | **49.08 %** |

> **With the measured privacy, the floor is 0.4908 — worse than the 0.4334 the
> idealisation grants. At level 7 that is `0.4908 × 1,500 GB = 736 GB` against
> 143 GB, i.e. `5.1×` short with `k → ∞` and zero CPU cost.**

**The honest scope limit, stated plainly.** §3's diffs are at level 5, where
width ≥ 10 is only **0.245 % of entries and 1.365 % of packed bytes**, against
20.8 % / 56.7 % at level 6 — so the width-10 privacy figure (56.3 %) is
measured on 29,722 states, not on the level-6 population of 19.6 million. It is
the right *kind* of measurement below the width wave, not a measurement of the
level-7 object, exactly the scope limitation `level7-redecision.md` §4.3 flags
for C910 itself. Two things reduce the worry. First, the floor is not sensitive
to it: setting the width-≥10 privacy to 100 % (the most generous possible
assumption) still leaves a floor of 0.2390, i.e. 359 GB against 143 GB, **2.5×
short**. Second, the width-11 result points the other way — privacy *falls* at
the top width, and level 7 opens widths 12 and 13, which will be the newest and
therefore the most root-adjacent of all.

### 7.4 Why it fails, mechanistically — and why no `k` fixes it

The monolithic search **never certifies any interior state to its true value.**
`Search::improve` raises the root's lower bound by
`min over successors + 1`, and `Edges::improve_next` sorts successors so that
those already at or above the current target go last: each successor is
improved only far enough to move the current minimum, and then abandoned. The
root's bound climbs 5 → 9 → 13 → … → 34 in fourteen such passes, and no
depth-2 state is ever pinned down.

A depth-`d` prefix job is asked for something strictly stronger: certify
`bound(X_P) >= L - d` outright. It must therefore pay for work the monolith
never does. The signature is visible in the iteration tables: the monolith
reaches limit 34 in **14** bound iterations, the depth-2 job needs **24**, and
depth-3 jobs need up to **27** — with the bound climbing in steps of one
instead of three or four, because a prefixed root's successors are
heterogeneous and the minimum moves slowly.

That extra iteration count is *not* the cost, and it is worth saying so: the
final iteration is 99.4 % of the monolith's wall and 99.4 % of the depth-2
job's, so re-deriving the shallow levels costs 0.6 %. The cost is that the
final iteration itself is over a larger, harder object.

**This is a property of iterative-deepening branch-and-bound, not of this
engine or this problem.** Decomposing such a search into independent
subproblems converts an incremental, mutually-truncating computation into `k`
complete certifications. The only way to restore the truncation is to give
each job the others' bounds — which is the shared bound oracle, which is §6,
which is the memory.

### 7.5 The number, at the `k` the brief asks about

Taking the measurements at face value and A1–A5 as stated:

| decomposition | `k` | `CPU_x` | `MEM_x` | level-7 wall | level-7 memo | combined deficit |
|---|---|---|---|---|---|---|
| **none** (C910 monolith) | 1 | 1.000 | 1.000 | 45–190 d | 1,500 GB | **17.8×** |
| prefix depth 2 | 3 | 1.802 | 1.035 | 81–342 d | 1,552 GB | **33×** |
| prefix depth 3 | 9 | 3.544 | 0.998 | 159–673 d | 1,497 GB | **63×** |
| prefix depth 4 | 27 | 55.07 | 23.582 | 6.8–28.7 yr | 35.4 TB | **2.3×10⁴** |
| prefix depth 5 | 91 | 264.0 | 25.704 | 32.5–137 yr | 38.6 TB | **1.2×10⁵** |
| *idealised, `k → ∞`, free* | ∞ | — | **0.4334** | — | 650 GB | **4.5× (memory alone)** |

`CPU_x` here is the **`get_calls` multiplier**, not a wall multiplier: it is an
exact counter, unaffected by the machine's competing load (§1.2), and it is
the quantity the `k^{1-e}` prediction is actually about. Depths 2 and 3 use
Arm B's level-5 values, depths 4 and 5 Arm A's level-4 values (the only level
at which they were measured; §4.2 shows the multiplier gets *worse* at the
deeper level, so these are optimistic).

"Combined deficit" is the product of the wall deficit against the ~90 d
horizon and the memory deficit against 143 GB, the same convention
`level7-redecision.md` §0 uses; it gives 17.8 for the monolith where that
document rounds to ~17.

---

## 8. Verdict

> **FAILS.**
>
> Decomposition does not close the ~17× gap; the best point on its own curve
> leaves the memory deficit at **10.5×** and multiplies the CPU deficit by
> **3.5×**, and the operating points with the `k` the brief asks for are three
> to four orders of magnitude worse. There is no carve-out to request and no
> campaign to sketch, because there is no `k` at which the campaign is cheaper
> than the monolithic run it replaces.
>
> **The one number:** `MEM_x_min = 0.990`, against the `0.0953` required.
> Decomposition delivers **no memory reduction at any prefix depth**.
>
> **The assumption-light second number, for anyone who distrusts the
> extrapolation:** 43.34 % of the certified level-6 memo, by packed bytes, sits
> at widths ≤ 9, which every prefix cone must contain. So no prefix split of
> any width can put the level-7 memo below **650 GB against 143 GB** — 4.5×
> short with `k → ∞` and zero CPU.

**What this closes.** `level7-redecision.md` §6.2 rung 2 ("measure the
job-private fraction") is done, and its own stated failure mode is what
happened. Rung 3's levers (`SUBSUME_DIMS`/`SUBSUME_RANKS`, Z+M composed with
census-tracking widths, and above all the index-lookup engineering that is 79 %
of the certified run's CPU) are unaffected by this result and remain the only
places with unexploited factors. **The programme's conclusion is unchanged:
NO-GO on level 7, and the binding constraint remains wall clock and RAM.**

---

## 9. Corrections this document owes to other documents

| document | correction |
|---|---|
| `docs/level7-redecision.md` §6.2, §9 item 3 | *"`wall ~ N^e` with `e > 1` makes prefix decomposition a CPU win of `k^{e-1}`"* is **false as applied**. The arithmetic is right; the premise that `k` jobs carry `N/k` states each is wrong by up to a factor of `k`. Measured: a 91-way split costs 253× the CPU, not 4.5–32× less. |
| `docs/level7-redecision.md` §6.2 | *"The measured Jaccard between two independent runs' level-4 memos is 0.9936"* is **triply misapplied**: it was `n = 9` versus `n = 10` (different ambients, not independent runs of the same thing); `ambient-reduction.md` §0/§4.2 has since shown the residual to be thread-scheduling noise, with the true value 1.000000 at pinned thread count; and full-cube run-vs-run overlap is not a proxy for sibling **prefix-cone** overlap, which is what §6.2's own experiment needed and which §3 above measures for the first time. |
| `docs/level7-redecision.md` §6.2 | the inference that the level-6 census's *"width ≥ 10 is 20.8 % of entries and 56.7 % of bytes"* is a job-private share "in the favourable direction" is **not supported**: §3 measures privacy directly and §7.3 shows that even granting the inference in full leaves the memory 4.5× short. |
| `docs/lowmem-endgame-assessment.md` §6.2 | its projection of the job-private share (~11 % at level 6, ~63 % at level 7) was already superseded at level 6 by the certified census; §7.3 shows that even the aggressive 63 % model does not make decomposition viable. |
| `docs/lowmem-endgame-assessment.md` §11 | *"The splitting-cost trap, quantified"* — the Boolean-Pythagorean-Triples prior (62 % of 35,000 CPU-hours went on splitting) is **confirmed**, not refuted, and `level7-redecision.md` §6.2's reversal of it should be withdrawn. Its "concrete rule" (measure the per-cell cost at two depths at `n = 11` and plot the total) is what this document does; the curve has no interior minimum — it is monotone upward from depth 1. |
| `evidence/v3/decomp/report.md` | blocker 3, the prefix-depth U-curve, is **resolved**: there is no U. §4.3 and §5 give the curve at two levels and it rises monotonically from the first non-trivial depth. |
| `tools/class_campaign.py` | `build_frontier` should dedup by canonical key at every depth rather than only at the end (§2.1), and should drop classes that already appeared at a shallower depth (§2.2, −24 % of jobs at depth 6). Neither changes any result; both are cost. |

### New, not corrections

1. **Prefix cones are not a partition and the largest cone is the whole
   problem.** At level 5, depth 2, the job with prefix `(0,1),(2,3)` has 1.9 %
   *more* memo entries than the entire monolithic run. (§4.1)
2. **Peak per-job memory rises with prefix depth**, reaching 18.8× the
   monolith's total entry count at level 4, depth 4. Decomposition is not a
   memory-for-CPU trade here — it is worse on both axes. (§5)
3. **The per-state cost of a prefix-rooted cone is higher, not lower**: 34.4 µs
   against 18.9 µs at level 5, despite 24 % fewer states and 49 % fewer index
   candidates. The excess is index churn (`idx_ns_evict` ×2.94). (§4.2)
4. **The mechanism is general**: iterative-deepening branch-and-bound never
   certifies its interior states, and decomposition forces exactly that. Any
   decomposition of this search that does not also share the bound frontier
   pays it. (§7.4)
5. **The canonical prefix frontier is `n`-independent** at depths 1–5
   (1, 3, 9, 27, 91 at both `n = 11` and `n = 13`; 374 vs 375 at depth 6), so
   `k(d)` needs no extrapolation. (§2.3)

---

## 10. Reproduction

```
# canonical prefix frontier (no search, no bound)
python3 .build/v3-decomp-econ/frontier.py <engine> 11 6 .build/v3-decomp-econ/frontier-n11
python3 .build/v3-decomp-econ/frontier.py <wide13-engine> 13 6 .build/v3-decomp-econ/frontier-n13

# arm A, level 4, every canonical class to depth 5 (M4, ~2 h)
DECOMP_ECON_BIN=.build/v3-prefixcert/source/target/release/sortnetopt \
  python3 .build/v3-decomp-econ/drive.py 11 frontier-n11 m4-L33 33 0,1,2,3,4,5

# arm B, level 5, every canonical class to depth 3 (server, ~50 min)
ssh ollama; cd /data/mericanii_s13_method_v3/decomp-econ
python3 drive.py 11 frontier-n11 runs/L34-d0123 34 0,1,2,3

# job-private fraction (dumps the memo, then diffs as (width, packed key) sets)
python3 drive.py 11 frontier-n11 runs/L34-dump 34 0,1,2 --dump
python3 statediff.py statediff.json runs/L34-dump/d*.states

# shared bound oracle transplant
python3 seedexp.py 11 frontier-n11 runs/seed-d2 34 2 3

# every table above
python3 .build/v3-decomp-econ/econ.py m4-L33 srv-L34
```

Engines: server native build of the 11-patch stack, SHA-256
`241857053898a6825b9ffdc3d6b449140ee5b4d611de9342e59294105ac24db6`, built from
`.build/v3-prefixcert/source` with the toolchain at
`/data/mericanii_s13_method_v3/tier1-smoke/toolchain`; M4 build SHA-256
`15352938e26af571968146aeadf2e4764658abc4e139e6be4c1f69586ddcb556`; wide13
build (enumeration only) SHA-256
`683ef3c63fcf81d44eed994016fde0255e12ed0b315f03b41525e62bb6e363fd`.

Server workspace `/data/mericanii_s13_method_v3/decomp-econ/`; local copies of
every `results.jsonl`, `instrument.json`, engine log and the recovered baseline
extracts under `.build/v3-decomp-econ/`. Machine facts re-read at report time:
10 vCPU AMD Ryzen 5 3600, 47 GB RAM, 96 GB swap, 95 GB free on `/data`.
