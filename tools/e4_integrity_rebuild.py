#!/usr/bin/env python3
"""Rebuild SENSO and Mericanii V2 from frozen inputs for E4 integrity replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

if __package__:
    from tools import setup_senso, setup_senso_mericanii_v2
    from tools.method_runtime import ROOT, sha256, write_json
else:
    import setup_senso
    import setup_senso_mericanii_v2
    from method_runtime import ROOT, sha256, write_json


RUN_ID = re.compile(r"^e4-exam-[0-9]{8}T[0-9]{6}Z$")


def read_active(path: Path) -> tuple[dict, Path]:
    active = json.loads(path.read_text(encoding="utf-8"))
    manifest_path = ROOT / active["manifest_path"]
    if sha256(manifest_path) != active["manifest_sha256"]:
        raise RuntimeError(f"rebuilt manifest pointer mismatch: {path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    binary = ROOT / manifest["binary_path"]
    if manifest.get("status") != "PASS" or sha256(binary) != manifest["binary_sha256"]:
        raise RuntimeError(f"rebuilt binary mismatch: {binary}")
    return manifest, manifest_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if Path.cwd().resolve() != ROOT:
        raise RuntimeError(f"run only from {ROOT}")
    if not RUN_ID.fullmatch(args.run_id):
        raise RuntimeError("invalid E4 run id")

    rebuild_root = ROOT / ".build/e4-integrity" / args.run_id
    if rebuild_root.exists():
        raise RuntimeError(f"integrity rebuild already exists: {rebuild_root}")
    rebuild_root.mkdir(parents=True)

    setup_senso.BUILD_ROOT = rebuild_root / "senso"
    setup_senso.ACTIVE = setup_senso.BUILD_ROOT / "active.json"
    if setup_senso.main() != 0:
        raise RuntimeError("frozen SENSO integrity rebuild failed")

    method_builder = setup_senso_mericanii_v2._BUILDER
    method_builder.BUILD_ROOT = rebuild_root / "mericanii-v2"
    method_builder.ACTIVE = method_builder.BUILD_ROOT / "active.json"
    if method_builder.main() != 0:
        raise RuntimeError("frozen Mericanii V2 integrity rebuild failed")

    senso, senso_manifest_path = read_active(setup_senso.ACTIVE)
    method, method_manifest_path = read_active(method_builder.ACTIVE)
    if senso["archive_sha256"] != setup_senso.ARCHIVE_SHA256:
        raise RuntimeError("SENSO rebuild archive mismatch")
    expected_method = setup_senso_mericanii_v2.expected_hashes()
    for key, expected in expected_method.items():
        if method.get(key) != expected:
            raise RuntimeError(f"Mericanii rebuild input mismatch: {key}")
    fixture = method.get("compiled_inference_check", {})
    if fixture.get("status") != "PASS" or fixture.get("rows") != 32 or fixture.get("max_absolute_error", 1) > fixture.get("tolerance", 0):
        raise RuntimeError("Mericanii rebuild compiled inference replay failed")

    summary = {
        "schema_version": "s13-e4-integrity-rebuild/v1",
        "run_id": args.run_id,
        "status": "PASS",
        "root": rebuild_root.relative_to(ROOT).as_posix(),
        "senso": {
            "manifest_path": senso_manifest_path.relative_to(ROOT).as_posix(),
            "manifest_sha256": sha256(senso_manifest_path),
            "binary_path": senso["binary_path"],
            "binary_sha256": senso["binary_sha256"],
            "source_path": senso["source_path"],
        },
        "mericanii_v2": {
            "manifest_path": method_manifest_path.relative_to(ROOT).as_posix(),
            "manifest_sha256": sha256(method_manifest_path),
            "binary_path": method["binary_path"],
            "binary_sha256": method["binary_sha256"],
            "source_path": method["source_path"],
            "method_patch_sha256": method["method_patch_sha256"],
            "model_header_sha256": method["model_header_sha256"],
        },
    }
    summary_path = rebuild_root / "rebuild-summary.json"
    write_json(summary_path, summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
