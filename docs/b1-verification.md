# B1 independent verification protocol

Falsifiable outcome: Verifier A and Verifier B must agree on the artifact
identity, syntax classification, correctness verdict, and first
counterexample for every parsed negative case. Both must accept the public
45-comparator witness. Any disagreement fails B1 and blocks later gates.

Verifier A is a Python implementation that parses the canonical text itself,
enumerates input integers in ascending order, applies comparators to Boolean
arrays, and stops at the first unsorted output. Verifier B is a separate Go
implementation with its own parser; it represents each channel as a
bit-parallel truth table, propagates all inputs at once with AND/OR, and counts
failing inputs. Neither imports code from the other or from the gate driver.
They share only `docs/candidate-format.md` and candidate fixtures.

The frozen gate covers the public witness, four ordinary small networks, the
one-channel empty network, a syntactically legal repeated-comparator network,
a known invalid network, seven static malformed artifacts, a wrong-channel
invocation, and a missing-final-newline artifact. Reports for all static cases
are replayed byte-for-byte.

Reflection maps every comparator `(i,j)` to `(n-1-j,n-1-i)` without changing
its sequence position or layer. This is a valid sorting-network metamorphism
under simultaneous wire reversal and Boolean duality; arbitrary channel
permutations are not assumed valid. The gate applies reflection to positive
and negative fixtures and requires verdict preservation.

Three single-comparator deletions of the public witness are admitted as
negative mutation cases only when both verifiers independently return
counterexamples in the same gate. Before freezing the selection, an unscored
feasibility check independently rejected removal indices 0, 22, and 44 with
first failing inputs 1, 456, and 254 respectively in both implementations.
The scored gate re-establishes those results. Random differential cases are
reconstructed from the frozen seed. The exhaustive subset is every sequence
of length zero through three over the three possible comparators on three
channels: 40 cases, of which exactly six are sorting networks.
