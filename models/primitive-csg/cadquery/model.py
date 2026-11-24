"""CadQuery reference for primitive union, difference and intersection."""

import cadquery as cq


sphere = cq.Solid.makeSphere(20)
box = cq.Solid.makeBox(30, 30, 20, cq.Vector(3, -15, 0))
body = sphere.fuse(box)

bore = cq.Workplane("YZ").circle(4).extrude(60, both=True).val()
body = body.cut(bore)

clip = cq.Solid.makeBox(50, 50, 30, cq.Vector(-25, -25, 0))
result = body.intersect(clip)

model = cq.Assembly()
model.add(result, name="csg")
