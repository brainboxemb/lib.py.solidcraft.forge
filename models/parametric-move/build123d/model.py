"""build123d reference: two normally translated block occurrences."""
from build123d import Align, Box, BuildPart, Locations

center = (Align.CENTER, Align.CENTER, Align.CENTER)

with BuildPart() as model:
    with Locations((0, 0, 0), (40, 0, 0)):
        Box(20, 20, 10, align=center)
