"""CadQuery reference for a stepped circular body."""

import cadquery as cq

disc = cq.Workplane("XY").circle(50).extrude(10)
hub = cq.Workplane("XY").workplane(offset=10).circle(22).extrude(16)
result = disc.union(hub)

model = cq.Assembly()
model.add(result, name="round_top_sketch")
