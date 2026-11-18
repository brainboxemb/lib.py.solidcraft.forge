"""Select the smallest useful verification scope for a pull request.

The selector turns changed paths into concrete qualification cases. Workflows
must use this result instead of compiling every model by default.
"""

from __future__ import annotations

import argparse
from pathlib import Path, PurePosixPath
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qualification.case_evidence import CASE_EVIDENCE
from qualification.cases import DEFAULT_REFERENCE_IMPLEMENTATIONS
from qualification.case_selection import CASE_SLUGS


REFERENCE_IMPLEMENTATIONS = frozenset(DEFAULT_REFERENCE_IMPLEMENTATIONS)
REFERENCE_INFRA_FILES = frozenset(
    {
        "qualification/reference_validation.py",
        "qualification/build123d_export.py",
        "qualification/cases.py",
        "docs/agent/reference-libraries.md",
    }
)
GLOBAL_CASE_FILES = frozenset(
    {
        "qualification/case_evidence.py",
        "qualification/case_selection.py",
        "qualification/cases.py",
        "qualification/run_case_evidence.py",
    }
)
FOUNDATIONAL_FORGE_FILES = frozenset(
    {
        "scpf/scpf/compiler.py",
        "scpf/scpf/headless.py",
        "scpf/scpf/replay.py",
        "scpf/scpf/runner.py",
    }
)
NATIVE_QUALIFICATION_FILES = frozenset(
    {
        "qualification/native_cases.py",
        "qualification/native_validation.py",
        "qualification/run_affected.py",
        "qualification/visual_validation.py",
    }
)


def _normalized(path: str) -> PurePosixPath:
    value = path.replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return PurePosixPath(value)


def _strings(paths: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(_normalized(path)) for path in paths)


def affected_cases(paths: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Return qualification cases proved by the changed source/tests."""
    normalized = _strings(paths)
    selected: set[str] = set()

    if any(path in GLOBAL_CASE_FILES for path in normalized):
        return CASE_SLUGS

    for raw in normalized:
        path = PurePosixPath(raw)
        parts = path.parts
        if len(parts) >= 2 and parts[0] == "examples" and parts[1] in CASE_SLUGS:
            selected.add(parts[1])

    changed = set(normalized)
    for slug, levels in CASE_EVIDENCE.items():
        for level in ("q1", "q2"):
            for target in levels[level]:
                if target["file"] in changed:
                    selected.add(slug)

    forge_source_changed = any(
        path.startswith("scpf/scpf/") and path.endswith(".py")
        for path in normalized
    )
    if forge_source_changed and not selected:
        raise ValueError(
            "Forge source changed without an affected qualification case. "
            "Change/add the proving unit test referenced by CASE_EVIDENCE or "
            "change/add examples/<case>/ for this API contract."
        )

    return tuple(slug for slug in CASE_SLUGS if slug in selected)


def reference_smoke_reasons(paths: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    """Return changed paths that require executing comparison references."""
    reasons: list[str] = []
    for raw in _strings(paths):
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


def reference_smoke_required(paths: list[str] | tuple[str, ...]) -> bool:
    return bool(reference_smoke_reasons(paths))


def final_gate(paths: list[str] | tuple[str, ...], cases: tuple[str, ...]) -> str:
    """Return the end-of-change verification expected before promotion."""
    normalized = _strings(paths)

    if any(path in FOUNDATIONAL_FORGE_FILES for path in normalized):
        return "full-q1-q6"

    native_sensitive = any(
        path.startswith("scpf/scpf/")
        or (
            path.startswith("examples/")
            and "/scpf/" in path
        )
        or path in NATIVE_QUALIFICATION_FILES
        for path in normalized
    )
    if native_sensitive:
        return "affected-q1-q6"

    if cases:
        return "affected-q1-q2"

    return "preflight"


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
    cases = affected_cases(paths)
    reference_reasons = reference_smoke_reasons(paths)
    gate = final_gate(paths, cases)

    print("Changed paths:")
    for path in paths:
        print(f"  - {path}")
    print("Affected cases: " + (", ".join(cases) if cases else "none"))
    print("PR verification: preflight + affected Q1/Q2")
    print(f"Final gate: {gate}")
    if reference_reasons:
        print("Reference smoke: required")
        for path in reference_reasons:
            print(f"  - {path}")
    else:
        print("Reference smoke: skipped")

    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(f"cases={','.join(cases)}\n")
            handle.write(f"has_cases={'true' if cases else 'false'}\n")
            handle.write(
                "reference_smoke="
                + ("true" if reference_reasons else "false")
                + "\n"
            )
            handle.write(f"final_gate={gate}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
