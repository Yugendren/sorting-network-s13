#!/usr/bin/env python3
"""Compile the frozen header and check its logits against the export fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path("/Users/yugendren/experiments/sorting_network_s13")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def cpp_float(value: str) -> str:
    if not value.endswith("f"):
        raise RuntimeError(f"fixture value is not a float32 hex literal: {value}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--header", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    args = parser.parse_args()

    if Path.cwd().resolve() != ROOT:
        raise RuntimeError(f"run only from {ROOT}")
    header = args.header.resolve()
    fixture_path = args.fixture.resolve()
    if not header.is_file() or not fixture_path.is_file():
        raise RuntimeError("header or fixture is missing")
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if fixture.get("feature_dimension") != 85 or not fixture.get("rows"):
        raise RuntimeError("fixture schema mismatch")

    work_dir = args.work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=False)
    source = work_dir / "verify.cpp"
    binary = work_dir / "verify"
    rows = fixture["rows"]
    body: list[str] = [
        "#include <cmath>",
        "#include <iomanip>",
        "#include <iostream>",
        f'#include "{header.as_posix()}"',
        "int main() {",
        "  double max_error = 0.0;",
    ]
    for index, row in enumerate(rows):
        features = row.get("raw_feature_hex", [])
        if len(features) != 85:
            raise RuntimeError(f"fixture row {index} feature count mismatch")
        body.append(f"  const float features_{index}[85] = {{")
        for offset in range(0, 85, 8):
            body.append("    " + ", ".join(cpp_float(value) for value in features[offset:offset + 8]) + ",")
        body.extend(
            [
                "  };",
                f"  const float expected_{index} = {cpp_float(row['expected_logit_hex'])};",
                f"  const float actual_{index} = MericaniiModelV1::score(features_{index});",
                f"  const double error_{index} = std::fabs((double)actual_{index} - (double)expected_{index});",
                f"  if (error_{index} > max_error) max_error = error_{index};",
            ]
        )
    body.extend(
        [
            '  std::cout << std::setprecision(17) << "{\\\"rows\\\":' + str(len(rows)) + ',\\\"max_absolute_error\\\":" << max_error << "}\\n";',
            "  return max_error <= 1.0e-4 ? 0 : 1;",
            "}",
        ]
    )
    source.write_text("\n".join(body) + "\n", encoding="utf-8")
    compile_command = ["clang++", "-std=c++11", "-O2", str(source), "-o", str(binary)]
    compiled = subprocess.run(compile_command, cwd=ROOT, text=True, capture_output=True, check=False)
    (work_dir / "compile.stdout.txt").write_text(compiled.stdout, encoding="utf-8")
    (work_dir / "compile.stderr.txt").write_text(compiled.stderr, encoding="utf-8")
    if compiled.returncode != 0:
        raise RuntimeError(f"fixture compilation failed with exit {compiled.returncode}")
    checked = subprocess.run([str(binary)], cwd=ROOT, text=True, capture_output=True, check=False)
    (work_dir / "run.stdout.txt").write_text(checked.stdout, encoding="utf-8")
    (work_dir / "run.stderr.txt").write_text(checked.stderr, encoding="utf-8")
    if checked.returncode != 0:
        raise RuntimeError(f"compiled inference fixture failed with exit {checked.returncode}")
    result = json.loads(checked.stdout)
    result.update(
        {
            "schema_version": "s13-compiled-inference-check/v1",
            "status": "PASS",
            "tolerance": 1.0e-4,
            "header_sha256": sha256(header),
            "fixture_sha256": sha256(fixture_path),
            "source_sha256": sha256(source),
            "binary_sha256": sha256(binary),
            "compile_command": compile_command,
        }
    )
    (work_dir / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"compiled model verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
