"""pyBOSL2 geometry reference: four short L profiles on the side corners."""

from pybosl2 import Anchor, cuboid

frame = cuboid([120, 80, 60], rounding=8, edges=Anchor.Z).up(30)

def l_profile():
    horizontal = cuboid([32, 4, 16]).translate([12, -2, 0])
    vertical = cuboid([4, 32, 16]).translate([-2, 12, 0])
    return horizontal | vertical

profile = l_profile()
model = frame
for x, y, angle in [(-60, -40, 0), (60, -40, 90), (60, 40, 180), (-60, 40, 270)]:
    model = model | profile.rotate(angle, [0, 0, 1]).translate([x, y, 30])

model.show()
