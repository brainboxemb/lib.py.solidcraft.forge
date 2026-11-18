"""CadQuery reference for two occurrences of one reusable block."""

import cadquery as cq


block = cq.Solid.makeBox(
    40,
    30,
    10,
    cq.Vector(-20, -15, 0),
)

model = cq.Assembly()
model.add(block, name="left", loc=cq.Location((0, 0, 0)))
model.add(block, name="right", loc=cq.Location((40, 0, 0)))
