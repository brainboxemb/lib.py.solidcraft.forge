"""PythonSCAD CSG reference for the Hole family.

The threaded case is represented by its Ø5 M6 tap-drill envelope; thread
metadata and modeled thread geometry are SolidCraft-native qualification.
"""
from pythonscad import *

plate = cube([120, 40, 12], center="00-")

simple = cylinder(d=6, h=16).translate([-45, 0, -2])

counterbore = (
    cylinder(d=6, h=16).translate([-15, 0, -2])
    | cylinder(d=12, h=4).translate([-15, 0, 8])
)

countersink = (
    cylinder(d=6, h=16).translate([15, 0, -2])
    | cylinder(d1=6, d2=12, h=3).translate([15, 0, 9])
)

tap_drill = cylinder(d=5, h=16).translate([45, 0, -2])

model = plate - (simple | counterbore | countersink | tap_drill)
