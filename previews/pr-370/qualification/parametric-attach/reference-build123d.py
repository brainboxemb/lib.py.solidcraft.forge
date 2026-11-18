"""build123d reference: a block attached to the right with a gap."""
from build123d import Align, Box, BuildPart, Locations

gap, base_width, child_width = 10.0, 40.0, 20.0
bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    Box(base_width, 30, 10, align=bottom)
    with Locations((base_width / 2 + child_width / 2 + gap, 0, 0)):
        Box(child_width, 20, 10, align=bottom)
