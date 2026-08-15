from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from tools.generate_method_seeds import compact_sha256, reproduce


ROOT = Path(__file__).resolve().parents[1]
E4 = ROOT / "config/experiment-v1/e4"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class E4FreezeTests(unittest.TestCase):
    def test_failure_analysis_precedes_materialized_repair(self) -> None:
        change = json.loads((E4 / "change-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(sha256(ROOT / change["failure_analysis_path"]), change["failure_analysis_sha256"])
        self.assertIn("zero positive", (E4 / "failure-analysis.md").read_text(encoding="utf-8"))
        self.assertEqual(change["e3_seed_outcomes_used"], 0)
        self.assertEqual(change["e4_seed_outcomes_used"], 0)

    def test_e4_holdout_reveals_exact_precommitment(self) -> None:
        manifest = json.loads((E4 / "seeds-e4-holdout.json").read_text(encoding="utf-8"))
        seeds = manifest["seeds"]
        generated = reproduce()
        self.assertEqual(seeds, generated["e4_future_holdout"])
        self.assertEqual(len(seeds), 60)
        self.assertEqual(compact_sha256(seeds), manifest["compact_seed_array_sha256_commitment"])
        earlier: list[int] = []
        for name in ("seeds-development.json", "seeds-validation.json", "seeds-e3-holdout.json"):
            earlier.extend(json.loads((ROOT / "config/experiment-v1" / name).read_text())["seeds"])
        self.assertEqual(len(set(earlier + seeds)), len(earlier + seeds))

    def test_change_manifest_hashes_every_new_freeze(self) -> None:
        change = json.loads((E4 / "change-manifest.json").read_text(encoding="utf-8"))
        for prefix in ("e4_seed_manifest", "model_v2_config", "exam_v2_config"):
            self.assertEqual(sha256(ROOT / change[f"{prefix}_path"]), change[f"{prefix}_sha256"])

    def test_only_learning_objective_changes(self) -> None:
        change = json.loads((E4 / "change-manifest.json").read_text(encoding="utf-8"))
        v1 = json.loads((ROOT / "config/experiment-v1/model-v1.json").read_text(encoding="utf-8"))
        v2 = json.loads((E4 / "model-v2.json").read_text(encoding="utf-8"))
        self.assertEqual(change["selected_major_change"], "learning_objective")
        self.assertFalse(change["representation_change_allowed"])
        self.assertFalse(change["integration_change_allowed"])
        self.assertEqual(v2["architecture"]["layers"], v1["architecture"]["layers"])
        self.assertEqual(v2["architecture"]["trainable_parameters"], v1["architecture"]["trainable_parameters"])
        self.assertEqual(v2["integration"]["patch_sha256"], change["frozen_unchanged"]["integration_patch_sha256"])
        self.assertEqual(v2["objective"]["loss"], "mean squared error")
        self.assertIn("negative final_count", v2["objective"]["raw_target"])
        self.assertEqual(v2["data"]["change_from_v1"], "none")

    def test_v2_exam_keeps_all_six_user_gates(self) -> None:
        exam = json.loads((E4 / "exam-v2.json").read_text(encoding="utf-8"))
        criteria = exam["pass_criteria"]
        self.assertEqual(exam["paired_seed_count"], 60)
        self.assertEqual(exam["candidate_evaluations_per_method_per_seed"], 50_200)
        self.assertEqual(criteria["minimum_mericanii_successes"], 12)
        self.assertEqual(criteria["minimum_success_ratio_vs_senso"], 2.0)
        self.assertEqual(criteria["maximum_mericanii_evaluations_per_seed"], 50_200)
        self.assertTrue(criteria["every_claimed_candidate_dual_verified"])
        self.assertTrue(criteria["integrity_replay"])
        self.assertFalse(criteria["holdout_used_for_tuning"])


if __name__ == "__main__":
    unittest.main()
