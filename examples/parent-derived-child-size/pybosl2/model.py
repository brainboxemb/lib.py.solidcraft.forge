"""pyBOSL2 reference: child dimensions are derived from parent values."""

from pybosl2 import cuboid

base_width = 120.0
base_depth = 80.0

parent = cuboid([base_width, base_depth, 10]).up(5)
child = cuboid([base_width / 2, base_depth / 2, 6]).up(23)
model = parent | child
