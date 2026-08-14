#!/usr/bin/env python3
"""Fetch only the small, B0-pinned source artifacts into the ignored cache."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request


ROOT = Path("/Users/yugendren/experiments/sorting_network_s13")
CACHE = ROOT / ".cache"
SOURCES = CACHE / "sources"
THIRD_PARTY = CACHE / "third_party"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, destination: Path, expected_sha256: str, expected_size: int) -> None:
    if destination.exists():
        actual = sha256(destination)
        if actual != expected_sha256 or destination.stat().st_size != expected_size:
            raise RuntimeError(f"cached artifact mismatch: {destination}")
        print(f"verified cached {destination.relative_to(ROOT)}")
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "s13-baseline-b0/1"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as out:
            shutil.copyfileobj(response, out, length=1024 * 1024)
        actual = sha256(partial)
        if actual != expected_sha256 or partial.stat().st_size != expected_size:
            raise RuntimeError(
                f"download mismatch for {url}: sha256={actual}, size={partial.stat().st_size}"
            )
        os.replace(partial, destination)
    finally:
        if partial.exists():
            partial.unlink()
    print(f"fetched {destination.relative_to(ROOT)}")


def clone_exact(url: str, commit: str, destination: Path) -> None:
    if not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--filter=blob:none", "--no-checkout", url, str(destination)],
            check=True,
        )
    subprocess.run(["git", "-C", str(destination), "fetch", "--filter=blob:none", "origin", commit], check=True)
    subprocess.run(["git", "-C", str(destination), "checkout", "--detach", commit], check=True)
    head = subprocess.check_output(["git", "-C", str(destination), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(
        ["git", "-C", str(destination), "status", "--porcelain"], text=True
    ).strip()
    if head != commit or dirty:
        raise RuntimeError(f"third-party checkout mismatch or dirty state: {destination}")
    print(f"verified {destination.relative_to(ROOT)} @ {commit}")


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        raise RuntimeError(f"run only from {ROOT}")

    ledger = json.loads((ROOT / "config/frozen/sources.json").read_text(encoding="utf-8"))
    for item in ledger["sources"]:
        cache_file = item.get("cache_file")
        if cache_file:
            download(item["url"], SOURCES / cache_file, item["sha256"], item["size_bytes"])

    by_id = {item["id"]: item for item in ledger["sources"]}
    sortnetopt = by_id["sortnetopt"]
    clone_exact(sortnetopt["url"], sortnetopt["commit"], THIRD_PARTY / "sortnetopt")

    catalog = by_id["dobbelaere-catalog"]
    clone_exact(catalog["repository"], catalog["commit"], THIRD_PARTY / "dobbelaere-catalog")
    checked_html = THIRD_PARTY / "dobbelaere-catalog" / "sorting_networks_extended.html"
    if sha256(checked_html) != catalog["sha256"]:
        raise RuntimeError("catalog Git snapshot does not match the frozen retrieved HTML")

    print("B0 source cache ready; the n=11 certificate is intentionally deferred to B3.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"setup failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
