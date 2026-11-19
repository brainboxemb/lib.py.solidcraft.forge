"""CadQuery geometry reference for the selected board corner and marker.

Forge's stronger contract is persisted native topology identity after a saved
SolidCraft resize; this reference compares the baseline geometry and datum.
"""

import cadquery as cq


board = cq.Solid.makeBox(40, 20, 20, cq.Vector(-20, -10, 0))
marker = cq.Solid.makeBox(10, 10, 10, cq.Vector(-5, -5, -5))

model = cq.Assembly()
model.add(board, name="board")
model.add(marker, name="marker", loc=cq.Location((-20, -15, 20)))
