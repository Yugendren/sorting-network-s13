from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from tools import setup_senso_mericanii_v1, setup_senso_mericanii_v2


ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / ".build/senso-mericanii-v2/active.json"
METHOD_PATCH = ROOT / "tools/patches/symmetry-1.1-mericanii-v1.patch"
CHANGE = ROOT / "config/experiment-v1/e4/change-manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class E4IntegrationTests(unittest.TestCase):
    def active_manifest(self) -> dict:
        active = json.loads(ACTIVE.read_text(encoding="utf-8"))
        manifest_path = ROOT / active["manifest_path"]
        self.assertEqual(sha256(manifest_path), active["manifest_sha256"])
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def test_v2_builder_does_not_mutate_v1_module(self) -> None:
        self.assertEqual(setup_senso_mericanii_v1.BUILD_ROOT.name, "senso-mericanii-v1")
        self.assertEqual(setup_senso_mericanii_v1.MODEL_HEADER_SHA256, "f7533479d67d44ff5b5da7e9dd3cad9909785e7a912997b8c2b2edfc8fd69864")
        self.assertEqual(setup_senso_mericanii_v2.BUILD_ROOT.name, "senso-mericanii-v2")

    def test_v2_uses_exact_frozen_v1_integration_patch(self) -> None:
        change = json.loads(CHANGE.read_text(encoding="utf-8"))
        expected = change["frozen_unchanged"]["integration_patch_sha256"]
        self.assertEqual(sha256(METHOD_PATCH), expected)
        self.assertEqual(setup_senso_mericanii_v2.expected_hashes()["method_patch_sha256"], expected)

    def test_active_build_and_v2_weights_are_hash_verified(self) -> None:
        manifest = setup_senso_mericanii_v2.verify_active()
        self.assertIsNotNone(manifest, "run make setup-method-v2")
        assert manifest is not None
        self.assertEqual(manifest["schema_version"], "s13-senso-mericanii-build/v2")
        self.assertEqual(manifest["status"], "PASS")
        self.assertEqual(manifest["model_header_sha256"], setup_senso_mericanii_v2.MODEL_HEADER_SHA256)
        self.assertEqual(manifest["model_fixture_sha256"], setup_senso_mericanii_v2.MODEL_FIXTURE_SHA256)
        self.assertEqual(sha256(ROOT / manifest["binary_path"]), manifest["binary_sha256"])

    def test_compiled_float32_fixture_within_frozen_tolerance(self) -> None:
        result = self.active_manifest()["compiled_inference_check"]
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["rows"], 32)
        self.assertLessEqual(result["max_absolute_error"], result["tolerance"])

    def test_smoke_records_ranker_activity(self) -> None:
        stats = self.active_manifest()["smoke_inference_stats"]
        self.assertEqual(stats["rank_calls"], 3)
        self.assertGreaterEqual(stats["score_calls"], stats["rank_calls"])
        self.assertEqual(sum(stats["selected_proposal_histogram"]), stats["rank_calls"])
        self.assertGreater(stats["rank_nanoseconds"], 0)


if __name__ == "__main__":
    unittest.main()
