"""build123d reference: a true rounded sketch pad on a rectangular base."""
from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    RectangleRounded,
    extrude,
)

base_width, base_depth, base_height = 80.0, 60.0, 5.0
pad_width, pad_depth, radius, pad_height = 40.0, 30.0, 5.0, 8.0
bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    Box(base_width, base_depth, base_height, align=bottom)

    with BuildSketch(model.faces().sort_by(Axis.Z)[-1]):
        RectangleRounded(pad_width, pad_depth, radius)

    extrude(amount=pad_height)
