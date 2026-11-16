"""CadQuery reference for a box centered on its declared origin."""

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
model.add(box, name="centered_box")
