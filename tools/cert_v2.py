#!/usr/bin/env python3
"""cert_v2.py -- standalone tool for the sorting-network certificate v2 wide
container (docs/certificate-format-v2.md).

Stdlib only. Subcommands: info, transcode, untranscode, check, selftest.

This mirrors the checking semantics of the frozen unverified reference
checker (checker/snocheck/src/{Check,VectSet,Decode,ProofStep}.hs) for both
the legacy (v1) container and the v2 wide container. checker/ is read-only
input to this tool and is never modified by it.
"""

import sys
import os
import re
import hashlib
import argparse
from collections import deque

MAGIC_V2 = b"SNOCERT2"
END_MAGIC_V2 = b"SNOCEND2"
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
# step payload structural decode (shared by v1 and v2; id_size differs)
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
# containers
# --------------------------------------------------------------------------

def detect_version(data: bytes) -> int:
    if len(data) >= 8 and data[0:8] == MAGIC_V2:
        return 2
    return 1


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


def parse_v2_container(data: bytes):
    n = len(data)
    if n < 64:
        raise CertError("file too short for v2 header")
    if data[0:8] != MAGIC_V2:
        raise CertError("bad v2 magic")
    format_version = u32(data, 8)
    if format_version != 2:
        raise CertError("unsupported format_version")
    flags = u32(data, 12)
    if flags != 0:
        raise CertError("flags must be zero")
    step_count = u64(data, 16)
    if step_count < 1:
        raise CertError("step_count must be at least 1")
    table_offset = u64(data, 24)
    if table_offset != 64:
        raise CertError("table_offset must be 64")
    payload_offset = u64(data, 32)
    if payload_offset != 64 + 16 * step_count:
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

    expected_total = 64 + 16 * step_count + payload_bytes + 40
    if n != expected_total:
        raise CertError("unexpected file length")

    table = []
    prev_end = payload_offset
    for i in range(step_count):
        entry_off = 64 + 16 * i
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

    return step_count, get_payload, 8, root_channels, root_bound


def load_container(data: bytes):
    version = detect_version(data)
    if version == 1:
        step_count, get_payload, id_size = parse_v1_container(data)
        return version, step_count, get_payload, id_size
    step_count, get_payload, id_size, root_channels, root_bound = parse_v2_container(data)
    last_payload = get_payload(step_count - 1)
    last_parsed = parse_step(last_payload, id_size)
    if last_parsed["channels"] != root_channels or last_parsed["bound"] != root_bound:
        raise CertError("root fields do not match decoded last step")
    return version, step_count, get_payload, id_size


def do_check(data: bytes, progress=True):
    version, step_count, get_payload, id_size = load_container(data)
    get_step = make_get_step(get_payload, id_size)
    return check_proof(step_count, get_step, progress=progress)


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
    if detect_version(data) == 2:
        raise CertError("input is already v2")
    step_count, get_payload, id_size = parse_v1_container(data)
    payloads_v2 = []
    for i in range(step_count):
        payload = get_payload(i)
        parsed = parse_step(payload, id_size)
        payloads_v2.append(_widen_or_narrow(payload, parsed["id_spans"], 8))
    return build_v2_bytes(payloads_v2)


def untranscode_bytes(data: bytes) -> bytes:
    if detect_version(data) != 2:
        raise CertError("input is not v2")
    step_count, get_payload, id_size, root_channels, root_bound = parse_v2_container(data)
    payloads_v1 = []
    for i in range(step_count):
        payload = get_payload(i)
        parsed = parse_step(payload, id_size)
        for off, size in parsed["id_spans"]:
            val = int.from_bytes(payload[off:off + size], "little")
            if val >= (1 << 32):
                raise CertError(f"step {i}: witness id exceeds 2**32-1, cannot untranscode")
        payloads_v1.append(_widen_or_narrow(payload, parsed["id_spans"], 4))
    return build_v1_bytes(payloads_v1)


def recompute_v2_digests(data: bytes) -> bytes:
    """Recompute header_hash and trailer sha256 in place; leaves everything
    else (including step_count/offsets/lengths/end_magic) untouched."""
    b = bytearray(data)
    payload_offset = u64(b, 32)
    payload_bytes = u64(b, 40)
    hh = fnv1a64(bytes(b[0:56]))
    b[56:64] = hh.to_bytes(8, "little")
    trailer_off = payload_offset + payload_bytes
    digest = hashlib.sha256(bytes(b[64:trailer_off])).digest()
    b[trailer_off:trailer_off + 32] = digest
    return bytes(b)


def flip_byte(data: bytes, offset: int) -> bytes:
    b = bytearray(data)
    b[offset] ^= 0xFF
    return bytes(b)


def table_entry(data: bytes, i: int):
    entry_off = 64 + 16 * i
    return u64(data, entry_off), u64(data, entry_off + 8)


def find_present_witness(data: bytes, min_wchan=0):
    """Scan a v2 file for the first present witness with perm length
    >= min_wchan. Returns a dict of absolute file offsets, or None."""
    step_count, get_payload, id_size, _rc, _rb = parse_v2_container(data)
    for i in range(step_count):
        off, length = table_entry(data, i)
        payload = data[off:off + length]
        parsed = parse_step(payload, id_size)
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


def cmd_info(args):
    data = read_file(args.file)
    version = detect_version(data)
    print(f"container: v{version}")
    try:
        if version == 1:
            step_count, get_payload, id_size = parse_v1_container(data)
            print(f"step_count: {step_count}")
            last = parse_step(get_payload(step_count - 1), id_size)
        else:
            step_count, get_payload, id_size, root_channels, root_bound = parse_v2_container(data)
            print(f"step_count: {step_count}")
            print(f"format_version: {u32(data, 8)}")
            print(f"flags: {u32(data, 12)}")
            print(f"table_offset: {u64(data, 24)}")
            print(f"payload_offset: {u64(data, 32)}")
            print(f"payload_bytes: {u64(data, 40)}")
            print(f"root_channels: {root_channels}")
            print(f"root_bound: {root_bound}")
            print(f"header_hash: {u64(data, 56):#018x}")
            last = parse_step(get_payload(step_count - 1), id_size)
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
        channels, bound = do_check(data)
        print(f"OK ({channels},{bound})")
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

    all_pass = True
    width = max(len(name) for name, _ok, _detail in results)
    for name, ok, detail in results:
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

    p_self = sub.add_parser("selftest")
    p_self.add_argument("v1file")
    p_self.set_defaults(func=cmd_selftest)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
