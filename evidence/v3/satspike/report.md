# Tier-3 SAT-Hybrid Feasibility Spike — VERDICT: REJECT

Date: 2026-08-17. Author: spike lead agent (report persisted by the
orchestrating session because the agent's configuration blocked writing
markdown report files; content verbatim from its final report).

## Verdict

**REJECT** — not even "adopt-for-UNSAT-only": UNSAT is the *worse*
direction for SAT here, and it is the only direction exhaustion needs.
The criterion was "SAT wins if >=5x faster on UNSAT at n=9/n=10."
Measured: kissat was **1,000x-17,600x slower** on every UNSAT instance
it finished, and finished none of the ten primary target instances.
Missed by 4-5 orders of magnitude in the wrong direction.

## Headline instance table

Engine time = internal search-phase wall clock (see timing correction
below). All SAT models re-verified against all 2^n inputs; all UNSAT
answers DRAT-checked by drat-trim (`s VERIFIED`).

| n | prefix | k | c* | expect | got | SAT | engine | ratio |
|---|---|---|---|---|---|---|---|---|
| 9 | 16 | 10 | 11 | UNSAT | UNSAT | 3.23 s | 3 ms | 1,077x |
| 9 | 16 | 11 | 11 | SAT | SAT ok | 1.64 s | 3 ms | 547x |
| 9 | 14 | 12 | 13 | UNSAT | UNSAT | 91.63 s | 6 ms | 15,272x |
| 9 | 14 | 13 | 13 | SAT | SAT ok | 1.12 s | 6 ms | 187x |
| 10 | 16 | 15 | 16 | UNSAT | TIMEOUT 600 s | >600 s | 34 ms | >17,647x |
| 10 | 16 | 16 | 16 | SAT | SAT ok | 92.01 s | 34 ms | 2,706x |
| 9 | 8 | 16 | 17 | UNSAT | TIMEOUT 600 s | >600 s | 50 ms | >12,000x |
| 9 | 8 | 17 | 17 | SAT | TIMEOUT 180 s | >180 s | 52 ms | — |
| 10 | 9 | 19 | 20 | UNSAT | not attempted (k=14 already >300 s) | — | 241 ms | — |

Budget frontier (n=9, p=8, |U|=62, c*=17): k=8 -> 0.51 s, k=10 ->
2.39 s, k=11 -> 7.75 s, k=12 -> 28.15 s, k=13 -> 133.41 s, k=14 ->
>300 s, k=16 -> >600 s; clause count over that range moves only
108k -> 233k. Cube-and-conquer (n=9, p=8, k=13; monolithic 137.4 s):
26 cubes, all UNSAT, 853.07 s total CPU (6.2x worse), 9% parallel
efficiency.

## Ground truth and a timing artifact fixed en route

Ground truth from the frozen engine via `sortnetopt -m search <n> -p
<prefix>`; on all 10 two-layer-prefix ladder instances p + c*
reproduced S(9)=25 and S(10)=29 exactly.

**Measurement hazard (programme-wide):** `Search::search`
(src/search.rs:46-56) spawns a stats thread sleeping in 10-second
intervals; the scope won't tear down until it ticks, so process wall
time has a ~10 s floor regardless of difficulty (n=9/p=8: real 10.01,
internal elapsed_ms 52). Any benchmark reading /usr/bin/time on
sub-second sortnetopt jobs is wrong by up to 200x. All engine numbers
above use internal elapsed_ms — the figure least favourable to the
spike's own conclusion.

## Encoding (size was never the problem)

BZ-style with five exact reductions (residual-set-only, sorted-vector
drop, constant end/start values, touched-indicator pass-through,
Foata adjacent-commutation symmetry breaking worth a measured 2.7x).
Hardest n=10 instance built: 225,066 clauses. Projected n=13
class-completion instance: |U|=418, ~5.3-7.6M clauses — 7x under the
abort threshold, and smaller |U| than n=10 instances that already
time out. **|U| is not the driver; the budget is** — instances at
gap 1 (exactly c*-1, the phase transition) are the slow ones, and
exhaustion campaigns live at gap 1 by definition.

## Proof parity

DRAT verified end-to-end (drat-trim) on all finished UNSAT instances,
but proofs grow ~4x per comparator of budget: extrapolated ~14 GB for
a question the engine settles in 50 ms. Formally fine, practically
inverted.

## n=13 projection

Gap-1 scaling base ~5.33 per comparator of budget => ~2x10^17 s per
class-completion instance (gentlest defensible base still ~10^12 s),
~100 canonical-prefix instances per class. **Gap to feasibility:
10-16 orders of magnitude.**

## Why SAT loses (structural)

The engine and cube-and-conquer explore the same decomposition (tree
of reachable output sets); the engine wins on canonical-form
memoization + subsumption + the Huffman bound. "This output set needs
>= b more comparators" is a statement about a *function of* the
assignment, not the assignment — not expressible as a learned clause,
so CDCL can never discover it. The measured 6.2x cube CPU inflation is
that lost sharing made visible.

## Consequences for the programme

1. The Tier-3 hybrid line is closed. Ranked-queue order otherwise
   unchanged; binding constraints for the 3-class campaigns remain
   Tier-1 #1-3, Tier-2 #5 (SDD) and #6 (prefix decomposition), plus
   the max-path tracer from docs/s13-shape-case-split.md section 7.3
   (now doubly motivated — it is also the only thing that could
   reopen this verdict, via class-restricted rather than layered
   prefixes; a two-hour drive.py re-run settles that if it lands).
2. **Narrow keep (Track A, protocol-gated, NOT run in this spike):**
   SAT is fast in the SAT polarity with slack (0.77-23.8 s at c*+2..+7
   vs timeout at c*) — a construction capability our lower-bound
   engine lacks. The tooling in .build/v3-satspike/ suffices for a
   Wang-2025-style prefix+SAT-completion upper-bound pipeline. Any
   such use falls under the witness-audit rules; no comparator count
   was used as a target anywhere in this spike (all instances n=9/10
   with engine-derived ground truth).
3. Engine `--limit` decision mode measured *faster* than full
   optimisation for the exhaustion question (50 ms at n=9/p=8) — the
   completion subproblem is simply not a bottleneck for us.

## Artifacts

Encoder/driver/cuber/projector/probes + kissat 4.0.4 and drat-trim
(user-space builds, hashes in agent transcript) under
.build/v3-satspike/; engine ground-truth logs and per-instance JSONL
records under .build/v3-satspike/work/. Nothing outside that tree was
created or modified; no server use; pinned clone untouched.
