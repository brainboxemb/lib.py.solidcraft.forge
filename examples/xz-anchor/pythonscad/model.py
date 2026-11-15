"""PythonSCAD geometry reference for the XZ-board and two front corner markers.

Forge's case specifically qualifies an explicit XZ Sketch and associative
corner attachments.
"""

from pythonscad import *

board = cube([40, 12, 20], center=True).translate([0, 6, 10])
right_marker = cube([10, 10, 10], center=True).translate([15, -5, 15])
left_marker = cube([10, 10, 10], center=True).translate([-15, -5, 15])
show(board | right_marker | left_marker)
