"""CadQuery geometry reference for a corner marker with a planar shift.

The final Location compares the visible local-offset result. Forge separately
qualifies persisted local joint-frame mutation in SolidCraft.
"""

import cadquery as cq


shift = 5.0
base = cq.Solid.makeBox(40, 30, 20, cq.Vector(-20, -15, 0))
marker = cq.Solid.makeBox(10, 10, 10, cq.Vector(-5, -5, -5))

model = cq.Assembly()
model.add(base, name="base")
model.add(marker, name="marker", loc=cq.Location((15, -20, 20)))
