"""CadQuery reference for a six-hole circular feature pattern."""

from math import cos, pi, sin
import cadquery as cq


points = [
    (30 * cos(index * 2 * pi / 6), 30 * sin(index * 2 * pi / 6))
    for index in range(6)
]

result = (
    cq.Workplane("XY")
    .box(100, 100, 6, centered=(True, True, False))
    .faces(">Z")
    .workplane()
    .pushPoints(points)
    .circle(4)
    .cutThruAll()
)

model = cq.Assembly()
model.add(result, name="circular_feature_pattern")
