"""CadQuery reference for a plate with two symmetric through holes."""

import cadquery as cq


width = 100.0
depth = 60.0
thickness = 10.0
spacing = 40.0

plate = (
    cq.Workplane("XY")
    .box(width, depth, thickness, centered=(False, False, False))
    .faces(">Z")
    .workplane()
    .pushPoints([
        (width / 2, depth / 2 - spacing / 2),
        (width / 2, depth / 2 + spacing / 2),
    ])
    .hole(8.0)
)

model = cq.Assembly()
model.add(plate, name="plate")
