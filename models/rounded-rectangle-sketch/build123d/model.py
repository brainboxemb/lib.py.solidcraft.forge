"""build123d reference: rounded pad plus independent world-plane tunnel."""
from build123d import (
    Align,
    Axis,
    Box,
    BuildPart,
    BuildSketch,
    Locations,
    Mode,
    RectangleRounded,
    extrude,
)

base_width, base_depth, base_height = 80.0, 60.0, 5.0
pad_width, pad_depth, radius, pad_height = 40.0, 30.0, 5.0, 8.0
cut_width, cut_height, cut_y, cut_z, cut_length = 10.0, 2.0, 22.0, 2.5, 100.0
bottom = (Align.CENTER, Align.CENTER, Align.MIN)
centered = (Align.CENTER, Align.CENTER, Align.CENTER)

with BuildPart() as model:
    Box(base_width, base_depth, base_height, align=bottom)

    with BuildSketch(model.faces().sort_by(Axis.Z)[-1]):
        RectangleRounded(pad_width, pad_depth, radius)

    extrude(amount=pad_height)

    with Locations((0, cut_y, cut_z)):
        Box(
            cut_length,
            cut_width,
            cut_height,
            align=centered,
            mode=Mode.SUBTRACT,
        )
