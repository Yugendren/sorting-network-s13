from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from tools import b4_gate


ROOT = Path(__file__).resolve().parents[1]


class B4AggregateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads((ROOT / "config/frozen/b4-aggregate.json").read_text())

    def test_exact_prerequisite_identities_pass(self) -> None:
        records = b4_gate.validate_prerequisites(self.config)
        self.assertEqual([record["gate"] for record in records], ["B0", "B1", "B2", "B3"])
        self.assertTrue(all(record["status"] == "PASS" for record in records))

    def test_semantic_aggregation_passes(self) -> None:
        data = b4_gate.collect_report_data(self.config)
        self.assertEqual(len(data["scored_runs"]), 10)
        self.assertEqual(len(data["b2"]["rows"]["senso"]), 20)
        self.assertEqual(min(row["best_size"] for row in data["b2"]["rows"]["senso"]), 45)
        self.assertEqual(data["b3"]["n11"]["checker_result"], [11, 35])

    def test_report_is_complete_and_has_one_terminal_token(self) -> None:
        data = b4_gate.collect_report_data(self.config)
        report = b4_gate.render_report(data, self.config, "b4-test", "0" * 40)
        b4_gate.validate_report(report, self.config)
        count = sum(report.count(verdict) for verdict in b4_gate.TERMINAL_VERDICTS)
        self.assertEqual(count, 1)
        self.assertEqual(report.count(self.config["terminal_verdict"]), 1)
        self.assertIn("Seed 18 is the sole SENSO-style size-45 result", report)
        self.assertIn("No later experimental contract was drafted or executed", report)

    def test_b2_verifier_disagreement_is_rejected(self) -> None:
        result_path = ROOT / self.config["prerequisites"][2]["run_dir"] / "seed-results.json"
        raw = json.loads(result_path.read_text())
        mutated = deepcopy(raw["senso"])
        mutated[17]["verification"]["verifier_b"] = "INVALID"
        rows = b4_gate.normalized_baseline_rows(mutated)
        with self.assertRaisesRegex(b4_gate.GateFailure, "verifier disagreement"):
            b4_gate.validate_baseline_rows("senso", rows, self.config["expected"]["b2"]["seeds"])

    def test_makefile_exposes_b4_and_report_without_search_command(self) -> None:
        makefile = (ROOT / "Makefile").read_text()
        self.assertIn("$(PYTHON) tools/b4_gate.py", makefile)
        self.assertIn("baseline-report.md", makefile)
        source = (ROOT / "tools/b4_gate.py").read_text()
        self.assertNotIn("search_and_verify.sh", source)
        self.assertNotIn("verify_proof_cert.sh", source)


if __name__ == "__main__":
    unittest.main()
