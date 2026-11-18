#!/usr/bin/env python3
"""Confirm whether a main push may reuse canonical build/main evidence."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.impact import affected_cases, changed_paths, final_gate


ZERO_SHA = "0" * 40


def reusable_paths(paths: tuple[str, ...] | list[str]) -> bool:
    cases = affected_cases(tuple(paths))
    return final_gate(tuple(paths), cases) == "preflight"


def normalize_base(base: str, head: str) -> str:
    if base and base != ZERO_SHA:
        return base
    return subprocess.run(
        ["git", "rev-parse", f"{head}^"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("scope",))
    parser.add_argument("--base", default="")
    parser.add_argument("--head", required=True)
    parser.add_argument("--github-output", type=Path, required=True)
    args = parser.parse_args()

    base = normalize_base(args.base, args.head)
    paths = changed_paths(base, args.head)
    allowed = reusable_paths(paths)
    print("Site publication scope: " + ("reusable" if allowed else "technical"))
    for path in paths:
        print(f"  - {path}")
    with args.github_output.open("a", encoding="utf-8") as handle:
        handle.write(f"site_only={'true' if allowed else 'false'}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
