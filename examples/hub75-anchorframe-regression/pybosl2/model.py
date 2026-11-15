"""pyBOSL2 reference for the HUB75-like two-sideboard bracket layout."""

from pybosl2 import cuboid


left_board = cuboid([12, 60, 80]).translate([-66, 30, 52])
right_board = cuboid([12, 60, 80]).translate([66, 30, 52])


def l_profile():
    horizontal = cuboid([28, 24, 4]).translate([14, 0, 2])
    vertical = cuboid([4, 24, 28]).translate([-2, 0, -14])
    return horizontal | vertical


model = left_board | right_board
for x, angle in [(-72, 0), (72, 90)]:
    for y in (12, 48):
        model = model | l_profile().rotate(angle, [0, 1, 0]).translate([x, y, 104])

for x, angle in [(72, 180), (-72, 270)]:
    for y in (12, 48):
        model = model | l_profile().rotate(angle, [0, 1, 0]).translate([x, y, 0])
