# Sorting-network lower-bound certificate — wide container format (v2)

Status: **specification + unverified reference implementation**. The frozen
Isabelle/HOL-extracted checker (`snocheck -v`) does **not** read v2 and is not
changed by this document. Extending the verified checker to v2 is a separate,
later campaign.

Scope: this document specifies (a) the legacy container, normatively, so that
"unchanged" has a precise meaning; (b) the v2 wide container; (c) which one an
emitter must produce; (d) the cross-validation procedure that ties v2 back to
the verified checker.

Owner campaign: v3 engine limits. Related: `docs/sortnetopt-internals.md` §6
(certificate emission and the checker contract).

---

## 0. Why

`src/proof.rs` writes the step count as a `u32` and every witness step id as a
`u32`; `checker/snocheck/src/Decode.hs` reads both with `read32LE`. A
certificate is therefore capped at `2^32 - 1 = 4,294,967,295` steps. The n=13
extrapolation is ~1.5e11 certificate steps (`docs/sota-survey.md:209`), **35x
beyond what the container can express**. Every n<=11 certificate produced to
date is many orders of magnitude below the cap (n=11: 12,659,079 steps), so the
cap has never been reached and the legacy container must keep working
unchanged.

v2 widens the container only. **The step semantics are byte-for-byte the same
except that witness step ids are 8 bytes instead of 4.** No new proof rule, no
new witness kind, no change to the packed-set encoding, no change to what the
checker must verify.

**v2 does not make an n=13 monolithic certificate practical.** At n=13 a single
step payload is at least `2 + 1024 + 1 + 78*(1 + 13 + 8)` bytes ~ 2.7 kB, so
1.5e11 steps is ~4e14 bytes. v2 removes the *representational* cap; the
*practical* route to n>=12 certificates remains decomposition into
independently-checkable per-subproblem certificates that compose outside the
verified kernel (`docs/research/synthesis-ranked-queue.md`, Tier 2 item 6). v2
is what lets a *single decomposed job* at n=12/13 exceed 4.29e9 steps without
the emitter silently truncating.

---

## 1. Conventions

* All multi-byte integers are **little-endian**.
* Offsets are **absolute byte offsets from the start of the file**.
* `packed_len(c) = 2^max(0, c - 3)` bytes — the packed bitmap length for a
  `c`-channel output set. (This is `bit (0 max (channels-3))` in
  `Decode.hs:50`, and `((1 << c) + 7) / 8` in `OutputSet::packed_len_for_channels`
  for `c >= 3`; the two agree for all `c >= 3` and both give 1 for `c < 3`.)
* Bit `i` of the packed bitmap is bit `i mod 8` of byte `i div 8`, and is set
  iff the Boolean vector whose integer encoding is `i` (bit `j` of `i` = value
  on channel `j`) is present in the set.
* `FNV1A64(bytes)`: offset basis `0xcbf29ce484222325`, prime
  `0x00000100000001b3`, `h = (h XOR byte) * prime` per byte, wrapping at 64
  bits.
* `SHA256(bytes)`: FIPS 180-4, 32 raw bytes (not hex).

---

## 2. Legacy container (v1) — normative restatement

This is the format `GenProof::write_proof` emits today and the format
`Decode.hs` reads. It is reproduced here so that "bit-identical legacy output"
is checkable against a written spec rather than against the code.

```
offset 0                        u32   step_count
offset 4 + 12*i, i in 0..count  u64   payload offset of step i   (absolute)
offset 4 + 12*i + 8             u32   payload length of step i
offset 4 + 12*count             ...   payloads, concatenated in step-id order
```

There is **no magic and no version field**. The first four bytes are a step
count.

### 2.1 Step payload (identical in v1 and v2 except for the id width)

```
byte 0                       u8    channels c
byte 1                       u8    bound
bytes 2 .. 2+packed_len(c)   u8[]  packed bitmap of the step's output set
byte 2+packed_len(c)         u8    witness kind:
                                     0 = Huffman, polarity false
                                     1 = Huffman, polarity true
                                     2 = Successors
then, per witness, in order:
    u8 = 2                         witness absent
  | u8 invert (0 or 1)             witness present
    u8[pl]  perm                   pl = c-1 for Huffman, c for Successors
    u32 LE  step id                (v1)
    u64 LE  step id                (v2)
```

The witness list is terminated by the end of the payload; its length is
implicit and must equal:

* for Huffman: the number of extremal channels of the step's set at the given
  polarity, in **ascending channel index**;
* for Successors: the number of non-redundant comparators `(j, i)` enumerated
  as `for i in 0..c { for j in 0..i }`, in that order.

A step's own id is its index in the table; ids are assigned so that **every
witness id is strictly less than the id of the step referring to it**, and the
**last** step (`id = step_count - 1`) is the claim.

---

## 3. v2 container

### 3.1 File layout

```
[ header      64 bytes                     ]
[ step table  16 * step_count bytes        ]
[ payloads    payload_bytes bytes          ]
[ trailer     40 bytes                     ]
```

### 3.2 Header (64 bytes, offset 0)

| offset | size | field | value |
|---|---|---|---|
| 0  | 8 | `magic` | ASCII `SNOCERT2` = `53 4E 4F 43 45 52 54 32` |
| 8  | 4 | `format_version` | u32 = `2` |
| 12 | 4 | `flags` | u32, reserved; MUST be 0; a reader MUST reject non-zero |
| 16 | 8 | `step_count` | u64, number of steps; MUST be >= 1 |
| 24 | 8 | `table_offset` | u64, MUST be 64 |
| 32 | 8 | `payload_offset` | u64, MUST be `64 + 16 * step_count` |
| 40 | 8 | `payload_bytes` | u64, total length of the payload region |
| 48 | 2 | `root_channels` | u16, `channels` of step `step_count - 1` |
| 50 | 2 | `root_bound` | u16, `bound` of step `step_count - 1` |
| 52 | 4 | `reserved` | u32, MUST be 0 |
| 56 | 8 | `header_hash` | u64 = `FNV1A64(bytes[0..56])` |

`root_channels` / `root_bound` are a **convenience mirror** of the last step,
not an independent claim: a reader MUST verify they equal the decoded values of
step `step_count - 1` and reject on mismatch. They exist so that a tool can
report what a file claims without decoding the whole file.

### 3.3 Step table (offset 64)

`step_count` entries, entry `i` at offset `64 + 16*i`:

| offset | size | field |
|---|---|---|
| +0 | 8 | u64 absolute payload offset of step `i` |
| +8 | 8 | u64 payload length of step `i` |

Constraints a reader MUST enforce:

* every entry satisfies `payload_offset <= off` and
  `off + len <= payload_offset + payload_bytes`;
* `len >= 4` (channels, bound, at least one packed byte, kind);
* entries are **contiguous and in order**: `off_0 == payload_offset` and
  `off_{i+1} == off_i + len_i`, and `off_{last} + len_{last} ==
  payload_offset + payload_bytes`. (The emitter always writes them this way;
  requiring it makes the payload digest of §3.5 cover exactly the bytes the
  table addresses.)

### 3.4 Payloads

As §2.1, with `u64 LE` witness step ids.

### 3.5 Trailer (40 bytes, at `payload_offset + payload_bytes`)

| offset | size | field |
|---|---|---|
| +0 | 32 | `payload_sha256` = `SHA256(bytes[table_offset .. payload_offset + payload_bytes])` |
| +32 | 8 | `end_magic` = ASCII `SNOCEND2` |

The digest covers the step table **and** the payloads, so a flip anywhere after
byte 63 is detected; the header is covered by `header_hash`. Between them every
byte of the file except the trailer itself is integrity-checked, and the
trailer's own `end_magic` catches truncation.

Total file size is exactly `64 + 16*step_count + payload_bytes + 40`. A reader
MUST reject a file whose length differs.

---

## 4. Which container an emitter produces

An emitter MUST produce **v1** when `step_count <= 0xFFFF_FFFF`, and **v2**
otherwise. That rule makes every certificate producible today — every n<=11
run, by a factor of ~340 — byte-identical to what the pre-change emitter wrote,
so the frozen verified checker keeps accepting them with no transition period
and no flag.

`SORTNETOPT_CERT_FORMAT` overrides the rule for testing only:

| value | effect |
|---|---|
| unset / `auto` / `v1` | the rule above |
| `v2` | always emit v2 (used to produce small v2 files for validation) |

The override MUST NOT be used for a certificate intended for the verified
checker, which cannot read v2.

A v2-capable reader MUST accept both containers, dispatching on the 8-byte
magic: if `bytes[0..8] == "SNOCERT2"` the file is v2, otherwise it is v1.

This is unambiguous, and the argument is worth writing down because v1 has no
magic of its own. A v1 file's first 8 bytes are `step_count` (u32) followed by
the low 4 bytes of the *first* payload offset, and the first payload offset is
always exactly `4 + 12*step_count`. For a collision we would need
`step_count = LE32("SNOC") = 0x434F4E53 = 1,129,270,867`, which forces the
first offset to `4 + 12*1,129,270,867 = 13,551,250,408`, whose low 32 bits are
`0x27B7AB84`, i.e. bytes `84 AB B7 27` — not `"ERT2"` = `45 52 54 32`. No v1
file the emitter can produce starts with the v2 magic.

---

## 5. Checking semantics (unchanged from v1)

A v2 reader performs exactly the checks the reference checker
(`checker/snocheck/src/Check.hs`) performs, which are the unverified mirror of
`checker/verified/Checker.thy`. For every step `s` in `0 .. step_count-1`:

1. Decode step `s`. Let `A` be its set (width `c`), `b` its bound.
2. Every witness id `w` referenced by step `s` MUST satisfy `w < s`.
   (`checkStep`'s `steps'`.)
3. **Huffman, polarity `p`.** Let `E = [i in 0..c : (e_i XOR flip_p) in A]` in
   ascending order, where `flip_p = 0` for `p = false` and `2^c - 1` for
   `p = true`. The number of witnesses MUST equal `|E|`. For each `(i, witness)`
   pair positionally, let `P_i = pruneExtremal(p, i, A)` (filter `A` to vectors
   whose bit `i` equals `p ? 0 : 1`, then delete bit `i`), and let
   `b_i = getBound(witness, P_i)`. Require `huffmanBound([b_i]) >= b`, where
   `huffmanBound` is the greedy merge that repeatedly pops the two smallest
   values `x <= y` and pushes `1 + max(x, y)`, returning the last remaining
   value.
4. **Successors.** Let `S = [applyComp(i, j, A) : i in 0..c, j in 0..i]`
   keeping only the non-redundant ones, in that order. `applyComp(i,j,A)` is
   non-redundant iff `A` contains some vector `v` with `v & (2^i | 2^j) == 2^i`
   **and** some vector with `v & (2^i | 2^j) == 2^j`; the successor maps every
   `v` with `v & (2^i|2^j) == 2^j` to `v XOR (2^i|2^j)` and fixes the rest.
   Require `|S| == |witnesses|`, require `|A| > 1 + c` ("set might already be
   sorted"), and for each pair positionally require
   `getBound(witness, S_k) + 1 >= b`.
5. `getBound(None, V)` = `0` if `|V| <= 1 + channels(V)` else `1`.
   `getBound(Some(inv, perm, w), V)`: let `W` be step `w`'s set; if `inv`,
   complement every vector of `W` within its width; then permute, where the
   permuted vector `u` of `v` has `bit i of u = bit perm[i] of v`; require
   `permute(perm, W')` is a **subset** of `V` and return step `w`'s bound.
   A reader SHOULD additionally require that `perm` is a genuine permutation of
   `0..width` and that `W` has the same width as `V` — the verified checker
   does (`Checker.thy:425-445`); `Check.hs` relies on the subset test to catch
   violations.

The claim of the certificate is `(channels, bound)` of step `step_count - 1`.

---

## 6. Cross-validation procedure

Because the verified checker cannot read v2, v2's correctness is established by
**agreement on transcoded certificates**, not by trusting the v2 reader.

1. Produce a legacy certificate the normal way (`search` -> `prune-all` ->
   `gen-proof`) at n=9 and n=10 and verify it with the frozen
   `snocheck -v`. Record `Just (n, bound)`.
2. Transcode the legacy file to v2 with `tools/cert_v2.py transcode`. The
   transcoder is a pure container rewrite: it re-emits the identical payload
   bytes with the four-byte ids widened to eight, and it MUST be able to
   transcode back (`tools/cert_v2.py untranscode`) to a file byte-identical to
   the input. Round-trip byte-identity is the evidence that no step content was
   altered.
3. Check the v2 file with the reference checker
   (`tools/cert_v2.py check`). It MUST report the same `(channels, bound)` the
   frozen checker reported.
4. **Negative tests.** For each of: a byte flipped in the magic; a byte flipped
   in `step_count`; a byte flipped in `header_hash`; a byte flipped in the step
   table; a byte flipped in a payload; the trailer truncated — the reference
   checker MUST reject with a specific message, and MUST NOT report a bound.
5. **Semantic negative tests.** With the integrity fields *recomputed* after
   the edit (so the digests pass and only the proof content is wrong): a witness
   id raised to `>= s`; a perm entry duplicated; a bound raised by one on a
   non-root step. All MUST be rejected by the checking pass, not by the digest
   pass.

Steps 4 and 5 are separated deliberately: step 4 tests the container, step 5
tests the checker.

---

## 7. What is deliberately not in v2

* **No compression.** Payloads are dominated by packed bitmaps, which are
  already dense; and a compressed container would put a decompressor inside the
  trust boundary when the verified checker is eventually extended.
* **No random-access index by output set.** The checker walks all steps.
* **No provenance, no search metadata, no upper bounds.** The certificate
  records only the step DAG (`docs/sortnetopt-internals.md` §6.3). Anything
  else would have to be either verified or ignored, and ignored fields in a
  proof object are a hazard.
* **Perm entries stay `u8`**, capping the format at 255 channels. n=13 needs
  13.
* **`bound` stays `u8` in the payload** (and `u16` in the header mirror, purely
  as a decoded convenience). The largest bound of interest is 45 at n=13 and
  the quadratic ceiling at n=255 would be 32,385 — a future >64-channel format
  would need a payload change, which is out of scope and is noted here so it is
  not discovered later.

---

## 8. Implementation status

| piece | where | status |
|---|---|---|
| emitter, both containers | `src/proof.rs` (`write_proof_v1` / `write_proof_v2`), in `tools/patches/sortnetopt-limits-v3.patch` | implemented |
| container selection | `choose_wide`, `SORTNETOPT_CERT_FORMAT` | implemented |
| reference reader / checker | `tools/cert_v2.py check` | implemented, **unverified** |
| transcoder both ways | `tools/cert_v2.py transcode` / `untranscode` | implemented |
| validation battery | `tools/cert_v2.py selftest` | implemented |
| **verified checker support for v2** | `checker/verified/Checker.thy` | **not started, out of scope, separate campaign** |

Evidence recorded by the v3 engine-limits campaign (see that campaign's report):

* the frozen verified checker accepts the n=9 and n=10 legacy certificates
  emitted by the patched binary — `Just (9,25)` and `Just (10,29)`;
* `tools/cert_v2.py check` returns the *same* verdicts, `OK (9,25)` and
  `OK (10,29)`, on the v2 files the Rust emitter produced from the same pruned
  input;
* the Rust `SORTNETOPT_CERT_FORMAT=v2` output and the Python transcoder's
  output from the corresponding v1 file are **byte-identical** at n=8, n=9 and
  n=10, and `untranscode` reproduces the v1 file byte-for-byte — two
  independent implementations agreeing on every byte of the container;
* `selftest` passes all 13 lines on the n=9 and n=10 certificates, including
  the six container-corruption and three semantic-corruption negatives of §6.

**Known divergence from the verified checker**, recorded rather than hidden:
`Check.hs` — and therefore `cert_v2.py`, which mirrors it — does not enforce
`bound ≠ 0` in the Successors rule, which `Checker.thy:553-574` does. The
reference checker is thus very slightly more permissive than the verified one.
That is safe for its only intended use (cross-checking files the verified
checker has already accepted) and must be closed before the reference checker
is ever used as an *authority*.
