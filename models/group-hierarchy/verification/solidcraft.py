"""Model-specific declarative verification for group-hierarchy."""

from __future__ import annotations

from pathlib import Path

from cad_verification import (
    BodyEnvelope,
    SolidCraftInspection,
    SolidCraftInspectionCheck,
    SolidCraftInspectionSelect,
    SolidCraftModelExpectation,
    SolidCraftVerification,
)


HERE = Path(__file__).resolve().parent

VERIFICATION = SolidCraftVerification(
    verification_id="group-hierarchy",
    baseline=SolidCraftModelExpectation(
        body_count=3,
        body_envelopes=(
            BodyEnvelope((-5.0, -1.0, 0.0), (5.0, 1.0, 20.0)),
            BodyEnvelope((6.0, -1.0, 0.0), (16.0, 1.0, 20.0)),
            BodyEnvelope((-17.5, 15.0, 0.0), (17.5, 25.0, 40.0)),
        ),
        bounds_tolerance=0.001,
    ),
    inspections=(
        SolidCraftInspection(
            id="hierarchy",
            command_path=HERE / "inspect_bom.json",
            checks=(
                SolidCraftInspectionCheck(id="result_count", count=3),
                SolidCraftInspectionCheck(
                    id="top_levels", path=(0, "levels"), expected="top",
                ),
                SolidCraftInspectionCheck(
                    id="top_row_count", path=(0, "rows"), count=2,
                ),
                SolidCraftInspectionCheck(
                    id="top_frame_count",
                    path=(0, "rows", SolidCraftInspectionSelect("definition", "Frame"), "count"),
                    expected=1,
                ),
                SolidCraftInspectionCheck(
                    id="top_group_count",
                    path=(0, "rows", SolidCraftInspectionSelect("definition", "PanelGroup"), "count"),
                    expected=1,
                ),
                SolidCraftInspectionCheck(
                    id="top_total", path=(0, "total_occurrences"), expected=2,
                ),
                SolidCraftInspectionCheck(
                    id="flat_levels", path=(1, "levels"), expected="flat",
                ),
                SolidCraftInspectionCheck(
                    id="flat_row_count", path=(1, "rows"), count=2,
                ),
                SolidCraftInspectionCheck(
                    id="flat_frame_count",
                    path=(1, "rows", SolidCraftInspectionSelect("definition", "Frame"), "count"),
                    expected=1,
                ),
                SolidCraftInspectionCheck(
                    id="flat_panel_count",
                    path=(1, "rows", SolidCraftInspectionSelect("definition", "Panel"), "count"),
                    expected=2,
                ),
                SolidCraftInspectionCheck(
                    id="flat_total", path=(1, "total_occurrences"), expected=3,
                ),
                SolidCraftInspectionCheck(
                    id="panel_group_occurrence_count",
                    path=(2, "components", SolidCraftInspectionSelect("name", "PanelGroup"), "occurrences"),
                    count=1,
                ),
                SolidCraftInspectionCheck(
                    id="panel_group_grounded",
                    path=(2, "components", SolidCraftInspectionSelect("name", "PanelGroup"), "occurrences", 0, "grounded"),
                    expected=False,
                ),
                SolidCraftInspectionCheck(
                    id="panel_occurrence_count",
                    path=(2, "components", SolidCraftInspectionSelect("name", "Panel"), "occurrences"),
                    count=2,
                ),
                SolidCraftInspectionCheck(
                    id="panel_first_grounded",
                    path=(2, "components", SolidCraftInspectionSelect("name", "Panel"), "occurrences", 0, "grounded"),
                    expected=True,
                ),
            ),
        ),
    ),
)
