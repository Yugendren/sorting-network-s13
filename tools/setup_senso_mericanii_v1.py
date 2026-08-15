#!/usr/bin/env python3
"""Build pinned SENSO plus frozen E1 instrumentation and Mericanii V1 ranker."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tarfile
import time
from typing import Any


ROOT = Path("/Users/yugendren/experiments/sorting_network_s13")
ARCHIVE = ROOT / ".cache/sources/symmetry-1.1.tar.gz"
PORTABILITY_PATCH = ROOT / "tools/patches/symmetry-1.1-macos.patch"
INSTRUMENTATION_PATCH = ROOT / "tools/patches/symmetry-1.1-mericanii-instrumentation.patch"
METHOD_PATCH = ROOT / "tools/patches/symmetry-1.1-mericanii-v1.patch"
MODEL_ROOT = ROOT / "evidence/e2/e2-train-20260815T023758Z/replay-1/artifacts"
MODEL_HEADER = MODEL_ROOT / "MericaniiModelV1Weights.hpp"
MODEL_FIXTURE = MODEL_ROOT / "model-inference-fixture.json"
BUILD_ROOT = ROOT / ".build/senso-mericanii-v1"
ACTIVE = BUILD_ROOT / "active.json"
ARCHIVE_SHA256 = "d3e960fa5c7b292e38a3024e76436fec3550baa27de240faa90568da0882b53c"
MODEL_HEADER_SHA256 = "f7533479d67d44ff5b5da7e9dd3cad9909785e7a912997b8c2b2edfc8fd69864"
MODEL_FIXTURE_SHA256 = "428ef8f0b67c2f05f923501d23f85ad4690f79e310fbe77039b44294c71c15bc"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_extract(archive: Path, destination: Path) -> None:
    resolved = destination.resolve()
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            target = (destination / member.name).resolve()
            if target != resolved and resolved not in target.parents:
                raise RuntimeError(f"unsafe archive member: {member.name}")
        bundle.extractall(destination, filter="data")


def expected_hashes() -> dict[str, str]:
    return {
        "archive_sha256": ARCHIVE_SHA256,
        "portability_patch_sha256": sha256(PORTABILITY_PATCH),
        "instrumentation_patch_sha256": sha256(INSTRUMENTATION_PATCH),
        "method_patch_sha256": sha256(METHOD_PATCH),
        "model_header_sha256": MODEL_HEADER_SHA256,
        "model_fixture_sha256": MODEL_FIXTURE_SHA256,
    }


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
        if any(manifest.get(key) != value for key, value in expected_hashes().items()):
            return None
        return manifest
    except (OSError, KeyError, json.JSONDecodeError):
        return None


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        raise RuntimeError(f"run only from {ROOT}")
    if not ARCHIVE.is_file() or sha256(ARCHIVE) != ARCHIVE_SHA256:
        raise RuntimeError("pinned SENSO archive missing or hash-mismatched")
    for path in (PORTABILITY_PATCH, INSTRUMENTATION_PATCH, METHOD_PATCH, MODEL_HEADER, MODEL_FIXTURE):
        if not path.is_file():
            raise RuntimeError(f"missing frozen input: {path}")
    if sha256(MODEL_HEADER) != MODEL_HEADER_SHA256 or sha256(MODEL_FIXTURE) != MODEL_FIXTURE_SHA256:
        raise RuntimeError("frozen model header or inference fixture hash mismatch")

    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    active = verify_active()
    if active is not None:
        print(f"verified Mericanii V1 build {active['binary_path']} ({active['binary_sha256']})")
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

    def invoke(command: list[str], cwd: Path, env: dict[str, str], *, label: str | None = None) -> None:
        record: dict[str, Any] = {"command": command, "cwd": cwd.relative_to(ROOT).as_posix()}
        if label:
            record["environment_profile"] = label
        commands.append(record)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"$ {' '.join(shlex.quote(part) for part in command)}\n")
            log.flush()
            completed = subprocess.run(command, cwd=cwd, env=env, text=True, stdout=log, stderr=subprocess.STDOUT, check=False)
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
                "GOMAXPROCS": "1",
                "OMP_NUM_THREADS": "1",
                "VECLIB_MAXIMUM_THREADS": "1",
                "LC_ALL": "C",
                "TZ": "UTC",
            }
        )
        for patch, role in (
            (PORTABILITY_PATCH, "portability"),
            (INSTRUMENTATION_PATCH, "instrumentation"),
            (METHOD_PATCH, "mericanii-v1"),
        ):
            invoke(["patch", "-p1", "-i", str(patch)], source, env, label=role)
        installed_header = source / "beagle/beagle/SN/include/beagle/SN/MericaniiModelV1Weights.hpp"
        shutil.copy2(MODEL_HEADER, installed_header)
        if sha256(installed_header) != MODEL_HEADER_SHA256:
            raise RuntimeError("model header copy mismatch")

        fixture_work = attempt / "compiled-inference-check"
        invoke(
            [
                sys.executable,
                str(ROOT / "tools/verify_compiled_model.py"),
                "--header",
                str(installed_header),
                "--fixture",
                str(MODEL_FIXTURE),
                "--work-dir",
                str(fixture_work),
            ],
            ROOT,
            env,
            label="compiled-float32-fixture",
        )
        fixture_result = json.loads((fixture_work / "result.json").read_text(encoding="utf-8"))

        beagle = source / "beagle"
        invoke(["./configure", "--disable-shared", f"--prefix={install_root}"], beagle, env)
        invoke(["make", "-j1"], beagle, env)
        invoke(["make", "-j1", "install"], beagle, env)

        pkg_env = env.copy()
        pkg_env["PKG_CONFIG_PATH"] = str(install_root / "lib/pkgconfig")
        flags = subprocess.check_output(["pkg-config", "--cflags", "--libs", "beagle", "beagle-sn"], cwd=ROOT, env=pkg_env, text=True)
        binary = binary_dir / "sorting"
        compile_command = [
            "clang++", "-O2", "-g", str(source / "experiments/sorting/sorting/main.cpp"), "-o", str(binary),
            "-I/opt/homebrew/include", *shlex.split(flags),
        ]
        invoke(compile_command, ROOT, pkg_env)

        dataset = smoke_dir / "dataset.tsv"
        inference_stats = smoke_dir / "inference-stats.json"
        smoke_env = env.copy()
        smoke_env.update(
            {
                "MERICANII_DATASET_PATH": str(dataset),
                "MERICANII_DATASET_SEED": "1",
                "MERICANII_INFERENCE_STATS_PATH": str(inference_stats),
            }
        )
        smoke_command = [
            str(binary), f"-OBconf={source / 'experiments/sorting/sorting/beagle.conf'}",
            "-OBec.pop.size=2", "-OBec.rand.seed=1", "-OBec.term.maxgen=1",
            "-OBsn.init.numinputs=13", "-OBsn.init.filter=0:21", "-OBsn.init.initfuncs=1",
            "-OBsn.eval.compfit=1", "-OBsn.estimate.frac=0.5", "-OBsn.estimate.prob=0.5",
            "-OBsn.estimate.gtrun=1", "-OBsn.mutation.mksym=1", "-OBms.write.interval=0",
            "-OBms.write.prefix=smoke", "-OBlg.file.name=smoke.log",
        ]
        invoke(smoke_command, smoke_dir, smoke_env, label="mericanii-v1-smoke-seed-1")
        milestones = sorted(smoke_dir.glob("smoke_g*.obm.gz"))
        if len(milestones) != 1:
            raise RuntimeError(f"expected one smoke milestone, found {len(milestones)}")
        if not dataset.is_file() or len(dataset.read_text(encoding="utf-8").splitlines()) != 4:
            raise RuntimeError("Mericanii smoke dataset must contain header plus 3 rows")
        stats = json.loads(inference_stats.read_text(encoding="utf-8"))
        if stats.get("rank_calls") != 3 or stats.get("score_calls", 0) < 3:
            raise RuntimeError("Mericanii inference smoke counters mismatch")

        ended = datetime.now(timezone.utc)
        manifest = {
            "schema_version": "s13-senso-mericanii-build/v1",
            "status": "PASS",
            "started_at": started.isoformat(),
            "ended_at": ended.isoformat(),
            "wall_seconds": round(time.perf_counter() - started_perf, 6),
            **expected_hashes(),
            "archive_path": ARCHIVE.relative_to(ROOT).as_posix(),
            "portability_patch_path": PORTABILITY_PATCH.relative_to(ROOT).as_posix(),
            "instrumentation_patch_path": INSTRUMENTATION_PATCH.relative_to(ROOT).as_posix(),
            "method_patch_path": METHOD_PATCH.relative_to(ROOT).as_posix(),
            "model_header_path": MODEL_HEADER.relative_to(ROOT).as_posix(),
            "model_fixture_path": MODEL_FIXTURE.relative_to(ROOT).as_posix(),
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
            "compiled_inference_check": fixture_result,
            "smoke_dataset": {"path": dataset.relative_to(ROOT).as_posix(), "sha256": sha256(dataset), "data_rows": 3},
            "smoke_inference_stats": {"path": inference_stats.relative_to(ROOT).as_posix(), "sha256": sha256(inference_stats), **stats},
            "smoke_milestone": {"path": milestones[0].relative_to(ROOT).as_posix(), "sha256": sha256(milestones[0])},
        }
        manifest_path = attempt / "build-manifest.json"
        write_json(manifest_path, manifest)
        write_json(ACTIVE, {"manifest_path": manifest_path.relative_to(ROOT).as_posix(), "manifest_sha256": sha256(manifest_path)})
        print(f"built and smoke-tested Mericanii V1: {binary.relative_to(ROOT)}")
        return 0
    except Exception as exc:
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"FAIL: {type(exc).__name__}: {exc}\n")
        write_json(
            attempt / "failure.json",
            {
                "schema_version": "s13-senso-mericanii-build-failure/v1",
                "status": "FAIL",
                "started_at": started.isoformat(),
                "ended_at": datetime.now(timezone.utc).isoformat(),
                "error_type": type(exc).__name__,
                "error": str(exc),
                "commands": commands,
                "build_log_sha256": sha256(log_path),
            },
        )
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Mericanii V1 build failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
