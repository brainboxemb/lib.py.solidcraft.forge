"""build123d reference for the original lower-left-bottom plate datum."""
from build123d import Align, Box, BuildPart, Cylinder, Locations, Mode

width, depth, thickness, spacing = 100.0, 60.0, 10.0, 40.0

with BuildPart() as model:
    Box(
        width,
        depth,
        thickness,
        align=(Align.MIN, Align.MIN, Align.MIN),
    )
    with Locations(
        (width / 2, depth / 2 - spacing / 2, thickness / 2),
        (width / 2, depth / 2 + spacing / 2, thickness / 2),
    ):
        Cylinder(4.0, thickness + 2, mode=Mode.SUBTRACT)
