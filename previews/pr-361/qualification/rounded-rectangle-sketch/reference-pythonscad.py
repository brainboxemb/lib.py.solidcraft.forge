"""PythonSCAD reference for the centered rounded pad qualification intent.

No manual half-width/half-depth placement correction is needed: the 2D profile
is centered by construction.
"""

from pythonscad import *

base_width = 80.0
base_depth = 60.0
base_height = 5.0
pad_width = 40.0
pad_depth = 30.0
radius = 5.0
pad_height = 8.0

base = cube([base_width, base_depth, base_height], center=True).up(base_height / 2)
profile = square(
    [pad_width - 2 * radius, pad_depth - 2 * radius],
    center=True,
).offset(r=radius)
pad = profile.linear_extrude(height=pad_height).up(base_height)

model = base | pad
