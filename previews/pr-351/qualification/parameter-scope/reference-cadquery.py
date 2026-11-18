"""CadQuery geometry reference for explicit parameter-scope qualification.

CadQuery evaluates these Python values directly. Saved SolidCraft parameter
publication and mutation remain native Forge qualification evidence.
"""

import cadquery as cq


shared_width = 80.0


def panel(width):
    return cq.Solid.makeBox(
        width,
        20,
        10,
        cq.Vector(-width / 2, -10, 0),
    )


model = cq.Assembly()
model.add(panel(40), name="fixed_40", loc=cq.Location((0, 0, 0)))
model.add(panel(60), name="fixed_60", loc=cq.Location((100, 0, 0)))
model.add(panel(shared_width), name="shared_1", loc=cq.Location((220, 0, 0)))
model.add(panel(shared_width), name="shared_2", loc=cq.Location((340, 0, 0)))
model.add(panel(shared_width / 2), name="derived", loc=cq.Location((460, 0, 0)))
