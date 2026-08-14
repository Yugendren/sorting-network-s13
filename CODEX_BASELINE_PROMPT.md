# Copy-paste prompt: build the S(13) baseline and stop

```text
/goal Build and verify the complete B0-B4 baseline for the Mericanii S(13)
sorting-network laboratory, issue one terminal baseline verdict, and stop
before any novel experiment.

WORKING DIRECTORY AND AUTHORITY

Run only inside:

/Users/yugendren/experiments/sorting_network_s13

Before editing:

1. Confirm the current directory exactly.
2. Read AGENTS.md, PROJECT_CONTRACT.md, GOAL_STATE.md, and README.md completely.
3. Inspect Git status, branch, recent commits, worktrees, local dependencies,
   available disk, CPU, and memory.
4. If this is not yet a Git repository, initialize it with main as the stable
   baseline, commit the supplied contract files unchanged, then create and work
   on `goal/s13-baseline`. Never implement directly on main.
5. Preserve unrelated user files and never modify sibling folders, including
   /Users/yugendren/defense,
   /Users/yugendren/experiments/deletion_code, and
   /Users/yugendren/experiments/mericanii_knowledge.

PROJECT BOUNDARY

The active goal is baseline readiness only:

- B0: audit and freeze current sources, artifacts, protocol, budgets, and
  evidence rules;
- B1: build two independent witness verifiers and verify the known 45-comparator
  13-input network;
- B2: reproduce the constructive SENSO-style 45-comparator baseline over the
  frozen 20 seeds plus transparent weaker baselines;
- B3: run Harder's n=9 exact workflow and independently replay the published
  n=11 certificate;
- B4: aggregate evidence, identify the baseline to beat, issue the verdict, and
  stop.

Do NOT:

- search for a 44-comparator network;
- attempt to prove 44 impossible;
- train ML or RL;
- build an LLM, multi-agent, diffusion, policy, value, or learned-ranking loop;
- use the RTX 3060 or rent a 4090;
- regenerate Harder's full n=11 search;
- publish, push, contact maintainers, or make novelty claims;
- weaken any gate to manufacture BASELINE_READY.

If a baseline unexpectedly returns a 44-comparator candidate, immediately
freeze the exact artifact and run only both B1 verifiers. Then stop and request
a new verification contract. Do not continue search or announce a result.

SCIENTIFIC RULES

The current `44 <= S(13) <= 45` snapshot is provisional until B0 re-audits it.
Use primary papers, official repositories, and current maintained artifact
lists. If the case is already solved, issue STALE_TARGET and stop; do not select
another problem.

Keep minimum size separate from minimum depth. Our problem is comparator count.
The known exact minimum depth of 9 is contextual only.

Every accepted candidate must pass two genuinely independent verifiers that
share only the input schema and fixtures. A solver status, a timeout, a copied
paper number, or one checker is not proof. Every certificate claim must be tied
to the exact artifact hash and independently replayed through the official or
audited checker.

Label facts as PUBLISHED, ARTIFACT_VERIFIED, LOCALLY_REPRODUCED, MEASURED,
ASSUMED, or UNKNOWN. Never turn an absent result into a default.

WORKING LOOP

Work serially through B0, B1, B2, B3, and B4 with at most one active gate.
For each gate:

1. State one falsifiable outcome.
2. Implement the thinnest complete end-to-end slice.
3. Run narrow tests.
4. Run the complete gate command.
5. Save immutable evidence with manifests and SHA-256 checksums.
6. Update documentation, traceability, and GOAL_STATE.md.
7. Commit the verified checkpoint with explicit paths.

After compaction or resumption, reconstruct truth from GOAL_STATE.md, Git,
tests, and evidence—not from conversation memory.

REQUIRED PROJECT SHAPE

Create a lean local project with pinned dependencies and, where appropriate:

- src/ for project-owned implementation;
- tests/ for unit, differential, corruption, and integration tests;
- docs/ for the mathematical specification, source ledger, trust boundary,
  licensing audit, and baseline protocol;
- config/frozen/ for immutable scored configurations;
- witnesses/ for small canonical checked witnesses;
- evidence/b0 through evidence/b4 for immutable results;
- evidence/reports/ for aggregate reports and final verdict;
- tools/ for auditable wrappers;
- third_party/ only for source-pinned, license-compatible small dependencies;
- external downloads, certificates, compiler caches, and large builds in a
  Git-ignored cache with their hashes recorded in evidence.

Expose these commands:

make setup
make verify
make baseline-b0
make baseline-b1
make baseline-b2
make baseline-b3
make baseline-b4
make baseline
make evidence-check
make report

Local verifier tests must not require cloud services or a GPU.

B0 — FREEZE

Re-audit and pin:

- the current maintained S(13) size bound and explicit 45-comparator witness;
- Harder's paper, official sortnetopt commit, official certificate URL/hash,
  checker dependencies, and license;
- the SENSO paper, author code artifact, license, and exact paper parameters;
- any replacement or clean-room implementation decision;
- the optional Wang prefix-plus-SAT source as context only.

Freeze:

- candidate schema;
- exact source/artifact hashes;
- 20 explicit seeds;
- primary M4 host and thread policy;
- random/greedy and SENSO-style baseline budgets;
- pass/fail/timeout rules;
- evidence manifest schema;
- contract and prompt hashes.

Do not vendor or modify code without a compatible license. If the legacy SENSO
artifact lacks permission or cannot run, document that and implement a
paper-faithful clean baseline without copying restricted source. Record every
deviation.

B1 — CONSTRUCTION TRUTH

Implement:

- Verifier A using direct enumeration of all 8192 Boolean inputs and sequential
  compare-and-swap semantics.
- Verifier B using a materially independent algorithm or language, such as
  bit-parallel channel truth tables or symbolic monotone Boolean functions.

Both must validate schema and return a concrete failing input/output on invalid
networks. Build positive, negative, malformed, randomized differential,
metamorphic, determinism, and checksum tests. Import the public 45-comparator
witness canonically and require both verifiers to accept it.

Any disagreement produces INVALID and stops the run.

B2 — CONSTRUCTIVE BASELINE

Run the frozen transparent baselines and the SENSO-style method:

- n=13;
- target <=45 comparators;
- population 200;
- 500 generations;
- 20 B0-frozen seeds;
- maximum 15 minutes single-thread-equivalent CPU per seed;
- aggregate cap 6 wall-clock hours and 10 GiB RAM;
- no GPU.

Validate every output using both B1 verifiers. Retain all seeds, failures, and
timeouts. Report success rate, best/median size, evaluations, time-to-45, CPU,
wall time, and peak memory. B2 passes only if at least one frozen SENSO-style
seed produces a valid network of 45 comparators or fewer under the cap.

B3 — EXACT/CERTIFICATE BASELINE

Pin and build Harder's official sortnetopt/checker stack.

1. Run its official n=9 search-and-verify workflow under a 10-minute/1-GiB cap.
2. Retrieve the official n=11 certificate from the linked archive.
3. Check the published checksum before replay.
4. Replay it under a 4-hour/12-GiB cap.
5. Record exactly what it proves locally and what S(12) statement remains a
   paper-derived corollary unless separately checked.
6. Demonstrate safe rejection of a corrupted small input/certificate.

Do not regenerate the n=11 search. The reference required nearly 200 GiB RAM
and roughly 80 hours; it is out of scope and impossible on this M4.

B4 — REPORT AND STOP

Generate:

- evidence/reports/baseline-report.md
- evidence/reports/baseline-results.json
- evidence/reports/baseline-verdict.md
- evidence/checksums.txt

The report must distinguish published, artifact-verified, locally reproduced,
and measured facts. Include every seed, failure, timeout, resource measurement,
unreproduced claim, and license limitation. Identify the exact strongest
constructive baseline and state the later experimental threshold needed to beat
it, but do not design or implement the learned method.

Issue exactly one verdict:

- BASELINE_READY
- CONDITIONAL
- BLOCKED
- INVALID
- STALE_TARGET

Only BASELINE_READY means the laboratory is ready for a separately authorized
Mericanii experiment. Stop immediately after the clean final replay, final
commit, and handoff.

FINAL HANDOFF

Report:

- branch and final commit;
- every command actually run;
- B0-B4 verdicts and evidence paths;
- verifier agreement status;
- 20-seed constructive success distribution;
- n=9 reproduction and n=11 certificate-replay result;
- measured CPU/RAM/wall time and disk use;
- external artifacts not committed;
- unresolved risks;
- one next prerequisite for the later experimental contract.

Do not claim that S(13) was solved merely because the baseline is ready.
```

