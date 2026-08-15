from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools import e2_validation_gate


ROOT = Path(__file__).resolve().parents[1]
MODEL_ROOT = ROOT / "evidence/e2/e2-train-20260815T023758Z/replay-1/artifacts"


class E2ValidationTests(unittest.TestCase):
    def test_validation_gate_parses_without_ml_runtime(self) -> None:
        source = (ROOT / "tools/e2_validation_gate.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertNotIn("import torch", source)
        self.assertNotIn("import numpy", source)
        self.assertIn('"no_e3_seed_accessed": True', source)

    def test_primary_rule_is_fixed_micro_within_seed_concordance(self) -> None:
        source = (ROOT / "tools/e2_validation_gate.py").read_text(encoding="utf-8")
        self.assertIn("micro over unequal-final-size pairs within seeds; exact score ties contribute 0.5", source)
        self.assertIn('metric["micro_concordance"] > 0.5', source)
        self.assertIn("E3 is forbidden for V1", source)

    def test_stream_scorer_constant_scores_equal_reference(self) -> None:
        active = json.loads((ROOT / ".build/senso-instrumented/active.json").read_text(encoding="utf-8"))
        build = json.loads((ROOT / active["manifest_path"]).read_text(encoding="utf-8"))
        smoke = ROOT / build["smoke_dataset"]["path"]
        lines = smoke.read_text(encoding="utf-8").splitlines()
        fields = lines[1].split("\t")
        synthetic = [lines[0]]
        for index, final_count in enumerate((45, 46, 47, 48)):
            row = fields.copy()
            row[3] = str(index)
            row[91] = str(final_count)
            row[92] = "1" if final_count <= 45 else "0"
            row[93] = ""
            synthetic.append("\t".join(row))
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            binary = directory_path / "scorer"
            compiled = subprocess.run(
                [
                    "clang++", "-std=c++11", "-O2", "-I", str(MODEL_ROOT),
                    "tools/score_validation_model.cpp", "-o", str(binary),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            scored = subprocess.run(
                [str(binary)],
                cwd=ROOT,
                input="\n".join(synthetic) + "\n",
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        self.assertEqual(scored.returncode, 0, scored.stderr)
        report = json.loads(scored.stdout)
        self.assertEqual(report["comparable_pairs"], 6)
        self.assertEqual(report["tied_score_pairs"], 6)
        self.assertEqual(report["micro_concordance"], 0.5)

    def test_report_labels_holdout_and_frontier_unknown(self) -> None:
        report = e2_validation_gate.render_report("test", "0" * 40, None, None, None, "FAIL", "test")
        self.assertIn("UNKNOWN: E3 final-holdout performance", report)
        self.assertIn("UNKNOWN: existence of a 44-comparator network", report)
        self.assertNotIn("METHOD_REJECTED", report)


if __name__ == "__main__":
    unittest.main()
