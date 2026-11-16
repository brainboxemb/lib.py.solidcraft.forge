"""build123d reference: marker at the base's front/top/right corner."""
from build123d import Align, Box, BuildPart, Locations

bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    Box(40, 30, 20, align=bottom)
    with Locations((15, -20, 15)):
        Box(10, 10, 10)
