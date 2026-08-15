#!/usr/bin/env python3
"""Build Mericanii V2 with the frozen V1 integration and V2 weights."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path("/Users/yugendren/experiments/sorting_network_s13")
BASE_PATH = ROOT / "tools/setup_senso_mericanii_v1.py"


def _isolated_builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location("_s13_senso_mericanii_v2_builder", BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load frozen builder: {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BUILDER = _isolated_builder()
MODEL_ROOT = ROOT / "evidence/e4/e4-train-20260815T032452Z/replay-1/artifacts"
MODEL_HEADER = MODEL_ROOT / "MericaniiModelV1Weights.hpp"
MODEL_FIXTURE = MODEL_ROOT / "model-inference-fixture.json"
BUILD_ROOT = ROOT / ".build/senso-mericanii-v2"
ACTIVE = BUILD_ROOT / "active.json"
MODEL_HEADER_SHA256 = "b2caca36602a0fb86ff1f3cb6310ebdd2f3e1b1c420667c426034161334fc984"
MODEL_FIXTURE_SHA256 = "0b63002e366c3e55cb9bd1715510de726293b05fa4f9c38cf78314ff7895c95a"

_BUILDER.MODEL_ROOT = MODEL_ROOT
_BUILDER.MODEL_HEADER = MODEL_HEADER
_BUILDER.MODEL_FIXTURE = MODEL_FIXTURE
_BUILDER.BUILD_ROOT = BUILD_ROOT
_BUILDER.ACTIVE = ACTIVE
_BUILDER.MODEL_HEADER_SHA256 = MODEL_HEADER_SHA256
_BUILDER.MODEL_FIXTURE_SHA256 = MODEL_FIXTURE_SHA256
_BUILDER.METHOD_LABEL = "Mericanii V2"
_BUILDER.METHOD_PROFILE = "mericanii-v2-frozen-v1-integration"
_BUILDER.BUILD_SCHEMA = "s13-senso-mericanii-build/v2"
_BUILDER.FAILURE_SCHEMA = "s13-senso-mericanii-build-failure/v2"


def expected_hashes() -> dict[str, str]:
    return _BUILDER.expected_hashes()


def verify_active() -> dict[str, Any] | None:
    return _BUILDER.verify_active()


def main() -> int:
    return _BUILDER.main()


if __name__ == "__main__":
    raise SystemExit(main())
