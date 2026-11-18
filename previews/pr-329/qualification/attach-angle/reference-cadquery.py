"""CadQuery assembly reference for a 90-degree clocked top attachment."""

import cadquery as cq


base = cq.Solid.makeBox(60, 60, 10, cq.Vector(-30, -30, 0))
arm = cq.Solid.makeBox(30, 10, 6, cq.Vector(-15, -5, 0))
clocked = cq.Location(cq.Vector(0, 0, 10), cq.Vector(0, 0, 1), 90)

model = cq.Assembly()
model.add(base, name="base")
model.add(arm, name="arm", loc=clocked)
