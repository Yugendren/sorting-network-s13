#!/usr/bin/env python3
"""Run the complete, fail-closed B1 independent-verifier gate."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
from itertools import product
import json
import os
from pathlib import Path
import platform
import random
import resource
import shutil
import subprocess
import sys
import time
from typing import Any


ROOT = Path("/Users/yugendren/experiments/sorting_network_s13")
CONFIG_PATH = ROOT / "config/frozen/b1-verification.json"
BUILD_ROOT = ROOT / ".build/b1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aggregate_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256(path)))
        digest.update(b"\n")
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_checksums(directory: Path) -> None:
    files = sorted(path for path in directory.rglob("*") if path.is_file() and path.name != "checksums.sha256")
    lines = [f"{sha256(path)}  {path.relative_to(directory).as_posix()}" for path in files]
    (directory / "checksums.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_text(command: list[str], *, check: bool = True) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}\n{completed.stdout}")
    return completed.stdout.strip()


def sysctl(name: str) -> str:
    return subprocess.check_output(["sysctl", "-n", name], text=True).strip()


def host_record() -> dict[str, Any]:
    disk = shutil.disk_usage(ROOT)
    return {
        "model": sysctl("hw.model"),
        "cpu": sysctl("machdep.cpu.brand_string"),
        "logical_cores": int(sysctl("hw.logicalcpu")),
        "physical_cores": int(sysctl("hw.physicalcpu")),
        "memory_bytes": int(sysctl("hw.memsize")),
        "os": platform.platform(),
        "machine": platform.machine(),
        "disk_free_bytes_at_start": disk.free,
    }


def check_b0_prerequisite() -> list[str]:
    completed = subprocess.run(
        [sys.executable, "tools/evidence_check.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"B0 evidence integrity prerequisite failed:\n{completed.stdout}")
    passes: list[str] = []
    for path in sorted((ROOT / "evidence/b0").glob("*/manifest.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if manifest.get("status") == "PASS":
            passes.append(path.parent.relative_to(ROOT).as_posix())
    if not passes:
        raise RuntimeError("B1 requires committed B0 PASS evidence")
    return passes


def candidate_bytes(
    channels: int,
    comparators: list[tuple[int, int, int | None]],
    source: str,
) -> bytes:
    layered = bool(comparators) and all(layer is not None for _, _, layer in comparators)
    if any(layer is not None for _, _, layer in comparators) != layered:
        raise RuntimeError("generated candidate has mixed layer annotations")
    layer_count = str(max(layer for _, _, layer in comparators if layer is not None) + 1) if layered else "-"
    lines = [
        "sorting-network-v1",
        f"channels {channels}",
        f"declared_count {len(comparators)}",
        f"layer_count {layer_count}",
        f"source {source}",
        "truth_label ASSUMED",
        "comparators_begin",
    ]
    for lower, upper, layer in comparators:
        suffix = f" {layer}" if layer is not None else ""
        lines.append(f"{lower} {upper}{suffix}")
    lines.append("comparators_end")
    prefix = ("\n".join(lines) + "\n").encode()
    return prefix + f"sha256 {hashlib.sha256(prefix).hexdigest()}\n".encode()


def load_transform_fixture(path: Path) -> tuple[int, list[tuple[int, int, int | None]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    channels = int(lines[1].split(" ", 1)[1])
    begin = lines.index("comparators_begin") + 1
    end = lines.index("comparators_end")
    comparators: list[tuple[int, int, int | None]] = []
    for line in lines[begin:end]:
        parts = [int(part) for part in line.split(" ")]
        comparators.append((parts[0], parts[1], parts[2] if len(parts) == 3 else None))
    return channels, comparators


class GateRunner:
    def __init__(
        self,
        config: dict[str, Any],
        binary: Path,
        generated: Path,
        deadline: float,
        stderr_lines: list[str],
    ) -> None:
        self.config = config
        self.binary = binary
        self.generated = generated
        self.deadline = deadline
        self.stderr_lines = stderr_lines
        self.results: list[dict[str, Any]] = []

    def invoke(self, verifier: str, path: Path, expected_channels: int) -> tuple[int, bytes, bytes, dict[str, Any]]:
        if verifier == "A":
            command = [sys.executable, "src/verifier_a.py", "--expected-channels", str(expected_channels), str(path)]
        else:
            command = [str(self.binary), "--expected-channels", str(expected_channels), str(path)]
        remaining = self.deadline - time.perf_counter()
        if remaining <= 0:
            raise TimeoutError("B1 aggregate wall limit reached")
        timeout = min(self.config["limits"]["per_verifier_timeout_seconds"], remaining)
        env = os.environ.copy()
        env["GOMAXPROCS"] = "1"
        try:
            completed = subprocess.run(
                command,
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=timeout,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"verifier {verifier} timed out for {path.name}") from exc
        if completed.stderr:
            self.stderr_lines.append(f"{verifier} {path.name}: {completed.stderr.decode(errors='replace')}")
        try:
            report = json.loads(completed.stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"verifier {verifier} emitted invalid JSON for {path.name}") from exc
        return completed.returncode, completed.stdout, completed.stderr, report

    def pair(
        self,
        case_id: str,
        category: str,
        path: Path,
        expected_channels: int,
        expected_verdict: str | None,
        *,
        deterministic: bool = False,
        details: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, bytes]]:
        replays = self.config["deterministic_replays"] if deterministic else 1
        invocations: dict[str, list[tuple[int, bytes, bytes, dict[str, Any]]]] = {"A": [], "B": []}
        for verifier in ("A", "B"):
            for _ in range(replays):
                invocations[verifier].append(self.invoke(verifier, path, expected_channels))
            first = invocations[verifier][0]
            if any((item[0], item[1], item[2]) != (first[0], first[1], first[2]) for item in invocations[verifier][1:]):
                raise RuntimeError(f"nondeterministic verifier {verifier} report for {case_id}")

        code_a, stdout_a, stderr_a, report_a = invocations["A"][0]
        code_b, stdout_b, stderr_b, report_b = invocations["B"][0]
        verdict_a, verdict_b = report_a.get("verdict"), report_b.get("verdict")
        if verdict_a != verdict_b:
            raise RuntimeError(f"verifier disagreement for {case_id}: {verdict_a} vs {verdict_b}")
        if expected_verdict is not None and verdict_a != expected_verdict:
            raise RuntimeError(f"unexpected verdict for {case_id}: {verdict_a}, expected {expected_verdict}")
        expected_code = {"ACCEPT": 0, "INVALID": 1, "MALFORMED": 2}.get(verdict_a)
        if expected_code is None or code_a != expected_code or code_b != expected_code:
            raise RuntimeError(f"exit-code disagreement for {case_id}: A={code_a}, B={code_b}, verdict={verdict_a}")
        if report_a.get("artifact_sha256") != report_b.get("artifact_sha256"):
            raise RuntimeError(f"artifact hash disagreement for {case_id}")
        if verdict_a in ("ACCEPT", "INVALID"):
            for field in ("candidate_checksum", "channels", "comparators", "counterexample"):
                if report_a.get(field) != report_b.get(field):
                    raise RuntimeError(f"verifier disagreement for {case_id} field {field}")
            if sorted(report_a.get("duplicate_comparators", [])) != sorted(report_b.get("duplicate_comparators", [])):
                raise RuntimeError(f"duplicate-warning disagreement for {case_id}")
        elif report_a.get("error_code") != report_b.get("error_code"):
            raise RuntimeError(f"malformed error-code disagreement for {case_id}")

        result: dict[str, Any] = {
            "case_id": case_id,
            "category": category,
            "expected_channels": expected_channels,
            "artifact_sha256": report_a.get("artifact_sha256"),
            "candidate_checksum": report_a.get("candidate_checksum"),
            "verdict": verdict_a,
            "counterexample": report_a.get("counterexample"),
            "verifier_a_report_sha256": hashlib.sha256(stdout_a).hexdigest(),
            "verifier_b_report_sha256": hashlib.sha256(stdout_b).hexdigest(),
            "verifier_b_failing_input_count": report_b.get("failing_input_count"),
            "deterministic_replays": replays,
        }
        if details:
            result["details"] = details
        self.results.append(result)
        return result, {"a_stdout": stdout_a, "a_stderr": stderr_a, "b_stdout": stdout_b, "b_stderr": stderr_b}


def main() -> int:
    if Path.cwd().resolve() != ROOT:
        print(f"B1 preflight failed: cwd must be exactly {ROOT}", file=sys.stderr)
        return 2
    if run_text(["git", "branch", "--show-current"]) != "goal/s13-baseline":
        print("B1 preflight failed: wrong branch", file=sys.stderr)
        return 2
    dirty = run_text(["git", "status", "--porcelain", "--untracked-files=all"])
    if dirty:
        print("B1 preflight failed: scored configuration is dirty", file=sys.stderr)
        print(dirty, file=sys.stderr)
        return 2
    try:
        b0_passes = check_b0_prerequisite()
    except Exception as exc:
        print(f"B1 preflight failed: {exc}", file=sys.stderr)
        return 2

    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    started_cpu = time.process_time()
    run_id = started.strftime("b1-%Y%m%dT%H%M%SZ")
    out = ROOT / "evidence/b1" / run_id
    out.mkdir(parents=True, exist_ok=False)
    generated = BUILD_ROOT / "generated" / run_id
    generated.mkdir(parents=True, exist_ok=False)
    binary = BUILD_ROOT / "verifier-b"
    status = "FAIL"
    error: str | None = None
    config_hash = "0" * 64
    host: dict[str, Any] = {}
    log_lines = ["B1 falsifiable gate: two independent verifiers must agree on every frozen case."]
    stderr_lines: list[str] = []
    results: list[dict[str, Any]] = []
    build_record: dict[str, Any] = {}
    config_snapshot: dict[str, Any] = {}

    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        shutil.copyfile(CONFIG_PATH, out / "frozen-b1-config.json")
        limits = config["limits"]
        deadline = started_perf + limits["wall_seconds"]
        fixture_entries = config["positive_fixtures"] + config["negative_fixtures"] + config["malformed_fixtures"]
        frozen_paths = [
            CONFIG_PATH,
            ROOT / config["verifier_a"]["path"],
            ROOT / config["verifier_b"]["path"],
            ROOT / "tools/b1_gate.py",
            ROOT / "tests/test_b1_verifiers.py",
            ROOT / "docs/candidate-format.md",
            ROOT / "docs/b1-verification.md",
            *(ROOT / entry["path"] for entry in fixture_entries),
        ]
        if len({path.resolve() for path in frozen_paths}) != len(frozen_paths):
            frozen_paths = list(dict.fromkeys(frozen_paths))
        for path in frozen_paths:
            if not path.is_file():
                raise RuntimeError(f"missing frozen B1 input: {path.relative_to(ROOT)}")
        for entry in fixture_entries:
            actual = sha256(ROOT / entry["path"])
            if actual != entry["artifact_sha256"]:
                raise RuntimeError(f"fixture hash mismatch: {entry['path']}")
        config_hash = aggregate_hash(frozen_paths)
        config_snapshot = {
            "aggregate_sha256": config_hash,
            "b0_pass_prerequisites": b0_passes,
            "files": [
                {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)} for path in sorted(frozen_paths)
            ],
            "limits": limits,
        }

        build_command = ["go", "build", "-trimpath", "-ldflags=-buildid=", "-o", str(binary), config["verifier_b"]["path"]]
        build_env = os.environ.copy()
        build_env["GOMAXPROCS"] = "1"
        built = subprocess.run(
            build_command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=min(60, max(1, deadline - time.perf_counter())),
            env=build_env,
        )
        if built.stdout:
            log_lines.append(built.stdout.rstrip())
        if built.stderr:
            stderr_lines.append(built.stderr.rstrip())
        if built.returncode != 0:
            raise RuntimeError(f"Verifier B build failed with exit {built.returncode}")
        build_record = {
            "command": build_command,
            "go_version": run_text(["go", "version"]),
            "python_version": run_text([sys.executable, "--version"]),
            "verifier_a_source_sha256": sha256(ROOT / config["verifier_a"]["path"]),
            "verifier_b_source_sha256": sha256(ROOT / config["verifier_b"]["path"]),
            "verifier_b_binary_sha256": sha256(binary),
            "gomaxprocs": 1,
        }
        runner = GateRunner(config, binary, generated, deadline, stderr_lines)

        public_raw: dict[str, bytes] | None = None
        for entry in config["positive_fixtures"]:
            result, raw = runner.pair(
                f"positive:{entry['path']}", "positive", ROOT / entry["path"], entry["expected_channels"], "ACCEPT",
                deterministic=True,
            )
            if result["artifact_sha256"] != entry["artifact_sha256"] or result["candidate_checksum"] != entry["candidate_checksum"]:
                raise RuntimeError(f"positive fixture identity mismatch: {entry['path']}")
            if entry["path"] == "witnesses/public/n13-45-dobbelaere.sortnet":
                public_raw = raw
        if public_raw is None:
            raise RuntimeError("public witness was not tested")
        shutil.copyfile(ROOT / "witnesses/public/n13-45-dobbelaere.sortnet", out / "public-witness.sortnet")
        (out / "public-verifier-a.json").write_bytes(public_raw["a_stdout"])
        (out / "public-verifier-b.json").write_bytes(public_raw["b_stdout"])
        (out / "public-verifier-a.stderr").write_bytes(public_raw["a_stderr"])
        (out / "public-verifier-b.stderr").write_bytes(public_raw["b_stderr"])

        for entry in config["negative_fixtures"]:
            result, _ = runner.pair(
                f"negative:{entry['path']}", "negative", ROOT / entry["path"], entry["expected_channels"], "INVALID",
                deterministic=True,
            )
            if result["artifact_sha256"] != entry["artifact_sha256"] or result["candidate_checksum"] != entry["candidate_checksum"]:
                raise RuntimeError(f"negative fixture identity mismatch: {entry['path']}")
            if result["counterexample"] is None:
                raise RuntimeError(f"negative fixture lacks a counterexample: {entry['path']}")

        for entry in config["malformed_fixtures"]:
            result, _ = runner.pair(
                f"malformed:{entry['path']}", "malformed", ROOT / entry["path"], entry["expected_channels"], "MALFORMED",
                deterministic=True,
            )
            if result["artifact_sha256"] != entry["artifact_sha256"]:
                raise RuntimeError(f"malformed fixture identity mismatch: {entry['path']}")

        wrong = config["wrong_channel_fixture"]
        runner.pair(
            "malformed:wrong-channel-count", "malformed", ROOT / wrong["path"], wrong["expected_channels"], "MALFORMED",
            deterministic=True,
        )
        missing_newline = generated / "missing-final-newline.sortnet"
        missing_newline.write_bytes((ROOT / "witnesses/small/n2-one.sortnet").read_bytes()[:-1])
        runner.pair("malformed:missing-final-newline", "malformed", missing_newline, 2, "MALFORMED", deterministic=True)

        public_channels, public_comparators = load_transform_fixture(ROOT / "witnesses/public/n13-45-dobbelaere.sortnet")
        for index in config["witness_mutations"]["removed_zero_based_indices"]:
            mutated = public_comparators[:index] + public_comparators[index + 1 :]
            path = generated / f"public-remove-{index:02d}.sortnet"
            path.write_bytes(candidate_bytes(public_channels, mutated, f"b1-public-removal-{index}"))
            result, _ = runner.pair(
                f"mutation:remove-{index}", "mutation", path, public_channels,
                config["witness_mutations"]["required_verdict"],
                details={"removed_index": index, "removed_comparator": public_comparators[index], "comparators": mutated},
            )
            if result["counterexample"] is None:
                raise RuntimeError(f"witness mutation {index} lacks a counterexample")
            mutation_dir = out / "confirmed-negative-mutations"
            mutation_dir.mkdir(exist_ok=True)
            shutil.copyfile(path, mutation_dir / path.name)

        for number, relative in enumerate(config["reflection_metamorphisms"]):
            original_path = ROOT / relative
            channels, comparators = load_transform_fixture(original_path)
            base, _ = runner.pair(f"reflection-base:{number}", "reflection-base", original_path, channels, None)
            reflected = [(channels - 1 - upper, channels - 1 - lower, layer) for lower, upper, layer in comparators]
            path = generated / f"reflection-{number:02d}.sortnet"
            path.write_bytes(candidate_bytes(channels, reflected, f"b1-reflection-{number}"))
            runner.pair(
                f"reflection:{number}", "reflection", path, channels, base["verdict"],
                details={"source_fixture": relative, "comparators": reflected},
            )

        random_config = config["random_differential"]
        rng = random.Random(random_config["seed"])
        for number in range(random_config["cases"]):
            channels = rng.randint(random_config["minimum_channels"], random_config["maximum_channels"])
            count = rng.randint(0, random_config["maximum_comparators"])
            comparators = []
            for _ in range(count):
                lower = rng.randrange(channels - 1)
                upper = rng.randrange(lower + 1, channels)
                comparators.append((lower, upper, None))
            path = generated / f"random-{number:03d}.sortnet"
            path.write_bytes(candidate_bytes(channels, comparators, f"b1-random-{number}"))
            runner.pair(
                f"random:{number:03d}", "random-differential", path, channels, None,
                details={"channels": channels, "comparators": comparators},
            )

        exhaustive = config["exhaustive_subset"]
        channels = exhaustive["channels"]
        choices = [(lower, upper, None) for lower in range(channels) for upper in range(lower + 1, channels)]
        exhaustive_count = 0
        exhaustive_accepts = 0
        for length in range(exhaustive["maximum_length"] + 1):
            for sequence in product(choices, repeat=length):
                path = generated / f"exhaustive-{exhaustive_count:03d}.sortnet"
                comparators = list(sequence)
                path.write_bytes(candidate_bytes(channels, comparators, f"b1-exhaustive-{exhaustive_count}"))
                result, _ = runner.pair(
                    f"exhaustive:{exhaustive_count:03d}", "exhaustive-subset", path, channels, None,
                    details={"comparators": comparators},
                )
                exhaustive_count += 1
                exhaustive_accepts += result["verdict"] == "ACCEPT"
        if exhaustive_count != exhaustive["candidate_count"]:
            raise RuntimeError(f"exhaustive candidate count mismatch: {exhaustive_count}")
        if exhaustive_accepts != exhaustive["expected_accept_count"]:
            raise RuntimeError(f"exhaustive accept count mismatch: {exhaustive_accepts}")

        results = runner.results
        category_counts = Counter(result["category"] for result in results)
        verdict_counts = Counter(result["verdict"] for result in results)
        summary = {
            "status": "PASS",
            "case_count": len(results),
            "category_counts": dict(sorted(category_counts.items())),
            "verdict_counts": dict(sorted(verdict_counts.items())),
            "public_witness_artifact_sha256": config["positive_fixtures"][0]["artifact_sha256"],
            "public_witness_candidate_checksum": config["positive_fixtures"][0]["candidate_checksum"],
            "public_witness_verifier_agreement": "ACCEPT",
            "exhaustive_candidate_count": exhaustive_count,
            "exhaustive_accept_count": exhaustive_accepts,
            "random_seed": random_config["seed"],
            "random_case_count": random_config["cases"],
            "mutation_indices_independently_rejected": config["witness_mutations"]["removed_zero_based_indices"],
        }
        write_json(out / "agreement-summary.json", summary)
        status = "PASS"
        log_lines.append(
            f"PASS: both independent verifiers agreed on {len(results)} cases; public 45-comparator witness accepted."
        )
        log_lines.append(
            f"PASS: exhaustive n=3 subset={exhaustive_count}, accepts={exhaustive_accepts}; random cases={random_config['cases']}."
        )
    except TimeoutError as exc:
        status = "TIMEOUT"
        error = str(exc)
        log_lines.append(f"TIMEOUT: {error}")
    except Exception as exc:
        status = "FAIL"
        error = str(exc)
        log_lines.append(f"FAIL: {error}")

    if not results and "runner" in locals():
        results = runner.results
    write_json(out / "case-results.json", results)
    write_json(out / "config-snapshot.json", config_snapshot)
    write_json(out / "verifier-build.json", build_record)
    host = host_record()
    self_usage = resource.getrusage(resource.RUSAGE_SELF)
    child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    multiplier = 1 if sys.platform == "darwin" else 1024
    peak_rss = max(int(self_usage.ru_maxrss * multiplier), int(child_usage.ru_maxrss * multiplier))
    if status == "PASS" and peak_rss > config["limits"]["peak_memory_bytes"]:
        status = "FAIL"
        error = f"peak RSS {peak_rss} exceeds B1 cap"
        log_lines.append(f"FAIL: {error}")
    ended = datetime.now(timezone.utc)
    manifest = {
        "schema_version": "s13-evidence-manifest/v1",
        "run_id": run_id,
        "gate": "B1",
        "source_commit": run_text(["git", "rev-parse", "HEAD"]),
        "dirty_at_start": False,
        "command": [sys.executable, "tools/b1_gate.py"],
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "wall_seconds": round(time.perf_counter() - started_perf, 6),
        "cpu_seconds": round(time.process_time() - started_cpu + child_usage.ru_utime + child_usage.ru_stime, 6),
        "peak_rss_bytes": peak_rss,
        "threads": 1,
        "host": host,
        "config_sha256": config_hash,
        "status": status,
    }
    if error is not None:
        manifest["error"] = error
    write_json(out / "manifest.json", manifest)
    (out / "command.txt").write_text(f"{sys.executable} tools/b1_gate.py\n", encoding="utf-8")
    (out / "stdout.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    (out / "stderr.txt").write_text("\n".join(stderr_lines) + ("\n" if stderr_lines else ""), encoding="utf-8")
    write_checksums(out)
    for line in log_lines:
        print(line)
    print(f"evidence: {out.relative_to(ROOT)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
