from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools import evidence_check


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EvidenceCheckTests(unittest.TestCase):
    def make_run(self, root: Path) -> Path:
        run = root / "b1" / "test-run"
        run.mkdir(parents=True)
        manifest = {
            "schema_version": "s13-evidence-manifest/v1",
            "run_id": "test-run",
            "gate": "B1",
            "source_commit": "a" * 40,
            "dirty_at_start": False,
            "command": ["python3", "tool.py"],
            "started_at": "2026-08-15T00:00:00+00:00",
            "ended_at": "2026-08-15T00:00:01+00:00",
            "wall_seconds": 1.0,
            "cpu_seconds": 0.5,
            "peak_rss_bytes": 1024,
            "threads": 1,
            "host": {},
            "config_sha256": "b" * 64,
            "status": "PASS",
        }
        (run / "manifest.json").write_text(json.dumps(manifest) + "\n")
        (run / "command.txt").write_text("python3 tool.py\n")
        (run / "stdout.txt").write_text("PASS\n")
        (run / "stderr.txt").write_text("")
        files = sorted(path for path in run.iterdir() if path.is_file())
        lines = [f"{sha256(path)}  {path.name}" for path in files]
        (run / "checksums.sha256").write_text("\n".join(lines) + "\n")
        return run

    def test_valid_run_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run = self.make_run(Path(directory))
            self.assertEqual(evidence_check.verify_run(run), [])

    def test_missing_inventory_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run = self.make_run(Path(directory))
            (run / "checksums.sha256").unlink()
            self.assertTrue(any("missing checksums" in error for error in evidence_check.verify_run(run)))

    def test_unsafe_inventory_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            run = self.make_run(Path(directory))
            inventory = run / "checksums.sha256"
            inventory.write_text(inventory.read_text() + f"{'c' * 64}  ../escape\n")
            self.assertTrue(any("unsafe inventory path" in error for error in evidence_check.verify_run(run)))


if __name__ == "__main__":
    unittest.main()
