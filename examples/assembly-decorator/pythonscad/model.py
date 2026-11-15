"""PythonSCAD geometry reference for the imported PostPair subassembly."""

from pythonscad import *

post = cube([10, 10, 20], center=True).up(10)
pair = post.left(15) | post.right(15)
show(pair)
