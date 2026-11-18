"""build123d geometry reference for the 3 x 2 rectangular slot pattern."""

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Locations,
    Mode,
    SlotCenterToCenter,
    extrude,
)

bottom = (Align.CENTER, Align.CENTER, Align.MIN)
points = [(x, y) for y in (0, 28) for x in (0, 24, 48)]

with BuildPart() as model:
    Box(120, 80, 4, align=bottom)
    with BuildSketch(model.faces().sort_by(Axis.Z)[-1]):
        with Locations(*points):
            SlotCenterToCenter(10, 6)
    extrude(amount=-4, mode=Mode.SUBTRACT)
