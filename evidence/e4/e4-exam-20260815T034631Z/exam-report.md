# Mericanii method V2 frozen E4 exam report

Run: `e4-exam-20260815T034631Z`  
Tested commit: `4881f9a135b61a70ee145f021889255c5a0c12ad`  
Gate decision: `E4_FAIL`

This is the final method exam, not the canonical terminal goal report.

## Frozen identities

- ARTIFACT_VERIFIED contract SHA-256: `6d8e9c3d0c4719bbd4c28bf55bc068ead10407e4a5928978afc55be338e503e6`.
- ARTIFACT_VERIFIED E4 seed manifest SHA-256: `b408752e404b3cfa2fb55b3fbaac5377e098128ddf3f04bbe43d6821d5a77b82`.
- ARTIFACT_VERIFIED SENSO binary SHA-256: `1d6fe20b547fa0e9dd9c899e34b608ac157104f63fd845d858e6e4ae9c0e6cc6`.
- ARTIFACT_VERIFIED Mericanii V2 binary SHA-256: `382e4a298f56bacf52d633ae80d08d3ede8590f5083e7726cf0a61d54d337fdf`.
- ARTIFACT_VERIFIED model checkpoint SHA-256: `60af80b18701f0c93276134b95e8f7ce554c20163020b03ec2d32d8ffe53383f`.
- ARTIFACT_VERIFIED unchanged integration patch SHA-256: `f2d8fd259f1ceab62e2e41f826f0573feb1d05cdbd4e17f5cf82df9960f1a132`.

## Result

- LOCALLY_REPRODUCED SENSO successes: 2/60; Wilson 95% interval 0.0092--0.1136.
- LOCALLY_REPRODUCED Mericanii successes: 0/60; Wilson 95% interval 0.0000--0.0602.
- MEASURED paired success-rate effect: -0.0333; paired-bootstrap 95% interval -0.0833--+0.0000.
- MEASURED final-size distributions: SENSO `{"45": 2, "46": 56, "47": 2}`; Mericanii `{"46": 27, "47": 33}`.
- MEASURED wall seconds/evaluation: SENSO 0.000382424; Mericanii 0.000662451.
- MEASURED model ranking time: 872.931173s total (43.7493% of method wall time); model-only score time 41.261445s.

## Six frozen criteria

- PASS: `every_claimed_candidate_dual_verified`.
- FAIL: `mericanii_at_least_12_of_60`.
- FAIL: `mericanii_at_least_twice_senso`.
- PASS: `mericanii_no_more_evaluations_per_seed`.
- PASS: `integrity_replay`.
- PASS: `no_holdout_data_used_for_tuning`.

## Complete paired outcomes

| # | seed | order | SENSO size | SENSO success | V2 size | V2 success | effect | SENSO s | V2 s |
|---:|---:|---|---:|:---:|---:|:---:|---:|---:|---:|
| 1 | 130188847 | frozen_mericanii_v2 → frozen_senso | 46 | no | 46 | no | +0 | 18.829 | 33.161 |
| 2 | 537458764 | frozen_senso → frozen_mericanii_v2 | 46 | no | 46 | no | +0 | 19.395 | 32.934 |
| 3 | 874859405 | frozen_mericanii_v2 → frozen_senso | 46 | no | 47 | no | +0 | 18.879 | 33.195 |
| 4 | 1154909215 | frozen_senso → frozen_mericanii_v2 | 46 | no | 47 | no | +0 | 19.124 | 33.493 |
| 5 | 104651114 | frozen_mericanii_v2 → frozen_senso | 46 | no | 47 | no | +0 | 19.370 | 33.222 |
| 6 | 252103815 | frozen_senso → frozen_mericanii_v2 | 46 | no | 47 | no | +0 | 18.851 | 33.504 |
| 7 | 1753459311 | frozen_mericanii_v2 → frozen_senso | 46 | no | 47 | no | +0 | 19.466 | 33.208 |
| 8 | 1985200550 | frozen_senso → frozen_mericanii_v2 | 46 | no | 47 | no | +0 | 19.083 | 33.392 |
| 9 | 1337844944 | frozen_mericanii_v2 → frozen_senso | 46 | no | 47 | no | +0 | 19.359 | 33.345 |
| 10 | 1127971196 | frozen_senso → frozen_mericanii_v2 | 47 | no | 47 | no | +0 | 19.382 | 33.995 |
| 11 | 309190520 | frozen_mericanii_v2 → frozen_senso | 46 | no | 47 | no | +0 | 19.115 | 33.304 |
| 12 | 742384021 | frozen_senso → frozen_mericanii_v2 | 46 | no | 46 | no | +0 | 18.869 | 32.776 |
| 13 | 1345529701 | frozen_mericanii_v2 → frozen_senso | 46 | no | 47 | no | +0 | 19.121 | 33.568 |
| 14 | 649008375 | frozen_senso → frozen_mericanii_v2 | 46 | no | 46 | no | +0 | 19.097 | 32.851 |
| 15 | 1708309951 | frozen_mericanii_v2 → frozen_senso | 45 | yes | 46 | no | -1 | 19.063 | 32.848 |
| 16 | 1299380017 | frozen_senso → frozen_mericanii_v2 | 46 | no | 46 | no | +0 | 19.130 | 33.226 |
| 17 | 1724641247 | frozen_mericanii_v2 → frozen_senso | 46 | no | 46 | no | +0 | 19.126 | 33.384 |
| 18 | 837946137 | frozen_senso → frozen_mericanii_v2 | 46 | no | 46 | no | +0 | 18.827 | 33.091 |
| 19 | 1599563688 | frozen_mericanii_v2 → frozen_senso | 46 | no | 47 | no | +0 | 19.369 | 33.359 |
| 20 | 425695314 | frozen_senso → frozen_mericanii_v2 | 46 | no | 47 | no | +0 | 18.876 | 33.172 |
| 21 | 1571111281 | frozen_mericanii_v2 → frozen_senso | 46 | no | 47 | no | +0 | 18.879 | 33.194 |
| 22 | 754396234 | frozen_senso → frozen_mericanii_v2 | 46 | no | 47 | no | +0 | 18.838 | 33.197 |
| 23 | 648149119 | frozen_mericanii_v2 → frozen_senso | 46 | no | 47 | no | +0 | 19.100 | 33.167 |
| 24 | 1073359152 | frozen_senso → frozen_mericanii_v2 | 46 | no | 46 | no | +0 | 19.069 | 32.843 |
| 25 | 929647190 | frozen_mericanii_v2 → frozen_senso | 46 | no | 46 | no | +0 | 18.765 | 33.026 |
| 26 | 606492659 | frozen_senso → frozen_mericanii_v2 | 46 | no | 47 | no | +0 | 19.659 | 33.292 |
| 27 | 1796157188 | frozen_mericanii_v2 → frozen_senso | 46 | no | 47 | no | +0 | 20.923 | 33.379 |
| 28 | 1393557639 | frozen_senso → frozen_mericanii_v2 | 46 | no | 46 | no | +0 | 19.710 | 32.909 |
| 29 | 1470478131 | frozen_mericanii_v2 → frozen_senso | 46 | no | 46 | no | +0 | 19.651 | 33.044 |
| 30 | 2026112155 | frozen_senso → frozen_mericanii_v2 | 45 | yes | 46 | no | -1 | 18.846 | 32.609 |
| 31 | 1493004438 | frozen_mericanii_v2 → frozen_senso | 46 | no | 47 | no | +0 | 18.819 | 33.117 |
| 32 | 54848151 | frozen_senso → frozen_mericanii_v2 | 46 | no | 46 | no | +0 | 18.838 | 32.851 |
| 33 | 56444445 | frozen_mericanii_v2 → frozen_senso | 46 | no | 46 | no | +0 | 19.090 | 32.891 |
| 34 | 1241096891 | frozen_senso → frozen_mericanii_v2 | 47 | no | 46 | no | +0 | 20.015 | 32.933 |
| 35 | 710548898 | frozen_mericanii_v2 → frozen_senso | 46 | no | 47 | no | +0 | 19.068 | 33.416 |
| 36 | 1371411087 | frozen_senso → frozen_mericanii_v2 | 46 | no | 47 | no | +0 | 18.835 | 33.155 |
| 37 | 2088332683 | frozen_mericanii_v2 → frozen_senso | 46 | no | 46 | no | +0 | 19.087 | 33.155 |
| 38 | 852008742 | frozen_senso → frozen_mericanii_v2 | 46 | no | 47 | no | +0 | 19.407 | 33.188 |
| 39 | 2028087844 | frozen_mericanii_v2 → frozen_senso | 46 | no | 47 | no | +0 | 20.203 | 35.586 |
| 40 | 1096207646 | frozen_senso → frozen_mericanii_v2 | 46 | no | 47 | no | +0 | 19.420 | 33.133 |
| 41 | 665692908 | frozen_mericanii_v2 → frozen_senso | 46 | no | 46 | no | +0 | 19.095 | 33.169 |
| 42 | 999353783 | frozen_senso → frozen_mericanii_v2 | 46 | no | 46 | no | +0 | 19.103 | 33.464 |
| 43 | 1756887738 | frozen_mericanii_v2 → frozen_senso | 46 | no | 47 | no | +0 | 19.931 | 34.557 |
| 44 | 212315403 | frozen_senso → frozen_mericanii_v2 | 46 | no | 47 | no | +0 | 19.624 | 34.472 |
| 45 | 1494266182 | frozen_mericanii_v2 → frozen_senso | 46 | no | 46 | no | +0 | 19.711 | 34.280 |
| 46 | 1098831218 | frozen_senso → frozen_mericanii_v2 | 46 | no | 47 | no | +0 | 19.371 | 33.398 |
| 47 | 662955960 | frozen_mericanii_v2 → frozen_senso | 46 | no | 46 | no | +0 | 19.111 | 33.518 |
| 48 | 64634128 | frozen_senso → frozen_mericanii_v2 | 46 | no | 47 | no | +0 | 18.845 | 33.441 |
| 49 | 2021753797 | frozen_mericanii_v2 → frozen_senso | 46 | no | 47 | no | +0 | 18.811 | 33.184 |
| 50 | 1587390717 | frozen_senso → frozen_mericanii_v2 | 46 | no | 47 | no | +0 | 19.354 | 32.864 |
| 51 | 66627002 | frozen_mericanii_v2 → frozen_senso | 46 | no | 46 | no | +0 | 18.805 | 32.603 |
| 52 | 1083539942 | frozen_senso → frozen_mericanii_v2 | 46 | no | 47 | no | +0 | 19.125 | 33.407 |
| 53 | 709187043 | frozen_mericanii_v2 → frozen_senso | 46 | no | 46 | no | +0 | 18.819 | 33.142 |
| 54 | 1562522203 | frozen_senso → frozen_mericanii_v2 | 46 | no | 47 | no | +0 | 19.094 | 33.125 |
| 55 | 1411665102 | frozen_mericanii_v2 → frozen_senso | 46 | no | 46 | no | +0 | 19.085 | 32.859 |
| 56 | 62978616 | frozen_senso → frozen_mericanii_v2 | 46 | no | 46 | no | +0 | 19.125 | 32.913 |
| 57 | 1793816582 | frozen_mericanii_v2 → frozen_senso | 46 | no | 46 | no | +0 | 18.835 | 32.901 |
| 58 | 1933742509 | frozen_senso → frozen_mericanii_v2 | 46 | no | 46 | no | +0 | 19.266 | 32.815 |
| 59 | 340256295 | frozen_mericanii_v2 → frozen_senso | 46 | no | 47 | no | +0 | 19.117 | 33.001 |
| 60 | 578296042 | frozen_senso → frozen_mericanii_v2 | 46 | no | 47 | no | +0 | 19.082 | 33.076 |

## Integrity replay

- LOCALLY_REPRODUCED clean-input rebuild: `PASS`.
- LOCALLY_REPRODUCED successful candidates reverified: 2.
- LOCALLY_REPRODUCED exact sentinel comparisons: 4/4.
- LOCALLY_REPRODUCED raw results were reaggregated from disk; final recursive checksums were independently replayed.

## Boundary

- Target size 44 was not used for training, selection, scoring, or routine exam acceptance.
- Failure here is a measured method result, not evidence that a 44-comparator network is impossible.
- E5 remains forbidden unless this report says `E4_PASS`.
