"""CadQuery reference for a marker touching the front/top/right corner."""

import cadquery as cq


base = cq.Solid.makeBox(40, 30, 20, cq.Vector(-20, -15, 0))
marker = cq.Solid.makeBox(10, 10, 10, cq.Vector(-5, -5, -5))

model = cq.Assembly()
model.add(base, name="base")
model.add(marker, name="marker", loc=cq.Location((15, -20, 15)))
