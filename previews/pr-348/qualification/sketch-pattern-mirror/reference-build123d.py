"""build123d geometry reference for sketch pattern/mirror qualification."""

from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Locations,
    Mode,
    SlotCenterToCenter,
    extrude,
)

bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    Box(240, 160, 5, align=bottom)

    with BuildSketch(model.faces().sort_by(Axis.Z)[-1]):
        with Locations(*[
            (x, y)
            for y in (-45, 45)
            for x in (-60, -35, -10, 15)
        ]):
            Circle(4)

        with Locations(*[
            (x, y)
            for y in (-20, 20)
            for x in (-80, -30, 30, 80)
        ]):
            SlotCenterToCenter(20, 8)

    extrude(amount=-5, mode=Mode.SUBTRACT)
