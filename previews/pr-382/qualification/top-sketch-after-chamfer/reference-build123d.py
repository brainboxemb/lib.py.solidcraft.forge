"""build123d reference for a chamfered plate with one through hole."""

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Mode,
    chamfer,
    extrude,
)


with BuildPart() as model:
    Box(
        100,
        70,
        10,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    chamfer(model.edges().filter_by(Axis.Z), length=8)
    with BuildSketch(model.faces().sort_by(Axis.Z)[-1]):
        Circle(6)
    extrude(amount=-10, mode=Mode.SUBTRACT)
