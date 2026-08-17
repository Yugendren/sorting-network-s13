#!/usr/bin/env python3
"""Track A evaluator: score constructor programs from the pool.

Zero-one principle: a 13-channel comparator network sorts all inputs iff
it sorts all 2^13 = 8192 binary vectors. Score tuple (lexicographic,
lower is better): (unsorted_vector_count, comparator_count).

Every scored result is appended to ledger/scores.jsonl with the
program's content hash. Programs are pure constructors:

    def build(params: dict) -> list[tuple[int, int]]

They receive a params dict (including an integer "variant" index for
deterministic diversity) and return a comparator list for 13 channels.
No program may read the ledger, the clock, or the network.

Usage:
    python3 track_a/evaluator.py                 # score whole pool
    python3 track_a/evaluator.py pool/gen0_x.py  # score one program
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import time
import traceback

import numpy as np

CHANNELS = 13
N_VECTORS = 1 << CHANNELS  # 8192
TARGET = 45  # public best; candidates below this trigger the audit path
VARIANTS_PER_PROGRAM = 32
MAX_COMPARATORS = 400  # sanity cap; anything longer is a broken program

ROOT = os.path.dirname(os.path.abspath(__file__))
POOL_DIR = os.path.join(ROOT, "pool")
LEDGER_PATH = os.path.join(ROOT, "ledger", "scores.jsonl")

# All 8192 binary vectors as a (8192, 13) uint8 matrix, column 0 = channel 0.
_INPUTS = ((np.arange(N_VECTORS)[:, None] >> np.arange(CHANNELS)) & 1).astype(
    np.uint8
)
_SORTED = np.sort(_INPUTS, axis=1)


def apply_network(network: list[tuple[int, int]]) -> np.ndarray:
    """Run the comparator network over all 8192 vectors; return outputs."""
    state = _INPUTS.copy()
    for lo, hi in network:
        a = state[:, lo]
        b = state[:, hi]
        lo_v = np.minimum(a, b)
        hi_v = np.maximum(a, b)
        state[:, lo] = lo_v
        state[:, hi] = hi_v
    return state


def diagnose(outputs: np.ndarray) -> dict:
    """Diagnostics fed back to the mutating LLM."""
    unsorted_mask = (outputs != _SORTED).any(axis=1)
    unsorted_count = int(unsorted_mask.sum())
    # Distinct output values per channel position (1 = fully determined).
    per_channel_distinct = [
        int(len(np.unique(outputs[:, c]))) for c in range(CHANNELS)
    ]
    sample_failures = []
    if unsorted_count:
        idx = np.flatnonzero(unsorted_mask)[:5]
        sample_failures = [
            {
                "input": _INPUTS[i].tolist(),
                "output": outputs[i].tolist(),
            }
            for i in idx
        ]
    return {
        "unsorted_count": unsorted_count,
        "per_channel_distinct": per_channel_distinct,
        "sample_failures": sample_failures,
    }


def validate_network(network) -> str | None:
    if not isinstance(network, list) or not network:
        return "not a non-empty list"
    if len(network) > MAX_COMPARATORS:
        return f"too long ({len(network)} > {MAX_COMPARATORS})"
    for item in network:
        if (
            not isinstance(item, tuple)
            or len(item) != 2
            or not all(isinstance(x, int) for x in item)
        ):
            return f"bad comparator {item!r}"
        lo, hi = item
        if not (0 <= lo < CHANNELS and 0 <= hi < CHANNELS and lo != hi):
            return f"out-of-range comparator {item!r}"
    return None


def load_program(path: str):
    spec = importlib.util.spec_from_file_location(
        os.path.splitext(os.path.basename(path))[0], path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "build"):
        raise AttributeError("program has no build(params)")
    return mod


def normalize(network) -> list[tuple[int, int]]:
    """Comparators are order-normalized to (min,max): standard networks."""
    return [(min(a, b), max(a, b)) for a, b in network]


def score_program(path: str) -> dict:
    rel = os.path.relpath(path, ROOT)
    with open(path, "rb") as fh:
        content = fh.read()
    prog_hash = hashlib.sha256(content).hexdigest()

    best = None
    variants = []
    error = None
    t0 = time.time()
    try:
        mod = load_program(path)
        for variant in range(VARIANTS_PER_PROGRAM):
            network = mod.build({"variant": variant, "channels": CHANNELS})
            network = normalize(list(network))
            problem = validate_network(network)
            if problem:
                variants.append({"variant": variant, "error": problem})
                continue
            outputs = apply_network(network)
            diag = diagnose(outputs)
            entry = {
                "variant": variant,
                "comparators": len(network),
                "unsorted_count": diag["unsorted_count"],
            }
            variants.append(entry)
            key = (diag["unsorted_count"], len(network))
            if best is None or key < best["key"]:
                best = {
                    "key": key,
                    "variant": variant,
                    "network": network,
                    "diag": diag,
                }
    except Exception:
        error = traceback.format_exc(limit=8)

    elapsed = time.time() - t0
    record = {
        "schema": "track-a-score-v1",
        "program": rel,
        "sha256": prog_hash,
        "wall_seconds": round(elapsed, 3),
        "variants_scored": len(variants),
        "error": error,
        "best": None,
    }
    if best is not None:
        unsorted_count, comparators = best["key"]
        record["best"] = {
            "variant": best["variant"],
            "unsorted_count": unsorted_count,
            "comparators": comparators,
            "valid_sorter": unsorted_count == 0,
            "diagnostics": best["diag"],
        }
        # Candidate worth auditing: a valid sorter at or below the target.
        if unsorted_count == 0 and comparators <= TARGET:
            record["best"]["network"] = best["network"]
            record["best"]["audit_required"] = True
    return record


def append_ledger(records: list[dict]) -> None:
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, separators=(",", ":")) + "\n")


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        paths = [os.path.abspath(p) for p in argv[1:]]
    else:
        paths = sorted(
            os.path.join(POOL_DIR, f)
            for f in os.listdir(POOL_DIR)
            if f.endswith(".py") and not f.startswith("_")
        )
    records = []
    for path in paths:
        rec = score_program(path)
        records.append(rec)
        best = rec["best"]
        if rec["error"]:
            line = f"{rec['program']}: ERROR"
        elif best is None:
            line = f"{rec['program']}: no valid variants"
        else:
            line = (
                f"{rec['program']}: unsorted={best['unsorted_count']} "
                f"comparators={best['comparators']}"
                + (" *** VALID SORTER ***" if best["valid_sorter"] else "")
                + (
                    " *** <=45: AUDIT REQUIRED ***"
                    if best.get("audit_required")
                    else ""
                )
            )
        print(line)
    append_ledger(records)
    print(f"\n{len(records)} program(s) scored; ledger: {LEDGER_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
