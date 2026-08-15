#!/usr/bin/env python3
"""Run E1: audit instrumentation and build the frozen development dataset."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import resource
import shutil
import subprocess
import sys
import time
from typing import Any

if __package__:
    from tools.method_runtime import (
        ROOT,
        VerificationFailure,
        aggregate_hash,
        candidate_bytes,
        parse_candidate,
        parse_milestone,
        run_limited,
        senso_command,
        sha256,
        verify_candidate,
        write_checksums,
        write_json,
    )
else:
    from method_runtime import (
        ROOT,
        VerificationFailure,
        aggregate_hash,
        candidate_bytes,
        parse_candidate,
        parse_milestone,
        run_limited,
        senso_command,
        sha256,
        verify_candidate,
        write_checksums,
        write_json,
    )


CONFIG = ROOT / "config/experiment-v1"
E0_MANIFEST = ROOT / "evidence/e0/e0-20260815T021424Z/manifest.json"
E0_MANIFEST_SHA256 = "a38832f101d24fbc5430ce8c25b5a343cbbcd8fcedf66c723f8383a588499754"
VERIFIER_B = ROOT / ".build/b1/verifier-b"
VERIFIER_B_SHA256 = "212805ebb2f71bfdc3a470a0e873167c6494fea0cea9829a8db889298368e3a2"
EXPECTED_HEADER = [
    "schema",
    "seed",
    "generation",
    "sample_index",
    "parent_count",
    "prefix_count",
    *(f"f{index:03d}" for index in range(85)),
    "final_count",
    "success45",
    "candidate_sequence_if_success45",
]


class FrontierStop(RuntimeError):
    def __init__(self, sequence: str, seed: int, sample_index: int):
        super().__init__(f"unexpected <=44 candidate at seed {seed}, row {sample_index}")
        self.sequence = sequence
        self.seed = seed
        self.sample_index = sample_index


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
        "hostname": platform.node(),
        "model": sysctl("hw.model"),
        "cpu": sysctl("machdep.cpu.brand_string"),
        "logical_cores": int(sysctl("hw.logicalcpu")),
        "physical_cores": int(sysctl("hw.physicalcpu")),
        "memory_bytes": int(sysctl("hw.memsize")),
        "os": platform.platform(),
        "machine": platform.machine(),
        "disk_free_bytes_at_start": disk.free,
    }


def load_active(path: Path, schema: str) -> tuple[dict[str, Any], Path, Path, str]:
    if not path.is_file():
        raise RuntimeError(f"missing build pointer: {path}; run the matching setup tool")
    active = json.loads(path.read_text(encoding="utf-8"))
    manifest_path = ROOT / active["manifest_path"]
    if sha256(manifest_path) != active["manifest_sha256"]:
        raise RuntimeError(f"build manifest pointer mismatch: {path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["schema_version"] != schema or manifest["status"] != "PASS":
        raise RuntimeError(f"wrong or failed build manifest: {manifest_path}")
    binary = ROOT / manifest["binary_path"]
    source = ROOT / manifest["source_path"]
    if sha256(binary) != manifest["binary_sha256"]:
        raise RuntimeError(f"build binary mismatch: {binary}")
    return manifest, binary, source, active["manifest_sha256"]


def prerequisite_check() -> dict[str, Any]:
    if sha256(E0_MANIFEST) != E0_MANIFEST_SHA256:
        raise RuntimeError("accepted E0 manifest hash mismatch")
    e0 = json.loads(E0_MANIFEST.read_text(encoding="utf-8"))
    if e0["status"] != "PASS":
        raise RuntimeError("accepted E0 is not PASS")
    replay = run_text([sys.executable, "tools/evidence_check.py"])
    config_hash = aggregate_hash(sorted(CONFIG.glob("*.json")))
    if config_hash != e0["config_sha256"]:
        raise RuntimeError("experiment config aggregate differs from accepted E0")
    if sha256(VERIFIER_B) != VERIFIER_B_SHA256:
        raise RuntimeError("frozen Go verifier binary mismatch")

    instrumented, instrumented_binary, instrumented_source, instrumented_manifest_sha = load_active(
        ROOT / ".build/senso-instrumented/active.json",
        "s13-senso-instrumented-build/v1",
    )
    original, original_binary, original_source, original_manifest_sha = load_active(
        ROOT / ".build/senso/active.json",
        "s13-senso-build/v1",
    )
    patch = ROOT / instrumented["instrumentation_patch_path"]
    if sha256(patch) != instrumented["instrumentation_patch_sha256"]:
        raise RuntimeError("instrumentation patch differs from instrumented build")
    if original["binary_sha256"] != "1d6fe20b547fa0e9dd9c899e34b608ac157104f63fd845d858e6e4ae9c0e6cc6":
        raise RuntimeError("original SENSO binary differs from E0 pin")

    development = json.loads((CONFIG / "seeds-development.json").read_text(encoding="utf-8"))["seeds"]
    validation = set(json.loads((CONFIG / "seeds-validation.json").read_text(encoding="utf-8"))["seeds"])
    holdout = set(json.loads((CONFIG / "seeds-e3-holdout.json").read_text(encoding="utf-8"))["seeds"])
    if development != list(range(1, 21)) or set(development) & (validation | holdout):
        raise RuntimeError("E1 development partition mismatch or leakage")
    return {
        "evidence_replay": replay,
        "config_sha256": config_hash,
        "development_seeds": development,
        "instrumented": instrumented,
        "instrumented_binary": instrumented_binary,
        "instrumented_source": instrumented_source,
        "instrumented_manifest_sha256": instrumented_manifest_sha,
        "original": original,
        "original_binary": original_binary,
        "original_source": original_source,
        "original_manifest_sha256": original_manifest_sha,
    }


def parse_sequence(text: str) -> list[tuple[int, int]]:
    if not text:
        return []
    comparators: list[tuple[int, int]] = []
    for item in text.split(";"):
        parts = item.split("-")
        if len(parts) != 2:
            raise RuntimeError("malformed success sequence")
        lower, upper = (int(value) for value in parts)
        if not (0 <= lower < upper < 13):
            raise RuntimeError("noncanonical comparator in success sequence")
        comparators.append((lower, upper))
    return comparators


def validate_dataset(path: Path, seed: int, *, expected_rows: int | None) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    generation_counts: Counter[int] = Counter()
    final_counts: Counter[int] = Counter()
    success_sequences: dict[str, dict[str, Any]] = {}
    row_count = 0
    min_feature = math.inf
    max_feature = -math.inf
    with path.open("r", encoding="utf-8", newline="") as stream:
        header = stream.readline().rstrip("\n").split("\t")
        if header != EXPECTED_HEADER:
            raise RuntimeError(f"dataset header mismatch for seed {seed}")
        for raw in stream:
            fields = raw.rstrip("\n").split("\t")
            if len(fields) != len(EXPECTED_HEADER):
                raise RuntimeError(f"dataset column count mismatch seed={seed} row={row_count}")
            if fields[0] != "s13-completion-row-v1" or int(fields[1]) != seed:
                raise RuntimeError(f"dataset schema/seed mismatch seed={seed} row={row_count}")
            generation = int(fields[2])
            sample_index = int(fields[3])
            parent_count = int(fields[4])
            prefix_count = int(fields[5])
            if sample_index != row_count or not (0 <= generation <= 500):
                raise RuntimeError(f"dataset index/generation mismatch seed={seed} row={row_count}")
            if parent_count < 0 or not (0 <= prefix_count <= parent_count):
                raise RuntimeError(f"dataset prefix/parent mismatch seed={seed} row={row_count}")
            features = [float(value) for value in fields[6:91]]
            if len(features) != 85 or any(not math.isfinite(value) for value in features):
                raise RuntimeError(f"dataset feature invalid seed={seed} row={row_count}")
            min_feature = min(min_feature, *features)
            max_feature = max(max_feature, *features)
            final_count = int(fields[91])
            success = int(fields[92])
            sequence = fields[93]
            if success not in (0, 1) or success != int(final_count <= 45):
                raise RuntimeError(f"dataset label mismatch seed={seed} row={row_count}")
            if success:
                comparators = parse_sequence(sequence)
                if len(comparators) != final_count:
                    raise RuntimeError(f"dataset success sequence length mismatch seed={seed} row={row_count}")
                item = success_sequences.setdefault(
                    sequence,
                    {"count": 0, "first_sample_index": row_count, "final_count": final_count},
                )
                item["count"] += 1
                if final_count <= 44:
                    raise FrontierStop(sequence, seed, row_count)
            elif sequence:
                raise RuntimeError(f"non-success row carries candidate sequence seed={seed} row={row_count}")
            generation_counts[generation] += 1
            final_counts[final_count] += 1
            row_count += 1
    if expected_rows is not None and row_count != expected_rows:
        raise RuntimeError(f"dataset row count mismatch seed={seed}: {row_count} != {expected_rows}")
    if expected_rows == 50_200:
        expected_generations = {0: 200, **{generation: 100 for generation in range(1, 501)}}
        if dict(generation_counts) != expected_generations:
            raise RuntimeError(f"dataset generation distribution mismatch seed={seed}")
    summary = {
        "seed": seed,
        "rows": row_count,
        "generation_counts": {str(key): value for key, value in sorted(generation_counts.items())},
        "final_size_distribution": {str(key): value for key, value in sorted(final_counts.items())},
        "success_rows": sum(item["count"] for item in success_sequences.values()),
        "unique_success_sequences": len(success_sequences),
        "feature_minimum": min_feature if row_count else None,
        "feature_maximum": max_feature if row_count else None,
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
    }
    return summary, success_sequences


def finalize_run(
    directory: Path,
    *,
    seed: int,
    resource_record: dict[str, Any],
    predecessor: list[tuple[int, int]],
) -> tuple[dict[str, Any], list[tuple[int, int]]]:
    result: dict[str, Any] = {"seed": seed, "resource": resource_record, "status": resource_record["status"]}
    if resource_record["status"] != "PASS":
        write_json(directory / "result.json", result)
        raise RuntimeError(f"SENSO run failed for seed {seed}: {resource_record['status']}")
    milestones = sorted(directory.glob("milestone_g*.obm.gz"))
    if len(milestones) != 1:
        raise RuntimeError(f"seed {seed}: expected one milestone, found {len(milestones)}")
    parsed = parse_milestone(milestones[0])
    if parsed["generation"] != 500 or parsed["evaluations"] != 50_200 or parsed["channels"] != 13:
        raise RuntimeError(f"seed {seed}: milestone generation/evaluation/channel mismatch")
    comparators = parsed["comparators"]
    if comparators != predecessor:
        raise RuntimeError(f"seed {seed}: instrumented trajectory differs from frozen B2 candidate")
    candidate = directory / "candidate.sortnet"
    candidate.write_bytes(candidate_bytes(13, comparators, f"e1-instrumented-seed-{seed}"))
    verification = verify_candidate(candidate, VERIFIER_B, directory)
    result.update(
        {
            "status": "PASS",
            "generation": 500,
            "evaluations": 50_200,
            "best_size": len(comparators),
            "milestone_sha256": sha256(milestones[0]),
            "milestone_size_bytes": milestones[0].stat().st_size,
            "candidate_sha256": sha256(candidate),
            "verification": verification,
        }
    )
    write_json(directory / "result.json", result)
    return result, comparators


def verify_success_sequences(
    sequences: dict[str, dict[str, Any]],
    success_root: Path,
    verified: dict[str, dict[str, Any]],
    *,
    seed: int,
) -> list[dict[str, Any]]:
    references = []
    for sequence, occurrence in sequences.items():
        sequence_hash = hashlib.sha256(sequence.encode("ascii")).hexdigest()
        if sequence_hash not in verified:
            directory = success_root / f"candidate-{sequence_hash[:20]}"
            directory.mkdir()
            comparators = parse_sequence(sequence)
            candidate = directory / "candidate.sortnet"
            candidate.write_bytes(candidate_bytes(13, comparators, f"e1-dataset-success-{sequence_hash[:20]}"))
            verification = verify_candidate(candidate, VERIFIER_B, directory)
            if verification["comparators"] != len(comparators):
                raise VerificationFailure("success sequence verifier count mismatch")
            verified[sequence_hash] = {
                "sequence_sha256": sequence_hash,
                "candidate_path": candidate.relative_to(success_root.parents[1]).as_posix(),
                "candidate_sha256": sha256(candidate),
                "comparators": len(comparators),
                "verification": verification,
            }
            write_json(directory / "result.json", verified[sequence_hash])
        references.append(
            {
                "seed": seed,
                "sequence_sha256": sequence_hash,
                "occurrences": occurrence["count"],
                "first_sample_index": occurrence["first_sample_index"],
                "final_count": occurrence["final_count"],
            }
        )
    return references


def compress_dataset(paths: list[Path], output: Path) -> dict[str, Any]:
    command = ["zstd", "-q", "-T1", "-3", "-o", str(output)]
    process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdin is not None
    try:
        for index, path in enumerate(paths):
            with path.open("rb") as stream:
                if index > 0:
                    stream.readline()
                shutil.copyfileobj(stream, process.stdin, length=1024 * 1024)
        process.stdin.close()
        stdout = process.stdout.read() if process.stdout is not None else b""
        stderr = process.stderr.read() if process.stderr is not None else b""
        return_code = process.wait()
    except Exception:
        process.kill()
        process.wait()
        raise
    if return_code != 0:
        raise RuntimeError(f"dataset compression failed: {stderr.decode('utf-8', errors='replace')}")
    tested = subprocess.run(["zstd", "-q", "-t", str(output)], cwd=ROOT, check=False)
    if tested.returncode != 0:
        raise RuntimeError("compressed dataset integrity test failed")
    return {
        "command": command,
        "stdout": stdout.decode("utf-8", errors="replace"),
        "stderr": stderr.decode("utf-8", errors="replace"),
        "sha256": sha256(output),
        "size_bytes": output.stat().st_size,
    }


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        print(f"E1 preflight failed: cwd must be exactly {ROOT}", file=sys.stderr)
        return 2
    if run_text(["git", "branch", "--show-current"]) != "goal/s13-method-v1":
        print("E1 preflight failed: wrong branch", file=sys.stderr)
        return 2
    dirty = run_text(["git", "status", "--porcelain", "--untracked-files=all"])
    if dirty:
        print("E1 preflight failed: scored configuration is dirty", file=sys.stderr)
        print(dirty, file=sys.stderr)
        return 2

    prerequisite = prerequisite_check()
    source_commit = run_text(["git", "rev-parse", "HEAD"])
    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    started_cpu = time.process_time()
    run_id = started.strftime("e1-%Y%m%dT%H%M%SZ")
    out = ROOT / "evidence/e1" / run_id
    cache = ROOT / ".cache/method-v1/datasets" / run_id
    out.mkdir(parents=True, exist_ok=False)
    cache.mkdir(parents=True, exist_ok=False)
    success_root = out / "successes"
    success_root.mkdir()
    host = host_record()
    log_lines = ["E1 falsifiable gate: instrumentation preserves SENSO and yields every frozen development row without leakage."]
    status = "FAIL"
    error: str | None = None
    seed_results: list[dict[str, Any]] = []
    dataset_summaries: list[dict[str, Any]] = []
    dataset_paths: list[Path] = []
    verified_successes: dict[str, dict[str, Any]] = {}
    success_references: list[dict[str, Any]] = []
    trajectory_audit: dict[str, Any] = {}

    try:
        write_json(out / "instrumented-build-manifest.json", prerequisite["instrumented"])
        write_json(out / "original-build-manifest.json", prerequisite["original"])
        write_json(
            out / "prerequisite.json",
            {
                "e0_manifest_path": E0_MANIFEST.relative_to(ROOT).as_posix(),
                "e0_manifest_sha256": E0_MANIFEST_SHA256,
                "evidence_replay": prerequisite["evidence_replay"],
                "config_sha256": prerequisite["config_sha256"],
                "instrumented_manifest_sha256": prerequisite["instrumented_manifest_sha256"],
                "original_manifest_sha256": prerequisite["original_manifest_sha256"],
                "verifier_b_binary_sha256": VERIFIER_B_SHA256,
            },
        )

        budgets = json.loads((CONFIG / "budgets-v1.json").read_text(encoding="utf-8"))
        local_budget = budgets["local_search"]
        if host["disk_free_bytes_at_start"] < 20 * 1024**3:
            raise RuntimeError("less than 20 GiB free before E1 dataset")

        sentinel_dir = out / "audit-off-seed-01"
        sentinel_dir.mkdir()
        predecessor_one = parse_candidate(ROOT / "evidence/b2/b2-20260814T232833Z/senso/seed-01/candidate.sortnet")
        off_resource = run_limited(
            senso_command(prerequisite["instrumented_binary"], prerequisite["instrumented_source"], seed=1),
            sentinel_dir,
            cpu_limit=local_budget["per_seed_cpu_seconds"],
            wall_limit=local_budget["per_seed_wall_seconds"],
            memory_limit=local_budget["peak_rss_bytes"],
        )
        off_result, off_sequence = finalize_run(
            sentinel_dir,
            seed=1,
            resource_record=off_resource,
            predecessor=predecessor_one,
        )
        print("E1 audit-off seed 1: PASS", flush=True)

        for seed in prerequisite["development_seeds"]:
            seed_dir = out / f"seed-{seed:02d}"
            seed_dir.mkdir()
            dataset_path = cache / f"seed-{seed:02d}.tsv"
            predecessor_path = ROOT / f"evidence/b2/b2-20260814T232833Z/senso/seed-{seed:02d}/candidate.sortnet"
            predecessor = parse_candidate(predecessor_path)
            environment = {
                "MERICANII_DATASET_PATH": str(dataset_path),
                "MERICANII_DATASET_SEED": str(seed),
            }
            resource_record = run_limited(
                senso_command(prerequisite["instrumented_binary"], prerequisite["instrumented_source"], seed=seed),
                seed_dir,
                cpu_limit=local_budget["per_seed_cpu_seconds"],
                wall_limit=local_budget["per_seed_wall_seconds"],
                memory_limit=local_budget["peak_rss_bytes"],
                environment_overrides=environment,
            )
            if resource_record["status"] != "PASS" and dataset_path.is_file():
                validate_dataset(dataset_path, seed, expected_rows=None)
            result, final_sequence = finalize_run(
                seed_dir,
                seed=seed,
                resource_record=resource_record,
                predecessor=predecessor,
            )
            summary, successes = validate_dataset(dataset_path, seed, expected_rows=50_200)
            references = verify_success_sequences(
                successes,
                success_root,
                verified_successes,
                seed=seed,
            )
            success_references.extend(references)
            dataset_path.chmod(0o444)
            result["dataset"] = {
                "path": dataset_path.relative_to(ROOT).as_posix(),
                "sha256": summary["sha256"],
                "size_bytes": summary["size_bytes"],
                "rows": summary["rows"],
            }
            result["success_sequence_references"] = references
            write_json(seed_dir / "result.json", result)
            seed_results.append(result)
            dataset_summaries.append(summary)
            dataset_paths.append(dataset_path)
            print(
                f"E1 seed {seed:02d}: PASS rows={summary['rows']} positives={summary['success_rows']} best={result['best_size']}",
                flush=True,
            )
            if seed == 1:
                trajectory_audit = {
                    "seed": 1,
                    "predecessor_b2_sequence_equal": predecessor == final_sequence,
                    "instrumentation_off_sequence_equal": off_sequence == final_sequence,
                    "instrumentation_off_evaluations": off_result["evaluations"],
                    "instrumentation_on_evaluations": result["evaluations"],
                    "instrumentation_off_best_size": off_result["best_size"],
                    "instrumentation_on_best_size": result["best_size"],
                    "rng_calls_added_by_instrumentation": 0,
                }
                if not all(
                    (
                        trajectory_audit["predecessor_b2_sequence_equal"],
                        trajectory_audit["instrumentation_off_sequence_equal"],
                        trajectory_audit["instrumentation_off_evaluations"] == 50_200,
                        trajectory_audit["instrumentation_on_evaluations"] == 50_200,
                    )
                ):
                    raise RuntimeError("instrumentation sentinel trajectory mismatch")

        if sum(item["rows"] for item in dataset_summaries) != 1_004_000:
            raise RuntimeError("aggregate E1 dataset row count mismatch")
        if [item["seed"] for item in dataset_summaries] != list(range(1, 21)):
            raise RuntimeError("E1 dataset seed order mismatch")
        aggregate_path = cache / "development-dataset.tsv.zst"
        compression = compress_dataset(dataset_paths, aggregate_path)
        aggregate_path.chmod(0o444)
        raw_total_bytes = sum(path.stat().st_size for path in dataset_paths)
        if raw_total_bytes > budgets["e1"]["maximum_raw_dataset_bytes"]:
            raise RuntimeError("E1 raw dataset exceeds frozen byte cap")
        dataset_manifest = {
            "schema_version": "s13-completion-dataset-manifest/v1",
            "run_id": run_id,
            "source_commit": source_commit,
            "config_sha256": prerequisite["config_sha256"],
            "instrumentation_patch_sha256": prerequisite["instrumented"]["instrumentation_patch_sha256"],
            "instrumented_binary_sha256": prerequisite["instrumented"]["binary_sha256"],
            "seed_manifest_path": "config/experiment-v1/seeds-development.json",
            "seed_manifest_sha256": sha256(CONFIG / "seeds-development.json"),
            "feature_definition_path": "config/experiment-v1/features-v1.json",
            "feature_definition_sha256": sha256(CONFIG / "features-v1.json"),
            "rows": 1_004_000,
            "feature_dimension": 85,
            "raw_total_bytes": raw_total_bytes,
            "raw_files": [result["dataset"] for result in seed_results],
            "aggregate": {
                "path": aggregate_path.relative_to(ROOT).as_posix(),
                "sha256": compression["sha256"],
                "size_bytes": compression["size_bytes"],
                "compression_command": compression["command"],
                "logical_rows": 1_004_000,
                "header_rows": 1,
            },
            "success_rows": sum(item["success_rows"] for item in dataset_summaries),
            "unique_dual_verified_successes": len(verified_successes),
            "validation_seed_rows": 0,
            "e3_holdout_seed_rows": 0,
            "target_44_rows": 0,
        }
        write_json(out / "dataset-manifest.json", dataset_manifest)
        write_json(out / "dataset-summaries.json", dataset_summaries)
        write_json(out / "seed-results.json", seed_results)
        write_json(out / "success-index.json", {"verified": list(verified_successes.values()), "references": success_references})
        write_json(out / "trajectory-audit.json", trajectory_audit)
        status = "PASS"
        log_lines.append("PASS: instrumented-off, instrumented-on, and frozen B2 seed-1 sequences agree at 50200 evaluations.")
        log_lines.append("PASS: all 20 development seeds exactly reproduced their frozen B2 final candidate sequences.")
        log_lines.append(
            f"PASS: 1004000 rows validated; {dataset_manifest['success_rows']} success rows map to {len(verified_successes)} dual-verified unique candidates."
        )
        log_lines.append(
            f"PASS: dataset aggregate {compression['sha256']} is immutable at {aggregate_path.relative_to(ROOT)}."
        )
    except FrontierStop as exc:
        status = "INVALID"
        error = str(exc)
        log_lines.append(f"UNEXPECTED_44_STOP: {error}")
    except VerificationFailure as exc:
        status = "INVALID"
        error = str(exc)
        log_lines.append(f"INVALID: {error}")
    except Exception as exc:
        status = "FAIL"
        error = str(exc)
        log_lines.append(f"FAIL: {error}")

    write_json(
        out / "cache-reference.json",
        {
            "path": cache.relative_to(ROOT).as_posix(),
            "exists": cache.is_dir(),
            "files": [
                {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path), "size_bytes": path.stat().st_size}
                for path in sorted(cache.glob("*"))
                if path.is_file()
            ],
        },
    )
    ended = datetime.now(timezone.utc)
    self_usage = resource.getrusage(resource.RUSAGE_SELF)
    child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    peak_rss = int(max(self_usage.ru_maxrss, child_usage.ru_maxrss) if sys.platform == "darwin" else max(self_usage.ru_maxrss, child_usage.ru_maxrss) * 1024)
    manifest = {
        "schema_version": "s13-method-evidence-manifest/v1",
        "run_id": run_id,
        "gate": "E1",
        "source_commit": source_commit,
        "dirty_at_start": False,
        "command": [sys.executable, "tools/e1_dataset_gate.py"],
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "wall_seconds": round(time.perf_counter() - started_perf, 6),
        "cpu_seconds": round(time.process_time() - started_cpu, 6),
        "peak_rss_bytes": peak_rss,
        "threads": 1,
        "host": host,
        "config_sha256": prerequisite["config_sha256"],
        "status": status,
    }
    if error is not None:
        manifest["error"] = error
    write_json(out / "manifest.json", manifest)
    (out / "command.txt").write_text(f"{sys.executable} tools/e1_dataset_gate.py\n", encoding="utf-8")
    (out / "stdout.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    (out / "stderr.txt").write_text("", encoding="utf-8")
    write_checksums(out)
    for line in log_lines:
        print(line)
    print(f"evidence: {out.relative_to(ROOT)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
