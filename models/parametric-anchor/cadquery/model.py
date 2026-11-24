"""CadQuery reference for a block placed against the base's right face."""

import cadquery as cq


base_width = 40.0
child_width = 20.0

base = cq.Solid.makeBox(base_width, 30, 10, cq.Vector(-base_width / 2, -15, 0))
block = cq.Solid.makeBox(child_width, 20, 10, cq.Vector(-child_width / 2, -10, 0))

model = cq.Assembly()
model.add(base, name="base")
model.add(
    block,
    name="block",
    loc=cq.Location((base_width / 2 + child_width / 2, 0, 0)),
)
