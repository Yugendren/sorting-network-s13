#!/usr/bin/env python3
"""Cross-validate snocheck2 (verified core, unverified decoder) against
cert_v2.py (unverified, mirrors Checker.thy) on real prefix certificates and
on semantically corrupted variants of them.

The high-value case is D1: `cert_v2.py` gained a `bound != 0` guard in the
Successors rule to match Checker.thy:566. snocheck2's core IS Checker.thy, so
running the same corrupted file through both is an independent check that the
guard was read correctly -- not a check that two mirrors of the same reading
agree.

Usage: crosscheck.py <snocheck2> <v2p file> [<v2p file> ...]
"""

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, "/Users/yugendren/experiments/sorting_network_s13/tools")
import cert_v2 as C


def run_snocheck2(binary, path):
    p = subprocess.run([binary, "-p", path], capture_output=True, text=True)
    out = (p.stdout or "").strip().splitlines()
    err = [l for l in (p.stderr or "").strip().splitlines()
           if not l.startswith("warning:")]
    line = out[0] if out else (err[0] if err else "<no output>")
    return p.returncode, line


def run_cert_v2(path):
    p = subprocess.run(
        [sys.executable,
         "/Users/yugendren/experiments/sorting_network_s13/tools/cert_v2.py",
         "prefix-check", "--quiet", path],
        capture_output=True, text=True)
    out = (p.stdout or "").strip().splitlines()
    err = (p.stderr or "").strip().splitlines()
    line = out[0] if out else (err[0] if err else "<no output>")
    return p.returncode, line


def bound_of(line):
    for tok in line.split():
        if tok.startswith("bound="):
            return tok.split("=", 1)[1]
    return None


# ---- corruption builders: each returns new bytes or None if inapplicable ----

def corrupt_claimed_bound(data):
    b = bytearray(data)
    old = C.u16(b, 64 + 12)
    b[64 + 12:64 + 14] = ((old + 1) & 0xFFFF).to_bytes(2, "little")
    return C.recompute_v2_digests(bytes(b))


def corrupt_root_witness_oob(data):
    b = bytearray(data)
    step_count = C.u64(b, 16)
    b[64 + 16:64 + 24] = step_count.to_bytes(8, "little")
    return C.recompute_v2_digests(bytes(b))


def corrupt_root_perm(data):
    b = bytearray(data)
    n = C.u16(b, 64 + 8)
    L = C.u16(b, 64 + 10)
    perm_off = 64 + 32 + 2 * L
    if n < 2:
        return None
    b[perm_off + 1] = b[perm_off]
    return C.recompute_v2_digests(bytes(b))


def corrupt_successors_bound_zero(data):
    loc = C.find_successors_step(data)
    if loc is None:
        return None
    _sid, off = loc
    b = bytearray(data)
    b[off] = 0
    return C.recompute_v2_digests(bytes(b))


def corrupt_witness_id(data):
    w = C.find_present_witness(data, min_wchan=0)
    if w is None:
        return None
    b = bytearray(data)
    b[w["abs_id_off"]:w["abs_id_off"] + w["id_size"]] = \
        w["step_id"].to_bytes(w["id_size"], "little")
    return C.recompute_v2_digests(bytes(b))


def corrupt_step_perm(data):
    w = C.find_present_witness(data, min_wchan=2)
    if w is None:
        return None
    b = bytearray(data)
    b[w["abs_perm_off"] + 1] = b[w["abs_perm_off"]]
    return C.recompute_v2_digests(bytes(b))


def corrupt_prefix_comparator(data):
    sec = C.parse_prefix_section(data)
    L = sec["prefix_len"]
    if L == 0:
        return None
    n = sec["channels"]
    old_a, old_b = sec["prefix"][-1]
    stored = sec["root_vects"]
    chosen = None
    for cand in range(n):
        if cand in (old_a, old_b):
            continue
        if C.simulate_prefix(n, sec["prefix"][:-1] + [(cand, old_b)]) != stored:
            chosen = cand
            break
    if chosen is None:
        return None
    b = bytearray(data)
    b[64 + 32 + 2 * (L - 1)] = chosen
    return C.recompute_v2_digests(bytes(b))


# name, builder, both-must-reject?
CASES = [
    ("original (must both ACCEPT, equal bounds)", None, False),
    ("claimed_bound raised by 1", corrupt_claimed_bound, True),
    ("root_witness_step out of bounds", corrupt_root_witness_oob, True),
    ("duplicate root_perm entry", corrupt_root_perm, True),
    ("D1: successors step bound zeroed", corrupt_successors_bound_zero, True),
    ("witness id >= referring step", corrupt_witness_id, True),
    ("duplicate perm entry in a step witness", corrupt_step_perm, True),
    ("last prefix comparator changed", corrupt_prefix_comparator, None),
]


def main():
    binary = sys.argv[1]
    files = sys.argv[2:]
    failures = []
    tmpdir = tempfile.mkdtemp(prefix="crosscheck-")

    for path in files:
        data = open(path, "rb").read()
        print(f"\n=== {path}  ({len(data)} bytes) ===")
        for name, builder, must_reject in CASES:
            if builder is None:
                target = path
            else:
                variant = builder(data)
                if variant is None:
                    print(f"  SKIP  {name}: not applicable to this file")
                    continue
                target = os.path.join(
                    tmpdir, f"{os.path.basename(os.path.dirname(path))}-"
                            f"{abs(hash(name))}.bin")
                with open(target, "wb") as f:
                    f.write(variant)

            rc_c, line_c = run_cert_v2(target)
            rc_s, line_s = run_snocheck2(binary, target)
            acc_c, acc_s = rc_c == 0, rc_s == 0

            verdict = "?"
            if must_reject is True:
                ok = (not acc_c) and (not acc_s)
                verdict = "PASS" if ok else "FAIL"
            elif must_reject is False:
                ok = acc_c and acc_s and bound_of(line_c) == bound_of(line_s)
                verdict = "PASS" if ok else "FAIL"
            else:
                ok = True
                verdict = "INFO" if acc_c == acc_s else "DIVERGE"

            if verdict == "FAIL":
                failures.append((path, name, line_c, line_s))

            print(f"  {verdict:7} {name}")
            print(f"          cert_v2  [{rc_c}] {line_c}")
            print(f"          snocheck2[{rc_s}] {line_s}")

    print("\n" + "=" * 70)
    if failures:
        print(f"{len(failures)} FAILURE(S):")
        for path, name, lc, ls in failures:
            print(f"  {path} :: {name}\n    cert_v2: {lc}\n    snocheck2: {ls}")
        return 1
    print("ALL CROSS-CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
