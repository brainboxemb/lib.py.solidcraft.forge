"""CadQuery assembly reference preserving an already authored marker pose.

The Assembly Location expresses the occurrence pose independently of any
constraint. Forge additionally qualifies the persisted SolidCraft as-built
relationship.
"""

import cadquery as cq


base = cq.Solid.makeBox(40, 30, 10, cq.Vector(-20, -15, 0))
marker = cq.Solid.makeBox(30, 10, 8, cq.Vector(-15, -5, 0))
marker_pose = (
    cq.Location((50, 20, 15))
    * cq.Location(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 90)
)

model = cq.Assembly()
model.add(base, name="base")
model.add(marker, name="marker", loc=marker_pose)
