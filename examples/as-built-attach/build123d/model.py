"""build123d reference: preserve an already positioned and rotated marker."""
from build123d import Align, Box, BuildPart, Locations, Rot

center = (Align.CENTER, Align.CENTER, Align.CENTER)

with BuildPart() as model:
    Box(40, 30, 10, align=center)
    with Locations((50, 20, 15)):
        with Locations(Rot(0, 0, 90)):
            Box(30, 10, 8, align=center)
