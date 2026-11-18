"""build123d reference for a six-hole circular feature pattern."""

from math import cos, pi, sin
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
points = [
    (30 * cos(index * 2 * pi / 6), 30 * sin(index * 2 * pi / 6))
    for index in range(6)
]

with BuildPart() as model:
    Box(100, 100, 6, align=bottom)
    with BuildSketch(model.faces().sort_by(Axis.Z)[-1]):
        with Locations(*points):
            Circle(4)
    extrude(amount=-6, mode=Mode.SUBTRACT)
