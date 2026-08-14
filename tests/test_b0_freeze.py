from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / "config/frozen"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class B0FreezeTests(unittest.TestCase):
    def test_authority_hashes_match_supplied_files(self) -> None:
        freeze = json.loads((FROZEN / "b0-freeze.json").read_text())
        for key in ("contract", "prompt", "agents"):
            path = ROOT / freeze["authority"][f"{key}_path"]
            self.assertEqual(sha256(path), freeze["authority"][f"{key}_sha256"])

    def test_seed_freeze_is_exactly_twenty_unique_nonzero_values(self) -> None:
        seeds = json.loads((FROZEN / "seeds.json").read_text())["seeds"]
        self.assertEqual(len(seeds), 20)
        self.assertEqual(len(set(seeds)), 20)
        self.assertTrue(all(isinstance(seed, int) and seed != 0 for seed in seeds))

    def test_contract_caps_are_not_weakened(self) -> None:
        budgets = json.loads((FROZEN / "budgets.json").read_text())
        self.assertFalse(budgets["gpu_allowed"])
        self.assertEqual(budgets["constructive"]["threads_per_seed"], 1)
        self.assertLessEqual(budgets["constructive"]["per_seed_cpu_seconds"], 15 * 60)
        self.assertLessEqual(budgets["constructive"]["aggregate_wall_seconds"], 6 * 60 * 60)
        self.assertLessEqual(budgets["exact_n9"]["wall_seconds"], 10 * 60)
        self.assertLessEqual(budgets["certificate_n11"]["wall_seconds"], 4 * 60 * 60)
        self.assertLessEqual(budgets["total_after_setup"]["wall_seconds"], 12 * 60 * 60)

    def test_constructive_protocol_targets_only_known_baseline(self) -> None:
        freeze = json.loads((FROZEN / "b0-freeze.json").read_text())
        b2 = json.loads((FROZEN / "b2-senso.json").read_text())
        self.assertFalse(freeze["problem"]["frontier_search_allowed"])
        self.assertEqual(b2["channels"], 13)
        self.assertEqual(b2["acceptance_size"], 45)
        self.assertEqual(b2["population"], 200)
        self.assertEqual(b2["generations"], 500)

    def test_source_ids_and_hashes_are_well_formed(self) -> None:
        sources = json.loads((FROZEN / "sources.json").read_text())["sources"]
        ids = [source["id"] for source in sources]
        self.assertEqual(len(ids), len(set(ids)))
        for source in sources:
            if "sha256" in source:
                self.assertRegex(source["sha256"], r"^[0-9a-f]{64}$")
            if "commit" in source:
                self.assertRegex(source["commit"], r"^[0-9a-f]{40}$")

    def test_cached_small_sources_match_frozen_hashes(self) -> None:
        sources = json.loads((FROZEN / "sources.json").read_text())["sources"]
        for source in sources:
            if "cache_file" not in source:
                continue
            path = ROOT / ".cache/sources" / source["cache_file"]
            self.assertTrue(path.is_file(), f"missing {path}; run make setup")
            self.assertEqual(path.stat().st_size, source["size_bytes"])
            self.assertEqual(sha256(path), source["sha256"])

    def test_every_required_frozen_file_exists(self) -> None:
        freeze = json.loads((FROZEN / "b0-freeze.json").read_text())
        required = freeze["required_frozen_files"]
        self.assertEqual(len(required), len(set(required)))
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_makefile_exposes_required_interface(self) -> None:
        makefile = (ROOT / "Makefile").read_text()
        for target in (
            "setup",
            "verify",
            "baseline-b0",
            "baseline-b1",
            "baseline-b2",
            "baseline-b3",
            "baseline-b4",
            "baseline",
            "evidence-check",
            "report",
        ):
            self.assertIn(f"{target}:", makefile)


if __name__ == "__main__":
    unittest.main()
