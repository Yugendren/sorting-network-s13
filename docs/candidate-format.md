# Canonical candidate format

The shared interchange format is strict UTF-8 text named
`sorting-network-v1`. Verifier implementations may share this document and
fixtures, but must not share parsing, execution, or validity code.

```text
sorting-network-v1
channels <positive decimal integer>
declared_count <nonnegative decimal integer>
layer_count <nonnegative decimal integer or ->
source <nonempty single-line provenance URL or identifier>
truth_label <PUBLISHED|ARTIFACT_VERIFIED|LOCALLY_REPRODUCED|MEASURED|ASSUMED|UNKNOWN>
comparators_begin
<lower channel> <upper channel> [<zero-based layer>]
...
comparators_end
sha256 <64 lowercase hexadecimal digits>
```

The checksum is SHA-256 over the exact bytes from `sorting-network-v1` through
the newline immediately after `comparators_end`. The checksum line and its
final newline are excluded. Files must end immediately after the checksum
line's newline. CRLF, a missing final newline, blank lines, comments, duplicate
headers, unknown headers, and trailing bytes are rejected.

Channel indices are zero based. Every comparator must satisfy
`0 <= lower < upper < channels`; no implicit normalization is performed. The
number of comparator records must equal `declared_count`. Comparator records
may all omit layers, or all include them. If layers are present,
`layer_count` is required, layers must be nondecreasing and in range, and no
two comparators in one layer may touch the same channel. If layers are absent,
`layer_count` must be `-`. Layer annotations never change comparator-count
semantics.

Repeated comparator pairs are syntactically legal and reported as warnings.
Correctness is determined independently by each verifier.
