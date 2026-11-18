"""PR verification scope built on the single impact classifier."""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.cases import DEFAULT_REFERENCE_IMPLEMENTATIONS
from qualification.impact import (
    affected_cases,
    changed_paths,
    classify,
    final_gate,
)


REFERENCE_IMPLEMENTATIONS = frozenset(DEFAULT_REFERENCE_IMPLEMENTATIONS)
REFERENCE_INFRA_FILES = frozenset(
    {
        "qualification/reference_validation.py",
        "qualification/build123d_export.py",
        "qualification/cases.py",
        "qualification/toolchain.json",
        "docs/agent/reference-libraries.md",
    }
)


def _norm(path: str) -> str:
    value = path.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return str(PurePosixPath(value))


def reference_smoke_reasons(
    paths: list[str] | tuple[str, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    for raw in (_norm(path) for path in paths):
        path = PurePosixPath(raw)
        parts = path.parts
        if raw in REFERENCE_INFRA_FILES:
            reasons.append(raw)
            continue
        if (
            len(parts) >= 3
            and parts[0] == "examples"
            and parts[2] in REFERENCE_IMPLEMENTATIONS
        ):
            reasons.append(raw)
            continue
        if (
            len(parts) >= 2
            and parts[0] == "qualification"
            and "reference" in path.name
            and path.suffix == ".py"
        ):
            reasons.append(raw)
    return tuple(reasons)


def reference_smoke_required(
    paths: list[str] | tuple[str, ...],
) -> bool:
    return bool(reference_smoke_reasons(paths))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    paths = changed_paths(args.base, args.head)
    cases = affected_cases(paths)
    risk = classify(paths)
    gate = final_gate(paths, cases)
    reference_reasons = reference_smoke_reasons(paths)

    print("Changed paths:")
    for path in paths:
        print(f"  - {path}")
    print(f"Risk class: {risk}")
    print("Affected cases: " + (", ".join(cases) if cases else "none"))
    print(f"Final gate: {gate}")
    print(
        "Reference smoke: "
        + ("required" if reference_reasons else "skipped")
    )
    for path in reference_reasons:
        print(f"  - {path}")

    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(f"risk={risk}\n")
            handle.write(f"cases={','.join(cases)}\n")
            handle.write(f"has_cases={'true' if cases else 'false'}\n")
            handle.write(
                f"reference_smoke={'true' if reference_reasons else 'false'}\n"
            )
            handle.write(f"final_gate={gate}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
