from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import unittest

from tools import e4_train_gate


ROOT = Path(__file__).resolve().parents[1]
E4 = ROOT / "config/experiment-v1/e4"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class E4TrainingTests(unittest.TestCase):
    def test_training_source_parses_without_local_ml_dependencies(self) -> None:
        source = (ROOT / "tools/train_completion_model_v2.py").read_text(encoding="utf-8")
        ast.parse(source)

    def test_v2_keeps_topology_optimizer_split_and_normalization(self) -> None:
        source = (ROOT / "tools/train_completion_model_v2.py").read_text(encoding="utf-8")
        for literal in (
            "TRAINING_SEEDS = list(range(1, 17))",
            "CALIBRATION_SEEDS = [17, 18, 19, 20]",
            "MODEL_SEED = 2026081501",
            "torch.nn.Linear(85, 64)",
            "torch.nn.Linear(64, 32)",
            "torch.nn.Linear(32, 1)",
            "torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.0001)",
            "batch_size = 4096",
            "for epoch in range(1, 51)",
            "load_v1_normalization(args.v1_export)",
        ):
            self.assertIn(literal, source)

    def test_v2_changes_only_objective_dependent_code(self) -> None:
        source = (ROOT / "tools/train_completion_model_v2.py").read_text(encoding="utf-8")
        self.assertIn("torch.nn.MSELoss()", source)
        self.assertIn("raw_target = -final_counts.astype(np.float64)", source)
        self.assertIn("selected_calibration_micro_concordance", source)
        self.assertNotIn("BCEWithLogitsLoss", source)
        self.assertNotIn("positive_weight", source)
        self.assertNotIn("success45", source)

    def test_gate_is_pinned_to_committed_change_and_development_data(self) -> None:
        prerequisite = e4_train_gate.prerequisite_check()
        self.assertEqual(prerequisite["dataset_sha256"], e4_train_gate.DATASET_SHA256)
        self.assertEqual(prerequisite["v1_export_sha256"], e4_train_gate.V1_EXPORT_SHA256)
        self.assertEqual(prerequisite["change_manifest_sha256"], e4_train_gate.CHANGE_MANIFEST_SHA256)
        self.assertEqual(sha256(E4 / "failure-analysis.md"), e4_train_gate.FAILURE_ANALYSIS_SHA256)

    def test_export_preserves_frozen_cpp_integration_abi(self) -> None:
        source = (ROOT / "tools/train_completion_model_v2.py").read_text(encoding="utf-8")
        self.assertIn('header_path = output / "MericaniiModelV1Weights.hpp"', source)
        self.assertIn('"namespace MericaniiModelV1 {"', source)
        self.assertIn("inline float score(const float* inFeatures)", source)
        change = json.loads((E4 / "change-manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(change["integration_change_allowed"])


if __name__ == "__main__":
    unittest.main()
