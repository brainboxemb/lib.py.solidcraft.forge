"""CadQuery reference for a right-side placement separated by a gap."""

import cadquery as cq


gap = 10.0
base_width = 40.0
child_width = 20.0

base = cq.Solid.makeBox(40, 30, 10, cq.Vector(-20, -15, 0))
block = cq.Solid.makeBox(20, 20, 10, cq.Vector(-10, -10, 0))

model = cq.Assembly()
model.add(base, name="base")
model.add(
    block,
    name="block",
    loc=cq.Location((base_width / 2 + child_width / 2 + gap, 0, 0)),
)
