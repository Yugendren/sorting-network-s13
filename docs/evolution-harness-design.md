# LLM-Evolved Constructor Harness — Design Sketch

Last updated: 2026-08-17. Companion to `SOLUTION_STRATEGY.md` attack #1.

## Core idea

Evolve *programs that build sorting networks*, not networks directly.
The LLM (Claude, via this Claude Code session — no API key required)
plays the mutation/crossover operator. All scoring is local, deterministic,
and LLM-free.

```
┌────────────────────────────────────────────────────────┐
│ Claude Code session (subscription — no API key)        │
│  reads: top-K programs + scores + failure diagnostics  │
│  writes: N new candidate programs per generation       │
└──────────────┬─────────────────────────────────────────┘
               │ .py files in pool/
┌──────────────▼─────────────────────────────────────────┐
│ Local evaluator (M4 + 3060 boxes, pure CPU, no LLM)    │
│  runs each program → emits comparator network(s)       │
│  scores: sorts-all-8192? comparator count? partials?   │
│  appends every result to the ledger                    │
└────────────────────────────────────────────────────────┘
```

## Why no API key

- Interactive mode: the user runs generations inside Claude Code sessions;
  Claude reads the scoreboard file and writes mutants directly.
- Semi-automated: `claude -p "<mutate prompt>"` (headless CLI) can be
  invoked by a driver script — still uses the existing subscription.
- A raw Anthropic API key is only needed if we want a fully unattended
  24/7 loop with programmatic API calls. Not required to start; decide
  later if generation throughput becomes the bottleneck.

## Candidate representation

Each candidate = one small Python file exposing:

```python
def build(params: dict) -> list[tuple[int, int]]:
    """Return comparator list [(lo, hi), ...] for 13 channels."""
```

Programs may implement: greedy constructions, layer patterns,
symmetry-mirrored builders, prefix libraries + local search completers,
annealing over suffixes — anything deterministic given `params`.

## Evaluation (the cheap part)

- Zero-one principle: a 13-channel network is a valid sorter iff it sorts
  all 2^13 = 8192 binary vectors. That is **microseconds in C, ~ms in
  numpy** (vectorized: 8192×13 bit-matrix, one min/max per comparator).
- Score tuple (lexicographic): (unsorted_vector_count, comparator_count).
  Valid sorter with fewer comparators always wins.
- Rich diagnostics fed back to Claude: which vectors fail, per-channel
  output-set sizes, where progress stalls — so mutations are informed,
  not blind.
- Any claimed <=45 network additionally goes through both frozen B1
  verifiers before entering the ledger as a success.

## Hardware roles

| Machine | Role |
|---|---|
| M4 Mac mini | Orchestrator: pool, ledger, Claude Code session, verifiers |
| 2× RTX 3060 boxes | CPU evaluation farm: each program's inner parameter/restart sweeps (GPUs idle for this attack; reserved for ranker training if #4 continues) |

Throughput estimate: a network evaluation is ~10^-5 s; the bottleneck is
how many *ideas* per day, not compute. This is exactly why the LLM-outer-
loop design is compute-efficient: expensive intelligence only between
generations, cheap arithmetic inside them.

## Generation cycle (one "tick")

1. Evaluator scores every program in `pool/` across its parameter sweep
   (parallel across machines; results → `ledger/scores.jsonl`, append-only).
2. Claude reads scoreboard + diagnostics of top-K (e.g. K=10) and
   worst-failure examples.
3. Claude writes N (e.g. 20) new programs: mutations, crossovers,
   fresh ideas seeded by literature patterns (Batcher, Green filters,
   Valsalam–Miikkulainen symmetry).
4. Pool pruned to top-M by score with diversity protection.
5. Every program file is content-hashed; nothing is deleted from the ledger.

## Success ladder (falsifiable gates)

1. Harness produces *any* valid 13-sorter (sanity, expect ~immediate).
2. Evolved programs reach 45 comparators (match SENSO/known witness).
3. Beat SENSO's matched-compute baseline: >2/60 seeds reaching 45.
4. A 44 appears → stop everything, freeze, run witness-audit procedure.

Gate 3 is the first scientifically interesting result; gate 4 solves the
problem. Failure to pass gate 2 after a bounded budget is itself a clean
negative result.

## Model-tiered subagents (token economics)

Defined in `.claude/agents/`. Route each job to the cheapest model that
does it well; premium models only where creativity pays.

Four-tier delegation chain — each tier hands work down to the cheapest
model that can do it:

```
Fable  architect   strategy memo, every ~5 generations
  └─► Opus  lead       owns one major subtask end-to-end
        └─► Sonnet  mutator   writes program variants
              └─► Haiku  runner    zero-judgment execution
```

| Agent | Model | Used for | Frequency |
|---|---|---|---|
| `architect` | Fable | diagnose stagnation, invent strategy families, set pool policy | every ~5 generations |
| `lead` | Opus | own one major subtask (a family build-out, a new mechanism, evaluator upgrades); decompose + delegate + verify | per subtask |
| `mutator` | Sonnet | write program variants from scoreboard + diagnostics | every generation |
| `runner` | Haiku | run evaluator, parse logs, grep ledger, hash files, ledger appends | constantly (cheap) |
| built-in `Explore` | fast | codebase search / file location | as needed |

Rule of thumb: ~90% of calls land on Haiku/Sonnet. Fable touches only
the distilled scoreboard summary, never raw logs; Opus sees one
subtask's context, not the whole campaign. Leads and mutators can run in
parallel (disjoint subtasks / program families, disjoint files).

## Open items before build

- v3 contract authorising LLM-outer-loop evolution (v2's ban was scoped
  to the feature-eng goal).
- Fix the evaluation budget per generation and the pool sizes (K, N, M).
- Decide interactive vs. headless-CLI generation driver.
