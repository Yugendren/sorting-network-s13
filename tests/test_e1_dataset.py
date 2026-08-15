from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import unittest

from tools import e1_dataset_gate
from tools.method_runtime import parse_milestone


ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / ".build/senso-instrumented/active.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class E1DatasetTests(unittest.TestCase):
    def active_manifest(self) -> dict:
        active = json.loads(ACTIVE.read_text(encoding="utf-8"))
        manifest_path = ROOT / active["manifest_path"]
        self.assertEqual(sha256(manifest_path), active["manifest_sha256"])
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def test_instrumentation_patch_applies_to_frozen_source(self) -> None:
        source = ROOT / ".build/senso/attempt-20260814T232113Z/source/symmetry-1.1"
        patch = ROOT / "tools/patches/symmetry-1.1-mericanii-instrumentation.patch"
        completed = subprocess.run(
            ["patch", "--dry-run", "-p1", "-i", str(patch)],
            cwd=source,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)

    def test_active_instrumented_build_is_hash_verified(self) -> None:
        manifest = self.active_manifest()
        self.assertEqual(manifest["schema_version"], "s13-senso-instrumented-build/v1")
        self.assertEqual(manifest["status"], "PASS")
        binary = ROOT / manifest["binary_path"]
        patch = ROOT / manifest["instrumentation_patch_path"]
        self.assertEqual(sha256(binary), manifest["binary_sha256"])
        self.assertEqual(sha256(patch), manifest["instrumentation_patch_sha256"])
        self.assertEqual(manifest["archive_sha256"], "d3e960fa5c7b292e38a3024e76436fec3550baa27de240faa90568da0882b53c")

    def test_smoke_dataset_has_three_valid_rows_and_85_features(self) -> None:
        manifest = self.active_manifest()
        dataset = ROOT / manifest["smoke_dataset"]["path"]
        self.assertEqual(sha256(dataset), manifest["smoke_dataset"]["sha256"])
        summary, successes = e1_dataset_gate.validate_dataset(dataset, 1, expected_rows=3)
        self.assertEqual(summary["rows"], 3)
        self.assertEqual(summary["seed"], 1)
        self.assertIsInstance(successes, dict)

    def test_smoke_milestone_is_valid(self) -> None:
        manifest = self.active_manifest()
        milestone = ROOT / manifest["smoke_milestone"]["path"]
        parsed = parse_milestone(milestone)
        self.assertEqual(parsed["channels"], 13)
        self.assertEqual(parsed["generation"], 1)
        self.assertEqual(parsed["evaluations"], 3)

    def test_development_partition_excludes_validation_and_holdout(self) -> None:
        config = ROOT / "config/experiment-v1"
        development = set(json.loads((config / "seeds-development.json").read_text())["seeds"])
        validation = set(json.loads((config / "seeds-validation.json").read_text())["seeds"])
        holdout = set(json.loads((config / "seeds-e3-holdout.json").read_text())["seeds"])
        self.assertEqual(development, set(range(1, 21)))
        self.assertFalse(development & validation)
        self.assertFalse(development & holdout)


if __name__ == "__main__":
    unittest.main()
