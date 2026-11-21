"""build123d reference: a symmetric pair of translated blocks."""
from build123d import Align, Box, BuildPart, Locations

center = (Align.CENTER, Align.CENTER, Align.CENTER)

with BuildPart() as model:
    with Locations((-40, 0, 0), (40, 0, 0)):
        Box(20, 20, 10, align=center)
