"""PythonSCAD geometry reference for preserving an already positioned marker."""

from pythonscad import *

base = cube([40, 30, 10], center=True).up(5)
marker = (
    cube([30, 10, 8], center=True)
    .rotate([0, 0, 90])
    .translate([50, 20, 15])
)
show(base | marker)
