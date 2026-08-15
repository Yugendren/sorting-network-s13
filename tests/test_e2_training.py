from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest

from tools import e2_train_gate


ROOT = Path(__file__).resolve().parents[1]


class E2TrainingTests(unittest.TestCase):
    def test_training_source_parses_without_importing_remote_dependencies(self) -> None:
        source = (ROOT / "tools/train_completion_model.py").read_text(encoding="utf-8")
        ast.parse(source)

    def test_frozen_model_shape_and_training_constants_are_present(self) -> None:
        config = json.loads((ROOT / "config/experiment-v1/model-v1.json").read_text())
        source = (ROOT / "tools/train_completion_model.py").read_text(encoding="utf-8")
        self.assertEqual(config["architecture"]["layers"], [85, 64, 32, 1])
        self.assertEqual(config["training"]["batch_size"], 4096)
        self.assertEqual(config["training"]["max_epochs"], 50)
        self.assertEqual(config["training"]["seed"], 2026081501)
        for literal in ("Linear(85, 64)", "Linear(64, 32)", "Linear(32, 1)", "batch_size = 4096", "range(1, 51)", "MODEL_SEED = 2026081501"):
            self.assertIn(literal, source)

    def test_e1_dataset_prerequisite_is_exact(self) -> None:
        prerequisite = e2_train_gate.prerequisite_check()
        self.assertEqual(prerequisite["dataset_sha256"], "5628fd5187772bd66ff630bc3889f1973ca8cfefae468b189e586cc83f6be994")
        self.assertEqual(prerequisite["dataset_manifest"]["rows"], 1_004_000)
        self.assertEqual(prerequisite["dataset_manifest"]["success_rows"], 1_216)
        self.assertEqual(prerequisite["dataset_manifest"]["target_44_rows"], 0)

    def test_training_split_is_not_changed_after_e1(self) -> None:
        source = (ROOT / "tools/train_completion_model.py").read_text(encoding="utf-8")
        self.assertIn("TRAINING_SEEDS = list(range(1, 17))", source)
        self.assertIn("CALIBRATION_SEEDS = [17, 18, 19, 20]", source)
        self.assertNotIn("TRAINING_SEEDS = list(range(1, 19))", source)


if __name__ == "__main__":
    unittest.main()
