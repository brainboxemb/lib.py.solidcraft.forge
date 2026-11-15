"""pyBOSL2 reference for the SimpleBox qualification intent."""

from pybosl2 import cuboid

length = 40.0
width = 30.0
height = 10.0

body = cuboid([length, width, height]).up(height / 2)
body.show()
