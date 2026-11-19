"""CadQuery assembly reference for an assembly-owned inspection datum layout."""

import cadquery as cq


base = cq.Solid.makeBox(40, 30, 20, cq.Vector(-20, -15, 0))
small = cq.Solid.makeBox(10, 10, 10, cq.Vector(-5, -5, -5))

model = cq.Assembly()
model.add(base, name="base")
model.add(small, name="companion", loc=cq.Location((70, 0, 5)))
model.add(small, name="marker", loc=cq.Location((15, -20, 15)))
