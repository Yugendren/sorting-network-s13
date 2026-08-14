# Trust boundary

Verifier A and Verifier B may share only the candidate format specification
and immutable fixtures. They must not import common candidate parsing,
network-execution, sortedness, or counterexample logic. A is direct exhaustive
zero-one enumeration. B is a separately implemented bit-parallel truth-table
checker in another language.

The maintained catalog supplies a candidate, not a correctness oracle. A
candidate becomes accepted only when both verifiers independently accept the
same checksum. Any disagreement is `INVALID` and blocks B2-B4.

The sortnetopt search executable is not its own proof. B3 accepts a lower-bound
claim only after the exact certificate hash is checked and the official
checked pipeline returns the corresponding bound. The parser and runtime
around Harder's extracted checker remain in the trusted computing base; the
formally verified core and its strictness/parallelism patch are recorded
separately.

Scored evidence is append-only by run directory. A manifest identifies the
source commit, clean/dirty state, command, frozen configuration hash, host,
times, CPU, peak memory, thread policy, artifacts, and terminal status. Each
run ends with a checksum inventory. Missing, changed, or unexpected files make
the evidence check fail.
