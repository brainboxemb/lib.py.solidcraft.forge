"""Independent geometry facts shared by qualification checks.

These values describe the intended model, not a SolidCraft result.  Reference
libraries and visual/native checks may consume the same facts so one
implementation cannot silently become its own expected result.
"""

from __future__ import annotations

import math


def _through_probes(points, z_values, distance):
    return [
        {
            "label": f"{label} at z={z:g}",
            "point": [x, y, z],
            "distance_mm": distance,
            "tolerance_mm": 0.30,
        }
        for label, x, y in points
        for z in z_values
    ]


_RECTANGULAR_SLOT_CENTERS = [
    (f"slot {column + 1},{row + 1}", x, y)
    for row, y in enumerate((0.0, 28.0))
    for column, x in enumerate((0.0, 24.0, 48.0))
]

_SLOT_FAMILY_CENTERS = [
    ("center-to-center slot", -50.0, -35.0),
    ("overall slot", 5.0, -35.0),
    ("center-point slot", 55.0, -35.0),
    ("three-point arc slot", -35.0, 38.0),
    (
        "center arc slot",
        40.0 + 12.0 * math.cos(math.radians(60.0)),
        25.0 + 12.0 * math.sin(math.radians(60.0)),
    ),
]


GEOMETRY_CONTRACTS = {
    "anchored-holes": {
        "volume_mm3": 100.0 * 60.0 * 10.0 - 2.0 * math.pi * 4.0**2 * 10.0,
        # PythonSCAD/pyBOSL2 export circular holes with coarser STL facets.
        # Their measured volume differs by about 39 mm3 while the 3D wall
        # probes below still enforce radius, position and through depth.
        "volume_tolerance_mm3": 50.0,
        "watertight": True,
        "surface_distance_probes": _through_probes(
            [
                ("front hole", 50.0, 10.0),
                ("rear hole", 50.0, 50.0),
            ],
            (1.0, 5.0, 9.0),
            4.0,
        ),
    },
    "rectangular-pattern": {
        "volume_mm3": (
            120.0 * 80.0 * 4.0
            - 6.0 * (10.0 * 6.0 + math.pi * 3.0**2) * 4.0
        ),
        # PythonSCAD/pyBOSL2 use coarse circular tessellation. Their six-slot
        # volume differs by about 44 mm3, while the 18 independent 3D probes
        # still enforce every slot centre, width and through depth.
        "volume_tolerance_mm3": 55.0,
        "watertight": True,
        "surface_distance_probes": _through_probes(
            _RECTANGULAR_SLOT_CENTERS,
            (0.5, 2.0, 3.5),
            3.0,
        ),
    },
    "slot-family": {
        "volume_mm3": (
            160.0 * 120.0 * 5.0
            - 5.0
            * (
                (20.0 * 8.0 + math.pi * 4.0**2)
                + (22.0 * 8.0 + math.pi * 4.0**2)
                + (20.0 * 8.0 + math.pi * 4.0**2)
                + (
                    15.153846153846153
                    * math.radians(163.65753288010052)
                    * 8.0
                    + math.pi * 4.0**2
                )
                + (
                    12.0 * math.radians(120.0) * 8.0
                    + math.pi * 4.0**2
                )
            )
        ),
        # Coarse PythonSCAD/pyBOSL2 arc tessellation differs by about 49 mm3.
        # The 15 independent 3D probes remain the stricter size/position/depth
        # check for the five individual slots.
        "volume_tolerance_mm3": 55.0,
        "watertight": True,
        "surface_distance_probes": _through_probes(
            _SLOT_FAMILY_CENTERS,
            (0.5, 2.5, 4.5),
            4.0,
        ),
    },
}


def geometry_contract(slug: str) -> dict | None:
    """Return independent measurable geometry facts for one case."""
    return GEOMETRY_CONTRACTS.get(slug)
