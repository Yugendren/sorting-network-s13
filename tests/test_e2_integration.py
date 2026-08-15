from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from tools import setup_senso_mericanii_v1


ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / ".build/senso-mericanii-v1/active.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class E2IntegrationTests(unittest.TestCase):
    def active_manifest(self) -> dict:
        active = json.loads(ACTIVE.read_text(encoding="utf-8"))
        manifest_path = ROOT / active["manifest_path"]
        self.assertEqual(sha256(manifest_path), active["manifest_sha256"])
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def test_active_build_and_frozen_model_are_hash_verified(self) -> None:
        manifest = setup_senso_mericanii_v1.verify_active()
        self.assertIsNotNone(manifest, "run make setup-method-v1")
        assert manifest is not None
        self.assertEqual(manifest["schema_version"], "s13-senso-mericanii-build/v1")
        self.assertEqual(manifest["status"], "PASS")
        self.assertEqual(manifest["model_header_sha256"], setup_senso_mericanii_v1.MODEL_HEADER_SHA256)
        self.assertEqual(manifest["model_fixture_sha256"], setup_senso_mericanii_v1.MODEL_FIXTURE_SHA256)
        self.assertEqual(sha256(ROOT / manifest["binary_path"]), manifest["binary_sha256"])

    def test_compiled_float32_fixture_is_exact(self) -> None:
        result = self.active_manifest()["compiled_inference_check"]
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["rows"], 32)
        self.assertEqual(result["max_absolute_error"], 0)
        self.assertEqual(result["tolerance"], 1.0e-4)

    def test_smoke_records_ranking_without_extra_rng_policy(self) -> None:
        stats = self.active_manifest()["smoke_inference_stats"]
        self.assertEqual(stats["rank_calls"], 3)
        self.assertGreaterEqual(stats["score_calls"], stats["rank_calls"])
        self.assertEqual(sum(stats["selected_proposal_histogram"]), stats["rank_calls"])
        self.assertGreater(stats["rank_nanoseconds"], 0)
        self.assertGreater(stats["score_nanoseconds"], 0)

    def test_patch_contains_exact_frozen_proposals_and_one_base_draw(self) -> None:
        source = (ROOT / "tools/patches/symmetry-1.1-mericanii-v1.patch").read_text(encoding="utf-8")
        for expression in (
            "inBaseProposal, lParentCount",
            "inBaseProposal-2, lParentCount",
            "inBaseProposal+2, lParentCount",
            "inBaseProposal-4, lParentCount",
            "inBaseProposal+4, lParentCount",
            "inBaseProposal-8, lParentCount",
            "inBaseProposal+8, lParentCount",
            "addMericaniiProposal(lProposals, 0, lParentCount)",
        ):
            self.assertIn(expression, source)
        self.assertEqual(source.count("lRandomizer.rollGaussian"), 1)
        self.assertEqual(source.count("lRandomizer.rollInteger"), 1)
        self.assertIn("if (lScores[i] > lScores[lSelected])", source)
        self.assertNotIn("rollUniform", source)


if __name__ == "__main__":
    unittest.main()
