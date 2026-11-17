"""build123d geometry reference for the five Slot-family cut shapes."""

from build123d import (
    Align,
    Axis,
    Box,
    BuildLine,
    BuildPart,
    BuildSketch,
    CenterArc,
    Locations,
    Mode,
    SlotCenterPoint,
    SlotCenterToCenter,
    SlotCurve,
    SlotOverall,
    ThreePointArc,
    extrude,
)

bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    Box(160, 120, 5, align=bottom)

    with BuildSketch(model.faces().sort_by(Axis.Z)[-1]):
        with Locations((-50, -35)):
            SlotCenterToCenter(20, 8)
        with Locations((5, -35)):
            SlotOverall(30, 8)
        SlotCenterPoint((55, -35), (65, -35), 8)

        with BuildLine(mode=Mode.PRIVATE) as three_point:
            ThreePointArc((-50, 25), (-35, 38), (-20, 25))
        SlotCurve(three_point.edges()[0], 8)

        with BuildLine(mode=Mode.PRIVATE) as center_arc:
            CenterArc((40, 25), 12, 0, 120)
        SlotCurve(center_arc.edges()[0], 8)

    extrude(amount=-5, mode=Mode.SUBTRACT)
