"""pyBOSL2 reference: a centered Ø20 2D profile extruded in negative Z."""

from pybosl2 import circle

profile = circle(diameter=20)
solid = profile.linear_extrude(height=30).down(30)
solid.show()
