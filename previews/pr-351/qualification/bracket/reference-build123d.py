"""build123d reference: an L section across the Y symmetry plane."""
from build123d import Box, BuildPart, Locations

with BuildPart() as model:
    with Locations((20, 0, -6)):
        Box(40, 24, 12)
    with Locations((6, 0, -20)):
        Box(12, 24, 40)
