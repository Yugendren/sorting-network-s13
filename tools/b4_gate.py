#!/usr/bin/env python3
"""Aggregate the immutable B0--B3 evidence, issue one verdict, and stop."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import resource
import shutil
import subprocess
import sys
import time
from typing import Any


ROOT = Path("/Users/yugendren/experiments/sorting_network_s13")
CONFIG_PATH = ROOT / "config/frozen/b4-aggregate.json"
BUDGETS_PATH = ROOT / "config/frozen/budgets.json"
SOURCES_PATH = ROOT / "config/frozen/sources.json"
TERMINAL_VERDICTS = ("BASELINE_READY", "CONDITIONAL", "BLOCKED", "INVALID", "STALE_TARGET")


class GateFailure(RuntimeError):
    def __init__(self, message: str, status: str = "INVALID") -> None:
        super().__init__(message)
        self.status = status


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_checksums(directory: Path) -> None:
    paths = sorted(path for path in directory.rglob("*") if path.is_file() and path.name != "checksums.sha256")
    lines = [f"{sha256(path)}  {path.relative_to(directory).as_posix()}" for path in paths]
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


def aggregate_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(dict.fromkeys(paths)):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256(path)))
        digest.update(b"\n")
    return digest.hexdigest()


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


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GateFailure(message)


def basic_preflight() -> tuple[dict[str, Any], str]:
    if Path.cwd().resolve() != ROOT:
        raise RuntimeError(f"cwd must be exactly {ROOT}")
    if run_text(["git", "branch", "--show-current"]) != "goal/s13-baseline":
        raise RuntimeError("wrong branch")
    dirty = run_text(["git", "status", "--porcelain", "--untracked-files=all"])
    if dirty:
        raise RuntimeError(f"scored configuration is dirty:\n{dirty}")
    existing_reports = sorted((ROOT / "evidence/b4").glob("*/baseline-report.md"))
    if existing_reports:
        raise RuntimeError(f"terminal report already exists at {existing_reports[0].relative_to(ROOT)}; do not rerun B4")
    config = load_json(CONFIG_PATH)
    checked = subprocess.run(
        [sys.executable, "tools/evidence_check.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if checked.returncode != 0:
        raise RuntimeError(f"evidence prerequisite failed:\n{checked.stdout}")
    return config, checked.stdout


def validate_prerequisites(config: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    require(config.get("schema_version") == "s13-b4-aggregate/v1", "wrong B4 config schema")
    require([item["gate"] for item in config["prerequisites"]] == ["B0", "B1", "B2", "B3"], "B4 prerequisites must be B0--B3 in order")
    for item in config["prerequisites"]:
        run_dir = ROOT / item["run_dir"]
        manifest_path = run_dir / "manifest.json"
        checksums_path = run_dir / "checksums.sha256"
        require(manifest_path.is_file() and checksums_path.is_file(), f"missing prerequisite files for {item['gate']}")
        require(sha256(manifest_path) == item["manifest_sha256"], f"{item['gate']} manifest identity changed")
        require(sha256(checksums_path) == item["checksums_sha256"], f"{item['gate']} inventory identity changed")
        manifest = load_json(manifest_path)
        require(manifest["gate"] == item["gate"], f"{item['gate']} manifest gate mismatch")
        require(manifest["status"] == "PASS", f"{item['gate']} prerequisite is not PASS")
        require(manifest["dirty_at_start"] is False, f"{item['gate']} prerequisite began dirty")
        records.append(
            {
                **item,
                "run_id": manifest["run_id"],
                "source_commit": manifest["source_commit"],
                "status": manifest["status"],
                "wall_seconds": manifest["wall_seconds"],
                "cpu_seconds": manifest["cpu_seconds"],
                "peak_rss_bytes": manifest["peak_rss_bytes"],
                "threads": manifest["threads"],
            }
        )
    return records


def normalized_baseline_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "seed": item["seed"],
            "best_size": item.get("best_size"),
            "evaluations": item.get("evaluations"),
            "status": item["status"],
            "wall_seconds": item["resource"].get("wall_seconds"),
            "cpu_seconds": item["resource"].get("cpu_seconds"),
            "peak_rss_bytes": item["resource"].get("peak_rss_bytes"),
            "verifier_a": item.get("verification", {}).get("verifier_a"),
            "verifier_b": item.get("verification", {}).get("verifier_b"),
            "artifact_sha256": item.get("verification", {}).get("artifact_sha256"),
        }
        for item in results
    ]


def validate_baseline_rows(name: str, rows: list[dict[str, Any]], seeds: list[int]) -> None:
    require([row["seed"] for row in rows] == seeds, f"B2 {name} seed coverage mismatch")
    require(all(row["status"] == "PASS" for row in rows), f"B2 {name} contains a non-PASS seed")
    require(all(row["best_size"] is not None for row in rows), f"B2 {name} contains an absent candidate")
    require(all(row["best_size"] >= 45 for row in rows), f"B2 {name} contains an unexpected frontier candidate")
    require(all(row["verifier_a"] == row["verifier_b"] == "ACCEPT" for row in rows), f"B2 {name} verifier disagreement")


def collect_scored_runs() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for gate in ("b0", "b1", "b2", "b3"):
        for path in sorted((ROOT / "evidence" / gate).glob("*/manifest.json")):
            manifest = load_json(path)
            rows.append(
                {
                    "run_id": manifest["run_id"],
                    "gate": manifest["gate"],
                    "status": manifest["status"],
                    "source_commit": manifest["source_commit"],
                    "wall_seconds": manifest["wall_seconds"],
                    "cpu_seconds": manifest["cpu_seconds"],
                    "peak_rss_bytes": manifest["peak_rss_bytes"],
                    "threads": manifest["threads"],
                    "error": manifest.get("error"),
                    "manifest_path": path.relative_to(ROOT).as_posix(),
                }
            )
    return rows


def collect_report_data(config: dict[str, Any]) -> dict[str, Any]:
    accepted = validate_prerequisites(config)
    expected = config["expected"]
    b0_dir = ROOT / config["prerequisites"][0]["run_dir"]
    b1_dir = ROOT / config["prerequisites"][1]["run_dir"]
    b2_dir = ROOT / config["prerequisites"][2]["run_dir"]
    b3_dir = ROOT / config["prerequisites"][3]["run_dir"]

    b0_protocol = load_json(b0_dir / "protocol-verification.json")
    b0_authority = load_json(b0_dir / "authority-verification.json")
    b0_sources = load_json(b0_dir / "source-verification.json")
    require(b0_protocol["aggregate_sha256"] == expected["b0_protocol_aggregate_sha256"], "B0 protocol aggregate mismatch")
    authority_by_path = {item["path"]: item["sha256"] for item in b0_authority}
    require(authority_by_path.get("PROJECT_CONTRACT.md") == expected["contract_sha256"], "contract identity mismatch")
    require(all(item["status"] == "ARTIFACT_VERIFIED" for item in b0_sources), "B0 source verification is incomplete")
    status_audit = (ROOT / "docs/current-status-audit.md").read_text(encoding="utf-8")
    require("44 <= S(13) <= 45" in status_audit and "target is not stale" in status_audit, "B0 live-status conclusion mismatch")

    b1_agreement = load_json(b1_dir / "agreement-summary.json")
    b1_a = load_json(b1_dir / "public-verifier-a.json")
    b1_b = load_json(b1_dir / "public-verifier-b.json")
    b1_expected = expected["b1"]
    require(b1_agreement["status"] == "PASS" and b1_agreement["case_count"] == b1_expected["case_count"], "B1 agreement summary mismatch")
    require(b1_agreement["public_witness_artifact_sha256"] == b1_expected["public_witness_artifact_sha256"], "B1 witness identity mismatch")
    require(b1_agreement["mutation_indices_independently_rejected"] == b1_expected["mutation_indices"], "B1 mutation controls mismatch")
    for report in (b1_a, b1_b):
        require(report["verdict"] == "ACCEPT", "a B1 verifier rejected the public witness")
        require(report["channels"] == b1_expected["channels"] and report["comparators"] == b1_expected["comparators"], "B1 public witness shape mismatch")
        require(report["artifact_sha256"] == b1_expected["public_witness_artifact_sha256"], "B1 verifier artifact mismatch")
    for field in ("artifact_sha256", "candidate_checksum", "channels", "comparators", "counterexample"):
        require(b1_a.get(field) == b1_b.get(field), f"B1 verifier disagreement on {field}")

    b2_summary = load_json(b2_dir / "summary.json")
    b2_raw = load_json(b2_dir / "seed-results.json")
    b2_expected = expected["b2"]
    require(b2_summary["status"] == "PASS", "B2 summary is not PASS")
    require(b2_summary["senso_acceptance_count"] == b2_expected["senso_acceptance_count"], "B2 SENSO acceptance count mismatch")
    require(b2_summary["baselines"]["senso"]["size_distribution"] == b2_expected["senso_size_distribution"], "B2 SENSO size distribution mismatch")
    require(b2_summary["baselines"]["greedy"]["best_size"] == b2_expected["greedy_best_size"], "B2 greedy best mismatch")
    require(b2_summary["baselines"]["random"]["best_size"] == b2_expected["random_best_size"], "B2 random best mismatch")
    b2_rows: dict[str, list[dict[str, Any]]] = {}
    for name in ("senso", "greedy", "random"):
        rows = normalized_baseline_rows(b2_raw[name])
        validate_baseline_rows(name, rows, b2_expected["seeds"])
        b2_rows[name] = rows
    require(min(row["best_size"] for row in b2_rows["senso"]) == b2_expected["senso_best_size"], "B2 SENSO best mismatch")
    require(sum(row["best_size"] == 45 for row in b2_rows["senso"]) == 1, "B2 must contain exactly one 45-comparator SENSO result")
    require(next(row for row in b2_rows["senso"] if row["seed"] == 18)["best_size"] == 45, "B2 seed 18 is not the accepted baseline")
    require(all(row["evaluations"] == b2_expected["expected_senso_evaluations_per_seed"] for row in b2_rows["senso"]), "B2 SENSO evaluation count mismatch")

    n9 = load_json(b3_dir / "n9-workflow/result.json")
    corruption = load_json(b3_dir / "corruption-rejection/result.json")
    n11 = load_json(b3_dir / "n11-replay/result.json")
    b3_summary = load_json(b3_dir / "summary.json")
    b3_expected = expected["b3"]
    require(b3_summary["status"] == "PASS", "B3 summary is not PASS")
    require(n9["status"] == "PASS" and n9["checker_result"] == b3_expected["n9_result"], "B3 n=9 result mismatch")
    require(n9["proof_sha256"] == b3_expected["n9_proof_sha256"], "B3 n=9 proof identity mismatch")
    require(corruption["status"] == "PASS" and corruption["checker_result"] is b3_expected["corruption_result"] and corruption["safe_rejection"] is True, "B3 corruption control mismatch")
    require(n11["status"] == "PASS" and n11["checker_result"] == b3_expected["n11_result"], "B3 n=11 result mismatch")
    require(n11["certificate_size_bytes"] == b3_expected["certificate_size_bytes"], "B3 certificate size mismatch")
    require(n11["certificate_sha256_before"] == n11["certificate_sha256_after"] == b3_expected["certificate_sha256"], "B3 certificate hash mismatch")
    toolchain = load_json(b3_dir / "toolchain-build-manifest.json")
    certificate_cache = load_json(b3_dir / "certificate-cache-manifest.json")
    require(toolchain["status"] == "PASS" and len(toolchain["portability_patches"]) == 2, "B3 toolchain identity mismatch")
    require(certificate_cache["status"] == "PASS" and certificate_cache["uncompressed_sha256"] == b3_expected["certificate_sha256"], "B3 certificate cache mismatch")

    runs = collect_scored_runs()
    require(len(runs) == expected["scored_run_count_through_b3"], "preserved scored-run count mismatch")
    budgets = load_json(BUDGETS_PATH)
    total_wall = sum(float(row["wall_seconds"]) for row in runs)
    require(total_wall < budgets["total_after_setup"]["wall_seconds"], "total scored wall budget was exceeded")

    return {
        "accepted_prerequisites": accepted,
        "sources": load_json(SOURCES_PATH)["sources"],
        "b0": {
            "protocol": b0_protocol,
            "authority": b0_authority,
            "source_verification": b0_sources,
        },
        "b1": {"agreement": b1_agreement, "verifier_a": b1_a, "verifier_b": b1_b},
        "b2": {"summary": b2_summary, "rows": b2_rows},
        "b3": {
            "summary": b3_summary,
            "n9": n9,
            "n9_resource": load_json(b3_dir / "n9-workflow/resource.json"),
            "corruption": corruption,
            "corruption_resource": load_json(b3_dir / "corruption-rejection/checker/resource.json"),
            "n11": n11,
            "n11_resource": load_json(b3_dir / "n11-replay/resource.json"),
            "toolchain": toolchain,
            "certificate_cache": certificate_cache,
        },
        "setup": {
            "senso": load_json(b2_dir / "senso-build-manifest.json"),
            "harder": toolchain,
            "certificate": certificate_cache,
        },
        "scored_runs": runs,
        "total_scored_manifest_wall_seconds": round(total_wall, 6),
        "wall_limit_seconds": budgets["total_after_setup"]["wall_seconds"],
    }


def markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def mib(value: int | float | None) -> str:
    return "--" if value is None else f"{float(value) / (1024 * 1024):.2f}"


def seconds(value: int | float | None) -> str:
    return "--" if value is None else f"{float(value):.6f}"


def source_pin(source: dict[str, Any]) -> str:
    parts: list[str] = []
    if source.get("doi"):
        parts.append(f"DOI `{source['doi']}`")
    if source.get("commit"):
        parts.append(f"commit `{source['commit']}`")
    if source.get("sha256"):
        parts.append(f"SHA-256 `{source['sha256']}`")
    if source.get("uncompressed_sha256"):
        parts.append(f"uncompressed SHA-256 `{source['uncompressed_sha256']}`")
    if source.get("compressed_md5"):
        parts.append(f"compressed MD5 `{source['compressed_md5']}`")
    return "; ".join(parts)


def seed_table(title: str, rows: list[dict[str, Any]]) -> list[str]:
    lines = [f"### {title}", "", "| Seed | Size | Evaluations | Wall s | CPU s | Peak MiB | A | B |", "|---:|---:|---:|---:|---:|---:|---|---|"]
    for row in rows:
        lines.append(
            f"| {row['seed']} | {row['best_size']} | {row['evaluations']} | {seconds(row['wall_seconds'])} | "
            f"{seconds(row['cpu_seconds'])} | {mib(row['peak_rss_bytes'])} | {row['verifier_a']} | {row['verifier_b']} |"
        )
    lines.append("")
    return lines


def render_report(data: dict[str, Any], config: dict[str, Any], run_id: str, source_commit: str) -> str:
    expected = config["expected"]
    b1 = data["b1"]["agreement"]
    b2 = data["b2"]
    b3 = data["b3"]
    host = load_json(ROOT / config["prerequisites"][3]["run_dir"] / "manifest.json")["host"]
    source_states = {
        "dobbelaere-catalog": "ARTIFACT_VERIFIED snapshot; witness correctness ARTIFACT_VERIFIED by B1",
        "harder-paper-v3": "ARTIFACT_VERIFIED bytes; claims PUBLISHED",
        "sortnetopt": "ARTIFACT_VERIFIED source; n=9 workflow LOCALLY_REPRODUCED",
        "harder-n11-certificate": "ARTIFACT_VERIFIED identity; replay LOCALLY_REPRODUCED",
        "valsalam-miikkulainen-paper": "ARTIFACT_VERIFIED bytes; method PUBLISHED",
        "symmetry-1.1": "ARTIFACT_VERIFIED archive; frozen-seed runs LOCALLY_REPRODUCED",
        "wang-n28d13-context": "PUBLISHED optional context; not a gate input",
    }
    lines = [
        "# Mericanii S(13) baseline report",
        "",
        f"B4 run: `{run_id}`. Source commit: `{source_commit}`. Evidence date: 2026-08-15.",
        "",
        "## Scope and result",
        "",
        "This report closes the contracted B0--B4 baseline only. The objective is minimum comparator count, not minimum depth. "
        "The B0 maintained snapshot states `44 <= S(13) <= 45`; its depth-9 entry is context only. No 44-comparator search, "
        "nonexistence attempt, learned method, GPU work, publication, or external claim was performed.",
        "",
        "All four prerequisite PASS manifests retain their frozen identities, all immutable inventories validate, the public "
        "45-comparator witness passes both independent verifiers, a frozen SENSO-style seed locally reproduces size 45, and "
        "the official exact/certificate workflow returns the required n=9 and n=11 lower bounds.",
        "",
        "## Truth-label key",
        "",
        "- `PUBLISHED`: stated by a pinned source.",
        "- `ARTIFACT_VERIFIED`: a pinned local artifact or witness was independently checked.",
        "- `LOCALLY_REPRODUCED`: regenerated or replayed locally from pinned inputs.",
        "- `MEASURED`: observed in this execution, without a mathematical inference beyond the observation.",
        "- `ASSUMED`: frozen protocol choice not supplied by the historical source.",
        "- `UNKNOWN`: not established by the available evidence.",
        "",
        "## Source and artifact ledger",
        "",
        "| ID | Role | Primary source and pin | Evidence state | License record |",
        "|---|---|---|---|---|",
    ]
    for source in data["sources"]:
        lines.append(
            f"| `{source['id']}` | {markdown_cell(source['role'])} | [{source['url']}]({source['url']}); "
            f"{markdown_cell(source_pin(source))} | {source_states[source['id']]} | {markdown_cell(source['license'])} |"
        )
    lines.extend(["", "## Gate traceability and preserved attempts", "", "Accepted prerequisite identities:", "", "| Gate | Run | Source commit | Manifest SHA-256 | Inventory SHA-256 |", "|---|---|---|---|---|"])
    for item in data["accepted_prerequisites"]:
        lines.append(
            f"| {item['gate']} | `{item['run_id']}` | `{item['source_commit']}` | `{item['manifest_sha256']}` | `{item['checksums_sha256']}` |"
        )
    lines.extend(["", "All scored attempts, including superseded and failed runs:", "", "| Run | Gate | Status | Wall s | CPU s | Peak MiB | Threads | Preserved outcome |", "|---|---|---|---:|---:|---:|---:|---|"])
    for row in data["scored_runs"]:
        outcome = row["error"] or "accepted or superseded PASS evidence"
        lines.append(
            f"| `{row['run_id']}` | {row['gate']} | {row['status']} | {seconds(row['wall_seconds'])} | "
            f"{seconds(row['cpu_seconds'])} | {mib(row['peak_rss_bytes'])} | {row['threads']} | {markdown_cell(outcome)} |"
        )
    lines.extend(
        [
            "",
            "The earlier B3 direct-import failure occurred before gate initialization and created no scored scientific process; "
            "it remains documented in `docs/b3-setup-audit.md` rather than being converted into evidence after the fact.",
            "",
            "## B1 independent witness verification",
            "",
            f"`ARTIFACT_VERIFIED`: Python direct zero-one enumeration and an independently implemented Go bit-parallel checker "
            f"both accepted the same 13-input, 45-comparator public artifact `{b1['public_witness_artifact_sha256']}`. "
            f"They agreed on all {b1['case_count']} cases.",
            "",
            "| Check family | Count/result |",
            "|---|---|",
        ]
    )
    for name, count in b1["category_counts"].items():
        lines.append(f"| `{name}` | {count} |")
    lines.extend(
        [
            f"| Public witness | both `ACCEPT`; candidate checksum `{b1['public_witness_candidate_checksum']}` |",
            f"| Comparator-removal controls | indices {', '.join(str(item) for item in b1['mutation_indices_independently_rejected'])} independently rejected |",
            f"| Case-result totals | accepted={b1['verdict_counts']['ACCEPT']}, rejected={b1['verdict_counts']['INVALID']}, "
            f"malformed={b1['verdict_counts']['MALFORMED']} |",
            "",
            "The verifiers share only the candidate schema and fixtures. They do not share parsing, execution, sortedness, or counterexample logic.",
            "",
            "## B2 constructive and transparent baselines",
            "",
            "`LOCALLY_REPRODUCED`: every listed candidate was accepted by both B1 verifiers. `MEASURED`: sizes, evaluations, "
            "wall time, CPU, and memory are local observations. Seeds are frozen `ASSUMED` replacements because the historical seeds "
            "are `UNKNOWN`; the legacy variant-2 probability mapping is also `ASSUMED`.",
            "",
            "| Baseline | Best | Size distribution | Evaluations | Wall s | CPU s | Peak MiB |",
            "|---|---:|---|---:|---:|---:|---:|",
        ]
    )
    for name in ("senso", "greedy", "random"):
        summary = b2["summary"]["baselines"][name]
        distribution = ", ".join(f"{key}:{value}" for key, value in summary["size_distribution"].items())
        lines.append(
            f"| {name} | {summary['best_size']} | {distribution} | {summary['total_evaluations']} | "
            f"{seconds(summary['total_wall_seconds'])} | {seconds(summary['total_cpu_seconds'])} | {mib(summary['peak_rss_bytes'])} |"
        )
    lines.extend([""])
    lines.extend(seed_table("Frozen 20-seed SENSO-style batch", b2["rows"]["senso"]))
    lines.extend(seed_table("Transparent greedy initialization baseline", b2["rows"]["greedy"]))
    lines.extend(seed_table("Transparent uniform-random baseline", b2["rows"]["random"]))
    lines.extend(
        [
            "Seed 18 is the sole SENSO-style size-45 result. The distribution is 45:1, 46:16, 47:3; no baseline returned a candidate below 45.",
            "",
            "## B3 exact workflow and certificate replay",
            "",
            f"- `LOCALLY_REPRODUCED`: the official n=9 search-and-verify workflow returned `{b3['n9']['checker_output_line']}` and "
            f"generated proof SHA-256 `{b3['n9']['proof_sha256']}` ({b3['n9']['proof_size_bytes']} bytes; "
            f"{b3['n9']['generated_artifact_count']} generated artifacts). This establishes only `S(9) >= 25` locally.",
            f"- `LOCALLY_REPRODUCED`: changing the parseable n=9 proof's root-bound byte returned `{b3['corruption']['checker_output_line']}`, "
            "providing the required negative control.",
            f"- `ARTIFACT_VERIFIED`: the published n=11 certificate is {b3['n11']['certificate_size_bytes']} bytes and retained SHA-256 "
            f"`{b3['n11']['certificate_sha256_before']}` before and after replay.",
            f"- `LOCALLY_REPRODUCED`: the exact certificate returned `{b3['n11']['checker_output_line']}`. This establishes only "
            "`S(11) >= 35` locally; the equality and n=12 consequence remain separately labeled below.",
            "",
            "| B3 phase | Result | Wall s | CPU s | Peak MiB | Limit |",
            "|---|---|---:|---:|---:|---|",
            f"| n=9 official workflow | `{b3['n9']['checker_output_line']}` | {seconds(b3['n9_resource']['wall_seconds'])} | "
            f"{seconds(b3['n9_resource']['cpu_seconds'])} | {mib(b3['n9_resource']['peak_rss_bytes'])} | 600 s / 1 GiB |",
            f"| corrupted-proof control | `{b3['corruption']['checker_output_line']}` | {seconds(b3['corruption_resource']['wall_seconds'])} | "
            f"{seconds(b3['corruption_resource']['cpu_seconds'])} | {mib(b3['corruption_resource']['peak_rss_bytes'])} | 120 s / 1 GiB |",
            f"| n=11 certificate replay | `{b3['n11']['checker_output_line']}` | {seconds(b3['n11_resource']['wall_seconds'])} | "
            f"{seconds(b3['n11_resource']['cpu_seconds'])} | {mib(b3['n11_resource']['peak_rss_bytes'])} | 14,400 s / 12 GiB |",
            "",
            "The pinned upstream is `jix/sortnetopt` commit `0b5d09c47446096f9e3a0812b35afc72b7f2a718`. Two hashed macOS "
            "portability patches affect diagnostic `/proc` logging and unverified large-file I/O only; the parser and formally checked core remain unchanged.",
            "",
            "## Hardware and resource accounting",
            "",
            f"`MEASURED`: Apple model `{host['model']}`, CPU `{host['cpu']}`, {host['logical_cores']} logical/{host['physical_cores']} physical cores, "
            f"{host['memory_bytes'] / (1024**3):.2f} GiB RAM, `{host['machine']}`, `{host['os']}`. Constructive runs used one thread per seed; "
            "the official exact pipeline used the host's ten cores. GPU and remote compute were prohibited and unused.",
            "",
            f"All ten B0--B3 scored manifests total {data['total_scored_manifest_wall_seconds']:.6f} wall seconds "
            f"({data['total_scored_manifest_wall_seconds'] / 60:.2f} minutes), below the {data['wall_limit_seconds']} second post-setup limit. "
            f"The largest measured process tree was {mib(max(row['peak_rss_bytes'] for row in data['scored_runs']))} MiB. "
            "B4 itself is report-only; its exact small resource record is in its manifest.",
            "",
            "| Setup item (excluded from post-setup scored total) | Status | Wall s | Identity |",
            "|---|---|---:|---|",
            f"| SENSO build/smoke | {data['setup']['senso']['status']} | {seconds(data['setup']['senso']['wall_seconds'])} | binary `{data['setup']['senso']['binary_sha256']}` |",
            f"| active Harder toolchain build | {data['setup']['harder']['status']} | {seconds(data['setup']['harder']['wall_seconds'])} | checker `{data['setup']['harder']['checker_binary']['sha256']}` |",
            f"| certificate fetch/decompression | {data['setup']['certificate']['status']} | {seconds(data['setup']['certificate']['wall_seconds'])} | uncompressed `{data['setup']['certificate']['uncompressed_sha256']}` |",
            "",
            "## Unreproduced claims and limits",
            "",
            "| Statement or artifact | Label | Why it is not locally established here |",
            "|---|---|---|",
            "| Exact minimum size of S(13) | `UNKNOWN` | The audited interval remains 44--45; both a size-44 search and a nonexistence attempt were prohibited. |",
            "| Historical SENSO run identity | `UNKNOWN` | Historical seeds were not published; this laboratory used explicit `ASSUMED` seeds and an audited mapping. |",
            "| `S(11)=35` equality | `PUBLISHED` | B3 replayed the lower-bound certificate but did not separately replay a matching construction. |",
            "| `S(12)=39` | `PUBLISHED` | This paper-derived consequence was not separately replayed with an n=12 certificate. |",
            "| Full n=11 certificate generation | `PUBLISHED` resource account | Explicitly prohibited; the reference required roughly 200 GiB RAM and 80 hours on a 48-thread EPYC host. |",
            "| Minimum depth 9 for 13 inputs | `PUBLISHED` context | Depth is not comparator count and is not this laboratory's optimization target. |",
            "| Optional modern n=28 construction context | `PUBLISHED` | Not a B0--B4 dependency and not executed. |",
            "",
            "An unsuccessful or timed-out run is nowhere used as a proof. The live-status audit is a dated snapshot and must be repeated before later work.",
            "",
            "## Strongest baseline to beat later",
            "",
            "The later comparator-count experiment, if separately authorized, must beat 45 comparators. That size is supported two ways: "
            "B1 independently verifies the public 45-comparator artifact, and B2 seed 18 locally regenerates a different dual-verified "
            "size-45 result. Improvement therefore means a valid 44-comparator witness accepted by both B1 verifiers. This report neither searches for nor claims one.",
            "",
            "## Exact next prerequisite",
            "",
            config["next_prerequisite"],
            "",
            "No later experimental contract was drafted or executed as part of B4.",
            "",
            "## Terminal verdict",
            "",
            f"`{config['terminal_verdict']}`",
            "",
        ]
    )
    return "\n".join(lines)


def validate_report(report: str, config: dict[str, Any]) -> None:
    for section in config["required_report_sections"]:
        require(f"## {section}" in report, f"report missing section: {section}")
    for label in config["required_truth_labels"]:
        require(label in report, f"report missing truth label: {label}")
    verdict_count = sum(report.count(verdict) for verdict in TERMINAL_VERDICTS)
    require(verdict_count == 1, f"report must contain exactly one terminal verdict token, found {verdict_count}")
    require(report.count(config["terminal_verdict"]) == 1, "report does not contain exactly one configured verdict")
    for seed in config["expected"]["b2"]["seeds"]:
        require(f"| {seed} |" in report, f"report does not expose seed {seed}")


def main() -> int:
    try:
        config, integrity_output = basic_preflight()
    except Exception as exc:
        print(f"B4 preflight failed: {exc}", file=sys.stderr)
        return 2

    started = datetime.now(timezone.utc)
    started_perf = time.perf_counter()
    started_cpu = time.process_time()
    run_id = started.strftime("b4-%Y%m%dT%H%M%SZ")
    out = ROOT / "evidence/b4" / run_id
    out.mkdir(parents=True, exist_ok=False)
    status = "FAIL"
    error: str | None = None
    config_hash = "0" * 64
    log_lines = ["B4 falsifiable gate: all frozen B0--B3 evidence and report requirements must pass; no novel experiment may run."]
    stderr_lines: list[str] = []
    summary: dict[str, Any] = {"status": "FAIL"}

    try:
        data = collect_report_data(config)
        frozen_paths = [
            CONFIG_PATH,
            BUDGETS_PATH,
            SOURCES_PATH,
            ROOT / "Makefile",
            ROOT / "docs/current-status-audit.md",
            ROOT / "docs/source-ledger.md",
            ROOT / "docs/trust-boundary.md",
            ROOT / "docs/b1-verification.md",
            ROOT / "docs/b2-execution.md",
            ROOT / "docs/b3-execution.md",
            ROOT / "docs/b3-setup-audit.md",
            ROOT / "docs/b4-aggregation.md",
            ROOT / "tools/b4_gate.py",
            ROOT / "tools/evidence_check.py",
            ROOT / "tests/test_b4_aggregate.py",
        ]
        for item in config["prerequisites"]:
            run_dir = ROOT / item["run_dir"]
            frozen_paths.extend([run_dir / "manifest.json", run_dir / "checksums.sha256"])
        config_hash = aggregate_hash(frozen_paths)
        write_json(
            out / "config-snapshot.json",
            {
                "aggregate_sha256": config_hash,
                "files": [
                    {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)}
                    for path in sorted(frozen_paths)
                ],
            },
        )
        shutil.copyfile(CONFIG_PATH, out / "frozen-b4-config.json")
        (out / "integrity-check.txt").write_text(integrity_output, encoding="utf-8")
        write_json(out / "prerequisite-snapshot.json", data["accepted_prerequisites"])
        write_json(out / "all-scored-runs.json", data["scored_runs"])
        write_json(out / "report-inputs.json", data)

        source_commit = run_text(["git", "rev-parse", "HEAD"])
        report = render_report(data, config, run_id, source_commit)
        validate_report(report, config)
        projected_total = data["total_scored_manifest_wall_seconds"] + (time.perf_counter() - started_perf)
        require(projected_total < data["wall_limit_seconds"], "B4 would exceed total scored wall budget")
        report_path = out / "baseline-report.md"
        report_path.write_text(report, encoding="utf-8")
        summary = {
            "status": "PASS",
            "report_path": report_path.relative_to(out).as_posix(),
            "report_sha256": sha256(report_path),
            "required_section_count": len(config["required_report_sections"]),
            "truth_labels_present": config["required_truth_labels"],
            "terminal_verdict_token_count": 1,
            "accepted_prerequisite_count": len(data["accepted_prerequisites"]),
            "preserved_scored_run_count_through_b3": len(data["scored_runs"]),
            "novel_experiment_started": False,
        }
        status = "PASS"
        log_lines.append(f"PASS: validated {len(data['accepted_prerequisites'])} accepted gates and {len(data['scored_runs'])} preserved scored runs.")
        log_lines.append(f"PASS: generated one complete terminal report with SHA-256 {summary['report_sha256']}.")
    except GateFailure as exc:
        status = exc.status
        error = str(exc)
        log_lines.append(f"{status}: {error}")
    except Exception as exc:
        status = "FAIL"
        error = str(exc)
        log_lines.append(f"FAIL: {error}")

    summary["status"] = status
    if error is not None:
        summary["error"] = error
        stderr_lines.append(error)
    write_json(out / "summary.json", summary)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    multiplier = 1 if sys.platform == "darwin" else 1024
    ended = datetime.now(timezone.utc)
    manifest: dict[str, Any] = {
        "schema_version": "s13-evidence-manifest/v1",
        "run_id": run_id,
        "gate": "B4",
        "source_commit": run_text(["git", "rev-parse", "HEAD"]),
        "dirty_at_start": False,
        "command": [sys.executable, "tools/b4_gate.py"],
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "wall_seconds": round(time.perf_counter() - started_perf, 6),
        "cpu_seconds": round(time.process_time() - started_cpu, 6),
        "peak_rss_bytes": int(usage.ru_maxrss * multiplier),
        "threads": 1,
        "host": host_record(),
        "config_sha256": config_hash,
        "status": status,
    }
    if error is not None:
        manifest["error"] = error
    write_json(out / "manifest.json", manifest)
    (out / "command.txt").write_text(f"{sys.executable} tools/b4_gate.py\n", encoding="utf-8")
    (out / "stdout.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    (out / "stderr.txt").write_text("\n".join(stderr_lines) + ("\n" if stderr_lines else ""), encoding="utf-8")
    write_checksums(out)
    for line in log_lines:
        print(line)
    print(f"evidence: {out.relative_to(ROOT)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
