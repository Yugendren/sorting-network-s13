#!/usr/bin/env python3
"""Build Harder's pinned search and checker without modifying upstream sources."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import time
from typing import Any


ROOT = Path("/Users/yugendren/experiments/sorting_network_s13")
UPSTREAM = ROOT / ".cache/third_party/sortnetopt"
BUILD_ROOT = ROOT / ".build/b3-toolchain"
ACTIVE = BUILD_ROOT / "active.json"
STACK_ROOT = ROOT / ".cache/toolchains/b3-stack-root"
PINNED_COMMIT = "0b5d09c47446096f9e3a0812b35afc72b7f2a718"
STACK_LOCK_SHA256 = "b7717e291ca56bc694daebbcc60024c3d6f719dacc25dc00cc7e705d9db671bc"
STRICT_PATCH_SHA256 = "df374fe21c9aa07ee91da700dc2642581c999b61defdacc1ee201a87225435e0"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def command_output(command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> str:
    return subprocess.check_output(command, cwd=cwd, env=env, text=True, stderr=subprocess.STDOUT).strip()


def upstream_identity() -> dict[str, Any]:
    if not (UPSTREAM / ".git").is_dir():
        raise RuntimeError("pinned sortnetopt clone is missing; run tools/setup_sources.py")
    commit = command_output(["git", "rev-parse", "HEAD"], cwd=UPSTREAM)
    if commit != PINNED_COMMIT:
        raise RuntimeError(f"sortnetopt commit mismatch: {commit}")
    tracked_dirty = command_output(
        ["git", "status", "--porcelain", "--untracked-files=no"], cwd=UPSTREAM
    )
    if tracked_dirty:
        raise RuntimeError(f"sortnetopt tracked source is dirty:\n{tracked_dirty}")
    lock = UPSTREAM / "checker/snocheck/stack.yaml.lock"
    patch = UPSTREAM / "checker/verified/strict_and_parallel.patch"
    if sha256(lock) != STACK_LOCK_SHA256:
        raise RuntimeError("sortnetopt Stack lock hash mismatch")
    if sha256(patch) != STRICT_PATCH_SHA256:
        raise RuntimeError("sortnetopt strict/parallel patch hash mismatch")

    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=UPSTREAM).split(b"\0")
    tracked = [name.decode("utf-8") for name in names if name]
    aggregate = hashlib.sha256()
    for name in sorted(tracked):
        path = UPSTREAM / name
        aggregate.update(name.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(bytes.fromhex(sha256(path)))
        aggregate.update(b"\n")
    return {
        "repository": "https://github.com/jix/sortnetopt.git",
        "commit": commit,
        "tracked_file_count": len(tracked),
        "tracked_source_aggregate_sha256": aggregate.hexdigest(),
        "stack_lock_sha256": sha256(lock),
        "strict_and_parallel_patch_sha256": sha256(patch),
    }


def verify_active() -> dict[str, Any] | None:
    if not ACTIVE.is_file():
        return None
    try:
        reference = json.loads(ACTIVE.read_text(encoding="utf-8"))
        manifest_path = ROOT / reference["manifest_path"]
        if sha256(manifest_path) != reference["manifest_sha256"]:
            return None
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("status") != "PASS" or manifest.get("upstream", {}).get("commit") != PINNED_COMMIT:
            return None
        identity = upstream_identity()
        if identity["tracked_source_aggregate_sha256"] != manifest["upstream"]["tracked_source_aggregate_sha256"]:
            return None
        for key in ("stack_wrapper", "rust_binary", "checker_binary"):
            item = manifest[key]
            path = ROOT / item["path"]
            if not path.is_file() or path.stat().st_size != item["size_bytes"] or sha256(path) != item["sha256"]:
                return None
        return manifest
    except (OSError, KeyError, json.JSONDecodeError, RuntimeError, subprocess.SubprocessError):
        return None


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        print(f"sortnetopt setup failed: cwd must be exactly {ROOT}", file=sys.stderr)
        return 2
    try:
        identity = upstream_identity()
    except Exception as exc:
        print(f"sortnetopt setup failed before build attempt: {exc}", file=sys.stderr)
        return 2

    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    active = verify_active()
    if active is not None:
        print(
            "verified Harder toolchain "
            f"{active['rust_binary']['sha256']} / {active['checker_binary']['sha256']}"
        )
        return 0

    stack_real = shutil.which("stack")
    cargo = shutil.which("cargo")
    if stack_real is None or cargo is None:
        print("sortnetopt setup failed: stack and cargo are required", file=sys.stderr)
        return 2
    zstd = shutil.which("zstd")
    if zstd is None:
        print("sortnetopt setup failed: zstd is required", file=sys.stderr)
        return 2

    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    attempt = BUILD_ROOT / started.strftime("attempt-%Y%m%dT%H%M%SZ")
    attempt.mkdir(exist_ok=False)
    bin_dir = attempt / "bin"
    bin_dir.mkdir()
    log_path = attempt / "build.log"
    wrapper = bin_dir / "stack"
    wrapper.write_text(
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        f"exec {shlex.quote(stack_real)} --arch x86_64 \"$@\"\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    STACK_ROOT.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["STACK_ROOT"] = str(STACK_ROOT)
    commands: list[dict[str, Any]] = []

    def run(command: list[str], cwd: Path) -> None:
        record: dict[str, Any] = {
            "command": command,
            "cwd": cwd.relative_to(ROOT).as_posix(),
        }
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
            record["exit_code"] = completed.returncode
            log.write(f"exit={completed.returncode}\n")
        if completed.returncode != 0:
            raise RuntimeError(f"build command failed ({completed.returncode}): {' '.join(command)}")

    status = "FAIL"
    error: str | None = None
    try:
        run(["cargo", "build", "--release"], UPSTREAM)
        checker_dir = UPSTREAM / "checker/snocheck"
        run(["stack", "setup"], checker_dir)
        run(
            ["stack", "build", "--copy-bins", "--local-bin-path", str(bin_dir)],
            checker_dir,
        )
        rust_binary = UPSTREAM / "target/release/sortnetopt"
        checker_binary = bin_dir / "snocheck"
        if not rust_binary.is_file() or not checker_binary.is_file():
            raise RuntimeError("expected Rust or Haskell executable is missing after build")
        run([str(rust_binary), "--help"], UPSTREAM)
        run([str(checker_binary)], UPSTREAM)
        status = "PASS"
    except Exception as exc:
        error = str(exc)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"FAIL: {error}\n")

    ended = datetime.now(timezone.utc)
    manifest: dict[str, Any] = {
        "schema_version": "s13-harder-toolchain-build/v1",
        "status": status,
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "wall_seconds": round(time.perf_counter() - started_perf, 6),
        "host_machine": platform.machine(),
        "portability_mode": "aarch64 Stack host selecting x86_64 GHC under Rosetta",
        "stack_root": STACK_ROOT.relative_to(ROOT).as_posix(),
        "upstream": identity,
        "stack_wrapper": {
            "path": wrapper.relative_to(ROOT).as_posix(),
            "sha256": sha256(wrapper),
            "size_bytes": wrapper.stat().st_size,
        },
        "stack_version": command_output([stack_real, "--version"]).splitlines()[0],
        "cargo_version": command_output([cargo, "--version"]),
        "rustc_version": command_output(["rustc", "--version"]),
        "zstd_version": command_output([zstd, "--version"]),
        "commands": commands,
        "build_log_sha256": sha256(log_path),
    }
    for key, path in (
        ("rust_binary", UPSTREAM / "target/release/sortnetopt"),
        ("checker_binary", bin_dir / "snocheck"),
    ):
        if path.is_file():
            manifest[key] = {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": sha256(path),
                "size_bytes": path.stat().st_size,
                "file_type": command_output(["file", "-b", str(path)]),
            }
        else:
            manifest[key] = {"path": path.relative_to(ROOT).as_posix(), "missing": True}
    if error is not None:
        manifest["error"] = error
    manifest_path = attempt / "build-manifest.json"
    write_json(manifest_path, manifest)

    if status != "PASS":
        print(
            f"sortnetopt setup failed; preserved attempt at {attempt.relative_to(ROOT)}: {error}",
            file=sys.stderr,
        )
        return 1
    write_json(
        ACTIVE,
        {
            "manifest_path": manifest_path.relative_to(ROOT).as_posix(),
            "manifest_sha256": sha256(manifest_path),
        },
    )
    print(f"built and smoke-tested Harder toolchain: {attempt.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
