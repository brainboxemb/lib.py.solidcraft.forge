"""build123d reference: eight reusable trihedral corner protectors."""
from build123d import (
    Align,
    Axis,
    BasePartObject,
    Box,
    BuildPart,
    Locations,
    Mode,
    fillet,
)


class FlightCaseCorner(BasePartObject):
    """Reusable corner protector built in local coordinates."""

    def __init__(self, sx, sy, sz, mode=Mode.ADD):
        def box_bounds(lo, hi):
            size = [hi[i] - lo[i] for i in range(3)]
            center = [(lo[i] + hi[i]) / 2 for i in range(3)]
            with Locations(tuple(center)):
                Box(*size)

        xi, yi, zi = -sx * 20, -sy * 20, sz * 20
        x0, x1 = sorted((0, xi))
        y0, y1 = sorted((0, yi))
        z0, z1 = sorted((0, zi))

        with BuildPart() as corner:
            box_bounds(
                (x0, y0, -4 if sz > 0 else 0),
                (x1, y1, 0 if sz > 0 else 4),
            )
            box_bounds(
                (x0, min(0, sy * 4), z0),
                (x1, max(0, sy * 4), z1),
            )
            box_bounds(
                (min(0, sx * 4), y0, z0),
                (max(0, sx * 4), y1, z1),
            )

        super().__init__(part=corner.part, mode=mode)


bottom = (Align.CENTER, Align.CENTER, Align.MIN)

with BuildPart() as model:
    Box(120, 80, 60, align=bottom)
    fillet(model.edges().filter_by(Axis.Z), radius=8)

    for x, y, z, sx, sy, sz in [
        (-60, -40, 0, -1, -1, 1),
        (60, -40, 0, 1, -1, 1),
        (60, 40, 0, 1, 1, 1),
        (-60, 40, 0, -1, 1, 1),
        (-60, -40, 60, -1, -1, -1),
        (60, -40, 60, 1, -1, -1),
        (60, 40, 60, 1, 1, -1),
        (-60, 40, 60, -1, 1, -1),
    ]:
        with Locations((x, y, z)):
            FlightCaseCorner(sx, sy, sz)
