#!/usr/bin/env python3
"""Run explicit case-specific Q1 or Q2 unittest evidence."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qualification.case_evidence import evidence_for, validate_case_evidence
from qualification.case_selection import parse_case_selection


_RAN = re.compile(r"Ran\s+(\d+)\s+tests?")


def _target_cwd(
    target: dict[str, str],
    caller_cwd: Path | None = None,
) -> Path:
    """Run Q1 from the package root so `import scpf` resolves the real package."""
    if target["file"].startswith("scpf/tests/"):
        return caller_cwd or (ROOT / "scpf")
    return ROOT


def _run_target(
    target: dict[str, str],
) -> tuple[list[str], str, int, bool]:
    path = ROOT / target["file"]
    command = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        str(path.parent),
        "-p",
        path.name,
        "-k",
        target["test"],
        "-v",
    ]

    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    completed = subprocess.run(
        command,
        cwd=_target_cwd(target),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    match = _RAN.search(completed.stdout)
    count = int(match.group(1)) if match else 0
    passed = completed.returncode == 0 and count > 0
    return command, completed.stdout, count, passed


def run(
    level: str,
    out: Path,
    selection: str = "all",
) -> int:
    validate_case_evidence()
    selected = parse_case_selection(selection)

    evidence_root = out / "case-evidence" / level
    evidence_root.mkdir(parents=True, exist_ok=True)

    rows = []
    failures = []
    for slug in selected:
        targets = list(evidence_for(slug, level))
        log = []
        passed = True

        for target in targets:
            command, output, count, target_passed = _run_target(target)
            log.append("$ " + " ".join(command))
            log.append(output.rstrip())
            log.append(
                f"matched_tests={count} "
                f"status={'PASS' if target_passed else 'FAIL'}"
            )
            passed = passed and target_passed

        evidence = f"case-evidence/{level}/{slug}.txt"
        (out / evidence).write_text(
            "\n\n".join(log) + "\n",
            encoding="utf-8",
        )
        status = "PASS" if passed else "FAIL"
        rows.append(
            {
                "case": slug,
                "status": status,
                "tests": json.dumps(targets, separators=(",", ":")),
                "evidence": evidence,
            }
        )
        if not passed:
            failures.append(slug)
            print(
                f"\n{level.upper()} evidence failure: {slug}",
                file=sys.stderr,
            )
            for entry in log:
                print(entry, file=sys.stderr)

    with (out / f"{level}-case-evidence.tsv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("case", "status", "tests", "evidence"),
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)

    if failures:
        print(
            f"{level.upper()} case evidence failed: {', '.join(failures)}",
            file=sys.stderr,
        )
        return 1

    print(
        f"{level.upper()} case evidence PASS: "
        f"{len(rows)} selected cases"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--level",
        choices=("q1", "q2"),
        required=True,
    )
    parser.add_argument(
        "--cases",
        default="all",
        help="comma/space separated case slugs, group:<name>, or all",
    )
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
    )
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    return run(args.level, args.out, args.cases)


if __name__ == "__main__":
    raise SystemExit(main())
