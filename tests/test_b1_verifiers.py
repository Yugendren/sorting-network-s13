from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / ".build/tests/verifier-b"


class B1VerifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        BINARY.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["go", "build", "-trimpath", "-ldflags=-buildid=", "-o", str(BINARY), "src/verifier_b.go"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def run_verifier(self, verifier: str, path: str, channels: int) -> tuple[int, bytes, dict[str, object]]:
        if verifier == "A":
            command = ["python3", "src/verifier_a.py", "--expected-channels", str(channels), path]
        else:
            command = [str(BINARY), "--expected-channels", str(channels), path]
        completed = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        self.assertEqual(completed.stderr, b"")
        return completed.returncode, completed.stdout, json.loads(completed.stdout)

    def test_public_witness_is_accepted_independently(self) -> None:
        path = "witnesses/public/n13-45-dobbelaere.sortnet"
        reports = [self.run_verifier(verifier, path, 13) for verifier in ("A", "B")]
        self.assertEqual([result[0] for result in reports], [0, 0])
        self.assertEqual([result[2]["verdict"] for result in reports], ["ACCEPT", "ACCEPT"])
        self.assertEqual(reports[0][2]["artifact_sha256"], reports[1][2]["artifact_sha256"])
        self.assertEqual(reports[0][2]["candidate_checksum"], reports[1][2]["candidate_checksum"])

    def test_invalid_network_has_same_first_counterexample(self) -> None:
        path = "tests/fixtures/b1/negative/n3-two-comparator.sortnet"
        reports = [self.run_verifier(verifier, path, 3) for verifier in ("A", "B")]
        self.assertEqual([result[0] for result in reports], [1, 1])
        self.assertEqual(reports[0][2]["counterexample"], reports[1][2]["counterexample"])
        self.assertEqual(reports[0][2]["counterexample"]["input_integer"], 3)

    def test_malformed_fixtures_are_rejected_by_both(self) -> None:
        for path in sorted((ROOT / "tests/fixtures/b1/malformed").glob("*.sortnet")):
            with self.subTest(path=path.name):
                reports = [self.run_verifier(verifier, str(path), 3) for verifier in ("A", "B")]
                self.assertEqual([result[0] for result in reports], [2, 2])
                self.assertEqual([result[2]["verdict"] for result in reports], ["MALFORMED", "MALFORMED"])
                self.assertEqual(reports[0][2]["error_code"], reports[1][2]["error_code"])

    def test_repeated_comparator_is_legal_and_reported(self) -> None:
        path = "witnesses/small/n2-repeated.sortnet"
        reports = [self.run_verifier(verifier, path, 2) for verifier in ("A", "B")]
        self.assertEqual([result[2]["verdict"] for result in reports], ["ACCEPT", "ACCEPT"])
        self.assertEqual(reports[0][2]["duplicate_comparators"], ["0 1 x2"])
        self.assertEqual(reports[1][2]["duplicate_comparators"], ["0 1 x2"])

    def test_reports_are_byte_deterministic(self) -> None:
        path = "witnesses/public/n13-45-dobbelaere.sortnet"
        for verifier in ("A", "B"):
            first = self.run_verifier(verifier, path, 13)
            second = self.run_verifier(verifier, path, 13)
            self.assertEqual(first[:2], second[:2])


if __name__ == "__main__":
    unittest.main()
