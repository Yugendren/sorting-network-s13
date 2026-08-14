from __future__ import annotations

import json
from pathlib import Path
import struct
import tempfile
import unittest

from tools import b3_gate, fetch_harder_certificate, setup_sortnetopt


ROOT = Path(__file__).resolve().parents[1]


class B3ExactTests(unittest.TestCase):
    def test_frozen_source_identities_agree(self) -> None:
        config = json.loads((ROOT / "config/frozen/b3-exact.json").read_text())
        sources = json.loads((ROOT / "config/frozen/sources.json").read_text())["sources"]
        by_id = {item["id"]: item for item in sources}
        self.assertEqual(config["commit"], by_id["sortnetopt"]["commit"])
        self.assertEqual(
            config["certificate_uncompressed_sha256"],
            by_id["harder-n11-certificate"]["uncompressed_sha256"],
        )
        self.assertFalse(config["n11_regeneration_allowed"])

    def test_active_toolchain_matches_frozen_upstream(self) -> None:
        manifest = setup_sortnetopt.verify_active()
        self.assertIsNotNone(manifest, "run make setup")
        assert manifest is not None
        self.assertEqual(manifest["status"], "PASS")
        self.assertEqual(manifest["upstream"]["commit"], setup_sortnetopt.PINNED_COMMIT)
        self.assertIn("x86_64", manifest["checker_binary"]["file_type"])
        self.assertIn("arm64", manifest["rust_binary"]["file_type"])

    def test_active_certificate_matches_published_identity(self) -> None:
        manifest = fetch_harder_certificate.verify_active()
        self.assertIsNotNone(manifest, "run make setup")
        assert manifest is not None
        self.assertEqual(manifest["compressed_size_bytes"], fetch_harder_certificate.COMPRESSED_SIZE_BYTES)
        self.assertEqual(manifest["compressed_md5"], fetch_harder_certificate.COMPRESSED_MD5)
        self.assertEqual(manifest["uncompressed_sha256"], fetch_harder_certificate.UNCOMPRESSED_SHA256)

    def test_checker_result_parser_is_exact(self) -> None:
        self.assertEqual(b3_gate.parse_checker_result("Some (9,25)\n"), (9, 25))
        self.assertIsNone(b3_gate.parse_checker_result("build text\nNone\n"))
        with self.assertRaises(ValueError):
            b3_gate.parse_checker_result("Some (9,25)\nSome (9,25)\n")
        with self.assertRaises(ValueError):
            b3_gate.parse_checker_result("Some (9,24) trailing\n")

    def test_root_bound_corruption_preserves_container_shape(self) -> None:
        step = bytes([9, 25, 0, 2])
        proof = struct.pack("<I", 1) + struct.pack("<QI", 16, len(step)) + step
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "proof.bin"
            target = Path(directory) / "corrupt.bin"
            source.write_bytes(proof)
            mutation = b3_gate.corrupt_root_bound(source, target)
            changed = target.read_bytes()
        self.assertEqual(len(changed), len(proof))
        self.assertEqual(changed[17], 255)
        self.assertEqual(mutation["original_byte"], 25)
        self.assertEqual(mutation["replacement_byte"], 255)
        self.assertNotEqual(mutation["source_sha256"], mutation["corrupted_sha256"])


if __name__ == "__main__":
    unittest.main()
