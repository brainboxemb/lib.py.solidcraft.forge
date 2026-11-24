"""pyBOSL2 reference for rounded pad plus world-plane Boolean cut."""

from pybosl2 import Anchor, cuboid, rect

base_width = 80.0
base_depth = 60.0
base_height = 5.0
pad_width = 40.0
pad_depth = 30.0
radius = 5.0
pad_height = 8.0
cut_width = 10.0
cut_height = 2.0
cut_y = 22.0
cut_z = 2.5
cut_length = 100.0

base = cuboid([base_width, base_depth, base_height]).up(base_height / 2)
profile = rect(
    [pad_width, pad_depth],
    rounding=radius,
    anchor=Anchor.CENTER,
)
pad = profile.linear_extrude(height=pad_height).up(base_height)
cut = cuboid([cut_length, cut_width, cut_height]).translate(
    [0, cut_y, cut_z]
)

model = (base | pad) - cut
