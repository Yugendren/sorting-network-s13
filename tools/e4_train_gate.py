#!/usr/bin/env python3
"""Run two deterministic RTX replays of the objective-only V2 repair."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import resource
import shlex
import subprocess
import sys
import time
from typing import Any

if __package__:
    from tools.generate_method_seeds import compact_sha256, reproduce
    from tools.method_runtime import ROOT, aggregate_hash, sha256, write_checksums, write_json
else:
    from generate_method_seeds import compact_sha256, reproduce
    from method_runtime import ROOT, aggregate_hash, sha256, write_checksums, write_json


CONFIG = ROOT / "config/experiment-v1"
E4_CONFIG = CONFIG / "e4"
E1_MANIFEST = ROOT / "evidence/e1/e1-20260815T022353Z/manifest.json"
E1_MANIFEST_SHA256 = "af6e1fb05a4fcf984f71d0a3ab4f40d39e4288d7fb68c2daae2b32c61f3236b5"
DATASET_MANIFEST = ROOT / "evidence/e1/e1-20260815T022353Z/dataset-manifest.json"
DATASET_MANIFEST_SHA256 = "59dfe8c85b389d3f08568155638b1900808a03d9502670900208b8ac1441ce2d"
DATASET_SHA256 = "5628fd5187772bd66ff630bc3889f1973ca8cfefae468b189e586cc83f6be994"
V1_EXPORT = ROOT / "evidence/e2/e2-train-20260815T023758Z/replay-1/artifacts/model-export.json"
V1_EXPORT_SHA256 = "eb606f4f6712a1eaa53bde8d36c0c8280c635c73453d22a861112ccf356babb7"
FAILURE_ANALYSIS_SHA256 = "39e6a0e90bc43e542f56d55ce235ec462d0a3f968794da370edb49da65536574"
CHANGE_MANIFEST_SHA256 = "06ae75520aefde309e7a60a60cb0af84b20f23b3727b8c781b8cd7a5788bb3ac"
TRAINING_HOST = "ollama"
REMOTE_ROOT = Path("/data/mericanii_s13_method_v2")


def run_text(command: list[str], *, check: bool = True) -> str:
    completed = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    if check and completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {shlex.join(command)}\n{completed.stdout}")
    return completed.stdout.strip()


def host_record() -> dict[str, Any]:
    return {"hostname": platform.node(), "os": platform.platform(), "machine": platform.machine()}


def prerequisite_check() -> dict[str, Any]:
    if sha256(E1_MANIFEST) != E1_MANIFEST_SHA256 or json.loads(E1_MANIFEST.read_text())["status"] != "PASS":
        raise RuntimeError("accepted E1 manifest mismatch")
    if sha256(DATASET_MANIFEST) != DATASET_MANIFEST_SHA256:
        raise RuntimeError("accepted E1 dataset manifest mismatch")
    dataset_manifest = json.loads(DATASET_MANIFEST.read_text(encoding="utf-8"))
    dataset = ROOT / dataset_manifest["aggregate"]["path"]
    if dataset_manifest["aggregate"]["sha256"] != DATASET_SHA256 or sha256(dataset) != DATASET_SHA256:
        raise RuntimeError("frozen E1 training dataset mismatch")
    if dataset_manifest["rows"] != 1_004_000 or dataset_manifest["target_44_rows"] != 0:
        raise RuntimeError("frozen E1 dataset row/target audit mismatch")
    if sha256(V1_EXPORT) != V1_EXPORT_SHA256:
        raise RuntimeError("frozen V1 feature-normalization export mismatch")
    failure_analysis = E4_CONFIG / "failure-analysis.md"
    if sha256(failure_analysis) != FAILURE_ANALYSIS_SHA256:
        raise RuntimeError("committed E4 failure analysis mismatch")
    change_path = E4_CONFIG / "change-manifest.json"
    change = json.loads(change_path.read_text(encoding="utf-8"))
    if CHANGE_MANIFEST_SHA256 and sha256(change_path) != CHANGE_MANIFEST_SHA256:
        raise RuntimeError("E4 change manifest mismatch")
    if change["selected_major_change"] != "learning_objective" or change["representation_change_allowed"] or change["integration_change_allowed"]:
        raise RuntimeError("E4 change boundary mismatch")
    for prefix in ("failure_analysis", "e4_seed_manifest", "model_v2_config", "exam_v2_config"):
        if sha256(ROOT / change[f"{prefix}_path"]) != change[f"{prefix}_sha256"]:
            raise RuntimeError(f"E4 frozen file mismatch: {prefix}")
    seed_manifest = json.loads((E4_CONFIG / "seeds-e4-holdout.json").read_text(encoding="utf-8"))
    generated = reproduce()
    if seed_manifest["seeds"] != generated["e4_future_holdout"]:
        raise RuntimeError("E4 holdout does not reproduce precommitment")
    if compact_sha256(seed_manifest["seeds"]) != seed_manifest["compact_seed_array_sha256_commitment"]:
        raise RuntimeError("E4 holdout compact commitment mismatch")
    if sorted((ROOT / "evidence/e4").glob("e4-train-*")) if (ROOT / "evidence/e4").is_dir() else []:
        raise RuntimeError("E4 V2 training has already been attempted")
    if sorted((ROOT / "evidence/e4").glob("e4-exam-*")) if (ROOT / "evidence/e4").is_dir() else []:
        raise RuntimeError("E4 exam evidence exists before V2 training")
    replay = run_text([sys.executable, "tools/evidence_check.py"])
    training_script = ROOT / "tools/train_completion_model_v2.py"
    frozen_paths = [*sorted(CONFIG.glob("*.json")), *sorted(path for path in E4_CONFIG.iterdir() if path.is_file())]
    return {
        "dataset_manifest": dataset_manifest,
        "dataset": dataset,
        "dataset_sha256": DATASET_SHA256,
        "v1_export": V1_EXPORT,
        "v1_export_sha256": V1_EXPORT_SHA256,
        "config_sha256": aggregate_hash(frozen_paths),
        "base_config_sha256": aggregate_hash(sorted(CONFIG.glob("*.json"))),
        "change_manifest_sha256": sha256(change_path),
        "seed_manifest_sha256": sha256(E4_CONFIG / "seeds-e4-holdout.json"),
        "evidence_replay": replay,
        "training_script": training_script,
        "training_script_sha256": sha256(training_script),
    }


def run_remote(command: str, stdout_path: Path, stderr_path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        completed = subprocess.run(["ssh", TRAINING_HOST, command], cwd=ROOT, stdout=stdout, stderr=stderr, check=False)
    return {
        "command": ["ssh", TRAINING_HOST, command],
        "exit_code": completed.returncode,
        "wall_seconds": round(time.perf_counter() - started, 6),
        "stdout_sha256": sha256(stdout_path),
        "stderr_sha256": sha256(stderr_path),
    }


def copy_command(source: str, destination: str) -> dict[str, Any]:
    command = ["rsync", "--archive", "--checksum", source, destination]
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    record = {
        "command": command,
        "exit_code": completed.returncode,
        "wall_seconds": round(time.perf_counter() - started, 6),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode != 0:
        raise RuntimeError(f"rsync failed: {completed.stderr}")
    return record


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        print(f"E4 training preflight failed: cwd must be exactly {ROOT}", file=sys.stderr)
        return 2
    if run_text(["git", "branch", "--show-current"]) != "goal/s13-method-v1":
        print("E4 training preflight failed: wrong branch", file=sys.stderr)
        return 2
    dirty = run_text(["git", "status", "--porcelain", "--untracked-files=all"])
    if dirty:
        print("E4 training preflight failed: scored configuration is dirty", file=sys.stderr)
        print(dirty, file=sys.stderr)
        return 2

    prerequisite = prerequisite_check()
    source_commit = run_text(["git", "rev-parse", "HEAD"])
    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    started_cpu = time.process_time()
    run_id = started.strftime("e4-train-%Y%m%dT%H%M%SZ")
    out = ROOT / "evidence/e4" / run_id
    out.mkdir(parents=True, exist_ok=False)
    remote = REMOTE_ROOT / run_id
    log_lines = ["E4 V2 training gate: two RTX replays must export identical regression-score arrays while representation and integration remain frozen."]
    status = "FAIL"
    error: str | None = None
    commands: list[dict[str, Any]] = []
    training_host: dict[str, Any] = {}

    try:
        environment_command = "python3 - <<'PY'\nimport json, platform, numpy, pandas, torch\nprint(json.dumps({'hostname':platform.node(),'platform':platform.platform(),'python':platform.python_version(),'numpy':numpy.__version__,'pandas':pandas.__version__,'torch':torch.__version__,'cuda':torch.version.cuda,'cudnn':torch.backends.cudnn.version(),'gpu':torch.cuda.get_device_name(0),'capability':list(torch.cuda.get_device_capability(0))},sort_keys=True))\nPY\nnvidia-smi --query-gpu=name,uuid,memory.total,driver_version --format=csv,noheader,nounits"
        environment_output = run_text(["ssh", TRAINING_HOST, environment_command])
        environment_lines = environment_output.splitlines()
        if len(environment_lines) != 2:
            raise RuntimeError("unexpected training-host environment output")
        training_host = json.loads(environment_lines[0])
        training_host["nvidia_smi"] = environment_lines[1]
        if training_host["torch"] != "2.10.0+cu128" or training_host["gpu"] != "NVIDIA GeForce RTX 3060":
            raise RuntimeError("training host differs from E0 freeze")
        write_json(out / "training-host.json", training_host)

        mkdir_record = run_remote(f"mkdir -p {shlex.quote(str(remote))}", out / "remote-mkdir.stdout", out / "remote-mkdir.stderr")
        commands.append(mkdir_record)
        if mkdir_record["exit_code"] != 0:
            raise RuntimeError("could not create unique remote V2 training directory")
        for source, destination in (
            (prerequisite["dataset"], "development-dataset.tsv.zst"),
            (prerequisite["training_script"], "train_completion_model_v2.py"),
            (prerequisite["v1_export"], "v1-model-export.json"),
        ):
            commands.append(copy_command(str(source), f"{TRAINING_HOST}:{remote}/{destination}"))

        reports = []
        for replay in (1, 2):
            replay_dir = out / f"replay-{replay}"
            replay_dir.mkdir()
            remote_output = remote / f"replay-{replay}"
            argv = [
                "python3", "train_completion_model_v2.py",
                "--dataset", "development-dataset.tsv.zst",
                "--dataset-sha256", prerequisite["dataset_sha256"],
                "--v1-export", "v1-model-export.json",
                "--v1-export-sha256", prerequisite["v1_export_sha256"],
                "--output", remote_output.name,
                "--replay", str(replay),
            ]
            remote_command = f"cd {shlex.quote(str(remote))} && CUDA_VISIBLE_DEVICES=0 /usr/bin/time -v timeout --signal=TERM 1800s {shlex.join(argv)}"
            record = run_remote(remote_command, replay_dir / "stdout.txt", replay_dir / "stderr.txt")
            commands.append(record)
            write_json(replay_dir / "command.json", record)
            if record["exit_code"] != 0:
                raise RuntimeError(f"V2 training replay {replay} failed")
            artifacts = replay_dir / "artifacts"
            artifacts.mkdir()
            commands.append(copy_command(f"{TRAINING_HOST}:{remote_output}/", str(artifacts) + "/"))
            report = json.loads((artifacts / "training-report.json").read_text(encoding="utf-8"))
            if report["schema_version"] != "s13-completion-training-report/v2":
                raise RuntimeError(f"V2 training replay {replay} schema mismatch")
            if report["dataset_sha256"] != DATASET_SHA256 or report["v1_normalization_export_sha256"] != V1_EXPORT_SHA256:
                raise RuntimeError(f"V2 training replay {replay} input identity mismatch")
            if report["training_rows"] != 803_200 or report["calibration_rows"] != 200_800:
                raise RuntimeError(f"V2 training replay {replay} split mismatch")
            if report["target_44_used"] or report["e3_rows_used"] or report["e4_rows_used"]:
                raise RuntimeError(f"V2 training replay {replay} leakage marker")
            if report["trainable_parameters"] != 7_617 or report["objective"] != "MSE on standardized negative final_count":
                raise RuntimeError(f"V2 training replay {replay} objective/topology mismatch")
            reports.append(report)
            print(
                f"E4 training replay {replay}: PASS epoch={report['selected_epoch']} calibration_concordance={report['selected_calibration_micro_concordance']:.9f}",
                flush=True,
            )

        replay_one = out / "replay-1/artifacts"
        replay_two = out / "replay-2/artifacts"
        reproducible_files = ["model-export.json", "MericaniiModelV1Weights.hpp", "model-inference-fixture.json"]
        reproducibility = {}
        for name in reproducible_files:
            first = sha256(replay_one / name)
            second = sha256(replay_two / name)
            reproducibility[name] = {"replay_1_sha256": first, "replay_2_sha256": second, "equal": first == second}
            if first != second:
                raise RuntimeError(f"V2 training replay export mismatch: {name}")
        for field in (
            "target_mean", "target_scale", "selected_epoch",
            "selected_calibration_micro_concordance", "selected_calibration_mse", "epochs_run",
        ):
            if reports[0][field] != reports[1][field]:
                raise RuntimeError(f"V2 training replay metric mismatch: {field}")
        selected = {
            "replay": 1,
            "artifacts_path": replay_one.relative_to(ROOT).as_posix(),
            "checkpoint_sha256": sha256(replay_one / "checkpoint.pt"),
            "model_export_sha256": sha256(replay_one / "model-export.json"),
            "cpp_header_sha256": sha256(replay_one / "MericaniiModelV1Weights.hpp"),
            "inference_fixture_sha256": sha256(replay_one / "model-inference-fixture.json"),
            "selected_epoch": reports[0]["selected_epoch"],
            "selected_calibration_micro_concordance": reports[0]["selected_calibration_micro_concordance"],
            "selected_calibration_mse": reports[0]["selected_calibration_mse"],
            "target_mean": reports[0]["target_mean"],
            "target_scale": reports[0]["target_scale"],
        }
        write_json(out / "reproducibility.json", reproducibility)
        write_json(out / "selected-model.json", selected)
        write_json(out / "commands.json", commands)
        write_json(
            out / "prerequisite.json",
            {
                "e1_manifest_sha256": E1_MANIFEST_SHA256,
                "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
                "dataset_path": prerequisite["dataset"].relative_to(ROOT).as_posix(),
                "dataset_sha256": DATASET_SHA256,
                "v1_normalization_export_path": V1_EXPORT.relative_to(ROOT).as_posix(),
                "v1_normalization_export_sha256": V1_EXPORT_SHA256,
                "failure_analysis_sha256": FAILURE_ANALYSIS_SHA256,
                "change_manifest_sha256": prerequisite["change_manifest_sha256"],
                "seed_manifest_sha256": prerequisite["seed_manifest_sha256"],
                "config_sha256": prerequisite["config_sha256"],
                "base_config_sha256": prerequisite["base_config_sha256"],
                "training_script_sha256": prerequisite["training_script_sha256"],
                "evidence_replay": prerequisite["evidence_replay"],
                "remote_path": str(remote),
                "e3_rows_used": 0,
                "e4_rows_used": 0,
            },
        )
        status = "PASS"
        log_lines.extend(
            [
                "PASS: both RTX replays consumed only the frozen E1 development dataset and exact V1 feature normalization.",
                "PASS: the only major change is MSE regression on standardized negative final_count; E3/E4 rows and target 44 were unused.",
                f"PASS: selected epoch {selected['selected_epoch']} calibration concordance {selected['selected_calibration_micro_concordance']:.9f}; export {selected['model_export_sha256']}.",
                "PASS: exported float arrays, C++ ABI header, and inference fixture are byte-identical across replays.",
            ]
        )
    except Exception as exc:
        error = str(exc)
        log_lines.append(f"FAIL: {error}")

    if not (out / "commands.json").is_file():
        write_json(out / "commands.json", commands)
    ended = datetime.now(timezone.utc)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    multiplier = 1 if sys.platform == "darwin" else 1024
    manifest = {
        "schema_version": "s13-method-evidence-manifest/v1",
        "run_id": run_id,
        "gate": "E4",
        "source_commit": source_commit,
        "dirty_at_start": False,
        "command": [sys.executable, "tools/e4_train_gate.py"],
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "wall_seconds": round(time.perf_counter() - started_perf, 6),
        "cpu_seconds": round(time.process_time() - started_cpu, 6),
        "peak_rss_bytes": int(usage.ru_maxrss * multiplier),
        "threads": 1,
        "host": {"local": host_record(), "training": training_host},
        "config_sha256": prerequisite["config_sha256"],
        "status": status,
    }
    if error is not None:
        manifest["error"] = error
    write_json(out / "manifest.json", manifest)
    (out / "command.txt").write_text(f"{sys.executable} tools/e4_train_gate.py\n", encoding="utf-8")
    (out / "stdout.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    (out / "stderr.txt").write_text("", encoding="utf-8")
    write_checksums(out)
    for line in log_lines:
        print(line)
    print(f"evidence: {out.relative_to(ROOT)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
