"""CadQuery reference for a centred plate with two symmetric through holes."""

import cadquery as cq


width = 100.0
depth = 60.0
thickness = 10.0
spacing = 40.0

plate = (
    cq.Workplane("XY")
    .box(width, depth, thickness, centered=(True, True, False))
    .faces(">Z")
    .workplane()
    .pushPoints([
        (0, -spacing / 2),
        (0, spacing / 2),
    ])
    .hole(8.0)
)

model = cq.Assembly()
model.add(plate, name="plate")
