"""build123d reference: a top-mounted arm clocked 90 degrees in XY."""
from build123d import Align, Box, BuildPart, Locations, Rot

bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    Box(60, 60, 10, align=bottom)
    with Locations((0, 0, 10)):
        with Locations(Rot(0, 0, 90)):
            Box(30, 10, 6, align=bottom)
