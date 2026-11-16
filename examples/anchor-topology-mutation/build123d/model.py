"""build123d baseline for a board and a topology-anchored marker.

The persisted edited-topology identity is tested only by native SolidCraft.
"""
from build123d import Align, Box, Compound, Pos

board = Box(40, 20, 20, align=(Align.CENTER, Align.CENTER, Align.MIN))
marker = Pos(-20, -15, 20) * Box(10, 10, 10)
model = Compound(children=[board, marker])
