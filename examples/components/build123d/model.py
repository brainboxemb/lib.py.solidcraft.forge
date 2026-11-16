"""build123d reference: two positions of one block geometry."""
from build123d import Align, Box, BuildPart, Locations

bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    with Locations((0, 0, 0), (40, 0, 0)):
        Box(40, 30, 10, align=bottom)
