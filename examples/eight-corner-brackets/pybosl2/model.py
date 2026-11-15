"""pyBOSL2 geometry reference: two L profiles on every vertical corner."""

from pybosl2 import Anchor, cuboid

frame = cuboid([120, 80, 60], rounding=8, edges=Anchor.Z).up(30)

def l_profile():
    horizontal = cuboid([32, 4, 16]).translate([12, -2, 8])
    vertical = cuboid([4, 32, 16]).translate([-2, 12, 8])
    return horizontal | vertical

model = frame
for x, y, angle in [(-60, -40, 0), (60, -40, 90), (60, 40, 180), (-60, 40, 270)]:
    low = l_profile().rotate(angle, [0, 0, 1]).translate([x, y, 0])
    high = l_profile().rotate(angle, [0, 0, 1]).translate([x, y, 44])
    model = model | low | high

model.show()
