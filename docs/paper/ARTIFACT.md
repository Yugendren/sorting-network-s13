# Artifact repository layout for `audit-paper-v2`

**Status: design document.** This specifies the public repository and data
deposit that `docs/paper/audit-paper-v2.md` will cite. **Nothing here has been
published.** Creating the public repo, minting the DOI and uploading the
certificate are the user's decisions and are deliberately not automated.

Date: 2026-08-22. Owner: paper-revision campaign.

---

## 0. The model, and why

Harder's *An Answer to the Bose–Nelson Sorting Problem for 11 and 12 Channels*
(arXiv:2012.04400) is the direct precedent and the pattern we copy:

| layer | Harder | us |
|---|---|---|
| the argument | arXiv preprint | arXiv preprint (`audit-paper-v2`) |
| the machinery | `github.com/jix/sortnetopt` (search engine + Isabelle checker) | `sortnet-audit` GitHub repo (this layout) |
| the data | 2.9 GB certificate, regenerable, not archived with the paper | 2.44 GB certificate, archived under DOI |

Two deliberate departures from Harder.

1. **We archive the certificate under a DOI.** Harder's is regenerable from his
   code and was never deposited. Ours is the *credential* for a claim the paper
   makes about its own engine, so it must be fetchable without a four-day
   recomputation. 2.44 GB is inside Zenodo's 50 GB per-record limit.
2. **We ship the verifiers as the primary artifact, not the search engine.** The
   paper's core claims are mathematics checked by short stdlib-only Python. That
   code is the thing a referee will actually run, so it is at the top of the
   tree, runs with no arguments, and needs no build.

**Governing principle.** *If a number appears in the paper, some file in this
repository recomputes it, and the quickstart says how long that takes.* Where
that is not currently true, §7 says so explicitly rather than quietly.

---

## 1. Repository tree

```
sortnet-audit/
├── README.md                     # 1 page: what this is, the claim ladder, the quickstart
├── LICENSE                       # code: MIT.  docs/data: CC-BY-4.0.  See NOTICE.
├── NOTICE                        # third-party provenance: sortnetopt (Apache-2.0/MIT),
│                                 #   the pinned upstream commit, and what we changed
├── CITATION.cff
├── Makefile                      # `make tier1`, `make tier2`, `make verify-cert`, `make all`
│
├── verifiers/                    # ── TIER 1: the paper's mathematics, stdlib only ──
│   ├── verify_huffman2.py        #   48 checks  A1..H3     ~105 s
│   ├── verify_kraft_dispute.py   #   36 checks  A1..D'5    ~2 s   (independent re-derivation)
│   ├── verify_kraft_wave1.py     #   26 checks  W1a..W5d   ~206 s
│   ├── verify_kraft_wave2.py     #   27 checks  X1a..X6e   ~153 s
│   ├── verify_shape_case_split.py#   33 checks (--corrected) ~21 s
│   ├── verify_endgame.py         #   0 failures            ~4 s
│   ├── run_all.sh                #   runs the six above, prints one summary, exits non-zero on any failure
│   └── CHECKS.md                 #   ★ the full check-ID → claim table (moved out of the paper)
│                                 #   NB the counts above are the runtime totals reported by each
│                                 #   script; a static count of `check(` call sites differs (one ID
│                                 #   has two call sites on success/abort paths). CHECKS.md must
│                                 #   state the runtime count and the convention, once.
│
├── engine/                       # ── TIER 3/4: the lower-bound computation ──
│   ├── PINNED                    #   jix/sortnetopt @ 0b5d09c47446096f9e3a0812b35afc72b7f2a718
│   ├── patches/                  #   13 patches, each with its sha256 in MANIFEST.sha256
│   │   ├── sortnetopt-tier1-v3.patch          … SIMD kernel + exact prefilters
│   │   ├── sortnetopt-online-subsumption-v3.patch
│   │   ├── sortnetopt-perf-v3.patch
│   │   ├── sortnetopt-limits-v3.patch         … n=12/13 unlock, upper-bound seeds ONLY
│   │   ├── sortnetopt-prefixcert-v3.patch
│   │   ├── sortnetopt-decomp-v3.patch
│   │   ├── sortnetopt-zm-v3.patch
│   │   ├── sortnetopt-endgame-v3.patch
│   │   ├── sortnetopt-instrumentation-v3.patch
│   │   ├── sortnetopt-tier2a-v3.patch  · -tier2b-v3.patch
│   │   └── sortnetopt-macos-large-read.patch · -macos-proc.patch
│   ├── MANIFEST.sha256
│   ├── build.md                  #   exact toolchain versions; what "unchanged checker" means
│   └── configs/n11-lowmem.env    #   SUBSUME=evict DIMS=96 W=8,9 — the config the run used
│
├── checker/                      # ── the trust boundary ──
│   ├── Prefix_Checker.thy        #   241 lines, no `sorry`
│   ├── Prefix_Checker_Codegen.thy
│   ├── snocheck2/{Main,Decode2,Translate2}.hs
│   ├── crosscheck.py
│   ├── ROOT · build.sh
│   └── TRUST.md                  #   ★ "a verified prefix checker with an unverified decoder" —
│                                 #     verbatim, plus the frozen-snocheck digest and the
│                                 #     two-checker protocol
│
├── theory/                       # ── the long-form mathematics the paper compresses ──
│   ├── audit.md                  #   = van-voorhis-theory-report.md  (the 1972 read)
│   ├── dispute.md                #   = kraft-dispute-verdict.md      (ten steelmen, adversarial)
│   ├── repair-wave1.md · repair-wave2.md
│   ├── shape-case-split.md       #   incl. the S1=6|7=C2 / S2=5|8=C1 adjudication
│   ├── level-law.md              #   = ambient-reduction.md, with Theorem A reframed
│   ├── endgame.md
│   └── DEADENDS.md               #   ★ every refuted repair family, one page, with counterexamples
│
├── evidence/                     # ── measurement records, append-only ──
│   ├── MANIFEST.json             #   per-run: source commit, command, host, checksums
│   ├── n11-certified/            #   report.md + search.log + prune.log + genproof.log + verify.log
│   ├── limits/ · tier1/ · tier2a/ · tier2b/ · m0/ · m2a/ · m2b/
│   ├── satspike/ · zm/ · decomp/ · prefixcert/ · vcheck/
│   └── census/                   #   ★ NEW — regenerates the §5.5 coverage table (see §7, gap G6)
│       ├── coverage_census.py
│       └── expected.json         #   153,011 networks; 0.183 / 0.223 / 0.224 / 0.496
│
├── fixtures/                     # ── kilobyte inputs that make the selftests argument-free ──
│   ├── n9-cert-v1.bin            #   for cert_v2.py selftest
│   ├── ambient-dump-n9-L25/      #   for verify_ambient.py selfcheck
│   └── README.md
│
├── papers/                       # ── primary sources, where redistribution is permitted ──
│   ├── SOURCES.md                #   ★ what we read, what we could NOT obtain, and why
│   └── (no redistributable copy of the 1972 chapter — see SOURCES.md)
│
└── paper/
    ├── audit-paper-v2.md · .tex · .pdf
    └── CLAIMS.md                 #   ★ the claim → artifact map of §3 below
```

★ = file that exists **only** because material was moved out of the paper.

---

## 2. The data deposit (Zenodo-style)

One record, one DOI, cited in the paper's Data Availability statement.

| item | size | sha256 | why deposited |
|---|---|---|---|
| `proof_n11_ours.bin` | 2,442,317,348 B | `672c433fb5f7a85602c937acfcd2135fd8a9f64d63c7ea3075706156d2c08e38` | the credential; 4 days to regenerate, 90 min to check |
| `verify.log` | KB | — | the checker's own transcript, `Just (11,35)`, exit 0 |
| `snocheck` (frozen binary) + `snocheck.sha256` | MB | `4cd30511…` (matches the committed B3 toolchain manifest) | the exact checker that accepted the certificate |
| `prefixcert-certs.tar` | MB | per-file digests in `evidence/prefixcert/` | 8 per-job certificates, composing to 25/25/29/29 |
| `census-corpus.tar.zst` | ~GB | — | the 153,011-network coverage corpus (§7, gap G6) |

Deposit README states the one sentence that matters: **the certificate is
checked by an unmodified extraction of a formally verified prefix checker, with
an unverified decoder around it.** Nothing in the deposit is required to check
the paper's *mathematics* — only its *computation*.

---

## 3. Claim → artifact map

Paper sections are those of `audit-paper-v2.md`. Tier = the claim ladder in §1.2
of the paper.

| tier | paper § | claim | artifact | cost |
|---|---|---|---|---|
| 1 | §3.2 | `T1 = [(0,1),(0,2),(1,2)]` has 3 comparators in `MAX(T)` where the chapter asserts 2 | `verify_huffman2.py` `E1`; `verify_kraft_dispute.py` `C1`,`C2` | 2 s, or by hand |
| 1 | §3.2 | eq (5) returns 4 for a quantity whose value is 3 | `V1:E2,E3`; `V2:C3,C4` | 2 s |
| 1 | §3.2 | eq (6)'s Kraft sum is 5/4 > 1 | `V1:E4`; `V2:C5` | 2 s |
| 1 | §3.2 | under the literal reading of (9), eq (8) itself fails on `T1` | `V1:E5,E6`; `V2:C6,C7,C8` | 2 s |
| 1 | §3.3 | prevalence over 387 constructed sorters (61.0 / 44.4 / 42.4 / 27.1 %) | `V2` Part D, seed `20260818`; existence/universality asserted by `D0`,`D1`,`D2`,`D3`,`D-1`,`D-2`, counts printed | 2 s |
| 1 | §3.3 | the pooled tight-and-broken figure 37.1 % over 149,040 optimal 5-sorters | `verify_kraft_wave1.py` §3 | 206 s |
| 1 | §3.3 | the broken Kraft sum reaches 1.6875 at n=6 and 1.8125 at n=7 | `W4c`; wave-1 §5 | 206 s |
| 1 | §3.4 | S10 (MAX/MAX2 disjointness) refuted; holds on Batcher-8 | `V2:C10`,`C11`,`D-1` | 2 s |
| 1 | §3.4 | exhaustive: 42 sequences at n=3 (len ≤ 4), 912 at n=4 (len ≤ 6), 0 violations | `V2:E3`,`E4`; `_all_sorters` prunes nothing | 2 s |
| 1 | §3.5 | Fig. 4's own Kraft sum is 0.75 — a misstatement, not the gap | `V1:E7,E8`; `V2:B1`–`B6` | 2 s |
| 1 | §4 | no erratum, no reproof, 18 citing works, none engages | `theory/SOURCES.md`; OpenAlex query recorded, dated | manual |
| 2 | §5.1 | Lemma W1: `W*(c) = a(c) + eps(c) + gamma(c) + r(c)` | `X1a`–`X1e`; 152,003 + 32,043 sorters, 0 violations | 153 s |
| 2 | §5.2 | Theorem 6′ (escape-free) | `W2a`–`W2j`; `X2a`–`X2f` | 206 + 153 s |
| 2 | §5.3 | Theorem 6″ ((C)∧(D)) | `X3a`,`X3b`; `X4a`–`X4f` | 153 s |
| 2 | §5.4 | Theorem 8 and Corollaries 8a–8c (pass-through-rich end) | `X6a`–`X6e` | 153 s |
| 2 | §5.5 | coverage: clean 18.3 %, escape-free 22.3 %, structural union **22.4 %**, no route **49.6 %** | `evidence/census/coverage_census.py` — **does not exist yet**, see §7 G6 | ~1 h |
| 2 | §5.6 | per-node charging closed structurally (`sum_c 2^{a(c)-p(2,T)} = 1` on tight networks) | `W5a`,`W5b` | 206 s |
| 2 | §5.6 | LEMMA★ refuted by the 15-comparator 6-sorter `T3` | `V1:G5`; `V2:D'3`; `W4a` | 105 s |
| 3 | §6 | Lemmas 10 and 11 (cube chain; unique cube successor) | `verify_ambient.py chain`, `census` + `fixtures/ambient-dump-n9-L25/` | ~1 min |
| 3 | §6 | Theorem 12 (Chain Collapse), empirical exactness across 21 ambient pairs | `verify_ambient.py lemma-l`, `compare`, `compare-big` | ~1 min |
| 3 | §6 | ambient-freedom, and the sole leak (`SUBSUME_WIDTHS` defaulting to `{n−3,n−2}`) | `theory/level-law.md` §5.3 — **code-reading audit plus a second reader, not machine-checked**; the paper states it that way | manual |
| 4 | §7 | independently certified `S(11) = 35` | deposit: `proof_n11_ours.bin` + frozen `snocheck` | 90 min |
| 4 | §7.1 | the memory/time trade (14.6× search memory; ~1.5× at the binding stage; 14.7× search wall) | `evidence/n11-certified/` four stage logs | read-only |
| 5 | §8 | the measured wall for n = 13 | `evidence/limits/`, `evidence/m2a/`, `evidence/m2b/`, `evidence/zm/`, `evidence/satspike/`, `evidence/tier2a/` | read-only |
| 5 | §8 | the negative results (ambient 1.00×, suffix 1.000×, SAT 3–4 orders short, matcher 1.13×) | same | read-only |

---

## 4. Reproduce-everything quickstart

Hardware baseline for all times below: **Apple M4, 16 GB, macOS 15 (Darwin
25.5.0), Python 3.14.4**, unless a row says otherwise. Times were taken with
other processes active and are upper bounds.

### Tier 0 — by hand, 5 minutes, no computer

Draw `T1 = [(0,1),(0,2),(1,2)]`. Trace the three max-paths. Count the
comparators in `MAX(T1)`: three, where the chapter asserts two. Put the maximum
on channel 0 and the second maximum on channel 1; they separate at `(0,1)` and
**meet again** at `(1,2)`. That is the whole finding.

### Tier 1 — the paper's mathematics, ~9 minutes, no dependencies

```
git clone https://github.com/<org>/sortnet-audit && cd sortnet-audit
make tier1          # or: verifiers/run_all.sh
```

| tool | mode | wall | expected |
|---|---|---|---|
| `verify_huffman2.py` | full | 105 s | `all 48 checks PASSED`, exit 0 |
| `verify_kraft_dispute.py` | full | 2 s | 36 checks; `VERDICT: (A) HOLE CONFIRMED`, exit 0 |
| `verify_kraft_wave1.py` | full | 206 s | 26 checks, 0 failures, exit 0 |
| `verify_kraft_wave2.py` | full | 153 s | 27 checks, 0 failures, exit 0 |
| `verify_shape_case_split.py` | `--corrected` | 21 s | 33/33, exit 0 |
| `verify_endgame.py` | default | 4 s | `TOTAL FAILURES: 0`, exit 0 |

Total ≈ 550 s. Requires Python ≥ 3.11 and nothing else: no pip, no network, no
data files.

**Two contracts a reviewer must be told about, in the README, not in a footnote:**

- `verify_shape_case_split.py` **without** `--corrected` exits **1 by design** —
  it fails the single historical check "exactly 5 root shape classes survive",
  which this project's machine-verified 5→3 correction refutes. `--corrected`
  is the release default; `--as-documented` reproduces the historical failure.
- `--fast` **does not reproduce the paper.** It keeps the check counts and
  shrinks the populations (387→93, 900→320, 912→12). Every percentage in the
  paper needs the full runs.

### Tier 2 — the selftests that need fixtures, ~1 minute

```
make tier2
```

| tool | fixture | wall | expected |
|---|---|---|---|
| `cert_v2.py selftest fixtures/n9-cert-v1.bin` | 9-channel v1 certificate | 4 s | 21 PASS, 0 FAIL |
| `verify_ambient.py selfcheck fixtures/ambient-dump-n9-L25/` | state dump | < 1 s | widths [3..9], 207,995 states |
| `class_campaign.py --selftest --no-engine` | none | 5 s | 19 checks (engine-free subset) |

All three currently require artifacts that live outside the repository; making
them argument-free is gap **G4** below and is a precondition for release.

### Tier 3 — check the n = 11 certificate, ~95 minutes, 8 GB RAM

```
make fetch-cert          # ~2.44 GB from the DOI; verifies sha256 672c433f…
make verify-cert         # frozen snocheck -v
```

Expected: `Just (11,35)`, exit 0, 89 m 24 s wall, 4.35 GB max RSS on the M4.
This is the only step that establishes `S(11) = 35` from *our* certificate
rather than from Harder's; it does not depend on any patch in `engine/`.

### Tier 4 — regenerate the certificate, ~4 days, 48 GB RAM + 96 GB swap

Do not attempt on a laptop. The pipeline that produced the deposited
certificate, on an AMD Ryzen 3600 with 47 GB RAM:

| stage | wall | peak memory |
|---|---|---|
| search (`SUBSUME=evict DIMS=96 W=8,9`) | 71 h 06 m | 13.08 GB |
| prune-all (`CROSS_BOUND_PRUNE=1`) | 9 h 45 m | ~8.4 GB |
| gen-proof | ~9 h | **> 37.9 GB** — OOM-killed twice at 37.9 GB before swap was armed |
| verify (M4) | 89 m | 4.35 GB |

**Arm at least 64 GB of swap before gen-proof.** Gen-proof, not search, is the
binding constraint; budget it separately. This is the single most useful
operational fact in the artifact.

### Tier 5 — the n = 13 measurements

Not reproducible on commodity hardware and not claimed to be. `evidence/limits/`
records what was attempted, what the OS killed and at what footprint. Read, do
not run.

---

## 5. What moved out of the paper into this repository

Listed so the paper's cuts are auditable.

| moved | to | why |
|---|---|---|
| the full check-ID → claim table (28 rows) | `verifiers/CHECKS.md` | in-text the paper names scripts only |
| the nine known artifact defects | `verifiers/CHECKS.md` §"Known defects" | referee-relevant, not reader-relevant |
| verbatim verifier stdout (30 lines) | `verifiers/CHECKS.md` §"Reference output" | reproducible on demand |
| eight of the ten steelman defences | `theory/dispute.md` | the paper keeps S9 and S10, the two that carry weight |
| the six refuted repair families in full | `theory/DEADENDS.md` | the paper keeps a five-line table |
| the proofs of Facts 1–3, (R1)–(R3), Lemmas A–E | `theory/repair-wave2.md` §3 | the paper states them and proves only Theorem 6′ |
| Theorem 7, Lemma W2, Corollaries 7a/8b/8c | `theory/repair-wave2.md` §§5–6 | correct, narrow, not load-bearing |
| the MIN dual, `P(2,11)=9`-reduces-to-one-shape, realizability | `theory/shape-case-split.md` | "adjacent results" — cheap and correct, not the finding |
| the Huffman-2 generalisation | `theory/audit.md` §8.4(d) | proved modulo the same two broken lemmas; adds no independent risk |
| per-stage n=11 logs and incident history | `evidence/n11-certified/` | the paper keeps one five-row table |
| the level-ladder cost model, all eight negative-result campaigns with their measurements | `evidence/*`, `theory/endgame.md` | the paper keeps two paragraphs |
| the AI-agent methodology description | `README.md` §"How this was produced" | one short paragraph survives in the paper |

Net: **13,191 → 8,140 words** (7,685 excluding the reference list and the draft
banner), a 38 % reduction. Nothing was deleted; everything was relocated.

*Open length question for the architect.* The paper carries five claim tiers and
lands at ~15 typeset pages rather than the 10–14 targeted. The external
prior-art review recommends a split — the audit and repair (§§1–5) as a short
journal note, the collapse theorem and certified computation (§§6–8) as a
separate paper — which is the only cut that reaches the target without losing
required content. This layout supports either choice: the claim map in §3 is
already partitioned by tier.

---

## 6. Licensing and provenance

- **Our code and text:** MIT (code), CC-BY-4.0 (docs and data).
- **`engine/`:** patches only. The upstream `jix/sortnetopt` tree is *not*
  vendored; `PINNED` names commit `0b5d09c4…` and `build.md` gives the clone
  command. `git archive` of that commit reproduces `a243f270…`, recorded so a
  future reader can detect upstream history rewrites. Upstream's own licence
  governs upstream code; `NOTICE` states this.
- **`checker/`:** derived from Harder's Isabelle development; the extracted core
  is **unchanged** and `TRUST.md` says exactly which wrapper files we edited
  (`checker/snocheck/src/Main.hs`, via `sortnetopt-macos-large-read.patch`).
  The word "unchanged" is scoped there and must not be used unscoped anywhere.
- **`papers/`:** we redistribute nothing that is not clearly redistributable.
  The 1972 Plenum chapter is **not** included; `SOURCES.md` gives the citation,
  the page range we read, and the two items we could not obtain at all.
- **No witness network for any open case appears anywhere in this repository.**
  Four comparator lists are hard-coded in the verifiers (`T1`, `T2`, the
  15-comparator 6-sorter `T3`, and the transcribed `F(N)` row); each is named in
  `CHECKS.md` and none is a witness for an open case.

---

## 7. Gaps that must be closed before this repository can be published

These are release blockers, not wishes. Each is cheap except G1.

| # | gap | source | fix |
|---|---|---|---|
| **G1** | The n = 11 evidence chain is one markdown file. Search, prune-all and gen-proof have **no preserved artifact**; only the verify stage has a log, and it lives under a gitignored path. | internal review B-12 | preserve the four stage logs, or re-run and capture them |
| **G2** | `verify.log` records no checker identity, yet "unchanged verified checker" is the load-bearing phrase. | B-13 | record binary path + sha256 in the log; state the wrapper patch |
| **G3** | The v3 evidence tree has **no `MANIFEST.json` and no `checksums.sha256`** and is exempt from the project's own trust-boundary rule; `evidence_check.py` covers `b0..b4`/`e0..e5` only and exits 0 while touching none of it. | B-14 | extend `evidence_check.py`; add manifests |
| **G4** | Three of the nine tools cannot run from a clean checkout (they need a dump, a certificate and the engine binary). | B-17 | commit the kilobyte fixtures; add `--no-engine` |
| **G5** | 11 of 24 cited digests are no longer recomputable — the scratch directories are gone. One correction (`limits/probe13-43-addendum.md`) depends on a file that no longer exists. | B-15 | mark each unrecomputable digest as such in `MANIFEST.json`; do not silently keep citing them |
| **G6** | **The coverage census — 22.4 % and 49.6 %, the best new result in the paper — is not regenerable by any shipped tool.** It was computed over 153,011 networks in a gitignored scratch tree. | I-14 | write `evidence/census/coverage_census.py`; **the paper must not print these numbers until it exists** |
| **G7** | `verify_huffman2.py`'s `admissible_13()` shape ordering is unharmonised with the adjudicated authority (`verify_shape_case_split.py`: S1 = 6\|7 = C2, S2 = 5\|8 = C1). Harmonising changes a published sha256. | I-1, I-2 | decide *before* the hash is in print: harmonise and republish, or document the ordering as deliberate |
| **G8** | **Two shipped scripts still print retracted claims.** `verify_kraft_dispute.py` Part F prints `"S(13) >= S(11) + P(2,13) = 35 + 9 = the published bound"` — the 44 is *not* published — and its check `D-2` is labelled *"pass-through comparators are the SOLE obstruction"*, a claim wave 1 retracted (escapes are the right notion, and the label also overstates its own predicate, which tests only the fatal directions). Both were confirmed by a live run on 2026-08-22. An artifact evaluator will read the tool's own output before reading the paper. | NOTES B17, B7; internal review B-7 | rewrite both strings; this changes the published sha256, so bundle with G7 |
| **G9** | `theory/level-law.md` §0 claims Lemma L follows from three facts "all machine-checked". Theorem A is a code-reading audit and Theorem D has no machine check at all. | B-16 | rewrite §0; the paper already scopes this correctly and the doc must match |
| **G10** | Two archival sources were never obtained: the IEEE TC 1972 note and the 1971 Stanford dissertation. | external review §1.2–1.3 | `SOURCES.md` records the attempts and the negative result; re-check the new bitsavers Stanford collection at proof stage |

**Recommended order:** G4 (kilobytes, unblocks a third of the suite) → G6 (gates
a headline number) → G7+G8 together (one hash change, not two) → G1–G3, G5
(evidence chain) → G9 → G10 at proof stage.

---

## 8. What this repository deliberately does not contain

- **No search for a 44-comparator 13-sorter, and no target of 44 anywhere in any
  runnable path.** `engine/patches/sortnetopt-limits-v3.patch` seeds *upper*
  bounds only. Configuration files under `config/experiment-v1/` in the private
  research repository are frozen historical artifacts of a predecessor
  experiment that terminated `METHOD_REJECTED`; one of them records a
  44-comparator target. Nothing in this programme executed under them and they
  are not carried into this artifact.
- **No claim that `S(13) ≥ 44` is false.** It is unrefuted; ~15,000 adversarially
  searched networks did not break it.
- **No machine-checked proof of any theorem in §5 of the paper.** The Isabelle
  content in `checker/` verifies a certificate checker, not the new mathematics.
  `TRUST.md` says so in its first paragraph.
