"""build123d reference for a stepped circular body."""

from build123d import Align, BuildPart, Cylinder, Locations

bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    Cylinder(50, 10, align=bottom)
    with Locations((0, 0, 10)):
        Cylinder(22, 16, align=bottom)
