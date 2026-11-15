"""CadQuery reference for the HUB75-like two-sideboard bracket layout."""

import cadquery as cq


left_board = cq.Solid.makeBox(12, 60, 80, cq.Vector(-72, 0, 12))
right_board = cq.Solid.makeBox(12, 60, 80, cq.Vector(60, 0, 12))

horizontal = cq.Solid.makeBox(28, 24, 12, cq.Vector(0, -12, 0))
vertical = cq.Solid.makeBox(12, 24, 28, cq.Vector(-12, -12, -28))
profile = horizontal.fuse(vertical)

model = cq.Assembly()
model.add(left_board, name="left_board")
model.add(right_board, name="right_board")

placements = [
    ("top_left_front", -72, 12, 104, 0),
    ("top_left_rear", -72, 48, 104, 0),
    ("top_right_front", 72, 12, 104, 90),
    ("top_right_rear", 72, 48, 104, 90),
    ("bottom_right_front", 72, 12, 0, 180),
    ("bottom_right_rear", 72, 48, 0, 180),
    ("bottom_left_front", -72, 12, 0, 270),
    ("bottom_left_rear", -72, 48, 0, 270),
]
for name, x, y, z, angle in placements:
    rotation = cq.Location(
        cq.Vector(0, 0, 0),
        cq.Vector(0, 1, 0),
        angle,
    )
    model.add(
        profile,
        name=name,
        loc=cq.Location((x, y, z)) * rotation,
    )
