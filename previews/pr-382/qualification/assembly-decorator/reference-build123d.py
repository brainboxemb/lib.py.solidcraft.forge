"""build123d reference: two posts built from one reusable shape."""
from build123d import Align, Box, BuildPart, Locations

bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    with Locations((-15, 0, 0), (15, 0, 0)):
        Box(10, 10, 20, align=bottom)
