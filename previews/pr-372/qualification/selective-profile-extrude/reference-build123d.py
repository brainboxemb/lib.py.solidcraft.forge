"""build123d geometry reference for selective profile extrusion."""

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Locations,
    Mode,
    extrude,
)

bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    Box(120, 60, 5, align=bottom)
    with BuildSketch(model.faces().sort_by(Axis.Z)[-1]):
        with Locations(*[(x, 0) for x in (-30, -10, 30)]):
            Circle(4)
    extrude(amount=-5, mode=Mode.SUBTRACT)
