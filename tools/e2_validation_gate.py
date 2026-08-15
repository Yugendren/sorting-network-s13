#!/usr/bin/env python3
"""Run the single-use E2 V1 validation and integration audit."""

from __future__ import annotations

from datetime import datetime, timezone
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

if __package__:
    from tools.e1_dataset_gate import (
        FrontierStop,
        compress_dataset,
        host_record,
        load_active,
        validate_dataset,
        verify_success_sequences,
    )
    from tools.method_runtime import (
        ROOT,
        VerificationFailure,
        aggregate_hash,
        candidate_bytes,
        parse_milestone,
        run_limited,
        senso_command,
        sha256,
        verify_candidate,
        write_checksums,
        write_json,
    )
else:
    from e1_dataset_gate import (
        FrontierStop,
        compress_dataset,
        host_record,
        load_active,
        validate_dataset,
        verify_success_sequences,
    )
    from method_runtime import (
        ROOT,
        VerificationFailure,
        aggregate_hash,
        candidate_bytes,
        parse_milestone,
        run_limited,
        senso_command,
        sha256,
        verify_candidate,
        write_checksums,
        write_json,
    )


CONFIG = ROOT / "config/experiment-v1"
CONTRACT = ROOT / "METHOD_EXPERIMENT_CONTRACT_V1.md"
CONTRACT_SHA256 = "6d8e9c3d0c4719bbd4c28bf55bc068ead10407e4a5928978afc55be338e503e6"
E2_TRAIN = ROOT / "evidence/e2/e2-train-20260815T023758Z"
E2_TRAIN_MANIFEST_SHA256 = "2ff8fc719428d62b87aa3c50b785f4a2b42581be780f93fd675065ff3f893074"
MODEL_ROOT = E2_TRAIN / "replay-1/artifacts"
MODEL_HEADER = MODEL_ROOT / "MericaniiModelV1Weights.hpp"
MODEL_EXPORT = MODEL_ROOT / "model-export.json"
MODEL_FIXTURE = MODEL_ROOT / "model-inference-fixture.json"
MODEL_CHECKPOINT = MODEL_ROOT / "checkpoint.pt"
MODEL_HEADER_SHA256 = "f7533479d67d44ff5b5da7e9dd3cad9909785e7a912997b8c2b2edfc8fd69864"
MODEL_EXPORT_SHA256 = "eb606f4f6712a1eaa53bde8d36c0c8280c635c73453d22a861112ccf356babb7"
MODEL_FIXTURE_SHA256 = "428ef8f0b67c2f05f923501d23f85ad4690f79e310fbe77039b44294c71c15bc"
MODEL_CHECKPOINT_SHA256 = "ad736315f79493ffccaee6418a4d95624282374bb6e844d0001346dd88d617ab"
METHOD_PATCH_SHA256 = "f2d8fd259f1ceab62e2e41f826f0573feb1d05cdbd4e17f5cf82df9960f1a132"
VERIFIER_B = ROOT / ".build/b1/verifier-b"
VERIFIER_B_SHA256 = "212805ebb2f71bfdc3a470a0e873167c6494fea0cea9829a8db889298368e3a2"
EXPECTED_CONFIG_SHA256 = "5c22a3ce05504045ceaa7359a7b25d318cc0a923163b162779c32975c2533465"


def run_text(command: list[str], *, check: bool = True) -> str:
    completed = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if check and completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}\n{completed.stdout}")
    return completed.stdout.strip()


def prerequisite_check() -> dict[str, Any]:
    if sha256(CONTRACT) != CONTRACT_SHA256:
        raise RuntimeError("active method contract hash mismatch")
    train_manifest = E2_TRAIN / "manifest.json"
    if sha256(train_manifest) != E2_TRAIN_MANIFEST_SHA256:
        raise RuntimeError("accepted E2 training manifest hash mismatch")
    if json.loads(train_manifest.read_text(encoding="utf-8"))["status"] != "PASS":
        raise RuntimeError("accepted E2 training subgate is not PASS")
    expected_model = {
        MODEL_HEADER: MODEL_HEADER_SHA256,
        MODEL_EXPORT: MODEL_EXPORT_SHA256,
        MODEL_FIXTURE: MODEL_FIXTURE_SHA256,
        MODEL_CHECKPOINT: MODEL_CHECKPOINT_SHA256,
    }
    for path, expected in expected_model.items():
        if sha256(path) != expected:
            raise RuntimeError(f"frozen model artifact hash mismatch: {path}")
    if sha256(VERIFIER_B) != VERIFIER_B_SHA256:
        raise RuntimeError("frozen verifier-B binary hash mismatch")
    config_hash = aggregate_hash(sorted(CONFIG.glob("*.json")))
    if config_hash != EXPECTED_CONFIG_SHA256:
        raise RuntimeError("experiment config aggregate differs from E0")
    replay = run_text([sys.executable, "tools/evidence_check.py"])

    instrumented, instrumented_binary, instrumented_source, instrumented_manifest_sha = load_active(
        ROOT / ".build/senso-instrumented/active.json", "s13-senso-instrumented-build/v1"
    )
    method, method_binary, method_source, method_manifest_sha = load_active(
        ROOT / ".build/senso-mericanii-v1/active.json", "s13-senso-mericanii-build/v1"
    )
    if method["method_patch_sha256"] != METHOD_PATCH_SHA256 or method["model_header_sha256"] != MODEL_HEADER_SHA256:
        raise RuntimeError("active method build differs from frozen V1 patch/model")
    fixture = method.get("compiled_inference_check", {})
    if fixture.get("status") != "PASS" or fixture.get("max_absolute_error") != 0 or fixture.get("rows") != 32:
        raise RuntimeError("active method build lacks exact compiled inference replay")

    validation_path = CONFIG / "seeds-validation.json"
    validation = json.loads(validation_path.read_text(encoding="utf-8"))["seeds"]
    development = set(json.loads((CONFIG / "seeds-development.json").read_text(encoding="utf-8"))["seeds"])
    holdout = set(json.loads((CONFIG / "seeds-e3-holdout.json").read_text(encoding="utf-8"))["seeds"])
    if len(validation) != 20 or len(set(validation)) != 20 or set(validation) & (development | holdout):
        raise RuntimeError("validation seed partition mismatch or leakage")
    prior_evidence = sorted((ROOT / "evidence/e2").glob("e2-validation-*"))
    prior_cache = sorted((ROOT / ".cache/method-v1/validation").glob("e2-validation-*")) if (ROOT / ".cache/method-v1/validation").is_dir() else []
    if prior_evidence or prior_cache:
        raise RuntimeError("single-use E2 validation has already been materialized")
    return {
        "evidence_replay": replay,
        "config_sha256": config_hash,
        "validation_seed_manifest_sha256": sha256(validation_path),
        "validation_seeds": validation,
        "instrumented": instrumented,
        "instrumented_binary": instrumented_binary,
        "instrumented_source": instrumented_source,
        "instrumented_manifest_sha256": instrumented_manifest_sha,
        "method": method,
        "method_binary": method_binary,
        "method_source": method_source,
        "method_manifest_sha256": method_manifest_sha,
    }


def finalize_search_run(
    directory: Path,
    *,
    seed: int,
    resource_record: dict[str, Any],
    source_label: str,
) -> tuple[dict[str, Any], list[tuple[int, int]]]:
    if resource_record["status"] != "PASS":
        raise RuntimeError(f"search run failed for seed {seed}: {resource_record['status']}")
    milestones = sorted(directory.glob("milestone_g*.obm.gz"))
    if len(milestones) != 1:
        raise RuntimeError(f"seed {seed}: expected one milestone, found {len(milestones)}")
    parsed = parse_milestone(milestones[0])
    if parsed["generation"] != 500 or parsed["evaluations"] != 50_200 or parsed["channels"] != 13:
        raise RuntimeError(f"seed {seed}: milestone generation/evaluation/channel mismatch")
    comparators = parsed["comparators"]
    candidate = directory / "candidate.sortnet"
    candidate.write_bytes(candidate_bytes(13, comparators, source_label))
    verification = verify_candidate(candidate, VERIFIER_B, directory)
    if len(comparators) <= 44:
        sequence = ";".join(f"{lower}-{upper}" for lower, upper in comparators)
        raise FrontierStop(sequence, seed, -1)
    result = {
        "status": "PASS",
        "seed": seed,
        "generation": parsed["generation"],
        "evaluations": parsed["evaluations"],
        "best_size": len(comparators),
        "resource": resource_record,
        "milestone_sha256": sha256(milestones[0]),
        "milestone_size_bytes": milestones[0].stat().st_size,
        "candidate_sha256": sha256(candidate),
        "verification": verification,
    }
    write_json(directory / "result.json", result)
    return result, comparators


def compile_scorer(out: Path) -> tuple[Path, dict[str, Any]]:
    build = out / "compiled-validation-scorer"
    build.mkdir()
    binary = build / "score-validation-model"
    command = [
        "clang++", "-std=c++11", "-O2", "-I", str(MODEL_ROOT),
        str(ROOT / "tools/score_validation_model.cpp"), "-o", str(binary),
    ]
    completed = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    (build / "compile.stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (build / "compile.stderr.txt").write_text(completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(f"validation scorer compilation failed with exit {completed.returncode}")
    record = {
        "command": command,
        "source_path": "tools/score_validation_model.cpp",
        "source_sha256": sha256(ROOT / "tools/score_validation_model.cpp"),
        "model_header_sha256": sha256(MODEL_HEADER),
        "binary_path": binary.relative_to(ROOT).as_posix(),
        "binary_sha256": sha256(binary),
        "compiler": subprocess.check_output(["clang++", "--version"], text=True).splitlines()[0],
    }
    write_json(build / "build.json", record)
    return binary, record


def score_dataset(out: Path, dataset: Path, scorer: Path, local_budget: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    directory = out / "validation-scoring"
    directory.mkdir()
    result_path = directory / "validation-score.json"
    command = [
        sys.executable,
        str(ROOT / "tools/score_validation_stream.py"),
        "--dataset", str(dataset),
        "--scorer", str(scorer),
        "--output", str(result_path),
        "--decompress-stderr", str(directory / "decompress.stderr"),
        "--scorer-stderr", str(directory / "scorer.stderr"),
    ]
    resources = run_limited(
        command,
        directory,
        cpu_limit=local_budget["per_seed_cpu_seconds"],
        wall_limit=local_budget["per_seed_wall_seconds"],
        memory_limit=local_budget["peak_rss_bytes"],
    )
    if resources["status"] != "PASS":
        raise RuntimeError(f"offline validation scoring failed: {resources['status']}")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if (directory / "decompress.stderr").read_bytes() or (directory / "scorer.stderr").read_bytes():
        raise RuntimeError("offline validation scoring emitted stderr")
    return result, resources


def render_report(
    run_id: str,
    source_commit: str,
    metric: dict[str, Any] | None,
    dataset_manifest: dict[str, Any] | None,
    integration: dict[str, Any] | None,
    status: str,
    error: str | None,
) -> str:
    decision = "E2_PASS" if status == "PASS" else "E2_FAIL" if metric is not None else status
    lines = [
        "# Mericanii method V1 validation report",
        "",
        f"Run: `{run_id}`  ",
        f"Tested commit: `{source_commit}`  ",
        f"Gate decision: `{decision}`",
        "",
        "This is an E2 gate decision, not a terminal goal verdict.",
        "",
        "## Frozen identities",
        "",
        f"- ARTIFACT_VERIFIED contract SHA-256: `{CONTRACT_SHA256}`.",
        f"- ARTIFACT_VERIFIED model export SHA-256: `{MODEL_EXPORT_SHA256}`.",
        f"- ARTIFACT_VERIFIED model checkpoint SHA-256: `{MODEL_CHECKPOINT_SHA256}`.",
        "- ASSUMED primary aggregation fixed before execution: micro-average over all unequal-final-size pairs within each seed; exact score ties contribute 0.5.",
        "",
        "## Result",
        "",
    ]
    if metric is not None and dataset_manifest is not None:
        lines.extend(
            [
                f"- LOCALLY_REPRODUCED rows: {metric['row_count']:,} across {metric['seed_count']} frozen validation seeds.",
                f"- MEASURED comparable within-seed pairs: {metric['comparable_pairs']:,}.",
                f"- MEASURED micro concordance: {metric['micro_concordance']:.12f}.",
                f"- MEASURED macro seed concordance: {metric['macro_concordance']:.12f}.",
                f"- LOCALLY_REPRODUCED <=45 label rows: {dataset_manifest['success_rows']:,}; all unique successes were checked by both frozen verifiers.",
                f"- Gate threshold: strictly greater than 0.5; result: {'PASS' if status == 'PASS' else 'FAIL'}.",
            ]
        )
    if integration is not None:
        stats = integration["inference_stats"]
        lines.extend(
            [
                "",
                "## Frozen integration audit",
                "",
                f"- LOCALLY_REPRODUCED seed: {integration['seed']}.",
                f"- LOCALLY_REPRODUCED evaluations: {integration['evaluations']:,}.",
                f"- LOCALLY_REPRODUCED final comparator count: {integration['best_size']} (accepted by both verifiers).",
                f"- MEASURED rank calls / model score calls: {stats['rank_calls']:,} / {stats['score_calls']:,}.",
                f"- MEASURED total ranking / model-only time: {stats['rank_nanoseconds'] / 1e9:.6f}s / {stats['score_nanoseconds'] / 1e9:.6f}s.",
            ]
        )
    if error:
        lines.extend(["", "## Error", "", f"`{error}`"])
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- UNKNOWN: E3 final-holdout performance; no E3 seed was executed or used for tuning here.",
            "- UNKNOWN: existence of a 44-comparator network; target 44 was not used in this gate.",
            "- No configuration change is permitted after this validation result.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        print(f"E2 validation preflight failed: cwd must be exactly {ROOT}", file=sys.stderr)
        return 2
    if run_text(["git", "branch", "--show-current"]) != "goal/s13-method-v1":
        print("E2 validation preflight failed: wrong branch", file=sys.stderr)
        return 2
    dirty = run_text(["git", "status", "--porcelain", "--untracked-files=all"])
    if dirty:
        print("E2 validation preflight failed: scored configuration is dirty", file=sys.stderr)
        print(dirty, file=sys.stderr)
        return 2

    prerequisite = prerequisite_check()
    source_commit = run_text(["git", "rev-parse", "HEAD"])
    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    started_cpu = time.process_time()
    run_id = started.strftime("e2-validation-%Y%m%dT%H%M%SZ")
    out = ROOT / "evidence/e2" / run_id
    cache = ROOT / ".cache/method-v1/validation" / run_id
    out.mkdir(parents=True, exist_ok=False)
    cache.mkdir(parents=True, exist_ok=False)
    success_root = out / "successes"
    success_root.mkdir()
    host = host_record()
    status = "FAIL"
    error: str | None = None
    log_lines = ["E2 V1 falsifiable gate: micro within-seed validation concordance must be strictly greater than 0.5 and compiled integration must replay exactly."]
    seed_results: list[dict[str, Any]] = []
    dataset_summaries: list[dict[str, Any]] = []
    dataset_paths: list[Path] = []
    verified_successes: dict[str, dict[str, Any]] = {}
    success_references: list[dict[str, Any]] = []
    dataset_manifest: dict[str, Any] | None = None
    metric: dict[str, Any] | None = None
    integration: dict[str, Any] | None = None
    scorer_build: dict[str, Any] | None = None

    try:
        write_json(
            out / "prerequisite.json",
            {
                "contract_sha256": CONTRACT_SHA256,
                "e2_training_manifest_sha256": E2_TRAIN_MANIFEST_SHA256,
                "evidence_replay": prerequisite["evidence_replay"],
                "config_sha256": prerequisite["config_sha256"],
                "validation_seed_manifest_sha256": prerequisite["validation_seed_manifest_sha256"],
                "instrumented_manifest_sha256": prerequisite["instrumented_manifest_sha256"],
                "method_manifest_sha256": prerequisite["method_manifest_sha256"],
                "model_export_sha256": MODEL_EXPORT_SHA256,
                "model_checkpoint_sha256": MODEL_CHECKPOINT_SHA256,
                "verifier_b_binary_sha256": VERIFIER_B_SHA256,
                "no_e3_seed_accessed": True,
            },
        )
        write_json(out / "instrumented-build-manifest.json", prerequisite["instrumented"])
        write_json(out / "method-build-manifest.json", prerequisite["method"])
        budgets = json.loads((CONFIG / "budgets-v1.json").read_text(encoding="utf-8"))
        local_budget = budgets["local_search"]
        if host["disk_free_bytes_at_start"] < 20 * 1024**3:
            raise RuntimeError("less than 20 GiB free before single-use validation materialization")

        for ordinal, seed in enumerate(prerequisite["validation_seeds"], start=1):
            seed_dir = out / f"label-seed-{ordinal:02d}-{seed}"
            seed_dir.mkdir()
            dataset_path = cache / f"seed-{ordinal:02d}-{seed}.tsv"
            resource_record = run_limited(
                senso_command(prerequisite["instrumented_binary"], prerequisite["instrumented_source"], seed=seed),
                seed_dir,
                cpu_limit=local_budget["per_seed_cpu_seconds"],
                wall_limit=local_budget["per_seed_wall_seconds"],
                memory_limit=local_budget["peak_rss_bytes"],
                environment_overrides={"MERICANII_DATASET_PATH": str(dataset_path), "MERICANII_DATASET_SEED": str(seed)},
            )
            if resource_record["status"] != "PASS" and dataset_path.is_file():
                validate_dataset(dataset_path, seed, expected_rows=None)
            result, _ = finalize_search_run(
                seed_dir,
                seed=seed,
                resource_record=resource_record,
                source_label=f"e2-validation-label-seed-{seed}",
            )
            summary, successes = validate_dataset(dataset_path, seed, expected_rows=50_200)
            references = verify_success_sequences(successes, success_root, verified_successes, seed=seed)
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
                f"E2 validation label {ordinal:02d}/20 seed={seed}: PASS rows={summary['rows']} positives={summary['success_rows']} final={result['best_size']}",
                flush=True,
            )

        if sum(item["rows"] for item in dataset_summaries) != 1_004_000:
            raise RuntimeError("validation aggregate row count mismatch")
        if [item["seed"] for item in dataset_summaries] != prerequisite["validation_seeds"]:
            raise RuntimeError("validation dataset seed order mismatch")
        aggregate_path = cache / "validation-dataset.tsv.zst"
        compression = compress_dataset(dataset_paths, aggregate_path)
        aggregate_path.chmod(0o444)
        dataset_manifest = {
            "schema_version": "s13-validation-dataset-manifest/v1",
            "run_id": run_id,
            "source_commit": source_commit,
            "seed_manifest_path": "config/experiment-v1/seeds-validation.json",
            "seed_manifest_sha256": prerequisite["validation_seed_manifest_sha256"],
            "feature_definition_sha256": sha256(CONFIG / "features-v1.json"),
            "instrumented_binary_sha256": prerequisite["instrumented"]["binary_sha256"],
            "rows": 1_004_000,
            "feature_dimension": 85,
            "raw_total_bytes": sum(path.stat().st_size for path in dataset_paths),
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
            "development_seed_rows": 0,
            "e3_holdout_seed_rows": 0,
            "target_44_rows": 0,
        }
        write_json(out / "validation-dataset-manifest.json", dataset_manifest)
        write_json(out / "validation-dataset-summaries.json", dataset_summaries)
        write_json(out / "validation-seed-results.json", seed_results)
        write_json(out / "validation-success-index.json", {"verified": list(verified_successes.values()), "references": success_references})

        scorer, scorer_build = compile_scorer(out)
        metric, scoring_resources = score_dataset(out, aggregate_path, scorer, local_budget)
        metric["aggregation"] = "micro over unequal-final-size pairs within seeds; exact score ties contribute 0.5"
        metric["constant_score_reference"] = 0.5
        metric["model_header_sha256"] = MODEL_HEADER_SHA256
        metric["dataset_sha256"] = compression["sha256"]
        metric["scoring_resources"] = scoring_resources
        if metric["row_count"] != 1_004_000 or metric["seed_count"] != 20 or metric["comparable_pairs"] <= 0:
            raise RuntimeError("compiled validation score cardinality mismatch")
        scored_by_seed = {item["seed"]: item for item in metric["seed_results"]}
        if set(scored_by_seed) != set(prerequisite["validation_seeds"]):
            raise RuntimeError("compiled validation score seed set mismatch")
        for summary in dataset_summaries:
            scored = scored_by_seed[summary["seed"]]
            if scored["rows"] != 50_200 or scored["final_size_distribution"] != summary["final_size_distribution"]:
                raise RuntimeError(f"compiled score/label distribution mismatch for seed {summary['seed']}")
        write_json(out / "validation-metric.json", metric)

        audit_seed = prerequisite["validation_seeds"][0]
        audit_dir = out / f"integration-audit-seed-{audit_seed}"
        audit_dir.mkdir()
        inference_path = audit_dir / "inference-stats.json"
        audit_resource = run_limited(
            senso_command(prerequisite["method_binary"], prerequisite["method_source"], seed=audit_seed),
            audit_dir,
            cpu_limit=local_budget["per_seed_cpu_seconds"],
            wall_limit=local_budget["per_seed_wall_seconds"],
            memory_limit=local_budget["peak_rss_bytes"],
            environment_overrides={"MERICANII_INFERENCE_STATS_PATH": str(inference_path)},
        )
        audit_result, _ = finalize_search_run(
            audit_dir,
            seed=audit_seed,
            resource_record=audit_resource,
            source_label=f"e2-v1-integration-audit-seed-{audit_seed}",
        )
        inference = json.loads(inference_path.read_text(encoding="utf-8"))
        if inference.get("rank_calls") != 50_200 or not (50_200 <= inference.get("score_calls", 0) <= 8 * 50_200):
            raise RuntimeError("V1 integration inference call-count mismatch")
        if sum(inference.get("selected_proposal_histogram", [])) != 50_200:
            raise RuntimeError("V1 integration selected-proposal histogram mismatch")
        if audit_result["evaluations"] != seed_results[0]["evaluations"]:
            raise RuntimeError("V1 integration changed the candidate-evaluation budget")
        integration = {**audit_result, "inference_stats": inference, "baseline_label_result": seed_results[0]}
        write_json(audit_dir / "result.json", integration)
        write_json(out / "integration-audit.json", integration)

        validation_pass = metric["micro_concordance"] > 0.5
        status = "PASS" if validation_pass else "FAIL"
        log_lines.extend(
            [
                f"PASS: generated and validated 1004000 rows on exactly 20 frozen validation seeds; E3 rows=0.",
                f"PASS: compiled scorer used model header {MODEL_HEADER_SHA256} and {metric['comparable_pairs']} comparable within-seed pairs.",
                f"MEASURED: micro concordance={metric['micro_concordance']:.12f}; constant reference=0.5.",
                f"PASS: integration audit used exactly {integration['evaluations']} evaluations and {inference['rank_calls']} rank calls.",
                ("E2_PASS: V1 strictly beat the constant-score ranker." if validation_pass else "E2_FAIL: V1 did not strictly beat the constant-score ranker; E3 is forbidden for V1."),
            ]
        )
    except FrontierStop as exc:
        status = "INVALID"
        error = str(exc)
        log_lines.append(f"UNEXPECTED_44_STOP: {error}")
        unexpected = out / "unexpected-44"
        unexpected.mkdir(exist_ok=True)
        comparators = [tuple(int(value) for value in item.split("-")) for item in exc.sequence.split(";") if item]
        candidate = unexpected / "candidate.sortnet"
        candidate.write_bytes(candidate_bytes(13, comparators, "e2-unexpected-44-stop"))
        try:
            verification = verify_candidate(candidate, VERIFIER_B, unexpected)
            write_json(unexpected / "result.json", {"seed": exc.seed, "sample_index": exc.sample_index, "verification": verification})
        except Exception as verification_error:
            write_json(unexpected / "result.json", {"seed": exc.seed, "sample_index": exc.sample_index, "verification_error": str(verification_error)})
    except VerificationFailure as exc:
        status = "INVALID"
        error = str(exc)
        log_lines.append(f"INVALID: {error}")
    except Exception as exc:
        status = "FAIL"
        error = str(exc)
        log_lines.append(f"FAIL: {error}")

    for path in cache.glob("*.tsv"):
        path.chmod(0o444)
    write_json(
        out / "cache-reference.json",
        {
            "path": cache.relative_to(ROOT).as_posix(),
            "files": [
                {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path), "size_bytes": path.stat().st_size}
                for path in sorted(cache.glob("*")) if path.is_file()
            ],
        },
    )
    (out / "validation-report.md").write_text(
        render_report(run_id, source_commit, metric, dataset_manifest, integration, status, error), encoding="utf-8"
    )
    ended = datetime.now(timezone.utc)
    self_usage = resource.getrusage(resource.RUSAGE_SELF)
    child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    multiplier = 1 if sys.platform == "darwin" else 1024
    peak_rss = int(max(self_usage.ru_maxrss, child_usage.ru_maxrss) * multiplier)
    manifest = {
        "schema_version": "s13-method-evidence-manifest/v1",
        "run_id": run_id,
        "gate": "E2",
        "source_commit": source_commit,
        "dirty_at_start": False,
        "command": [sys.executable, "tools/e2_validation_gate.py"],
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
    (out / "command.txt").write_text(f"{sys.executable} tools/e2_validation_gate.py\n", encoding="utf-8")
    (out / "stdout.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    (out / "stderr.txt").write_text("", encoding="utf-8")
    write_checksums(out)
    for line in log_lines:
        print(line)
    print(f"evidence: {out.relative_to(ROOT)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
