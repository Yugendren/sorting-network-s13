#!/usr/bin/env python3
"""extract_mining_dataset.py -- build a per-state labeled dataset for the
"certified lemma mining" line of the S(13) programme, from a completed
sortnetopt search+prune+gen-proof dump directory
(docs/sortnetopt-internals.md sections 2-3, 6; docs/certificate-format-v2.md).

Stdlib + numpy only. Read-only w.r.t. the dump directory.

-----------------------------------------------------------------------------
WHAT A DUMP DIRECTORY CONTAINS (recap, see docs/sortnetopt-internals.md)
-----------------------------------------------------------------------------

A dump directory is the output of the pipeline `search -> prune-all ->
gen-proof` (search_and_verify.sh) for one fixed n:

  * `index.txt`               one line per group, e.g. "group_6_4.bin"
  * `group_{c}_{b}.bin`       every canonical output-set (channel count c,
                               *terminal* lower bound b) the search's
                               StateMap ever held, as a headerless array of
                               fixed-stride packed bitmaps (stride =
                               packed_len(c) = (2**c + 7) // 8 bytes for
                               c >= 3). This is written once, at the very
                               end of `Search::search`, after the DP has
                               reached its fixpoint (search.rs:73-75,
                               80-107) -- so every record is a *terminal*
                               state, not a transient one. StateMap never
                               evicts (docs section 2.5), so this is a
                               complete census of every distinct canonical
                               set the search ever computed a bound for at
                               that (channels, bound) pair. This is
                               "EXPLORED".
  * `group_{c}_{b}.pbin`      the subset of the matching .bin file that
                               survived offline subsumption pruning
                               (prune.rs `prune`/`prune_all`): the
                               antichain-minimal set of sets at that (c, b)
                               under permutation + complement subsumption. A
                               record present in .bin but absent from .pbin
                               was thrown away because some other set
                               already in the pruning index subsumes it
                               (A.subsumes(B) = A is a permuted/complemented
                               subset of B; see internals doc section
                               2.4/3.3). This is "SUBSUMED-AWAY, i.e.
                               explored-but-wasted in the specific, measured
                               sense that accounts for ~99.4% of the
                               store-then-prune gap (internals doc section
                               8.0)".

                               IMPORTANT PROVENANCE CAVEAT: the *pinned*
                               original clone's `prune_all` (the one
                               documented in docs/sortnetopt-internals.md)
                               only ever compares a record against other
                               records from the *same* (channels, bound)
                               group. The v3-limits patch stack adds an
                               opt-in `SORTNETOPT_CROSS_BOUND_PRUNE=1` mode
                               (`prune_all_cross_bound`, prune.rs) that
                               instead compares across *all* bound groups of
                               a channel count at once, dropping a set at
                               bound b if a kept set with bound >= b
                               subsumes it, regardless of which group it
                               came from -- a strictly stronger prune. Both
                               modes produce a `.pbin` file in exactly the
                               same format, and this tool's byte-membership
                               test for "subsumed_away" is correct either
                               way (it only ever asks "is this exact packed
                               record present in the matching .pbin"). What
                               it CANNOT do is tell you, from the files
                               alone, which prune mode produced a given
                               dump -- that determines whether
                               "subsumed_away" means "dominated within its
                               own bound group" or "dominated by any
                               equal-or-stronger group", and it is not
                               recorded anywhere in the dump directory
                               itself. Record it out of band (see the
                               per-dataset README this tool's datasets ship
                               with) rather than assuming one or the other.
  * `proof.bin`                the certificate: a DAG of "steps", each step
                               being a (channels, bound, packed bitmap) plus
                               a justification (Huffman or Successors) that
                               references earlier steps as witnesses
                               (proof.rs `GenProof`). Only pruned
                               (.pbin-surviving) sets that are *reachable
                               from the root* by this specific witness DFS
                               (`encode_proof`, proof.rs:141-183) get an
                               actual step id written to the file; the rest
                               of the pruned population never appears here
                               even though it is equally valid. Supports
                               both the legacy v1 container (bare u32 step
                               count) and the v2 "SNOCERT2" wide container
                               (docs/certificate-format-v2.md); this tool
                               reads both, using only the fixed-size
                               [channels u8][bound u8][packed bitmap] step
                               header (it does not need to parse witnesses).

Because every .pbin record's bytes are copied verbatim from its .bin record
(prune.rs: `output_file.write_all(packed)`), and every proof step's packed
bitmap is copied verbatim from the pruned index it was read out of
(proof.rs `GenProof::new`/`encode_proof`), membership across the three
artifacts can be tested by exact byte equality of the packed record within
the same channel count. No re-parsing of comparators, canonical forms, or
subsumption logic is needed or performed by this tool.

-----------------------------------------------------------------------------
LABEL SEMANTICS -- read this before using the dataset for anything
-----------------------------------------------------------------------------

Every row is a state (canonical output set) taken from some `group_{c}_{b}.bin`
file (the EXPLORED population -- this is the complete row set; .pbin and
proof.bin are only used to assign labels, never to add rows). Each row gets
exactly one of three labels:

  * "certificate_step"   The row's exact packed bitmap is decoded from a
                          step payload in proof.bin at the same channel
                          count. This is the closest available proxy for
                          "this state's bound was actually used to justify
                          the final claimed lower bound", i.e. NEEDED.

  * "pruned_survivor"    The row's bitmap is present in the matching .pbin
                          (so it is NOT redundant under subsumption -- it is
                          a genuine, non-dominated, correctly-bounded state)
                          but it does NOT appear anywhere in proof.bin. It
                          was explored, survived pruning, and then simply
                          was never visited by the one witness-DFS that
                          happened to build this particular certificate.
                          This is the internals doc's "reachable-from-root"
                          gap (~1.1-1.2x on these dumps; ~1.22x at n=11 per
                          the published figures in docs/sortnetopt-internals.md
                          section 8.0).

  * "subsumed_away"      The row's bitmap is present in .bin but ABSENT from
                          the matching .pbin: some other state at the same
                          (channels, bound) subsumes it (dominates it under
                          permutation/complement), so prune.rs discarded it
                          as redundant. This is genuinely, measurably wasted
                          search effort in the narrow sense of "this
                          particular canonical form added nothing beyond
                          what another stored form already gave you" -- it
                          is NOT necessarily "this state was a bad choice by
                          the search"; the search has no subsumption
                          awareness at all (internals doc section 3.1) and
                          visits it for reasons unrelated to redundancy.

By construction .bin superset .pbin superset {certificate_step rows}, so
the three labels partition the .bin population exactly (every row gets
exactly one label; there is no residual "unknown" category).

HONESTY CAVEATS -- what the dumps do NOT let us determine (do not treat the
above three-way split as more than it is):

 (a) There is no record of pure *waste* in the sense of "created, computed
     on, and discarded before the search finished". `dump_states` runs once,
     after the DP fixpoint closes (bounds[0] == bounds[1]), so every row here
     is a *terminal* state. The search's `Edges` frames, the per-set async
     locks, the number of times each state was revisited, and its full
     upper/huffman-bound history are never written to disk at all
     (internals doc section 3.2, 4) -- this dataset cannot see any of that,
     and this tool does not fabricate it. "subsumed_away" is waste in the
     *offline pruning* sense only, not in the *online search* sense.

 (b) `subsumed_away` records who lost, not who won: prune.rs's in-memory
     OutputSetIndex records which permutation of which surviving record
     subsumed a discarded one, but that pairing is never written to disk --
     only the surviving antichain (.pbin) is. This tool cannot and does not
     attribute a subsumed-away state to its specific subsumer.

 (c) `certificate_step` is a proxy for "used by the one certificate that was
     built", not a proof of logical necessity or of being the *unique*
     minimal justification. `GenProof::prove_all` (proof.rs:112-136) tries
     justifications in a fixed priority order (trivial, then Huffman, then
     Successors) and keeps the first one that validates -- a state can have
     several valid justifications and only one is ever recorded. Separately,
     `encode_proof`'s DFS from the root only walks the witnesses that
     specific justification happens to reference; a `pruned_survivor` state
     may be an equally valid (or logically interchangeable) witness that
     simply was not reached. The evidence/v3/limits/report.md control
     finding notes proof.bin is NOT byte-reproducible across runs of the
     same binary on the same input (nondeterministic search order feeding a
     deterministic-but-order-sensitive justification search) -- so which
     pruned_survivor rows would instead be certificate_step rows is itself
     somewhat arbitrary among equally-valid alternatives. Read
     "certificate_step" as "used by THIS certificate", not "essential to
     every valid certificate of this bound".

 (d) This tool does not run or link against the Rust crate, the checker, or
     any subsumption/canonicalization code; it only reads already-produced
     files byte-for-byte. It cannot detect an internal inconsistency in the
     dump itself (e.g. a .pbin record that was never in the corresponding
     .bin, which would indicate a corrupted or mismatched dump) beyond a
     best-effort sanity check reported in the run summary.

-----------------------------------------------------------------------------
OUTPUT SCHEMA
-----------------------------------------------------------------------------

One .npz file per dump, with these arrays (row i is one state):

  width        uint8   [n]        channel count c of this state (called
                                   "channels" elsewhere in sortnetopt; the
                                   two names denote the same quantity)
  bound        uint8   [n]        the lower bound recorded for this state
                                   (from its group_{c}_{b} filename)
  label        uint8   [n]        0 = subsumed_away, 1 = pruned_survivor,
                                   2 = certificate_step (see LABEL_NAMES)
  size         uint16  [n]        |A| = popcount of the packed bitmap
                                   (number of Boolean vectors in the set)
  packed       uint8   [n, PW]    packed bitmap, PW = packed_len(max
                                   channel count present in this dump),
                                   right-zero-padded beyond packed_len(c)
                                   bytes for rows with c < max channels
  weight_hist  uint16  [n, HW]    popcount-by-Hamming-weight histogram of
                                   the *included* vectors: entry w = count
                                   of vectors i in A with popcount(i) == w,
                                   for w in 0..=max_channels (right-padded
                                   with structurally-true zeros for w > c)
  chan_marg    int16   [n, CW]    per-channel marginal: entry j = count of
                                   vectors i in A with bit j of i set, for
                                   j in 0..max_channels; entries with
                                   j >= c (channel does not exist for this
                                   row) are set to -1, distinguishing
                                   "channel absent" from "channel present
                                   with zero count"

Plus a sidecar `<out>.manifest.json` recording provenance: dump directory,
per-file sha256, binary path + sha256 if discoverable, per-group and
per-label row counts, and the proof.bin container version detected.

LABEL_NAMES = {0: "subsumed_away", 1: "pruned_survivor", 2: "certificate_step"}
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
from collections import Counter, defaultdict

import numpy as np

LABEL_SUBSUMED = 0
LABEL_SURVIVOR = 1
LABEL_CERTIFICATE = 2
LABEL_NAMES = {
    LABEL_SUBSUMED: "subsumed_away",
    LABEL_SURVIVOR: "pruned_survivor",
    LABEL_CERTIFICATE: "certificate_step",
}

GROUP_RE = re.compile(r"^group_(\d+)_(\d+)\.bin$")


def packed_len(channels: int) -> int:
    """Matches OutputSet::packed_len_for_channels: (2**c + 7) // 8."""
    return (2 ** channels + 7) // 8


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------
# index.txt / group discovery
# --------------------------------------------------------------------------

def read_index_groups(dump_dir: str):
    """Return sorted list of (channels, bound, basename_no_ext) from index.txt,
    replicating prune::prune_all's own parse (split on '_', then on '.')."""
    index_path = os.path.join(dump_dir, "index.txt")
    groups = []
    with open(index_path, "r") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            m = GROUP_RE.match(line)
            if not m:
                raise ValueError(f"index.txt line does not match group_C_B.bin: {line!r}")
            channels = int(m.group(1))
            bound = int(m.group(2))
            groups.append((channels, bound, line[: -len(".bin")]))
    groups.sort()
    return groups


# --------------------------------------------------------------------------
# proof.bin (v1 legacy + v2 SNOCERT2) -- header-only parse
# --------------------------------------------------------------------------

MAGIC_V2 = b"SNOCERT2"


def read_proof_states(proof_path: str):
    """Return (dict[(channels, packed_bytes) -> bound], format_version_str)."""
    with open(proof_path, "rb") as fh:
        data = fh.read()

    if data[:8] == MAGIC_V2:
        fmt = "v2"
        (format_version, flags) = struct.unpack_from("<II", data, 8)
        if flags != 0:
            raise ValueError(f"proof.bin v2 flags field is nonzero: {flags}")
        (step_count, table_offset, payload_offset, payload_bytes) = struct.unpack_from(
            "<QQQQ", data, 16
        )
        if table_offset != 64:
            raise ValueError("proof.bin v2 table_offset != 64")
        table_entry = "<QQ"  # (offset u64, length u64)
        table_entry_size = 16
    else:
        fmt = "v1"
        (step_count,) = struct.unpack_from("<I", data, 0)
        table_offset = 4
        table_entry = "<QI"  # (offset u64, length u32)
        table_entry_size = 12

    states = {}
    for i in range(step_count):
        off, _length = struct.unpack_from(table_entry, data, table_offset + table_entry_size * i)
        channels = data[off]
        bound = data[off + 1]
        plen = packed_len(channels)
        packed = bytes(data[off + 2 : off + 2 + plen])
        states[(channels, packed)] = bound

    return states, fmt, step_count


# --------------------------------------------------------------------------
# per-group extraction (vectorized)
# --------------------------------------------------------------------------

_WEIGHT_CACHE = {}
_BITS_CACHE = {}


def _weight_onehot(channels: int) -> np.ndarray:
    """Shape (2**channels, channels+1) one-hot of popcount(i) for i in 0..2**c."""
    if channels not in _WEIGHT_CACHE:
        idx = np.arange(2 ** channels, dtype=np.uint32)
        w = np.array([bin(x).count("1") for x in idx], dtype=np.uint16)
        onehot = np.zeros((2 ** channels, channels + 1), dtype=np.uint16)
        onehot[np.arange(2 ** channels), w] = 1
        _WEIGHT_CACHE[channels] = onehot
    return _WEIGHT_CACHE[channels]


def _bit_matrix(channels: int) -> np.ndarray:
    """Shape (2**channels, channels): entry [i, j] = bit j of i."""
    if channels not in _BITS_CACHE:
        idx = np.arange(2 ** channels, dtype=np.uint32)
        bits = ((idx[:, None] >> np.arange(channels)) & 1).astype(np.uint16)
        _BITS_CACHE[channels] = bits
    return _BITS_CACHE[channels]


def load_group_matrix(path: str, channels: int) -> np.ndarray:
    stride = packed_len(channels)
    raw = np.fromfile(path, dtype=np.uint8)
    if raw.size % stride != 0:
        raise ValueError(f"{path}: size {raw.size} not a multiple of stride {stride}")
    return raw.reshape(-1, stride)


def extract_group(channels, bound, bin_mat, pbin_mat, proof_states):
    """Return dict of column arrays for all rows of this (channels, bound) group."""
    n = bin_mat.shape[0]
    pbin_set = {row.tobytes() for row in pbin_mat}

    labels = np.empty(n, dtype=np.uint8)
    for i in range(n):
        rb = bin_mat[i].tobytes()
        if rb not in pbin_set:
            labels[i] = LABEL_SUBSUMED
        elif (channels, rb) in proof_states:
            labels[i] = LABEL_CERTIFICATE
        else:
            labels[i] = LABEL_SURVIVOR

    flags = np.unpackbits(bin_mat, axis=1, bitorder="little").astype(np.uint16)
    # flags now has exactly 2**channels columns (packed_len(c)*8 == 2**c for c>=3)
    size = flags.sum(axis=1).astype(np.uint16)

    hist = flags @ _weight_onehot(channels)  # (n, channels+1)
    marg = flags @ _bit_matrix(channels)  # (n, channels)

    return {
        "width": np.full(n, channels, dtype=np.uint8),
        "bound": np.full(n, bound, dtype=np.uint8),
        "label": labels,
        "size": size,
        "packed": bin_mat,
        "weight_hist": hist.astype(np.uint16),
        "chan_marg": marg.astype(np.int16),
    }


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------

def build_dataset(dump_dir: str, verbose=True):
    groups = read_index_groups(dump_dir)
    if not groups:
        raise ValueError(f"no groups found in {dump_dir}/index.txt")

    proof_path = os.path.join(dump_dir, "proof.bin")
    proof_states, proof_fmt, proof_step_count = read_proof_states(proof_path)

    max_channels = max(c for c, _, _ in groups)
    pad_width = packed_len(max_channels)
    hist_width = max_channels + 1
    marg_width = max_channels

    rows_by_col = defaultdict(list)
    per_group_counts = {}
    missing_pbin = []

    for channels, bound, base in groups:
        bin_path = os.path.join(dump_dir, base + ".bin")
        pbin_path = os.path.join(dump_dir, base + ".pbin")
        if not os.path.exists(pbin_path):
            missing_pbin.append(base)
            continue

        bin_mat = load_group_matrix(bin_path, channels)
        pbin_mat = load_group_matrix(pbin_path, channels)

        cols = extract_group(channels, bound, bin_mat, pbin_mat, proof_states)

        # right-pad packed/weight_hist/chan_marg to the dataset-wide widths
        n = cols["width"].shape[0]
        packed_padded = np.zeros((n, pad_width), dtype=np.uint8)
        packed_padded[:, : cols["packed"].shape[1]] = cols["packed"]
        hist_padded = np.zeros((n, hist_width), dtype=np.uint16)
        hist_padded[:, : cols["weight_hist"].shape[1]] = cols["weight_hist"]
        marg_padded = np.full((n, marg_width), -1, dtype=np.int16)
        marg_padded[:, : cols["chan_marg"].shape[1]] = cols["chan_marg"]

        rows_by_col["width"].append(cols["width"])
        rows_by_col["bound"].append(cols["bound"])
        rows_by_col["label"].append(cols["label"])
        rows_by_col["size"].append(cols["size"])
        rows_by_col["packed"].append(packed_padded)
        rows_by_col["weight_hist"].append(hist_padded)
        rows_by_col["chan_marg"].append(marg_padded)

        counts = Counter(cols["label"].tolist())
        per_group_counts[base] = {
            LABEL_NAMES[k]: counts.get(k, 0) for k in LABEL_NAMES
        }

        if verbose:
            print(
                f"  {base}: explored={n} "
                f"subsumed_away={counts.get(LABEL_SUBSUMED,0)} "
                f"pruned_survivor={counts.get(LABEL_SURVIVOR,0)} "
                f"certificate_step={counts.get(LABEL_CERTIFICATE,0)}"
            )

    if missing_pbin:
        raise ValueError(
            f"{dump_dir}: index.txt lists groups with no .pbin (prune-all "
            f"incomplete?): {missing_pbin}"
        )

    out = {
        "width": np.concatenate(rows_by_col["width"]),
        "bound": np.concatenate(rows_by_col["bound"]),
        "label": np.concatenate(rows_by_col["label"]),
        "size": np.concatenate(rows_by_col["size"]),
        "packed": np.concatenate(rows_by_col["packed"], axis=0),
        "weight_hist": np.concatenate(rows_by_col["weight_hist"], axis=0),
        "chan_marg": np.concatenate(rows_by_col["chan_marg"], axis=0),
    }

    manifest = {
        "dump_dir": os.path.abspath(dump_dir),
        "proof_format": proof_fmt,
        "proof_step_count": proof_step_count,
        "max_channels": max_channels,
        "num_rows": int(out["width"].shape[0]),
        "per_group_counts": per_group_counts,
        "label_names": LABEL_NAMES,
        "sha256": {
            "index.txt": sha256_file(os.path.join(dump_dir, "index.txt")),
            "proof.bin": sha256_file(proof_path),
        },
    }

    return out, manifest


def print_stats(out, manifest, dump_label):
    print(f"\n=== {dump_label}: rows per label per width ===")
    width = out["width"]
    label = out["label"]
    widths = sorted(set(width.tolist()))
    header = ["width"] + [LABEL_NAMES[k] for k in sorted(LABEL_NAMES)] + ["total"]
    print("  " + "  ".join(f"{h:>17}" for h in header))
    grand = Counter()
    for w in widths:
        mask = width == w
        row = [str(w)]
        wtot = 0
        for k in sorted(LABEL_NAMES):
            c = int(((label == k) & mask).sum())
            row.append(str(c))
            grand[k] += c
            wtot += c
        row.append(str(wtot))
        print("  " + "  ".join(f"{v:>17}" for v in row))
    total = sum(grand.values())
    trow = ["ALL"] + [str(grand[k]) for k in sorted(LABEL_NAMES)] + [str(total)]
    print("  " + "  ".join(f"{v:>17}" for v in trow))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("dump_dir", help="dump directory (contains index.txt, group_*.bin/.pbin, proof.bin)")
    ap.add_argument("--out", required=True, help="output .npz path")
    ap.add_argument("--label", default=None, help="short label for stats printout (default: basename of --out)")
    ap.add_argument("--quiet-groups", action="store_true", help="suppress per-group progress lines")
    args = ap.parse_args()

    out, manifest = build_dataset(args.dump_dir, verbose=not args.quiet_groups)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    np.savez_compressed(args.out, **out)

    manifest_path = args.out + ".manifest.json"
    with open(manifest_path, "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)

    label = args.label or os.path.basename(args.out)
    print_stats(out, manifest, label)
    print(f"\nwrote {args.out} ({out['width'].shape[0]} rows)")
    print(f"wrote {manifest_path}")


if __name__ == "__main__":
    main()
