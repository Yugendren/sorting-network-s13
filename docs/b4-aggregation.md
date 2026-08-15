# B4 aggregation and stop protocol

Falsifiable outcome: B4 passes only if the exact frozen B0--B3 PASS evidence
identities remain intact, every immutable evidence inventory validates, the
semantic facts required by the contract agree across their source files, and
the generated report contains every required section and truth label. Any
checksum change, verifier disagreement, missing seed, candidate below the
contract boundary, certificate mismatch, failed prerequisite, or incomplete
report fails B4.

B4 performs no search and launches no scientific workload. It reads the
already committed evidence, checks the four accepted gate identities, checks
all preserved scored-run manifests, and writes one immutable report into its
own B4 evidence directory. The report includes all 20 SENSO, greedy, and
random seed results rather than replacing absent values with defaults.

The report is the canonical human-readable terminal record. It must contain
exactly one terminal-verdict token. A B4 directory that already contains a
terminal report prevents rerunning the gate, even if later finalization were
to fail; this avoids issuing a second verdict. `make report` displays the
canonical report without generating or modifying evidence.

Passing B4 records laboratory readiness only. The next action is limited to
obtaining approval for and freezing a new experimental contract. This gate
does not draft or execute that contract, search for a smaller network, or make
a novelty claim.
