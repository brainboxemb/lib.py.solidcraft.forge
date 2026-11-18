"""build123d reference: a child's dimensions derive from its parent."""
from build123d import Align, Box, BuildPart, Locations

base_width, base_depth = 120.0, 80.0
bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    Box(base_width, base_depth, 10, align=bottom)
    with Locations((0, 0, 20)):
        Box(base_width / 2, base_depth / 2, 6, align=bottom)
