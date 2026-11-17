"""Decide whether a PR preview needs the external reference smoke test.

The fast preview always runs Forge API/qualification tests and builds the site.
Comparison libraries are installed only when the changed paths can affect the
reference-validation layer itself.
"""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qualification.cases import DEFAULT_REFERENCE_IMPLEMENTATIONS


REFERENCE_IMPLEMENTATIONS = frozenset(DEFAULT_REFERENCE_IMPLEMENTATIONS)


def _normalized(path: str) -> PurePosixPath:
    value = path.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return PurePosixPath(value)


def reference_smoke_reasons(paths: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Return changed paths that require executing comparison references."""
    reasons: list[str] = []
    for raw in paths:
        path = _normalized(raw)
        parts = path.parts
        if not parts:
            continue

        # Python under qualification is executable qualification
        # infrastructure. JSON commands, diagrams, templates and generated
        # evidence do not by themselves require third-party CAD libraries.
        if parts[0] == "qualification" and path.suffix == ".py":
            reasons.append(str(path))
            continue

        # Reference source directories are derived from the central registry,
        # so adding another case does not require editing this selector.
        if (
            len(parts) >= 3
            and parts[0] == "examples"
            and parts[2] in REFERENCE_IMPLEMENTATIONS
        ):
            reasons.append(str(path))
            continue

        if str(path) == "docs/agent/reference-libraries.md":
            reasons.append(str(path))
            continue

        # A change to this workflow must exercise its own conditional branch.
        if str(path) == ".github/workflows/preview.yml":
            reasons.append(str(path))

    return tuple(reasons)


def reference_smoke_required(paths: list[str] | tuple[str, ...]) -> bool:
    return bool(reference_smoke_reasons(paths))


def changed_paths(base: str, head: str) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", base, head, "--"],
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    paths = changed_paths(args.base, args.head)
    reasons = reference_smoke_reasons(paths)
    required = bool(reasons)

    print("Changed paths:")
    for path in paths:
        print(f"  - {path}")
    if required:
        print("Reference smoke: required")
        for path in reasons:
            print(f"  - {path}")
    else:
        print("Reference smoke: skipped; no reference-validation paths changed")

    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(
                f"reference_smoke={'true' if required else 'false'}\n"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
