"""PythonSCAD reference for the primitive CSG qualification."""

from pythonscad import *

body = sphere(r=20)
body = body | cube([30, 30, 20], center=True).translate([18, 0, 10])

bore = cylinder(d=8, h=60).rotate([0, 90, 0]).translate([-30, 0, 0])
body = body - bore

clip = cube([50, 50, 30], center=True).up(15)
model = body & clip
