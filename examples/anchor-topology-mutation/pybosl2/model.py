"""pyBOSL2 geometry reference for the topology-mutation qualification.

pyBOSL2 supplies readable anchors, but this reference does not claim
SolidCraft-style persisted topology identity across a saved-design mutation.
"""

from pybosl2 import cuboid

board = cuboid([40, 20, 20]).up(10)
marker = cuboid([10, 10, 10]).translate([-20, -15, 20])
(board | marker).show()
