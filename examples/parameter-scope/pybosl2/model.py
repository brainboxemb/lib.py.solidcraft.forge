"""pyBOSL2 geometry reference for Forge parameter-scope qualification.

The repeated Python value shows the same visible intent; it is not a reference
for SolidCraft's editable parameter-binding persistence.
"""

from pybosl2 import cuboid

shared_width = 80.0

def panel(width):
    return cuboid([width, 20, 10]).up(5)

model = (
    panel(40)
    | panel(60).right(100)
    | panel(shared_width).right(220)
    | panel(shared_width).right(340)
    | panel(shared_width / 2).right(460)
)
model.show()
