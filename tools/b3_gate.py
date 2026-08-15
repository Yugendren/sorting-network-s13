#!/usr/bin/env python3
"""Run Harder's frozen n=9 workflow and replay the published n=11 certificate."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import resource
import shutil
import signal
import struct
import subprocess
import sys
import time
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import fetch_harder_certificate, setup_sortnetopt


ROOT = Path("/Users/yugendren/experiments/sorting_network_s13")
UPSTREAM = ROOT / ".cache/third_party/sortnetopt"
CONFIG_PATH = ROOT / "config/frozen/b3-exact.json"
BUDGETS_PATH = ROOT / "config/frozen/budgets.json"
SOURCES_PATH = ROOT / "config/frozen/sources.json"
WORK_ROOT = ROOT / ".build/b3-runs"
B2_MANIFEST = ROOT / "evidence/b2/b2-20260814T232833Z/manifest.json"
B2_MANIFEST_SHA256 = "8d057c43edb1e408d4334783cbb0a615110011bfa2aac121319ca32924888d74"
EXPECTED_RESULTS = {9: (9, 25), 11: (11, 35)}


class GateFailure(RuntimeError):
    def __init__(self, message: str, status: str = "FAIL") -> None:
        super().__init__(message)
        self.status = status


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_checksums(directory: Path) -> None:
    files = sorted(path for path in directory.rglob("*") if path.is_file() and path.name != "checksums.sha256")
    lines = [f"{sha256(path)}  {path.relative_to(directory).as_posix()}" for path in files]
    (directory / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_text(command: list[str], *, cwd: Path = ROOT, check: bool = True) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}\n{completed.stdout}")
    return completed.stdout.strip()


def aggregate_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(dict.fromkeys(paths)):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
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
        "disk_free_bytes_at_start": disk.free,
    }


def process_tree_rss_bytes(root_pid: int) -> int:
    completed = subprocess.run(
        ["ps", "-axo", "pid=,ppid=,rss="],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if completed.returncode != 0:
        return 0
    parents: dict[int, int] = {}
    rss_kib: dict[int, int] = {}
    for line in completed.stdout.splitlines():
        parts = line.split()
        if len(parts) != 3:
            continue
        pid, parent, rss = (int(part) for part in parts)
        parents[pid] = parent
        rss_kib[pid] = rss
    selected = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, parent in parents.items():
            if parent in selected and pid not in selected:
                selected.add(pid)
                changed = True
    return sum(rss_kib.get(pid, 0) for pid in selected) * 1024


def parse_time_metrics(stderr_path: Path) -> dict[str, Any]:
    text = stderr_path.read_text(encoding="utf-8", errors="replace")
    timing = re.search(r"(?m)^\s*([0-9.]+) real\s+([0-9.]+) user\s+([0-9.]+) sys\s*$", text)
    resident = re.search(r"(?m)^\s*([0-9]+)\s+maximum resident set size\s*$", text)
    return {
        "time_real_seconds": float(timing.group(1)) if timing else None,
        "user_seconds": float(timing.group(2)) if timing else None,
        "system_seconds": float(timing.group(3)) if timing else None,
        "time_peak_rss_bytes": int(resident.group(1)) if resident else None,
    }


def run_limited(
    command: list[str],
    cwd: Path,
    destination: Path,
    *,
    env: dict[str, str],
    wall_limit: int,
    memory_limit: int,
    poll_seconds: float = 1.0,
) -> dict[str, Any]:
    destination.mkdir()
    stdout_path = destination / "stdout.txt"
    stderr_path = destination / "stderr.txt"
    wrapped = ["/usr/bin/time", "-l", *command]
    write_json(
        destination / "command.json",
        {
            "command": command,
            "cwd": cwd.relative_to(ROOT).as_posix(),
            "wrapped_command": wrapped,
            "environment": {
                "PATH_prefix": env["PATH"].split(os.pathsep)[0],
                "STACK_ROOT": env["STACK_ROOT"],
            },
        },
    )
    started = time.perf_counter()
    reason: str | None = None
    peak_polled_rss = 0
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(
            wrapped,
            cwd=cwd,
            env=env,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
        while process.poll() is None:
            elapsed = time.perf_counter() - started
            peak_polled_rss = max(peak_polled_rss, process_tree_rss_bytes(process.pid))
            if peak_polled_rss > memory_limit:
                reason = "MEMORY_LIMIT"
                break
            if elapsed > wall_limit:
                reason = "WALL_TIMEOUT"
                break
            time.sleep(min(poll_seconds, max(0.01, wall_limit - elapsed)))
        if reason is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        return_code = process.wait()
    wall_seconds = time.perf_counter() - started
    metrics = parse_time_metrics(stderr_path)
    peak_rss = max(peak_polled_rss, metrics["time_peak_rss_bytes"] or 0)
    cpu_seconds = None
    if metrics["user_seconds"] is not None and metrics["system_seconds"] is not None:
        cpu_seconds = metrics["user_seconds"] + metrics["system_seconds"]
    if reason is not None:
        status = reason
    elif return_code == 0:
        status = "PASS"
    elif return_code < 0 or return_code >= 128:
        status = "CRASH"
    else:
        status = "REJECTED"
    result = {
        "status": status,
        "exit_code": return_code,
        "wall_seconds": round(wall_seconds, 6),
        "cpu_seconds": cpu_seconds,
        "peak_rss_bytes": peak_rss,
        "wall_limit_seconds": wall_limit,
        "memory_limit_bytes": memory_limit,
        "stdout_sha256": sha256(stdout_path),
        "stderr_sha256": sha256(stderr_path),
        **metrics,
    }
    write_json(destination / "resource.json", result)
    return result


def parse_checker_output(text: str) -> tuple[str, tuple[int, int] | None]:
    matches = re.findall(
        r"(?m)^\s*(Nothing|None|(?:Just|Some) \((-?\d+),(-?\d+)\))\s*$",
        text,
    )
    if len(matches) != 1:
        raise ValueError(f"expected exactly one checker result line, found {len(matches)}")
    whole, width, bound = matches[0]
    if whole in ("Nothing", "None"):
        return whole, None
    return whole, (int(width), int(bound))


def parse_checker_result(text: str) -> tuple[int, int] | None:
    return parse_checker_output(text)[1]


def require_successful_replay(stage: Path, resource_record: dict[str, Any], channels: int) -> tuple[int, int]:
    if resource_record["status"] != "PASS":
        status = "TIMEOUT" if resource_record["status"] == "WALL_TIMEOUT" else "FAIL"
        raise GateFailure(f"n={channels} official command ended as {resource_record['status']}", status)
    result = parse_checker_result((stage / "stdout.txt").read_text(encoding="utf-8", errors="replace"))
    if result != EXPECTED_RESULTS[channels]:
        raise GateFailure(
            f"n={channels} checker result mismatch: expected {EXPECTED_RESULTS[channels]}, got {result}",
            "INVALID",
        )
    return result


def corrupt_root_bound(source: Path, destination: Path) -> dict[str, Any]:
    data = bytearray(source.read_bytes())
    if len(data) < 16:
        raise ValueError("proof is too short")
    step_count = struct.unpack_from("<I", data, 0)[0]
    if step_count < 1 or 4 + 12 * step_count > len(data):
        raise ValueError("invalid proof header")
    header_offset = 4 + 12 * (step_count - 1)
    step_offset, step_length = struct.unpack_from("<QI", data, header_offset)
    bound_offset = step_offset + 1
    if step_length < 2 or bound_offset >= len(data):
        raise ValueError("invalid root proof-step bounds")
    original = data[bound_offset]
    replacement = 255 if original != 255 else 254
    data[bound_offset] = replacement
    destination.write_bytes(data)
    return {
        "method": "replace root proof-step bound byte with an impossible high value",
        "step_count": step_count,
        "root_step_offset": step_offset,
        "root_step_length": step_length,
        "changed_file_offset": bound_offset,
        "original_byte": original,
        "replacement_byte": replacement,
        "source_sha256": sha256(source),
        "corrupted_sha256": sha256(destination),
        "size_bytes": destination.stat().st_size,
    }


def toolchain_environment(manifest: dict[str, Any]) -> dict[str, str]:
    wrapper = ROOT / manifest["stack_wrapper"]["path"]
    env = os.environ.copy()
    env["PATH"] = f"{wrapper.parent}{os.pathsep}{env['PATH']}"
    env["STACK_ROOT"] = str(ROOT / manifest["stack_root"])
    return env


def preflight() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    if Path.cwd().resolve() != ROOT:
        raise RuntimeError(f"cwd must be exactly {ROOT}")
    if run_text(["git", "branch", "--show-current"]) != "goal/s13-baseline":
        raise RuntimeError("wrong branch")
    dirty = run_text(["git", "status", "--porcelain", "--untracked-files=all"])
    if dirty:
        raise RuntimeError(f"scored configuration is dirty:\n{dirty}")
    checked = run_text([sys.executable, "tools/evidence_check.py"], check=False)
    if "verified" not in checked:
        raise RuntimeError(f"evidence prerequisite failed:\n{checked}")
    if sha256(B2_MANIFEST) != B2_MANIFEST_SHA256:
        raise RuntimeError("B2 prerequisite manifest hash mismatch")
    if json.loads(B2_MANIFEST.read_text(encoding="utf-8"))["status"] != "PASS":
        raise RuntimeError("B2 prerequisite is not PASS")

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    budgets = json.loads(BUDGETS_PATH.read_text(encoding="utf-8"))
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    toolchain = setup_sortnetopt.verify_active()
    certificate = fetch_harder_certificate.verify_active()
    if toolchain is None:
        raise RuntimeError("Harder toolchain is missing or hash-mismatched; run make setup")
    if certificate is None:
        raise RuntimeError("published n=11 certificate is missing or hash-mismatched; run make setup")
    if toolchain["upstream"]["commit"] != config["commit"]:
        raise RuntimeError("active Harder toolchain does not match frozen commit")
    if certificate["uncompressed_sha256"] != config["certificate_uncompressed_sha256"]:
        raise RuntimeError("active certificate does not match frozen SHA-256")
    return config, budgets, sources, toolchain, certificate


def generated_artifacts(directory: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": path.relative_to(directory).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    ]


def prepare_official_datadir(path: Path) -> Path:
    """Make the leaf resolvable before the upstream script's early realpath call."""
    path.mkdir(parents=True, exist_ok=False)
    if not path.is_dir() or not path.resolve().is_absolute():
        raise RuntimeError(f"failed to prepare official data directory: {path}")
    return path


def prior_scored_wall_seconds() -> float:
    total = 0.0
    for gate in ("b1", "b2", "b3"):
        for path in (ROOT / "evidence" / gate).glob("*/manifest.json"):
            manifest = json.loads(path.read_text(encoding="utf-8"))
            total += float(manifest["wall_seconds"])
    return total


def main() -> int:
    try:
        config, budgets, sources, toolchain, certificate_cache = preflight()
    except Exception as exc:
        print(f"B3 preflight failed: {exc}", file=sys.stderr)
        return 2

    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    started_cpu = time.process_time()
    run_id = started.strftime("b3-%Y%m%dT%H%M%SZ")
    out = ROOT / "evidence/b3" / run_id
    out.mkdir(parents=True, exist_ok=False)
    work = WORK_ROOT / run_id
    work.mkdir(parents=True, exist_ok=False)
    status = "FAIL"
    error: str | None = None
    log_lines = [
        "B3 falsifiable gate: official n=9 workflow, exact n=11 replay, and safe corrupted-certificate rejection must all pass."
    ]
    stderr_lines: list[str] = []
    resources: list[dict[str, Any]] = []
    summary: dict[str, Any] = {"status": "FAIL"}
    config_hash = "0" * 64
    env = toolchain_environment(toolchain)

    try:
        frozen_paths = [
            CONFIG_PATH,
            BUDGETS_PATH,
            SOURCES_PATH,
            ROOT / "docs/b3-execution.md",
            ROOT / "docs/b3-setup-audit.md",
            ROOT / "tools/patches/sortnetopt-macos-proc.patch",
            ROOT / "tools/setup_sortnetopt.py",
            ROOT / "tools/fetch_harder_certificate.py",
            ROOT / "tools/b3_gate.py",
            ROOT / "tests/test_b3_exact.py",
            B2_MANIFEST,
        ]
        config_hash = aggregate_hash(frozen_paths)
        write_json(
            out / "config-snapshot.json",
            {
                "aggregate_sha256": config_hash,
                "files": [
                    {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)}
                    for path in sorted(frozen_paths)
                ],
                "config": config,
                "budgets": {
                    "exact_n9": budgets["exact_n9"],
                    "certificate_n11": budgets["certificate_n11"],
                    "total_after_setup": budgets["total_after_setup"],
                },
            },
        )
        shutil.copyfile(CONFIG_PATH, out / "frozen-b3-config.json")
        write_json(out / "toolchain-build-manifest.json", toolchain)
        cargo_lock = ROOT / toolchain["generated_cargo_lock"]["path"]
        shutil.copyfile(cargo_lock, out / "generated-Cargo.lock")
        write_json(out / "certificate-cache-manifest.json", certificate_cache)
        write_json(
            out / "external-source-reference.json",
            {
                "sortnetopt": toolchain["upstream"],
                "sortnetopt_portability_patch": toolchain["portability_patch"],
                "sortnetopt_generated_cargo_lock": toolchain["generated_cargo_lock"],
                "certificate": {
                    "url": certificate_cache["url"],
                    "doi": certificate_cache["doi"],
                    "compressed_size_bytes": certificate_cache["compressed_size_bytes"],
                    "compressed_md5": certificate_cache["compressed_md5"],
                    "uncompressed_size_bytes": certificate_cache["uncompressed_size_bytes"],
                    "uncompressed_sha256": certificate_cache["uncompressed_sha256"],
                    "bytes_committed": False,
                },
            },
        )

        runtime_source = ROOT / toolchain["runtime_source_path"]
        n9_data = prepare_official_datadir(work / "n9-data")
        n9_stage = out / "n9-workflow"
        n9_command = ["bash", "search_and_verify.sh", "9", str(n9_data)]
        n9_resource = run_limited(
            n9_command,
            runtime_source,
            n9_stage,
            env=env,
            wall_limit=budgets["exact_n9"]["wall_seconds"],
            memory_limit=budgets["exact_n9"]["peak_memory_bytes"],
            poll_seconds=0.25,
        )
        resources.append(n9_resource)
        n9_result = require_successful_replay(n9_stage, n9_resource, 9)
        n9_output_line = parse_checker_output(
            (n9_stage / "stdout.txt").read_text(encoding="utf-8", errors="replace")
        )[0]
        proof = n9_data / "_search_9/proof.bin"
        if not proof.is_file():
            raise GateFailure("official n=9 workflow produced no proof.bin", "INVALID")
        n9_proof = n9_stage / "proof.bin"
        shutil.copyfile(proof, n9_proof)
        n9_artifacts = generated_artifacts(n9_data)
        write_json(n9_stage / "generated-artifacts.json", n9_artifacts)
        write_json(
            n9_stage / "result.json",
            {
                "status": "PASS",
                "checker_result": list(n9_result),
                "checker_output_line": n9_output_line,
                "local_statement": "The replayed generated certificate establishes the size lower bound S(9) >= 25.",
                "truth_label": "LOCALLY_REPRODUCED",
                "proof_sha256": sha256(n9_proof),
                "proof_size_bytes": n9_proof.stat().st_size,
                "generated_artifact_count": len(n9_artifacts),
            },
        )
        log_lines.append(
            f"PASS: official n=9 workflow returned {n9_output_line} in {n9_resource['wall_seconds']} seconds."
        )

        negative_stage = out / "corruption-rejection"
        negative_stage.mkdir()
        corrupt_proof = negative_stage / "proof-corrupt-root-bound.bin"
        mutation = corrupt_root_bound(n9_proof, corrupt_proof)
        write_json(negative_stage / "mutation.json", mutation)
        negative_run = negative_stage / "checker"
        negative_command = ["bash", "verify_proof_cert.sh", str(corrupt_proof)]
        negative_resource = run_limited(
            negative_command,
            runtime_source,
            negative_run,
            env=env,
            wall_limit=min(120, budgets["exact_n9"]["wall_seconds"]),
            memory_limit=budgets["exact_n9"]["peak_memory_bytes"],
            poll_seconds=0.25,
        )
        resources.append(negative_resource)
        if negative_resource["status"] != "PASS":
            raise GateFailure(
                f"corrupted certificate checker did not reject cleanly: {negative_resource['status']}",
                "INVALID",
            )
        negative_output_line, negative_result = parse_checker_output(
            (negative_run / "stdout.txt").read_text(encoding="utf-8", errors="replace")
        )
        if negative_result is not None:
            raise GateFailure(f"corrupted certificate was not rejected: {negative_result}", "INVALID")
        write_json(
            negative_stage / "result.json",
            {
                "status": "PASS",
                "checker_result": None,
                "checker_output_line": negative_output_line,
                "safe_rejection": True,
                "truth_label": "LOCALLY_REPRODUCED",
            },
        )
        log_lines.append(
            f"PASS: well-formed n=9 certificate corruption returned {negative_output_line}."
        )

        certificate_path = ROOT / certificate_cache["uncompressed_path"]
        before_sha = sha256(certificate_path)
        if before_sha != config["certificate_uncompressed_sha256"]:
            raise GateFailure("n=11 certificate changed before replay", "INVALID")
        n11_stage = out / "n11-replay"
        n11_command = ["bash", "verify_proof_cert.sh", str(certificate_path)]
        n11_resource = run_limited(
            n11_command,
            runtime_source,
            n11_stage,
            env=env,
            wall_limit=budgets["certificate_n11"]["wall_seconds"],
            memory_limit=budgets["certificate_n11"]["peak_memory_bytes"],
            poll_seconds=1.0,
        )
        resources.append(n11_resource)
        n11_result = require_successful_replay(n11_stage, n11_resource, 11)
        n11_output_line = parse_checker_output(
            (n11_stage / "stdout.txt").read_text(encoding="utf-8", errors="replace")
        )[0]
        after_sha = sha256(certificate_path)
        if after_sha != before_sha:
            raise GateFailure("n=11 certificate changed during replay", "INVALID")
        write_json(
            n11_stage / "result.json",
            {
                "status": "PASS",
                "checker_result": list(n11_result),
                "checker_output_line": n11_output_line,
                "certificate_sha256_before": before_sha,
                "certificate_sha256_after": after_sha,
                "certificate_size_bytes": certificate_path.stat().st_size,
                "local_statement": "The published certificate replay establishes the size lower bound S(11) >= 35.",
                "truth_label": "LOCALLY_REPRODUCED",
            },
        )
        log_lines.append(
            f"PASS: exact published n=11 certificate returned {n11_output_line} in {n11_resource['wall_seconds']} seconds."
        )

        elapsed = time.perf_counter() - started_perf
        prior_wall = prior_scored_wall_seconds()
        total_wall = prior_wall + elapsed
        if total_wall > budgets["total_after_setup"]["wall_seconds"]:
            raise GateFailure(
                f"total scored baseline wall budget exceeded: {total_wall} seconds",
                "TIMEOUT",
            )
        summary = {
            "status": "PASS",
            "n9": {
                "checker_result": list(n9_result),
                "checker_output_line": n9_output_line,
                "truth_label": "LOCALLY_REPRODUCED",
                "establishes": "S(9) >= 25",
            },
            "corruption_rejection": {
                "checker_result": None,
                "checker_output_line": negative_output_line,
                "safe_rejection": True,
                "truth_label": "LOCALLY_REPRODUCED",
            },
            "n11": {
                "checker_result": list(n11_result),
                "checker_output_line": n11_output_line,
                "truth_label": "LOCALLY_REPRODUCED",
                "establishes": "S(11) >= 35",
            },
            "s11_exact_equality": {
                "statement": "S(11)=35",
                "truth_label": "PUBLISHED",
                "note": "The local replay establishes the lower bound; the matching construction was not separately replayed in B3.",
            },
            "s12": {
                "statement": "S(12)=39",
                "truth_label": "PUBLISHED",
                "note": "Paper-derived consequence; no separate n=12 certificate was replayed.",
            },
            "prior_scored_wall_seconds": round(prior_wall, 6),
            "total_scored_wall_seconds_through_b3": round(total_wall, 6),
            "total_wall_limit_seconds": budgets["total_after_setup"]["wall_seconds"],
        }
        status = "PASS"
    except GateFailure as exc:
        status = exc.status
        error = str(exc)
        log_lines.append(f"{status}: {error}")
    except Exception as exc:
        status = "FAIL"
        error = str(exc)
        log_lines.append(f"FAIL: {error}")

    summary["status"] = status
    if error is not None:
        summary["error"] = error
    write_json(out / "summary.json", summary)
    self_usage = resource.getrusage(resource.RUSAGE_SELF)
    child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    multiplier = 1 if sys.platform == "darwin" else 1024
    measured_peak = max([0, *(item.get("peak_rss_bytes") or 0 for item in resources)])
    peak_rss = max(int(self_usage.ru_maxrss * multiplier), int(child_usage.ru_maxrss * multiplier), measured_peak)
    measured_cpu = sum(item.get("cpu_seconds") or 0 for item in resources)
    ended = datetime.now(timezone.utc)
    manifest: dict[str, Any] = {
        "schema_version": "s13-evidence-manifest/v1",
        "run_id": run_id,
        "gate": "B3",
        "source_commit": run_text(["git", "rev-parse", "HEAD"]),
        "dirty_at_start": False,
        "command": [sys.executable, "tools/b3_gate.py"],
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "wall_seconds": round(time.perf_counter() - started_perf, 6),
        "cpu_seconds": round(time.process_time() - started_cpu + measured_cpu, 6),
        "peak_rss_bytes": peak_rss,
        "threads": int(sysctl("hw.logicalcpu")),
        "host": host_record(),
        "config_sha256": config_hash,
        "status": status,
    }
    if error is not None:
        manifest["error"] = error
    write_json(out / "manifest.json", manifest)
    (out / "command.txt").write_text(f"{sys.executable} tools/b3_gate.py\n", encoding="utf-8")
    (out / "stdout.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    (out / "stderr.txt").write_text("\n".join(stderr_lines) + ("\n" if stderr_lines else ""), encoding="utf-8")
    write_checksums(out)
    for line in log_lines:
        print(line)
    print(f"evidence: {out.relative_to(ROOT)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
