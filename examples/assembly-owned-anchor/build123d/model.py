"""build123d reference: companion and marker positioned by assembly intent."""
from build123d import Align, Box, BuildPart, Locations

bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    Box(40, 30, 20, align=bottom)
    with Locations((70, 0, 5), (15, -20, 15)):
        Box(10, 10, 10)
