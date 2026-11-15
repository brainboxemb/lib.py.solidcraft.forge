"""CadQuery reference for two independently positioned block occurrences.

This reference compares visible assembly/location geometry only. SolidCraft
saved-design parameter mutation remains native Forge qualification evidence.
"""

import cadquery as cq


block = cq.Solid.makeBox(
    20,
    20,
    10,
    cq.Vector(-10, -10, 0),
)

model = cq.Assembly()
model.add(block, name="fixed", loc=cq.Location((0, 0, 0)))
model.add(block, name="placed", loc=cq.Location((40, 0, 0)))
