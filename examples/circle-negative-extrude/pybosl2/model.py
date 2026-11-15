"""pyBOSL2 reference: use native anchor semantics for a downward cylinder."""

from pybosl2 import Anchor, cyl


model = cyl(
    diameter=20,
    height=30,
    anchor=Anchor.TOP,
)
