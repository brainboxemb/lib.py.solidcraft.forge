"""pyBOSL2 reference: a diameter-20 cylinder with its TOP anchored at Z=0."""

from pybosl2 import Anchor, cyl


model = cyl(diameter=20, height=30, anchor=Anchor.TOP)
