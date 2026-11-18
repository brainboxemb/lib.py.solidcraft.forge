"""build123d reference: a marker shifted relative to a top/front corner."""
from build123d import Align, Box, BuildPart, Locations

shift = 5.0
bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    Box(40, 30, 20, align=bottom)
    with Locations((15, -15 - shift, 20)):
        Box(10, 10, 10)
