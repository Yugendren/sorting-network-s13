# E1 dataset gate

Falsifiable outcome: E1 passes only if instrumentation adds no RNG calls or
search decisions, enabled and disabled sentinel runs reproduce the exact frozen
B2 candidate at 50,200 evaluations, all 20 development seeds preserve their B2
final sequences, exactly 1,004,000 schema-valid rows are saved, and every <=45
row maps to a candidate accepted by both frozen verifiers.

The patch is `tools/patches/symmetry-1.1-mericanii-instrumentation.patch`. It is
applied after the baseline portability patch in a separate ignored build tree;
the original SENSO binary is never modified. Logging activates only when both
`MERICANII_DATASET_PATH` and `MERICANII_DATASET_SEED` are provided. With neither
variable, the writer does not open a file or consume RNG state.

Run from a clean experiment commit:

```sh
make setup-method-instrumented
make method-e1
make evidence-check
```

Per-seed raw TSV files and their compressed concatenation remain under the
content-addressed `.cache/method-v1/datasets/` reference recorded in E1
evidence. They are made read-only and are not committed. Commands, complete
stdout/stderr, resource records, milestones, final candidates, verifier
reports, hashes, distributions, trajectory audit, and dataset manifest are
committed under `evidence/e1/`.

Any <=44 row flushes its exact sequence and stops the process immediately for
the contract's witness audit.
