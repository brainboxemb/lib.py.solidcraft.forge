"""CadQuery geometry reference for selective profile extrusion."""

import cadquery as cq

plate = cq.Workplane("XY").box(120, 60, 5, centered=(True, True, False))
cutters = None

for x in (-30, -10, 30):
    hole = (
        cq.Workplane("XY")
        .center(x, 0)
        .circle(4)
        .extrude(7)
        .translate((0, 0, -1))
    )
    cutters = hole if cutters is None else cutters.union(hole)

result = plate.cut(cutters)
model = cq.Assembly()
model.add(result, name="selective_profile_extrude")
