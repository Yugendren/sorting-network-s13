#!/usr/bin/env python3
"""Verifier A: strict parsing and direct zero-one enumeration."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


TRUTH_LABELS = {
    "PUBLISHED",
    "ARTIFACT_VERIFIED",
    "LOCALLY_REPRODUCED",
    "MEASURED",
    "ASSUMED",
    "UNKNOWN",
}


class CandidateError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Candidate:
    channels: int
    declared_count: int
    layer_count: int | None
    source: str
    truth_label: str
    comparators: tuple[tuple[int, int, int | None], ...]
    checksum: str
    artifact_sha256: str


def decimal(value: str, field: str, *, positive: bool = False) -> int:
    if not re.fullmatch(r"[0-9]+", value):
        raise CandidateError("MALFORMED_HEADER", f"{field} is not decimal")
    number = int(value)
    if positive and number == 0:
        raise CandidateError("MALFORMED_HEADER", f"{field} must be positive")
    return number


def header(line: str, name: str) -> str:
    prefix = name + " "
    if not line.startswith(prefix) or len(line) == len(prefix):
        raise CandidateError("MALFORMED_HEADER", f"missing or empty {name} header")
    return line[len(prefix) :]


def parse_candidate(path: Path, expected_channels: int | None) -> Candidate:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise CandidateError("READ_ERROR", str(exc)) from exc
    artifact_sha256 = hashlib.sha256(raw).hexdigest()
    if not raw.endswith(b"\n"):
        raise CandidateError("MISSING_FINAL_NEWLINE", "artifact must end in one newline")
    if b"\r" in raw:
        raise CandidateError("NON_CANONICAL_NEWLINE", "carriage returns are prohibited")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise CandidateError("INVALID_UTF8", str(exc)) from exc
    lines = text[:-1].split("\n")
    if len(lines) < 9 or any(line == "" for line in lines):
        raise CandidateError("MALFORMED_STRUCTURE", "blank or missing required lines")
    if lines[0] != "sorting-network-v1":
        raise CandidateError("WRONG_SCHEMA", "schema line must be sorting-network-v1")

    channels = decimal(header(lines[1], "channels"), "channels", positive=True)
    declared_count = decimal(header(lines[2], "declared_count"), "declared_count")
    layer_text = header(lines[3], "layer_count")
    layer_count = None if layer_text == "-" else decimal(layer_text, "layer_count")
    source = header(lines[4], "source")
    truth_label = header(lines[5], "truth_label")
    if truth_label not in TRUTH_LABELS:
        raise CandidateError("BAD_TRUTH_LABEL", "unrecognized truth label")
    if lines[6] != "comparators_begin":
        raise CandidateError("MALFORMED_STRUCTURE", "missing comparators_begin")

    if lines[-2] != "comparators_end":
        raise CandidateError("TRAILING_OR_MISSING_DATA", "comparators_end must precede checksum")
    checksum_match = re.fullmatch(r"sha256 ([0-9a-f]{64})", lines[-1])
    if checksum_match is None:
        raise CandidateError("MALFORMED_CHECKSUM", "checksum line is malformed")
    checksum = checksum_match.group(1)
    signed_prefix = ("\n".join(lines[:-1]) + "\n").encode("utf-8")
    if hashlib.sha256(signed_prefix).hexdigest() != checksum:
        raise CandidateError("CHECKSUM_MISMATCH", "candidate checksum does not match")

    comparators: list[tuple[int, int, int | None]] = []
    layer_presence: set[bool] = set()
    prior_layer = -1
    channels_used_by_layer: dict[int, set[int]] = {}
    for line_number, line in enumerate(lines[7:-2], 8):
        match = re.fullmatch(r"([0-9]+) ([0-9]+)(?: ([0-9]+))?", line)
        if match is None:
            raise CandidateError("MALFORMED_COMPARATOR", f"bad comparator at line {line_number}")
        lower = decimal(match.group(1), "lower")
        upper = decimal(match.group(2), "upper")
        layer = decimal(match.group(3), "layer") if match.group(3) is not None else None
        layer_presence.add(layer is not None)
        if not (0 <= lower < upper < channels):
            raise CandidateError("INVALID_CHANNEL_PAIR", f"invalid comparator at line {line_number}")
        if layer is not None:
            if layer_count is None or layer >= layer_count:
                raise CandidateError("INVALID_LAYER", f"layer out of range at line {line_number}")
            if layer < prior_layer:
                raise CandidateError("INVALID_LAYER", "layers must be nondecreasing")
            prior_layer = layer
            used = channels_used_by_layer.setdefault(layer, set())
            if lower in used or upper in used:
                raise CandidateError("LAYER_CONFLICT", f"channel reused in layer {layer}")
            used.update((lower, upper))
        comparators.append((lower, upper, layer))

    if len(layer_presence) > 1:
        raise CandidateError("MIXED_LAYER_ANNOTATIONS", "layers must be present on all or no comparators")
    has_layers = layer_presence == {True}
    if has_layers != (layer_count is not None):
        raise CandidateError("LAYER_HEADER_MISMATCH", "layer_count disagrees with comparator records")
    if len(comparators) != declared_count:
        raise CandidateError("COUNT_MISMATCH", "declared comparator count does not match records")
    if expected_channels is not None and channels != expected_channels:
        raise CandidateError("WRONG_CHANNEL_COUNT", "candidate has the wrong number of channels")
    return Candidate(
        channels=channels,
        declared_count=declared_count,
        layer_count=layer_count,
        source=source,
        truth_label=truth_label,
        comparators=tuple(comparators),
        checksum=checksum,
        artifact_sha256=artifact_sha256,
    )


def duplicate_pairs(candidate: Candidate) -> list[str]:
    counts = Counter((lower, upper) for lower, upper, _ in candidate.comparators)
    return [f"{lower} {upper} x{counts[(lower, upper)]}" for lower, upper in sorted(counts) if counts[(lower, upper)] > 1]


def verify(candidate: Candidate) -> dict[str, object]:
    for input_integer in range(1 << candidate.channels):
        values = [(input_integer >> channel) & 1 for channel in range(candidate.channels)]
        for lower, upper, _ in candidate.comparators:
            if values[lower] > values[upper]:
                values[lower], values[upper] = values[upper], values[lower]
        if any(values[index] > values[index + 1] for index in range(candidate.channels - 1)):
            input_bits = "".join(str((input_integer >> channel) & 1) for channel in range(candidate.channels))
            output_bits = "".join(str(value) for value in values)
            return {
                "artifact_sha256": candidate.artifact_sha256,
                "candidate_checksum": candidate.checksum,
                "channels": candidate.channels,
                "comparators": candidate.declared_count,
                "counterexample": {
                    "input_bits": input_bits,
                    "input_integer": input_integer,
                    "output_bits": output_bits,
                },
                "duplicate_comparators": duplicate_pairs(candidate),
                "implementation": "verifier-a-python-direct-v1",
                "verdict": "INVALID",
            }
    return {
        "artifact_sha256": candidate.artifact_sha256,
        "candidate_checksum": candidate.checksum,
        "channels": candidate.channels,
        "comparators": candidate.declared_count,
        "counterexample": None,
        "duplicate_comparators": duplicate_pairs(candidate),
        "implementation": "verifier-a-python-direct-v1",
        "verdict": "ACCEPT",
    }


def emit(report: dict[str, object]) -> None:
    sys.stdout.write(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-channels", type=int)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    try:
        candidate = parse_candidate(args.candidate, args.expected_channels)
        report = verify(candidate)
    except CandidateError as exc:
        try:
            artifact_hash = hashlib.sha256(args.candidate.read_bytes()).hexdigest()
        except OSError:
            artifact_hash = None
        report = {
            "artifact_sha256": artifact_hash,
            "error": str(exc),
            "error_code": exc.code,
            "implementation": "verifier-a-python-direct-v1",
            "verdict": "MALFORMED",
        }
        emit(report)
        return 2
    emit(report)
    return 0 if report["verdict"] == "ACCEPT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
