"""CadQuery reference for a centered diameter-20 profile extruded to -Z."""

import cadquery as cq


solid = cq.Workplane("XY").circle(10).extrude(-30)

model = cq.Assembly()
model.add(solid, name="negative_extrude")
