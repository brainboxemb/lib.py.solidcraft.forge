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
        "command": "qualification/commands/simple-box/change-length.json",
        "save": "model-length-50.sc",
        "measurements": "measurements-length-50.json",
        "label": "length 40 -> 50 mm",
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
    "repeated-parent-attachments": {
        "command": "qualification/commands/repeated-parent-attachments/change-height.json",
        "save": "model-height-60.sc",
        "measurements": "measurements-height-60.json",
        "label": "parent_height 40 -> 60 mm; both attached markers follow",
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
    "sketch-pattern-mirror": {
        "command": "qualification/commands/sketch-pattern-mirror/change-patterns.json",
        "save": "model-patterns-mutated.sc",
        "measurements": "measurements-patterns-mutated.json",
        "label": "Circle diameter and sketch pattern spacing mutate through existing pattern/mirror relationships",
    },
    "selective-profile-extrude": {
        "command": "qualification/commands/selective-profile-extrude/change-pattern.json",
        "save": "model-pattern-mutated.sc",
        "measurements": "measurements-pattern-mutated.json",
        "label": "hole diameter 8 -> 10 mm; pattern pitch 20 -> 24 mm; selected profiles remain associated",
    },
    "circular-feature-pattern": {
        "command": "qualification/commands/circular-feature-pattern/change-count.json",
        "save": "model-bolts-4.sc",
        "measurements": "measurements-bolts-4.json",
        "label": "bolt count 6 -> 4",
    },
    "rectangular-pattern": {
        "command": "qualification/commands/rectangular-pattern/change-columns-pitch.json",
        "save": "model-columns-2-pitch-30.sc",
        "measurements": "measurements-columns-2-pitch-30.json",
        "label": "columns 3 -> 2; pitch 24 -> 30 mm",
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
    "sheet-fold": {
        "command": "qualification/commands/sheet-fold/inspect-flat-pattern.json",
        "output": "results-flat-pattern.json",
    },
}


def saved_design_cases() -> tuple[str, ...]:
    return tuple(
        case["slug"]
        for case in supported_qualification_cases()
        if case.get("saved_design_required", False)
    )


def mutation_spec(slug: str) -> dict | None:
    return MUTATIONS.get(slug)


def validate_runtime_metadata() -> None:
    expected = set(saved_design_cases())
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
