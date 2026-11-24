"""40 x 30 x 10 mm box centered in XY and based at Z=0."""
from pybosl2 import cuboid

model = cuboid([40, 30, 10]).up(5)
