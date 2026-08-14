#!/usr/bin/env python3
"""Fetch, decompress, and identify Harder's published n=11 certificate."""

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
import time
from typing import Any


ROOT = Path("/Users/yugendren/experiments/sorting_network_s13")
BUILD_ROOT = ROOT / ".build/b3-certificate"
ACTIVE = BUILD_ROOT / "active.json"
CACHE = ROOT / ".cache/certificates"
COMPRESSED = CACHE / "proof_cert_11.bin.zst"
CERTIFICATE = CACHE / "proof_cert_11.bin"
URL = "https://zenodo.org/api/records/4108365/files/proof_cert_11.bin.zst/content"
DOI = "10.5281/zenodo.4108365"
COMPRESSED_SIZE_BYTES = 1_247_864_564
COMPRESSED_MD5 = "2847374c6bab1260c9771d6fafe65f44"
UNCOMPRESSED_SHA256 = "7fe9f5cd694714bf83da0bcab162a290eb076ad4257265507a74cea8fab85b7e"


def digest(path: Path, algorithm: str) -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def sha256(path: Path) -> str:
    return digest(path, "sha256")


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify_active() -> dict[str, Any] | None:
    if not ACTIVE.is_file():
        return None
    try:
        reference = json.loads(ACTIVE.read_text(encoding="utf-8"))
        manifest_path = ROOT / reference["manifest_path"]
        if sha256(manifest_path) != reference["manifest_sha256"]:
            return None
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("status") != "PASS":
            return None
        if (
            not COMPRESSED.is_file()
            or COMPRESSED.stat().st_size != COMPRESSED_SIZE_BYTES
            or digest(COMPRESSED, "md5") != COMPRESSED_MD5
        ):
            return None
        if not CERTIFICATE.is_file() or sha256(CERTIFICATE) != UNCOMPRESSED_SHA256:
            return None
        if CERTIFICATE.stat().st_size != manifest["uncompressed_size_bytes"]:
            return None
        return manifest
    except (OSError, KeyError, json.JSONDecodeError):
        return None


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        print(f"certificate setup failed: cwd must be exactly {ROOT}", file=sys.stderr)
        return 2
    curl = shutil.which("curl")
    zstd = shutil.which("zstd")
    if curl is None or zstd is None:
        print("certificate setup failed: curl and zstd are required", file=sys.stderr)
        return 2
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    active = verify_active()
    if active is not None:
        print(
            f"verified published n=11 certificate {UNCOMPRESSED_SHA256} "
            f"({active['uncompressed_size_bytes']} bytes)"
        )
        return 0

    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    attempt = BUILD_ROOT / started.strftime("attempt-%Y%m%dT%H%M%SZ")
    attempt.mkdir(exist_ok=False)
    log_path = attempt / "fetch.log"
    commands: list[dict[str, Any]] = []

    def run(command: list[str]) -> None:
        record: dict[str, Any] = {"command": command, "cwd": ROOT.as_posix()}
        commands.append(record)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"$ {' '.join(shlex.quote(part) for part in command)}\n")
            log.flush()
            completed = subprocess.run(
                command,
                cwd=ROOT,
                text=True,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
            record["exit_code"] = completed.returncode
            log.write(f"exit={completed.returncode}\n")
        if completed.returncode != 0:
            raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}")

    status = "FAIL"
    error: str | None = None
    try:
        partial_compressed = CACHE / "proof_cert_11.bin.zst.partial"
        if not COMPRESSED.is_file():
            run(
                [
                    curl,
                    "--location",
                    "--fail",
                    "--retry",
                    "5",
                    "--retry-delay",
                    "5",
                    "--continue-at",
                    "-",
                    "--output",
                    str(partial_compressed),
                    URL,
                ]
            )
            if partial_compressed.stat().st_size != COMPRESSED_SIZE_BYTES:
                raise RuntimeError(
                    f"compressed size mismatch: {partial_compressed.stat().st_size}"
                )
            if digest(partial_compressed, "md5") != COMPRESSED_MD5:
                raise RuntimeError("compressed MD5 mismatch")
            partial_compressed.replace(COMPRESSED)
        if COMPRESSED.stat().st_size != COMPRESSED_SIZE_BYTES:
            raise RuntimeError(f"cached compressed size mismatch: {COMPRESSED.stat().st_size}")
        if digest(COMPRESSED, "md5") != COMPRESSED_MD5:
            raise RuntimeError("cached compressed MD5 mismatch")

        if not CERTIFICATE.is_file() or sha256(CERTIFICATE) != UNCOMPRESSED_SHA256:
            partial_certificate = CACHE / "proof_cert_11.bin.partial"
            run([zstd, "--decompress", "--force", "--no-progress", "-o", str(partial_certificate), str(COMPRESSED)])
            if sha256(partial_certificate) != UNCOMPRESSED_SHA256:
                raise RuntimeError("uncompressed SHA-256 mismatch")
            partial_certificate.replace(CERTIFICATE)
        if sha256(CERTIFICATE) != UNCOMPRESSED_SHA256:
            raise RuntimeError("cached uncompressed SHA-256 mismatch")
        status = "PASS"
    except Exception as exc:
        error = str(exc)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"FAIL: {error}\n")

    ended = datetime.now(timezone.utc)
    manifest: dict[str, Any] = {
        "schema_version": "s13-harder-certificate-cache/v1",
        "status": status,
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "wall_seconds": round(time.perf_counter() - started_perf, 6),
        "url": URL,
        "doi": DOI,
        "compressed_path": COMPRESSED.relative_to(ROOT).as_posix(),
        "compressed_size_bytes": COMPRESSED.stat().st_size if COMPRESSED.is_file() else None,
        "compressed_md5": digest(COMPRESSED, "md5") if COMPRESSED.is_file() else None,
        "uncompressed_path": CERTIFICATE.relative_to(ROOT).as_posix(),
        "uncompressed_size_bytes": CERTIFICATE.stat().st_size if CERTIFICATE.is_file() else None,
        "uncompressed_sha256": sha256(CERTIFICATE) if CERTIFICATE.is_file() else None,
        "commands": commands,
        "fetch_log_sha256": sha256(log_path),
    }
    if error is not None:
        manifest["error"] = error
    manifest_path = attempt / "certificate-manifest.json"
    write_json(manifest_path, manifest)
    if status != "PASS":
        print(
            f"certificate setup failed; preserved attempt at {attempt.relative_to(ROOT)}: {error}",
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
    print(f"downloaded and verified published n=11 certificate: {CERTIFICATE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
