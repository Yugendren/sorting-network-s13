# B2 constructive execution protocol

Falsifiable outcome: all 20 frozen seeds must be reported, and at least one
pinned SENSO run must return a network of at most 45 comparators that both B1
verifiers accept. A run failure or timeout is retained as `MEASURED`; it is
never interpreted as proof. Any accepted candidate below 45 triggers the
exceptional contract stop after only the two verifier checks.

The mixed-license `symmetry-1.1` distribution remains external and Git-ignored.
`tools/setup_senso.py` verifies the author archive, extracts it into a unique
attempt directory, applies the audited three-change portability patch, builds
serially, links the sorting executable, and smoke-tests it. Failed setup
attempts are retained. The active build manifest records every command and
hash; B2 copies that manifest, not the source or binary, into evidence.

The author implementation directly supplies the top-half estimation/copy
operator, Gaussian truncation, and 0.5 model/random comparator choice described
in the paper. The paper specifies the Variant 2 preference but not its command
line probability; mapping Variant 2 to the source switch
`sn.mutation.mksym=1` is explicitly `ASSUMED`. The paper's original seeds are
`UNKNOWN`; this run uses the 20 new seeds frozen in B0.

Each SENSO run uses population 200 and generation 500. Only the final compressed
milestone is requested. The best hall-of-fame network is converted to the
canonical unlayered candidate format, then checked by Verifier A and Verifier
B. Raw stdout, stderr/resource output, milestone, candidate, exact command,
times, evaluations, and verifier reports are retained per seed.

The transparent greedy baseline is the same pinned initialization operator with
population 20 and generation 0 for each seed. The transparent random baseline
performs 100 trials per seed, sampling comparator pairs uniformly with
replacement until the network sorts or 512 comparators are reached. It returns
only the smallest valid candidate per seed; trial sizes and all unsuccessful
trials remain in the report. Each returned greedy, random, or SENSO candidate
must pass both B1 verifiers.

macOS exposes address-space resource constants but rejected lowering their
limits in a setup probe. CPU is therefore kernel-limited with `RLIMIT_CPU`,
while the parent polls aggregate process-tree RSS every 0.25 seconds and kills
the complete process group at the frozen memory cap. Wall caps use the same
process-group termination path.
