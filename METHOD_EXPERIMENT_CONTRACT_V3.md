# Mericanii S(13) research programme contract, version 3
# Dual-track: evolution 44-hunt + proof engineering

Created: 2026-08-17
Branch: main
Supersedes as active authority: METHOD_EXPERIMENT_CONTRACT_V2.md (its goal
`goal/s13-feature-eng-v1-omp` is PARKED at gate F0, not terminated; its
evidence rules remain binding for that branch if ever resumed).

## 1. Objective

Definitively settle S(13) ∈ {44, 45}:

- **Track A (upper bound)**: an LLM-outer-loop program-evolution harness
  searching for a valid 44-comparator network. Terminates the programme
  instantly if a 44 exists and is found.
- **Track B (lower bound / proof engineering)**: make the exact
  lower-bound computation (Harder's sortnetopt DP, which settled
  S(11)=35 and S(12)=39) feasible for n=13 by attacking its memory
  exponent, guided by measurement, ML-ordered (never ML-decided) search,
  and GPU offload of compute-bound kernels.

Anchor documents: `SOLUTION_STRATEGY.md`, `docs/research-programme.md`
(milestones M0–M5 with kill/pivot rules), `docs/sota-survey.md`
(literature, 2026-08-17), `docs/evolution-harness-design.md`.

## 2. Inherited pins (immutable)

- B0–B4 and e0–final evidence trees: never alter, delete, or regenerate.
- Frozen Python verifier SHA-256:
  `b420583606173d9f892e48e5656580792d2a4a2aa27a39f9a599ff5770e9ab2e`
- Frozen Go verifier SHA-256:
  `a07336fb4d4d1b8c7b275fd00fe65173df3fd8cb4f9ebd017cc90e1ecea1ee2f`
- Frozen SENSO binary SHA-256:
  `1d6fe20b547fa0e9dd9c899e34b608ac157104f63fd845d858e6e4ae9c0e6cc6`
- sortnetopt upstream pin: commit
  `0b5d09c47446096f9e3a0812b35afc72b7f2a718` (github.com/jix/sortnetopt);
  the pinned clone under `.cache/third_party/sortnetopt` is never
  modified — all changes are project-owned patches applied to detached
  worktrees, per the established `tools/setup_sortnetopt.py` pattern.
- n=11 certificate: Zenodo 10.5281/zenodo.4108365, decompressed SHA-256
  `7fe9f5cd694714bf83da0bcab162a290eb076ad4257265507a74cea8fab85b7e`.
- SENSO matched-compute baseline: 2/60 seeds reach ≤45 at
  50,200 evaluations per seed.
- Research snapshot: `44 <= S(13) <= 45` (44 bound provenance: van
  Voorhis two-channel theorem + S(11)=35; folklore 2025; see side quest).

## 3. Authorisations

1. Track A harness under `track_a/`: LLM (Claude subscription, any tier)
   as outer-loop mutator/strategist; deterministic local evaluator;
   append-only ledger. LLMs are never scored inner-loop oracles: no LLM
   call occurs inside a scored evaluation.
2. Track B lower-bound work: profiling, algorithmic modification of the
   search (via project-owned patches), out-of-core/distributed execution,
   GPU kernels, and ML models that ORDER exploration or PRE-FILTER exact
   checks. Explicitly authorised despite predecessor bans (those were
   scoped to their goals).
3. Local hardware: M4 Mac mini, 3060 box A (48 GB), 3060 box B (32 GB).
4. Cloud compute, budget-gated:
   - AWS: within the ~$500 USD credit pool; any single run with
     estimated cost > $50 requires explicit user approval beforehand.
   - RunPod: within ~40 SGD total; same per-run estimate discipline.
   - Every cloud run: cost estimate recorded before launch, actual cost
     recorded after, in the evidence ledger.
5. The 44 lower-bound write-up (`docs/s13-lower-bound-note.md`) as an
   internal document; publication or any external contact requires
   explicit user approval.

## 4. Prohibitions

- Using target 44 inside Track A scored search as a stopping bound or
  reward beyond natural comparator-count minimisation (finding a valid
  44 is the win condition, not a training signal to fake).
- Hard-coding any known witness network into Track A candidates.
- ML making pruning/soundness decisions in Track B: every pruning
  decision must trace to an exact, machine-checkable criterion; ML may
  only reorder work or pre-filter candidates for exact checks.
- Altering the pinned upstream clones, frozen verifiers, or any
  predecessor evidence.
- Publishing results or contacting maintainers/authors without user
  approval.
- Unbounded cloud spend: no run may start without a recorded estimate
  inside the budget pools above.

## 5. Evidence and integrity rules

- New evidence tree: `evidence/v3/`, append-only, same discipline as
  predecessors: exact commands, hashes, resource measurements, and
  outcomes for every scored run (success, failure, crash, timeout).
- Track A: any candidate at ≤45 comparators must pass BOTH frozen B1
  verifiers before being recorded as a success; a 44-comparator
  candidate triggers immediate stop-freeze-dual-verify and the
  witness-audit procedure of `PROJECT_CONTRACT.md`.
- Track B: any modified search must, at every development checkpoint,
  reproduce the known bounds bit-identically at n=9 (and n=10/n=11 when
  run) AND emit certificates accepted by the UNCHANGED Isabelle/HOL-
  verified checker (`snocheck`). A modified search that produces a
  different bound, or a certificate the checker rejects, is a defect —
  never evidence about S(13).
- Certificate or verifier disagreement, or tampering with pinned
  sources, renders the affected result `INVALID`.

## 6. Terminal verdicts

- `FOUND_44`: dual-verified 44-comparator network (either track) →
  S(13) = 44. Witness-audit procedure; no publication without approval.
- `PROVED_45`: independently checkable certificate that no 44-comparator
  network exists (full n=13 lower-bound computation gives ≥45, or an
  equivalent complete argument) → S(13) = 45.
- `PARTIAL`: restricted-class exhaustions and scaling results worth
  reporting, with the full question open. This is the honest default
  outcome and is a valid, documented completion state for any pause.
- `INFEASIBLE_FOR_NOW`: M1–M3 measurements show n=13 remains out of
  reach even with achieved improvements; programme pauses with complete
  negative evidence recorded.

There is no deadline and no version cap in this contract; gates are
milestone-driven (M0–M5) with the kill/pivot rules recorded in
`docs/research-programme.md`. One falsifiable milestone active per track
at a time.
