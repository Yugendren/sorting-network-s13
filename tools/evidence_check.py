#!/usr/bin/env python3
"""Verify inventories and manifests for every immutable scored-run directory."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any


ROOT = Path("/Users/yugendren/experiments/sorting_network_s13")
BASELINE_GATES = tuple(f"b{number}" for number in range(5))
METHOD_GATES = tuple(f"e{number}" for number in range(6))
GATES = BASELINE_GATES + METHOD_GATES
STATUSES = {"PASS", "FAIL", "TIMEOUT", "CRASH", "INVALID", "BLOCKED"}
REQUIRED_MANIFEST_KEYS = {
    "schema_version",
    "run_id",
    "gate",
    "source_commit",
    "dirty_at_start",
    "command",
    "started_at",
    "ended_at",
    "wall_seconds",
    "cpu_seconds",
    "peak_rss_bytes",
    "threads",
    "host",
    "config_sha256",
    "status",
}
ALLOWED_MANIFEST_KEYS = REQUIRED_MANIFEST_KEYS | {"error"}
REQUIRED_RUN_FILES = {"manifest.json", "command.txt", "stdout.txt", "stderr.txt"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_manifest(run_dir: Path) -> list[str]:
    path = run_dir / "manifest.json"
    if not path.is_file():
        return [f"{run_dir}: missing manifest.json"]
    try:
        manifest: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: invalid JSON: {exc}"]
    if not isinstance(manifest, dict):
        return [f"{path}: manifest must be an object"]

    errors: list[str] = []
    keys = set(manifest)
    missing = REQUIRED_MANIFEST_KEYS - keys
    extra = keys - ALLOWED_MANIFEST_KEYS
    if missing:
        errors.append(f"{path}: missing manifest fields {sorted(missing)}")
    if extra:
        errors.append(f"{path}: unexpected manifest fields {sorted(extra)}")
    if missing:
        return errors

    expected_schema = (
        "s13-method-evidence-manifest/v1"
        if run_dir.parent.name.startswith("e")
        else "s13-evidence-manifest/v1"
    )
    if manifest["schema_version"] != expected_schema:
        errors.append(f"{path}: wrong schema_version")
    if manifest["run_id"] != run_dir.name:
        errors.append(f"{path}: run_id does not match directory")
    if manifest["gate"] != run_dir.parent.name.upper():
        errors.append(f"{path}: gate does not match parent directory")
    if not isinstance(manifest["source_commit"], str) or not re.fullmatch(
        r"[0-9a-f]{40}", manifest["source_commit"]
    ):
        errors.append(f"{path}: invalid source_commit")
    if type(manifest["dirty_at_start"]) is not bool:
        errors.append(f"{path}: dirty_at_start must be boolean")
    command = manifest["command"]
    if not isinstance(command, list) or not command or not all(isinstance(item, str) for item in command):
        errors.append(f"{path}: command must be a nonempty string array")
    for field in ("started_at", "ended_at"):
        try:
            datetime.fromisoformat(manifest[field])
        except (TypeError, ValueError):
            errors.append(f"{path}: invalid {field}")
    for field in ("wall_seconds", "cpu_seconds"):
        value = manifest[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            errors.append(f"{path}: {field} must be nonnegative")
    for field, minimum in (("peak_rss_bytes", 0), ("threads", 1)):
        value = manifest[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            errors.append(f"{path}: {field} must be an integer >= {minimum}")
    if not isinstance(manifest["host"], dict):
        errors.append(f"{path}: host must be an object")
    if not isinstance(manifest["config_sha256"], str) or not re.fullmatch(
        r"[0-9a-f]{64}", manifest["config_sha256"]
    ):
        errors.append(f"{path}: invalid config_sha256")
    if manifest["status"] not in STATUSES:
        errors.append(f"{path}: invalid status")
    if "error" in manifest and not isinstance(manifest["error"], str):
        errors.append(f"{path}: error must be a string")
    return errors


def verify_run(run_dir: Path) -> list[str]:
    inventory = run_dir / "checksums.sha256"
    if not inventory.is_file():
        return [f"{run_dir}: missing checksums.sha256"]

    errors: list[str] = []
    expected: dict[str, str] = {}
    for number, line in enumerate(inventory.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            errors.append(f"{inventory}:{number}: malformed inventory line")
            continue
        digest, relative = match.groups()
        relative_path = PurePosixPath(relative)
        if relative_path.is_absolute() or any(part in ("", ".", "..") for part in relative_path.parts):
            errors.append(f"{inventory}:{number}: unsafe inventory path {relative}")
            continue
        if relative == "checksums.sha256":
            errors.append(f"{inventory}:{number}: inventory must not hash itself")
            continue
        if relative in expected:
            errors.append(f"{inventory}:{number}: duplicate path {relative}")
        expected[relative] = digest

    actual_paths: set[str] = set()
    for path in run_dir.rglob("*"):
        if path.is_symlink():
            errors.append(f"{run_dir}: symlink prohibited in evidence: {path.relative_to(run_dir)}")
        elif path.is_file() and path.name != "checksums.sha256":
            actual_paths.add(path.relative_to(run_dir).as_posix())
    if set(expected) != actual_paths:
        errors.append(
            f"{run_dir}: inventory mismatch missing={sorted(set(expected)-actual_paths)} "
            f"unexpected={sorted(actual_paths-set(expected))}"
        )
    missing_required = REQUIRED_RUN_FILES - actual_paths
    if missing_required:
        errors.append(f"{run_dir}: missing required evidence files {sorted(missing_required)}")
    for relative, digest in expected.items():
        path = run_dir / relative
        if path.is_file() and sha256(path) != digest:
            errors.append(f"{run_dir}: checksum mismatch {relative}")
    errors.extend(validate_manifest(run_dir))
    return errors


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        print(f"run only from {ROOT}", file=sys.stderr)
        return 2

    selected_gates = GATES
    if sys.argv[1:]:
        if sys.argv[1:] == ["--baseline-only"]:
            selected_gates = BASELINE_GATES
        else:
            print("usage: evidence_check.py [--baseline-only]", file=sys.stderr)
            return 2

    run_dirs: list[Path] = []
    errors: list[str] = []
    for gate in selected_gates:
        gate_dir = ROOT / "evidence" / gate
        if not gate_dir.exists():
            continue
        for entry in sorted(gate_dir.iterdir()):
            if entry.is_dir() and not entry.is_symlink():
                run_dirs.append(entry)
            else:
                errors.append(f"{gate_dir}: unexpected non-directory entry {entry.name}")
    if not run_dirs:
        print("no scored evidence run directories found", file=sys.stderr)
        return 2
    for run_dir in run_dirs:
        errors.extend(verify_run(run_dir))
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"verified {len(run_dirs)} immutable evidence inventories and manifests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
