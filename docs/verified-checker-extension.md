# Extending the verified checker to prefix-rooted certificates

Status: **the extension exists, is proved, and runs.** `tools/verified/Prefix_Checker.thy`
adds a prefix-rooted entry point to the Isabelle/HOL checker, with a machine-checked
soundness theorem, and extracts to Haskell through the upstream pipeline;
`tools/verified/build.sh` turns it into a working binary, `snocheck2`, which accepts
all eight campaign prefix certificates and reproduces the frozen checker's verdicts on
the legacy ones. Nothing in the pinned clone's `checker/` is modified; the frozen
`snocheck` is untouched and remains the anchor for full-problem v1 results.

Read §5 before quoting any of this as "verified": the proof rules and the root
construction are verified, the *decoder* is not.

Owner campaign: verified-checker campaign. Prerequisites read: `docs/certificate-format-v2.md`
(all sections), `docs/sortnetopt-internals.md` §6, `evidence/v3/prefixcert/report.md`,
`checker/verified/*.thy` in the pinned clone.

---

## 0. Summary of findings

Three things were expected to be hard and turned out not to be.

1. **The proof-step semantics are already parameterised over the root set.**
   The full cube is *not* baked into the soundness argument. It appears only in
   the last 35 lines of `Checker.thy`. This is the single fact that makes the
   whole extension cheap; §2 works through it.
2. **u64 witness ids need no Isabelle work at all.** The verified core's `int`
   extracts to a newtype over Haskell `Integer`, i.e. arbitrary precision. The
   4-byte cap lives entirely in `Decode.hs`'s `read32LE`, which is unverified
   glue. §3.1.
3. **The extraction pipeline still works, exactly.** Isabelle2020 rebuilds the
   upstream session and regenerates `Verified/Checker.hs` differing from the
   committed frozen copy by only the header comment line and the three hunks of
   `strict_and_parallel.patch`. §4.

And one thing that was recorded as a single known defect turned out to be four.
§6.

---

## 1. Reproducing the verified pipeline

| step | cost |
|---|---|
| Isabelle2020 macOS bundle (`Isabelle2020_macos.tar.gz`, 425,926,872 bytes) | one download |
| `isabelle build -d . Sorting_Networks` (HOL-Library + the 5 upstream theories) | **~25 s wall** (14 s for the session itself, 8 threads) |
| `isabelle build -e` to export the Haskell | ~5 s |
| the prefix extension session on top | ~1 s |

Isabelle2020 is x86_64 and runs under Rosetta on this M4; the bundle ships prebuilt
`Pure` and `HOL` heap images, so no HOL bootstrap is needed. Upstream's `README.md`
requires "Isabelle2019 or Isabelle2020"; 2020 was chosen for fidelity.

The upstream `ROOT` asks for a PDF document, which needs a LaTeX toolchain. The
working copy under `.build/v3-vcheck/baseline/ROOT` sets `document = false` and is
otherwise identical. The theories themselves are byte-identical copies
(`Checker.thy` sha256 `dca9c0e253052a7228a877095d4b4cda97c1d8ef366ab177580ea121d9e331ae`
in both the pinned clone and the working copy).

**Fidelity check.** Regenerated `Verified/Checker.hs` vs the frozen committed copy:

```
0a1   > -- Generated using update_extracted_code.sh, do not edit --
14a16 > import qualified Parallel;
73c75 < data Vect_trie = VtEmpty | VtNode Bool Vect_trie Vect_trie;
      > data Vect_trie = VtEmpty | VtNode !Bool !Vect_trie !Vect_trie;
122c124 < par a b = b;
        > par = Parallel.par;
```

That is the header comment plus exactly the three hunks of
`checker/verified/strict_and_parallel.patch`. The extraction pipeline is therefore
reproduced, not approximated.

---

## 2. Why the extension is small: where the full cube actually enters

This is the load-bearing observation, so it is worth being precise.

`Checker.thy:447` defines what checking a step buys you:

```
step_checked step = (
  list_all (\<lambda>xs. length xs = nat (step_width step)) (step_vect_list step) \<and>
  pls_bound (list_to_vect ` set_vt (vt_list (step_vect_list step))) (nat (step_bound step)))
```

`pls_bound A b` (`Sorting_Network.thy:167`) is a statement about **an arbitrary set
`A`**: every comparator network that sorts `A` has at least `b` comparators. Not about
the cube. `check_proof_spec` (`Checker.thy:1435`) lifts `check_proof` to
`step_checked` for every step, and `get_bound_bound` (`:452`) is already the general
"witness subsumes target" lemma:

> if every step below `step_limit` is `step_checked`, and `set_vt A` is a set of
> width-`n` vectors, and `get_bound proof_steps step_limit witness n A = Some b`,
> then `pls_bound (list_to_vect ` set_vt A) b`.

The full cube enters in exactly one place, `step_checked_bound` (`:1450`), which takes
the *last* step's set, observes it is a subset of `{v. fixed_len_bseq n v}`, and
applies `bound_mono_subset` to widen the bound to the cube. `check_proof_get_bound_spec`
(`:1467`) then reports `lower_size_bound (nat width) (nat bound)`.

So the interior of the checker — `check_step`, `check_successors`, `check_huffman`,
`get_bound`, and the two big lemmas `check_successors_step_checked` (~150 lines) and
`check_huffman_step_checked` (~170 lines) — never mentions the cube and **needs no
change and no re-proof**. A prefix root only replaces the final widening step.

Note also what §9.4 P5 of the format spec asks for: apply `getBound` with the root
`(invert, perm, step)` witness against `X_P`. That is *literally* `get_bound`, and
`get_bound_bound` is *literally* its soundness lemma. P5 was designed to be free, and
it is.

---

## 3. Exact list of changes, by requirement

### 3.1 u64 witness ids (the v2 wide container)

**Isabelle changes required: none.**

`proof_witness` carries `witness_step_id :: int`; Isabelle `int` extracts (via
`HOL-Library.Code_Target_Numeral`) to `newtype Int = Int_of_integer Integer` — arbitrary
precision. `Translate.hs` already widens Haskell `Int` to `Integer`. The `2^32 - 1` cap
is imposed solely by `Decode.hs:read32LE` and by the 12-byte v1 table entry.

Extending the *verified* checker to v2 is therefore a pure glue task: a decoder that
reads the 64-byte header, 16-byte table entries and u64 ids. No theory edit, no lemma,
no re-extraction. This was previously recorded as "not started, out of scope, separate
campaign" (`docs/certificate-format-v2.md` §8) on the implicit assumption that the
verified core was the obstacle. It is not.

**Demonstrated.** `snocheck2 -v` on the n=9 legacy certificate transcoded to v2 by
`cert_v2.py transcode` returns `Just (9,25)` — the same verdict the frozen `snocheck -v`
gives on the v1 original. The verified checker reads the wide container today.

### 3.2 Prefix roots (the v2p container)

**Isabelle changes required: one new theory. Zero edits to existing theories. Zero
lemmas re-proven.**

`tools/verified/Prefix_Checker.thy` (190 lines) adds, in order:

| new item | kind | purpose | difficulty |
|---|---|---|---|
| `all_vects :: nat => bool list list` | `fun` | the full cube as a list of bool lists | trivial |
| `set_all_vects` | lemma | `set (all_vects n) = {xs. length xs = n}` | easy induction; one `metis` for the bool split |
| `all_vects_vt`, `set_vt_all_vects_vt` | def + lemma | the cube as a `vect_trie` | one-liner via `set_vt_list` |
| `list_to_vect_all_vects_vt` | lemma | `list_to_vect \` set_vt (all_vects_vt n) = {v. fixed_len_bseq n v}` | the only nontrivial set equality; `\<supseteq>` needs the witness `xs = map v [0..<n]` |
| `apply_cmp_vt`, `apply_cmps_vt` | defs | apply one / many comparators to a trie | reuses the exact idiom `check_successors` already uses |
| `set_vt_apply_cmp_vt`, `apply_cmp_vt_width`, `apply_cmps_vt_width` | lemmas | width preservation across the prefix | `length_apply_cmp_list` already exists |
| `list_to_vect_apply_cmp_vt` | lemma | one-comparator semantics | **discharged by the existing `apply_cmp_as_apply_cmp_list'`** (`Checker.thy:597`) |
| `list_to_vect_apply_cmps_vt` | lemma | fold semantics over the prefix | induction on the comparator list |
| `check_prefix_proof_get_bound` | def | the new entry point | 6 lines |
| `check_prefix_proof_get_bound_spec` | **theorem** | `partial_lower_size_bound (fold apply_cmp P \` {v. fixed_len_bseq n v}) b` | assembles `check_proof_spec` + `get_bound_bound` + `pls_bound_implies_lower_size_bound` |
| `prefix_network_size_bound` | **corollary** | any network beginning with `P` that sorts all n-channel inputs has `>= length P + b` comparators | `fold_append`, three lines |

The entry point is:

```
check_prefix_proof_get_bound cert n prefix root_witness = (
  if check_proof cert \<and> list_all (\<lambda>c. fst c < n \<and> snd c < n) prefix
  then get_bound (cert_step cert) (cert_length cert) root_witness n
         (apply_cmps_vt prefix (all_vects_vt n))
  else None)
```

`check_proof` and `get_bound` are Checker.thy's, unchanged and unqualified.

**Estimated vs actual difficulty.** Estimated a day of expert Isabelle time; actual
was about an hour, with the theory building on the first substantive attempt (two
mechanical failures first: an unqualified import, and a `@{thm ...}` antiquotation
forward-referencing a theorem later in the same file). The 25-second edit/build loop
is what makes this cheap; anyone continuing this work should keep that loop.

There are **no `sorry`, `oops`, or admitted lemmas** anywhere in the new theory.

### 3.3 What the new theorem actually says

```
theorem check_prefix_proof_get_bound_spec:
  assumes "check_prefix_proof_get_bound cert n prefix root_witness = Some b"
  shows   "partial_lower_size_bound (fold apply_cmp prefix ` {v. fixed_len_bseq n v}) b"

corollary prefix_network_size_bound:
  assumes "check_prefix_proof_get_bound cert n prefix root_witness = Some b"
    and   "\<And>x. fixed_len_bseq n x \<Longrightarrow> mono (fold apply_cmp (prefix @ cn) x)"
  shows   "length (prefix @ cn) \<ge> length prefix + b"
```

The corollary is the §9.1 claim verbatim: *any* `n`-channel sorting network beginning
with `P` has at least `L + b` comparators. Compare `check_proof_get_bound_spec`, which
yields `lower_size_bound (nat width) (nat bound)` — the two live side by side and
neither weakens the other.

One property is **stronger than the reference checker**: check P3 (prefix binding) is
discharged *by construction*, not by comparison. The verified core computes `X_P` from
the prefix itself and never reads the stored packed root set. `cert_v2.py` recomputes
`X_P` and compares it against the stored copy; the verified core makes the stored copy
irrelevant to the claim. A corrupted stored root set cannot change what is proved.

---

## 4. The extraction pipeline for the extension

`tools/verified/Prefix_Checker_Codegen.thy` restates the soundness theorem (so it is
re-checked in the theory that performs the extraction, and the exported constant is
provably the one the statement is about) and exports:

```
check_prefix_proof_get_bound :: Proof_cert -> Nat -> [(Nat, Nat)] -> Maybe Proof_witness -> Maybe Nat
check_proof_get_bound        :: Proof_cert -> Maybe (Int, Int)
```

plus `nat_of_integer`, `integer_of_nat`, `int_of_integer`, `integer_of_int` and the
five certificate constructors, into `Verified/PrefixChecker.hs` (546 lines). Both entry
points are exported from one module so a single binary can check v1, v2 and v2p.

Build recipe (reproducible from a clean checkout, given the Isabelle bundle):

```
isabelle build -d tools/verified-baseline -d tools/verified -e Sorting_Networks_Prefix
```

where the baseline directory holds byte-identical copies of the five upstream theories
plus a `document = false` ROOT. See `.build/v3-vcheck/` for the working tree used here.

### 4.1 `snocheck2`

`tools/verified/build.sh` builds a new binary, `snocheck2`, end to end from a clean
tree in one command: it copies the upstream theories out of the pinned clone, builds
and extracts through Isabelle, prints the fidelity diff of §1, assembles the Haskell
tree, applies the three `strict_and_parallel` edits, and compiles with the GHC 8.6.5
that the b3 toolchain already installed. **The frozen `snocheck` is never rebuilt or
touched.**

```
snocheck2 -v FILE    v1/v2 full-problem check   (check_proof_get_bound)
snocheck2 -p FILE    v2p prefix-rooted check    (check_prefix_proof_get_bound)
```

`-v` on a v2p file and `-p` on a non-v2p file both refuse with exit 2: a prefix claim
must never be printed as a full-problem bound.

Only files this campaign wrote live in `tools/verified/`. The three unchanged upstream
Haskell modules (`VectSet`, `ProofStep`, `Parallel`) and the five upstream theories are
copied out of the pinned clone at build time rather than vendored, so the pinned clone
stays the single source of truth for third-party code and nothing is duplicated into
the repository.

**Known limitation — the two SHA-256 checks are skipped.** The available GHC package
database has neither `cryptohash-sha256` nor `SHA`, so `Decode2.hs` does not verify the
trailer `payload_sha256` (§3.5) nor the v2p `section_sha256` (§9.3). They are *skipped
and announced*, not faked: `snocheck2` prints a warning naming exactly the two skipped
checks on every run. Everything else is enforced — magic, `format_version`/`flags`,
the FNV1a64 `header_hash`, all length/offset/table-contiguity constraints, `end_magic`,
the full prefix-section structure, and the `root_perm` permutation check. This weakens
*corruption detection only*; it does not weaken the proof check, because the verified
core reads the step DAG itself and the digests were never inputs to soundness. Pair
`snocheck2` with `cert_v2.py`, which does check both digests, until a SHA-256 library
is available.

### 4.2 Cross-validation

`tools/verified/crosscheck.py` runs `cert_v2.py` and `snocheck2` over the same file and
over seven semantically corrupted variants of it (digests recomputed, so the *proof*
layer is what is being tested rather than the integrity layer). On the n=8 prefix
certificates all cases pass: identical bounds on the originals, and both checkers
reject every corruption.

The highest-value line in that matrix is **D1**. Zeroing a real Successors step's bound
is rejected by `snocheck2`, whose core *is* the extracted `Checker.thy`. That is
independent confirmation that the D1 guard added to `cert_v2.py` matches the verified
rule — it is a check against the verified checker, not two mirrors of one reading of it.

One case is informative rather than pass/fail: **changing the last prefix comparator**.
`cert_v2.py` rejects it because the stored root set no longer matches the recomputed
`X_P` (its P3). `snocheck2` has no such check — it never reads the stored root set — and
rejects for a different and stronger reason: the recomputed `X_P` no longer subsumes the
root witness. Both reject, for different reasons, and `snocheck2`'s reason is the one
that bears on soundness.

**The comparator-convention swap is demonstrated, not assumed.** For every prefix
certificate tested, the un-swapped orientation produces a *different* `X_P` of the same
cardinality which does **not** subsume the root witness:

| certificate | prefix | `X_P` correct | `X_P` un-swapped |
|---|---|---|---|
| `regress-wide/default-n8` | `1-0` | 192 vectors, subsumes | 192 vectors, does **not** subsume |
| `campaigns/n9-d2/7525bd33ce7850ea` | `1-0,2-0` | 320, subsumes | 320, does **not** subsume |
| `campaigns/n9-d2/195fd065a6cdcad7` | `1-0,3-2` | 288, subsumes | 288, does **not** subsume |

So `snocheck2` *accepting* these certificates is positive evidence that its swap is
right: the wrong orientation would have been rejected. This is the one glue obligation
that a test can actually discriminate, and it does.

### 4.3 Results on the real campaign certificates

All eight per-job certificates of the n=9 and n=10 depth-1/depth-2 campaigns, checked
by the verified core. Every `(n, L, prefix, bound)` matches what `cert_v2.py
prefix-check` independently reports, and every `bound` equals the job's `claimed`.
Measured twice, independently, with identical results.

| campaign / job | verified verdict | wall |
|---|---|---|
| n9-d1 `1127234971ddf6ab` | `OK verified prefix n=9 L=1 prefix=1-0 bound=24 claimed=24` | 3-4 s |
| n9-d2 `195fd065a6cdcad7` | `... n=9 L=2 prefix=1-0,3-2 bound=23 claimed=23` | 3 s |
| n9-d2 `f447a179d768726d` | `... n=9 L=2 prefix=1-0,1-0 bound=24 claimed=24` | 3-5 s |
| n9-d2 `7525bd33ce7850ea` | `... n=9 L=2 prefix=1-0,2-0 bound=23 claimed=23` | 3-4 s |
| n10-d1 `fc91c44f5e4e4fdd` | `... n=10 L=1 prefix=1-0 bound=28 claimed=28` | 11-13 s |
| n10-d2 `f7b3fd126ddf0999` | `... n=10 L=2 prefix=1-0,3-2 bound=27 claimed=27` | 11-13 s |
| n10-d2 `259c4a8b3fd550b9` | `... n=10 L=2 prefix=1-0,2-0 bound=27 claimed=27` | 11 s |
| n10-d2 `d5f5370feaa95d44` | `... n=10 L=2 prefix=1-0,1-0 bound=28 claimed=28` | 10 s |

Composition is unchanged and still `min(L + b)` = 25 / 25 / 29 / 29 for the four
campaigns, now with a verified bound behind every term of each `min`.

Anchors, for comparison, all agreeing:

| file | frozen `snocheck -v` | `snocheck2 -v` | `cert_v2.py check` |
|---|---|---|---|
| n=9 legacy v1 | `Just (9,25)` | `Just (9,25)` | `OK (9,25)` |
| n=10 legacy v1 | `Just (10,29)` | `Just (10,29)` | `OK (10,29)` |
| n=9 transcoded to v2 | *cannot read* | `Just (9,25)` | `OK (9,25)` |

Cost is roughly a second per 5,000 certificate steps at n=10; the n=10 files are
9.8-12 MB and 59k-69k steps.

---

## 5. The trust boundary: what is verified and what is not

This matters more than the theorem, because the theorem is only as useful as the
glue that feeds it.

**Verified** (machine-checked, extracted, no hand-written step in between):
every proof rule; the whole step DAG walk; `get_bound`'s permutation/inversion/subset
witness rule; the construction of `X_P` from the prefix; the final bound arithmetic;
the size-bound conclusion.

**Unverified glue** — the same category as `Decode.hs`/`Translate.hs` in the frozen
build, and the reason the frozen checker has always had an unverified perimeter:

1. **Container decoding.** Header, prefix section, step table, payload layout, u64 ids.
   A decoding bug produces a true theorem about a *different* certificate.
2. **The comparator convention swap.** The v2p prefix section stores `(a, b)` meaning
   "`a` receives the pairwise maximum, `b` the minimum" (§9.3). Isabelle's `apply_cmp
   (i, j)` sends `i` to the **minimum**. So stored `(a, b)` must be passed as `(b, a)`.
   Get this wrong and you obtain a perfectly valid theorem about the mirror-image
   prefix. This is the single most dangerous line in the glue and is commented as such
   in both the theory header and the decoder.
3. **The `claimed_bound` comparison.** The verified core returns the bound it proved;
   comparing it against the file's `claimed_bound` happens in `Main`. Mitigated by
   printing the *verified* number in the OK line, so the operator sees the real value
   rather than the claimed one.
4. **Integrity digests** (FNV1a64 header hash, the two SHA-256s). These protect against
   corruption, not against a lying prover; the verified core needs none of them.
5. **Reporting.** That a v2p result is displayed as a prefix claim and never as a
   full-problem bound.

**Outside every checker**, verified or not — the §9.6 composition obligations:
exhaustiveness of the prefix set, certificate/job agreement, and coverage. These are
`tools/class_campaign.py verify`'s job and no certificate discharges them. A verified
per-job checker does not make a class result unconditional; it removes one of the three
reasons it was conditional.

---

## 6. The divergence list (was one, is four)

`docs/certificate-format-v2.md` §8 recorded one known divergence between the reference
checker and `Checker.thy`. Reading the two side by side turned up four. All are now
closed in `tools/cert_v2.py`, each guarded at its site and each with a selftest that
pairs the negative with a positive control differing only in the guarded field.

| id | rule | `Checker.thy` | what `Check.hs` / `cert_v2.py` did |
|---|---|---|---|
| D1 | Successors requires `bound \<noteq> 0` | `:566` | omitted; `b + 1 >= 0` holds vacuously, so a bound-0 Successors step was accepted |
| D2 | Huffman requires `width \<noteq> 0` | `:921` | omitted; a width-0 Huffman step has no extremal channels, no witnesses, and `huffmanBound [] = 0` justified bound 0 |
| D3 | Huffman requires a nonempty witness list | `:923` | omitted. Note `Check.hs` does not *accept* these — its `huffmanBound'` is a partial function and raises a pattern-match failure on the empty queue. It crashes where the verified checker returns `False`. `cert_v2.py` returned 0 and accepted. |
| D4 | every vector of a step's set must have length = the step's width | `:449`, `:569`, `:922`, and `B_list` in `get_bound` at `:441` | never checked. The Haskell decoder cannot violate it — `VectSet.asBoolVectList` truncates every vector to `channels` bits — so the frozen binary silently *reinterprets* an out-of-range vector instead of rejecting it. Only reachable for `channels <= 2`, where `packed_len` rounds up to a whole byte. |

D1 is a permissiveness gap, not a soundness hole: `pls_bound A 0` is trivially true, so
a bound-0 Successors step could never have made a false claim. It mattered because a
checker used as an *authority* must reject everything the verified checker rejects, and
that is now exactly the standard `cert_v2.py` is held to. D4 is the interesting one: it
is the only place where the frozen `snocheck` and a faithful mirror can disagree on
*content* rather than on accept/reject, and the mirror is deliberately the stricter of
the two.

Evidence that closing them broke nothing: `cert_v2.py selftest` 31/31 on the n=10
legacy certificate paired with a v2p file; `OK (9,25)` / `OK (10,29)` unchanged on the
legacy certificates, agreeing with the frozen `snocheck -v`'s `Just (9,25)` /
`Just (10,29)`; all 8 campaign prefix certificates and all 4 regression v2p files still
accepted with identical bounds.

---

## 7. The 13 GB misread hazard

`tools/snocheck_guard.sh` refuses to hand a v2/v2p file to the frozen `snocheck`.
v1 has no magic — its first four bytes are a step count — so `snocheck` reads the ASCII
`"SNOC"` as a step count of 1,129,270,867 and walks a
`4 + 12 * 1,129,270,867 = 13,551,250,408`-byte step table. The wrapper checks the magic,
identifies v2 vs v2p from `format_version` so the message names the right tool, and
additionally enforces the v1 layout invariant `first_payload_offset == 4 + 12*step_count`
so that a truncated or non-certificate file is refused before any large read. Everything
else is passed through unchanged and in order, so `+RTS -N10 -RTS` blocks still work.

Note for wiring: `tools/class_campaign.py` **never invokes `snocheck`** — its per-job
certificates are v2p, and it calls `tools/cert_v2.py prefix-check`. Every `snocheck -v`
invocation in this repository is a hand-run command in a docs or evidence page. The
wrapper is therefore the operator-facing guard, and the `snocheck -v ...` recipes in
`docs/` and `evidence/` should be read as `tools/snocheck_guard.sh -v ...` from now on.
(Evidence pages are frozen and are not rewritten.)

---

## 8. What is still missing

1. **The glue is unverified**, as it always has been for the frozen checker. The v2p
   decoder is newer and less exercised than `Decode.hs`, and it carries the convention
   swap of §5.2. Cross-checking `snocheck2` against `cert_v2.py` on every certificate,
   including corruption cases, is the mitigation, not a proof. (The swap specifically
   *is* discriminated by the tests — §4.2 — so it is the best-evidenced part of the
   decoder, not the weakest.)
2. **`snocheck2` skips the two SHA-256 integrity checks** for want of a library
   (§4.1). Corruption detection, not soundness, but it means `snocheck2` alone is not
   a substitute for `cert_v2.py` on an untrusted file. Fixing this needs one package
   or ~80 lines of SHA-256; it is the cheapest remaining item on this list.
3. **No verified checker reads v1 and v2p from the same audited decoder.** `snocheck2`
   has its own decoder; the frozen `snocheck` keeps its own. They agree on the v1
   certificates, which is evidence, not equivalence.
4. **`Prefix_Checker.thy` is not upstream** and has had one author. It should be read
   by a second person before a class result is published on the strength of it. The
   statements to read are the two in §3.3; everything else is plumbing.
5. **The composition argument (`certificate-format-v2.md` §9.6) has no machine-checked
   form at all.** It is a `min` over `L + b_P` plus an exhaustiveness claim, checked by
   Python. With the per-job checker now verified, this is the weakest link in the chain
   for a class result — ahead of the checker, which is a change from where things stood
   before this campaign.

---

## 9. What the class programme should treat as its checker story

* **Full-problem n<=11 results** keep the frozen `snocheck -v` as the anchor.
  Unchanged, and it should stay unchanged: it is the one binary nothing in this
  campaign has touched.
* **Per-job prefix certificates** are checked by **both** `snocheck2 -p` and
  `cert_v2.py prefix-check`, and a campaign should record both verdicts. `snocheck2`
  is the authority on the *bound*; `cert_v2.py` is the cross-check that the decoder
  did not misread the file, and it is the one that checks the two SHA-256 digests
  (§4.1) and the stored-root consistency. Neither subsumes the other today. Running
  both costs about 25 s for a whole n=10 depth-2 campaign.
* A class result may now be described as **resting on a verified prefix checker with
  an unverified decoder**, rather than on an unverified checker. That is a real
  strengthening and should be stated in exactly those words — not as "verified"
  unqualified.
* The three composition obligations of `certificate-format-v2.md` §9.6 remain outside
  the verified perimeter and remain the reason a class result inherits its class's
  epistemic status. They are now the binding constraint (§8.5).
* **Never hand a v2/v2p file to the frozen `snocheck`.** Use
  `tools/snocheck_guard.sh`, which refuses on the magic before exec'ing it.
