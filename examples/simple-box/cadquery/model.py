"""CadQuery reference for the centered SimpleBox qualification intent."""

import cadquery as cq


length = 40.0
width = 30.0
height = 10.0

box = (
    cq.Workplane("XY")
    .box(length, width, height, centered=(True, True, True))
    .val()
)

model = cq.Assembly()
model.add(box, name="box")
