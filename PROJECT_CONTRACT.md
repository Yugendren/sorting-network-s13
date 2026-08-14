---
title: "Mericanii S(13) Sorting-Network Baseline Contract"
status: proposed-for-execution
version: 1
created: 2026-08-15
as_of: 2026-08-15
scope: "Baseline only; B0-B4"
---

# Mericanii S(13) Sorting-Network Baseline Contract

## 1. Objective

Build a small, reproducible, proof-aware laboratory that can recognize a valid
13-input sorting network, reproduce the known 45-comparator constructive
baseline, and replay established lower-bound evidence. Stop before attempting
the open 44-comparator question.

The baseline answers four questions:

1. Do we represent the problem correctly?
2. Can two independent implementations determine whether a candidate works?
3. Can an accessible classical search rediscover the known 45-comparator
   result under a frozen budget?
4. Can we independently replay a real certificate from the exact lower-bound
   literature?

`BASELINE_READY` is laboratory readiness, not a discovery.

## 2. Exact problem

A comparator on channels `i < j` replaces the pair `(x_i, x_j)` with:

\[
(\min(x_i,x_j),\max(x_i,x_j)).
\]

A comparator network is an ordered finite list of comparators. It is a sorting
network on `n` channels if it maps every input to nondecreasing order.

Let:

\[
S(n)=\min\{|C|:C\text{ is a sorting network on }n\text{ channels}\}.
\]

The zero-one principle states that a comparator network sorts all totally
ordered inputs if and only if it sorts every Boolean input in `{0,1}^n`.
Therefore a 13-input candidate is checked on exactly:

\[
2^{13}=8192
\]

Boolean inputs.

### Current frontier to re-audit

As of 2026-08-15, the maintained public snapshot is:

\[
44 \le S(13) \le 45.
\]

Do not confuse minimum size with minimum depth. The exact minimum depth at 13
inputs is already 9. The active future frontier is minimum size.

### What would eventually settle the problem

- A valid explicit 44-comparator network proves `S(13)=44`.
- A replayable global proof that no 44-comparator network exists, combined with
  the known 45-comparator witness, proves `S(13)=45`.

Neither is part of this baseline execution.

## 3. Primary sources and artifacts

Re-audit, pin exact versions, and record retrieval dates during B0.

### Current bound and known witnesses

- Maintained catalog:
  https://bertdobbelaere.github.io/sorting_networks_extended.html

### Certified minimum-size precedent

- Jannis Harder, *An Answer to the Bose-Nelson Sorting Problem for 11 and 12
  Channels*:
  https://arxiv.org/abs/2012.04400
- Official implementation and checker:
  https://github.com/jix/sortnetopt
- Published n=11 certificate is linked by that repository and archived at
  Zenodo. The repository currently reports uncompressed SHA-256:
  `7fe9f5cd694714bf83da0bcab162a290eb076ad4257265507a74cea8fab85b7e`.

### Constructive evolutionary baseline

- Valsalam and Miikkulainen, *Using Symmetry and Evolutionary Search to
  Minimize Sorting Networks*:
  https://www.jmlr.org/papers/volume14/valsalam13a/valsalam13a.pdf
- Author-hosted code page:
  https://nn.cs.utexas.edu/?sorting-code=

The paper used population 200, 500 generations, and 20 runs. It reproduced the
45-comparator 13-input result. Its harder 16-input runs took about 15 minutes
each on one 2.83 GHz Xeon X5440.

### Optional modern construction reference

- Wang, *Depth-13 Sorting Networks for 28 Channels*:
  https://arxiv.org/abs/2511.04107
- Implementation:
  https://github.com/wcgbg/sorting-network-n28d13

This structured-prefix plus SAT pipeline took under 20 minutes on an M2 Mac
mini with 16 GiB RAM. It is useful context but is not a B0-B4 pass dependency.

## 4. Truth labels

Every report must distinguish:

- `PUBLISHED`: stated by a pinned source.
- `ARTIFACT_VERIFIED`: independently checked local artifact.
- `LOCALLY_REPRODUCED`: regenerated locally from pinned source/code.
- `MEASURED`: produced by this implementation and run manifest.
- `ASSUMED`: deliberately frozen but not independently established.
- `UNKNOWN`: unresolved; never silently replaced by a default.

## 5. Canonical candidate format

Use a stable text or JSON representation containing:

- schema version;
- number of channels;
- ordered list of comparator pairs;
- declared comparator count;
- optional layer annotation that does not affect size semantics;
- source/provenance;
- SHA-256 checksum.

Validation must reject:

- channel indices outside `[0,n)`;
- `i >= j` unless a documented canonicalizer normalizes the pair first;
- malformed pairs;
- declared count mismatch;
- unexpected data after the artifact;
- wrong channel count.

Repeated comparators are syntactically legal but should be reported because
they are normally redundant. Correctness, not appearance, determines validity.

## 6. Independent verification contract

Build two verifiers that share only the candidate schema and test fixtures.
They must not share network-execution or validity logic.

### Verifier A — direct enumeration

- Enumerate integers `0..8191` as Boolean inputs.
- Apply comparators sequentially.
- Reject on the first unsorted output.
- Emit the exact failing input and output.

### Verifier B — independent representation

Use a materially different implementation, such as bit-parallel channel truth
tables, symbolic monotone Boolean functions, or a second language. It must
produce its own failing input/counterexample and count.

### Required tests

- public 45-comparator witness accepted by both;
- trusted small sorting networks accepted;
- deliberately invalid networks rejected with counterexamples;
- malformed artifacts rejected;
- deterministic output and checksums;
- randomized differential testing;
- channel permutation/reflection metamorphic tests where mathematically valid;
- mutations of the 45-comparator witness, retaining only mutations independently
  confirmed invalid before using them as negative fixtures;
- exhaustive agreement over all tractable small candidate spaces or a frozen
  exhaustive subset.

Any verifier disagreement makes the laboratory `INVALID` and blocks all later
search.

## 7. Baseline milestones

### B0 — Freeze source, scope, and protocol

Required outputs:

- current-status audit with primary/current sources;
- pinned repository commits, licenses, artifact URLs, and hashes;
- exact candidate schema;
- frozen 20 seeds;
- hardware/thread policy;
- budgets and stop rules;
- immutable evidence policy;
- project dependency lock;
- contract and prompt hashes.

If `S(13)` is already settled, issue `STALE_TARGET` and stop.

### B1 — Establish construction truth

Required outputs:

- two independent verifiers;
- public 45-comparator witness in canonical format;
- complete positive, negative, malformed, differential, and metamorphic tests;
- deterministic verifier reports and hashes.

Pass only if both verifiers agree on every frozen case and both accept the
public witness.

### B2 — Reproduce the constructive baseline

Audit the SENSO license and code first. If redistribution or modification is
not authorized, do not vendor it. Run it as an external pinned artifact where
lawful, or implement a clean paper-faithful baseline with documented deviations.

Frozen initial configuration:

- problem: 13 inputs;
- target: at most 45 comparators;
- population: 200;
- generations: 500;
- seeds: 20 explicit values frozen at B0;
- per-seed cap: 15 minutes single-thread-equivalent CPU time;
- aggregate constructive cap: 6 wall-clock hours and 10 GiB RAM;
- GPU: prohibited;
- every returned candidate checked by both B1 verifiers.

Also run transparent random/greedy baselines under a declared smaller budget so
the SENSO-style result is not compared only with itself.

B2 passes when at least one frozen SENSO-style seed produces a valid network of
45 comparators or fewer within the aggregate cap. Report all 20 seeds, success
rate, best size, evaluations, CPU time, wall time, memory, and failures. Do not
report only the best seed.

Finding 44 during a baseline would be an unexpected frontier artifact. Stop,
freeze it, run only the two verifiers, and ask the user for a new verification
contract; do not continue searching or claim discovery under this baseline
contract.

### B3 — Reproduce exact/certificate capability

Pin Harder's official repository and checker.

Required:

1. Run the official 9-channel search-and-verify workflow. The author's reference
   is under 10 seconds and 50 MB, but local measured performance governs.
2. Obtain the published n=11 certificate from the official link/archive.
3. Verify its published checksum before replay.
4. Replay it through the official checked pipeline.
5. Record exactly what local result the certificate establishes and what
   statement about `S(12)=39` is only derived from the paper unless separately
   replayed.
6. Corrupt a copy of a small certificate or input and confirm safe rejection.

Hard caps:

- n=9 exact workflow: 10 wall-clock minutes, 1 GiB RAM;
- n=11 certificate replay: 4 wall-clock hours, 12 GiB RAM;
- downloaded certificate/cache: never commit to Git;
- total baseline compute after setup: 12 wall-clock hours;
- GPU: prohibited.

Explicitly prohibited: regenerating Harder's complete n=11 search. The public
reference required nearly 200 GiB RAM and roughly 80 hours on a 48-thread EPYC
system. This machine cannot reproduce it safely and baseline readiness does not
require it.

### B4 — Aggregate and stop

Generate a report containing:

- source/artifact ledger;
- verifier agreement and negative tests;
- all 20 constructive seeds and transparent baselines;
- n=9 exact reproduction;
- n=11 certificate checksum/replay status;
- hardware and resource accounting;
- unreproduced claims and why;
- strongest baseline to beat in the later Mericanii experiment;
- exact next prerequisite, without implementing it.

Then issue exactly one terminal verdict and stop.

## 8. Terminal verdicts

- `BASELINE_READY`: B0-B4 all pass; known 45 is independently verified and
  rediscovered; exact certificate replay works; evidence is complete.
- `CONDITIONAL`: construction truth is sound, but a named nonfatal legacy-code
  or certificate portability problem prevents full reproduction.
- `BLOCKED`: a required artifact, dependency, license, or resource prevents a
  mandatory gate.
- `INVALID`: verifier disagreement, encoding mismatch, certificate failure, or
  evidence-integrity failure makes results unusable.
- `STALE_TARGET`: the current audit shows the open problem has already been
  settled.

Only `BASELINE_READY` authorizes drafting the later experimental contract. It
does not automatically authorize its execution.

## 9. Compute and hardware policy

The baseline is CPU/RAM work, not neural training.

- Primary host: Apple M4 Mac mini, 10 CPU cores, 16 GiB RAM.
- RTX 3060: prohibited for B0-B4; reserve for a future learned ranker.
- RunPod/4090: prohibited.
- No full n=11 regeneration.
- No full n=13 lower-bound search.
- Parallelism, thread count, and CPU time must be recorded.
- A timeout is a measured failure, never an impossibility result.

Expected after setup, not an acceptance guarantee:

- public witness verification: under one second;
- 20-seed constructive batch: approximately 1--6 hours;
- n=11 certificate checking: approximately 0.5--3 hours;
- total actual baseline compute: hours, not weeks.

## 10. Evidence contract

Each scored run gets an immutable directory containing:

- run ID;
- source commit and dirty-state flag;
- configuration and SHA-256;
- dependency/tool versions;
- host, CPU, RAM, operating system, and thread count;
- seed and resource limits;
- exact command;
- start/end, wall time, CPU time, and peak memory;
- stdout/stderr;
- candidate/certificate artifacts and hashes;
- both verifier reports where applicable;
- terminal status including timeout/crash;
- manifest and checksum inventory.

Never overwrite a scored run. Preserve invalid outputs, failed seeds, and
timeouts. Large third-party downloads and build caches remain Git-ignored but
their URLs, versions, sizes, and hashes belong in evidence.

## 11. Required project interface

The baseline implementation should expose:

```text
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
```

Commands must fail loudly on missing tools, invalid witnesses, verifier
disagreement, failed certificate replay, exceeded mandatory evidence, or dirty
scored configuration.

## 12. Out of scope

- searching for 44 comparators;
- proving 44 impossible;
- ML/RL/diffusion or LLM-guided search;
- learned prefix, policy, or value models;
- fine-tuning any model;
- GPU benchmarking or rental;
- physical sorting hardware;
- product claims;
- public paper, press, or record submission;
- changes to sibling Mericanii repositories.

