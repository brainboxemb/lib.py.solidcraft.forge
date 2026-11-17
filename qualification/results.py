#!/usr/bin/env python3
"""Collect qualification outputs into stable per-case JSON results.

This module does not run CAD operations itself. It normalizes evidence already
produced by the Python tests and native SolidCraft qualification workflow so
Pages, CI summaries and future tooling can consume the same result contract.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qualification.cases import QUALIFICATION_CASES
from qualification.native_cases import mutation_spec


SCHEMA_VERSION = 4


def _read_tsv(path: Path, key: str = "case") -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        return {
            row[key]: row
            for row in csv.DictReader(handle, delimiter="\t")
            if row.get(key)
        }


def _parse_tests(row: dict[str, str] | None) -> list[dict[str, str]]:
    if not row or not row.get("tests"):
        return []
    try:
        value = json.loads(row["tests"])
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    if not all(
        isinstance(target, dict)
        and isinstance(target.get("file"), str)
        and target["file"]
        and isinstance(target.get("test"), str)
        and target["test"]
        for target in value
    ):
        return []
    return value


def _copy_case_evidence(
    qualification_dir: Path,
    case_dir: Path,
    level: str,
    row: dict[str, str] | None,
) -> str | None:
    if not row or not row.get("evidence"):
        return None
    source = qualification_dir / row["evidence"]
    if not source.is_file() or source.stat().st_size == 0:
        return None
    name = f"{level}-case-evidence.txt"
    case_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, case_dir / name)
    return name


def _case_status(
    row: dict[str, str] | None,
    evidence_name: str | None,
    tests: list[dict[str, str]],
    *,
    extra_status: str | None = None,
) -> str:
    if not row:
        return "missing"
    if row.get("status") == "FAIL" or extra_status == "FAIL":
        return "fail"
    if (
        row.get("status") != "PASS"
        or evidence_name is None
        or not tests
    ):
        return "missing"
    if extra_status is not None and extra_status != "PASS":
        return "missing"
    return "pass"


def _existing_names(case_dir: Path, patterns: tuple[str, ...]) -> list[str]:
    names: set[str] = set()
    for pattern in patterns:
        names.update(path.name for path in case_dir.glob(pattern) if path.is_file() and path.stat().st_size)
    return sorted(names)


def collect(
    qualification_dir: Path,
    native_root: Path,
    source_commit: str,
    forge_version: str,
    solidcraft_version: str,
    qualified_at: str,
) -> dict:
    q1_rows = _read_tsv(qualification_dir / "q1-case-evidence.tsv")
    q2_case_rows = _read_tsv(qualification_dir / "q2-case-evidence.tsv")
    q2_rows = _read_tsv(qualification_dir / "q2-command-contract.tsv")
    native_rows = _read_tsv(qualification_dir / "q3-q4-q6-native.tsv")
    mutation_rows = _read_tsv(qualification_dir / "q5-parametric-mutation.tsv")
    validation_rows = _read_tsv(qualification_dir / "native-validation.tsv")
    visual_rows = _read_tsv(qualification_dir / "visual-validation.tsv")

    aggregate = {
        "schema_version": SCHEMA_VERSION,
        "source_commit": source_commit,
        "forge_version": forge_version,
        "solidcraft_version": solidcraft_version,
        "qualified_at": qualified_at,
        "cases": {},
    }

    for case in QUALIFICATION_CASES:
        slug = case["slug"]
        case_dir = native_root / slug
        case_dir.mkdir(parents=True, exist_ok=True)

        q1 = q1_rows.get(slug)
        q2_case = q2_case_rows.get(slug)
        q2 = q2_rows.get(slug, {})
        native = native_rows.get(slug, {})
        mutation = mutation_rows.get(slug)
        validation = validation_rows.get(slug, {})
        visual = visual_rows.get(slug, {})
        visual_detail_path = case_dir / "visual-validation.json"
        visual_detail = (
            json.loads(visual_detail_path.read_text(encoding="utf-8"))
            if visual_detail_path.is_file()
            else {}
        )
        mutation_required = bool(case.get("q5_required", False))

        images = _existing_names(case_dir, ("*.png",))
        images.sort(key=lambda name: (name != "model.png", name))
        native_files = _existing_names(
            case_dir,
            (
                "results*.json",
                "measurements*.json",
                "change-*.json",
                "parameters*.json",
                "joint-*.json",
                "model.json",
                "model*.sc",
                "model*.step",
                "export-*.json",
                "validation.json",
                "visual-validation.json",
                "visual-diff-*.png",
            ),
        )

        q1_evidence = _copy_case_evidence(
            qualification_dir,
            case_dir,
            "q1",
            q1,
        )
        q2_evidence = _copy_case_evidence(
            qualification_dir,
            case_dir,
            "q2",
            q2_case,
        )
        for evidence_name in (q1_evidence, q2_evidence):
            if evidence_name and evidence_name not in native_files:
                native_files.append(evidence_name)
        native_files.sort()

        q1_tests = _parse_tests(q1)
        q2_tests = _parse_tests(q2_case)
        q1_status = _case_status(
            q1,
            q1_evidence,
            q1_tests,
        )
        q2_status = _case_status(
            q2_case,
            q2_evidence,
            q2_tests,
            extra_status=q2.get("status"),
        )
        q3_pass = native.get("build") == "PASS" and native.get("eval") == "PASS"

        q4_status = validation.get("q4", "MISSING").lower()
        if q4_status not in {"pass", "fail", "review"}:
            q4_status = "missing"

        if mutation_required:
            q5_status = validation.get("q5", "MISSING").lower()
            if q5_status not in {"pass", "fail", "review"}:
                q5_status = "missing"
        else:
            q5_status = "not-required"

        q6_status = visual.get("status", "MISSING").lower()
        visual_detail_status = str(
            visual_detail.get("status", "missing")
        ).lower()
        regression_status = str(
            visual_detail.get("regression", {}).get("status", "missing")
        ).lower()
        expected_shape_status = str(
            visual_detail.get("expected_shape", {}).get("status", "missing")
        ).lower()
        required_views = visual_detail.get(
            "expected_shape",
            {},
        ).get("required_views", [])
        if (
            q6_status not in {"pass", "fail", "review"}
            or visual_detail_status != q6_status
        ):
            q6_status = "missing"
        elif (
            q6_status == "pass"
            and (
                regression_status != "pass"
                or expected_shape_status != "pass"
            )
        ):
            q6_status = "missing"

        levels = {
            "q1": {
                "status": q1_status,
                "tests": q1_tests,
                "evidence": [q1_evidence] if q1_evidence else [],
            },
            "q2": {
                "status": q2_status,
                "tests": q2_tests,
                "commands": (
                    int(q2["commands"])
                    if q2.get("commands", "").isdigit()
                    else None
                ),
                "evidence": [q2_evidence] if q2_evidence else [],
            },
            "q3": {
                "status": "pass" if q3_pass else "missing",
                "evidence": [name for name in native_files if name in {"results.json", "model.sc", "model.step"}],
            },
            "q4": {
                "status": q4_status,
                "evidence": [
                    name for name in native_files
                    if name.startswith("measurements")
                    or name.startswith("joint-")
                    or name == "results-bom.json"
                    or name == "validation.json"
                ],
            },
            "q5": {
                "status": q5_status,
                "required": mutation_required,
                "reason": case["mutation"],
                "mutation": mutation.get("mutation") if mutation else None,
                "evidence": (
                    [
                        name
                        for name in native_files
                        if name in {
                            mutation_spec(slug)["save"],
                            mutation_spec(slug)["measurements"],
                        }
                    ]
                    if mutation_required else []
                ),
            },
            "q6": {
                "status": q6_status,
                "regression_status": regression_status,
                "expected_shape_status": expected_shape_status,
                "required_views": required_views,
                "images": images,
                "evidence": [
                    name
                    for name in native_files
                    if name == "visual-validation.json"
                    or name.startswith("visual-diff-")
                    or name.startswith("goal-")
                    or name.startswith("overlay-")
                ],
            },
        }

        blocked_reason = case.get("blocked_reason")
        if blocked_reason:
            for key in ("q2", "q3", "q4", "q5", "q6"):
                levels[key]["status"] = "blocked"

        required_statuses = [
            level["status"]
            for key, level in levels.items()
            if key != "q5" or mutation_required
        ]
        if blocked_reason:
            overall = "blocked"
        elif "fail" in required_statuses:
            overall = "fail"
        elif "missing" in required_statuses:
            overall = "incomplete"
        elif "review" in required_statuses:
            overall = "review"
        else:
            overall = "pass"

        result = {
            "schema_version": SCHEMA_VERSION,
            "case": slug,
            "title": case["title"],
            "source_commit": source_commit,
            "forge_version": forge_version,
            "solidcraft_version": solidcraft_version,
            "qualified_at": qualified_at,
            "status": overall,
            "blocked_reason": blocked_reason,
            "levels": levels,
            "evidence": {
                "native_files": native_files,
                "images": images,
            },
        }
        aggregate["cases"][slug] = result

        (case_dir / "qualification-result.json").write_text(
            json.dumps(result, indent=2) + "\n",
            encoding="utf-8",
        )

    qualification_dir.mkdir(parents=True, exist_ok=True)
    (qualification_dir / "results.json").write_text(
        json.dumps(aggregate, indent=2) + "\n",
        encoding="utf-8",
    )
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qualification-dir", type=Path, required=True)
    parser.add_argument("--native-root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--forge-version", required=True)
    parser.add_argument("--solidcraft-version", required=True)
    parser.add_argument("--qualified-at", required=True)
    args = parser.parse_args()

    aggregate = collect(
        args.qualification_dir,
        args.native_root,
        args.source_sha,
        args.forge_version,
        args.solidcraft_version,
        args.qualified_at,
    )
    counts = {}
    for result in aggregate["cases"].values():
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    print(
        f"Collected {len(aggregate['cases'])} qualification case results: "
        + ", ".join(f"{key}={value}" for key, value in sorted(counts.items()))
    )
    # FAIL/REVIEW are report data. The workflow gates after artifacts and Pages
    # have been generated so failed qualification remains inspectable.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
