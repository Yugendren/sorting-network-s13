#!/usr/bin/env python3
"""Run the two deterministic RTX training replays for method version 1."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import resource
import shlex
import shutil
import subprocess
import sys
import time
from typing import Any

if __package__:
    from tools.method_runtime import ROOT, aggregate_hash, sha256, write_checksums, write_json
else:
    from method_runtime import ROOT, aggregate_hash, sha256, write_checksums, write_json


CONFIG = ROOT / "config/experiment-v1"
E1_MANIFEST = ROOT / "evidence/e1/e1-20260815T022353Z/manifest.json"
E1_MANIFEST_SHA256 = "af6e1fb05a4fcf984f71d0a3ab4f40d39e4288d7fb68c2daae2b32c61f3236b5"
DATASET_MANIFEST = ROOT / "evidence/e1/e1-20260815T022353Z/dataset-manifest.json"
DATASET_MANIFEST_SHA256 = "59dfe8c85b389d3f08568155638b1900808a03d9502670900208b8ac1441ce2d"
TRAINING_HOST = "ollama"
REMOTE_ROOT = Path("/data/mericanii_s13_method_v1")


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
        raise RuntimeError(f"command failed ({completed.returncode}): {shlex.join(command)}\n{completed.stdout}")
    return completed.stdout.strip()


def host_record() -> dict[str, Any]:
    return {
        "hostname": platform.node(),
        "os": platform.platform(),
        "machine": platform.machine(),
    }


def prerequisite_check() -> dict[str, Any]:
    if sha256(E1_MANIFEST) != E1_MANIFEST_SHA256:
        raise RuntimeError("accepted E1 manifest hash mismatch")
    if json.loads(E1_MANIFEST.read_text(encoding="utf-8"))["status"] != "PASS":
        raise RuntimeError("accepted E1 is not PASS")
    if sha256(DATASET_MANIFEST) != DATASET_MANIFEST_SHA256:
        raise RuntimeError("E1 dataset manifest hash mismatch")
    dataset_manifest = json.loads(DATASET_MANIFEST.read_text(encoding="utf-8"))
    dataset = ROOT / dataset_manifest["aggregate"]["path"]
    if sha256(dataset) != dataset_manifest["aggregate"]["sha256"]:
        raise RuntimeError("E1 compressed dataset hash mismatch")
    if dataset_manifest["rows"] != 1_004_000 or dataset_manifest["target_44_rows"] != 0:
        raise RuntimeError("E1 dataset row/target audit mismatch")
    config_hash = aggregate_hash(sorted(CONFIG.glob("*.json")))
    if config_hash != json.loads(E1_MANIFEST.read_text(encoding="utf-8"))["config_sha256"]:
        raise RuntimeError("experiment config aggregate differs from accepted E1")
    replay = run_text([sys.executable, "tools/evidence_check.py"])
    training_script = ROOT / "tools/train_completion_model.py"
    return {
        "dataset_manifest": dataset_manifest,
        "dataset": dataset,
        "dataset_sha256": dataset_manifest["aggregate"]["sha256"],
        "config_sha256": config_hash,
        "evidence_replay": replay,
        "training_script": training_script,
        "training_script_sha256": sha256(training_script),
    }


def run_remote(command: str, stdout_path: Path, stderr_path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        completed = subprocess.run(
            ["ssh", TRAINING_HOST, command],
            cwd=ROOT,
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
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
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
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
        print(f"E2 training preflight failed: cwd must be exactly {ROOT}", file=sys.stderr)
        return 2
    if run_text(["git", "branch", "--show-current"]) != "goal/s13-method-v1":
        print("E2 training preflight failed: wrong branch", file=sys.stderr)
        return 2
    dirty = run_text(["git", "status", "--porcelain", "--untracked-files=all"])
    if dirty:
        print("E2 training preflight failed: scored configuration is dirty", file=sys.stderr)
        print(dirty, file=sys.stderr)
        return 2

    prerequisite = prerequisite_check()
    source_commit = run_text(["git", "rev-parse", "HEAD"])
    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    started_cpu = time.process_time()
    run_id = started.strftime("e2-train-%Y%m%dT%H%M%SZ")
    out = ROOT / "evidence/e2" / run_id
    out.mkdir(parents=True, exist_ok=False)
    remote = REMOTE_ROOT / run_id
    log_lines = ["E2 training falsifiable gate: two frozen RTX replays export byte-identical float arrays despite the zero-positive training split."]
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

        mkdir_command = f"mkdir -p {shlex.quote(str(remote))}"
        mkdir_record = run_remote(mkdir_command, out / "remote-mkdir.stdout", out / "remote-mkdir.stderr")
        commands.append(mkdir_record)
        if mkdir_record["exit_code"] != 0:
            raise RuntimeError("could not create unique remote training directory")
        commands.append(
            copy_command(
                str(prerequisite["dataset"]),
                f"{TRAINING_HOST}:{remote}/development-dataset.tsv.zst",
            )
        )
        commands.append(
            copy_command(
                str(prerequisite["training_script"]),
                f"{TRAINING_HOST}:{remote}/train_completion_model.py",
            )
        )

        reports = []
        for replay in (1, 2):
            replay_dir = out / f"replay-{replay}"
            replay_dir.mkdir()
            remote_output = remote / f"replay-{replay}"
            argv = [
                "python3",
                "train_completion_model.py",
                "--dataset",
                "development-dataset.tsv.zst",
                "--dataset-sha256",
                prerequisite["dataset_sha256"],
                "--output",
                str(remote_output.name),
                "--replay",
                str(replay),
            ]
            remote_command = f"cd {shlex.quote(str(remote))} && CUDA_VISIBLE_DEVICES=0 /usr/bin/time -v {shlex.join(argv)}"
            record = run_remote(
                remote_command,
                replay_dir / "stdout.txt",
                replay_dir / "stderr.txt",
            )
            commands.append(record)
            write_json(replay_dir / "command.json", record)
            if record["exit_code"] != 0:
                raise RuntimeError(f"training replay {replay} failed")
            artifacts = replay_dir / "artifacts"
            artifacts.mkdir()
            commands.append(
                copy_command(
                    f"{TRAINING_HOST}:{remote_output}/",
                    str(artifacts) + "/",
                )
            )
            report_path = artifacts / "training-report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            if report["dataset_sha256"] != prerequisite["dataset_sha256"] or report["rows"] != 1_004_000:
                raise RuntimeError(f"training replay {replay} dataset identity mismatch")
            if report["training_positive_count"] != 0 or report["calibration_positive_count"] != 1_216:
                raise RuntimeError(f"training replay {replay} class counts mismatch")
            if not report["zero_positive_training_case"] or report["positive_weight"] != 100.0:
                raise RuntimeError(f"training replay {replay} did not record frozen zero-positive limit")
            reports.append(report)
            print(
                f"E2 training replay {replay}: PASS epoch={report['selected_epoch']} calibration_ap={report['selected_calibration_average_precision']:.9f}",
                flush=True,
            )

        replay_one = out / "replay-1/artifacts"
        replay_two = out / "replay-2/artifacts"
        reproducible_files = [
            "model-export.json",
            "MericaniiModelV1Weights.hpp",
            "model-inference-fixture.json",
        ]
        reproducibility = {}
        for name in reproducible_files:
            first = sha256(replay_one / name)
            second = sha256(replay_two / name)
            reproducibility[name] = {"replay_1_sha256": first, "replay_2_sha256": second, "equal": first == second}
            if first != second:
                raise RuntimeError(f"training replay export mismatch: {name}")
        for field in (
            "selected_epoch",
            "selected_calibration_average_precision",
            "selected_calibration_bce",
            "epochs_run",
        ):
            if reports[0][field] != reports[1][field]:
                raise RuntimeError(f"training replay metric mismatch: {field}")
        selected = {
            "replay": 1,
            "artifacts_path": replay_one.relative_to(ROOT).as_posix(),
            "checkpoint_sha256": sha256(replay_one / "checkpoint.pt"),
            "model_export_sha256": sha256(replay_one / "model-export.json"),
            "cpp_header_sha256": sha256(replay_one / "MericaniiModelV1Weights.hpp"),
            "inference_fixture_sha256": sha256(replay_one / "model-inference-fixture.json"),
            "selected_epoch": reports[0]["selected_epoch"],
            "selected_calibration_average_precision": reports[0]["selected_calibration_average_precision"],
            "selected_calibration_bce": reports[0]["selected_calibration_bce"],
        }
        write_json(out / "reproducibility.json", reproducibility)
        write_json(out / "selected-model.json", selected)
        write_json(out / "commands.json", commands)
        write_json(
            out / "prerequisite.json",
            {
                "e1_manifest_path": E1_MANIFEST.relative_to(ROOT).as_posix(),
                "e1_manifest_sha256": E1_MANIFEST_SHA256,
                "dataset_manifest_path": DATASET_MANIFEST.relative_to(ROOT).as_posix(),
                "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
                "dataset_path": prerequisite["dataset"].relative_to(ROOT).as_posix(),
                "dataset_sha256": prerequisite["dataset_sha256"],
                "config_sha256": prerequisite["config_sha256"],
                "training_script_sha256": prerequisite["training_script_sha256"],
                "evidence_replay": prerequisite["evidence_replay"],
                "remote_path": str(remote),
            },
        )
        status = "PASS"
        log_lines.append("PASS: both RTX replays consumed the frozen 1004000-row dataset and the fixed seed/configuration.")
        log_lines.append("PASS: training seeds contain zero positives; the limiting configured positive weight 100.0 was used without changing labels or split.")
        log_lines.append(
            f"PASS: selected epoch {selected['selected_epoch']} calibration AP {selected['selected_calibration_average_precision']:.9f}; model export {selected['model_export_sha256']}."
        )
        log_lines.append("PASS: exported float arrays, C++ header, and inference fixture are byte-identical across replays.")
    except Exception as exc:
        error = str(exc)
        log_lines.append(f"FAIL: {error}")

    if not (out / "commands.json").is_file():
        write_json(out / "commands.json", commands)
    ended = datetime.now(timezone.utc)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    peak_rss = int(usage.ru_maxrss if sys.platform == "darwin" else usage.ru_maxrss * 1024)
    manifest = {
        "schema_version": "s13-method-evidence-manifest/v1",
        "run_id": run_id,
        "gate": "E2",
        "source_commit": source_commit,
        "dirty_at_start": False,
        "command": [sys.executable, "tools/e2_train_gate.py"],
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "wall_seconds": round(time.perf_counter() - started_perf, 6),
        "cpu_seconds": round(time.process_time() - started_cpu, 6),
        "peak_rss_bytes": peak_rss,
        "threads": 1,
        "host": {"local": host_record(), "training": training_host},
        "config_sha256": prerequisite["config_sha256"],
        "status": status,
    }
    if error is not None:
        manifest["error"] = error
    write_json(out / "manifest.json", manifest)
    (out / "command.txt").write_text(f"{sys.executable} tools/e2_train_gate.py\n", encoding="utf-8")
    (out / "stdout.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    (out / "stderr.txt").write_text("", encoding="utf-8")
    write_checksums(out)
    for line in log_lines:
        print(line)
    print(f"evidence: {out.relative_to(ROOT)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
