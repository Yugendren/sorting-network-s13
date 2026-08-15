from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import unittest

from tools import e4_exam_gate


ROOT = Path(__file__).resolve().parents[1]
E4 = ROOT / "config/experiment-v1/e4"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class E4ExamTests(unittest.TestCase):
    def test_exam_source_and_rebuild_source_parse(self) -> None:
        for name in ("e4_exam_gate.py", "e4_integrity_rebuild.py"):
            ast.parse((ROOT / "tools" / name).read_text(encoding="utf-8"))

    def test_exam_constants_match_frozen_artifacts(self) -> None:
        self.assertEqual(sha256(E4 / "exam-v2.json"), e4_exam_gate.EXAM_SHA256)
        self.assertEqual(sha256(E4 / "seeds-e4-holdout.json"), e4_exam_gate.SEEDS_SHA256)
        self.assertEqual(sha256(ROOT / "METHOD_EXPERIMENT_CONTRACT_V1.md"), e4_exam_gate.CONTRACT_SHA256)
        self.assertEqual(sha256(ROOT / "src/verifier_a.py"), e4_exam_gate.VERIFIER_A_SHA256)
        self.assertEqual(sha256(ROOT / "src/verifier_b.go"), e4_exam_gate.VERIFIER_B_SOURCE_SHA256)

    def test_run_order_inherits_frozen_alternation(self) -> None:
        self.assertEqual(e4_exam_gate.run_order(1), ("frozen_mericanii_v2", "frozen_senso"))
        self.assertEqual(e4_exam_gate.run_order(2), ("frozen_senso", "frozen_mericanii_v2"))
        self.assertEqual(e4_exam_gate.run_order(59), ("frozen_mericanii_v2", "frozen_senso"))
        self.assertEqual(e4_exam_gate.run_order(60), ("frozen_senso", "frozen_mericanii_v2"))

    def test_uncertainty_helpers_are_deterministic(self) -> None:
        self.assertEqual(e4_exam_gate.wilson_interval(0, 60)[0], 0.0)
        self.assertEqual(e4_exam_gate.wilson_interval(60, 60)[1], 1.0)
        effects = [1, 0, -1, 1] * 15
        first = e4_exam_gate.paired_bootstrap(effects)
        second = e4_exam_gate.paired_bootstrap(effects)
        self.assertEqual(first, second)
        self.assertEqual(first["resamples"], 10_000)
        self.assertEqual(first["seed"], 2026081502)
        self.assertAlmostEqual(first["point_estimate"], 0.25)

    def test_gate_criteria_do_not_relax_thresholds(self) -> None:
        aggregation = {
            "dual_verified_attempts": 120,
            "methods": {
                "frozen_senso": {"successes": 6, "evaluations_per_seed": [50_200]},
                "frozen_mericanii_v2": {"successes": 12, "evaluations_per_seed": [50_200]},
            },
            "paired_results": [],
        }
        criteria = e4_exam_gate.gate_criteria(aggregation, integrity_pass=True, no_holdout_tuning=True)
        self.assertTrue(all(criteria.values()))
        aggregation["methods"]["frozen_mericanii_v2"]["successes"] = 11
        self.assertFalse(e4_exam_gate.gate_criteria(aggregation, integrity_pass=True, no_holdout_tuning=True)["mericanii_at_least_12_of_60"])

    def test_holdout_is_60_unique_and_disjoint(self) -> None:
        seeds = json.loads((E4 / "seeds-e4-holdout.json").read_text(encoding="utf-8"))["seeds"]
        earlier: list[int] = []
        for name in ("seeds-development.json", "seeds-validation.json", "seeds-e3-holdout.json"):
            earlier.extend(json.loads((ROOT / "config/experiment-v1" / name).read_text(encoding="utf-8"))["seeds"])
        self.assertEqual(len(seeds), 60)
        self.assertEqual(len(set(seeds)), 60)
        self.assertFalse(set(seeds) & set(earlier))

    def test_scored_runtime_uses_frozen_environment_allowlist(self) -> None:
        self.assertEqual(
            e4_exam_gate.PARENT_ENVIRONMENT_ALLOWLIST,
            ("PATH", "TMPDIR", "USER", "LOGNAME", "SHELL"),
        )
        source = (ROOT / "tools/e4_exam_gate.py").read_text(encoding="utf-8")
        self.assertIn("parent_environment_allowlist=PARENT_ENVIRONMENT_ALLOWLIST", source)


if __name__ == "__main__":
    unittest.main()
