#!/usr/bin/env python3
"""Resume E2 only from the frozen validation aggregate after the CWD wrapper defect."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
from typing import Any

if __package__:
    from tools.e1_dataset_gate import FrontierStop, host_record, load_active
    from tools.e2_validation_gate import (
        CONFIG,
        CONTRACT_SHA256,
        MODEL_HEADER_SHA256,
        METHOD_PATCH_SHA256,
        VERIFIER_B,
        finalize_search_run,
        render_report,
        score_dataset,
    )
    from tools.method_runtime import (
        ROOT,
        VerificationFailure,
        candidate_bytes,
        run_limited,
        senso_command,
        sha256,
        verify_candidate,
        write_checksums,
        write_json,
    )
else:
    from e1_dataset_gate import FrontierStop, host_record, load_active
    from e2_validation_gate import (
        CONFIG,
        CONTRACT_SHA256,
        MODEL_HEADER_SHA256,
        METHOD_PATCH_SHA256,
        VERIFIER_B,
        finalize_search_run,
        render_report,
        score_dataset,
    )
    from method_runtime import (
        ROOT,
        VerificationFailure,
        candidate_bytes,
        run_limited,
        senso_command,
        sha256,
        verify_candidate,
        write_checksums,
        write_json,
    )


FAILED_RUN = ROOT / "evidence/e2/e2-validation-20260815T030452Z"
FAILED_MANIFEST_SHA256 = "6c71bfac465c496d19be05d1ee674a47ffa19a1cbec80c0c35cf80d4db8e62e2"
FAILED_INVENTORY_SHA256 = "5c825f4eb18ea26e820c2d1349347ac6b594e4e3ec63f783f4940df64dd03d15"
DATASET_MANIFEST_SHA256 = "2f8aed3b4e7dc10263b03aadb98f098f96347ea2e0570eb94203e5811a4764c0"
DATASET_SUMMARIES_SHA256 = "986b476b81b93e319a81e7f3a0b3e072bc0a8cbd770ea6c50e5e66cf9934f394"
SEED_RESULTS_SHA256 = "accf63566a6ed023ac8f20d58791651c1b32fd525a524382e61e2e5019c54943"
SUCCESS_INDEX_SHA256 = "1b6850d47928f507cde5ef7e63229a305ebd3819960adadbea72a0ffadd67593"
DATASET_SHA256 = "7bca7bec0cfda5573d4640eb6f9a3af697025dbedf3342242c330eb70dfbbfd9"
SCORER_SHA256 = "f16262aabb60ac178a3b558795dff8c7efc038725fd3ea624cddc9ec7bd9f0b3"
SCORER_SOURCE_SHA256 = "d6576e34d82e2d5619e04a4bb1d53220631ed85326c4a7d8264492029f0efc03"


def run_text(command: list[str], *, check: bool = True) -> str:
    completed = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if check and completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}\n{completed.stdout}")
    return completed.stdout.strip()


def preflight() -> dict[str, Any]:
    fixed_files = {
        FAILED_RUN / "manifest.json": FAILED_MANIFEST_SHA256,
        FAILED_RUN / "checksums.sha256": FAILED_INVENTORY_SHA256,
        FAILED_RUN / "validation-dataset-manifest.json": DATASET_MANIFEST_SHA256,
        FAILED_RUN / "validation-dataset-summaries.json": DATASET_SUMMARIES_SHA256,
        FAILED_RUN / "validation-seed-results.json": SEED_RESULTS_SHA256,
        FAILED_RUN / "validation-success-index.json": SUCCESS_INDEX_SHA256,
        FAILED_RUN / "compiled-validation-scorer/score-validation-model": SCORER_SHA256,
    }
    for path, digest in fixed_files.items():
        if not path.is_file() or sha256(path) != digest:
            raise RuntimeError(f"frozen failed-run artifact mismatch: {path}")
    failed_manifest = json.loads((FAILED_RUN / "manifest.json").read_text(encoding="utf-8"))
    if failed_manifest.get("status") != "FAIL" or failed_manifest.get("error") != "offline validation scoring failed: CRASH":
        raise RuntimeError("frozen failed-run classification mismatch")
    dataset_manifest = json.loads((FAILED_RUN / "validation-dataset-manifest.json").read_text(encoding="utf-8"))
    dataset = ROOT / dataset_manifest["aggregate"]["path"]
    if dataset_manifest["aggregate"]["sha256"] != DATASET_SHA256 or sha256(dataset) != DATASET_SHA256:
        raise RuntimeError("frozen validation aggregate hash mismatch")
    tested = subprocess.run(["zstd", "-q", "-t", str(dataset)], cwd=ROOT, check=False)
    if tested.returncode != 0:
        raise RuntimeError("frozen validation aggregate failed zstd integrity test")
    if sha256(ROOT / "tools/score_validation_model.cpp") != SCORER_SOURCE_SHA256:
        raise RuntimeError("validation metric/scorer source changed after materialization")
    replay = run_text([sys.executable, "tools/evidence_check.py"])
    prior_resumes = sorted((ROOT / "evidence/e2").glob("e2-validation-resume-*"))
    if prior_resumes:
        raise RuntimeError("validation resume has already been attempted")
    method, method_binary, method_source, method_manifest_sha = load_active(
        ROOT / ".build/senso-mericanii-v1/active.json", "s13-senso-mericanii-build/v1"
    )
    if method["method_patch_sha256"] != METHOD_PATCH_SHA256 or method["model_header_sha256"] != MODEL_HEADER_SHA256:
        raise RuntimeError("active V1 method build changed before resume")
    validation = json.loads((CONFIG / "seeds-validation.json").read_text(encoding="utf-8"))["seeds"]
    seed_results = json.loads((FAILED_RUN / "validation-seed-results.json").read_text(encoding="utf-8"))
    summaries = json.loads((FAILED_RUN / "validation-dataset-summaries.json").read_text(encoding="utf-8"))
    if [item["seed"] for item in seed_results] != validation or [item["seed"] for item in summaries] != validation:
        raise RuntimeError("frozen validation seed sequence mismatch")
    if any(item["evaluations"] != 50_200 for item in seed_results):
        raise RuntimeError("frozen validation label evaluation mismatch")
    return {
        "evidence_replay": replay,
        "dataset_manifest": dataset_manifest,
        "dataset": dataset,
        "summaries": summaries,
        "seed_results": seed_results,
        "validation_seeds": validation,
        "scorer": FAILED_RUN / "compiled-validation-scorer/score-validation-model",
        "method": method,
        "method_binary": method_binary,
        "method_source": method_source,
        "method_manifest_sha256": method_manifest_sha,
    }


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        print(f"E2 validation resume preflight failed: cwd must be exactly {ROOT}", file=sys.stderr)
        return 2
    if run_text(["git", "branch", "--show-current"]) != "goal/s13-method-v1":
        print("E2 validation resume preflight failed: wrong branch", file=sys.stderr)
        return 2
    dirty = run_text(["git", "status", "--porcelain", "--untracked-files=all"])
    if dirty:
        print("E2 validation resume preflight failed: scored configuration is dirty", file=sys.stderr)
        print(dirty, file=sys.stderr)
        return 2

    frozen = preflight()
    source_commit = run_text(["git", "rev-parse", "HEAD"])
    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    started_cpu = time.process_time()
    run_id = started.strftime("e2-validation-resume-%Y%m%dT%H%M%SZ")
    out = ROOT / "evidence/e2" / run_id
    out.mkdir(parents=True, exist_ok=False)
    host = host_record()
    status = "FAIL"
    error: str | None = None
    metric: dict[str, Any] | None = None
    integration: dict[str, Any] | None = None
    log_lines = [
        "E2 validation resume: use only the exact frozen 7bca7b... aggregate and f16262... scorer; no label trajectory may run."
    ]
    try:
        write_json(
            out / "resume-provenance.json",
            {
                "failed_run_path": FAILED_RUN.relative_to(ROOT).as_posix(),
                "failed_manifest_sha256": FAILED_MANIFEST_SHA256,
                "failed_inventory_sha256": FAILED_INVENTORY_SHA256,
                "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
                "dataset_sha256": DATASET_SHA256,
                "scorer_sha256": SCORER_SHA256,
                "scorer_source_sha256": SCORER_SOURCE_SHA256,
                "model_header_sha256": MODEL_HEADER_SHA256,
                "method_patch_sha256": METHOD_PATCH_SHA256,
                "method_manifest_sha256": frozen["method_manifest_sha256"],
                "wrapper_sha256": sha256(ROOT / "tools/score_validation_stream.py"),
                "repair": "allow execution from a subdirectory inside ROOT; no metric, data, model, or integration change",
                "evidence_replay": frozen["evidence_replay"],
                "validation_label_trajectories_executed_by_resume": 0,
                "e3_seed_trajectories_executed": 0,
            },
        )
        budgets = json.loads((CONFIG / "budgets-v1.json").read_text(encoding="utf-8"))
        local_budget = budgets["local_search"]
        metric, scoring_resources = score_dataset(out, frozen["dataset"], frozen["scorer"], local_budget)
        metric["aggregation"] = "micro over unequal-final-size pairs within seeds; exact score ties contribute 0.5"
        metric["constant_score_reference"] = 0.5
        metric["model_header_sha256"] = MODEL_HEADER_SHA256
        metric["dataset_sha256"] = DATASET_SHA256
        metric["scorer_sha256"] = SCORER_SHA256
        metric["scoring_resources"] = scoring_resources
        if metric["row_count"] != 1_004_000 or metric["seed_count"] != 20 or metric["comparable_pairs"] <= 0:
            raise RuntimeError("resumed validation score cardinality mismatch")
        scored_by_seed = {item["seed"]: item for item in metric["seed_results"]}
        if set(scored_by_seed) != set(frozen["validation_seeds"]):
            raise RuntimeError("resumed validation score seed set mismatch")
        for summary in frozen["summaries"]:
            scored = scored_by_seed[summary["seed"]]
            if scored["rows"] != 50_200 or scored["final_size_distribution"] != summary["final_size_distribution"]:
                raise RuntimeError(f"resumed score/label distribution mismatch for seed {summary['seed']}")
        write_json(out / "validation-metric.json", metric)
        print(f"E2 validation metric: micro_concordance={metric['micro_concordance']:.12f}", flush=True)

        audit_seed = frozen["validation_seeds"][0]
        audit_dir = out / f"integration-audit-seed-{audit_seed}"
        audit_dir.mkdir()
        inference_path = audit_dir / "inference-stats.json"
        audit_resource = run_limited(
            senso_command(frozen["method_binary"], frozen["method_source"], seed=audit_seed),
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
            raise RuntimeError("resumed V1 integration inference call-count mismatch")
        if sum(inference.get("selected_proposal_histogram", [])) != 50_200:
            raise RuntimeError("resumed V1 selected-proposal histogram mismatch")
        if audit_result["evaluations"] != frozen["seed_results"][0]["evaluations"]:
            raise RuntimeError("resumed V1 integration changed evaluation budget")
        integration = {**audit_result, "inference_stats": inference, "baseline_label_result": frozen["seed_results"][0]}
        write_json(audit_dir / "result.json", integration)
        write_json(out / "integration-audit.json", integration)
        print(
            f"E2 integration audit seed={audit_seed}: evaluations={integration['evaluations']} final={integration['best_size']}",
            flush=True,
        )

        validation_pass = metric["micro_concordance"] > 0.5
        status = "PASS" if validation_pass else "FAIL"
        log_lines.extend(
            [
                f"PASS: exact frozen validation aggregate {DATASET_SHA256} scored with exact frozen binary {SCORER_SHA256}.",
                f"MEASURED: {metric['comparable_pairs']} comparable pairs; micro concordance={metric['micro_concordance']:.12f}; reference=0.5.",
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
        candidate.write_bytes(candidate_bytes(13, comparators, "e2-resume-unexpected-44-stop"))
        try:
            verification = verify_candidate(candidate, VERIFIER_B, unexpected)
            write_json(unexpected / "result.json", {"seed": exc.seed, "verification": verification})
        except Exception as verification_error:
            write_json(unexpected / "result.json", {"seed": exc.seed, "verification_error": str(verification_error)})
    except VerificationFailure as exc:
        status = "INVALID"
        error = str(exc)
        log_lines.append(f"INVALID: {error}")
    except Exception as exc:
        status = "FAIL"
        error = str(exc)
        log_lines.append(f"FAIL: {error}")

    (out / "validation-report.md").write_text(
        render_report(run_id, source_commit, metric, frozen["dataset_manifest"], integration, status, error), encoding="utf-8"
    )
    ended = datetime.now(timezone.utc)
    self_usage = resource.getrusage(resource.RUSAGE_SELF)
    child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    multiplier = 1 if sys.platform == "darwin" else 1024
    manifest = {
        "schema_version": "s13-method-evidence-manifest/v1",
        "run_id": run_id,
        "gate": "E2",
        "source_commit": source_commit,
        "dirty_at_start": False,
        "command": [sys.executable, "tools/e2_validation_resume.py"],
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "wall_seconds": round(time.perf_counter() - started_perf, 6),
        "cpu_seconds": round(time.process_time() - started_cpu, 6),
        "peak_rss_bytes": int(max(self_usage.ru_maxrss, child_usage.ru_maxrss) * multiplier),
        "threads": 1,
        "host": host,
        "config_sha256": "5c22a3ce05504045ceaa7359a7b25d318cc0a923163b162779c32975c2533465",
        "status": status,
    }
    if error is not None:
        manifest["error"] = error
    write_json(out / "manifest.json", manifest)
    (out / "command.txt").write_text(f"{sys.executable} tools/e2_validation_resume.py\n", encoding="utf-8")
    (out / "stdout.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    (out / "stderr.txt").write_text("", encoding="utf-8")
    write_checksums(out)
    for line in log_lines:
        print(line)
    print(f"evidence: {out.relative_to(ROOT)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
