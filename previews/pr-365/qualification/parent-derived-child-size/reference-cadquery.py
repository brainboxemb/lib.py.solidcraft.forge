"""CadQuery reference with child dimensions derived from parent values."""

import cadquery as cq


base_width = 120.0
base_depth = 80.0

parent = cq.Solid.makeBox(
    base_width,
    base_depth,
    10,
    cq.Vector(-base_width / 2, -base_depth / 2, 0),
)
child = cq.Solid.makeBox(
    base_width / 2,
    base_depth / 2,
    6,
    cq.Vector(-base_width / 4, -base_depth / 4, 20),
)

model = cq.Assembly()
model.add(parent, name="parent")
model.add(child, name="child")
