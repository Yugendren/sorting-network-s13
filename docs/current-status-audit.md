# B0 current-status audit

Audit date: 2026-08-15 (Asia/Singapore).

Falsifiable outcome: the maintained current catalog must still state an open
minimum-size interval `44 <= S(13) <= 45` and expose an explicit 45-comparator
witness. Otherwise the only permitted verdict is `STALE_TARGET`.

## Result

- `ARTIFACT_VERIFIED`: commit
  `49b355d484aa92c2a661b6ab1a2f981a60b7c0c6` of the maintained catalog
  repository byte-matches the retrieved HTML snapshot with SHA-256
  `8a2d11c9f2ac66e16ea93a9c4301971b47d3115eaf28d4e12b50079c8238d116`.
- `PUBLISHED`: its summary row for 13 inputs states size bounds `44...45` and
  depth bound `9`.
- `ARTIFACT_VERIFIED`: the same snapshot contains a 13-input, 45-comparator,
  10-layer network. B1 will establish its construction truth locally.
- `PUBLISHED`: Harder's paper and official repository establish exact sizes at
  11 and 12 channels; neither claims to settle 13 channels.
- `MEASURED`: targeted current web and repository searches found no primary or
  maintained artifact superseding the catalog row. This absence is supporting
  audit evidence, not a proof of openness by itself.

The target is not stale at B0. Minimum size remains the active metric;
minimum depth 9 is context only.

Primary URLs and exact hashes are frozen in `config/frozen/sources.json`.
