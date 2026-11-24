"""build123d reference for two parent/marker pairs."""
from build123d import Align, Box, BuildPart, Locations

parent_height = 40.0
bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    Box(20, 20, parent_height, align=bottom)
    with Locations((60, 0, 0)):
        Box(20, 20, parent_height, align=bottom)
    with Locations((0, 0, parent_height)):
        Box(10, 10, 10, align=bottom)
    with Locations((60, 0, parent_height)):
        Box(10, 10, 10, align=bottom)
