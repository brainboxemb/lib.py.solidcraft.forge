"""CadQuery reference for two repeated parent/marker placements."""

import cadquery as cq


parent_height = 40.0
parent = cq.Solid.makeBox(20, 20, parent_height, cq.Vector(-10, -10, 0))
marker = cq.Solid.makeBox(10, 10, 10, cq.Vector(-5, -5, 0))

model = cq.Assembly()
model.add(parent, name="left_parent")
model.add(parent, name="right_parent", loc=cq.Location((60, 0, 0)))
model.add(marker, name="left_marker", loc=cq.Location((0, 0, parent_height)))
model.add(marker, name="right_marker", loc=cq.Location((60, 0, parent_height)))
