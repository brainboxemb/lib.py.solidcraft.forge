"""build123d geometry reference: fixed/shared/derived panel widths.

Persisted native SolidCraft parameter changes are qualified separately.
"""
from build123d import Align, Box, BuildPart, Locations

shared_width = 80.0
bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    for x, width in [
        (0, 40),
        (100, 60),
        (220, shared_width),
        (340, shared_width),
        (460, shared_width / 2),
    ]:
        with Locations((x, 0, 0)):
            Box(width, 20, 10, align=bottom)
