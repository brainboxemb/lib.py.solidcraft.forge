"""build123d reference: two translated and Z-rotated panel occurrences."""
from build123d import Align, Box, BuildPart, Locations, Rot

center = (Align.CENTER, Align.CENTER, Align.CENTER)

with BuildPart() as model:
    for x in (-40, 40):
        with Locations((x, 0, 0)):
            with Locations(Rot(0, 0, 90)):
                Box(20, 10, 4, align=center)
