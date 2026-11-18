"""pyBOSL2 reference for two independent TOP-to-BOTTOM attachments."""

from pybosl2 import Anchor, cuboid

parent_height = 40.0

left_parent = cuboid([20, 20, parent_height], anchor=Anchor.BOTTOM)
left_marker = cuboid([10, 10, 10], anchor=Anchor.BOTTOM)
left_pair = left_parent.attach(
    Anchor.TOP,
    left_marker,
    child_anchor=Anchor.BOTTOM,
).realize()

right_parent = cuboid([20, 20, parent_height], anchor=Anchor.BOTTOM).right(60)
right_marker = cuboid([10, 10, 10], anchor=Anchor.BOTTOM)
right_pair = right_parent.attach(
    Anchor.TOP,
    right_marker,
    child_anchor=Anchor.BOTTOM,
).realize()

model = left_pair | right_pair
