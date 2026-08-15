from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from tools.generate_method_seeds import reproduce


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/experiment-v1"


def load(name: str) -> dict:
    return json.loads((CONFIG / name).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class E0MethodFreezeTests(unittest.TestCase):
    def test_authority_and_predecessor_pins(self) -> None:
        freeze = load("e0-freeze.json")
        authority = freeze["authority"]
        self.assertEqual(sha256(ROOT / authority["contract_path"]), authority["contract_sha256"])
        predecessor = freeze["predecessor"]
        for path_key, hash_key in (
            ("report_path", "report_sha256"),
            ("python_verifier_path", "python_verifier_sha256"),
            ("go_verifier_path", "go_verifier_sha256"),
            ("b2_execution_path", "b2_execution_sha256"),
            ("b2_senso_path", "b2_senso_sha256"),
            ("b2_seeds_path", "b2_seeds_sha256"),
        ):
            self.assertEqual(sha256(ROOT / predecessor[path_key]), predecessor[hash_key])

    def test_config_inventory_is_complete_and_exact(self) -> None:
        freeze = load("e0-freeze.json")
        inventory = {item["path"]: item["sha256"] for item in freeze["config_inventory"]}
        expected = {
            path.relative_to(ROOT).as_posix()
            for path in CONFIG.glob("*.json")
            if path.name != "e0-freeze.json"
        }
        self.assertEqual(set(inventory), expected)
        for relative, digest in inventory.items():
            self.assertEqual(sha256(ROOT / relative), digest)

    def test_seed_partitions_reproduce_and_are_disjoint(self) -> None:
        generated = reproduce()
        development = load("seeds-development.json")["seeds"]
        validation = load("seeds-validation.json")["seeds"]
        e3 = load("seeds-e3-holdout.json")["seeds"]
        self.assertEqual(generated["development"], development)
        self.assertEqual(generated["validation"], validation)
        self.assertEqual(generated["e3_final_holdout"], e3)
        self.assertEqual([len(development), len(validation), len(e3)], [20, 20, 60])
        all_materialized = development + validation + e3
        self.assertEqual(len(all_materialized), len(set(all_materialized)))
        policy = load("seed-policy.json")
        self.assertEqual(
            generated["e4_compact_seed_array_sha256"],
            policy["partitions"][3]["compact_seed_array_sha256_commitment"],
        )

    def test_feature_indices_exactly_cover_85_inputs(self) -> None:
        features = load("features-v1.json")
        occupied = {item["index"] for item in features["scalar_features"]}
        for block in features["channel_blocks"]:
            occupied.update(range(block["start"], block["start"] + block["length"]))
        recent = features["recent_comparator_block"]
        occupied.update(range(recent["start"], recent["start"] + recent["length"]))
        self.assertEqual(features["input_dimension"], 85)
        self.assertEqual(occupied, set(range(85)))

    def test_model_is_small_and_only_ranks_truncation(self) -> None:
        model = load("model-v1.json")
        layers = model["architecture"]["layers"]
        count = sum(left * right + right for left, right in zip(layers, layers[1:]))
        self.assertEqual(count, 7617)
        self.assertEqual(count, model["architecture"]["trainable_parameters"])
        self.assertLessEqual(count, model["architecture"]["parameter_ceiling"])
        self.assertIn("truncation", model["role"])
        self.assertEqual(model["objective"]["label"], "final_count <= 45")
        self.assertEqual(model["integration"]["baseline_gaussian_draws_per_reconstruction"], 1)
        self.assertEqual(model["integration"]["proposal_count_maximum"], 8)
        self.assertIn("exactly recover", model["integration"]["constant_model_equivalence"])

    def test_dataset_and_exam_never_target_44(self) -> None:
        dataset = load("dataset-v1.json")
        exam = load("exam-v1.json")
        self.assertEqual(dataset["target_comparators"], 45)
        self.assertEqual(dataset["expected_total_rows"], 1_004_000)
        self.assertEqual(exam["acceptance_comparators"], 45)
        self.assertEqual(exam["paired_seed_count"], 60)
        self.assertEqual(exam["candidate_evaluations_per_method_per_seed"], 50_200)
        self.assertEqual(exam["pass_criteria"]["minimum_mericanii_successes"], 12)
        self.assertEqual(exam["pass_criteria"]["minimum_success_ratio_vs_senso"], 2.0)

    def test_frontier_is_conditional_and_bounded(self) -> None:
        frontier = load("budgets-v1.json")["e5"]
        self.assertTrue(frontier["enabled_only_after_method_pass"])
        self.assertEqual(frontier["target_comparators"], 44)
        self.assertEqual(frontier["aggregate_candidate_evaluations"], 100_000_000)
        self.assertEqual(frontier["calendar_seconds"], 7 * 24 * 60 * 60)
        self.assertFalse(frontier["paid_compute"])

    def test_goal_ledger_remains_concise(self) -> None:
        lines = (ROOT / "GOAL_STATE.md").read_text(encoding="utf-8").splitlines()
        self.assertLess(len(lines), 120)


if __name__ == "__main__":
    unittest.main()
