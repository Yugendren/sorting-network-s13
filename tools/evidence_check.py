#!/usr/bin/env python3
"""Verify exact file inventories for all immutable scored-run directories."""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys


ROOT = Path("/Users/yugendren/experiments/sorting_network_s13")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_run(run_dir: Path) -> list[str]:
    inventory = run_dir / "checksums.sha256"
    errors: list[str] = []
    expected: dict[str, str] = {}
    for number, line in enumerate(inventory.read_text(encoding="utf-8").splitlines(), 1):
        if not line or "  " not in line:
            errors.append(f"{inventory}:{number}: malformed inventory line")
            continue
        digest, relative = line.split("  ", 1)
        if relative in expected:
            errors.append(f"{inventory}:{number}: duplicate path {relative}")
        expected[relative] = digest

    actual_paths = {
        path.relative_to(run_dir).as_posix()
        for path in run_dir.rglob("*")
        if path.is_file() and path.name != "checksums.sha256"
    }
    if set(expected) != actual_paths:
        errors.append(
            f"{run_dir}: inventory mismatch missing={sorted(set(expected)-actual_paths)} "
            f"unexpected={sorted(actual_paths-set(expected))}"
        )
    for relative, digest in expected.items():
        path = run_dir / relative
        if path.is_file() and sha256(path) != digest:
            errors.append(f"{run_dir}: checksum mismatch {relative}")
    return errors


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        print(f"run only from {ROOT}", file=sys.stderr)
        return 2
    inventories = sorted((ROOT / "evidence").glob("b[0-4]/*/checksums.sha256"))
    if not inventories:
        print("no scored evidence inventories found", file=sys.stderr)
        return 2
    errors: list[str] = []
    for inventory in inventories:
        errors.extend(verify_run(inventory.parent))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"verified {len(inventories)} immutable evidence inventories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
