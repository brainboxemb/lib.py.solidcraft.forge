"""CadQuery reference for two independently and symmetrically placed blocks."""

import cadquery as cq

block = cq.Solid.makeBox(
    20,
    20,
    10,
    cq.Vector(-10, -10, -5),
)

model = cq.Assembly()
model.add(block, name="left", loc=cq.Location((-40, 0, 0)))
model.add(block, name="right", loc=cq.Location((40, 0, 0)))
