from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools import b2_gate, setup_senso


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class B2BaselineTests(unittest.TestCase):
    def test_frozen_parent_hashes_match(self) -> None:
        config = json.loads((ROOT / "config/frozen/b2-execution.json").read_text())
        for name, relative in config["parents"].items():
            if name.endswith("_path"):
                digest_name = name.removesuffix("_path") + "_sha256"
                self.assertEqual(sha256(ROOT / relative), config["parents"][digest_name])

    def test_active_external_build_is_hash_verified(self) -> None:
        manifest = setup_senso.verify_active()
        self.assertIsNotNone(manifest, "run make setup")
        assert manifest is not None
        self.assertEqual(manifest["status"], "PASS")
        self.assertEqual(manifest["archive_sha256"], setup_senso.ARCHIVE_SHA256)

    def test_setup_smoke_milestone_parses(self) -> None:
        manifest = setup_senso.verify_active()
        assert manifest is not None
        milestone = ROOT / manifest["smoke_milestones"][-1]["path"]
        parsed = b2_gate.parse_milestone(milestone)
        self.assertEqual(parsed["channels"], 13)
        self.assertEqual(parsed["generation"], 1)
        self.assertGreater(parsed["comparator_count"], 0)
        self.assertEqual(parsed["evaluations"], 3)

    def test_random_baseline_is_byte_deterministic(self) -> None:
        command = [
            "python3", "src/random_baseline.py", "--channels", "4", "--seed", "17",
            "--trials", "10", "--max-comparators", "64",
        ]
        first = subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        second = subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(first.stderr, b"")
        self.assertEqual(first.stdout, second.stdout)
        report = json.loads(first.stdout)
        self.assertEqual(report["trials"], 10)
        self.assertIsNotNone(report["best_comparators"])

    def test_smoke_candidate_is_accepted_by_both_b1_verifiers(self) -> None:
        manifest = setup_senso.verify_active()
        assert manifest is not None
        parsed = b2_gate.parse_milestone(ROOT / manifest["smoke_milestones"][-1]["path"])
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "smoke.sortnet"
            candidate.write_bytes(b2_gate.candidate_bytes(13, parsed["comparators"], "b2-test-smoke"))
            binary = ROOT / ".build/tests/verifier-b-b2"
            binary.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["go", "build", "-trimpath", "-ldflags=-buildid=", "-o", str(binary), "src/verifier_b.go"],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            commands = [
                ["python3", "src/verifier_a.py", "--expected-channels", "13", str(candidate)],
                [str(binary), "--expected-channels", "13", str(candidate)],
            ]
            reports = [subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.PIPE) for command in commands]
            parsed_reports = [json.loads(report.stdout) for report in reports]
            self.assertEqual([report["verdict"] for report in parsed_reports], ["ACCEPT", "ACCEPT"])
            self.assertEqual(parsed_reports[0]["artifact_sha256"], parsed_reports[1]["artifact_sha256"])


if __name__ == "__main__":
    unittest.main()
