#!/usr/bin/env python3
"""Verify and preserve the E0 learned-method experiment freeze."""

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
CONFIG = ROOT / "config/experiment-v1"
FREEZE_PATH = CONFIG / "e0-freeze.json"
BASELINE_COMMIT = "f4829768b9de2db170e4234d6c3d774b312eb318"


class BlockedError(RuntimeError):
    pass


class InvalidError(RuntimeError):
    pass


def run(command: list[str], *, check: bool = True, cwd: Path = ROOT) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n{completed.stdout}"
        )
    return completed.stdout.strip()


def is_ancestor(ancestor: str, descendant: str = "HEAD") -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return completed.returncode == 0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aggregate_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(dict.fromkeys(paths)):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256(path)))
        digest.update(b"\n")
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


def sysctl(name: str) -> str:
    return subprocess.check_output(["sysctl", "-n", name], text=True).strip()


def local_host_record() -> dict[str, Any]:
    disk = shutil.disk_usage(ROOT)
    return {
        "hostname": platform.node(),
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
        "go": ["go", "version"],
        "clang": ["clang", "--version"],
        "zstd": ["zstd", "--version"],
    }
    return {name: run(command).splitlines()[0] for name, command in commands.items()}


def training_host_record() -> dict[str, Any]:
    script = r'''python3 - <<'PY'
import json, platform
import numpy, torch
print(json.dumps({
    "hostname": platform.node(),
    "os": platform.platform(),
    "machine": platform.machine(),
    "python": platform.python_version(),
    "torch": torch.__version__,
    "numpy": numpy.__version__,
    "cuda_runtime": torch.version.cuda,
    "cudnn": torch.backends.cudnn.version(),
    "cuda_available": torch.cuda.is_available(),
    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    "capability": list(torch.cuda.get_device_capability(0)) if torch.cuda.is_available() else None,
}, sort_keys=True))
PY
nvidia-smi --query-gpu=name,uuid,memory.total,driver_version --format=csv,noheader,nounits'''
    try:
        output = run(["ssh", "ollama", script])
    except RuntimeError as exc:
        raise BlockedError(f"authorized training host unavailable: {exc}") from exc
    lines = output.splitlines()
    if len(lines) != 2:
        raise InvalidError("unexpected training-host audit output")
    record = json.loads(lines[0])
    gpu_parts = [part.strip() for part in lines[1].split(",")]
    if len(gpu_parts) != 4:
        raise InvalidError("unexpected nvidia-smi audit output")
    record.update(
        {
            "nvidia_smi_name": gpu_parts[0],
            "gpu_uuid": gpu_parts[1],
            "gpu_memory_mib": int(gpu_parts[2]),
            "driver": gpu_parts[3],
        }
    )
    return record


def repository_record() -> dict[str, Any]:
    return {
        "branch": run(["git", "branch", "--show-current"]),
        "head": run(["git", "rev-parse", "HEAD"]),
        "status_porcelain": run(["git", "status", "--porcelain", "--untracked-files=all"]),
        "recent_commits": run(["git", "log", "--oneline", "-5"]).splitlines(),
        "worktrees_porcelain": run(["git", "worktree", "list", "--porcelain"]).splitlines(),
    }


def validate_authority_and_predecessor(freeze: dict[str, Any]) -> dict[str, Any]:
    authority = freeze["authority"]
    contract = ROOT / authority["contract_path"]
    if sha256(contract) != authority["contract_sha256"]:
        raise InvalidError("method contract hash mismatch")
    if not is_ancestor(authority["authority_commit"]):
        raise InvalidError("authority commit is not an ancestor of HEAD")
    if not is_ancestor(BASELINE_COMMIT):
        raise InvalidError("baseline commit is not an ancestor of HEAD")

    predecessor = freeze["predecessor"]
    pin_fields = (
        ("report_path", "report_sha256"),
        ("python_verifier_path", "python_verifier_sha256"),
        ("go_verifier_path", "go_verifier_sha256"),
        ("b2_execution_path", "b2_execution_sha256"),
        ("b2_senso_path", "b2_senso_sha256"),
        ("b2_seeds_path", "b2_seeds_sha256"),
    )
    verified = []
    for path_key, hash_key in pin_fields:
        path = ROOT / predecessor[path_key]
        actual = sha256(path)
        if actual != predecessor[hash_key]:
            raise InvalidError(f"predecessor pin mismatch: {path.relative_to(ROOT)}")
        verified.append({"path": path.relative_to(ROOT).as_posix(), "sha256": actual})

    evidence_paths = predecessor["evidence_paths"]
    changed = run(["git", "diff", "--name-status", BASELINE_COMMIT, "--", *evidence_paths])
    untracked = run(["git", "status", "--porcelain", "--untracked-files=all", "--", *evidence_paths])
    if changed or untracked:
        raise InvalidError("B0--B4 evidence differs from the frozen baseline commit")
    replay = run([sys.executable, "tools/evidence_check.py"])
    return {"verified_pins": verified, "evidence_diff": changed, "evidence_status": untracked, "inventory_replay": replay}


def validate_senso(freeze: dict[str, Any]) -> dict[str, Any]:
    senso = freeze["senso"]
    pairs = (
        ("archive_path", "archive_sha256"),
        ("portability_patch_path", "portability_patch_sha256"),
        ("build_manifest_path", "build_manifest_sha256"),
        ("binary_path", "binary_sha256"),
    )
    result = []
    for path_key, hash_key in pairs:
        path = ROOT / senso[path_key]
        if not path.is_file():
            raise BlockedError(f"missing frozen SENSO artifact: {path}")
        actual = sha256(path)
        if actual != senso[hash_key]:
            raise InvalidError(f"frozen SENSO artifact mismatch: {path.relative_to(ROOT)}")
        result.append({"path": path.relative_to(ROOT).as_posix(), "sha256": actual, "size_bytes": path.stat().st_size})
    binary = ROOT / senso["binary_path"]
    if binary.stat().st_size != senso["binary_size_bytes"]:
        raise InvalidError("frozen SENSO binary size mismatch")
    return {"artifacts": result, "candidate_accounting": senso["candidate_accounting"]}


def validate_config_inventory(freeze: dict[str, Any]) -> dict[str, Any]:
    listed = []
    for item in freeze["config_inventory"]:
        path = ROOT / item["path"]
        actual = sha256(path)
        if actual != item["sha256"]:
            raise InvalidError(f"experiment config hash mismatch: {item['path']}")
        listed.append({"path": item["path"], "sha256": actual})

    actual_files = sorted(path for path in CONFIG.glob("*.json") if path.name != "e0-freeze.json")
    if {item["path"] for item in listed} != {path.relative_to(ROOT).as_posix() for path in actual_files}:
        raise InvalidError("E0 config inventory is incomplete or has unexpected paths")

    features = json.loads((CONFIG / "features-v1.json").read_text(encoding="utf-8"))
    occupied = {item["index"] for item in features["scalar_features"]}
    for block in features["channel_blocks"]:
        occupied.update(range(block["start"], block["start"] + block["length"]))
    recent = features["recent_comparator_block"]
    occupied.update(range(recent["start"], recent["start"] + recent["length"]))
    if occupied != set(range(features["input_dimension"])):
        raise InvalidError("feature indices do not exactly cover input dimension")

    model = json.loads((CONFIG / "model-v1.json").read_text(encoding="utf-8"))
    layers = model["architecture"]["layers"]
    parameter_count = sum(left * right + right for left, right in zip(layers, layers[1:]))
    if parameter_count != model["architecture"]["trainable_parameters"]:
        raise InvalidError("model parameter count mismatch")
    if parameter_count > model["architecture"]["parameter_ceiling"]:
        raise InvalidError("model exceeds parameter ceiling")
    if model["objective"]["label"] != "final_count <= 45" or model["method_version"] != 1:
        raise InvalidError("model objective/version mismatch")
    integration = model["integration"]
    if integration["baseline_gaussian_draws_per_reconstruction"] != 1 or integration["proposal_count_maximum"] != 8:
        raise InvalidError("method-v1 proposal/RNG freeze mismatch")

    dataset = json.loads((CONFIG / "dataset-v1.json").read_text(encoding="utf-8"))
    if dataset["target_comparators"] != 45 or dataset["expected_total_rows"] != 1_004_000:
        raise InvalidError("dataset target or row budget mismatch")
    if dataset["additional_data"] != "none":
        raise InvalidError("unfrozen additional dataset enabled")

    exam = json.loads((CONFIG / "exam-v1.json").read_text(encoding="utf-8"))
    if exam["acceptance_comparators"] != 45 or exam["paired_seed_count"] != 60:
        raise InvalidError("E3 target or seed-count mismatch")
    if exam["candidate_evaluations_per_method_per_seed"] != 50_200:
        raise InvalidError("E3 evaluation budget mismatch")
    if exam["pass_criteria"]["minimum_mericanii_successes"] != 12:
        raise InvalidError("E3 success threshold weakened")
    if exam["pass_criteria"]["minimum_success_ratio_vs_senso"] != 2.0:
        raise InvalidError("E3 ratio threshold weakened")

    budgets = json.loads((CONFIG / "budgets-v1.json").read_text(encoding="utf-8"))
    if not budgets["e5"]["enabled_only_after_method_pass"]:
        raise InvalidError("frontier campaign enabled before method pass")
    if budgets["e5"]["aggregate_candidate_evaluations"] != 100_000_000:
        raise InvalidError("frontier evaluation budget mismatch")
    if budgets["e5"]["calendar_seconds"] != 7 * 24 * 60 * 60 or budgets["e5"]["paid_compute"]:
        raise InvalidError("frontier wall/compute policy mismatch")

    config_files = sorted(CONFIG.glob("*.json"))
    return {"files": listed, "aggregate_sha256": aggregate_hash(config_files), "model_parameters": parameter_count, "feature_dimension": features["input_dimension"]}


def validate_seeds() -> dict[str, Any]:
    reproduction = json.loads(run([sys.executable, "tools/generate_method_seeds.py", "--verify"]))
    development = json.loads((CONFIG / "seeds-development.json").read_text(encoding="utf-8"))
    validation = json.loads((CONFIG / "seeds-validation.json").read_text(encoding="utf-8"))
    e3 = json.loads((CONFIG / "seeds-e3-holdout.json").read_text(encoding="utf-8"))
    partitions = [development["seeds"], validation["seeds"], e3["seeds"]]
    flat = [seed for partition in partitions for seed in partition]
    if [len(partition) for partition in partitions] != [20, 20, 60]:
        raise InvalidError("seed partition count mismatch")
    if len(flat) != len(set(flat)) or any(type(seed) is not int or seed <= 0 for seed in flat):
        raise InvalidError("materialized seed partitions overlap or contain invalid values")
    if development["training_seeds"] + development["calibration_seeds"] != development["seeds"]:
        raise InvalidError("development seed split mismatch")
    if not e3["sealed"]:
        raise InvalidError("E3 holdout is not sealed")
    return {"reproduction": reproduction, "materialized_partition_hashes": {
        "development": sha256(CONFIG / "seeds-development.json"),
        "validation": sha256(CONFIG / "seeds-validation.json"),
        "e3_final_holdout": sha256(CONFIG / "seeds-e3-holdout.json"),
    }}


def validate_sources() -> dict[str, Any]:
    config = json.loads((CONFIG / "sources-v1.json").read_text(encoding="utf-8"))
    status = config["research_status"]
    if status["settled"] or [status["lower_bound"], status["upper_bound"]] != [44, 45]:
        raise BlockedError("STALE_TARGET: frozen source audit no longer describes open 44..45 status")
    verified = []
    for source in config["sources"]:
        cache_path = source.get("cache_path")
        if cache_path:
            path = ROOT / cache_path
            if sha256(path) != source["cache_sha256"]:
                raise InvalidError(f"source cache mismatch: {cache_path}")
            verified.append({"id": source["id"], "path": cache_path, "sha256": source["cache_sha256"]})

    catalog = (ROOT / ".cache/sources/sorting_networks_extended.html").read_text(encoding="utf-8")
    if '<td class="idx">44&hellip;45</td>' not in catalog or 'id="N13L45D10"' not in catalog:
        raise BlockedError("STALE_TARGET: maintained catalog snapshot lacks open 44..45 / 45 witness facts")

    remote_commands = {
        "dobbelaere-maintained-catalog": ["git", "ls-remote", "--heads", "https://github.com/BertDobbelaere/bertdobbelaere.github.io.git"],
        "sortnetopt-context": ["git", "ls-remote", "--heads", "https://github.com/jix/sortnetopt.git"],
    }
    by_id = {item["id"]: item for item in config["sources"]}
    remote = {}
    for source_id, command in remote_commands.items():
        try:
            output = run(command)
        except RuntimeError as exc:
            raise BlockedError(f"live source audit unavailable: {source_id}: {exc}") from exc
        heads = {line.split()[0] for line in output.splitlines() if line.strip()}
        expected = by_id[source_id]["remote_head"]
        if expected not in heads:
            raise InvalidError(f"live remote head changed after E0 source freeze: {source_id}")
        remote[source_id] = sorted(heads)
    return {"research_status": status, "verified_caches": verified, "remote_heads": remote, "conclusion": config["audit_conclusion"]}


def validate_environment(local: dict[str, Any], training: dict[str, Any], freeze: dict[str, Any]) -> dict[str, Any]:
    expected = json.loads((CONFIG / "environment-v1.json").read_text(encoding="utf-8"))
    if local["model"] != expected["local"]["model"] or local["logical_cores"] != expected["local"]["logical_cores"]:
        raise InvalidError("local host identity differs from freeze")
    if local["memory_bytes"] < freeze["gate_rules"]["minimum_local_memory_bytes"]:
        raise BlockedError("local host memory below E0 minimum")
    if local["disk_free_bytes_at_start"] < freeze["gate_rules"]["minimum_free_disk_bytes"]:
        raise BlockedError("less than 20 GiB free for method experiment")
    training_expected = expected["training"]
    if training["gpu_uuid"] != training_expected["gpu_uuid"] or training["gpu_memory_mib"] < training_expected["gpu_memory_mib"]:
        raise InvalidError("training GPU identity or memory differs from freeze")
    if not training["cuda_available"] or training["torch"] != training_expected["torch"] or training["numpy"] != training_expected["numpy"]:
        raise BlockedError("frozen training Python/CUDA environment unavailable")
    return {"local": local, "training": training, "paid_compute_allowed": expected["paid_compute_allowed"]}


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        print(f"E0 preflight failed: cwd must be exactly {ROOT}", file=sys.stderr)
        return 2
    if run(["git", "branch", "--show-current"]) != "goal/s13-method-v1":
        print("E0 preflight failed: wrong branch", file=sys.stderr)
        return 2
    dirty = run(["git", "status", "--porcelain", "--untracked-files=all"])
    if dirty:
        print("E0 preflight failed: scored configuration is dirty", file=sys.stderr)
        print(dirty, file=sys.stderr)
        return 2

    repo = repository_record()
    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    started_cpu = time.process_time()
    run_id = started.strftime("e0-%Y%m%dT%H%M%SZ")
    out = ROOT / "evidence/e0" / run_id
    out.mkdir(parents=True, exist_ok=False)
    log_lines = ["E0 falsifiable gate: predecessor, status, partitions, method, budgets, and evidence rules are frozen before scores."]
    status = "FAIL"
    error: str | None = None
    config_hash = "0" * 64
    host: dict[str, Any] = {}

    try:
        freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        predecessor = validate_authority_and_predecessor(freeze)
        senso = validate_senso(freeze)
        configs = validate_config_inventory(freeze)
        config_hash = configs["aggregate_sha256"]
        seeds = validate_seeds()
        sources = validate_sources()
        local = local_host_record()
        training = training_host_record()
        environment = validate_environment(local, training, freeze)
        host = local

        write_json(out / "predecessor-audit.json", predecessor)
        write_json(out / "senso-audit.json", senso)
        write_json(out / "config-audit.json", configs)
        write_json(out / "seed-audit.json", seeds)
        write_json(out / "source-audit.json", sources)
        write_json(out / "environment-audit.json", environment)
        write_json(out / "repository-audit.json", repo)
        write_json(out / "tool-versions.json", tool_versions())
        status = "PASS"
        log_lines.append("PASS: maintained source heads and snapshot retain comparator-count 44..45 status.")
        log_lines.append("PASS: B0--B4 evidence and both frozen verifiers byte-match the baseline.")
        log_lines.append("PASS: 20 development, 20 validation, and 60 sealed E3 seeds are reproducible and disjoint.")
        log_lines.append("PASS: target-45 dataset, 7617-parameter truncation ranker, matched exam, repair, and conditional frontier budgets are frozen.")
    except BlockedError as exc:
        status = "BLOCKED"
        error = str(exc)
        log_lines.append(f"BLOCKED: {error}")
    except InvalidError as exc:
        status = "INVALID"
        error = str(exc)
        log_lines.append(f"INVALID: {error}")
    except Exception as exc:
        status = "FAIL"
        error = str(exc)
        log_lines.append(f"FAIL: {error}")

    ended = datetime.now(timezone.utc)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    peak_rss = int(usage.ru_maxrss if sys.platform == "darwin" else usage.ru_maxrss * 1024)
    manifest = {
        "schema_version": "s13-method-evidence-manifest/v1",
        "run_id": run_id,
        "gate": "E0",
        "source_commit": repo["head"],
        "dirty_at_start": False,
        "command": [sys.executable, "tools/e0_method_gate.py"],
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
    (out / "command.txt").write_text(f"{sys.executable} tools/e0_method_gate.py\n", encoding="utf-8")
    (out / "stdout.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    (out / "stderr.txt").write_text("", encoding="utf-8")
    write_checksums(out)
    for line in log_lines:
        print(line)
    print(f"evidence: {out.relative_to(ROOT)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
