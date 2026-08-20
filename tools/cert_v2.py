#!/usr/bin/env python3
"""cert_v2.py -- standalone tool for the sorting-network certificate v2 wide
container and v2p prefix-rooted container (docs/certificate-format-v2.md).

Stdlib only. Subcommands: info, transcode, untranscode, check, prefix-check,
selftest.

This mirrors the checking semantics of the frozen unverified reference
checker (checker/snocheck/src/{Check,VectSet,Decode,ProofStep}.hs) for the
legacy (v1) container and the v2 wide container, and implements
docs/certificate-format-v2.md sec.9 for the v2p prefix-rooted container.
checker/ is read-only input to this tool and is never modified by it.
"""

import sys
import os
import re
import hashlib
import argparse
from collections import deque, namedtuple

MAGIC_V2 = b"SNOCERT2"
END_MAGIC_V2 = b"SNOCEND2"
SECTION_MAGIC_V2P = b"SNPX"
FNV_OFFSET = 0xCBF29CE484222325
FNV_PRIME = 0x100000001B3
MASK64 = (1 << 64) - 1


class CertError(Exception):
    """A specific, reportable certificate-rejection reason."""


# --------------------------------------------------------------------------
# primitives
# --------------------------------------------------------------------------

def fnv1a64(data: bytes) -> int:
    h = FNV_OFFSET
    for b in data:
        h = ((h ^ b) * FNV_PRIME) & MASK64
    return h


def u16(data, off):
    return int.from_bytes(data[off:off + 2], "little")


def u32(data, off):
    return int.from_bytes(data[off:off + 4], "little")


def u64(data, off):
    return int.from_bytes(data[off:off + 8], "little")


def packed_len(channels: int) -> int:
    return 1 << max(0, channels - 3)


def decode_packed_set(packed_bytes: bytes):
    """Decode a packed bitmap into a python set of present vector ints."""
    s = set()
    for byte_idx, byte in enumerate(packed_bytes):
        b = byte
        base = byte_idx * 8
        while b:
            lsb = b & (-b)
            bit_idx = lsb.bit_length() - 1
            s.add(base + bit_idx)
            b ^= lsb
    return s


def encode_packed_set(channels: int, vects) -> bytes:
    n = packed_len(channels)
    buf = bytearray(n)
    for v in vects:
        buf[v // 8] |= 1 << (v % 8)
    return bytes(buf)


# --------------------------------------------------------------------------
# VectSet operations (mirror VectSet.hs, on plain python sets of ints)
# --------------------------------------------------------------------------

def vs_extremal_channels(pol: bool, channels: int, vects):
    flip = (1 << channels) - 1 if pol else 0
    return [i for i in range(channels) if ((1 << i) ^ flip) in vects]


def vs_prune_extremal(pol: bool, a: int, vects):
    """Filter to vectors whose bit a matches the polarity, then delete bit a."""
    mask = 1 << a
    target = 0 if pol else mask
    mask_low = mask - 1
    out = set()
    for v in vects:
        if (v & mask) == target:
            out.add((v & mask_low) | ((v >> 1) & ~mask_low))
    return out


def vs_apply_comp(i: int, j: int, vects):
    """None if redundant, else the successor VectSet's vects."""
    a_mask = 1 << i
    b_mask = 1 << j
    ab = a_mask | b_mask
    have_a = False
    have_b = False
    for v in vects:
        m = v & ab
        if m == a_mask:
            have_a = True
        elif m == b_mask:
            have_b = True
        if have_a and have_b:
            break
    if not (have_a and have_b):
        return None
    out = set()
    for v in vects:
        if (v & ab) == b_mask:
            out.add(v ^ ab)
        else:
            out.add(v)
    return out


def vs_permute(perm, vects):
    out = set()
    for v in vects:
        u = 0
        for i, p in enumerate(perm):
            if (v >> p) & 1:
                u |= 1 << i
        out.add(u)
    return out


def vs_invert(channels: int, vects):
    mask = (1 << channels) - 1
    return {v ^ mask for v in vects}


def huffman_bound(values):
    if not values:
        return 0
    import heapq
    heap = list(values)
    heapq.heapify(heap)
    while len(heap) > 1:
        x = heapq.heappop(heap)
        y = heapq.heappop(heap)
        heapq.heappush(heap, 1 + max(x, y))
    return heap[0]


# --------------------------------------------------------------------------
# step payload structural decode (shared by v1, v2 and v2p; id_size differs)
# --------------------------------------------------------------------------

def parse_step(payload, id_size: int):
    """Structurally decode one step payload.

    Returns a dict with:
      channels, bound, kind ('huffman'/'successors'), pol (bool or None),
      wchan (perm length), witnesses (list of None or (invert, perm_tuple, step_id)),
      vects (python set of ints), id_spans (list of (local_offset, id_size)
      for each present witness, in order), perm_spans (list of
      (local_offset, wchan) for each present witness, in order).
    """
    try:
        n = len(payload)
        if n < 4:
            raise CertError("step payload too short")
        channels = payload[0]
        bound = payload[1]
        plen = packed_len(channels)
        if n < 2 + plen + 1:
            raise CertError("step payload truncated before witness kind byte")
        packed_bytes = payload[2:2 + plen]
        kind_byte = payload[2 + plen]
        if kind_byte == 0:
            kind, pol, wchan = "huffman", False, channels - 1
        elif kind_byte == 1:
            kind, pol, wchan = "huffman", True, channels - 1
        elif kind_byte == 2:
            kind, pol, wchan = "successors", None, channels
        else:
            raise CertError("invalid witness kind byte")

        pos = 2 + plen + 1
        witnesses = []
        id_spans = []
        perm_spans = []
        while pos < n:
            tag = payload[pos]
            if tag == 2:
                witnesses.append(None)
                pos += 1
            elif tag in (0, 1):
                pos += 1
                if pos + wchan + id_size > n:
                    raise CertError("witness entry truncated")
                perm_off = pos
                perm = payload[pos:pos + wchan]
                pos += wchan
                id_off = pos
                step_id = int.from_bytes(payload[pos:pos + id_size], "little")
                pos += id_size
                witnesses.append((tag == 1, tuple(perm), step_id))
                id_spans.append((id_off, id_size))
                perm_spans.append((perm_off, wchan))
            else:
                raise CertError("invalid witness tag byte")

        vects = decode_packed_set(packed_bytes)
        return {
            "channels": channels,
            "bound": bound,
            "kind": kind,
            "pol": pol,
            "wchan": wchan,
            "witnesses": witnesses,
            "vects": vects,
            "id_spans": id_spans,
            "perm_spans": perm_spans,
        }
    except IndexError:
        raise CertError("truncated step payload")


# --------------------------------------------------------------------------
# proof checking (mirrors Check.hs)
# --------------------------------------------------------------------------

def get_bound(steps, witness, target_channels, target_vects):
    if witness is None:
        return 0 if len(target_vects) <= 1 + target_channels else 1
    invert_flag, perm, wid = witness
    wstep = steps(wid)
    wchannels = wstep["channels"]
    wvects = wstep["vects"]
    wbound = wstep["bound"]
    if invert_flag:
        wvects = vs_invert(wchannels, wvects)
    width = target_channels
    if len(perm) != width:
        raise CertError("witness perm length does not match target width")
    if wchannels != width:
        raise CertError("witness step width does not match target width")
    if sorted(perm) != list(range(width)):
        raise CertError("witness perm is not a permutation")
    permuted = vs_permute(perm, wvects)
    if not permuted.issubset(target_vects):
        raise CertError("witness does not subsume target")
    return wbound


def check_huffman(steps, step):
    channels = step["channels"]
    vects = step["vects"]
    pol = step["pol"]
    extremal = vs_extremal_channels(pol, channels, vects)
    witnesses = step["witnesses"]
    if len(extremal) != len(witnesses):
        raise CertError("wrong number of huffman witnesses")
    bounds = []
    for c, w in zip(extremal, witnesses):
        pruned = vs_prune_extremal(pol, c, vects)
        bounds.append(get_bound(steps, w, channels - 1, pruned))
    if not (huffman_bound(bounds) >= step["bound"]):
        raise CertError("huffman bound too low")


def check_successors(steps, step):
    channels = step["channels"]
    vects = step["vects"]
    if not (len(vects) > 1 + channels):
        raise CertError("set might already be sorted")
    successors = []
    for i in range(channels):
        for j in range(i):
            r = vs_apply_comp(i, j, vects)
            if r is not None:
                successors.append(r)
    witnesses = step["witnesses"]
    if len(successors) != len(witnesses):
        raise CertError("wrong number of successor witnesses")
    for succ_vects, w in zip(successors, witnesses):
        b = get_bound(steps, w, channels, succ_vects)
        if not (b + 1 >= step["bound"]):
            raise CertError("successor bound too low")


def make_get_step(get_payload, id_size, maxsize=200_000):
    cache = {}
    order = deque()

    def get_step(i):
        v = cache.get(i)
        if v is not None:
            return v
        payload = get_payload(i)
        parsed = parse_step(payload, id_size)
        cache[i] = parsed
        order.append(i)
        if len(order) > maxsize:
            old = order.popleft()
            cache.pop(old, None)
        return parsed

    return get_step


def check_proof(step_count, get_step, progress=True):
    for step_id in range(step_count):
        if progress and step_id and step_id % 100_000 == 0:
            print(f"... {step_id}/{step_count} steps checked", file=sys.stderr)
        try:
            step = get_step(step_id)

            def steps_prime(i, _sid=step_id):
                if not (i < _sid):
                    raise CertError("witness step id out of bounds")
                if not (0 <= i < step_count):
                    raise CertError("step id out of bounds")
                return get_step(i)

            if step["kind"] == "huffman":
                check_huffman(steps_prime, step)
            else:
                check_successors(steps_prime, step)
        except CertError as e:
            raise CertError(f"step {step_id}: {e}")
    last = get_step(step_count - 1)
    return last["channels"], last["bound"]


_PROOF_ERR_RE = re.compile(r"^step \d+: ")


def is_proof_check_error(msg: str) -> bool:
    return bool(_PROOF_ERR_RE.match(msg))


# --------------------------------------------------------------------------
# containers (v1, v2, v2p)
# --------------------------------------------------------------------------

def detect_version(data: bytes) -> int:
    """Legacy detector, kept for backwards compatibility: v2 and v2p files
    both start with the SNOCERT2 magic, so this returns 2 for both. Use
    detect_container() to distinguish v2 from v2p."""
    if len(data) >= 8 and data[0:8] == MAGIC_V2:
        return 2
    return 1


def detect_container(data: bytes) -> str:
    """Return "v1", "v2" or "v2p". Distinguishes v2 from v2p by reading
    format_version at offset 8 (docs/certificate-format-v2.md sec.9.2)."""
    if len(data) < 8 or data[0:8] != MAGIC_V2:
        return "v1"
    if len(data) < 12:
        raise CertError("file too short for v2 header")
    format_version = u32(data, 8)
    if format_version == 2:
        return "v2"
    if format_version == 3:
        return "v2p"
    raise CertError("unsupported format_version")


def parse_v1_container(data: bytes):
    if len(data) < 4:
        raise CertError("file too short for v1 step count")
    step_count = u32(data, 0)
    if step_count < 1:
        raise CertError("step_count must be at least 1")
    table_bytes_needed = 4 + 12 * step_count
    if table_bytes_needed > len(data):
        raise CertError("v1 step table extends past end of file")

    def get_payload(i):
        if not (0 <= i < step_count):
            raise CertError("step id out of bounds")
        entry_off = 4 + 12 * i
        off = u64(data, entry_off)
        length = u32(data, entry_off + 8)
        if off + length > len(data):
            raise CertError(f"step {i}: payload extends past end of file")
        return data[off:off + length]

    return step_count, get_payload, 4


# parse_prefix_section / parse_v2_container return type: a small struct that
# carries everything a v2 or v2p caller needs. `prefix` is None for v2 and
# the dict returned by parse_prefix_section() for v2p.
V2Container = namedtuple("V2Container", [
    "container",       # "v2" or "v2p"
    "step_count",
    "get_payload",
    "id_size",
    "root_channels",
    "root_bound",
    "table_offset",
    "payload_offset",
    "payload_bytes",
    "prefix",
])


def parse_prefix_section(data: bytes) -> dict:
    """Parse and validate the v2p prefix-root section at offset 64
    (docs/certificate-format-v2.md sec.9.3), implementing checks P1 and P2
    of sec.9.4. Returns a dict; see module docstring / cert_v2 task notes
    for the exact key set."""
    n_total = len(data)
    base = 64
    if n_total < base + 32:
        raise CertError("file too short for prefix section header")

    if data[base:base + 4] != SECTION_MAGIC_V2P:
        raise CertError("bad prefix section magic")
    section_version = u32(data, base + 4)
    if section_version != 1:
        raise CertError("unsupported prefix section_version")

    channels = u16(data, base + 8)
    if not (1 <= channels <= 255):
        raise CertError("prefix section channels out of range")
    prefix_len = u16(data, base + 10)
    claimed_bound = u16(data, base + 12)
    root_invert_byte = data[base + 14]
    if root_invert_byte not in (0, 1):
        raise CertError("root_invert must be 0 or 1")
    root_invert = bool(root_invert_byte)
    root_perm_len = data[base + 15]
    if root_perm_len != channels:
        raise CertError("root_perm_len does not match channels")
    root_witness_step = u64(data, base + 16)
    root_packed_len_field = u32(data, base + 24)
    expected_packed_len = packed_len(channels)
    if root_packed_len_field != expected_packed_len:
        raise CertError("root_packed_len does not match packed_len(channels)")
    reserved = u32(data, base + 28)
    if reserved != 0:
        raise CertError("prefix section reserved field must be zero")

    prefix_off = base + 32
    perm_off = prefix_off + 2 * prefix_len
    packed_off = perm_off + channels
    sha_off = packed_off + expected_packed_len
    prefix_bytes = (sha_off + 32) - base  # == 64 + 2*L + n + packed_len(n)

    if sha_off + 32 > n_total:
        raise CertError("prefix section extends past end of file")

    header_table_offset = u64(data, 24)
    if header_table_offset != base + prefix_bytes:
        raise CertError("table_offset inconsistent with prefix_bytes")

    prefix = []
    for k in range(prefix_len):
        a = data[prefix_off + 2 * k]
        b = data[prefix_off + 2 * k + 1]
        if not (a < channels and b < channels and a != b):
            raise CertError(f"prefix comparator {k}: channel out of range or a == b")
        prefix.append((a, b))

    root_perm = tuple(data[perm_off:perm_off + channels])
    if sorted(root_perm) != list(range(channels)):
        raise CertError("root_perm is not a permutation")

    root_packed = bytes(data[packed_off:packed_off + expected_packed_len])
    root_vects = decode_packed_set(root_packed)

    section_sha256 = bytes(data[sha_off:sha_off + 32])
    computed = hashlib.sha256(data[base:sha_off]).digest()
    if section_sha256 != computed:
        raise CertError("prefix section sha256 mismatch")

    return {
        "channels": channels,
        "prefix_len": prefix_len,
        "claimed_bound": claimed_bound,
        "root_invert": root_invert,
        "root_perm": root_perm,
        "root_witness_step": root_witness_step,
        "root_packed": root_packed,
        "root_vects": root_vects,
        "prefix": prefix,
        "prefix_bytes": prefix_bytes,
        "section_sha256": section_sha256,
    }


def simulate_prefix(channels: int, prefix):
    """P3's simulation: start from the full n-cube and apply each comparator
    (a, b) in order -- applyComp(a, b) of sec.5.4 with no redundancy test."""
    vects = set(range(1 << channels))
    for a, b in prefix:
        a_mask = 1 << a
        b_mask = 1 << b
        ab = a_mask | b_mask
        out = set()
        for v in vects:
            if (v & ab) == b_mask:
                out.add(v ^ ab)
            else:
                out.add(v)
        vects = out
    return vects


def parse_v2_container(data: bytes) -> V2Container:
    n = len(data)
    if n < 64:
        raise CertError("file too short for v2 header")
    if data[0:8] != MAGIC_V2:
        raise CertError("bad v2 magic")
    format_version = u32(data, 8)
    if format_version == 2:
        container = "v2"
        expected_flags = 0
    elif format_version == 3:
        container = "v2p"
        expected_flags = 1
    else:
        raise CertError("unsupported format_version")
    flags = u32(data, 12)
    if flags != expected_flags:
        raise CertError(f"flags must be {expected_flags} for {container}")
    step_count = u64(data, 16)
    if step_count < 1:
        raise CertError("step_count must be at least 1")

    prefix = None
    if container == "v2p":
        prefix = parse_prefix_section(data)
        table_offset = 64 + prefix["prefix_bytes"]
    else:
        table_offset = u64(data, 24)
        if table_offset != 64:
            raise CertError("table_offset must be 64")

    payload_offset = u64(data, 32)
    if payload_offset != table_offset + 16 * step_count:
        raise CertError("payload_offset inconsistent with step_count")
    payload_bytes = u64(data, 40)
    root_channels = u16(data, 48)
    root_bound = u16(data, 50)
    reserved = u32(data, 52)
    if reserved != 0:
        raise CertError("reserved header field must be zero")
    header_hash = u64(data, 56)
    if header_hash != fnv1a64(data[0:56]):
        raise CertError("header hash mismatch")

    expected_total = table_offset + 16 * step_count + payload_bytes + 40
    if n != expected_total:
        raise CertError("unexpected file length")

    table = []
    prev_end = payload_offset
    for i in range(step_count):
        entry_off = table_offset + 16 * i
        off = u64(data, entry_off)
        length = u64(data, entry_off + 8)
        if length < 4:
            raise CertError(f"step table entry {i}: payload length too short")
        if not (payload_offset <= off and off + length <= payload_offset + payload_bytes):
            raise CertError(f"step table entry {i}: out of payload bounds")
        if off != prev_end:
            raise CertError(f"step table entry {i}: not contiguous")
        table.append((off, length))
        prev_end = off + length
    if prev_end != payload_offset + payload_bytes:
        raise CertError("step table does not cover exact payload region")

    trailer_off = payload_offset + payload_bytes
    digest_actual = hashlib.sha256(data[table_offset:trailer_off]).digest()
    digest_stored = data[trailer_off:trailer_off + 32]
    if digest_actual != digest_stored:
        raise CertError("payload sha256 mismatch")
    end_magic = data[trailer_off + 32:trailer_off + 40]
    if end_magic != END_MAGIC_V2:
        raise CertError("end magic mismatch")

    def get_payload(i):
        if not (0 <= i < step_count):
            raise CertError("step id out of bounds")
        off, length = table[i]
        return data[off:off + length]

    return V2Container(
        container=container,
        step_count=step_count,
        get_payload=get_payload,
        id_size=8,
        root_channels=root_channels,
        root_bound=root_bound,
        table_offset=table_offset,
        payload_offset=payload_offset,
        payload_bytes=payload_bytes,
        prefix=prefix,
    )


def load_container(data: bytes):
    """Load a v1 or plain v2 (full-problem) container for do_check(). Raises
    CertError for v2p input -- a prefix claim must never be reported as a
    bare (channels, bound) full-problem result (sec.9.2/9.5)."""
    container = detect_container(data)
    if container == "v1":
        step_count, get_payload, id_size = parse_v1_container(data)
        return "v1", step_count, get_payload, id_size
    if container == "v2p":
        raise CertError(
            "prefix-rooted certificate (v2p): use do_check_prefix / the prefix-check subcommand"
        )
    c = parse_v2_container(data)
    last_payload = c.get_payload(c.step_count - 1)
    last_parsed = parse_step(last_payload, c.id_size)
    if last_parsed["channels"] != c.root_channels or last_parsed["bound"] != c.root_bound:
        raise CertError("root fields do not match decoded last step")
    return "v2", c.step_count, c.get_payload, c.id_size


def load_v2p_container(data: bytes) -> V2Container:
    """Load a v2p container, checking P6 (mirror fields). Raises CertError
    for non-v2p input."""
    container = detect_container(data)
    if container != "v2p":
        raise CertError("not a prefix-rooted (v2p) certificate")
    c = parse_v2_container(data)
    last_payload = c.get_payload(c.step_count - 1)
    last_parsed = parse_step(last_payload, c.id_size)
    if last_parsed["channels"] != c.root_channels or last_parsed["bound"] != c.root_bound:
        raise CertError("root fields do not match decoded last step")
    return c


def do_check(data: bytes, progress=True):
    """v1 / v2 full-problem check. Returns (channels, bound). Raises
    CertError on a v2p input (see load_container)."""
    version, step_count, get_payload, id_size = load_container(data)
    get_step = make_get_step(get_payload, id_size)
    return check_proof(step_count, get_step, progress=progress)


def do_check_prefix(data: bytes, progress=True) -> dict:
    """v2p prefix-rooted check: P1, P2 (parse_prefix_section), P3, P4, P5, P6
    of docs/certificate-format-v2.md sec.9.4. Returns a dict describing the
    prefix claim."""
    c = load_v2p_container(data)  # P1, P2, P6
    prefix = c.prefix
    n = prefix["channels"]

    # P3 -- prefix binding: recomputed X_P must equal the stored root set.
    simulated = simulate_prefix(n, prefix["prefix"])
    if simulated != prefix["root_vects"]:
        raise CertError(
            "stored root output set does not match the set obtained by "
            "applying the prefix to the full cube"
        )

    # P4 -- every proof step passes sec.5.
    get_step = make_get_step(c.get_payload, c.id_size)
    last_channels, last_bound = check_proof(c.step_count, get_step, progress=progress)

    # P5 -- root witness: getBound(Some(root_invert, root_perm, root_witness_step), X_P) >= claimed_bound.
    w = prefix["root_witness_step"]
    if not (w < c.step_count):
        raise CertError("root_witness_step out of bounds")

    def steps_lookup(i):
        if not (0 <= i < c.step_count):
            raise CertError("step id out of bounds")
        return get_step(i)

    witness = (prefix["root_invert"], prefix["root_perm"], w)
    root_witness_bound = get_bound(steps_lookup, witness, n, prefix["root_vects"])
    if root_witness_bound < prefix["claimed_bound"]:
        raise CertError(
            f"root witness bound {root_witness_bound} is below the claimed bound {prefix['claimed_bound']}"
        )

    return {
        "channels": n,
        "prefix": prefix["prefix"],
        "prefix_len": prefix["prefix_len"],
        "claimed_bound": prefix["claimed_bound"],
        "root_witness_step": w,
        "step_count": c.step_count,
        "last_channels": last_channels,
        "last_bound": last_bound,
    }


# --------------------------------------------------------------------------
# transcode / untranscode
# --------------------------------------------------------------------------

def _widen_or_narrow(payload, id_spans, new_size):
    if not id_spans:
        return bytes(payload)
    out = bytearray()
    pos = 0
    for off, size in id_spans:
        out += payload[pos:off]
        val = int.from_bytes(payload[off:off + size], "little")
        out += val.to_bytes(new_size, "little")
        pos = off + size
    out += payload[pos:]
    return bytes(out)


def build_v2_bytes(payloads):
    step_count = len(payloads)
    table_offset = 64
    payload_offset = 64 + 16 * step_count
    payload_blob = bytearray()
    table = bytearray()
    off = payload_offset
    for p in payloads:
        length = len(p)
        table += off.to_bytes(8, "little") + length.to_bytes(8, "little")
        payload_blob += p
        off += length
    payload_bytes = len(payload_blob)

    last = parse_step(payloads[-1], 8)
    root_channels = last["channels"]
    root_bound = last["bound"]

    header = bytearray(56)
    header[0:8] = MAGIC_V2
    header[8:12] = (2).to_bytes(4, "little")
    header[12:16] = (0).to_bytes(4, "little")
    header[16:24] = step_count.to_bytes(8, "little")
    header[24:32] = table_offset.to_bytes(8, "little")
    header[32:40] = payload_offset.to_bytes(8, "little")
    header[40:48] = payload_bytes.to_bytes(8, "little")
    header[48:50] = root_channels.to_bytes(2, "little")
    header[50:52] = root_bound.to_bytes(2, "little")
    header[52:56] = (0).to_bytes(4, "little")
    hh = fnv1a64(bytes(header))
    header += hh.to_bytes(8, "little")
    assert len(header) == 64

    digest = hashlib.sha256(bytes(table) + bytes(payload_blob)).digest()
    trailer = digest + END_MAGIC_V2

    return bytes(header) + bytes(table) + bytes(payload_blob) + trailer


def build_v1_bytes(payloads):
    step_count = len(payloads)
    header_len = 4 + 12 * step_count
    payload_blob = bytearray()
    table = bytearray()
    off = header_len
    for p in payloads:
        length = len(p)
        table += off.to_bytes(8, "little") + length.to_bytes(4, "little")
        payload_blob += p
        off += length
    return step_count.to_bytes(4, "little") + bytes(table) + bytes(payload_blob)


def transcode_bytes(data: bytes) -> bytes:
    container = detect_container(data)
    if container == "v2p":
        raise CertError(
            "v2p prefix-rooted certificates cannot be transcoded: the prefix root has no v1/v2 representation"
        )
    if container == "v2":
        raise CertError("input is already v2")
    step_count, get_payload, id_size = parse_v1_container(data)
    payloads_v2 = []
    for i in range(step_count):
        payload = get_payload(i)
        parsed = parse_step(payload, id_size)
        payloads_v2.append(_widen_or_narrow(payload, parsed["id_spans"], 8))
    return build_v2_bytes(payloads_v2)


def untranscode_bytes(data: bytes) -> bytes:
    container = detect_container(data)
    if container == "v2p":
        raise CertError(
            "v2p prefix-rooted certificates cannot be transcoded: the prefix root has no v1/v2 representation"
        )
    if container != "v2":
        raise CertError("input is not v2")
    c = parse_v2_container(data)
    payloads_v1 = []
    for i in range(c.step_count):
        payload = c.get_payload(i)
        parsed = parse_step(payload, c.id_size)
        for off, size in parsed["id_spans"]:
            val = int.from_bytes(payload[off:off + size], "little")
            if val >= (1 << 32):
                raise CertError(f"step {i}: witness id exceeds 2**32-1, cannot untranscode")
        payloads_v1.append(_widen_or_narrow(payload, parsed["id_spans"], 4))
    return build_v1_bytes(payloads_v1)


def recompute_v2_digests(data: bytes) -> bytes:
    """Recompute the integrity digests in place, leaving step_count / offsets
    / lengths / end_magic / proof content untouched. For v2p input the
    prefix section's section_sha256 is recomputed first (over
    bytes[64 : 64+prefix_bytes-32]), then header_hash, then the trailer
    digest (over bytes[table_offset : trailer_off]). For plain v2 input this
    is unchanged from before: header_hash then the trailer digest."""
    b = bytearray(data)
    format_version = u32(b, 8)
    if format_version == 3:
        channels = u16(b, 64 + 8)
        prefix_len = u16(b, 64 + 10)
        plen = packed_len(channels)
        prefix_bytes = 64 + 2 * prefix_len + channels + plen
        sha_off = 64 + prefix_bytes - 32
        section_digest = hashlib.sha256(bytes(b[64:sha_off])).digest()
        b[sha_off:sha_off + 32] = section_digest
        table_offset = 64 + prefix_bytes
    else:
        table_offset = u64(b, 24)
    payload_offset = u64(b, 32)
    payload_bytes = u64(b, 40)
    hh = fnv1a64(bytes(b[0:56]))
    b[56:64] = hh.to_bytes(8, "little")
    trailer_off = payload_offset + payload_bytes
    digest = hashlib.sha256(bytes(b[table_offset:trailer_off])).digest()
    b[trailer_off:trailer_off + 32] = digest
    return bytes(b)


def flip_byte(data: bytes, offset: int) -> bytes:
    b = bytearray(data)
    b[offset] ^= 0xFF
    return bytes(b)


def table_entry(data: bytes, i: int, table_offset: int = 64):
    entry_off = table_offset + 16 * i
    return u64(data, entry_off), u64(data, entry_off + 8)


def find_present_witness(data: bytes, min_wchan=0):
    """Scan a v2/v2p file for the first present witness with perm length
    >= min_wchan. Returns a dict of absolute file offsets, or None."""
    c = parse_v2_container(data)
    for i in range(c.step_count):
        off, length = table_entry(data, i, c.table_offset)
        payload = data[off:off + length]
        parsed = parse_step(payload, c.id_size)
        if parsed["wchan"] >= min_wchan and parsed["id_spans"]:
            local_id_off, id_sz = parsed["id_spans"][0]
            local_perm_off, plen = parsed["perm_spans"][0]
            return {
                "step_id": i,
                "abs_id_off": off + local_id_off,
                "id_size": id_sz,
                "abs_perm_off": off + local_perm_off,
                "perm_len": plen,
            }
    return None


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def read_file(path):
    with open(path, "rb") as f:
        return f.read()


def write_file(path, data):
    with open(path, "wb") as f:
        f.write(data)


def die(msg):
    print(f"REJECT: {msg}", file=sys.stderr)
    sys.exit(1)


def format_prefix_string(prefix) -> str:
    if not prefix:
        return "<empty>"
    return ",".join(f"{a}-{b}" for a, b in prefix)


def parse_prefix_expr(s: str):
    """Parse the engine's 'a-b,c-d' prefix syntax (same as canon-key
    --prefix / class_campaign.py's engine_prefix_string). Empty string ->
    empty prefix."""
    s = s.strip()
    if s == "":
        return []
    out = []
    for tok in s.split(","):
        tok = tok.strip()
        m = re.match(r"^(\d+)-(\d+)$", tok)
        if not m:
            raise CertError(f"invalid prefix token: {tok!r}")
        out.append((int(m.group(1)), int(m.group(2))))
    return out


def format_prefix_ok_line(result: dict) -> str:
    return (
        f"OK prefix n={result['channels']} L={result['prefix_len']} "
        f"prefix={format_prefix_string(result['prefix'])} bound={result['claimed_bound']} "
        f"root_witness={result['root_witness_step']} steps={result['step_count']}"
    )


def check_prefix_expectations(result: dict, expect_channels=None, expect_prefix=None, expect_bound=None):
    """Obligation 2 of sec.9.6: a certificate's (n, P) must equal the job it
    is being checked against. Raises CertError on mismatch."""
    if expect_channels is not None and result["channels"] != expect_channels:
        raise CertError(
            f"channels mismatch: certificate has n={result['channels']}, expected {expect_channels}"
        )
    if expect_prefix is not None:
        expected = parse_prefix_expr(expect_prefix)
        if expected != result["prefix"]:
            raise CertError(
                f"prefix mismatch: certificate has {result['prefix']}, expected {expected}"
            )
    if expect_bound is not None and result["claimed_bound"] != expect_bound:
        raise CertError(
            f"claimed_bound mismatch: certificate has b={result['claimed_bound']}, expected {expect_bound}"
        )


def cmd_info(args):
    data = read_file(args.file)
    try:
        container = detect_container(data)
    except CertError as e:
        die(str(e))
        return
    print(f"container: {container}")
    try:
        if container == "v1":
            step_count, get_payload, id_size = parse_v1_container(data)
            print(f"step_count: {step_count}")
            last = parse_step(get_payload(step_count - 1), id_size)
        else:
            c = parse_v2_container(data)
            print(f"step_count: {c.step_count}")
            print(f"format_version: {u32(data, 8)}")
            print(f"flags: {u32(data, 12)}")
            print(f"table_offset: {c.table_offset}")
            print(f"payload_offset: {c.payload_offset}")
            print(f"payload_bytes: {c.payload_bytes}")
            print(f"root_channels: {c.root_channels}")
            print(f"root_bound: {c.root_bound}")
            print(f"header_hash: {u64(data, 56):#018x}")
            if container == "v2p":
                p = c.prefix
                print(f"prefix_channels: {p['channels']}")
                print(f"prefix_len: {p['prefix_len']}")
                print(f"prefix: {format_prefix_string(p['prefix'])}")
                print(f"claimed_bound: {p['claimed_bound']}")
                print(f"root_invert: {int(p['root_invert'])}")
                print(f"root_perm: {','.join(str(x) for x in p['root_perm'])}")
                print(f"root_witness_step: {p['root_witness_step']}")
                print(f"root_packed_sha256: {hashlib.sha256(p['root_packed']).hexdigest()}")
                print(f"section_sha256: {p['section_sha256'].hex()}")
            last = parse_step(c.get_payload(c.step_count - 1), c.id_size)
        print(f"last step decoded: (channels={last['channels']}, bound={last['bound']})")
    except CertError as e:
        die(str(e))


def cmd_transcode(args):
    data = read_file(args.infile)
    try:
        out = transcode_bytes(data)
    except CertError as e:
        die(str(e))
        return
    write_file(args.outfile, out)


def cmd_untranscode(args):
    data = read_file(args.infile)
    try:
        out = untranscode_bytes(data)
    except CertError as e:
        die(str(e))
        return
    write_file(args.outfile, out)


def cmd_check(args):
    data = read_file(args.file)
    try:
        container = detect_container(data)
        if container == "v2p":
            result = do_check_prefix(data)
            print(format_prefix_ok_line(result))
        else:
            channels, bound = do_check(data)
            print(f"OK ({channels},{bound})")
    except CertError as e:
        print(f"REJECT: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_prefix_check(args):
    data = read_file(args.file)
    try:
        container = detect_container(data)
        if container != "v2p":
            raise CertError("not a prefix-rooted (v2p) certificate")
        result = do_check_prefix(data, progress=not args.quiet)
        check_prefix_expectations(
            result,
            expect_channels=args.expect_channels,
            expect_prefix=args.expect_prefix,
            expect_bound=args.expect_bound,
        )
        print(format_prefix_ok_line(result))
    except CertError as e:
        print(f"REJECT: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_selftest(args):
    data_v1 = read_file(args.v1file)
    if detect_version(data_v1) != 1:
        die("selftest expects a v1 (legacy) certificate")

    results = []  # (name, ok, detail)

    def record(name, ok, detail):
        results.append((name, ok, detail))

    baseline = None
    try:
        c1, b1 = do_check(data_v1, progress=False)
        baseline = (c1, b1)
        record("check(v1 original)", True, f"OK ({c1},{b1})")
    except CertError as e:
        record("check(v1 original)", False, f"REJECT: {e}")

    data_v2 = None
    try:
        data_v2 = transcode_bytes(data_v1)
        record("transcode v1->v2", True, f"{len(data_v2)} bytes")
    except CertError as e:
        record("transcode v1->v2", False, str(e))

    if data_v2 is not None and baseline is not None:
        try:
            c2, b2 = do_check(data_v2, progress=False)
            ok = (c1, b1) == (c2, b2)
            detail = f"OK ({c2},{b2})" if ok else f"OK ({c2},{b2}) != v1 result ({c1},{b1})"
            record("check(v2 transcoded) matches v1", ok, detail)
        except CertError as e:
            record("check(v2 transcoded) matches v1", False, f"REJECT: {e}")

    if data_v2 is not None:
        try:
            back = untranscode_bytes(data_v2)
            ok = back == data_v1
            record("untranscode(transcode(x)) == x", ok, "byte-identical" if ok else "MISMATCH")
        except CertError as e:
            record("untranscode(transcode(x)) == x", False, str(e))

    if data_v2 is not None:
        payload_offset = u64(data_v2, 32)
        corruption_specs = [
            ("corrupt: magic", 0),
            ("corrupt: step_count", 16),
            ("corrupt: header_hash", 56),
            ("corrupt: step table", 64),
            ("corrupt: payload byte", payload_offset),
        ]
        for name, off in corruption_specs:
            corrupted = flip_byte(data_v2, off)
            try:
                c, b = do_check(corrupted, progress=False)
                record(name, False, f"UNEXPECTEDLY ACCEPTED: OK ({c},{b})")
            except CertError as e:
                record(name, True, f"rejected -- {e}")

        truncated = data_v2[:-5]
        try:
            c, b = do_check(truncated, progress=False)
            record("corrupt: truncate trailer", False, f"UNEXPECTEDLY ACCEPTED: OK ({c},{b})")
        except CertError as e:
            record("corrupt: truncate trailer", True, f"rejected -- {e}")

        # semantic negative test (g): witness id >= referring step id
        wloc = find_present_witness(data_v2, min_wchan=0)
        if wloc is not None:
            edited = bytearray(data_v2)
            new_id = wloc["step_id"]
            edited[wloc["abs_id_off"]:wloc["abs_id_off"] + wloc["id_size"]] = new_id.to_bytes(
                wloc["id_size"], "little"
            )
            fixed = recompute_v2_digests(bytes(edited))
            try:
                c, b = do_check(fixed, progress=False)
                record("semantic: witness id >= referring step", False, f"UNEXPECTEDLY ACCEPTED: OK ({c},{b})")
            except CertError as e:
                caught_right = is_proof_check_error(str(e))
                record("semantic: witness id >= referring step", caught_right, f"rejected -- {e}")
        else:
            record("semantic: witness id >= referring step", False, "no present witness found")

        # semantic negative test (h): duplicate a perm entry
        wloc2 = find_present_witness(data_v2, min_wchan=2)
        if wloc2 is not None:
            edited = bytearray(data_v2)
            perm_off = wloc2["abs_perm_off"]
            edited[perm_off + 1] = edited[perm_off]
            fixed = recompute_v2_digests(bytes(edited))
            try:
                c, b = do_check(fixed, progress=False)
                record("semantic: duplicate perm entry", False, f"UNEXPECTEDLY ACCEPTED: OK ({c},{b})")
            except CertError as e:
                caught_right = is_proof_check_error(str(e))
                record("semantic: duplicate perm entry", caught_right, f"rejected -- {e}")
        else:
            record("semantic: duplicate perm entry", False, "no witness with perm length >= 2 found")

        # semantic negative test (i): raise the bound byte of a non-last step by 1
        step_count = u64(data_v2, 16)
        found_i = False
        for cand in range(0, min(step_count - 1, 2000)):
            off, length = table_entry(data_v2, cand)
            edited = bytearray(data_v2)
            edited[off + 1] = (edited[off + 1] + 1) & 0xFF
            fixed = recompute_v2_digests(bytes(edited))
            try:
                do_check(fixed, progress=False)
                continue
            except CertError as e:
                caught_right = is_proof_check_error(str(e))
                record(
                    "semantic: bound raised on non-last step",
                    caught_right,
                    f"step {cand}: rejected -- {e}",
                )
                found_i = True
                break
        if not found_i:
            record("semantic: bound raised on non-last step", False, "no candidate step triggered rejection")

    if args.v2p_file:
        data_v2p = read_file(args.v2p_file)
        if detect_container(data_v2p) != "v2p":
            die("--v2p file is not a v2p (prefix-rooted) certificate")

        try:
            result = do_check_prefix(data_v2p, progress=False)
            record("prefix-check(v2p original)", True, format_prefix_ok_line(result))
        except CertError as e:
            result = None
            record("prefix-check(v2p original)", False, f"REJECT: {e}")

        o = {
            "channels": u16(data_v2p, 64 + 8),
            "prefix_len": u16(data_v2p, 64 + 10),
        }
        plen = packed_len(o["channels"])
        prefix_off = 64 + 32
        perm_off = prefix_off + 2 * o["prefix_len"]
        packed_off = perm_off + o["channels"]
        sha_off = packed_off + plen

        # container negatives (integrity layer; digests NOT recomputed)
        container_negatives = [
            ("v2p corrupt: section_magic", 64),
            ("v2p corrupt: root packed set", packed_off),
            ("v2p corrupt: section_sha256", sha_off),
            ("v2p corrupt: format_version", 8),
            ("v2p corrupt: flags", 12),
        ]
        for name, off in container_negatives:
            corrupted = flip_byte(data_v2p, off)
            try:
                r = do_check_prefix(corrupted, progress=False)
                record(name, False, f"UNEXPECTEDLY ACCEPTED: {format_prefix_ok_line(r)}")
            except CertError as e:
                record(name, True, f"rejected -- {e}")

        truncated_p = data_v2p[:-5]
        try:
            r = do_check_prefix(truncated_p, progress=False)
            record("v2p corrupt: truncate trailer", False, f"UNEXPECTEDLY ACCEPTED: {format_prefix_ok_line(r)}")
        except CertError as e:
            record("v2p corrupt: truncate trailer", True, f"rejected -- {e}")

        # semantic negative (a): raise claimed_bound by 1
        edited = bytearray(data_v2p)
        old_bound = u16(edited, 64 + 12)
        new_bound = (old_bound + 1) & 0xFFFF
        edited[64 + 12:64 + 14] = new_bound.to_bytes(2, "little")
        fixed = recompute_v2_digests(bytes(edited))
        try:
            r = do_check_prefix(fixed, progress=False)
            record("v2p semantic: claimed_bound raised by 1", False, f"UNEXPECTEDLY ACCEPTED: {format_prefix_ok_line(r)}")
        except CertError as e:
            caught_right = "root witness bound" in str(e)
            record("v2p semantic: claimed_bound raised by 1", caught_right, f"rejected -- {e}")

        # semantic negative (b): change last comparator's a channel (skip if L == 0)
        try:
            orig_prefix_section = parse_prefix_section(data_v2p)
        except CertError:
            orig_prefix_section = None
        L = o["prefix_len"]
        if L == 0 or orig_prefix_section is None:
            record("v2p semantic: last comparator channel changed", None, "SKIP (empty prefix, nothing to edit)")
        else:
            n_chan = orig_prefix_section["channels"]
            plist = orig_prefix_section["prefix"]
            old_a, old_b = plist[-1]
            stored_root = orig_prefix_section["root_vects"]
            chosen = None
            for cand in range(n_chan):
                if cand == old_a or cand == old_b:
                    continue
                new_prefix = plist[:-1] + [(cand, old_b)]
                if simulate_prefix(n_chan, new_prefix) != stored_root:
                    chosen = cand
                    break
            if chosen is None:
                record("v2p semantic: last comparator channel changed", False, "no candidate channel changes X_P")
            else:
                last_off = prefix_off + 2 * (L - 1)
                edited = bytearray(data_v2p)
                edited[last_off] = chosen
                fixed = recompute_v2_digests(bytes(edited))
                try:
                    r = do_check_prefix(fixed, progress=False)
                    record(
                        "v2p semantic: last comparator channel changed", False,
                        f"UNEXPECTEDLY ACCEPTED: {format_prefix_ok_line(r)}",
                    )
                except CertError as e:
                    caught_right = "stored root output set does not match" in str(e)
                    record("v2p semantic: last comparator channel changed", caught_right, f"rejected -- {e}")

        # semantic negative (c): duplicate an entry of root_perm
        edited = bytearray(data_v2p)
        edited[perm_off + 1] = edited[perm_off]
        fixed = recompute_v2_digests(bytes(edited))
        try:
            r = do_check_prefix(fixed, progress=False)
            record("v2p semantic: duplicate root_perm entry", False, f"UNEXPECTEDLY ACCEPTED: {format_prefix_ok_line(r)}")
        except CertError as e:
            record("v2p semantic: duplicate root_perm entry", True, f"rejected -- {e}")

        # semantic negative (d): root_witness_step == step_count (out of bounds)
        step_count_p = u64(data_v2p, 16)  # step_count lives at header offset 16, same as v2
        edited = bytearray(data_v2p)
        edited[64 + 16:64 + 24] = step_count_p.to_bytes(8, "little")
        fixed = recompute_v2_digests(bytes(edited))
        try:
            r = do_check_prefix(fixed, progress=False)
            record("v2p semantic: root_witness_step out of bounds", False, f"UNEXPECTEDLY ACCEPTED: {format_prefix_ok_line(r)}")
        except CertError as e:
            caught_right = "root_witness_step out of bounds" in str(e)
            record("v2p semantic: root_witness_step out of bounds", caught_right, f"rejected -- {e}")

        # do_check(v2p) refuses
        try:
            do_check(data_v2p, progress=False)
            record("do_check(v2p) refuses", False, "UNEXPECTEDLY ACCEPTED")
        except CertError as e:
            expected_msg = "prefix-rooted certificate (v2p): use do_check_prefix / the prefix-check subcommand"
            record("do_check(v2p) refuses", str(e) == expected_msg, f"rejected -- {e}")

        # prefix-check with wrong --expect-prefix
        if result is not None:
            n_chan2 = result["channels"]
            actual_prefix = result["prefix"]
            if actual_prefix:
                wrong_pairs = actual_prefix[:-1]
            elif n_chan2 >= 2:
                wrong_pairs = [(0, 1)]
            else:
                wrong_pairs = None
            if wrong_pairs is None:
                record("prefix-check wrong --expect-prefix", None, "SKIP (n < 2, cannot construct a mismatching prefix)")
            else:
                wrong_str = format_prefix_string(wrong_pairs) if wrong_pairs else ""
                try:
                    r2 = do_check_prefix(data_v2p, progress=False)
                    check_prefix_expectations(r2, expect_prefix=wrong_str)
                    record("prefix-check wrong --expect-prefix", False, "UNEXPECTEDLY ACCEPTED")
                except CertError as e:
                    record("prefix-check wrong --expect-prefix", True, f"rejected -- {e}")
        else:
            record("prefix-check wrong --expect-prefix", False, "no baseline prefix-check result to compare against")

    all_pass = True
    width = max(len(name) for name, _ok, _detail in results)
    for name, ok, detail in results:
        if ok is None:
            status = "SKIP"
        else:
            status = "PASS" if ok else "FAIL"
            if not ok:
                all_pass = False
        print(f"{status:4}  {name:<{width}}  {detail}")
    sys.exit(0 if all_pass else 1)


def main():
    parser = argparse.ArgumentParser(prog="cert_v2.py")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_info = sub.add_parser("info")
    p_info.add_argument("file")
    p_info.set_defaults(func=cmd_info)

    p_tc = sub.add_parser("transcode")
    p_tc.add_argument("infile")
    p_tc.add_argument("outfile")
    p_tc.set_defaults(func=cmd_transcode)

    p_utc = sub.add_parser("untranscode")
    p_utc.add_argument("infile")
    p_utc.add_argument("outfile")
    p_utc.set_defaults(func=cmd_untranscode)

    p_check = sub.add_parser("check")
    p_check.add_argument("file")
    p_check.set_defaults(func=cmd_check)

    p_pc = sub.add_parser("prefix-check")
    p_pc.add_argument("file")
    p_pc.add_argument("--expect-channels", type=int, default=None)
    p_pc.add_argument("--expect-prefix", type=str, default=None)
    p_pc.add_argument("--expect-bound", type=int, default=None)
    p_pc.add_argument("--quiet", action="store_true")
    p_pc.set_defaults(func=cmd_prefix_check)

    p_self = sub.add_parser("selftest")
    p_self.add_argument("v1file")
    p_self.add_argument("--v2p", dest="v2p_file", default=None)
    p_self.set_defaults(func=cmd_selftest)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
