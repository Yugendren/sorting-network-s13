# Source and artifact ledger

All retrievals were performed on 2026-08-15. Exact machine-readable pins,
sizes, and hashes are in `config/frozen/sources.json`.

| ID | Role | Pin | Truth at B0 |
|---|---|---|---|
| dobbelaere-catalog | maintained size bounds and public witness | Git commit `49b355d...`; HTML SHA-256 `8a2d11c...` | `ARTIFACT_VERIFIED` snapshot; network correctness deferred to B1 |
| harder-paper-v3 | lower-bound method and exact n=11/n=12 statements | arXiv v3 PDF SHA-256 `48a54dee...` | `PUBLISHED` |
| sortnetopt | official search and checked certificate pipeline | commit `0b5d09c...` | source pin `ARTIFACT_VERIFIED`; execution deferred to B3 |
| harder-n11-certificate | n=11 proof certificate | Zenodo DOI; uncompressed SHA-256 `7fe9f5cd...` | metadata `ARTIFACT_VERIFIED`; bytes/replay deferred to B3 |
| valsalam-miikkulainen-paper | SENSO algorithm and parameters | JMLR PDF SHA-256 `59522734...` | `PUBLISHED` |
| symmetry-1.1 | author implementation | archive SHA-256 `d3e960fa...` | archive/license/build probe `ARTIFACT_VERIFIED`; scored runs deferred to B2 |
| wang-n28d13-context | optional modern context | commit `41950ab...` | `PUBLISHED`; no B0-B4 pass dependency |

The SENSO paper specifies population 200, 500 generations, top-half model
estimation and elitism, Gaussian truncation centered at half the comparator
sequence with one-quarter standard deviation, a 0.5 model/random split, and
20 runs per variant/input size. It reports 45 comparators for 13 inputs. Its
historical seeds are not published and remain `UNKNOWN`; this laboratory uses
new explicit `ASSUMED` seeds.

The build feasibility probe and the exact portability delta are recorded in
`docs/senso-portability.md`; they are setup evidence only, not a scored B2 run.
