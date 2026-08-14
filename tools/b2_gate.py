#!/usr/bin/env python3
"""Run the frozen B2 random, greedy, and 20-seed SENSO baselines."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import resource
import shutil
import signal
import subprocess
import sys
import time
from typing import Any
import xml.etree.ElementTree as ET


ROOT = Path("/Users/yugendren/experiments/sorting_network_s13")
CONFIG_PATH = ROOT / "config/frozen/b2-execution.json"
BUILD_ROOT = ROOT / ".build/b2"


class VerificationFailure(RuntimeError):
    pass


class FrontierArtifact(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aggregate_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(dict.fromkeys(paths)):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256(path)))
        digest.update(b"\n")
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_checksums(directory: Path) -> None:
    files = sorted(path for path in directory.rglob("*") if path.is_file() and path.name != "checksums.sha256")
    lines = [f"{sha256(path)}  {path.relative_to(directory).as_posix()}" for path in files]
    (directory / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_text(command: list[str], *, check: bool = True) -> str:
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
    prefix = ("\n".join(lines) + "\n").encode()
    return prefix + f"sha256 {hashlib.sha256(prefix).hexdigest()}\n".encode()


def parse_milestone(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rb") as stream:
        root = ET.parse(stream).getroot()
    genotype = root.find("./Vivarium/HallOfFame/Member/Individual/Genotype")
    fitness_node = root.find("./Vivarium/HallOfFame/Member/Individual/Fitness")
    processed_node = root.find("./Vivarium/Stats/Item[@key='total-processed']")
    if genotype is None or fitness_node is None or processed_node is None:
        raise RuntimeError("milestone lacks vivarium hall-of-fame or processed count")
    comparator_node = genotype.find("Comparators")
    if comparator_node is None:
        raise RuntimeError("milestone hall-of-fame lacks comparator data")
    text = (comparator_node.text or "").strip()
    values = [] if not text else [int(item) for item in text.split(";")]
    if len(values) % 2 != 0 or int(comparator_node.attrib["size"]) != len(values):
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
    work_dir: Path,
    *,
    cpu_limit: int,
    wall_limit: float,
    memory_limit: int,
    poll_seconds: float,
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
    write_json(work_dir / "command.json", {"command": command, "wrapped_command": wrapped})
    env = os.environ.copy()
    env.update({"GOMAXPROCS": "1", "OMP_NUM_THREADS": "1", "VECLIB_MAXIMUM_THREADS": "1"})
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
            raise VerificationFailure(f"verifier {name.upper()} rejected returned candidate {path.name}")
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


def load_active_senso(config: dict[str, Any]) -> tuple[dict[str, Any], Path, Path, str]:
    active_path = ROOT / ".build/senso/active.json"
    if not active_path.is_file():
        raise RuntimeError("missing active SENSO build; run make setup")
    active = json.loads(active_path.read_text(encoding="utf-8"))
    manifest_path = ROOT / active["manifest_path"]
    if sha256(manifest_path) != active["manifest_sha256"]:
        raise RuntimeError("active SENSO build manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    binary = ROOT / manifest["binary_path"]
    source = ROOT / manifest["source_path"]
    if manifest["status"] != "PASS" or sha256(binary) != manifest["binary_sha256"]:
        raise RuntimeError("active SENSO binary failed manifest verification")
    external = config["external_senso"]
    if manifest["archive_sha256"] != external["archive_sha256"] or manifest["patch_sha256"] != external["patch_sha256"]:
        raise RuntimeError("active SENSO build does not match frozen archive/patch")
    return manifest, binary, source, active["manifest_sha256"]


def prerequisite_check(config: dict[str, Any]) -> None:
    checked = subprocess.run(
        [sys.executable, "tools/evidence_check.py"], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    if checked.returncode != 0:
        raise RuntimeError(f"evidence prerequisite failed:\n{checked.stdout}")
    prerequisite = config["b1_prerequisite"]
    path = ROOT / prerequisite["manifest_path"]
    if sha256(path) != prerequisite["manifest_sha256"]:
        raise RuntimeError("B1 prerequisite manifest hash mismatch")
    if json.loads(path.read_text(encoding="utf-8"))["status"] != "PASS":
        raise RuntimeError("B1 prerequisite is not PASS")
    for name, parent in config["parents"].items():
        if not name.endswith("_path"):
            continue
        hash_name = name.removesuffix("_path") + "_sha256"
        if sha256(ROOT / parent) != config["parents"][hash_name]:
            raise RuntimeError(f"frozen B2 parent mismatch: {parent}")


def senso_command(binary: Path, source: Path, *, seed: int, population: int, generations: int) -> list[str]:
    return [
        str(binary),
        f"-OBconf={source / 'experiments/sorting/sorting/beagle.conf'}",
        f"-OBec.pop.size={population}",
        f"-OBec.rand.seed={seed}",
        f"-OBec.term.maxgen={generations}",
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
        "-OBms.write.prefix=milestone",
        "-OBlg.console.level=2",
        "-OBlg.file.level=3",
        "-OBlg.file.name=beagle.log",
    ]


def finalize_candidate_result(
    result: dict[str, Any],
    comparators: list[tuple[int, int]],
    source: str,
    seed_dir: Path,
    verifier_b: Path,
) -> None:
    candidate = seed_dir / "candidate.sortnet"
    candidate.write_bytes(candidate_bytes(13, comparators, source))
    result.update(
        {
            "best_size": len(comparators),
            "candidate_path": candidate.relative_to(seed_dir.parents[1]).as_posix(),
        }
    )
    result["verification"] = verify_candidate(candidate, verifier_b, seed_dir)
    if len(comparators) < 45:
        result["status"] = "UNEXPECTED_FRONTIER"
        write_json(seed_dir / "result.json", result)
        raise FrontierArtifact(
            f"{result['baseline']} seed {result['seed']} returned verified {len(comparators)}-comparator candidate"
        )


def skipped_result(baseline: str, seed: int, seed_dir: Path, reason: str) -> dict[str, Any]:
    (seed_dir / "stdout.txt").write_text("", encoding="utf-8")
    (seed_dir / "stderr.txt").write_text(reason + "\n", encoding="utf-8")
    write_json(seed_dir / "command.json", {"command": None, "reason": reason})
    resource_record = {
        "status": "AGGREGATE_TIMEOUT",
        "exit_code": None,
        "wall_seconds": 0,
        "cpu_seconds": 0,
        "peak_rss_bytes": 0,
    }
    write_json(seed_dir / "resource.json", resource_record)
    result = {"baseline": baseline, "seed": seed, "status": "AGGREGATE_TIMEOUT", "resource": resource_record}
    write_json(seed_dir / "result.json", result)
    return result


def run_random_stage(
    out: Path,
    seeds: list[int],
    config: dict[str, Any],
    budgets: dict[str, Any],
    verifier_b: Path,
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stage = out / "random"
    stage.mkdir()
    started = time.perf_counter()
    deadline = started + budgets["transparent_baselines"]["random_aggregate_wall_seconds"]
    random_config = config["random"]
    for seed in seeds:
        seed_dir = stage / f"seed-{seed:02d}"
        seed_dir.mkdir()
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            results.append(skipped_result("random", seed, seed_dir, "random aggregate wall cap reached"))
            continue
        command = [
            sys.executable,
            str(ROOT / random_config["implementation"]),
            "--channels", "13",
            "--seed", str(seed),
            "--trials", str(random_config["trials_per_seed"]),
            "--max-comparators", str(random_config["max_comparators_per_trial"]),
        ]
        resource_record = run_limited(
            command, seed_dir,
            cpu_limit=max(1, min(30, int(remaining))),
            wall_limit=max(1, min(30, remaining)),
            memory_limit=1024**3,
            poll_seconds=config["resource_enforcement"]["memory_poll_seconds"],
        )
        result: dict[str, Any] = {"baseline": "random", "seed": seed, "status": resource_record["status"], "resource": resource_record}
        if resource_record["status"] == "PASS":
            try:
                report = json.loads((seed_dir / "stdout.txt").read_text(encoding="utf-8"))
                write_json(seed_dir / "random-report.json", report)
                result.update(
                    {
                        "evaluations": report["evaluations"],
                        "successful_trials": report["successful_trials"],
                        "trial_sizes": report["trial_sizes"],
                    }
                )
                if report["best_comparators"] is not None:
                    comparators = [tuple(pair) for pair in report["best_comparators"]]
                    try:
                        finalize_candidate_result(result, comparators, f"random-baseline-seed-{seed}", seed_dir, verifier_b)
                    except FrontierArtifact:
                        results.append(result)
                        raise
                    except VerificationFailure as exc:
                        result["status"] = "INVALID"
                        result["error"] = str(exc)
                        write_json(seed_dir / "result.json", result)
                        results.append(result)
                        raise
            except (FrontierArtifact, VerificationFailure):
                raise
            except Exception as exc:
                result["status"] = "OUTPUT_INVALID"
                result["error"] = str(exc)
        write_json(seed_dir / "result.json", result)
        results.append(result)
    return results


def run_senso_stage(
    baseline: str,
    out: Path,
    seeds: list[int],
    config: dict[str, Any],
    budgets: dict[str, Any],
    verifier_b: Path,
    binary: Path,
    source: Path,
    *,
    population: int,
    generations: int,
    aggregate_wall: int,
    per_seed_wall: int,
    per_seed_cpu: int,
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stage = out / baseline
    stage.mkdir()
    deadline = time.perf_counter() + aggregate_wall
    memory_limit = budgets["constructive"]["peak_memory_bytes"]
    for seed in seeds:
        seed_dir = stage / f"seed-{seed:02d}"
        seed_dir.mkdir()
        remaining = deadline - time.perf_counter()
        if remaining <= 0:
            results.append(skipped_result(baseline, seed, seed_dir, f"{baseline} aggregate wall cap reached"))
            continue
        command = senso_command(binary, source, seed=seed, population=population, generations=generations)
        resource_record = run_limited(
            command, seed_dir,
            cpu_limit=per_seed_cpu,
            wall_limit=max(1, min(per_seed_wall, remaining)),
            memory_limit=memory_limit,
            poll_seconds=config["resource_enforcement"]["memory_poll_seconds"],
        )
        result: dict[str, Any] = {"baseline": baseline, "seed": seed, "status": resource_record["status"], "resource": resource_record}
        if resource_record["status"] == "PASS":
            try:
                milestones = sorted(seed_dir.glob("milestone_g*.obm.gz"))
                if len(milestones) != 1:
                    raise RuntimeError(f"expected exactly one final milestone, found {len(milestones)}")
                parsed = parse_milestone(milestones[0])
                expected_evaluations = population + generations * (population // 2)
                if parsed["generation"] != generations or parsed["evaluations"] != expected_evaluations:
                    raise RuntimeError(
                        f"milestone generation/evaluations mismatch: {parsed['generation']}/{parsed['evaluations']}"
                    )
                result.update(
                    {
                        "generation": parsed["generation"],
                        "evaluations": parsed["evaluations"],
                        "milestone_sha256": sha256(milestones[0]),
                        "milestone_size_bytes": milestones[0].stat().st_size,
                    }
                )
                try:
                    finalize_candidate_result(
                        result,
                        parsed["comparators"],
                        f"{baseline}-variant2-seed-{seed}-generation-{generations}",
                        seed_dir,
                        verifier_b,
                    )
                except FrontierArtifact:
                    results.append(result)
                    raise
                except VerificationFailure as exc:
                    result["status"] = "INVALID"
                    result["error"] = str(exc)
                    write_json(seed_dir / "result.json", result)
                    results.append(result)
                    raise
            except (FrontierArtifact, VerificationFailure):
                raise
            except Exception as exc:
                result["status"] = "OUTPUT_INVALID"
                result["error"] = str(exc)
        write_json(seed_dir / "result.json", result)
        results.append(result)
    return results


def summarize(results: list[dict[str, Any]], seeds: list[int]) -> dict[str, Any]:
    sizes = [result.get("best_size") for result in results if result.get("best_size") is not None]
    status_counts = Counter(result["status"] for result in results)
    return {
        "reported_seed_count": len(results),
        "expected_seed_count": len(seeds),
        "all_seeds_reported": len(results) == len(seeds) and [result["seed"] for result in results] == seeds,
        "status_counts": dict(sorted(status_counts.items())),
        "best_size": min(sizes) if sizes else None,
        "size_distribution": {str(size): sizes.count(size) for size in sorted(set(sizes))},
        "verified_candidate_count": sum("verification" in result for result in results),
        "total_evaluations": sum(result.get("evaluations", 0) for result in results),
        "total_cpu_seconds": round(sum(result["resource"].get("cpu_seconds") or 0 for result in results), 6),
        "total_wall_seconds": round(sum(result["resource"].get("wall_seconds") or 0 for result in results), 6),
        "peak_rss_bytes": max((result["resource"].get("peak_rss_bytes") or 0 for result in results), default=0),
    }


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        print(f"B2 preflight failed: cwd must be exactly {ROOT}", file=sys.stderr)
        return 2
    if run_text(["git", "branch", "--show-current"]) != "goal/s13-baseline":
        print("B2 preflight failed: wrong branch", file=sys.stderr)
        return 2
    dirty = run_text(["git", "status", "--porcelain", "--untracked-files=all"])
    if dirty:
        print("B2 preflight failed: scored configuration is dirty", file=sys.stderr)
        print(dirty, file=sys.stderr)
        return 2
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        prerequisite_check(config)
        build_manifest, senso_binary, senso_source, build_manifest_sha = load_active_senso(config)
    except Exception as exc:
        print(f"B2 preflight failed: {exc}", file=sys.stderr)
        return 2

    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    started_cpu = time.process_time()
    run_id = started.strftime("b2-%Y%m%dT%H%M%SZ")
    out = ROOT / "evidence/b2" / run_id
    out.mkdir(parents=True, exist_ok=False)
    status = "FAIL"
    error: str | None = None
    config_hash = "0" * 64
    log_lines = ["B2 falsifiable gate: report all 20 seeds and reproduce a dual-verified 45-comparator SENSO baseline."]
    stderr_lines: list[str] = []
    all_results: dict[str, list[dict[str, Any]]] = {"random": [], "greedy": [], "senso": []}
    summary: dict[str, Any] = {}

    try:
        budgets = json.loads((ROOT / config["parents"]["budgets_path"]).read_text(encoding="utf-8"))
        seeds = json.loads((ROOT / config["parents"]["seeds_path"]).read_text(encoding="utf-8"))["seeds"]
        if len(seeds) != 20:
            raise RuntimeError("B2 requires exactly 20 frozen seeds")
        frozen_paths = [
            CONFIG_PATH,
            ROOT / config["parents"]["b2_senso_path"],
            ROOT / config["parents"]["budgets_path"],
            ROOT / config["parents"]["seeds_path"],
            ROOT / config["external_senso"]["patch_path"],
            ROOT / "docs/b2-execution.md",
            ROOT / "docs/b2-setup-audit.md",
            ROOT / "tools/setup_senso.py",
            ROOT / "tools/run_with_limits.py",
            ROOT / "tools/b2_gate.py",
            ROOT / "tests/test_b2_baselines.py",
            ROOT / "src/random_baseline.py",
            ROOT / "src/verifier_a.py",
            ROOT / "src/verifier_b.go",
            ROOT / "docs/candidate-format.md",
            ROOT / config["b1_prerequisite"]["manifest_path"],
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
                "seeds": seeds,
                "budgets": budgets,
            },
        )
        shutil.copyfile(CONFIG_PATH, out / "frozen-b2-config.json")
        write_json(out / "senso-build-manifest.json", build_manifest)
        write_json(out / "senso-build-reference.json", {"manifest_sha256": build_manifest_sha})

        BUILD_ROOT.mkdir(parents=True, exist_ok=True)
        verifier_b = BUILD_ROOT / "verifier-b"
        built = subprocess.run(
            ["go", "build", "-trimpath", "-ldflags=-buildid=", "-o", str(verifier_b), "src/verifier_b.go"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=60,
            env={**os.environ, "GOMAXPROCS": "1"},
        )
        if built.returncode != 0:
            stderr_lines.append(built.stderr)
            raise RuntimeError("failed to build Verifier B")
        write_json(
            out / "verifier-build.json",
            {
                "go_version": run_text(["go", "version"]),
                "verifier_a_source_sha256": sha256(ROOT / "src/verifier_a.py"),
                "verifier_b_source_sha256": sha256(ROOT / "src/verifier_b.go"),
                "verifier_b_binary_sha256": sha256(verifier_b),
            },
        )

        run_random_stage(out, seeds, config, budgets, verifier_b, all_results["random"])
        run_senso_stage(
            "greedy", out, seeds, config, budgets, verifier_b, senso_binary, senso_source,
            population=config["greedy"]["population_per_seed"],
            generations=config["greedy"]["generations"],
            aggregate_wall=budgets["transparent_baselines"]["greedy_aggregate_wall_seconds"],
            per_seed_wall=60,
            per_seed_cpu=60,
            results=all_results["greedy"],
        )
        run_senso_stage(
            "senso", out, seeds, config, budgets, verifier_b, senso_binary, senso_source,
            population=config["senso"]["population"],
            generations=config["senso"]["generations"],
            aggregate_wall=budgets["constructive"]["aggregate_wall_seconds"],
            per_seed_wall=budgets["constructive"]["per_seed_cpu_seconds"],
            per_seed_cpu=budgets["constructive"]["per_seed_cpu_seconds"],
            results=all_results["senso"],
        )
        summaries = {name: summarize(results, seeds) for name, results in all_results.items()}
        acceptance_count = sum(
            result.get("best_size", 10**9) <= config["senso"]["acceptance_size"] and "verification" in result
            for result in all_results["senso"]
        )
        summary = {
            "status": "PASS" if acceptance_count > 0 else "FAIL",
            "acceptance_size": config["senso"]["acceptance_size"],
            "senso_acceptance_count": acceptance_count,
            "baselines": summaries,
            "all_senso_seeds_reported": summaries["senso"]["all_seeds_reported"],
            "truth_labels": config["truth_labels"],
        }
        if not all(item["all_seeds_reported"] for item in summaries.values()):
            raise RuntimeError("one or more B2 baselines did not report all frozen seeds")
        if acceptance_count == 0:
            raise RuntimeError("no SENSO seed reproduced a verified network of at most 45 comparators")
        status = "PASS"
        log_lines.append(
            f"PASS: all 20 SENSO seeds reported; {acceptance_count} returned dual-verified networks of at most 45 comparators."
        )
        log_lines.append(
            f"PASS: random best={summaries['random']['best_size']}, greedy best={summaries['greedy']['best_size']}, "
            f"SENSO best={summaries['senso']['best_size']}."
        )
    except FrontierArtifact as exc:
        status = "BLOCKED"
        error = str(exc)
        log_lines.append(f"BLOCKED: {error}; exact artifact frozen and both B1 verifiers run. Stop for a new contract.")
    except VerificationFailure as exc:
        status = "INVALID"
        error = str(exc)
        log_lines.append(f"INVALID: {error}")
    except Exception as exc:
        status = "FAIL"
        error = str(exc)
        log_lines.append(f"FAIL: {error}")

    write_json(out / "seed-results.json", all_results)
    if not summary:
        seeds = json.loads((ROOT / config["parents"]["seeds_path"]).read_text(encoding="utf-8"))["seeds"]
        summary = {
            "status": status,
            "baselines": {name: summarize(results, seeds) for name, results in all_results.items()},
        }
    write_json(out / "summary.json", summary)
    host = host_record()
    self_usage = resource.getrusage(resource.RUSAGE_SELF)
    child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    multiplier = 1 if sys.platform == "darwin" else 1024
    measured_peak = max(
        [0, *(result["resource"].get("peak_rss_bytes") or 0 for results in all_results.values() for result in results)]
    )
    peak_rss = max(int(self_usage.ru_maxrss * multiplier), int(child_usage.ru_maxrss * multiplier), measured_peak)
    measured_cpu = sum(
        result["resource"].get("cpu_seconds") or 0 for results in all_results.values() for result in results
    )
    ended = datetime.now(timezone.utc)
    manifest = {
        "schema_version": "s13-evidence-manifest/v1",
        "run_id": run_id,
        "gate": "B2",
        "source_commit": run_text(["git", "rev-parse", "HEAD"]),
        "dirty_at_start": False,
        "command": [sys.executable, "tools/b2_gate.py"],
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "wall_seconds": round(time.perf_counter() - started_perf, 6),
        "cpu_seconds": round(time.process_time() - started_cpu + measured_cpu, 6),
        "peak_rss_bytes": peak_rss,
        "threads": 1,
        "host": host,
        "config_sha256": config_hash,
        "status": status,
    }
    if error is not None:
        manifest["error"] = error
    write_json(out / "manifest.json", manifest)
    (out / "command.txt").write_text(f"{sys.executable} tools/b2_gate.py\n", encoding="utf-8")
    (out / "stdout.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    (out / "stderr.txt").write_text("\n".join(stderr_lines) + ("\n" if stderr_lines else ""), encoding="utf-8")
    write_checksums(out)
    for line in log_lines:
        print(line)
    print(f"evidence: {out.relative_to(ROOT)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
