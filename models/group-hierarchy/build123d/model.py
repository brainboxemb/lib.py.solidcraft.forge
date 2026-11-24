"""build123d reference: two panels plus a separate frame.

The builder compares visible geometry; SolidCraft-native qualification proves
browser hierarchy and BOM persistence.
"""
from build123d import Align, Box, BuildPart, Locations

bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    with Locations((0, 0, 0), (11, 0, 0)):
        Box(10, 2, 20, align=bottom)
    with Locations((0, 20, 0)):
        Box(35, 10, 40, align=bottom)
