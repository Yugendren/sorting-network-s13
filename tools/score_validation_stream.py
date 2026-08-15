#!/usr/bin/env python3
"""Decompress one immutable TSV stream into the exact compiled validation scorer."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path("/Users/yugendren/experiments/sorting_network_s13")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--scorer", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--decompress-stderr", type=Path, required=True)
    parser.add_argument("--scorer-stderr", type=Path, required=True)
    args = parser.parse_args()
    if Path.cwd().resolve() != ROOT:
        raise RuntimeError(f"run only from {ROOT}")
    for path in (args.dataset, args.scorer):
        if not path.resolve().is_file():
            raise RuntimeError(f"missing input: {path}")
    if args.output.exists():
        raise RuntimeError("validation score output already exists")

    with args.output.open("wb") as output, args.decompress_stderr.open("wb") as decompress_error, args.scorer_stderr.open("wb") as scorer_error:
        decompressor = subprocess.Popen(
            ["zstd", "-q", "-d", "-c", str(args.dataset.resolve())],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=decompress_error,
        )
        assert decompressor.stdout is not None
        scorer = subprocess.Popen(
            [str(args.scorer.resolve())],
            cwd=ROOT,
            stdin=decompressor.stdout,
            stdout=output,
            stderr=scorer_error,
        )
        decompressor.stdout.close()
        scorer_return = scorer.wait()
        decompressor_return = decompressor.wait()
    if decompressor_return != 0:
        raise RuntimeError(f"zstd decompressor failed with exit {decompressor_return}")
    if scorer_return != 0:
        raise RuntimeError(f"compiled validation scorer failed with exit {scorer_return}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"validation stream failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
