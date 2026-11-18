"""build123d reference: XZ-oriented board and two front corner markers."""
from build123d import Align, Box, BuildPart, Locations

bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    with Locations((0, 6, 0)):
        Box(40, 12, 20, align=bottom)

    with Locations((15, -5, 15), (-15, -5, 15)):
        Box(10, 10, 10)
