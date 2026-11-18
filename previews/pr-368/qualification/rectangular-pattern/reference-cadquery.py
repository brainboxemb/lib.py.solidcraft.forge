"""CadQuery geometry reference for the 3 x 2 rectangular slot pattern."""

import cadquery as cq

points = [(x, y) for y in (0, 28) for x in (0, 24, 48)]

result = (
    cq.Workplane("XY")
    .box(120, 80, 4, centered=(True, True, False))
    .faces(">Z")
    .workplane()
    .pushPoints(points)
    .slot2D(16, 6)
    .cutThruAll()
)

model = cq.Assembly()
model.add(result, name="rectangular_pattern")
