"""Runtime metadata for selected native qualification cases.

This module contains orchestration metadata only. Geometry expectations stay in
qualification.expectations/native_validation; public API meaning stays in scpf.
"""

from __future__ import annotations

from pathlib import Path

from qualification.cases import supported_qualification_cases


ROOT = Path(__file__).resolve().parents[1]


MUTATIONS = {
    "simple-box": {
        "command": "qualification/commands/simple-box/change-size.json",
        "save": "model-size-60x40x20.sc",
        "measurements": "measurements-size-60x40x20.json",
        "label": "box 40x30x10 -> 60x40x20 mm while centre stays fixed",
    },
    "parameter-scope": {
        "command": "qualification/commands/parameter-scope/change-shared-width.json",
        "save": "model-shared-width-100.sc",
        "measurements": "measurements-shared-width-100.json",
        "label": "shared_width 80 -> 100 mm",
    },
    "parent-derived-child-size": {
        "command": "qualification/commands/parent-derived-child-size/change-size.json",
        "save": "model-size-160x120.sc",
        "measurements": "measurements-size-160x120.json",
        "label": "parent 120x80 -> 160x120 mm; child follows 60x40 -> 80x60 mm",
    },
    "assembly-owned-anchor": {
        "command": "qualification/commands/assembly-owned-anchor/change-size.json",
        "save": "model-size-80x40.sc",
        "measurements": "measurements-size-80x40.json",
        "label": "base 40x20 -> 80x40 mm; named semantic anchor follows corner",
    },
    "anchor-topology-mutation": {
        "command": "qualification/commands/anchor-topology-mutation/change-size.json",
        "save": "model-size-80x40.sc",
        "measurements": "measurements-size-80x40.json",
        "label": "board 40x20 -> 80x40 mm; fixed topology pick follows corner",
    },
    "parametric-attach": {
        "command": "qualification/commands/parametric-attach/change-gap.json",
        "save": "model-gap-30.sc",
        "measurements": "measurements-gap-30.json",
        "label": "gap 10 -> 30 mm",
    },
    "parametric-offset": {
        "command": "qualification/commands/parametric-offset/change-shift.json",
        "save": "model-shift-10.sc",
        "measurements": "measurements-shift-10.json",
        "label": "shift 5 -> 10 mm",
    },
    "parametric-anchor": {
        "command": "qualification/commands/parametric-anchor/change-base-width.json",
        "save": "model-width-80.sc",
        "measurements": "measurements-width-80.json",
        "label": "base_width 40 -> 80 mm",
    },
    "corner-anchor": {
        "command": "qualification/commands/corner-anchor/change-size.json",
        "save": "model-size-80x40.sc",
        "measurements": "measurements-size-80x40.json",
        "label": "base 40x20 -> 80x40 mm",
    },
    "xz-anchor": {
        "command": "qualification/commands/xz-anchor/change-size.json",
        "save": "model-size-80x40.sc",
        "measurements": "measurements-size-80x40.json",
        "label": "board 40x20 -> 80x40 mm",
    },
    "four-corner-l": {
        "command": "qualification/commands/four-corner-l/change-size.json",
        "save": "model-size-160x120.sc",
        "measurements": "measurements-size-160x120.json",
        "label": "frame 120x80 -> 160x120 mm",
    },
    "eight-corner-brackets": {
        "command": "qualification/commands/eight-corner-brackets/change-size.json",
        "save": "model-size-160x120x90.sc",
        "measurements": "measurements-size-160x120x90.json",
        "label": "frame 120x80x60 -> 160x120x90 mm",
    },
    "eight-flightcase-corners": {
        "command": "qualification/commands/eight-flightcase-corners/change-size.json",
        "save": "model-size-160x120x90.sc",
        "measurements": "measurements-size-160x120x90.json",
        "label": "case 120x80x60 -> 160x120x90 mm",
    },
}


POST_BUILD_INSPECTIONS = {
    "group-hierarchy": {
        "command": "qualification/commands/group-hierarchy/inspect-bom.json",
        "output": "results-bom.json",
    },
}


def q5_required_cases() -> tuple[str, ...]:
    return tuple(
        case["slug"]
        for case in supported_qualification_cases()
        if case.get("q5_required", False)
    )


def mutation_spec(slug: str) -> dict | None:
    return MUTATIONS.get(slug)


def validate_runtime_metadata() -> None:
    expected = set(q5_required_cases())
    actual = set(MUTATIONS)
    if expected != actual:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(
            f"mutation metadata mismatch; missing={missing}, extra={extra}"
        )

    for slug, spec in MUTATIONS.items():
        path = ROOT / spec["command"]
        if not path.is_file():
            raise ValueError(f"missing mutation command for {slug}: {path}")

    for slug, spec in POST_BUILD_INSPECTIONS.items():
        path = ROOT / spec["command"]
        if not path.is_file():
            raise ValueError(f"missing post-build command for {slug}: {path}")
