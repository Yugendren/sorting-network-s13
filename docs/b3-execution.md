# B3 exact and certificate execution protocol

Falsifiable outcome: B3 passes only when the pinned official
`search_and_verify.sh 9 DATADIR` workflow returns `Some (9,25)`, a deliberately
corrupted but parseable copy of its small certificate returns `None`, and the
exact published n=11 certificate returns `Some (11,35)`. Missing dependencies,
timeouts, memory-cap violations, parse failures, checksum mismatches, or any
different checker result fail the gate. No unsuccessful search is interpreted
as a lower-bound proof.

Harder's unlicensed repository remains external and Git-ignored at commit
`0b5d09c47446096f9e3a0812b35afc72b7f2a718`. The native Rust search executable
is built without source changes. The checker remains on the upstream
`lts-14.10` snapshot and checked-in extracted Isabelle code. On this arm64 Mac,
an isolated Stack 3.11.1 installation selects the snapshot's x86_64 GHC 8.6.5
binary under Rosetta. A generated, hashed wrapper adds only Stack's
`--arch x86_64` portability selection; it does not patch the checker or its
dependencies. Setup records the upstream aggregate hash, lock hash,
strict/parallel patch hash, commands, logs, and executable identities. Failed
setup attempts are retained.

The Zenodo file is downloaded resumably to `.cache/certificates`. Its frozen
compressed size (1,247,864,564 bytes) and MD5 are checked before it is renamed,
then its decompressed SHA-256 is checked against the digest published by the
author. Both the compressed and 3,068,651,498-byte uncompressed files remain
external and are never committed. B3 hashes the uncompressed certificate
immediately before and after the read-only replay and commits only its identity
and replay output.

The n=9 workflow is capped at 600 wall seconds and 1 GiB process-tree RSS. The
n=11 replay is capped at 14,400 wall seconds and 12 GiB process-tree RSS. A
parent monitor terminates the complete process group on either cap; macOS
`time -l` provides an additional measurement. The upstream executables retain
their default parallelism, so the host's ten logical cores are recorded.

The generated n=9 `proof.bin` is small enough to retain in evidence. Its root
proof-step bound byte is changed to an impossible high value without damaging
the container format; clean `None` output is required. The local n=9 result
establishes `S(9) >= 25`, and the published n=11 certificate replay establishes
`S(11) >= 35`. The equality `S(11)=35` and the derived `S(12)=39` remain labeled
`PUBLISHED` because B3 does not separately replay their matching constructions
or an n=12 certificate. Full n=11 search regeneration is prohibited.
