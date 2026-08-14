#!/usr/bin/env python3
"""Run the immutable B0 source/protocol freeze gate."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import subprocess
import sys
import time
from typing import Any


ROOT = Path("/Users/yugendren/experiments/sorting_network_s13")
FROZEN = ROOT / "config/frozen"
CACHE_SOURCES = ROOT / ".cache/sources"
THIRD_PARTY = ROOT / ".cache/third_party"


def run(command: list[str], *, check: bool = True) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}\n{completed.stdout}")
    return completed.stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aggregate_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        relative = path.relative_to(ROOT).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256(path)))
        digest.update(b"\n")
    return digest.hexdigest()


def sysctl(name: str) -> str:
    return subprocess.check_output(["sysctl", "-n", name], text=True).strip()


def host_record() -> dict[str, Any]:
    disk = shutil.disk_usage(ROOT)
    return {
        "model": sysctl("hw.model"),
        "cpu": sysctl("machdep.cpu.brand_string"),
        "logical_cores": int(sysctl("hw.logicalcpu")),
        "physical_cores": int(sysctl("hw.physicalcpu")),
        "memory_bytes": int(sysctl("hw.memsize")),
        "os": platform.platform(),
        "machine": platform.machine(),
        "disk_total_bytes": disk.total,
        "disk_free_bytes_at_start": disk.free,
    }


def tool_versions() -> dict[str, str]:
    commands = {
        "git": ["git", "--version"],
        "make": ["make", "--version"],
        "cmake": ["cmake", "--version"],
        "python": [sys.executable, "--version"],
        "uv": ["uv", "--version"],
        "go": ["go", "version"],
        "clang": ["clang", "--version"],
        "gcc": ["gcc-16", "--version"],
        "cargo": ["cargo", "--version"],
        "rustc": ["rustc", "--version"],
        "node": ["node", "--version"],
        "zstd": ["zstd", "--version"],
        "boost": ["brew", "list", "--versions", "boost"],
    }
    return {name: run(command).splitlines()[0] for name, command in commands.items()}


def repository_record() -> dict[str, Any]:
    return {
        "branch": run(["git", "branch", "--show-current"]),
        "head": run(["git", "rev-parse", "HEAD"]),
        "status_porcelain": run(["git", "status", "--porcelain", "--untracked-files=all"]),
        "recent_commits": run(["git", "log", "--oneline", "-5"]).splitlines(),
        "worktrees_porcelain": run(["git", "worktree", "list", "--porcelain"]).splitlines(),
    }


def validate_authority(freeze: dict[str, Any]) -> list[dict[str, str]]:
    results = []
    for key in ("contract", "prompt", "agents"):
        path = ROOT / freeze["authority"][f"{key}_path"]
        expected = freeze["authority"][f"{key}_sha256"]
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(f"authority hash mismatch: {path}")
        results.append({"path": str(path.relative_to(ROOT)), "sha256": actual})
    return results


def validate_protocol(freeze: dict[str, Any]) -> dict[str, Any]:
    required = [ROOT / path for path in freeze["required_frozen_files"]]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing frozen files: {missing}")

    seeds = json.loads((FROZEN / "seeds.json").read_text(encoding="utf-8"))["seeds"]
    if len(seeds) != 20 or len(set(seeds)) != 20 or any(not isinstance(seed, int) or seed == 0 for seed in seeds):
        raise RuntimeError("seed freeze must contain exactly 20 unique nonzero integers")

    budgets = json.loads((FROZEN / "budgets.json").read_text(encoding="utf-8"))
    if budgets["gpu_allowed"] or budgets["constructive"]["threads_per_seed"] != 1:
        raise RuntimeError("GPU/thread policy contradicts the contract")
    if budgets["constructive"]["per_seed_cpu_seconds"] > 900:
        raise RuntimeError("constructive per-seed cap exceeds the contract")
    if budgets["certificate_n11"]["wall_seconds"] > 14400:
        raise RuntimeError("n=11 replay cap exceeds the contract")

    b2 = json.loads((FROZEN / "b2-senso.json").read_text(encoding="utf-8"))
    expected = {"channels": 13, "acceptance_size": 45, "population": 200, "generations": 500}
    for key, value in expected.items():
        if b2[key] != value:
            raise RuntimeError(f"B2 frozen parameter mismatch: {key}")
    if freeze["problem"]["frontier_search_allowed"]:
        raise RuntimeError("frontier search must remain prohibited")

    file_hashes = [
        {"path": str(path.relative_to(ROOT)), "sha256": sha256(path)}
        for path in required
    ]
    return {
        "required_files": [str(path.relative_to(ROOT)) for path in required],
        "required_file_sha256": file_hashes,
        "aggregate_sha256": aggregate_hash(required),
        "seeds": seeds,
        "resource_limits": budgets,
        "host_policy": freeze["host_policy"],
        "budgets_sha256": sha256(FROZEN / "budgets.json"),
        "b2_config_sha256": sha256(FROZEN / "b2-senso.json"),
        "b3_config_sha256": sha256(FROZEN / "b3-exact.json"),
    }


def validate_sources() -> list[dict[str, Any]]:
    ledger = json.loads((FROZEN / "sources.json").read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []
    for item in ledger["sources"]:
        cache_file = item.get("cache_file")
        if not cache_file:
            continue
        path = CACHE_SOURCES / cache_file
        if not path.is_file():
            raise RuntimeError(f"missing cached source; run make setup: {path}")
        actual_hash = sha256(path)
        actual_size = path.stat().st_size
        if actual_hash != item["sha256"] or actual_size != item["size_bytes"]:
            raise RuntimeError(f"cached source mismatch: {path}")
        results.append(
            {
                "id": item["id"],
                "path": str(path.relative_to(ROOT)),
                "sha256": actual_hash,
                "size_bytes": actual_size,
                "status": "ARTIFACT_VERIFIED",
            }
        )

    catalog = (CACHE_SOURCES / "sorting_networks_extended.html").read_text(encoding="utf-8")
    if '<td class="idx">44&hellip;45</td>' not in catalog:
        raise RuntimeError("frozen catalog no longer evidences size interval 44...45")
    if 'id="N13L45D10"' not in catalog or "13 inputs, 45 CEs, 10 layers" not in catalog:
        raise RuntimeError("frozen catalog lacks the required 45-comparator witness")

    by_id = {item["id"]: item for item in ledger["sources"]}
    for source_id, directory_name in (
        ("sortnetopt", "sortnetopt"),
        ("dobbelaere-catalog", "dobbelaere-catalog"),
    ):
        source = by_id[source_id]
        checkout = THIRD_PARTY / directory_name
        if not (checkout / ".git").exists():
            raise RuntimeError(f"missing pinned checkout; run make setup: {checkout}")
        head = run(["git", "-C", str(checkout), "rev-parse", "HEAD"])
        dirty = run(["git", "-C", str(checkout), "status", "--porcelain"])
        if head != source["commit"] or dirty:
            raise RuntimeError(f"third-party checkout mismatch or dirty state: {checkout}")
        results.append(
            {
                "id": source_id,
                "path": str(checkout.relative_to(ROOT)),
                "commit": head,
                "status": "ARTIFACT_VERIFIED",
            }
        )

    sortnetopt = THIRD_PARTY / "sortnetopt"
    for path_field, hash_field in (
        ("cargo_toml_path", "cargo_toml_sha256"),
        ("stack_yaml_path", "stack_yaml_sha256"),
        ("stack_lock_path", "stack_lock_sha256"),
    ):
        relative = by_id["sortnetopt"][path_field]
        if sha256(sortnetopt / relative) != by_id["sortnetopt"][hash_field]:
            raise RuntimeError(f"sortnetopt pinned-file mismatch: {relative}")

    catalog_git_html = THIRD_PARTY / "dobbelaere-catalog/sorting_networks_extended.html"
    if sha256(catalog_git_html) != by_id["dobbelaere-catalog"]["sha256"]:
        raise RuntimeError("catalog Git HTML does not byte-match the frozen retrieval")
    return results


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_checksums(directory: Path) -> None:
    files = sorted(path for path in directory.rglob("*") if path.is_file() and path.name != "checksums.sha256")
    lines = [f"{sha256(path)}  {path.relative_to(directory).as_posix()}" for path in files]
    (directory / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        print(f"B0 preflight failed: cwd must be exactly {ROOT}", file=sys.stderr)
        return 2
    if run(["git", "branch", "--show-current"]) != "goal/s13-baseline":
        print("B0 preflight failed: wrong branch", file=sys.stderr)
        return 2
    dirty = run(["git", "status", "--porcelain", "--untracked-files=all"])
    if dirty:
        print("B0 preflight failed: scored configuration is dirty", file=sys.stderr)
        print(dirty, file=sys.stderr)
        return 2

    repo = repository_record()

    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    started_cpu = time.process_time()
    run_id = started.strftime("b0-%Y%m%dT%H%M%SZ")
    out = ROOT / "evidence/b0" / run_id
    out.mkdir(parents=True, exist_ok=False)
    log_lines = ["B0 falsifiable gate: freeze is internally consistent and target is not stale."]
    status = "FAIL"
    error: str | None = None
    config_hash = "0" * 64
    host: dict[str, Any] = {}

    try:
        freeze = json.loads((FROZEN / "b0-freeze.json").read_text(encoding="utf-8"))
        authority = validate_authority(freeze)
        protocol = validate_protocol(freeze)
        config_hash = protocol["aggregate_sha256"]
        sources = validate_sources()
        host = host_record()
        if host["memory_bytes"] < 16 * 1024**3:
            raise RuntimeError("host memory is below the frozen 16 GiB baseline host")
        if host["disk_free_bytes_at_start"] < 20 * 1024**3:
            raise RuntimeError("less than 20 GiB free; B3 certificate replay is unsafe")

        write_json(out / "authority-verification.json", authority)
        write_json(out / "protocol-verification.json", protocol)
        write_json(out / "source-verification.json", sources)
        write_json(out / "repository-verification.json", repo)
        write_json(out / "tool-versions.json", tool_versions())
        status = "PASS"
        log_lines.append("PASS: catalog snapshot states 44...45 and contains the 45-comparator witness.")
        log_lines.append("PASS: authority, source, seed, budget, dependency, and evidence freezes verified.")
    except Exception as exc:
        error = str(exc)
        log_lines.append(f"FAIL: {error}")

    ended = datetime.now(timezone.utc)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    peak_rss = int(usage.ru_maxrss if sys.platform == "darwin" else usage.ru_maxrss * 1024)
    manifest = {
        "schema_version": "s13-evidence-manifest/v1",
        "run_id": run_id,
        "gate": "B0",
        "source_commit": run(["git", "rev-parse", "HEAD"]),
        "dirty_at_start": False,
        "command": [sys.executable, "tools/b0_gate.py"],
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "wall_seconds": round(time.perf_counter() - started_perf, 6),
        "cpu_seconds": round(time.process_time() - started_cpu, 6),
        "peak_rss_bytes": peak_rss,
        "threads": 1,
        "host": host,
        "config_sha256": config_hash,
        "status": status,
    }
    if error is not None:
        manifest["error"] = error
    write_json(out / "manifest.json", manifest)
    (out / "command.txt").write_text(f"{sys.executable} tools/b0_gate.py\n", encoding="utf-8")
    (out / "stdout.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    (out / "stderr.txt").write_text("", encoding="utf-8")
    write_checksums(out)
    for line in log_lines:
        print(line)
    print(f"evidence: {out.relative_to(ROOT)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
