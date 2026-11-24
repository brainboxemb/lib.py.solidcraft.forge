"""CadQuery reference for rounded pad plus independent world-plane tunnel."""

import cadquery as cq


base_width = 80.0
base_depth = 60.0
base_height = 5.0
pad_width = 40.0
pad_depth = 30.0
radius = 5.0
pad_height = 8.0
cut_width = 10.0
cut_height = 2.0
cut_y = 22.0
cut_z = 2.5
cut_length = 100.0

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
    .val()
)
body = base.fuse(pad)
cut = cq.Solid.makeBox(
    cut_length,
    cut_width,
    cut_height,
    cq.Vector(-cut_length / 2, cut_y - cut_width / 2, cut_z - cut_height / 2),
)
result = body.cut(cut)

model = cq.Assembly()
model.add(result, name="rounded-pad-world-cut")
