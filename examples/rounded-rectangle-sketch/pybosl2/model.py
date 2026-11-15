"""pyBOSL2 reference for the centered rounded pad qualification intent.

The rounded 2D rect defaults to Anchor.CENTER, so centering is semantic rather
than encoded as a numeric (-width/2, -depth/2) offset.
"""

from pybosl2 import Anchor, cuboid, rect

base_width = 80.0
base_depth = 60.0
base_height = 5.0
pad_width = 40.0
pad_depth = 30.0
radius = 5.0
pad_height = 8.0

base = cuboid([base_width, base_depth, base_height]).up(base_height / 2)
profile = rect(
    [pad_width, pad_depth],
    rounding=radius,
    anchor=Anchor.CENTER,
)
pad = profile.linear_extrude(height=pad_height).up(base_height)

(base | pad).show()
