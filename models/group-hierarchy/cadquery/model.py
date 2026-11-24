"""CadQuery assembly reference for grouped panels plus a separate frame.

This compares nested assembly intent and visible geometry. SolidCraft BOM
persistence remains native Forge qualification evidence.
"""

import cadquery as cq


panel = cq.Solid.makeBox(
    10,
    2,
    20,
    cq.Vector(-5, -1, 0),
)
frame = cq.Solid.makeBox(
    35,
    10,
    40,
    cq.Vector(-17.5, -5, 0),
)

panel_group = cq.Assembly(name="PanelGroup")
panel_group.add(panel, name="panel_1", loc=cq.Location((0, 0, 0)))
panel_group.add(panel, name="panel_2", loc=cq.Location((11, 0, 0)))

model = cq.Assembly()
model.add(panel_group, name="panels")
model.add(frame, name="frame", loc=cq.Location((0, 20, 0)))
