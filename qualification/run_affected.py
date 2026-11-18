#!/usr/bin/env python3
"""Run the full staged qualification flow for selected Forge cases.

Global Q1/Q2 suites execute once. Each selected case then runs through the
shared qualification.case_runner stages. Individual stages can be rerun
separately with qualification/case_runner.py.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
SCPF_ROOT = ROOT / "scpf"
if str(SCPF_ROOT) not in sys.path:
    sys.path.insert(0, str(SCPF_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.case_runner import STAGES, run_case
from qualification.case_selection import (
    format_selection_help,
    parse_case_selection,
)
from qualification.native_cases import validate_runtime_metadata


def _run(command: list[str], *, cwd: Path = ROOT) -> float:
    started = time.perf_counter()
    subprocess.run(command, cwd=cwd, check=True)
    return time.perf_counter() - started


def _stage_state(out: Path, slug: str, stage: str) -> dict:
    index = STAGES.index(stage) + 1
    path = out / "stages" / slug / f"{index:02d}-{stage}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _aggregate_validation(out: Path, selected: tuple[str, ...]) -> None:
    qualification = out / "qualification"
    qualification.mkdir(parents=True, exist_ok=True)

    native_summary = {}
    visual_summary = {}
    native_rows = ["case\tq4\tq5\n"]
    visual_rows = ["case\tstatus\n"]

    for slug in selected:
        native = json.loads(
            (out / "native" / slug / "validation.json").read_text(
                encoding="utf-8"
            )
        )
        visual = json.loads(
            (out / "native" / slug / "visual-validation.json").read_text(
                encoding="utf-8"
            )
        )
        native_summary[slug] = native
        visual_summary[slug] = visual
        native_rows.append(
            f"{slug}\t{native['q4'].upper()}\t{native['q5'].upper()}\n"
        )
        visual_rows.append(f"{slug}\t{visual['status'].upper()}\n")

    (qualification / "native-validation.json").write_text(
        json.dumps(native_summary, indent=2) + "\n",
        encoding="utf-8",
    )
    (qualification / "native-validation.tsv").write_text(
        "".join(native_rows),
        encoding="utf-8",
    )
    (qualification / "visual-validation.json").write_text(
        json.dumps(visual_summary, indent=2) + "\n",
        encoding="utf-8",
    )
    (qualification / "visual-validation.tsv").write_text(
        "".join(visual_rows),
        encoding="utf-8",
    )


def _aggregate_case_evidence(
    out: Path,
    selected: tuple[str, ...],
    level: str,
) -> None:
    rows = ["case\tstatus\tevidence\n"]
    for slug in selected:
        state = _stage_state(out, slug, level)
        evidence = f"case-evidence/{level}/{slug}.txt"
        rows.append(
            f"{slug}\t{state['status'].upper()}\t{evidence}\n"
        )
    (out / "qualification" / f"{level}-case-evidence.tsv").write_text(
        "".join(rows),
        encoding="utf-8",
    )


def _write_timings(
    out: Path,
    selected: tuple[str, ...],
    *,
    global_q1: float,
    global_q2: float,
) -> None:
    cases = {}
    for slug in selected:
        cases[slug] = {
            stage: _stage_state(out, slug, stage)["duration_seconds"]
            for stage in STAGES
        }

    payload = {
        "schema": 2,
        "selection": list(selected),
        "global": {
            "q1_seconds": round(global_q1, 6),
            "q2_seconds": round(global_q2, 6),
        },
        "cases": cases,
    }
    qualification = out / "qualification"
    (qualification / "affected-timings.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )

    rows = ["case\tstage\tseconds\tstatus\n"]
    for slug in selected:
        for stage in STAGES:
            state = _stage_state(out, slug, stage)
            rows.append(
                f"{slug}\t{stage}\t"
                f"{state['duration_seconds']:.6f}\t"
                f"{state['status'].upper()}\n"
            )
    (qualification / "affected-timings.tsv").write_text(
        "".join(rows),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=format_selection_help(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--cases",
        required=True,
        help="comma/space separated case slugs, group:<name>, or all",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "output" / "affected",
    )
    args = parser.parse_args()

    selected = parse_case_selection(args.cases)
    validate_runtime_metadata()

    out = args.out.resolve()
    if out.exists():
        shutil.rmtree(out)
    (out / "native").mkdir(parents=True, exist_ok=True)
    (out / "qualification").mkdir(parents=True, exist_ok=True)

    print("Affected qualification: " + ", ".join(selected))

    global_q1 = _run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT / "scpf",
    )
    global_q2 = _run(
        [sys.executable, "qualification/testsuite.py"]
    )

    for slug in selected:
        print(f"\n=== staged case: {slug} ===")
        run_case(slug, out, stages=STAGES)

    _aggregate_case_evidence(out, selected, "q1")
    _aggregate_case_evidence(out, selected, "q2")
    _aggregate_validation(out, selected)
    _write_timings(
        out,
        selected,
        global_q1=global_q1,
        global_q2=global_q2,
    )

    print("\nAffected staged qualification PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
