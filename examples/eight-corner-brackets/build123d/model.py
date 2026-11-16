"""build123d reference: two reusable L protectors per vertical frame corner."""
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
            with Locations((12, -2, 8)):
                Box(32, 4, 16)
            with Locations((-2, 12, 8)):
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
        for z in (0, 44):
            with Locations((x, y, z)):
                with Locations(Rot(0, 0, angle)):
                    LProtector()
