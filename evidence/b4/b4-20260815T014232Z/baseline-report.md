# Mericanii S(13) baseline report

B4 run: `b4-20260815T014232Z`. Source commit: `307198dceb6a832e65725f8e84ef9423f1abb451`. Evidence date: 2026-08-15.

## Scope and result

This report closes the contracted B0--B4 baseline only. The objective is minimum comparator count, not minimum depth. The B0 maintained snapshot states `44 <= S(13) <= 45`; its depth-9 entry is context only. No 44-comparator search, nonexistence attempt, learned method, GPU work, publication, or external claim was performed.

All four prerequisite PASS manifests retain their frozen identities, all immutable inventories validate, the public 45-comparator witness passes both independent verifiers, a frozen SENSO-style seed locally reproduces size 45, and the official exact/certificate workflow returns the required n=9 and n=11 lower bounds.

## Truth-label key

- `PUBLISHED`: stated by a pinned source.
- `ARTIFACT_VERIFIED`: a pinned local artifact or witness was independently checked.
- `LOCALLY_REPRODUCED`: regenerated or replayed locally from pinned inputs.
- `MEASURED`: observed in this execution, without a mathematical inference beyond the observation.
- `ASSUMED`: frozen protocol choice not supplied by the historical source.
- `UNKNOWN`: not established by the available evidence.

## Source and artifact ledger

| ID | Role | Primary source and pin | Evidence state | License record |
|---|---|---|---|---|
| `dobbelaere-catalog` | current bound and public 45-comparator witness | [https://bertdobbelaere.github.io/sorting_networks_extended.html](https://bertdobbelaere.github.io/sorting_networks_extended.html); commit `49b355d484aa92c2a661b6ab1a2f981a60b7c0c6`; SHA-256 `8a2d11c9f2ac66e16ea93a9c4301971b47d3115eaf28d4e12b50079c8238d116` | ARTIFACT_VERIFIED snapshot; witness correctness ARTIFACT_VERIFIED by B1 | UNKNOWN |
| `harder-paper-v3` | certified lower-bound method and statements | [https://arxiv.org/pdf/2012.04400v3](https://arxiv.org/pdf/2012.04400v3); SHA-256 `48a54deefef544dce2e1b8b73babb501a3990628d0ddc582333bfb2f925fd203` | ARTIFACT_VERIFIED bytes; claims PUBLISHED | arXiv page links a Creative Commons license |
| `sortnetopt` | official search, certificate generator, and checked pipeline | [https://github.com/jix/sortnetopt.git](https://github.com/jix/sortnetopt.git); commit `0b5d09c47446096f9e3a0812b35afc72b7f2a718` | ARTIFACT_VERIFIED source; n=9 workflow LOCALLY_REPRODUCED | UNKNOWN (repository contains no LICENSE or COPYING file) |
| `harder-n11-certificate` | published certificate to replay, never commit | [https://zenodo.org/api/records/4108365/files/proof_cert_11.bin.zst/content](https://zenodo.org/api/records/4108365/files/proof_cert_11.bin.zst/content); DOI `10.5281/zenodo.4108365`; uncompressed SHA-256 `7fe9f5cd694714bf83da0bcab162a290eb076ad4257265507a74cea8fab85b7e`; compressed MD5 `2847374c6bab1260c9771d6fafe65f44` | ARTIFACT_VERIFIED identity; replay LOCALLY_REPRODUCED | CC-BY-4.0 |
| `valsalam-miikkulainen-paper` | SENSO algorithm and published parameters | [https://www.jmlr.org/papers/volume14/valsalam13a/valsalam13a.pdf](https://www.jmlr.org/papers/volume14/valsalam13a/valsalam13a.pdf); SHA-256 `59522734f52c0b4927e80eba4971a49ba6cc756ea5d072e382af57648544df3e` | ARTIFACT_VERIFIED bytes; method PUBLISHED | PUBLISHED JMLR article; redistribution terms not inferred |
| `symmetry-1.1` | author-hosted SENSO implementation | [https://www.cs.utexas.edu/users/nn/downloads/software/symmetry-1.1.tar.gz](https://www.cs.utexas.edu/users/nn/downloads/software/symmetry-1.1.tar.gz); SHA-256 `d3e960fa5c7b292e38a3024e76436fec3550baa27de240faa90568da0882b53c` | ARTIFACT_VERIFIED archive; frozen-seed runs LOCALLY_REPRODUCED | mixed; experiments/COPYING BSD-3-Clause, OpenBEAGLE/SN LGPL-2.1-or-later, bundled components retain their own terms |
| `wang-n28d13-context` | optional construction context only | [https://github.com/wcgbg/sorting-network-n28d13.git](https://github.com/wcgbg/sorting-network-n28d13.git); commit `41950ab137671c6573b6e65a00ba2e52c159fea8` | PUBLISHED optional context; not a gate input | MIT |

## Gate traceability and preserved attempts

Accepted prerequisite identities:

| Gate | Run | Source commit | Manifest SHA-256 | Inventory SHA-256 |
|---|---|---|---|---|
| B0 | `b0-20260814T230315Z` | `19bd4efadddf75182caa8012981917c0938aa2ed` | `c03750bcefdee513e4ef2a91fb8a8c9b209d26be3657075ea644ad80f92d4c9a` | `d565262ca77051f81df9b26ac08a098992e554704b84b379adcfc8f51af94e44` |
| B1 | `b1-20260814T231402Z` | `48bd3e136545095b807f6d68f7f13b7a27af5524` | `51c22ef534a0cce11676b39e05b8c601a9760f075efee0f5a5232a7195a37e44` | `00f6a1b9ad99555c39cc9a717f346e10edd83e7c9817cff325e93c24c811a008` |
| B2 | `b2-20260814T232833Z` | `a91a1710201d4f1c4b1f13e6473930ce8ec13184` | `8d057c43edb1e408d4334783cbb0a615110011bfa2aac121319ca32924888d74` | `bed371c2a5f9d1b6be646939f9dacdc3b67ef98a79f5c244702b17665b65ee18` |
| B3 | `b3-20260815T000708Z` | `5d44ca23742cd86b490ba366ad568b5322e4f21f` | `4398642fa4b0811b44d573894c3df4bbfe263486a9344cf44b274c8064266170` | `1610609bb2ff4b4c3d0e5b06ffd8188403b9e532366903379d7d640a03990268` |

All scored attempts, including superseded and failed runs:

| Run | Gate | Status | Wall s | CPU s | Peak MiB | Threads | Preserved outcome |
|---|---|---|---:|---:|---:|---:|---|
| `b0-20260814T230033Z` | B0 | FAIL | 0.054307 | 0.015548 | 24.33 | 1 | [Errno 2] No such file or directory: '/Users/yugendren/experiments/sorting_network_s13/.cache/third_party/sortnetopt/stack.yaml' |
| `b0-20260814T230128Z` | B0 | PASS | 0.816708 | 0.031756 | 24.81 | 1 | accepted or superseded PASS evidence |
| `b0-20260814T230315Z` | B0 | PASS | 0.733192 | 0.032372 | 24.84 | 1 | accepted or superseded PASS evidence |
| `b1-20260814T231402Z` | B1 | PASS | 11.401776 | 10.864997 | 82.08 | 1 | accepted or superseded PASS evidence |
| `b2-20260814T232833Z` | B2 | PASS | 399.690669 | 385.407711 | 82.61 | 1 | accepted or superseded PASS evidence |
| `b3-20260814T235403Z` | B3 | FAIL | 0.289428 | 0.005742 | 33.53 | 10 | n=9 official command ended as REJECTED |
| `b3-20260814T235503Z` | B3 | FAIL | 0.807490 | 0.127663 | 49.00 | 10 | n=9 official command ended as REJECTED |
| `b3-20260815T000143Z` | B3 | FAIL | 16.187146 | 27.425146 | 80.75 | 10 | expected exactly one checker result line, found 0 |
| `b3-20260815T000326Z` | B3 | FAIL | 20.879262 | 41.812694 | 81.65 | 10 | n=11 official command ended as REJECTED |
| `b3-20260815T000708Z` | B3 | PASS | 5169.192063 | 39158.022648 | 4154.25 | 10 | accepted or superseded PASS evidence |

The earlier B3 direct-import failure occurred before gate initialization and created no scored scientific process; it remains documented in `docs/b3-setup-audit.md` rather than being converted into evidence after the fact.

## B1 independent witness verification

`ARTIFACT_VERIFIED`: Python direct zero-one enumeration and an independently implemented Go bit-parallel checker both accepted the same 13-input, 45-comparator public artifact `35ddd10b0869a8d589559cdca71fc2d3bd619411988017167e4e40e71992bb83`. They agreed on all 267 cases.

| Check family | Count/result |
|---|---|
| `exhaustive-subset` | 40 |
| `malformed` | 9 |
| `mutation` | 3 |
| `negative` | 1 |
| `positive` | 6 |
| `random-differential` | 200 |
| `reflection` | 4 |
| `reflection-base` | 4 |
| Public witness | both `ACCEPT`; candidate checksum `9358d2c5e17720df3b5b4d2c2e209b973c8531aa3174eab140bca369a4212403` |
| Comparator-removal controls | indices 0, 22, 44 independently rejected |
| Case-result totals | accepted=72, rejected=186, malformed=9 |

The verifiers share only the candidate schema and fixtures. They do not share parsing, execution, sortedness, or counterexample logic.

## B2 constructive and transparent baselines

`LOCALLY_REPRODUCED`: every listed candidate was accepted by both B1 verifiers. `MEASURED`: sizes, evaluations, wall time, CPU, and memory are local observations. Seeds are frozen `ASSUMED` replacements because the historical seeds are `UNKNOWN`; the legacy variant-2 probability mapping is also `ASSUMED`.

| Baseline | Best | Size distribution | Evaluations | Wall s | CPU s | Peak MiB |
|---|---:|---|---:|---:|---:|---:|
| senso | 45 | 45:1, 46:16, 47:3 | 1004000 | 384.875065 | 380.140000 | 16.36 |
| greedy | 47 | 47:5, 48:15 | 400 | 5.305380 | 0.600000 | 4.91 |
| random | 148 | 148:1, 166:1, 167:1, 177:1, 182:1, 194:1, 195:1, 200:1, 202:3, 206:1, 208:1, 210:1, 213:1, 215:1, 216:1, 218:1, 222:1, 231:1 | 720163 | 5.308245 | 2.720000 | 19.69 |

### Frozen 20-seed SENSO-style batch

| Seed | Size | Evaluations | Wall s | CPU s | Peak MiB | A | B |
|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 46 | 50200 | 18.720924 | 18.560000 | 16.23 | ACCEPT | ACCEPT |
| 2 | 46 | 50200 | 18.998714 | 18.710000 | 16.17 | ACCEPT | ACCEPT |
| 3 | 46 | 50200 | 19.009466 | 18.700000 | 16.17 | ACCEPT | ACCEPT |
| 4 | 46 | 50200 | 19.005242 | 18.750000 | 16.27 | ACCEPT | ACCEPT |
| 5 | 46 | 50200 | 18.758770 | 18.680000 | 16.20 | ACCEPT | ACCEPT |
| 6 | 46 | 50200 | 18.757032 | 18.620000 | 16.34 | ACCEPT | ACCEPT |
| 7 | 46 | 50200 | 19.352359 | 19.070000 | 16.25 | ACCEPT | ACCEPT |
| 8 | 47 | 50200 | 20.451433 | 19.860000 | 16.33 | ACCEPT | ACCEPT |
| 9 | 46 | 50200 | 19.045908 | 18.970000 | 16.27 | ACCEPT | ACCEPT |
| 10 | 47 | 50200 | 19.336253 | 19.250000 | 16.25 | ACCEPT | ACCEPT |
| 11 | 46 | 50200 | 19.036907 | 18.760000 | 16.22 | ACCEPT | ACCEPT |
| 12 | 46 | 50200 | 19.020495 | 18.760000 | 16.25 | ACCEPT | ACCEPT |
| 13 | 46 | 50200 | 19.041999 | 18.800000 | 16.34 | ACCEPT | ACCEPT |
| 14 | 46 | 50200 | 19.047808 | 18.860000 | 16.31 | ACCEPT | ACCEPT |
| 15 | 46 | 50200 | 19.326363 | 18.970000 | 16.31 | ACCEPT | ACCEPT |
| 16 | 47 | 50200 | 20.285433 | 20.060000 | 16.17 | ACCEPT | ACCEPT |
| 17 | 46 | 50200 | 19.310065 | 19.060000 | 16.31 | ACCEPT | ACCEPT |
| 18 | 45 | 50200 | 19.289673 | 18.990000 | 16.23 | ACCEPT | ACCEPT |
| 19 | 46 | 50200 | 19.281340 | 19.190000 | 16.23 | ACCEPT | ACCEPT |
| 20 | 46 | 50200 | 19.798881 | 19.520000 | 16.36 | ACCEPT | ACCEPT |

### Transparent greedy initialization baseline

| Seed | Size | Evaluations | Wall s | CPU s | Peak MiB | A | B |
|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 47 | 20 | 0.264627 | 0.030000 | 4.88 | ACCEPT | ACCEPT |
| 2 | 48 | 20 | 0.262288 | 0.030000 | 4.88 | ACCEPT | ACCEPT |
| 3 | 48 | 20 | 0.266369 | 0.030000 | 4.89 | ACCEPT | ACCEPT |
| 4 | 48 | 20 | 0.266186 | 0.030000 | 4.84 | ACCEPT | ACCEPT |
| 5 | 48 | 20 | 0.266750 | 0.030000 | 4.80 | ACCEPT | ACCEPT |
| 6 | 48 | 20 | 0.264867 | 0.030000 | 4.83 | ACCEPT | ACCEPT |
| 7 | 47 | 20 | 0.264183 | 0.030000 | 4.83 | ACCEPT | ACCEPT |
| 8 | 48 | 20 | 0.266290 | 0.030000 | 4.88 | ACCEPT | ACCEPT |
| 9 | 48 | 20 | 0.266616 | 0.030000 | 4.81 | ACCEPT | ACCEPT |
| 10 | 48 | 20 | 0.266513 | 0.030000 | 4.84 | ACCEPT | ACCEPT |
| 11 | 47 | 20 | 0.264677 | 0.030000 | 4.91 | ACCEPT | ACCEPT |
| 12 | 48 | 20 | 0.266466 | 0.030000 | 4.83 | ACCEPT | ACCEPT |
| 13 | 48 | 20 | 0.264858 | 0.030000 | 4.89 | ACCEPT | ACCEPT |
| 14 | 48 | 20 | 0.266509 | 0.030000 | 4.83 | ACCEPT | ACCEPT |
| 15 | 48 | 20 | 0.264623 | 0.030000 | 4.86 | ACCEPT | ACCEPT |
| 16 | 47 | 20 | 0.265035 | 0.030000 | 4.83 | ACCEPT | ACCEPT |
| 17 | 48 | 20 | 0.264367 | 0.030000 | 4.86 | ACCEPT | ACCEPT |
| 18 | 48 | 20 | 0.266476 | 0.030000 | 4.88 | ACCEPT | ACCEPT |
| 19 | 48 | 20 | 0.264396 | 0.030000 | 4.86 | ACCEPT | ACCEPT |
| 20 | 47 | 20 | 0.263284 | 0.030000 | 4.89 | ACCEPT | ACCEPT |

### Transparent uniform-random baseline

| Seed | Size | Evaluations | Wall s | CPU s | Peak MiB | A | B |
|---:|---:|---:|---:|---:|---:|---|---|
| 1 | 210 | 37122 | 0.266553 | 0.140000 | 19.66 | ACCEPT | ACCEPT |
| 2 | 222 | 34692 | 0.266300 | 0.120000 | 19.55 | ACCEPT | ACCEPT |
| 3 | 166 | 34480 | 0.263554 | 0.140000 | 19.58 | ACCEPT | ACCEPT |
| 4 | 195 | 35892 | 0.264189 | 0.130000 | 19.69 | ACCEPT | ACCEPT |
| 5 | 202 | 35604 | 0.263794 | 0.140000 | 19.53 | ACCEPT | ACCEPT |
| 6 | 202 | 37113 | 0.266259 | 0.140000 | 19.52 | ACCEPT | ACCEPT |
| 7 | 215 | 35782 | 0.266124 | 0.140000 | 19.58 | ACCEPT | ACCEPT |
| 8 | 167 | 34944 | 0.266601 | 0.130000 | 19.52 | ACCEPT | ACCEPT |
| 9 | 148 | 35440 | 0.266616 | 0.140000 | 19.56 | ACCEPT | ACCEPT |
| 10 | 216 | 36222 | 0.264508 | 0.140000 | 19.50 | ACCEPT | ACCEPT |
| 11 | 231 | 35740 | 0.266364 | 0.130000 | 19.61 | ACCEPT | ACCEPT |
| 12 | 177 | 37110 | 0.262786 | 0.140000 | 19.50 | ACCEPT | ACCEPT |
| 13 | 208 | 36657 | 0.266189 | 0.140000 | 19.69 | ACCEPT | ACCEPT |
| 14 | 182 | 38088 | 0.266337 | 0.140000 | 19.58 | ACCEPT | ACCEPT |
| 15 | 202 | 36395 | 0.261717 | 0.140000 | 19.59 | ACCEPT | ACCEPT |
| 16 | 218 | 37399 | 0.266299 | 0.140000 | 19.62 | ACCEPT | ACCEPT |
| 17 | 213 | 35688 | 0.264938 | 0.140000 | 19.64 | ACCEPT | ACCEPT |
| 18 | 206 | 34745 | 0.266537 | 0.130000 | 19.69 | ACCEPT | ACCEPT |
| 19 | 194 | 34923 | 0.266336 | 0.120000 | 19.66 | ACCEPT | ACCEPT |
| 20 | 200 | 36127 | 0.266244 | 0.140000 | 19.56 | ACCEPT | ACCEPT |

Seed 18 is the sole SENSO-style size-45 result. The distribution is 45:1, 46:16, 47:3; no baseline returned a candidate below 45.

## B3 exact workflow and certificate replay

- `LOCALLY_REPRODUCED`: the official n=9 search-and-verify workflow returned `Just (9,25)` and generated proof SHA-256 `26eb7b47e6b7902e17357e861a8166ceeb056de5b2cdf35401c4f3446916da9b` (1559129 bytes; 150 generated artifacts). This establishes only `S(9) >= 25` locally.
- `LOCALLY_REPRODUCED`: changing the parseable n=9 proof's root-bound byte returned `Nothing`, providing the required negative control.
- `ARTIFACT_VERIFIED`: the published n=11 certificate is 3068651498 bytes and retained SHA-256 `7fe9f5cd694714bf83da0bcab162a290eb076ad4257265507a74cea8fab85b7e` before and after replay.
- `LOCALLY_REPRODUCED`: the exact certificate returned `Just (11,35)`. This establishes only `S(11) >= 35` locally; the equality and n=12 consequence remain separately labeled below.

| B3 phase | Result | Wall s | CPU s | Peak MiB | Limit |
|---|---|---:|---:|---:|---|
| n=9 official workflow | `Just (9,25)` | 15.392936 | 27.890000 | 95.38 | 600 s / 1 GiB |
| corrupted-proof control | `Nothing` | 2.391103 | 12.370000 | 24.89 | 120 s / 1 GiB |
| n=11 certificate replay | `Just (11,35)` | 5148.689796 | 39106.380000 | 4154.25 | 14,400 s / 12 GiB |

The pinned upstream is `jix/sortnetopt` commit `0b5d09c47446096f9e3a0812b35afc72b7f2a718`. Two hashed macOS portability patches affect diagnostic `/proc` logging and unverified large-file I/O only; the parser and formally checked core remain unchanged.

## Hardware and resource accounting

`MEASURED`: Apple model `Mac16,10`, CPU `Apple M4`, 10 logical/10 physical cores, 16.00 GiB RAM, `arm64`, `macOS-26.5.2-arm64-arm-64bit-Mach-O`. Constructive runs used one thread per seed; the official exact pipeline used the host's ten cores. GPU and remote compute were prohibited and unused.

All ten B0--B3 scored manifests total 5620.052041 wall seconds (93.67 minutes), below the 43200 second post-setup limit. The largest measured process tree was 4154.25 MiB. B4 itself is report-only; its exact small resource record is in its manifest.

| Setup item (excluded from post-setup scored total) | Status | Wall s | Identity |
|---|---|---:|---|
| SENSO build/smoke | PASS | 66.865515 | binary `1d6fe20b547fa0e9dd9c899e34b608ac157104f63fd845d858e6e4ae9c0e6cc6` |
| active Harder toolchain build | PASS | 34.862314 | checker `4cd30511f73e7d7f6f3f7bc4083d84b37c0678f2156f85fcbfa186546218a84c` |
| certificate fetch/decompression | PASS | 282.576548 | uncompressed `7fe9f5cd694714bf83da0bcab162a290eb076ad4257265507a74cea8fab85b7e` |

## Unreproduced claims and limits

| Statement or artifact | Label | Why it is not locally established here |
|---|---|---|
| Exact minimum size of S(13) | `UNKNOWN` | The audited interval remains 44--45; both a size-44 search and a nonexistence attempt were prohibited. |
| Historical SENSO run identity | `UNKNOWN` | Historical seeds were not published; this laboratory used explicit `ASSUMED` seeds and an audited mapping. |
| `S(11)=35` equality | `PUBLISHED` | B3 replayed the lower-bound certificate but did not separately replay a matching construction. |
| `S(12)=39` | `PUBLISHED` | This paper-derived consequence was not separately replayed with an n=12 certificate. |
| Full n=11 certificate generation | `PUBLISHED` resource account | Explicitly prohibited; the reference required roughly 200 GiB RAM and 80 hours on a 48-thread EPYC host. |
| Minimum depth 9 for 13 inputs | `PUBLISHED` context | Depth is not comparator count and is not this laboratory's optimization target. |
| Optional modern n=28 construction context | `PUBLISHED` | Not a B0--B4 dependency and not executed. |

An unsuccessful or timed-out run is nowhere used as a proof. The live-status audit is a dated snapshot and must be repeated before later work.

## Strongest baseline to beat later

The later comparator-count experiment, if separately authorized, must beat 45 comparators. That size is supported two ways: B1 independently verifies the public 45-comparator artifact, and B2 seed 18 locally regenerates a different dual-verified size-45 result. Improvement therefore means a valid 44-comparator witness accepted by both B1 verifiers. This report neither searches for nor claims one.

## Exact next prerequisite

Obtain user approval for and freeze a new versioned experimental contract that re-audits S(13), specifies the later method and budgets, preserves both B1 verifiers, and defines candidate and stop handling before any novel run.

No later experimental contract was drafted or executed as part of B4.

## Terminal verdict

`BASELINE_READY`
