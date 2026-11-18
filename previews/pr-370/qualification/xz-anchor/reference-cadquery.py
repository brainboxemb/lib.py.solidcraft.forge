"""CadQuery reference for an XZ-oriented board with two front corner markers."""

import cadquery as cq


board = cq.Solid.makeBox(40, 12, 20, cq.Vector(-20, 0, 0))
marker = cq.Solid.makeBox(10, 10, 10, cq.Vector(-5, -5, -5))

model = cq.Assembly()
model.add(board, name="board")
model.add(marker, name="right_marker", loc=cq.Location((15, -5, 15)))
model.add(marker, name="left_marker", loc=cq.Location((-15, -5, 15)))
