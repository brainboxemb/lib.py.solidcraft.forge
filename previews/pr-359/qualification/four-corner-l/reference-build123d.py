"""build123d reference: four reusable L protectors around a rounded frame."""
from build123d import (
    Align,
    Axis,
    BasePartObject,
    Box,
    BuildPart,
    Locations,
    Mode,
    Rot,
    fillet,
)


class LProtector(BasePartObject):
    def __init__(self, mode=Mode.ADD):
        with BuildPart() as profile:
            with Locations((12, -2, 0)):
                Box(32, 4, 16)
            with Locations((-2, 12, 0)):
                Box(4, 32, 16)
        super().__init__(part=profile.part, mode=mode)


bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    Box(120, 80, 60, align=bottom)
    fillet(model.edges().filter_by(Axis.Z), radius=8)

    for x, y, angle in [
        (-60, -40, 0),
        (60, -40, 90),
        (60, 40, 180),
        (-60, 40, 270),
    ]:
        with Locations((x, y, 30)):
            with Locations(Rot(0, 0, angle)):
                LProtector()
