"""CadQuery reference for the parameterized Box qualification baseline."""

import cadquery as cq


length = 40.0
width = 30.0
height = 10.0

box = cq.Solid.makeBox(
    length,
    width,
    height,
    cq.Vector(-length / 2, -width / 2, 0),
)

model = cq.Assembly()
model.add(box, name="box")
