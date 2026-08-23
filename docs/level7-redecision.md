# The Level-7 Go/No-Go, Re-Decided

**Date:** 2026-08-23.
**Question put:** `docs/novel-facts.md` Fact 4 claims the standing level-7
`Go/no-go: NO` (`ambient-reduction.md` §8.2) rests on a bracket that is 82×
too pessimistic, and recommends reopening it. Level 7 at `n = 13` is the
first-ever computational proof of `S(13) ≥ 44`, so this is the highest-stakes
measurement in the programme.
**Scope:** read-only with respect to `src/`, `evidence/`, `config/`, `ledger/`.
New files: this document, `.build/v3-level7/bracket.py`, and a server workspace
at `/data/mericanii_s13_method_v3/level7-probe/`. No commits. One new
measurement campaign (§4), 8 runs at `n = 11`, limits 33 and 34.

**Scope note** (mirrors `novel-facts.md` and `audit-paper-v2.md` §10.8). No
search for a sorting network was run, no candidate network was constructed, and
no witness exists anywhere in this work. The integer 44 appears only as the
tabulated value under audit and as the *name* of a computation that was **not**
performed and is **not** recommended; it is never a target, bound, feature or
stopping condition of any procedure run here. Every run reported below is a
census measurement at `n = 11` with `--limit` 33 or 34. See §7, which raises the
one place where this constraint and the objective are in direct tension.

---

## 0. Verdict

> ## **NO-GO** — but the gap has shrunk from ~4 orders of magnitude to ~1, and it moved again today.
>
> **The number that kills it:** in the certified `n = 11` run — the operational
> machine, the operational configuration, the operational binary — the
> **level-5 → level-6 iteration wall multiplier was 418×** while the
> **stored-state multiplier was 22.3×**. Fact 4 extrapolates the 22, and the wall
> is charged the 418. Level 6 took **71 h 07 m** of search; one more level at the
> measured multiplier is **3.4 years**.
>
> **The number that keeps it alive:** the new measurement in §4 found a
> configuration (`SUBSUME_WIDTHS=9,10`, census-tracking) that is **2.02× faster
> than the certified configuration and 1.49× faster than no subsumption at all**,
> with a per-level wall growth of 241× against the certified 456×. It is the
> first strict Pareto improvement the programme has found on this frontier, and
> it is the exact lever Fact 4 flagged as "obvious and untried".
>
> **Where that leaves level 7**, at the best operating point now known:
> **≈ 45–190 days of search** (against a months-scale horizon) and
> **≈ 1.5 TB resident** (against 47 GB RAM + 96 GB swap). The binding deficit is
> now roughly **1.7× on wall and 10× on memory**, i.e. **~17× combined** — down
> from the standing bracket's 7.4×–600× on storage alone with a 4-order-of-
> magnitude state bracket. That is a real change and it is why this document
> recommends keeping the question open as a research target. It is **not**
> a GO, and nothing should be launched.

**Fact 4 is half right, and the right half is not the half that matters.** Its
memory claim survives and is important: in the memory-frugal configuration the
level-7 memo is of order 10² gigabytes, not the 2.4–195 TB the standing bracket
claimed, and the disk wall that carried the original NO-GO is indeed gone in
*that* configuration. Its *time* claim does not survive. The configuration that
produces the small memo produces it by paying a subsumption index whose cost
grows as roughly the **square** of the state count — and Fact 4 extrapolates the
state count, which is the memory quantity, to conclude something about time.

The binding constraint has moved from disk to wall clock. It has not gone away,
and it is now on firmer ground than the number Fact 4 replaced, because it is a
measurement of the very run the programme certified rather than an extrapolation
from levels 3–5.

**The finding underneath the verdict** (§2.5) is that the two configurations are
the two ends of a memory-for-time frontier, and neither end is reachable:

| level 7, `n = 13` | **A** (no index) | **B89** (certified) | **C910** (new, §4) |
|---|---|---|---|
| search wall | **9–20 d** | 1.5–3.4 yr | **45–190 d** |
| memo, resident | **~16 TB** | 546 GB | ~1.5 TB |
| wall deficit (vs ~90 d) | none | 6–14× | **1.7×** |
| memory deficit (vs 143 GB) | **110×** | 3.8× | 10× |
| **combined** | **110×** | **23×** | **17×** |

Every prior assessment costed one end of this frontier and declared the other
end's resource fine. `ambient-reduction.md` §8.2 costed **A** and correctly found
it storage-bound; Fact 4 recosted in **B** and correctly found the storage wall
gone — without recosting the time. C910 is the best point now known and it is
still 17× short.

Two of the brief's own premises are also factually wrong and both are
load-bearing; see §1.

| resource (config B, central case) | level-7 need | available | short by |
|---|---|---|---|
| **search wall** | **562 d – 3.4 yr** | policy horizon ~months | **6–40×** |
| memo peak RSS | 546 GB | 47 GB RAM + 96 GB swap = 143 GB | 3.8× |
| memo packed bytes | 185 GB | **97 GB** free on `/data` | 1.9× |
| gen-proof transient RSS | 740 GB | 143 GB | 5.2× |

---

## 1. Two corrections to the standing premises, both measured today

**(a) The server has 97 GB free, not ~324 GiB and not ~310 GB.**

```
/dev/sdb1   787G  657G   97G  88%  /data
```

Of the 787 GB, 307 GB is `/data/projects`, 97 GB is the swapfile itself, 64 GB
models, 35 GB Stable Diffusion, 28 GB alien-project, 25 GB aigp-qv2, 21 GB this
programme. The `324 GiB` figure entered the record in `lowmem-endgame-assessment`
§2.3, which explicitly flagged it as *"taken as given and not independently
checked here"*, and has been carried unchecked ever since — including into Fact
4's headline sentence *"roughly 250 GB against ~324 GiB free"*. The root
filesystem is separately at **97 % full with 3.1 GB free**, so nothing may be
written outside `/data`.

**(b) The certified run's log DOES survive.** `evidence/v3/n11-certified/report.md`
and its correction addendum both state that it does not, and the addendum leaves
the insertions-vs-stored-census ambiguity open on that basis. The log is at
`/data/mericanii_s13_method_v3/n11-full/run.log`, 999,153 bytes, 25,730 lines,
with the complete per-iteration table, the full counter dump, the width census,
and a `/usr/bin/time -v` block. `prune.log` and `genproof2.log` survive too.
This document is built on them. **The addendum should be re-corrected.**

> ### The counting ambiguity is CLOSED, from the artifact
>
> | quantity | value |
> |---|---|
> | per-width `inserts`, summed | 103,343,397 |
> | `idx_evictions` | 8,122,254 |
> | inserts − evictions | **95,221,143** |
> | reported `total_entries` / `peak_entries` / `live_entries` | **95,221,143** |
>
> The identity is exact. **`95,221,143` is the stored census, not the insertion
> counter.** The insertion counter is 103,343,397, 8.5 % larger.
> `|Reach(11,6)| = 95,221,143` and `|Reach(13,6)| = 95,221,145` are stored-census
> figures and may be printed as such. Fact 6 and the addendum's caveat can both
> be tightened.
>
> Side effect: Fact 4's headline multiplier `95,221,143 / 4,714,517 = 20.20×`
> mixes level-6 *entries* against level-5 *inserts*. Entries-to-entries, in the
> same run, it is `95,221,143 / 4,266,109 = ` **22.32×**. Immaterial to the
> conclusion, but the published figure is apples-to-oranges.

---

## 2. Hardening Fact 4 — what config B actually buys

### 2.1 Is B's advantage a real state-count reduction, or a counting artefact?

**It is real — and it is nevertheless not a cost reduction.** The A/B ladder logs
carry both hardware performance counters and the engine's own DP-side counters,
and together they settle this without any new run.

| `n = 11`, limit 34, 4 threads, same binary | config A (plain) | config B (frugal) | B/A |
|---|---|---|---|
| stored entries | 50,400,015 | 4,375,153 | **0.087** |
| `get_calls` (DP memo probes) | 906,222,216 | 89,608,385 | **0.099** |
| `improve_calls` | 72,724,398 | 6,507,427 | **0.089** |
| `huffman_prunings` | 518,934,075 | 43,664,476 | **0.084** |
| `successors_generated` | 182,129,499 | 28,247,374 | 0.155 |
| `filter_candidates` (index work) | **0** | **20,176,888,668** | — |
| **instructions retired** | 2.0633×10¹³ | **2.5479×10¹³** | **1.235** |
| **CPU cycles** | 9.1253×10¹² | **1.1778×10¹³** | **1.291** |
| search wall (ns) | 7.7598×10¹¹ | 9.2100×10¹¹ | 1.187 |
| peak RSS | 2.95 GB | 0.459 GB | 0.156 |

The DP-side counters all fall by ~10×, in lockstep with the stored census. So
config B is **not** merely declining to store what it computes: it genuinely
traverses a 10× smaller DAG. Fact 4's state reduction is a real reduction, and
the "insertions vs stored census" worry from the correction addendum is not what
is going on.

> **And yet config B retires 23.5 % MORE instructions and burns 29.1 % MORE
> cycles than config A.**
>
> Config A's DP work is 2.06×10¹³ instructions. Config B does one tenth of that
> DP work — ~2×10¹² instructions — and still totals 2.55×10¹³. **Roughly 92 % of
> config B's runtime is the subsumption index**, and the index costs about
> **twelve times more than the DP work it saved.**

**This is the load-bearing correction to Fact 4.** Fact 4 extrapolates the
level-7 cost from the config-B *state* count, which implicitly assumes
`cost ∝ states`. The measurement says `cost ∝ index candidates`, and index
candidates are a different, faster-growing quantity. Memory scales with the
config-B census; wall clock scales with the index.

### 2.2 The cost exponent, measured twice independently

**(i) Cross-level**, from the certified run's own iteration table:

| level | iteration wall | entries | wall mult | state mult | divergence |
|---|---|---|---|---|---|
| 3 | 0.14 s | 18,633 | — | — | — |
| 4 | 1.29 s | 133,049 | 9.1× | 7.14× | 1.3× |
| 5 | 610.3 s | 4,266,109 | **474.2×** | 32.06× | 14.8× |
| 6 | **255,370.5 s** | 95,221,143 | **418.4×** | 22.32× | **18.7×** |

`log(418.4) / log(22.32) = ` **wall ~ N^1.94**.

**(ii) Intra-level**, from the states-vs-time curve *inside* the level-6
iteration (25,613 samples, `level6_curve.csv`) — an entirely independent
measurement that does not use the level-5 anchor at all:

| live states | instantaneous rate |
|---|---|
| 9.17 M | 1,366 states/s |
| 40.6 M | 354 |
| 62.7 M | 264 |
| 80.4 M | 232 |
| 94.7 M | **216** |

The rate fell **6.32×** while `N` grew 10.3× ⇒ rate ~ `N^-0.79` ⇒
**wall ~ N^1.79**. And it was **still falling in the final hour** — 232 → 216
over the last third of the run. There is no plateau.

> **Two independent measurements agree: wall ~ N^1.79 … N^1.94.** Every model
> that assumes the per-state cost stops rising is refuted by the run's own log.

### 2.3 Why — and it is not a mystery

The counter dumps name the mechanism outright. First, where the certified
level-6 run's CPU went:

| | thread-seconds | share of user time |
|---|---|---|
| **subsumption index lookup** | 1,953,558 | **79.4 %** |
| index insert | 573,114 | 23.3 % |
| index evict | 112,411 | 4.6 % |
| abstraction | 12,689 | 0.5 % |
| *total user time* | *2,460,957* | |

Second — and this is the whole thing — how the index's work grows with the level:

| config B | level 5 | level 6 | growth |
|---|---|---|---|
| stored entries | 4,375,153 | 95,221,143 | **21.8×** |
| index population | 405,693 | 8,281,600 | 20.4× |
| **`filter_candidates`** | 2.018×10¹⁰ | 6.004×10¹² | **297×** |
| candidates **per stored state** | 4,612 | 63,054 | **13.7×** |
| *observed iteration wall* | *610 s* | *255,371 s* | ***418×*** |

The level-5 column is the M4 A/B ladder; §4's independent server run of the same
configuration gives 18,614,729,757 candidates over 4,173,827 entries =
**4,459 per state**, corroborating 4,612 on different hardware to within 3.3 %.

> Each query scans a bigger index, so the cost per state rises with the index
> population: `candidates/state ~ index^0.67` (measured: `13.7 = 20.4^0.67`).
> Hence `cost ~ states × states^0.67 = states^1.67`, and the observed wall
> exponent of 1.79–1.94 is that plus the width-wave term. **The wall multiplier
> tracks the 297× candidate multiplier, not the 21.8× state multiplier.**

A consistency check that makes the config-A exponent credible too: config A has
no index at all, so its per-state cost should rise only with the width wave.
Config A's measured exponent is 1.14, i.e. per-state cost ×`239.9^0.14` = **2.15×
per level** — against a directly measured bytes-per-state growth of **2.17× per
level** (§3.1). Two unrelated measurements, agreeing to 1 %.

**Config B is not a free lunch that the programme had failed to notice. It is a
memory-for-time trade whose exchange rate gets worse every level**, and the
certified run is the first place the programme has run it deep enough to see it.

### 2.4 The exchange rate, stated once

Applying the same exponent extraction to config A's own ladder
(`n = 11`, L33 → L34: wall ×507.3 at states ×239.9):

| configuration | cost exponent | states/level | memo bytes |
|---|---|---|---|
| **A** (no subsumption) | **1.08 (server) / 1.14 (M4)** | ~240× | 11.6× larger |
| **B** (evict, DIMS 96, w8,9) | **1.86 (M4) / 1.94 (server)** | ~22–32× | 11.6× smaller |

Config A's exponent is near-linear because it has no index; its per-state cost
rises only with the width wave. Config B's is near-quadratic because its index
grows with the run.

### 2.5 The frontier, and why the two prior assessments disagree

Carrying each configuration out to level 7 on its own measured scaling — config A
with its 33.3× geometric state multiplier and exponent 1.08, config B with its
18.76× multiplier and exponent 1.79–1.94, both with the measured 2.17×/level
bytes-per-state wave:

| | **config A** (no index) | **config B** (index) |
|---|---|---|
| level-7 states | 5.6×10¹⁰ | 1.8×10⁹ |
| bytes/state (packed) | ~140 | ~103 |
| **level-7 memo** | **~7.9 TB packed / ~16 TB resident** | **~185 GB packed / 546 GB resident** |
| **level-7 search wall** | **~9–20 days** | **~1.5–3.4 years** |
| against 97 GB disk / 143 GB RAM+swap | **short ~110×** | short 1.9× (disk) / 3.8× (RAM) |
| against a months-scale horizon | fits | **short 6–14×** |

> **The subsumption index is a memory-for-time exchange, and the two prior
> assessments each stood at one end of it.** `ambient-reduction.md` §8.2 costed
> level 7 in **config A** and correctly found it storage-bound. Fact 4 recosted
> it in **config B** and correctly found the storage wall gone — but did not
> recost the time. Neither is arithmetically wrong; each measured the resource
> its own configuration happened to be cheap in.
>
> The obvious question is whether some point *between* the two ends is feasible.
> Nobody had looked. **§4 looks, and finds a strictly better intermediate point
> — which is still not feasible.**

---

## 3. The hardened level-7 bracket

Anchored on `|Reach(13,6)| = 95,221,145` (Chain Collapse, Theorem E — the level-6
census at `n = 13` *is* the level-6 census at `n = 11` plus two) and scaled by
the certified run's own config-B state multipliers, whose observed spread across
the ladder is `[7.14, 38.53]`, geometric mean 18.76×.

### 3.1 States and bytes

| case | state mult | level-7 states | packed GB | peak RSS GB | gen-proof GB |
|---|---|---|---|---|---|
| floor | 7.14× | 6.80×10⁸ | 70 | 208 | 282 |
| **geometric** | **18.76×** | **1.79×10⁹** | **185** | **546** | **740** |
| ceiling | 38.53× | 3.67×10⁹ | 379 | 1,121 | 1,519 |

**Bytes per state, measured, not modelled.** The width census gives
`packed bytes/state = 2^w / 8` exactly. At level 6, `n = 11`:

| width | 6 | 7 | 8 | 9 | 10 | 11 |
|---|---|---|---|---|---|---|
| share of entries | 2.4 % | **46.5 %** | 19.9 % | 10.3 % | **20.6 %** | 0.2 % |
| B/state | 8 | 16 | 32 | 64 | 128 | 256 |

Mean packed bytes/state: **21.9 at level 5 → 47.6 at level 6, a 2.17× jump in
one level.** The level-7 figure above applies one more 2.17× step (→ 103
B/state). **This is conservative**: it ignores the fact that widths 12 and 13
open up at level 7 and cost **512 and 1024 B/state**, and that
`n_min(7) = 13` means level 7 is *precisely* the level at which they open. The
width-10 share alone jumped from 1.8 % to 20.6 % between levels 5 and 6.

Peak RSS is `2.96 × packed` (B-tree/allocator overhead plus the subsumption
index, which was 3.74 GB of the 13.08 GB at level 6 — **28 % of peak memory is
the index**, and the index grows with the level too).

### 3.2 Wall clock (search only)

Base: the **measured** level-6 iteration wall, 255,371 s = 2.96 days.

| | cost freezes (`N^1.00`) | `N^1.79` (intra-level) | `N^1.94` (cross-level) |
|---|---|---|---|
| floor, ×7.14 | 21 d | **100 d** | 135 d |
| **geometric, ×18.76** | 55 d | **562 d** | **2.42 yr** |
| ceiling, ×38.53 | 114 d | 5.58 yr | 9.79 yr |

Applying the directly measured 418× multiplier once more: **3.39 years.**

The `N^1.00` column is the model the brief's "~55 days" comes from, and the model
implicit in Fact 4. It assumes the per-state cost stops rising. §2.2(ii) refutes
that from the run's own log. It is printed only to show that **even that
indefensible best case does not rescue level 7**: 55 days of continuous
unattended compute is already 14× the entire certified `n = 11` campaign, and the
memory walls in §3.1 bind regardless.

**This table is for the certified configuration (B89).** §4 finds a better
configuration; its bracket is **45–190 days** at 2.85× the memory, and it is the
one that should be quoted going forward.

**On throughput and cores, since the brief raises it.** The server is 10 vCPU on
an AMD Ryzen 5 3600 (`lscpu`: 10 CPUs, 1 thread/core), and the engine uses them:
the certified run averaged **962 % CPU**, the sweep's config-A arm 955 %. Pool
utilisation is not the problem. Measured config-A throughput on the server is
**120,600 states/s** (50,840,923 states / 421.5 s) against the M4's 170,882 at 10
cores — the server is 0.71× the M4, consistent with `lowmem` §2.1's finding that
core count buys little.

What `lowmem` §2.1 gets wrong as a *planning rule* is its conclusion: *"treat
1.5×10⁵ states/s as a hardware constant."* It is not a constant, it is a
**level-5** constant. By the end of level 6 the certified run was managing **216
states/s** (§2.2). Every "M4-day" figure in the endgame assessment is computed by
dividing a deep-level state count by a shallow-level rate, and therefore
understates levels 6–8 by two to three orders of magnitude. That single
substitution, not any of the memory analysis, is what made level 7 look like
"3.8 M4-days".

### 3.3 The rest of the pipeline

Measured at level 6, from the surviving logs:

| stage | wall | peak RSS |
|---|---|---|
| search | 71 h 07 m | 13.4 GB |
| prune-all | 9 h 45 m | 8.9 GB |
| **gen-proof** | **12 h 45 m** | **39.4 GB**, 302,821 major faults |
| **total** | **93 h 36 m = 3.90 d** | |

Two corrections to `evidence/v3/n11-certified/report.md`: gen-proof was
**12 h 45 m**, not "~9 h", and its peak was **39.4 GB**, not ">37.9 GB" (the
37.9 GB was the OOM-kill point of the *failed* attempt). Prune + gen-proof is
32 % of search.

Gen-proof cost **3,837 bytes per certificate step** and was already swapping at
level 6. Level 7's certificate is ~1.9×10⁸ steps ⇒ **~740 GB transient**. This
matters because **gen-proof, not search, was the binding memory peak at
`n = 11`** — the brief is right about that, and it stays the binding peak at
level 7.

One piece of good news: `proof.rs`'s `u32` step-id cap (4.29×10⁹) is **not** a
level-7 blocker at 1.9×10⁸ steps, and the v2 format exists anyway. The
`~1.5×10¹¹` figure in `ambient-reduction.md` §6 is for the *full* `n = 13`
problem, not for level 7.

### 3.4 Which assumptions could be wrong, and in which direction

| assumption | could be wrong how | direction |
|---|---|---|
| the 6→7 **state** multiplier is in `[7.14, 38.53]` | **This is the one genuinely unmeasurable number** (`n_min(7) = 13`; no cheaper rehearsal exists, Theorem E). Levels 12 and 13 open at level 7 with no `n = 11` counterpart, so the ladder is being extrapolated *across* the `n_min` boundary. | **against us** — new widths add states the `n ≤ 11` ladder never saw |
| the cost exponent 1.79–1.94 persists | It could saturate if the index's candidate lists stop growing. | **for us**, but §4 tested the obvious lever and it did not move (see below) |
| bytes/state grows one more 2.17× step | Widths 12/13 cost 512/1024 B/state. | **strongly against us** |
| `2.96×` RSS-to-packed overhead holds | The index share (28 %) may grow. | mildly against us |
| survivor rate stays 10.8 % for gen-proof sizing | Unmeasured at level 7. | unknown |
| individual per-level multipliers are meaningful | `novel-facts.md` §1.6 shows they move 16 % under a scheduling change; only the geometric mean (which telescopes to the endpoints) is robust. | **widens the bracket both ways** |
| level 6 at `n = 13` reproduces level 6 at `n = 11` | Chain Collapse is **PROVEN** (Theorem E) and confirmed at levels 1–4. | safe |

The dominant uncertainty is not arithmetic. It is that **the 6→7 multiplier
crosses the one boundary in the whole problem where the object changes
character**, and no experiment below `n = 13` can probe it. That was true when
the NO-GO was written and Fact 4 does not change it.

---

## 4. The decisive experiment

### 4.1 What was rejected, and why

- **`n = 13 --limit 43` (level 6 in the wide13 build).** By Chain Collapse it
  must reproduce 95,221,145, and it would validate the whole chain end-to-end in
  the build a level-7 run would use. But it costs **~72 h** (the `n = 11` figure
  plus the 1.3 % wide13 tax) — twelve times the 6-hour reporting rule, and it
  tests a theorem that is already *proven* and already confirmed at four levels.
  Its expected information about the go/no-go is close to zero.
- **An instrumented partial level-7 run with a state cap.** This is the
  experiment the brief nominates, and it is **blocked on governance, not on
  cost**: level 7 at `n = 13` *is* `sortnetopt search 13 -l 44`. The integer 44
  would be the search's literal stopping bound. See §7.
- **A partial run capped by time rather than states** would measure only the
  early, cheap part of a level whose cost is concentrated at the end — the
  certified run reached 5 M of its 95 M states in the first 900 s of 255,371.
  It would systematically flatter level 7.

### 4.2 What was chosen and run

The question with the highest leverage that fits inside a few hours is **not**
"how big is level 7" — that is unmeasurable — but:

> **Is the `N^1.9` cost law intrinsic, or an artefact of `SUBSUME_WIDTHS=8,9`?**

If the exponent can be brought to config A's 1.14 while keeping config B's
memory, the wall bracket collapses by 1–2 orders of magnitude and the verdict
flips. Fact 4 names precisely this lever: *"Pinning `SUBSUME_WIDTHS` to the
widths where the mass actually sits at level 6/7 is now an obvious and untried
lever."* The level-6 census says the mass has moved to widths 7 and 10, not
8 and 9.

**Design.** `n = 11`, limits 33 (level 4) and 34 (level 5), four configurations,
on the server, using the *exact binary that produced the certified run*
(`tier1-smoke/target-native/release/sortnetopt`, SHA-256 `5a3045be…350f66`).
Two limits so that the **exponent**, not just the wall, is measured per
configuration. `RUST_LOG` unset; no `CHECKPOINT_DIR`; no dumps (disk is at
97 GB). Nothing involves `n = 13` or the integer 44.

| arm | `SUBSUME_WIDTHS` | rationale |
|---|---|---|
| A | (off) | work baseline, exponent 1.14 reference |
| B89 | 8,9 | the certified configuration, control |
| C910 | 9,10 | census-tracking widths — Fact 4's untried lever |
| D8910 | 8,9,10 | wider index |

Script: `/data/mericanii_s13_method_v3/level7-probe/sweep.sh`.
Logs: `/data/mericanii_s13_method_v3/level7-probe/logs/`.

**Decision rule, fixed before the runs:**

- **GO signal** — some arm reaches a cost exponent ≤ 1.3 with a memo within ~2×
  of B89's. Level-7 wall would then fall to the tens of days and the question
  reopens on memory alone.
- **NO-GO confirmed** — every subsuming arm stays at exponent ≥ 1.7. The `N^1.9`
  law is intrinsic to on-line subsumption at this scale, level 7 is
  420–520×·71 h, and the verdict stands.

### 4.3 Result — the lever is real, and it is not enough

All 8 runs completed, `result = 33` / `result = 34` on every arm (self-check
passed). Walls are the **per-iteration** figures from the engine's own iteration
table, not process wall, so the 10 s pool-shutdown floor is excluded.

| arm | level-4 wall | level-4 entries | **level-5 wall** | **level-5 entries** | level-5 RSS | **wall/level** | **exponent** |
|---|---|---|---|---|---|---|---|
| **A** (no index) | 1.094 s | 207,249 | 421.5 s | 50,840,923 | 3,135 MB | 385× | **1.08** |
| **B89** (certified) | 1.251 s | 132,894 | 570.4 s | 4,173,827 | 401 MB | 456× | **1.78** |
| **C910** (census-tracking) | 1.173 s | 202,642 | **282.2 s** | 11,900,303 | 747 MB | **241×** | **1.35** |
| **D8910** | 1.281 s | 132,240 | 543.1 s | 3,897,062 | 417 MB | 424× | **1.79** |

**Control validates.** B89 reproduces the certified run's own level-5 iteration
to 6.5 % in wall (570.4 s vs 610.3 s) and 2.2 % in entries (4,173,827 vs
4,266,109) — within the known run-to-run spread. The measurement apparatus is
sound.

> ### **C910 is a strict Pareto improvement over both existing configurations.**
>
> It is **1.49× faster than config A** *and* uses **4.2× less memory** than
> config A. It is **2.02× faster than the certified config B89** at 1.86× the
> memory. Its wall grows **241× per level against B89's 456×** — 1.9× better per
> level, **3.6× better over two levels**. Its index does 3.0× fewer candidate
> comparisons (6.18×10⁹ vs 1.86×10¹⁰) while removing 4.3× of the DP work: for the
> first time in this programme, **on-line subsumption is a net wall win, not a
> net wall tax.**
>
> This is exactly the lever Fact 4 named — *"pinning `SUBSUME_WIDTHS` to the
> widths where the mass actually sits is now an obvious and untried lever"* — and
> it works. It corroborates `evidence/v3/zm/report.md`'s finding that the index
> pays off from width 9 upward, from a completely different direction.

**Against the pre-registered decision rule:** C910 lands at exponent **1.35**
against a GO threshold of ≤ 1.30, with a memo at **1.86×** B89's against a
threshold of ≤ 2×. It **narrowly misses**, and the miss is not the point — the
point is what 1.35 buys at level 7:

Projecting each arm forward on its **own** measured level-5 wall and its **own**
per-level multiplier (B89's 456× reproduces the certified level-6 run's 71 h
from its 570 s level-5 to within 7 %, which is the check that this projection
method works at all):

| | level-5 wall | wall/level | ⇒ level 6 | ⇒ **level 7** | level-7 memo (resident) |
|---|---|---|---|---|---|
| B89 (certified) | 570 s | 456× | 72 h *(actual: 71 h)* | **1.5 – 3.4 yr** | 546 GB |
| **C910** | **282 s** | **241×** | **~19 h** | **45 – 190 d** | ~1.5 TB |

(The level-7 range spans 6→7 state multipliers of 20×–59× at exponent 1.35; a
pessimistic 80× gives ~290 d.)

C910's advantage compounds: 2.02× on base speed times (456/241)² = 3.6× on two
levels of growth = **7.3× at level 7**. But it moves the operating point
**along** the frontier toward config A rather than off it: 7.3× faster, 2.85×
more memory. Forty-five to a hundred and ninety days of continuous compute
against a months-scale horizon, with a memory requirement that has gone from
3.8× short to **10× short**, is not a GO.

**Caveat on scope, stated plainly.** This measures the exponent at levels 4→5,
where the population mass sits at widths 7–8. C910 indexes widths 9–10, which at
level 5 carry only 7.5 % of the states — so C910 is being tested *before* its
index is where the mass is. At level 6 the mass has moved (width ≥ 10 is 20.8 %
of entries and 56.7 % of bytes), so C910's compression should improve and its
index cost should rise, and the net could go either way. **Testing that requires
a level-6 run, which is ~19–24 h under C910** (see §6.1) — over the 6-hour rule,
so it was not run here.

### 4.4 The immediately actionable consequence

**Every future run in this programme should use `SUBSUME_WIDTHS` tracking the
census, not fixed at 8,9.** On today's measurement that is free: 2× the wall of
the certified configuration, recovered, for 1.9× the memory. Combined with
`evidence/v3/zm/report.md`'s `MATCH_FILTER_MIN_WIDTH=9` (measured 5.0 % on top,
independently), the level-6-at-`n = 13` chain-validation run
(`--limit 43`, wide13) drops from **~72 h to an estimated 19–24 h at ~25–40 GB
peak RSS** — which fits the server's 47 GB and is a single overnight
checkpointed job. That run is now affordable and is the right next
step; it was not affordable this morning.

---

## 5. What the money buys

The standing analysis (`lowmem` §9.1) chose `is4gen.8xlarge` for its **30 TB of
local NVMe**, because the old bracket needed 2.4–195 TB. **Fact 4's memory
finding makes that instance pointless**: the level-7 memo is ~185 GB packed /
~546 GB resident, so capacity is no longer the scarce thing. What is scarce is
**CPU-months**, and that is the one thing $100 cannot buy.

| what is needed | what $100 buys | ratio |
|---|---|---|
| 100 d – 2.4 yr of a ~768 GiB box | `i3en.24xlarge` spot @ $3.63/h → **27.6 h** | **87× – 770× short** |
| same, on dedicated hardware | Hetzner-class → ~18–22 d, but at ≤ 128 GB RAM | 5–40× short, and the RAM does not fit |

At `i3en.24xlarge` spot pricing the level-7 search costs **≈ $8,700 at the C910
floor and ≈ $49,000 at the config-B central estimate**. The correct
recommendation is unchanged from `lowmem` §11 Step 4: **spend nothing.** The
$100 is now worth *less* than it was, because the resource it was earmarked to
buy (bulk NVMe) turned out not to be the binding one. If money is ever spent,
the thing to buy is **RAM-hours, not NVMe-terabytes** — that is the one
planning conclusion this document does change.

---

## 6. What to do instead — a ranked ladder

Sketching a level-7 campaign now would be planning against a 45–190 day search
with a 10× memory deficit and a ~2 TB gen-proof stage. What follows is the
ladder that would have to be climbed before such a campaign could be honestly
proposed, in strict dependency order. Each rung is affordable; each produces a
number that decides the next.

### 6.1 Rung 1 — adopt C910 and run level 6 at `n = 13` in the wide13 build

Newly affordable **because of** §4: **~19–20 h** projected (C910's measured
level-5 wall of 282 s × its measured 241×/level, plus the 1.3 % wide13 tax),
against ~72 h this morning. `--limit 43`, wide13, `SUBSUME_WIDTHS=9,10`,
`MATCH_FILTER_MIN_WIDTH=9`, `CHECKPOINT_DIR` set and `RUST_LOG` **unset** (the
documented silent-exit hazard, `evidence/v3/decomp`).

**Memory is the risk on this run, not time.** C910 stores 2.85× what the
certified configuration did, so the projection is **~37 GB peak RSS against
47 GB of RAM** — tight, with the 96 GB swapfile as the backstop and a hard
tripwire warranted at 40 GB. Chain Collapse guarantees the width census is
identical to `n = 11`'s below width 11 plus one state each at widths 12 and 13,
so there is no `n = 13` width penalty; and C910's compression should *improve*
at level 6, where 20.8 % of entries have reached widths 9–10, which is where its
index sits. That is the upside case and it is untested.

By Chain Collapse it must return exactly **95,221,145**. What it buys is not the
census — that is a theorem — but everything else: the first end-to-end
validation of the 11-patch wide13 stack at real scale, the wide13 width census
including any width-12 population, the C910 exponent at the level where the mass
has actually reached widths 9–10 (§4.3's stated scope limitation), and a real
checkpoint/resume exercise. **It is over the 6-hour rule and must be run as a
checkpointed overnight job with a reporting checkpoint at 6 h.**

### 6.2 Rung 2 — measure the job-private fraction

The superlinearity is not only bad news. `wall ~ N^1.35…1.9` means splitting a
run of `N` states into `k` jobs of `N/k` costs `k·(N/k)^e = N^e · k^{1-e}`. At
`e = 1.78`, a 100-way split is a **32× reduction in total CPU**; at `e = 1.35`,
still **4.5×**. **Superlinear cost makes decomposition a win, not the tax the
Boolean-Pythagorean-Triples precedent warns about** — this is the single most
important structural consequence of the exponent, and it points the same way as
the memory constraint.

The machinery is largely built and validated end-to-end at `n = 9`/`n = 10`: job
manifests, sharding, checkpointing, prefix-rooted gen-proof, per-job
certificates and composition (`evidence/v3/decomp`, `evidence/v3/prefixcert`),
plus the shared bound oracle `SORTNETOPT_BOUND_SEED`.

**The one thing that decides whether it works is unmeasured:**

> **What fraction of the level-`ℓ` memo is job-private?**
>
> If prefix cones overlap almost completely, `k` jobs each rebuild the shared
> core and the split is a `k`-fold *loss* that swamps the `k^{1-e}` win. The
> measured Jaccard between two independent runs' level-4 memos is **0.9936** —
> near-total sharing, which would be fatal. But that was level 4. `lowmem` §6.2
> projects the job-private (width ≥ 10) share rising to ~11 % at level 6 and
> ~63 % at level 7, and **the certified run's width census now settles the level-6
> point directly: width ≥ 10 is 20.8 % of entries and 56.7 % of bytes — nearly
> double the projection, in the favourable direction.**

The experiment is two prefix jobs at `n = 11` and depth 2–4, diffed as key sets.
Hours, not days. It also supplies the prefix-depth U-curve that
`evidence/v3/decomp` lists as blocker 3.

### 6.3 Rung 3 — the levers that are still unpriced

- **`SUBSUME_DIMS` and `SUBSUME_RANKS`** were never swept alongside
  `SUBSUME_WIDTHS`. §4 swept one knob of three and found 2×. 
- **Z+M** (`MATCH_FILTER_MIN_WIDTH=9`) is measured at 5.0 % standalone but has
  never been composed with census-tracking widths, and `evidence/v3/zm` predicts
  the two are complementary (both are width-≥9 phenomena).
- **The `wall ~ N^e` exponent is a property of the index implementation, not of
  the problem.** 79 % of the certified run's CPU went to index *lookup*, at 63,054
  candidate comparisons per stored state. That is an engineering number, and it
  is the largest single unexploited factor anywhere in this analysis.

**Not built, and now correctly deprioritised:** the shell-bucketed external memo
(`lowmem` §7). Fact 4's memory finding cuts its value sharply — at 185–525 GB the
level-7 memo is RAM-sized on a rented box, so its purpose shrinks from "raises
the ceiling 100×" to "saves buying RAM". It remains the enabler for the oracle's
job-to-job propagation (the measured 45× on a sibling job), which is now its main
justification and which belongs behind rung 2.

---

## 7. A governance item the architect must resolve

The standing constraint is that **44 never appears as a target, bound, feature or
stopping condition inside search or learning**. Level 7 at `n = 13` is, literally,
`sortnetopt search 13 -l 44`: the integer 44 is the search's stopping bound.

The constraint is plainly aimed at the *constructive* side — programs that build
networks must not hard-code the tabulated value — and the backward lower-bound DP
is a different object, whose `--limit` is the quantity being proved rather than a
target being aimed at. But the constraint is written without that carve-out and
is marked non-negotiable, so **it is not mine to reinterpret.** No level-7 run,
not even an instrumented probe, was launched here. The experiment in §4 was
designed at `n = 11`, limits 33 and 34, specifically to avoid it.

If level 7 is ever revisited, this needs an explicit written carve-out first.
`novel-facts.md`'s scope note already contains the right language for one.

---

## 8. Reproduction

```
python3 .build/v3-level7/bracket.py          # every number in §§1-3, stdlib only

# on the server (ssh ollama):
/data/mericanii_s13_method_v3/level7-probe/sweep.sh
/data/mericanii_s13_method_v3/level7-probe/logs/{A,B89,C910,D8910}_L3{3,4}.log
/data/mericanii_s13_method_v3/level7-probe/level6_curve.csv   # 25,613 samples

# the surviving certified-run artifacts, which had been believed lost:
/data/mericanii_s13_method_v3/n11-full/run.log        # 999,153 B
/data/mericanii_s13_method_v3/n11-full/prune.log
/data/mericanii_s13_method_v3/n11-full/genproof2.log
```

Binary under test: `tier1-smoke/target-native/release/sortnetopt`,
SHA-256 `5a3045bea3ab01ae1a2a73d99d7988154dbb10c8fbb532ecde123fbbab350f66`
— the same binary that produced the certified `Just (11,35)`.

Local copies of every artifact this document depends on, so that it survives the
server: `.build/v3-level7/sweep-logs/*.log` (all 8 runs),
`.build/v3-level7/n11-certified-run.log.gz` (the recovered certified log),
`.build/v3-level7/sweep.sh`, `.build/v3-level7/bracket.out`.

**Independent numeric audit:** 40 of 40 claims in §§1–4 recomputed from the raw
logs by a separate process, all PASS (max deviation < 0.1 %). Machine facts
(97 GB free, 47 GB RAM, 96 GB swap) re-read at audit time.

---

## 9. Corrections this document owes to other documents

| document | correction |
|---|---|
| `docs/novel-facts.md` Fact 4 | the 82× improvement is in **bytes, not time**; the config-B multiplier extrapolates a storage counter to a cost that grows as `N^1.9`; "250 GB against ~324 GiB free" compares a **RAM** requirement against **disk** availability, using an external memo that was never built, against a disk figure that is really **97 GB** |
| `docs/novel-facts.md` Fact 4 | the 20.20× multiplier mixes level-6 entries with level-5 inserts; entries-to-entries it is 22.32× |
| `docs/novel-facts.md` §1.1 | the insertions-vs-census ambiguity is **resolved**: 95,221,143 is the stored census |
| `evidence/v3/n11-certified/report.md` | the run log **survives**; gen-proof was 12 h 45 m / 39.4 GB, not "~9 h / >37.9 GB" |
| `docs/lowmem-endgame-assessment.md` §2.3 | the 324 GiB server figure it flagged as unchecked is wrong; it is 97 GB |
| `docs/ambient-reduction.md` §8.2 | the disk-based NO-GO reasoning is superseded; **the verdict is not** — it now rests on wall clock and on RAM, and the deficit is ~17× rather than 7.4–600× |
| `docs/lowmem-endgame-assessment.md` §2.1 | "treat 1.5×10⁵ states/s as a hardware constant" is wrong as a planning rule — throughput fell to **216 states/s** by the end of level 6. It is a *level-5* constant. Every M4-day figure derived from it understates deep levels by 2–3 orders |
| `docs/lowmem-endgame-assessment.md` §11 Step 0b | the "measure the ladder with subsumption ON" action is now **done** (§4), and its answer is: the multipliers do not fall, but the *configuration* matters by 2× and had never been swept |

### New, not corrections

1. **`SUBSUME_WIDTHS=9,10` is a strict Pareto improvement** over both the plain
   and the certified configurations: 1.49× faster than no index at 4.2× less
   memory, 2.02× faster than the certified index at 1.86× the memory. First
   configuration in this programme for which on-line subsumption is a net wall
   **win**. Adopt as default. (§4.3)
2. **The cost exponent is a measurable, configuration-dependent quantity**
   (1.08 / 1.35 / 1.78 / 1.79 across four arms) and it, not the state multiplier,
   is what governs deep-level feasibility. It had never been extracted.
3. **`wall ~ N^e` with `e > 1` makes prefix decomposition a CPU *win*** of
   `k^{e-1}` — 4.5× to 32× at a 100-way split — rather than the splitting tax the
   literature precedents warn about. (§6.2)
4. **The certified run's throughput decayed 6.3× within level 6** and was still
   decaying at the end. (§2.2)
5. **Level 6 at `n = 13` in the wide13 build is now a ~19–24 h job**, not a
   ~72 h one. (§6.1)
