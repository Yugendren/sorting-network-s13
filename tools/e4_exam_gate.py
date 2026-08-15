#!/usr/bin/env python3
"""Run the single frozen 60-pair Mericanii V2 matched-compute exam."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import random
import resource
import subprocess
import sys
import time
from typing import Any

if __package__:
    from tools.e1_dataset_gate import host_record, load_active
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
    from e1_dataset_gate import host_record, load_active
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
E4_CONFIG = CONFIG / "e4"
CONTRACT = ROOT / "METHOD_EXPERIMENT_CONTRACT_V1.md"
CONTRACT_SHA256 = "6d8e9c3d0c4719bbd4c28bf55bc068ead10407e4a5928978afc55be338e503e6"
CONFIG_SHA256 = "8cfe3a2cdc2095a8477a39a196407861473fcf7530d75d0570bf9fe38ebda3fc"
CHANGE_SHA256 = "06ae75520aefde309e7a60a60cb0af84b20f23b3727b8c781b8cd7a5788bb3ac"
EXAM_SHA256 = "9c180ea2a0b3d3bd6763cabb3aba1130f1f32339c1d405e4664076a0ad7101d9"
MODEL_CONFIG_SHA256 = "16b8aa4371f7cfae4a2ff4902e2b56a61cc9746a8c66f7d9e9c0147c847d8452"
SEEDS_SHA256 = "b408752e404b3cfa2fb55b3fbaac5377e098128ddf3f04bbe43d6821d5a77b82"
TRAIN = ROOT / "evidence/e4/e4-train-20260815T032452Z"
TRAIN_MANIFEST_SHA256 = "0128da00420a5365d4e39c16b3020392be405b91de3109cfc0090f2c80b1f95f"
SELECTED_MODEL_SHA256 = "7d3311d6d2bcc121423005328c010872198bd084b11c98e5a55a9165cd281ef8"
MODEL_ROOT = TRAIN / "replay-1/artifacts"
MODEL_HEADER_SHA256 = "b2caca36602a0fb86ff1f3cb6310ebdd2f3e1b1c420667c426034161334fc984"
MODEL_EXPORT_SHA256 = "7c7ec61f499e37c290a8e1040374daceac3df29fe6f11354472b896c847e9e6a"
MODEL_FIXTURE_SHA256 = "0b63002e366c3e55cb9bd1715510de726293b05fa4f9c38cf78314ff7895c95a"
MODEL_CHECKPOINT_SHA256 = "60af80b18701f0c93276134b95e8f7ce554c20163020b03ec2d32d8ffe53383f"
METHOD_PATCH_SHA256 = "f2d8fd259f1ceab62e2e41f826f0573feb1d05cdbd4e17f5cf82df9960f1a132"
SENSO_MANIFEST_SHA256 = "24f47b42a966ed1b53553d4a77aca305af5cdd19ed12f44f0a8238210e5078e4"
SENSO_BINARY_SHA256 = "1d6fe20b547fa0e9dd9c899e34b608ac157104f63fd845d858e6e4ae9c0e6cc6"
METHOD_MANIFEST_SHA256 = "96ffbf06fb3135e636b283248d9daef72e59d851136acdc6c0ced0c02a7afd92"
METHOD_BINARY_SHA256 = "382e4a298f56bacf52d633ae80d08d3ede8590f5083e7726cf0a61d54d337fdf"
VERIFIER_A_SHA256 = "b420583606173d9f892e48e5656580792d2a4a2aa27a39f9a599ff5770e9ab2e"
VERIFIER_B_SOURCE_SHA256 = "a07336fb4d4d1b8c7b275fd00fe65173df3fd8cb4f9ebd017cc90e1ecea1ee2f"
VERIFIER_B = ROOT / ".build/b1/verifier-b"
VERIFIER_B_BINARY_SHA256 = "212805ebb2f71bfdc3a470a0e873167c6494fea0cea9829a8db889298368e3a2"
METHODS = ("frozen_senso", "frozen_mericanii_v2")
EVALUATIONS = 50_200
PARENT_ENVIRONMENT_ALLOWLIST = ("PATH", "TMPDIR", "USER", "LOGNAME", "SHELL")


class IntegrityFailure(RuntimeError):
    pass


class Unexpected44(RuntimeError):
    def __init__(self, result: dict[str, Any], directory: Path):
        super().__init__(f"verified {result['best_size']}-comparator candidate from {result['method']} seed {result['seed']}")
        self.result = result
        self.directory = directory


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


def percentile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("percentile requires values")
    ordered = sorted(values)
    location = (len(ordered) - 1) * probability
    lower = math.floor(location)
    upper = math.ceil(location)
    if lower == upper:
        return ordered[lower]
    fraction = location - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def numeric_summary(values: list[float]) -> dict[str, float]:
    if not values:
        raise ValueError("numeric summary requires values")
    return {
        "minimum": min(values),
        "q1": percentile(values, 0.25),
        "median": percentile(values, 0.5),
        "mean": sum(values) / len(values),
        "q3": percentile(values, 0.75),
        "maximum": max(values),
        "total": sum(values),
    }


def wilson_interval(successes: int, trials: int, z: float = 1.959963984540054) -> list[float]:
    if trials <= 0 or not 0 <= successes <= trials:
        raise ValueError("invalid Wilson interval counts")
    proportion = successes / trials
    denominator = 1.0 + z * z / trials
    center = (proportion + z * z / (2.0 * trials)) / denominator
    radius = z * math.sqrt(proportion * (1.0 - proportion) / trials + z * z / (4.0 * trials * trials)) / denominator
    lower = 0.0 if successes == 0 else max(0.0, center - radius)
    upper = 1.0 if successes == trials else min(1.0, center + radius)
    return [lower, upper]


def paired_bootstrap(effects: list[int], *, seed: int = 2026081502, resamples: int = 10_000) -> dict[str, Any]:
    if not effects or any(value not in (-1, 0, 1) for value in effects):
        raise ValueError("paired effects must be nonempty and in {-1,0,1}")
    rng = random.Random(seed)
    count = len(effects)
    samples = [sum(effects[rng.randrange(count)] for _ in range(count)) / count for _ in range(resamples)]
    return {
        "seed": seed,
        "resamples": resamples,
        "point_estimate": sum(effects) / count,
        "percentile_95": [percentile(samples, 0.025), percentile(samples, 0.975)],
    }


def run_order(ordinal: int) -> tuple[str, str]:
    if not 1 <= ordinal <= 60:
        raise ValueError("ordinal outside frozen E4 exam")
    return ("frozen_mericanii_v2", "frozen_senso") if ordinal % 2 else METHODS


def config_paths() -> list[Path]:
    return [*sorted(CONFIG.glob("*.json")), *sorted(path for path in E4_CONFIG.iterdir() if path.is_file())]


def prerequisite_check() -> dict[str, Any]:
    fixed = {
        CONTRACT: CONTRACT_SHA256,
        E4_CONFIG / "change-manifest.json": CHANGE_SHA256,
        E4_CONFIG / "exam-v2.json": EXAM_SHA256,
        E4_CONFIG / "model-v2.json": MODEL_CONFIG_SHA256,
        E4_CONFIG / "seeds-e4-holdout.json": SEEDS_SHA256,
        TRAIN / "manifest.json": TRAIN_MANIFEST_SHA256,
        TRAIN / "selected-model.json": SELECTED_MODEL_SHA256,
        MODEL_ROOT / "MericaniiModelV1Weights.hpp": MODEL_HEADER_SHA256,
        MODEL_ROOT / "model-export.json": MODEL_EXPORT_SHA256,
        MODEL_ROOT / "model-inference-fixture.json": MODEL_FIXTURE_SHA256,
        MODEL_ROOT / "checkpoint.pt": MODEL_CHECKPOINT_SHA256,
        ROOT / "src/verifier_a.py": VERIFIER_A_SHA256,
        ROOT / "src/verifier_b.go": VERIFIER_B_SOURCE_SHA256,
        VERIFIER_B: VERIFIER_B_BINARY_SHA256,
    }
    for path, expected in fixed.items():
        if not path.is_file() or sha256(path) != expected:
            raise IntegrityFailure(f"frozen prerequisite mismatch: {path}")
    if aggregate_hash(config_paths()) != CONFIG_SHA256:
        raise IntegrityFailure("E4 configuration aggregate mismatch")

    change = json.loads((E4_CONFIG / "change-manifest.json").read_text(encoding="utf-8"))
    exam = json.loads((E4_CONFIG / "exam-v2.json").read_text(encoding="utf-8"))
    training = json.loads((MODEL_ROOT / "training-report.json").read_text(encoding="utf-8"))
    if change["selected_major_change"] != "learning_objective" or change["integration_change_allowed"]:
        raise IntegrityFailure("E4 one-change boundary mismatch")
    if training["e3_rows_used"] != 0 or training["e4_rows_used"] != 0 or training["target_44_used"]:
        raise IntegrityFailure("training leakage or target-44 use detected")
    if exam["paired_seed_count"] != 60 or exam["candidate_evaluations_per_method_per_seed"] != EVALUATIONS:
        raise IntegrityFailure("E4 exam budget mismatch")

    seed_path = E4_CONFIG / "seeds-e4-holdout.json"
    seeds = json.loads(seed_path.read_text(encoding="utf-8"))["seeds"]
    earlier: list[int] = []
    for name in ("seeds-development.json", "seeds-validation.json", "seeds-e3-holdout.json"):
        earlier.extend(json.loads((CONFIG / name).read_text(encoding="utf-8"))["seeds"])
    if len(seeds) != 60 or len(set(seeds)) != 60 or set(seeds) & set(earlier):
        raise IntegrityFailure("E4 seed partition mismatch or leakage")
    if sorted((ROOT / "evidence/e4").glob("e4-exam-*")):
        raise IntegrityFailure("single-use E4 exam has already been attempted")

    senso, senso_binary, senso_source, senso_manifest_sha = load_active(
        ROOT / ".build/senso/active.json", "s13-senso-build/v1"
    )
    method, method_binary, method_source, method_manifest_sha = load_active(
        ROOT / ".build/senso-mericanii-v2/active.json", "s13-senso-mericanii-build/v2"
    )
    if senso_manifest_sha != SENSO_MANIFEST_SHA256 or senso["binary_sha256"] != SENSO_BINARY_SHA256:
        raise IntegrityFailure("active SENSO differs from frozen baseline")
    if method_manifest_sha != METHOD_MANIFEST_SHA256 or method["binary_sha256"] != METHOD_BINARY_SHA256:
        raise IntegrityFailure("active Mericanii V2 build differs from frozen integration")
    if method["method_patch_sha256"] != METHOD_PATCH_SHA256 or method["model_header_sha256"] != MODEL_HEADER_SHA256:
        raise IntegrityFailure("active Mericanii V2 patch or weights mismatch")
    fixture = method.get("compiled_inference_check", {})
    if fixture.get("status") != "PASS" or fixture.get("rows") != 32 or fixture.get("max_absolute_error", 1) > fixture.get("tolerance", 0):
        raise IntegrityFailure("active Mericanii compiled inference check failed")

    replay = run_text([sys.executable, "tools/evidence_check.py"])
    return {
        "seeds": seeds,
        "seed_manifest_sha256": sha256(seed_path),
        "exam": exam,
        "change": change,
        "training": training,
        "senso": senso,
        "senso_binary": senso_binary,
        "senso_source": senso_source,
        "senso_manifest_sha256": senso_manifest_sha,
        "method": method,
        "method_binary": method_binary,
        "method_source": method_source,
        "method_manifest_sha256": method_manifest_sha,
        "evidence_replay": replay,
        "budget": json.loads((CONFIG / "budgets-v1.json").read_text(encoding="utf-8"))["local_search"],
    }


def run_attempt(
    directory: Path,
    *,
    method: str,
    seed: int,
    ordinal: int,
    binary: Path,
    source: Path,
    budget: dict[str, Any],
    phase: str,
) -> dict[str, Any]:
    directory = directory.resolve()
    binary = binary.resolve()
    source = source.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    inference_path = directory / "inference-stats.json"
    overrides = {"MERICANII_INFERENCE_STATS_PATH": str(inference_path)} if method == "frozen_mericanii_v2" else {}
    resource_record = run_limited(
        senso_command(binary, source, seed=seed),
        directory,
        cpu_limit=budget["per_seed_cpu_seconds"],
        wall_limit=budget["per_seed_wall_seconds"],
        memory_limit=budget["peak_rss_bytes"],
        environment_overrides=overrides,
        parent_environment_allowlist=PARENT_ENVIRONMENT_ALLOWLIST,
    )
    try:
        if resource_record["status"] != "PASS":
            raise IntegrityFailure(f"{phase} {method} seed {seed} ended {resource_record['status']}")
        milestones = sorted(directory.glob("milestone_g*.obm.gz"))
        if len(milestones) != 1:
            raise IntegrityFailure(f"{phase} {method} seed {seed} produced {len(milestones)} milestones")
        parsed = parse_milestone(milestones[0])
        if parsed["generation"] != 500 or parsed["evaluations"] != EVALUATIONS or parsed["channels"] != 13:
            raise IntegrityFailure(f"{phase} {method} seed {seed} budget/channel mismatch")
        comparators = parsed["comparators"]
        candidate = directory / "candidate.sortnet"
        candidate.write_bytes(candidate_bytes(13, comparators, f"e4-{phase}-{method}-seed-{seed}"))
        verification = verify_candidate(candidate, VERIFIER_B, directory)
        result: dict[str, Any] = {
            "schema_version": "s13-e4-attempt/v1",
            "phase": phase,
            "status": "PASS",
            "method": method,
            "ordinal": ordinal,
            "seed": seed,
            "generation": parsed["generation"],
            "evaluations": parsed["evaluations"],
            "best_size": len(comparators),
            "success45": len(comparators) <= 45,
            "comparator_sequence": [[lower, upper] for lower, upper in comparators],
            "resource": resource_record,
            "milestone_path": milestones[0].relative_to(ROOT).as_posix(),
            "milestone_sha256": sha256(milestones[0]),
            "candidate_path": candidate.relative_to(ROOT).as_posix(),
            "candidate_sha256": sha256(candidate),
            "verification": verification,
        }
        if method == "frozen_mericanii_v2":
            if not inference_path.is_file():
                raise IntegrityFailure(f"{phase} method seed {seed} omitted inference statistics")
            inference = json.loads(inference_path.read_text(encoding="utf-8"))
            if inference.get("rank_calls") != EVALUATIONS:
                raise IntegrityFailure(f"{phase} method seed {seed} rank-call mismatch")
            if not (EVALUATIONS <= inference.get("score_calls", 0) <= 8 * EVALUATIONS):
                raise IntegrityFailure(f"{phase} method seed {seed} score-call mismatch")
            if sum(inference.get("selected_proposal_histogram", [])) != EVALUATIONS:
                raise IntegrityFailure(f"{phase} method seed {seed} proposal histogram mismatch")
            result["inference_stats"] = inference
        write_json(directory / "result.json", result)
    except Exception as exc:
        write_json(
            directory / "attempt-failure.json",
            {
                "schema_version": "s13-e4-attempt-failure/v1",
                "phase": phase,
                "method": method,
                "ordinal": ordinal,
                "seed": seed,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "resource": resource_record,
            },
        )
        raise
    if result["best_size"] <= 44:
        raise Unexpected44(result, directory)
    return result


def result_path(out: Path, ordinal: int, seed: int, method: str) -> Path:
    return out / "runs" / f"seed-{ordinal:02d}-{seed}" / method / "result.json"


def reaggregate(out: Path, seeds: list[int]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    paired: list[dict[str, Any]] = []
    for ordinal, seed in enumerate(seeds, start=1):
        by_method: dict[str, dict[str, Any]] = {}
        for method in METHODS:
            path = result_path(out, ordinal, seed, method)
            result = json.loads(path.read_text(encoding="utf-8"))
            if result["seed"] != seed or result["ordinal"] != ordinal or result["method"] != method:
                raise IntegrityFailure(f"raw result identity mismatch: {path}")
            if result["evaluations"] != EVALUATIONS or result["status"] != "PASS":
                raise IntegrityFailure(f"raw result budget/status mismatch: {path}")
            candidate = ROOT / result["candidate_path"]
            if sha256(candidate) != result["candidate_sha256"]:
                raise IntegrityFailure(f"raw candidate hash mismatch: {candidate}")
            sequence = [[lower, upper] for lower, upper in parse_candidate(candidate)]
            if sequence != result["comparator_sequence"] or len(sequence) != result["best_size"]:
                raise IntegrityFailure(f"raw candidate sequence mismatch: {candidate}")
            verification = result["verification"]
            if verification["verifier_a"] != "ACCEPT" or verification["verifier_b"] != "ACCEPT":
                raise IntegrityFailure(f"raw verifier rejection: {candidate}")
            for name in ("a", "b"):
                report = path.parent / f"verifier-{name}.json"
                if sha256(report) != verification[f"verifier_{name}_report_sha256"]:
                    raise IntegrityFailure(f"raw verifier report hash mismatch: {report}")
                if json.loads(report.read_text(encoding="utf-8"))["verdict"] != "ACCEPT":
                    raise IntegrityFailure(f"raw verifier report rejection: {report}")
            if result["success45"] != (result["best_size"] <= 45):
                raise IntegrityFailure(f"raw success label mismatch: {path}")
            if method == "frozen_mericanii_v2" and result["inference_stats"]["rank_calls"] != EVALUATIONS:
                raise IntegrityFailure(f"raw inference count mismatch: {path}")
            by_method[method] = result
            results.append(result)
        baseline = by_method["frozen_senso"]
        mericanii = by_method["frozen_mericanii_v2"]
        paired.append(
            {
                "ordinal": ordinal,
                "seed": seed,
                "run_order": list(run_order(ordinal)),
                "senso_size": baseline["best_size"],
                "mericanii_size": mericanii["best_size"],
                "senso_success": baseline["success45"],
                "mericanii_success": mericanii["success45"],
                "paired_effect": int(mericanii["success45"]) - int(baseline["success45"]),
                "senso_wall_seconds": baseline["resource"]["wall_seconds"],
                "mericanii_wall_seconds": mericanii["resource"]["wall_seconds"],
            }
        )

    methods: dict[str, dict[str, Any]] = {}
    for method in METHODS:
        selected = [item for item in results if item["method"] == method]
        success_count = sum(item["success45"] for item in selected)
        wall = [float(item["resource"]["wall_seconds"]) for item in selected]
        cpu = [float(item["resource"]["cpu_seconds"]) for item in selected]
        sizes = Counter(item["best_size"] for item in selected)
        method_result: dict[str, Any] = {
            "attempts": len(selected),
            "successes": success_count,
            "success_rate": success_count / len(selected),
            "wilson_95": wilson_interval(success_count, len(selected)),
            "final_size_distribution": {str(key): sizes[key] for key in sorted(sizes)},
            "evaluations_total": sum(item["evaluations"] for item in selected),
            "evaluations_per_seed": sorted({item["evaluations"] for item in selected}),
            "wall_seconds": numeric_summary(wall),
            "cpu_seconds": numeric_summary(cpu),
            "wall_seconds_per_evaluation": sum(wall) / sum(item["evaluations"] for item in selected),
            "peak_rss_bytes_maximum": max(item["resource"]["peak_rss_bytes"] for item in selected),
        }
        if method == "frozen_mericanii_v2":
            inference = [item["inference_stats"] for item in selected]
            rank_ns = sum(item["rank_nanoseconds"] for item in inference)
            score_ns = sum(item["score_nanoseconds"] for item in inference)
            histogram = [sum(item["selected_proposal_histogram"][index] for item in inference) for index in range(8)]
            method_result["inference"] = {
                "rank_calls": sum(item["rank_calls"] for item in inference),
                "score_calls": sum(item["score_calls"] for item in inference),
                "rank_seconds": rank_ns / 1e9,
                "model_score_seconds": score_ns / 1e9,
                "rank_fraction_of_method_wall": (rank_ns / 1e9) / sum(wall),
                "model_score_fraction_of_method_wall": (score_ns / 1e9) / sum(wall),
                "selected_proposal_histogram": histogram,
            }
        methods[method] = method_result

    effects = [item["paired_effect"] for item in paired]
    outcomes = Counter(
        (item["senso_success"], item["mericanii_success"])
        for item in paired
    )
    return {
        "schema_version": "s13-e4-exam-aggregation/v1",
        "paired_seed_count": len(seeds),
        "dual_verified_attempts": len(results),
        "methods": methods,
        "paired_outcome_counts": {
            "both_success": outcomes[(True, True)],
            "senso_only": outcomes[(True, False)],
            "mericanii_only": outcomes[(False, True)],
            "neither": outcomes[(False, False)],
        },
        "paired_effect": paired_bootstrap(effects),
        "paired_results": paired,
    }


def replay_successes(out: Path, aggregation: dict[str, Any]) -> dict[str, Any]:
    destination = out / "integrity" / "success-verifier-replay"
    destination.mkdir(parents=True)
    replayed: list[dict[str, Any]] = []
    for pair in aggregation["paired_results"]:
        for method, key in (("frozen_senso", "senso_success"), ("frozen_mericanii_v2", "mericanii_success")):
            if not pair[key]:
                continue
            raw_path = result_path(out, pair["ordinal"], pair["seed"], method)
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            replay_dir = destination / f"seed-{pair['ordinal']:02d}-{pair['seed']}-{method}"
            replay_dir.mkdir()
            candidate = ROOT / raw["candidate_path"]
            verification = verify_candidate(candidate, VERIFIER_B, replay_dir)
            if verification["artifact_sha256"] != raw["verification"]["artifact_sha256"]:
                raise IntegrityFailure(f"success verifier replay artifact mismatch: {candidate}")
            item = {
                "ordinal": pair["ordinal"],
                "seed": pair["seed"],
                "method": method,
                "candidate_path": raw["candidate_path"],
                "candidate_sha256": raw["candidate_sha256"],
                "verification": verification,
            }
            write_json(replay_dir / "result.json", item)
            replayed.append(item)
    result = {"status": "PASS", "successes_replayed": len(replayed), "results": replayed}
    write_json(destination / "index.json", result)
    return result


def rebuild_for_integrity(out: Path, run_id: str) -> dict[str, Any]:
    directory = out / "integrity" / "rebuild"
    directory.mkdir(parents=True)
    command = [sys.executable, "tools/e4_integrity_rebuild.py", "--run-id", run_id]
    write_json(directory / "command.json", {"command": command, "cwd": ROOT.as_posix()})
    started = time.perf_counter()
    with (directory / "stdout.txt").open("wb") as stdout, (directory / "stderr.txt").open("wb") as stderr:
        completed = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr, check=False)
    record = {"exit_code": completed.returncode, "wall_seconds": round(time.perf_counter() - started, 6)}
    write_json(directory / "resource.json", record)
    if completed.returncode != 0:
        raise IntegrityFailure("frozen integrity rebuild failed")
    summary_path = ROOT / ".build/e4-integrity" / run_id / "rebuild-summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("status") != "PASS":
        raise IntegrityFailure("frozen integrity rebuild summary is not PASS")
    write_json(directory / "rebuild-summary.json", summary)
    for label in ("senso", "mericanii_v2"):
        manifest_path = ROOT / summary[label]["manifest_path"]
        write_json(directory / f"{label}-build-manifest.json", json.loads(manifest_path.read_text(encoding="utf-8")))
    return summary


def replay_sentinels(
    out: Path,
    seeds: list[int],
    rebuild: dict[str, Any],
    budget: dict[str, Any],
) -> dict[str, Any]:
    destination = out / "integrity" / "sentinels"
    destination.mkdir(parents=True)
    rebuilt = {
        "frozen_senso": (
            ROOT / rebuild["senso"]["binary_path"],
            ROOT / rebuild["senso"]["source_path"],
        ),
        "frozen_mericanii_v2": (
            ROOT / rebuild["mericanii_v2"]["binary_path"],
            ROOT / rebuild["mericanii_v2"]["source_path"],
        ),
    }
    comparisons: list[dict[str, Any]] = []
    for ordinal in (1, 60):
        seed = seeds[ordinal - 1]
        for method in METHODS:
            binary, source = rebuilt[method]
            replay = run_attempt(
                destination / f"seed-{ordinal:02d}-{seed}" / method,
                method=method,
                seed=seed,
                ordinal=ordinal,
                binary=binary,
                source=source,
                budget=budget,
                phase="integrity-sentinel",
            )
            original = json.loads(result_path(out, ordinal, seed, method).read_text(encoding="utf-8"))
            exact = (
                replay["evaluations"] == original["evaluations"]
                and replay["comparator_sequence"] == original["comparator_sequence"]
            )
            if not exact:
                raise IntegrityFailure(f"sentinel replay mismatch for ordinal {ordinal} {method}")
            comparisons.append(
                {
                    "ordinal": ordinal,
                    "seed": seed,
                    "method": method,
                    "evaluations_exact": replay["evaluations"] == original["evaluations"],
                    "comparator_sequence_exact": replay["comparator_sequence"] == original["comparator_sequence"],
                    "original_candidate_sha256": original["candidate_sha256"],
                    "replay_candidate_sha256": replay["candidate_sha256"],
                }
            )
    result = {"status": "PASS", "comparisons": comparisons}
    write_json(destination / "index.json", result)
    return result


def gate_criteria(aggregation: dict[str, Any], *, integrity_pass: bool, no_holdout_tuning: bool) -> dict[str, bool]:
    baseline = aggregation["methods"]["frozen_senso"]
    method = aggregation["methods"]["frozen_mericanii_v2"]
    return {
        "every_claimed_candidate_dual_verified": aggregation["dual_verified_attempts"] == 120,
        "mericanii_at_least_12_of_60": method["successes"] >= 12,
        "mericanii_at_least_twice_senso": method["successes"] >= 2 * baseline["successes"],
        "mericanii_no_more_evaluations_per_seed": method["evaluations_per_seed"] == [EVALUATIONS]
        and baseline["evaluations_per_seed"] == [EVALUATIONS],
        "integrity_replay": integrity_pass,
        "no_holdout_data_used_for_tuning": no_holdout_tuning,
    }


def render_report(
    run_id: str,
    source_commit: str,
    aggregation: dict[str, Any] | None,
    criteria: dict[str, bool] | None,
    decision: str,
    integrity: dict[str, Any] | None,
    error: str | None,
) -> str:
    lines = [
        "# Mericanii method V2 frozen E4 exam report",
        "",
        f"Run: `{run_id}`  ",
        f"Tested commit: `{source_commit}`  ",
        f"Gate decision: `{decision}`",
        "",
        "This is the final method exam, not the canonical terminal goal report.",
        "",
        "## Frozen identities",
        "",
        f"- ARTIFACT_VERIFIED contract SHA-256: `{CONTRACT_SHA256}`.",
        f"- ARTIFACT_VERIFIED E4 seed manifest SHA-256: `{SEEDS_SHA256}`.",
        f"- ARTIFACT_VERIFIED SENSO binary SHA-256: `{SENSO_BINARY_SHA256}`.",
        f"- ARTIFACT_VERIFIED Mericanii V2 binary SHA-256: `{METHOD_BINARY_SHA256}`.",
        f"- ARTIFACT_VERIFIED model checkpoint SHA-256: `{MODEL_CHECKPOINT_SHA256}`.",
        f"- ARTIFACT_VERIFIED unchanged integration patch SHA-256: `{METHOD_PATCH_SHA256}`.",
        "",
    ]
    if aggregation is not None and criteria is not None:
        baseline = aggregation["methods"]["frozen_senso"]
        method = aggregation["methods"]["frozen_mericanii_v2"]
        lines.extend(
            [
                "## Result",
                "",
                f"- LOCALLY_REPRODUCED SENSO successes: {baseline['successes']}/60; Wilson 95% interval {baseline['wilson_95'][0]:.4f}--{baseline['wilson_95'][1]:.4f}.",
                f"- LOCALLY_REPRODUCED Mericanii successes: {method['successes']}/60; Wilson 95% interval {method['wilson_95'][0]:.4f}--{method['wilson_95'][1]:.4f}.",
                f"- MEASURED paired success-rate effect: {aggregation['paired_effect']['point_estimate']:+.4f}; paired-bootstrap 95% interval {aggregation['paired_effect']['percentile_95'][0]:+.4f}--{aggregation['paired_effect']['percentile_95'][1]:+.4f}.",
                f"- MEASURED final-size distributions: SENSO `{json.dumps(baseline['final_size_distribution'], sort_keys=True)}`; Mericanii `{json.dumps(method['final_size_distribution'], sort_keys=True)}`.",
                f"- MEASURED wall seconds/evaluation: SENSO {baseline['wall_seconds_per_evaluation']:.9f}; Mericanii {method['wall_seconds_per_evaluation']:.9f}.",
                f"- MEASURED model ranking time: {method['inference']['rank_seconds']:.6f}s total ({method['inference']['rank_fraction_of_method_wall']:.4%} of method wall time); model-only score time {method['inference']['model_score_seconds']:.6f}s.",
                "",
                "## Six frozen criteria",
                "",
                *[f"- {'PASS' if passed else 'FAIL'}: `{name}`." for name, passed in criteria.items()],
                "",
                "## Complete paired outcomes",
                "",
                "| # | seed | order | SENSO size | SENSO success | V2 size | V2 success | effect | SENSO s | V2 s |",
                "|---:|---:|---|---:|:---:|---:|:---:|---:|---:|---:|",
            ]
        )
        for pair in aggregation["paired_results"]:
            order = " → ".join(pair["run_order"])
            lines.append(
                f"| {pair['ordinal']} | {pair['seed']} | {order} | {pair['senso_size']} | {'yes' if pair['senso_success'] else 'no'} | "
                f"{pair['mericanii_size']} | {'yes' if pair['mericanii_success'] else 'no'} | {pair['paired_effect']:+d} | "
                f"{pair['senso_wall_seconds']:.3f} | {pair['mericanii_wall_seconds']:.3f} |"
            )
    if integrity is not None:
        lines.extend(
            [
                "",
                "## Integrity replay",
                "",
                f"- LOCALLY_REPRODUCED clean-input rebuild: `{integrity['rebuild']['status']}`.",
                f"- LOCALLY_REPRODUCED successful candidates reverified: {integrity['success_replay']['successes_replayed']}.",
                f"- LOCALLY_REPRODUCED exact sentinel comparisons: {len(integrity['sentinels']['comparisons'])}/4.",
                "- LOCALLY_REPRODUCED raw results were reaggregated from disk; final recursive checksums were independently replayed.",
            ]
        )
    if error:
        lines.extend(["", "## Integrity error", "", f"`{error}`"])
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Target size 44 was not used for training, selection, scoring, or routine exam acceptance.",
            "- Failure here is a measured method result, not evidence that a 44-comparator network is impossible.",
            "- E5 remains forbidden unless this report says `E4_PASS`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        print(f"E4 exam preflight failed: cwd must be exactly {ROOT}", file=sys.stderr)
        return 2
    if run_text(["git", "branch", "--show-current"]) != "goal/s13-method-v1":
        print("E4 exam preflight failed: wrong branch", file=sys.stderr)
        return 2
    dirty = run_text(["git", "status", "--porcelain", "--untracked-files=all"])
    if dirty:
        print("E4 exam preflight failed: scored source tree is dirty", file=sys.stderr)
        print(dirty, file=sys.stderr)
        return 2

    prerequisite = prerequisite_check()
    source_commit = run_text(["git", "rev-parse", "HEAD"])
    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    started_cpu = time.process_time()
    run_id = started.strftime("e4-exam-%Y%m%dT%H%M%SZ")
    out = ROOT / "evidence/e4" / run_id
    out.mkdir(parents=True, exist_ok=False)
    (out / "runs").mkdir()
    host = host_record()
    status = "INVALID"
    decision = "E4_INVALID"
    error: str | None = None
    aggregation: dict[str, Any] | None = None
    criteria: dict[str, bool] | None = None
    integrity: dict[str, Any] | None = None
    log_lines: list[str] = []

    def emit(message: str) -> None:
        log_lines.append(message)
        print(message, flush=True)

    emit("E4 V2 falsifiable gate: all 60 paired seeds receive exactly 50,200 evaluations; all six frozen criteria must pass.")
    try:
        if host["disk_free_bytes_at_start"] < 20 * 1024**3:
            raise IntegrityFailure("less than 20 GiB free before the single-use E4 exam")
        write_json(
            out / "prerequisite.json",
            {
                "contract_sha256": CONTRACT_SHA256,
                "config_sha256": CONFIG_SHA256,
                "change_manifest_sha256": CHANGE_SHA256,
                "exam_config_sha256": EXAM_SHA256,
                "seed_manifest_sha256": prerequisite["seed_manifest_sha256"],
                "training_manifest_sha256": TRAIN_MANIFEST_SHA256,
                "selected_model_sha256": SELECTED_MODEL_SHA256,
                "model_checkpoint_sha256": MODEL_CHECKPOINT_SHA256,
                "senso_build_manifest_sha256": prerequisite["senso_manifest_sha256"],
                "method_build_manifest_sha256": prerequisite["method_manifest_sha256"],
                "verifier_a_sha256": VERIFIER_A_SHA256,
                "verifier_b_source_sha256": VERIFIER_B_SOURCE_SHA256,
                "verifier_b_binary_sha256": VERIFIER_B_BINARY_SHA256,
                "evidence_replay": prerequisite["evidence_replay"],
                "e3_training_rows_used": prerequisite["training"]["e3_rows_used"],
                "e4_training_rows_used": prerequisite["training"]["e4_rows_used"],
                "holdout_outcomes_observed_before_start": 0,
                "target_44_used": False,
            },
        )
        write_json(out / "senso-build-manifest.json", prerequisite["senso"])
        write_json(out / "mericanii-v2-build-manifest.json", prerequisite["method"])
        write_json(out / "host.json", host)

        completed_results: list[dict[str, Any]] = []
        for ordinal, seed in enumerate(prerequisite["seeds"], start=1):
            seed_root = out / "runs" / f"seed-{ordinal:02d}-{seed}"
            seed_root.mkdir()
            order = run_order(ordinal)
            for method in order:
                binary, source = (
                    (prerequisite["senso_binary"], prerequisite["senso_source"])
                    if method == "frozen_senso"
                    else (prerequisite["method_binary"], prerequisite["method_source"])
                )
                result = run_attempt(
                    seed_root / method,
                    method=method,
                    seed=seed,
                    ordinal=ordinal,
                    binary=binary,
                    source=source,
                    budget=prerequisite["budget"],
                    phase="exam",
                )
                completed_results.append(
                    {
                        "ordinal": ordinal,
                        "seed": seed,
                        "method": method,
                        "best_size": result["best_size"],
                        "success45": result["success45"],
                        "evaluations": result["evaluations"],
                        "result_sha256": sha256(seed_root / method / "result.json"),
                    }
                )
                write_json(out / "progress.json", {"completed": completed_results, "expected_attempts": 120})
                emit(
                    f"E4 {len(completed_results):03d}/120 ordinal={ordinal:02d} seed={seed} method={method} "
                    f"size={result['best_size']} success45={str(result['success45']).lower()} "
                    f"evals={result['evaluations']} wall={result['resource']['wall_seconds']:.3f}s"
                )

        aggregation = reaggregate(out, prerequisite["seeds"])
        write_json(out / "aggregation.json", aggregation)
        success_replay = replay_successes(out, aggregation)
        rebuild = rebuild_for_integrity(out, run_id)
        sentinels = replay_sentinels(out, prerequisite["seeds"], rebuild, prerequisite["budget"])
        integrity = {
            "schema_version": "s13-e4-integrity-replay/v1",
            "status": "PASS",
            "reaggregated_raw_attempts": 120,
            "rebuild": {"status": rebuild["status"], "summary": rebuild},
            "success_replay": success_replay,
            "sentinels": sentinels,
            "pre_exam_evidence_inventory": prerequisite["evidence_replay"],
        }
        write_json(out / "integrity-replay.json", integrity)
        criteria = gate_criteria(aggregation, integrity_pass=True, no_holdout_tuning=True)
        status = "PASS" if all(criteria.values()) else "FAIL"
        decision = "E4_PASS" if status == "PASS" else "E4_FAIL"
        write_json(out / "gate-criteria.json", criteria)
        baseline_successes = aggregation["methods"]["frozen_senso"]["successes"]
        method_successes = aggregation["methods"]["frozen_mericanii_v2"]["successes"]
        emit(f"LOCALLY_REPRODUCED: SENSO successes={baseline_successes}/60; Mericanii V2 successes={method_successes}/60.")
        for name, passed in criteria.items():
            emit(f"{'PASS' if passed else 'FAIL'}: {name}")
        emit(f"{decision}: the frozen version-2 matched-compute exam {'passed' if status == 'PASS' else 'did not pass'}.")
    except Unexpected44 as exc:
        status = "PASS"
        decision = "UNEXPECTED_44_STOP"
        write_json(
            out / "unexpected-44.json",
            {
                "status": "FROZEN",
                "reason": str(exc),
                "result": exc.result,
                "directory": exc.directory.relative_to(ROOT).as_posix(),
                "next_action": "E5 witness audit only; no further search",
            },
        )
        emit(f"UNEXPECTED_44_STOP: {exc}")
    except (VerificationFailure, IntegrityFailure) as exc:
        status = "INVALID"
        decision = "E4_INVALID"
        error = str(exc)
        emit(f"INVALID: {error}")
    except Exception as exc:
        status = "INVALID"
        decision = "E4_INVALID"
        error = f"{type(exc).__name__}: {exc}"
        emit(f"INVALID: {error}")

    (out / "exam-report.md").write_text(
        render_report(run_id, source_commit, aggregation, criteria, decision, integrity, error),
        encoding="utf-8",
    )
    ended = datetime.now(timezone.utc)
    self_usage = resource.getrusage(resource.RUSAGE_SELF)
    child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    multiplier = 1 if sys.platform == "darwin" else 1024
    manifest = {
        "schema_version": "s13-method-evidence-manifest/v1",
        "run_id": run_id,
        "gate": "E4",
        "source_commit": source_commit,
        "dirty_at_start": False,
        "command": [sys.executable, "tools/e4_exam_gate.py"],
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "wall_seconds": round(time.perf_counter() - started_perf, 6),
        "cpu_seconds": round(time.process_time() - started_cpu, 6),
        "peak_rss_bytes": int(max(self_usage.ru_maxrss, child_usage.ru_maxrss) * multiplier),
        "threads": 1,
        "host": host,
        "config_sha256": CONFIG_SHA256,
        "status": status,
    }
    if error is not None:
        manifest["error"] = error
    write_json(out / "manifest.json", manifest)
    write_json(
        out / "terminal-state.json",
        {
            "gate_decision": decision,
            "terminal_goal_verdict_pending": True,
            "next_stage": "witness_audit" if decision == "UNEXPECTED_44_STOP" else "terminal_report" if decision != "E4_PASS" else "E5_freeze",
        },
    )
    (out / "command.txt").write_text(f"{sys.executable} tools/e4_exam_gate.py\n", encoding="utf-8")
    (out / "stdout.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    (out / "stderr.txt").write_text("", encoding="utf-8")
    write_checksums(out)

    inventory_replay = run_text([sys.executable, "tools/evidence_check.py"])
    (out / "inventory-replay.txt").write_text(inventory_replay + "\n", encoding="utf-8")
    write_checksums(out)
    final_replay = run_text([sys.executable, "tools/evidence_check.py"])
    print(final_replay, flush=True)
    print(f"evidence: {out.relative_to(ROOT)}", flush=True)
    if decision in ("E4_PASS", "UNEXPECTED_44_STOP"):
        return 0
    return 1 if decision == "E4_FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
