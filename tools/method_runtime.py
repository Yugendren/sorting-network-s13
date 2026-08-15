#!/usr/bin/env python3
"""Shared deterministic runtime helpers for Mericanii experiment gates."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from typing import Any
import xml.etree.ElementTree as ET


ROOT = Path("/Users/yugendren/experiments/sorting_network_s13")


class VerificationFailure(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_checksums(directory: Path) -> None:
    files = sorted(
        path for path in directory.rglob("*")
        if path.is_file() and path.name != "checksums.sha256"
    )
    lines = [f"{sha256(path)}  {path.relative_to(directory).as_posix()}" for path in files]
    (directory / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def aggregate_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(dict.fromkeys(paths)):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256(path)))
        digest.update(b"\n")
    return digest.hexdigest()


def candidate_bytes(channels: int, comparators: list[tuple[int, int]], source: str) -> bytes:
    lines = [
        "sorting-network-v1",
        f"channels {channels}",
        f"declared_count {len(comparators)}",
        "layer_count -",
        f"source {source}",
        "truth_label LOCALLY_REPRODUCED",
        "comparators_begin",
        *(f"{lower} {upper}" for lower, upper in comparators),
        "comparators_end",
    ]
    prefix = ("\n".join(lines) + "\n").encode("utf-8")
    return prefix + f"sha256 {hashlib.sha256(prefix).hexdigest()}\n".encode("utf-8")


def parse_candidate(path: Path) -> list[tuple[int, int]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    try:
        start = lines.index("comparators_begin") + 1
        end = lines.index("comparators_end")
    except ValueError as exc:
        raise RuntimeError(f"candidate markers missing: {path}") from exc
    result: list[tuple[int, int]] = []
    for line in lines[start:end]:
        lower, upper = (int(value) for value in line.split())
        result.append((lower, upper))
    return result


def parse_milestone(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rb") as stream:
        root = ET.parse(stream).getroot()
    genotype = root.find("./Vivarium/HallOfFame/Member/Individual/Genotype")
    fitness_node = root.find("./Vivarium/HallOfFame/Member/Individual/Fitness")
    processed_node = root.find("./Vivarium/Stats/Item[@key='total-processed']")
    if genotype is None or fitness_node is None or processed_node is None:
        raise RuntimeError("milestone lacks hall of fame, fitness, or processed count")
    comparator_node = genotype.find("Comparators")
    if comparator_node is None:
        raise RuntimeError("milestone hall of fame lacks comparator data")
    text = (comparator_node.text or "").strip()
    values = [] if not text else [int(item) for item in text.split(";")]
    if len(values) % 2 or int(comparator_node.attrib["size"]) != len(values):
        raise RuntimeError("milestone comparator vector size mismatch")
    channels = int(genotype.attrib["numInputs"])
    comparators = [(values[index], values[index + 1]) for index in range(0, len(values), 2)]
    if any(not (0 <= lower < upper < channels) for lower, upper in comparators):
        raise RuntimeError("milestone contains a noncanonical comparator")
    fitness = float((fitness_node.text or "").strip())
    if fitness != -float(len(comparators)):
        raise RuntimeError("milestone fitness does not equal negative comparator count")
    return {
        "generation": int(root.attrib["generation"]),
        "channels": channels,
        "comparators": comparators,
        "comparator_count": len(comparators),
        "fitness": fitness,
        "evaluations": int((processed_node.text or "").strip()),
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
        if len(parts) == 3:
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
    work_dir: Path,
    *,
    cpu_limit: int,
    wall_limit: float,
    memory_limit: int,
    environment_overrides: dict[str, str] | None = None,
    poll_seconds: float = 0.25,
) -> dict[str, Any]:
    stdout_path = work_dir / "stdout.txt"
    stderr_path = work_dir / "stderr.txt"
    wrapped = [
        "/usr/bin/time",
        "-l",
        sys.executable,
        str(ROOT / "tools/run_with_limits.py"),
        "--cpu-seconds",
        str(cpu_limit),
        *command,
    ]
    overrides = dict(environment_overrides or {})
    write_json(
        work_dir / "command.json",
        {
            "command": command,
            "wrapped_command": wrapped,
            "environment_overrides": overrides,
        },
    )
    env = os.environ.copy()
    env.update(
        {
            "GOMAXPROCS": "1",
            "OMP_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
            "LC_ALL": "C",
            "TZ": "UTC",
        }
    )
    env.update(overrides)
    started = time.perf_counter()
    reason: str | None = None
    peak_polled_rss = 0
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(
            wrapped,
            cwd=work_dir,
            env=env,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
        while process.poll() is None:
            elapsed = time.perf_counter() - started
            rss = process_tree_rss_bytes(process.pid)
            peak_polled_rss = max(peak_polled_rss, rss)
            if rss > memory_limit:
                reason = "MEMORY_LIMIT"
                break
            if elapsed > wall_limit:
                reason = "WALL_TIMEOUT"
                break
            time.sleep(min(poll_seconds, max(0.01, wall_limit - elapsed)))
        if reason is not None and process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
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
    elif return_code in (128 + signal.SIGXCPU, 128 + signal.SIGKILL, -signal.SIGXCPU, -signal.SIGKILL):
        status = "CPU_TIMEOUT"
    else:
        status = "CRASH"
    result = {
        "status": status,
        "exit_code": return_code,
        "wall_seconds": round(wall_seconds, 6),
        "cpu_seconds": cpu_seconds,
        "peak_rss_bytes": peak_rss,
        "cpu_limit_seconds": cpu_limit,
        "wall_limit_seconds": wall_limit,
        "memory_limit_bytes": memory_limit,
        "stdout_sha256": sha256(stdout_path),
        "stderr_sha256": sha256(stderr_path),
        **metrics,
    }
    write_json(work_dir / "resource.json", result)
    return result


def verify_candidate(path: Path, verifier_b: Path, destination: Path) -> dict[str, Any]:
    commands = {
        "a": [sys.executable, str(ROOT / "src/verifier_a.py"), "--expected-channels", "13", str(path)],
        "b": [str(verifier_b), "--expected-channels", "13", str(path)],
    }
    reports: dict[str, dict[str, Any]] = {}
    for name, command in commands.items():
        completed = subprocess.run(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        (destination / f"verifier-{name}.json").write_bytes(completed.stdout)
        (destination / f"verifier-{name}.stderr").write_bytes(completed.stderr)
        if completed.stderr:
            raise VerificationFailure(f"verifier {name.upper()} wrote stderr for {path.name}")
        try:
            report = json.loads(completed.stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise VerificationFailure(f"verifier {name.upper()} emitted invalid JSON") from exc
        reports[name] = report
        if completed.returncode != 0 or report.get("verdict") != "ACCEPT":
            raise VerificationFailure(f"verifier {name.upper()} rejected {path.name}")
    for field in ("artifact_sha256", "candidate_checksum", "channels", "comparators", "counterexample"):
        if reports["a"].get(field) != reports["b"].get(field):
            raise VerificationFailure(f"verifier disagreement on {field} for {path.name}")
    return {
        "artifact_sha256": reports["a"]["artifact_sha256"],
        "candidate_checksum": reports["a"]["candidate_checksum"],
        "comparators": reports["a"]["comparators"],
        "verifier_a": "ACCEPT",
        "verifier_b": "ACCEPT",
        "verifier_a_report_sha256": sha256(destination / "verifier-a.json"),
        "verifier_b_report_sha256": sha256(destination / "verifier-b.json"),
    }


def senso_command(binary: Path, source: Path, *, seed: int, milestone_prefix: str = "milestone") -> list[str]:
    return [
        str(binary),
        f"-OBconf={source / 'experiments/sorting/sorting/beagle.conf'}",
        "-OBec.pop.size=200",
        f"-OBec.rand.seed={seed}",
        "-OBec.term.maxgen=500",
        "-OBsn.init.numinputs=13",
        "-OBsn.init.filter=0:21",
        "-OBsn.init.initfuncs=1",
        "-OBsn.eval.compfit=1",
        "-OBsn.estimate.frac=0.5",
        "-OBsn.estimate.prob=0.5",
        "-OBsn.estimate.gtrun=1",
        "-OBsn.mutation.mksym=1",
        "-OBms.write.interval=0",
        "-OBms.write.compress=1",
        f"-OBms.write.prefix={milestone_prefix}",
        "-OBlg.console.level=2",
        "-OBlg.file.level=3",
        "-OBlg.file.name=beagle.log",
    ]
