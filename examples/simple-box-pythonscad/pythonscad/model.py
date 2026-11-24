"""40 x 30 x 10 mm box centered in XY and based at Z=0."""
from pythonscad import cube

model = cube([40, 30, 10], center=True).up(5)
