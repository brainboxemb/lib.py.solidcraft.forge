"""pyBOSL2 CSG reference for the Hole family.

The threaded case is represented by its Ø5 M6 tap-drill envelope; thread
metadata and modeled thread geometry are SolidCraft-native qualification.
"""
from pybosl2 import Anchor, cuboid, cyl

plate = cuboid([120, 40, 12], anchor=Anchor.BOTTOM)

simple = cyl(diameter=6, height=16).translate([-45, 0, 6])

counterbore = (
    cyl(diameter=6, height=16).translate([-15, 0, 6])
    | cyl(diameter=12, height=4, anchor=Anchor.TOP).translate([-15, 0, 12])
)

countersink = (
    cyl(diameter=6, height=16).translate([15, 0, 6])
    | cyl(d1=6, d2=12, height=3, anchor=Anchor.BOTTOM).translate([15, 0, 9])
)

tap_drill = cyl(diameter=5, height=16).translate([45, 0, 6])

model = plate - (simple | counterbore | countersink | tap_drill)
