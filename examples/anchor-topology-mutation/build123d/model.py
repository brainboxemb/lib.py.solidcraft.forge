"""build123d baseline for a board and a topology-anchored marker.

The persisted edited-topology identity is tested only by native SolidCraft.
"""
from build123d import Align, Box, BuildPart, Locations

bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    Box(40, 20, 20, align=bottom)
    with Locations((-20, -15, 20)):
        Box(10, 10, 10)
