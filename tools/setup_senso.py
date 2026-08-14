#!/usr/bin/env python3
"""Build the pinned external SENSO artifact with the audited portability patch."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
import time
from typing import Any


ROOT = Path("/Users/yugendren/experiments/sorting_network_s13")
ARCHIVE = ROOT / ".cache/sources/symmetry-1.1.tar.gz"
PATCH = ROOT / "tools/patches/symmetry-1.1-macos.patch"
BUILD_ROOT = ROOT / ".build/senso"
ACTIVE = BUILD_ROOT / "active.json"
ARCHIVE_SHA256 = "d3e960fa5c7b292e38a3024e76436fec3550baa27de240faa90568da0882b53c"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_active() -> dict[str, Any] | None:
    if not ACTIVE.is_file():
        return None
    try:
        active = json.loads(ACTIVE.read_text(encoding="utf-8"))
        manifest_path = ROOT / active["manifest_path"]
        if sha256(manifest_path) != active["manifest_sha256"]:
            return None
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        binary = ROOT / manifest["binary_path"]
        if not binary.is_file() or sha256(binary) != manifest["binary_sha256"]:
            return None
        if manifest["archive_sha256"] != ARCHIVE_SHA256 or manifest["patch_sha256"] != sha256(PATCH):
            return None
        return manifest
    except (OSError, KeyError, json.JSONDecodeError):
        return None


def safe_extract(archive: Path, destination: Path) -> None:
    destination_resolved = destination.resolve()
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            target = (destination / member.name).resolve()
            if destination_resolved not in target.parents and target != destination_resolved:
                raise RuntimeError(f"unsafe archive member: {member.name}")
        bundle.extractall(destination, filter="data")


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        raise RuntimeError(f"run only from {ROOT}")
    if not ARCHIVE.is_file() or sha256(ARCHIVE) != ARCHIVE_SHA256:
        raise RuntimeError("pinned SENSO archive missing or hash-mismatched; run tools/setup_sources.py")

    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    active = verify_active()
    if active is not None:
        print(f"verified SENSO build {active['binary_path']} ({active['binary_sha256']})")
        return 0

    started = datetime.now(timezone.utc)
    attempt = BUILD_ROOT / started.strftime("attempt-%Y%m%dT%H%M%SZ")
    attempt.mkdir(exist_ok=False)
    extract_root = attempt / "source"
    install_root = attempt / "install"
    binary_dir = attempt / "bin"
    smoke_dir = attempt / "smoke"
    for directory in (extract_root, install_root, binary_dir, smoke_dir):
        directory.mkdir(parents=True, exist_ok=True)
    log_path = attempt / "build.log"
    commands: list[dict[str, Any]] = []
    started_perf = time.perf_counter()

    def run(command: list[str], cwd: Path, env: dict[str, str]) -> None:
        record = {"command": command, "cwd": cwd.relative_to(ROOT).as_posix()}
        commands.append(record)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"$ {' '.join(shlex.quote(part) for part in command)}\n")
            log.flush()
            completed = subprocess.run(
                command,
                cwd=cwd,
                env=env,
                text=True,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
            log.write(f"exit={completed.returncode}\n")
        record["exit_code"] = completed.returncode
        if completed.returncode != 0:
            raise RuntimeError(f"build command failed ({completed.returncode}): {' '.join(command)}")

    try:
        safe_extract(ARCHIVE, extract_root)
        source = extract_root / "symmetry-1.1"
        env = os.environ.copy()
        env.update(
            {
                "CC": "clang",
                "CXX": "clang++",
                "CPPFLAGS": "-I/opt/homebrew/include",
                "LDFLAGS": "-L/opt/homebrew/lib",
            }
        )
        patch_result = subprocess.run(
            ["patch", "-p1", "-i", str(PATCH)],
            cwd=source,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        log_path.write_text(
            f"$ patch -p1 -i {PATCH}\n{patch_result.stdout}exit={patch_result.returncode}\n",
            encoding="utf-8",
        )
        commands.append(
            {
                "command": ["patch", "-p1", "-i", str(PATCH)],
                "cwd": source.relative_to(ROOT).as_posix(),
                "exit_code": patch_result.returncode,
            }
        )
        if patch_result.returncode != 0:
            raise RuntimeError("audited portability patch did not apply cleanly")

        beagle = source / "beagle"
        run(["./configure", "--disable-shared", f"--prefix={install_root}"], beagle, env)
        run(["make", "-j1"], beagle, env)
        run(["make", "-j1", "install"], beagle, env)

        pkg_env = env.copy()
        pkg_env["PKG_CONFIG_PATH"] = str(install_root / "lib/pkgconfig")
        flags_output = subprocess.check_output(
            ["pkg-config", "--cflags", "--libs", "beagle", "beagle-sn"],
            cwd=ROOT,
            env=pkg_env,
            text=True,
        )
        binary = binary_dir / "sorting"
        compile_command = [
            "clang++",
            "-O2",
            "-g",
            str(source / "experiments/sorting/sorting/main.cpp"),
            "-o",
            str(binary),
            "-I/opt/homebrew/include",
            *shlex.split(flags_output),
        ]
        run(compile_command, ROOT, pkg_env)

        smoke_command = [
            str(binary),
            f"-OBconf={source / 'experiments/sorting/sorting/beagle.conf'}",
            "-OBec.pop.size=2",
            "-OBec.rand.seed=1",
            "-OBec.term.maxgen=1",
            "-OBsn.init.numinputs=13",
            "-OBsn.init.filter=0:21",
            "-OBsn.init.initfuncs=1",
            "-OBsn.eval.compfit=1",
            "-OBms.write.interval=0",
            "-OBms.write.prefix=smoke",
            "-OBlg.file.name=smoke.log",
        ]
        run(smoke_command, smoke_dir, env)
        milestones = sorted(smoke_dir.glob("smoke_g*.obm.gz"))
        if not milestones:
            raise RuntimeError("SENSO smoke run produced no milestone")

        ended = datetime.now(timezone.utc)
        manifest = {
            "schema_version": "s13-senso-build/v1",
            "status": "PASS",
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
            "wall_seconds": round(time.perf_counter() - started_perf, 6),
            "archive_path": ARCHIVE.relative_to(ROOT).as_posix(),
            "archive_sha256": ARCHIVE_SHA256,
            "archive_size_bytes": ARCHIVE.stat().st_size,
            "patch_path": PATCH.relative_to(ROOT).as_posix(),
            "patch_sha256": sha256(PATCH),
            "source_path": source.relative_to(ROOT).as_posix(),
            "install_path": install_root.relative_to(ROOT).as_posix(),
            "binary_path": binary.relative_to(ROOT).as_posix(),
            "binary_sha256": sha256(binary),
            "binary_size_bytes": binary.stat().st_size,
            "build_log_path": log_path.relative_to(ROOT).as_posix(),
            "build_log_sha256": sha256(log_path),
            "compiler": subprocess.check_output(["clang++", "--version"], text=True).splitlines()[0],
            "boost": subprocess.check_output(["brew", "list", "--versions", "boost"], text=True).strip(),
            "commands": commands,
            "smoke_milestones": [
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": sha256(path),
                    "size_bytes": path.stat().st_size,
                }
                for path in milestones
            ],
        }
        manifest_path = attempt / "build-manifest.json"
        write_json(manifest_path, manifest)
        write_json(
            ACTIVE,
            {
                "manifest_path": manifest_path.relative_to(ROOT).as_posix(),
                "manifest_sha256": sha256(manifest_path),
            },
        )
        print(f"built and smoke-tested SENSO: {binary.relative_to(ROOT)}")
        return 0
    except Exception as exc:
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"FAIL: {exc}\n")
        print(f"SENSO setup failed; preserved attempt at {attempt.relative_to(ROOT)}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"SENSO setup failed before build attempt: {exc}", file=sys.stderr)
        raise SystemExit(1)
