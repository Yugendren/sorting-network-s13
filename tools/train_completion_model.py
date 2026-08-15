#!/usr/bin/env python3
"""Train the frozen 85-64-32-1 Mericanii completion classifier on RTX."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any

import numpy as np
import pandas as pd
import torch


FEATURES = [f"f{index:03d}" for index in range(85)]
TRAINING_SEEDS = list(range(1, 17))
CALIBRATION_SEEDS = [17, 18, 19, 20]
MODEL_SEED = 2026081501


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def average_precision(labels: np.ndarray, scores: np.ndarray) -> float:
    positives = int(labels.sum())
    if positives == 0:
        return 0.0
    order = np.lexsort((np.arange(len(scores), dtype=np.int64), -scores))
    ordered = labels[order].astype(np.int64, copy=False)
    cumulative = np.cumsum(ordered)
    ranks = np.arange(1, len(ordered) + 1, dtype=np.float64)
    return float(np.sum((cumulative / ranks) * ordered) / positives)


def f32_hex(value: float | np.floating[Any]) -> str:
    return float(np.float32(value)).hex() + "f"


def flatten_hex(array: np.ndarray) -> list[str]:
    return [f32_hex(value) for value in np.asarray(array, dtype=np.float32).ravel(order="C")]


def c_array(name: str, values: list[str], columns: int = 6) -> str:
    lines = [f"static const float {name}[{len(values)}] = {{"]
    for start in range(0, len(values), columns):
        lines.append("    " + ", ".join(values[start:start + columns]) + ",")
    lines.append("};")
    return "\n".join(lines)


def export_model(
    output: Path,
    state: dict[str, torch.Tensor],
    mean: np.ndarray,
    scale: np.ndarray,
) -> dict[str, str]:
    arrays = {
        "mean": np.asarray(mean, dtype=np.float32),
        "scale": np.asarray(scale, dtype=np.float32),
        "w1": state["0.weight"].detach().cpu().numpy().astype(np.float32),
        "b1": state["0.bias"].detach().cpu().numpy().astype(np.float32),
        "w2": state["2.weight"].detach().cpu().numpy().astype(np.float32),
        "b2": state["2.bias"].detach().cpu().numpy().astype(np.float32),
        "w3": state["4.weight"].detach().cpu().numpy().astype(np.float32),
        "b3": state["4.bias"].detach().cpu().numpy().astype(np.float32),
    }
    export = {
        "schema_version": "s13-completion-model-export/v1",
        "architecture": [85, 64, 32, 1],
        "dtype": "float32",
        "arrays": {name: flatten_hex(array) for name, array in arrays.items()},
        "shapes": {name: list(array.shape) for name, array in arrays.items()},
    }
    export_path = output / "model-export.json"
    export_path.write_text(
        json.dumps(export, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    sections = [
        "#ifndef MERICANII_MODEL_V1_WEIGHTS_HPP",
        "#define MERICANII_MODEL_V1_WEIGHTS_HPP",
        "",
        "namespace MericaniiModelV1 {",
        c_array("kMean", export["arrays"]["mean"]),
        c_array("kScale", export["arrays"]["scale"]),
        c_array("kW1", export["arrays"]["w1"]),
        c_array("kB1", export["arrays"]["b1"]),
        c_array("kW2", export["arrays"]["w2"]),
        c_array("kB2", export["arrays"]["b2"]),
        c_array("kW3", export["arrays"]["w3"]),
        c_array("kB3", export["arrays"]["b3"]),
        "",
        "inline float score(const float* inFeatures)",
        "{",
        "    float lHidden1[64];",
        "    float lHidden2[32];",
        "    for (unsigned int i = 0; i < 64; ++i) {",
        "        float lValue = kB1[i];",
        "        for (unsigned int j = 0; j < 85; ++j) {",
        "            const float lNormalized = (inFeatures[j] - kMean[j]) / kScale[j];",
        "            lValue += kW1[i*85+j] * lNormalized;",
        "        }",
        "        lHidden1[i] = lValue > 0.0f ? lValue : 0.0f;",
        "    }",
        "    for (unsigned int i = 0; i < 32; ++i) {",
        "        float lValue = kB2[i];",
        "        for (unsigned int j = 0; j < 64; ++j) lValue += kW2[i*64+j] * lHidden1[j];",
        "        lHidden2[i] = lValue > 0.0f ? lValue : 0.0f;",
        "    }",
        "    float lOutput = kB3[0];",
        "    for (unsigned int j = 0; j < 32; ++j) lOutput += kW3[j] * lHidden2[j];",
        "    return lOutput;",
        "}",
        "",
        "} // namespace MericaniiModelV1",
        "",
        "#endif",
        "",
    ]
    header_path = output / "MericaniiModelV1Weights.hpp"
    header_path.write_text("\n".join(sections), encoding="utf-8")
    return {
        "model_export_sha256": sha256(export_path),
        "cpp_header_sha256": sha256(header_path),
    }


def load_dataset(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    command = ["zstd", "-dc", str(path)]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert process.stdout is not None
    frame = pd.read_csv(
        process.stdout,
        sep="\t",
        usecols=["seed", *FEATURES, "final_count", "success45"],
        dtype={
            "seed": np.int32,
            **{name: np.float32 for name in FEATURES},
            "final_count": np.int16,
            "success45": np.int8,
        },
        engine="c",
    )
    stderr = process.stderr.read() if process.stderr is not None else b""
    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"zstd dataset read failed: {stderr.decode(errors='replace')}")
    if list(frame.columns) != ["seed", *FEATURES, "final_count", "success45"]:
        raise RuntimeError("dataset column order mismatch")
    return (
        frame[FEATURES].to_numpy(dtype=np.float32, copy=True),
        frame["success45"].to_numpy(dtype=np.int8, copy=True),
        frame["seed"].to_numpy(dtype=np.int32, copy=True),
        frame["final_count"].to_numpy(dtype=np.int16, copy=True),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--dataset-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replay", type=int, choices=(1, 2), required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output path already exists")
    if sha256(args.dataset) != args.dataset_sha256:
        parser.error("dataset hash mismatch")
    args.output.mkdir(parents=True)

    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    torch.set_num_threads(1)
    torch.manual_seed(MODEL_SEED)
    torch.cuda.manual_seed_all(MODEL_SEED)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cuda.matmul.allow_tf32 = False
    if not torch.cuda.is_available():
        raise RuntimeError("frozen CUDA training device is unavailable")
    device = torch.device("cuda:0")

    features, labels, seeds, final_counts = load_dataset(args.dataset)
    if features.shape != (1_004_000, 85) or not np.isfinite(features).all():
        raise RuntimeError(f"dataset feature shape/content mismatch: {features.shape}")
    seed_counts = {int(seed): int((seeds == seed).sum()) for seed in np.unique(seeds)}
    if seed_counts != {seed: 50_200 for seed in range(1, 21)}:
        raise RuntimeError("dataset seed distribution mismatch")
    if not np.array_equal(labels, (final_counts <= 45).astype(np.int8)):
        raise RuntimeError("dataset labels do not match final size <=45")

    training_mask = np.isin(seeds, TRAINING_SEEDS)
    calibration_mask = np.isin(seeds, CALIBRATION_SEEDS)
    if int(training_mask.sum()) != 803_200 or int(calibration_mask.sum()) != 200_800:
        raise RuntimeError("training/calibration split count mismatch")
    if np.any(training_mask & calibration_mask) or not np.all(training_mask | calibration_mask):
        raise RuntimeError("training/calibration split overlap or omission")
    training_positive_count = int(labels[training_mask].sum())
    calibration_positive_count = int(labels[calibration_mask].sum())
    positive_weight_value = min(
        math.inf if training_positive_count == 0 else (int(training_mask.sum()) - training_positive_count) / training_positive_count,
        100.0,
    )

    training_features = features[training_mask]
    calibration_features = features[calibration_mask]
    training_labels = labels[training_mask]
    calibration_labels = labels[calibration_mask]
    mean = training_features.mean(axis=0, dtype=np.float64).astype(np.float32)
    scale = training_features.std(axis=0, dtype=np.float64).astype(np.float32)
    scale = np.maximum(scale, np.float32(1e-6))
    fixture_raw = np.asarray(features[:32], dtype=np.float32).copy()
    training_features = ((training_features - mean) / scale).astype(np.float32, copy=False)
    calibration_features = ((calibration_features - mean) / scale).astype(np.float32, copy=False)

    x_train = torch.from_numpy(training_features).to(device)
    y_train = torch.from_numpy(training_labels.astype(np.float32, copy=False)).to(device)
    x_calibration = torch.from_numpy(calibration_features).to(device)
    y_calibration = torch.from_numpy(calibration_labels.astype(np.float32, copy=False)).to(device)
    del features, training_features, calibration_features

    model = torch.nn.Sequential(
        torch.nn.Linear(85, 64),
        torch.nn.ReLU(),
        torch.nn.Linear(64, 32),
        torch.nn.ReLU(),
        torch.nn.Linear(32, 1),
    ).to(device)
    if sum(parameter.numel() for parameter in model.parameters()) != 7_617:
        raise RuntimeError("model parameter count mismatch")
    positive_weight = torch.tensor([positive_weight_value], dtype=torch.float32, device=device)
    loss_function = torch.nn.BCEWithLogitsLoss(pos_weight=positive_weight)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.0001)
    generator = torch.Generator(device=device)
    generator.manual_seed(MODEL_SEED)
    batch_size = 4096
    curve: list[dict[str, Any]] = []
    best_state: dict[str, torch.Tensor] | None = None
    best_ap = -1.0
    best_bce = math.inf
    best_epoch = -1
    stale_epochs = 0

    for epoch in range(1, 51):
        model.train()
        permutation = torch.randperm(len(x_train), generator=generator, device=device)
        loss_sum = 0.0
        for start in range(0, len(x_train), batch_size):
            indices = permutation[start:start + batch_size]
            optimizer.zero_grad(set_to_none=True)
            logits = model(x_train[indices]).squeeze(1)
            loss = loss_function(logits, y_train[indices])
            loss.backward()
            optimizer.step()
            loss_sum += float(loss.detach().cpu()) * len(indices)
        model.eval()
        with torch.no_grad():
            calibration_logits = model(x_calibration).squeeze(1)
            calibration_bce = float(loss_function(calibration_logits, y_calibration).cpu())
            calibration_scores = calibration_logits.cpu().numpy().astype(np.float64)
        calibration_ap = average_precision(calibration_labels, calibration_scores)
        curve.append(
            {
                "epoch": epoch,
                "training_bce": loss_sum / len(x_train),
                "calibration_bce": calibration_bce,
                "calibration_average_precision": calibration_ap,
            }
        )
        improved = calibration_ap > best_ap or (
            calibration_ap == best_ap and calibration_bce < best_bce
        )
        if improved:
            best_ap = calibration_ap
            best_bce = calibration_bce
            best_epoch = epoch
            best_state = {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}
            stale_epochs = 0
        else:
            stale_epochs += 1
        if epoch >= 3 and stale_epochs >= 5:
            break
    if best_state is None:
        raise RuntimeError("no checkpoint selected")
    model.load_state_dict(best_state)

    export_hashes = export_model(args.output, best_state, mean, scale)
    model.eval()
    fixture_standardized = ((fixture_raw - mean) / scale).astype(np.float32)
    with torch.no_grad():
        fixture_logits = model(torch.from_numpy(fixture_standardized).to(device)).squeeze(1).cpu().numpy()
    fixture = {
        "schema_version": "s13-completion-inference-fixture/v1",
        "feature_dimension": 85,
        "rows": [
            {
                "raw_feature_hex": flatten_hex(row),
                "expected_logit_hex": f32_hex(logit),
            }
            for row, logit in zip(fixture_raw, fixture_logits)
        ],
        "comparison": "compiled CPU float32 absolute error <= 1e-4 per row",
    }
    fixture_path = args.output / "model-inference-fixture.json"
    fixture_path.write_text(
        json.dumps(fixture, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    checkpoint_path = args.output / "checkpoint.pt"
    torch.save(
        {
            "schema_version": "s13-completion-checkpoint/v1",
            "state_dict": best_state,
            "normalization_mean": torch.from_numpy(mean),
            "normalization_scale": torch.from_numpy(scale),
            "selected_epoch": best_epoch,
            "model_seed": MODEL_SEED,
        },
        checkpoint_path,
    )
    write_json(args.output / "training-curve.json", curve)
    ended = datetime.now(timezone.utc)
    report = {
        "schema_version": "s13-completion-training-report/v1",
        "replay": args.replay,
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "wall_seconds": round(time.perf_counter() - started_perf, 6),
        "dataset_path": str(args.dataset),
        "dataset_sha256": args.dataset_sha256,
        "rows": len(seeds),
        "feature_dimension": features.shape[1] if 'features' in locals() else 85,
        "seed_counts": {str(key): value for key, value in seed_counts.items()},
        "training_rows": int(training_mask.sum()),
        "calibration_rows": int(calibration_mask.sum()),
        "training_positive_count": training_positive_count,
        "calibration_positive_count": calibration_positive_count,
        "positive_weight": positive_weight_value,
        "zero_positive_training_case": training_positive_count == 0,
        "selected_epoch": best_epoch,
        "selected_calibration_average_precision": best_ap,
        "selected_calibration_bce": best_bce,
        "epochs_run": len(curve),
        "model_seed": MODEL_SEED,
        "trainable_parameters": 7_617,
        "checkpoint_sha256": sha256(checkpoint_path),
        "training_curve_sha256": sha256(args.output / "training-curve.json"),
        "inference_fixture_sha256": sha256(fixture_path),
        **export_hashes,
        "environment": {
            "hostname": platform.node(),
            "platform": platform.platform(),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "torch": torch.__version__,
            "cuda": torch.version.cuda,
            "cudnn": torch.backends.cudnn.version(),
            "gpu": torch.cuda.get_device_name(0),
            "gpu_capability": list(torch.cuda.get_device_capability(0)),
        },
    }
    write_json(args.output / "training-report.json", report)
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
