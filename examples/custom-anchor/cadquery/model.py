"""CadQuery assembly reference for an arm and a marker at its +Y tip datum."""

import cadquery as cq


arm = cq.Solid.makeBox(10, 40, 10, cq.Vector(-5, -20, 0))
marker = cq.Solid.makeBox(10, 10, 10, cq.Vector(-5, -5, -5))

model = cq.Assembly()
model.add(arm, name="arm")
model.add(marker, name="marker", loc=cq.Location((0, 20, 5)))
