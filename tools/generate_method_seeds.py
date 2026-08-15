#!/usr/bin/env python3
"""Reproduce the committed Mericanii experiment seed partitions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path("/Users/yugendren/experiments/sorting_network_s13")
CONFIG = ROOT / "config/experiment-v1"


def derive(domain: str, count: int, excluded: set[int]) -> list[int]:
    result: list[int] = []
    seen = set(excluded)
    for index in range(1, count + 1):
        nonce = 0
        while True:
            payload = f"{domain}|{index}|{nonce}".encode("utf-8")
            candidate = int.from_bytes(hashlib.sha256(payload).digest()[:4], "big") & 0x7FFF_FFFF
            if candidate != 0 and candidate not in seen:
                break
            nonce += 1
        seen.add(candidate)
        result.append(candidate)
    return result


def compact_sha256(values: list[int]) -> str:
    payload = json.dumps(values, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_seeds(name: str) -> list[int]:
    return json.loads((CONFIG / name).read_text(encoding="utf-8"))["seeds"]


def reproduce() -> dict[str, object]:
    development = list(range(1, 21))
    validation = derive(
        "mericanii-s13-method-v1/validation/2026-08-15", 20, set(development)
    )
    e3 = derive(
        "mericanii-s13-method-v1/e3-holdout/2026-08-15",
        60,
        set(development + validation),
    )
    e4 = derive(
        "mericanii-s13-method-v1/e4-holdout/2026-08-15",
        60,
        set(development + validation + e3),
    )
    return {
        "development": development,
        "validation": validation,
        "e3_final_holdout": e3,
        "e4_future_holdout": e4,
        "e4_compact_seed_array_sha256": compact_sha256(e4),
    }


def verify() -> dict[str, object]:
    generated = reproduce()
    expected = {
        "development": load_seeds("seeds-development.json"),
        "validation": load_seeds("seeds-validation.json"),
        "e3_final_holdout": load_seeds("seeds-e3-holdout.json"),
    }
    for name, values in expected.items():
        if generated[name] != values:
            raise RuntimeError(f"seed manifest mismatch: {name}")
    policy = json.loads((CONFIG / "seed-policy.json").read_text(encoding="utf-8"))
    commitment = policy["partitions"][3]["compact_seed_array_sha256_commitment"]
    if generated["e4_compact_seed_array_sha256"] != commitment:
        raise RuntimeError("E4 seed commitment mismatch")
    all_values = [*expected.values(), generated["e4_future_holdout"]]
    flat = [value for values in all_values for value in values]
    if len(flat) != len(set(flat)) or any(value <= 0 for value in flat):
        raise RuntimeError("seed partitions are not disjoint positive integers")
    return {
        "status": "PASS",
        "partition_counts": {name: len(values) for name, values in zip(
            ("development", "validation", "e3_final_holdout", "e4_future_holdout"),
            all_values,
        )},
        "e4_compact_seed_array_sha256": commitment,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if Path.cwd().resolve() != ROOT:
        parser.error(f"run only from {ROOT}")
    result = verify() if args.verify else reproduce()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
