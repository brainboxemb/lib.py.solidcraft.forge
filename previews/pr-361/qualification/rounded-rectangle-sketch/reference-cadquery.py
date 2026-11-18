"""CadQuery reference for a centered rounded pad on a rectangular base."""

import cadquery as cq


base_width = 80.0
base_depth = 60.0
base_height = 5.0
pad_width = 40.0
pad_depth = 30.0
radius = 5.0
pad_height = 8.0

base = cq.Solid.makeBox(
    base_width,
    base_depth,
    base_height,
    cq.Vector(-base_width / 2, -base_depth / 2, 0),
)
pad = (
    cq.Workplane("XY")
    .rect(pad_width - 2 * radius, pad_depth - 2 * radius)
    .offset2D(radius, kind="arc")
    .extrude(pad_height)
    .translate((0, 0, base_height))
)

model = cq.Assembly()
model.add(base, name="base")
model.add(pad, name="pad")
