"""Shared machine-readable geometry and proof contracts for qualification.

This file is the source of truth for baseline geometry. Native Q4 checks,
independent reference checks and Q6 goal rendering all consume the same
geometry contract. SolidCraft-only history, relationship and mutation
expectations are kept in a separate section of the proof contract.
"""

from __future__ import annotations

import math

from qualification.cases import QUALIFICATION_CASES


EXPECTED_BOUNDS = {
    "simple-box": [
        {"label": "SimpleBox", "min": [-20, -15, 0], "max": [20, 15, 10]},
    ],
    "anchored-holes": [
        {"label": "AnchoredHoles", "min": [0, 0, 0], "max": [100, 60, 10]},
    ],
    "parameter-scope": [
        {"label": "local", "min": [-20, -10, 0], "max": [20, 10, 10]},
        {"label": "override", "min": [70, -10, 0], "max": [130, 10, 10]},
        {"label": "shared_a", "min": [180, -10, 0], "max": [260, 10, 10]},
        {"label": "shared_b", "min": [300, -10, 0], "max": [380, 10, 10]},
        {"label": "derived", "min": [440, -10, 0], "max": [480, 10, 10]},
    ],
    "parent-derived-child-size": [
        {"label": "ParentBlock", "min": [-60, -40, 0], "max": [60, 40, 10]},
        {"label": "DerivedChild", "min": [-30, -20, 20], "max": [30, 20, 26]},
    ],
    "components": [
        {"label": "left", "min": [-20, -15, 0], "max": [20, 15, 10]},
        {"label": "right", "min": [20, -15, 0], "max": [60, 15, 10]},
    ],
    "repeated-parent-attachments": [
        {"label": "left Parent", "min": [-10, -10, 0], "max": [10, 10, 40]},
        {"label": "right Parent", "min": [50, -10, 0], "max": [70, 10, 40]},
        {"label": "left Marker", "min": [-5, -5, 40], "max": [5, 5, 50]},
        {"label": "right Marker", "min": [55, -5, 40], "max": [65, 5, 50]},
    ],
    "assembly-decorator": [
        {"label": "left Post", "min": [-20, -5, 0], "max": [-10, 5, 20]},
        {"label": "right Post", "min": [10, -5, 0], "max": [20, 5, 20]},
    ],
    "group-hierarchy": [
        {"label": "left Panel", "min": [-5, -1, 0], "max": [5, 1, 20]},
        {"label": "right Panel", "min": [6, -1, 0], "max": [16, 1, 20]},
        {"label": "root Frame", "min": [-17.5, 15, 0], "max": [17.5, 25, 40]},
    ],
    "attach-angle": [
        {"label": "Base", "min": [-30, -30, 0], "max": [30, 30, 10]},
        {"label": "Arm", "min": [-5, -15, 10], "max": [5, 15, 16]},
    ],
    "parametric-attach": [
        {"label": "Base", "min": [-20, -15, 0], "max": [20, 15, 10]},
        {"label": "Block", "min": [30, -10, 0], "max": [50, 10, 10]},
    ],
    "parametric-offset": [
        {"label": "Base", "min": [-20, -15, 0], "max": [20, 15, 20]},
        {"label": "Marker", "min": [10, -25, 15], "max": [20, -15, 25]},
    ],
    "parametric-anchor": [
        {"label": "Base", "min": [-20, -15, 0], "max": [20, 15, 10]},
        {"label": "Block", "min": [20, -10, 0], "max": [40, 10, 10]},
    ],
    "corner-anchor": [
        {"label": "Base", "min": [-20, -15, 0], "max": [20, 15, 20]},
        {"label": "Marker", "min": [10, -25, 10], "max": [20, -15, 20]},
    ],
    "anchor-topology-mutation": [
        {"label": "Board", "min": [-20, -10, 0], "max": [20, 10, 20]},
        {"label": "Marker", "min": [-25, -20, 15], "max": [-15, -10, 25]},
    ],
    "assembly-owned-anchor": [
        {"label": "Base", "min": [-20, -15, 0], "max": [20, 15, 20]},
        {"label": "Companion", "min": [65, -5, 0], "max": [75, 5, 10]},
        {"label": "Marker", "min": [10, -25, 10], "max": [20, -15, 20]},
    ],
    "four-corner-l": [
        {"label": "FrameBlock", "min": [-60, -40, 0], "max": [60, 40, 60]},
        {"label": "front-left", "min": [-64, -44, 22], "max": [-32, -12, 38]},
        {"label": "front-right", "min": [32, -44, 22], "max": [64, -12, 38]},
        {"label": "rear-right", "min": [32, 12, 22], "max": [64, 44, 38]},
        {"label": "rear-left", "min": [-64, 12, 22], "max": [-32, 44, 38]},
    ],
    "eight-flightcase-corners": [
        {"label": "CaseBlock", "min": [-60, -40, 0], "max": [60, 40, 60]},
        {"label": "front bottom-left", "min": [-64, -44, -4], "max": [-40, -20, 20]},
        {"label": "front bottom-right", "min": [40, -44, -4], "max": [64, -20, 20]},
        {"label": "rear bottom-right", "min": [40, 20, -4], "max": [64, 44, 20]},
        {"label": "rear bottom-left", "min": [-64, 20, -4], "max": [-40, 44, 20]},
        {"label": "front top-left", "min": [-64, -44, 40], "max": [-40, -20, 64]},
        {"label": "front top-right", "min": [40, -44, 40], "max": [64, -20, 64]},
        {"label": "rear top-right", "min": [40, 20, 40], "max": [64, 44, 64]},
        {"label": "rear top-left", "min": [-64, 20, 40], "max": [-40, 44, 64]},
    ],
    "eight-corner-brackets": [
        {"label": "FrameBlock", "min": [-60, -40, 0], "max": [60, 40, 60]},
        {"label": "front-left bottom", "min": [-64, -44, 0], "max": [-32, -12, 16]},
        {"label": "front-left top", "min": [-64, -44, 44], "max": [-32, -12, 60]},
        {"label": "front-right bottom", "min": [32, -44, 0], "max": [64, -12, 16]},
        {"label": "front-right top", "min": [32, -44, 44], "max": [64, -12, 60]},
        {"label": "rear-right bottom", "min": [32, 12, 0], "max": [64, 44, 16]},
        {"label": "rear-right top", "min": [32, 12, 44], "max": [64, 44, 60]},
        {"label": "rear-left bottom", "min": [-64, 12, 0], "max": [-32, 44, 16]},
        {"label": "rear-left top", "min": [-64, 12, 44], "max": [-32, 44, 60]},
    ],
    "xz-anchor": [
        {"label": "Board", "min": [-20, 0, 0], "max": [20, 12, 20]},
        {"label": "right Marker", "min": [10, -10, 10], "max": [20, 0, 20]},
        {"label": "left Marker", "min": [-20, -10, 10], "max": [-10, 0, 20]},
    ],
    "circle-negative-extrude": [
        {"label": "NegativeCircleExtrude", "min": [-10, -10, -30], "max": [10, 10, 0]},
    ],
    "sketch-pattern-mirror": [
        {"label": "SketchPatternMirror", "min": [-120, -80, 0], "max": [120, 80, 5]},
    ],
    "rectangular-pattern": [
        {"label": "RectangularPattern", "min": [-60, -40, 0], "max": [60, 40, 4]},
    ],
    "slot-family": [
        {"label": "SlotFamily", "min": [-80, -60, 0], "max": [80, 60, 5]},
    ],
    "rounded-rectangle-sketch": [
        {"label": "RoundedRectangleSketch", "min": [-40, -30, 0], "max": [40, 30, 13]},
    ],
    "primitive-csg": [
        # The X-axis Ø8 bore removes the sphere's exact X=-20 extremum.
        # Remaining sphere/bore intersection: -sqrt(20^2 - 4^2).
        {"label": "PrimitiveCsg", "min": [-19.595917942265423, -20, 0], "max": [25, 20, 20]},
    ],
    "bracket": [
        {"label": "Bracket", "min": [0, -12, -40], "max": [40, 12, 0]},
    ],
}

# Visual overlays may use a more detailed decomposition than the Q4 outer
# bounds. In particular an L-profile can be mirrored/rotated incorrectly while
# retaining the same overall bounding box, so draw its two arms separately.
EXPECTED_VISUAL_BOXES = dict(EXPECTED_BOUNDS)

# Visual decomposition may be more detailed than the final joined body bounds.
# The rounded-rectangle case is one native body, but its front projection is a
# wide 5 mm base with a narrower 8 mm pad on top.
EXPECTED_VISUAL_BOXES["rounded-rectangle-sketch"] = [
    {"label": "Base plate", "min": [-40, -30, 0], "max": [40, 30, 5]},
    {"label": "Rounded pad", "min": [-20, -15, 5], "max": [20, 15, 13]},
]


EXPECTED_VISUAL_BOXES["bracket"] = [
    {"label": "arm X", "min": [0, -12, -12], "max": [40, 12, 0]},
    {"label": "arm Z", "min": [0, -12, -40], "max": [12, 12, 0]},
]

EXPECTED_VISUAL_BOXES["four-corner-l"] = [
    {"label": "FrameBlock", "min": [-60, -40, 0], "max": [60, 40, 60]},

    {"label": "FL front arm", "min": [-60, -44, 22], "max": [-32, -40, 38]},
    {"label": "FL left arm", "min": [-64, -40, 22], "max": [-60, -12, 38]},
    {"label": "FR front arm", "min": [32, -44, 22], "max": [60, -40, 38]},
    {"label": "FR right arm", "min": [60, -40, 22], "max": [64, -12, 38]},
    {"label": "RR rear arm", "min": [32, 40, 22], "max": [60, 44, 38]},
    {"label": "RR right arm", "min": [60, 12, 22], "max": [64, 40, 38]},
    {"label": "RL rear arm", "min": [-60, 40, 22], "max": [-32, 44, 38]},
    {"label": "RL left arm", "min": [-64, 12, 22], "max": [-60, 40, 38]},
]

EXPECTED_VISUAL_BOXES["eight-flightcase-corners"] = [
    {"label": "CaseBlock", "min": [-60, -40, 0], "max": [60, 40, 60]},

    {"label": "FBL bottom plate", "min": [-60, -40, -4], "max": [-40, -20, 0]},
    {"label": "FBL front plate", "min": [-60, -44, 0], "max": [-40, -40, 20]},
    {"label": "FBL left plate", "min": [-64, -40, 0], "max": [-60, -20, 20]},

    {"label": "FBR bottom plate", "min": [40, -40, -4], "max": [60, -20, 0]},
    {"label": "FBR front plate", "min": [40, -44, 0], "max": [60, -40, 20]},
    {"label": "FBR right plate", "min": [60, -40, 0], "max": [64, -20, 20]},

    {"label": "RBR bottom plate", "min": [40, 20, -4], "max": [60, 40, 0]},
    {"label": "RBR rear plate", "min": [40, 40, 0], "max": [60, 44, 20]},
    {"label": "RBR right plate", "min": [60, 20, 0], "max": [64, 40, 20]},

    {"label": "RBL bottom plate", "min": [-60, 20, -4], "max": [-40, 40, 0]},
    {"label": "RBL rear plate", "min": [-60, 40, 0], "max": [-40, 44, 20]},
    {"label": "RBL left plate", "min": [-64, 20, 0], "max": [-60, 40, 20]},

    {"label": "FTL top plate", "min": [-60, -40, 60], "max": [-40, -20, 64]},
    {"label": "FTL front plate", "min": [-60, -44, 40], "max": [-40, -40, 60]},
    {"label": "FTL left plate", "min": [-64, -40, 40], "max": [-60, -20, 60]},

    {"label": "FTR top plate", "min": [40, -40, 60], "max": [60, -20, 64]},
    {"label": "FTR front plate", "min": [40, -44, 40], "max": [60, -40, 60]},
    {"label": "FTR right plate", "min": [60, -40, 40], "max": [64, -20, 60]},

    {"label": "RTR top plate", "min": [40, 20, 60], "max": [60, 40, 64]},
    {"label": "RTR rear plate", "min": [40, 40, 40], "max": [60, 44, 60]},
    {"label": "RTR right plate", "min": [60, 20, 40], "max": [64, 40, 60]},

    {"label": "RTL top plate", "min": [-60, 20, 60], "max": [-40, 40, 64]},
    {"label": "RTL rear plate", "min": [-60, 40, 40], "max": [-40, 44, 60]},
    {"label": "RTL left plate", "min": [-64, 20, 40], "max": [-60, 40, 60]},
]

EXPECTED_VISUAL_BOXES["eight-corner-brackets"] = [
    {"label": "FrameBlock", "min": [-60, -40, 0], "max": [60, 40, 60]},

    {"label": "FL bottom front arm", "min": [-60, -44, 0], "max": [-32, -40, 16]},
    {"label": "FL bottom left arm", "min": [-64, -40, 0], "max": [-60, -12, 16]},
    {"label": "FR bottom front arm", "min": [32, -44, 0], "max": [60, -40, 16]},
    {"label": "FR bottom right arm", "min": [60, -40, 0], "max": [64, -12, 16]},
    {"label": "RR bottom rear arm", "min": [32, 40, 0], "max": [60, 44, 16]},
    {"label": "RR bottom right arm", "min": [60, 12, 0], "max": [64, 40, 16]},
    {"label": "RL bottom rear arm", "min": [-60, 40, 0], "max": [-32, 44, 16]},
    {"label": "RL bottom left arm", "min": [-64, 12, 0], "max": [-60, 40, 16]},

    {"label": "FL top front arm", "min": [-60, -44, 44], "max": [-32, -40, 60]},
    {"label": "FL top left arm", "min": [-64, -40, 44], "max": [-60, -12, 60]},
    {"label": "FR top front arm", "min": [32, -44, 44], "max": [60, -40, 60]},
    {"label": "FR top right arm", "min": [60, -40, 44], "max": [64, -12, 60]},
    {"label": "RR top rear arm", "min": [32, 40, 44], "max": [60, 44, 60]},
    {"label": "RR top right arm", "min": [60, 12, 44], "max": [64, 40, 60]},
    {"label": "RL top rear arm", "min": [-60, 40, 44], "max": [-32, 44, 60]},
    {"label": "RL top left arm", "min": [-64, 12, 44], "max": [-60, 40, 60]},

]



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


_SKETCH_PATTERN_HOLE_CENTERS = [
    (f"hole {column + 1},{row + 1}", x, y)
    for row, y in enumerate((-45.0, 45.0))
    for column, x in enumerate((-60.0, -35.0, -10.0, 15.0))
]

_SKETCH_PATTERN_SLOT_CENTERS = [
    (f"slot {column + 1},{row + 1}", x, y)
    for row, y in enumerate((-20.0, 20.0))
    for column, x in enumerate((-80.0, -30.0, 30.0, 80.0))
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


DEFAULT_REQUIRED_VISUAL_VIEWS = ("iso", "front", "right")

REQUIRED_VISUAL_VIEWS = {
    case["slug"]: DEFAULT_REQUIRED_VISUAL_VIEWS
    for case in QUALIFICATION_CASES
}
REQUIRED_VISUAL_VIEWS.update({
    # Hole profiles are clearest normal to the plate; the right view separates
    # both Y positions and exposes the full Z depth.
    "anchored-holes": ("top", "right", "iso"),
    # Pattern/slot cases need a normal profile view plus an orthogonal view
    # that makes the through-cut depth visible.
    "sketch-pattern-mirror": ("top", "front", "iso"),
    "rectangular-pattern": ("top", "right", "iso"),
    "slot-family": ("top", "front", "iso"),
    "rounded-rectangle-sketch": ("top", "front", "iso"),
})


def _through_hole(label, x, y, diameter, z_min, z_max):
    return {
        "type": "through_hole",
        "label": label,
        "center": [float(x), float(y)],
        "diameter": float(diameter),
        "z": [float(z_min), float(z_max)],
    }


def _through_slot(label, centerline, width, z_min, z_max):
    return {
        "type": "through_slot",
        "label": label,
        "centerline": [
            [float(point[0]), float(point[1])]
            for point in centerline
        ],
        "width": float(width),
        "z": [float(z_min), float(z_max)],
    }


def _sample_arc(center, start, sweep_degrees, segments=20):
    cx, cy = center
    sx, sy = start
    radius = math.hypot(sx - cx, sy - cy)
    start_angle = math.atan2(sy - cy, sx - cx)
    sweep = math.radians(sweep_degrees)
    return [
        [
            cx + radius * math.cos(start_angle + sweep * index / segments),
            cy + radius * math.sin(start_angle + sweep * index / segments),
        ]
        for index in range(segments + 1)
    ]


def _sample_three_point_arc(p0, pm, p1, segments=20):
    x1, y1 = p0
    x2, y2 = pm
    x3, y3 = p1
    denominator = 2.0 * (
        x1 * (y2 - y3)
        + x2 * (y3 - y1)
        + x3 * (y1 - y2)
    )
    if abs(denominator) < 1e-12:
        raise ValueError("three-point visual slot arc is collinear")

    ux = (
        (x1 * x1 + y1 * y1) * (y2 - y3)
        + (x2 * x2 + y2 * y2) * (y3 - y1)
        + (x3 * x3 + y3 * y3) * (y1 - y2)
    ) / denominator
    uy = (
        (x1 * x1 + y1 * y1) * (x3 - x2)
        + (x2 * x2 + y2 * y2) * (x1 - x3)
        + (x3 * x3 + y3 * y3) * (x2 - x1)
    ) / denominator

    center = (ux, uy)
    a0 = math.atan2(y1 - uy, x1 - ux)
    am = math.atan2(y2 - uy, x2 - ux)
    a1 = math.atan2(y3 - uy, x3 - ux)

    def ccw(a, b):
        return (b - a) % (2.0 * math.pi)

    forward = ccw(a0, a1)
    if ccw(a0, am) <= forward + 1e-9:
        sweep = forward
    else:
        sweep = -ccw(a1, a0)

    return _sample_arc(
        center,
        p0,
        math.degrees(sweep),
        segments=segments,
    )


EXPECTED_VISUAL_FEATURES = {
    case["slug"]: []
    for case in QUALIFICATION_CASES
}

EXPECTED_VISUAL_FEATURES["anchored-holes"] = [
    _through_hole("front hole Ø8 through", 50, 10, 8, 0, 10),
    _through_hole("rear hole Ø8 through", 50, 50, 8, 0, 10),
]

EXPECTED_VISUAL_FEATURES["sketch-pattern-mirror"] = [
    *[
        _through_hole(label, x, y, 8.0, 0.0, 5.0)
        for label, x, y in _SKETCH_PATTERN_HOLE_CENTERS
    ],
    *[
        _through_slot(
            label,
            ((x - 10.0, y), (x + 10.0, y)),
            8.0,
            0.0,
            5.0,
        )
        for label, x, y in _SKETCH_PATTERN_SLOT_CENTERS
    ],
]

EXPECTED_VISUAL_FEATURES["rectangular-pattern"] = [
    _through_slot(
        label,
        ((x - 5.0, y), (x + 5.0, y)),
        6.0,
        0.0,
        4.0,
    )
    for label, x, y in _RECTANGULAR_SLOT_CENTERS
]

EXPECTED_VISUAL_FEATURES["slot-family"] = [
    _through_slot(
        "center-to-center slot",
        ((-60, -35), (-40, -35)),
        8,
        0,
        5,
    ),
    _through_slot(
        "overall slot",
        ((-6, -35), (16, -35)),
        8,
        0,
        5,
    ),
    _through_slot(
        "center-point slot",
        ((45, -35), (65, -35)),
        8,
        0,
        5,
    ),
    _through_slot(
        "three-point arc slot",
        _sample_three_point_arc(
            (-50, 25),
            (-35, 38),
            (-20, 25),
        ),
        8,
        0,
        5,
    ),
    _through_slot(
        "center arc slot",
        _sample_arc((40, 25), (52, 25), 120),
        8,
        0,
        5,
    ),
]


_BOUNDS_ASSESSMENTS = {
    "simple-box": {
        "sufficient": True,
        "reason": "This case is one rectangular solid. Its body size fully describes the visible geometry. The saved SolidCraft model is checked separately to confirm that the dimensions remain editable parameters.",
    },
    "anchored-holes": {
        "sufficient": False,
        "reason": "The holes do not change the outer plate bounds. Volume and 3D hole-wall probes are required.",
    },
    "parameter-scope": {
        "sufficient": True,
        "reason": "The body sizes and positions describe the visible result. The saved SolidCraft model is checked separately to confirm that shared parameters are reused instead of duplicated.",
    },
    "parent-derived-child-size": {
        "sufficient": True,
        "reason": "The geometry is two rectangular bodies whose declared sizes and positions are sufficient; the parent-to-child expression is proved by native mutation.",
    },
    "components": {
        "sufficient": True,
        "reason": "The two body sizes and positions describe the visible result. The saved SolidCraft model is checked separately to confirm that both occurrences reuse one component definition.",
    },
    "repeated-parent-attachments": {
        "sufficient": True,
        "reason": "Four rectangular body bounds expose both parent heights and both child positions. Q5 mutation separately proves that both disconnected native joint graphs follow the shared parent-height change.",
    },
    "assembly-decorator": {
        "sufficient": True,
        "reason": "This case adds reusable assembly construction around two rectangular posts; the geometry contribution is completely described by their bounds.",
    },
    "group-hierarchy": {
        "sufficient": True,
        "reason": "The body sizes describe the visible parts. The saved SolidCraft model is checked separately to confirm the expected group and BOM structure.",
    },
    "attach-angle": {
        "sufficient": True,
        "reason": "The non-square arm size shows whether the quarter-turn is correct. The saved SolidCraft model is also checked for the expected joint angle.",
    },
    "parametric-attach": {
        "sufficient": True,
        "reason": "The two rectangular body bounds describe the baseline gap geometry. Saved joint recompute is proved separately by Q5.",
    },
    "parametric-offset": {
        "sufficient": True,
        "reason": "The base and marker sizes and positions show the local offset. The saved SolidCraft model is then changed to confirm that the planar joint updates correctly.",
    },
    "parametric-anchor": {
        "sufficient": True,
        "reason": "The two body sizes and positions show the initial face-relative placement. The saved SolidCraft model is then changed to confirm that the same anchor is still used.",
    },
    "corner-anchor": {
        "sufficient": True,
        "reason": "The base and marker positions show the intended corner placement. The saved SolidCraft model is then changed to confirm that the marker keeps following that corner.",
    },
    "anchor-topology-mutation": {
        "sufficient": True,
        "reason": "The board and marker positions describe the visible result. After resizing the saved model, the marker must still follow the same selected edge and corner.",
    },
    "assembly-owned-anchor": {
        "sufficient": True,
        "reason": "The three body sizes and positions describe the visible assembly. The saved SolidCraft model is checked separately to confirm which assembly owns the anchor and which parts are related.",
    },
    "four-corner-l": {
        "sufficient": True,
        "reason": "This case adds placement of four already-qualified L-profile components around the frame. The component profile itself is qualified by the bracket case; these bounds describe this case's additional geometry.",
    },
    "eight-corner-brackets": {
        "sufficient": True,
        "reason": "This case adds eight placements of the qualified corner-bracket geometry. Per-occurrence bounds and the visual decomposition describe the added placement geometry; native relationships are checked separately.",
    },
    "eight-flightcase-corners": {
        "sufficient": True,
        "reason": "This case qualifies eight corner placements around the case. Per-occurrence bounds and the visual decomposition describe this case's placement geometry; native relationships are checked separately.",
    },
    "xz-anchor": {
        "sufficient": True,
        "reason": "The board and marker positions describe the visible XZ placement. After resizing the saved model, the markers must still use the same selected anchors.",
    },
    "circle-negative-extrude": {
        "sufficient": False,
        "reason": "A box can share the same envelope as this cylinder. Circular volume and a radial surface probe are required.",
    },
    "sketch-pattern-mirror": {
        "sufficient": False,
        "reason": "The Circle and Slot cuts do not change the plate envelope. Volume, 3D wall probes and saved-design mutation are required to prove the associative sketch pattern/mirror result.",
    },
    "rectangular-pattern": {
        "sufficient": False,
        "reason": "The six slot cuts do not change the plate envelope. Volume and 3D slot-wall probes are required.",
    },
    "slot-family": {
        "sufficient": False,
        "reason": "The five slot cuts do not change the plate envelope. Volume and 3D slot-wall probes are required.",
    },
    "rounded-rectangle-sketch": {
        "sufficient": False,
        "reason": "A sharp rectangular pad can share the same envelope. Rounded-pad volume and a corner-distance probe are required.",
    },
    "primitive-csg": {
        "sufficient": False,
        "reason": "Many different Boolean results can share this envelope. Surface probes must prove the surviving sphere, bore, clipped box and unioned extension.",
    },
    "bracket": {
        "sufficient": False,
        "reason": "A filled box can share the L-profile envelope. L-profile volume and a probe in the missing corner are required.",
    },
}


_GEOMETRY_DETAILS = {
    "anchored-holes": {
        "volume_mm3": 100.0 * 60.0 * 10.0 - 2.0 * math.pi * 4.0**2 * 10.0,
        "volume_tolerance_mm3": 55.0,
        "watertight": True,
        "surface_distance_probes": _through_probes(
            [("front hole", 50.0, 10.0), ("rear hole", 50.0, 50.0)],
            (1.0, 5.0, 9.0), 4.0,
        ),
    },
    "circle-negative-extrude": {
        "volume_mm3": math.pi * 10.0**2 * 30.0,
        "volume_tolerance_mm3": 100.0,
        "watertight": True,
        "surface_distance_probes": [{
            "label": "circular side outside the diagonal",
            "point": [8.0, 8.0, -15.0],
            "distance_mm": math.sqrt(8.0**2 + 8.0**2) - 10.0,
            "tolerance_mm": 0.30,
        }],
    },
    "sketch-pattern-mirror": {
        "volume_mm3": (
            240.0 * 160.0 * 5.0
            - 8.0 * math.pi * 4.0**2 * 5.0
            - 8.0 * (20.0 * 8.0 + math.pi * 4.0**2) * 5.0
        ),
        # PythonSCAD/pyBOSL2 use coarser circular facets for the eight holes
        # and Slot end-arcs. Their volume differs by about 155 mm³ while all
        # 3D wall probes remain within about 0.12 mm.
        "volume_tolerance_mm3": 180.0,
        "watertight": True,
        "surface_distance_probes": [
            *_through_probes(
                _SKETCH_PATTERN_HOLE_CENTERS,
                (0.5, 2.5, 4.5),
                4.0,
            ),
            *_through_probes(
                _SKETCH_PATTERN_SLOT_CENTERS,
                (0.5, 2.5, 4.5),
                4.0,
            ),
        ],
    },
    "rectangular-pattern": {
        "volume_mm3": 120.0 * 80.0 * 4.0 - 6.0 * (10.0 * 6.0 + math.pi * 3.0**2) * 4.0,
        # PythonSCAD/pyBOSL2 use coarser circular STL facets. Their volume
        # differs by about 44 mm³ while all slot-wall probes remain correct.
        "volume_tolerance_mm3": 50.0,
        "watertight": True,
        "surface_distance_probes": _through_probes(
            _RECTANGULAR_SLOT_CENTERS, (0.5, 2.0, 3.5), 3.0,
        ),
    },
    "slot-family": {
        "volume_mm3": (
            160.0 * 120.0 * 5.0
            - 5.0 * (
                (20.0 * 8.0 + math.pi * 4.0**2)
                + (22.0 * 8.0 + math.pi * 4.0**2)
                + (20.0 * 8.0 + math.pi * 4.0**2)
                + (15.153846153846153 * math.radians(163.65753288010052) * 8.0 + math.pi * 4.0**2)
                + (12.0 * math.radians(120.0) * 8.0 + math.pi * 4.0**2)
            )
        ),
        # PythonSCAD/pyBOSL2 use coarser circular/arc STL facets. Their volume
        # differs by about 49 mm³ while all 3D slot-wall probes remain correct.
        "volume_tolerance_mm3": 55.0,
        "watertight": True,
        "surface_distance_probes": _through_probes(
            _SLOT_FAMILY_CENTERS, (0.5, 2.5, 4.5), 4.0,
        ),
    },
    "rounded-rectangle-sketch": {
        "volume_mm3": 80.0 * 60.0 * 5.0 + (40.0 * 30.0 - (4.0 - math.pi) * 5.0**2) * 8.0,
        "volume_tolerance_mm3": 60.0,
        "watertight": True,
        "surface_distance_probes": [{
            "label": "rounded pad corner",
            "point": [20.0, 15.0, 9.0],
            "distance_mm": math.sqrt(5.0**2 + 5.0**2) - 5.0,
            "tolerance_mm": 0.30,
        }],
    },
    "primitive-csg": {
        "watertight": True,
        "surface_distance_probes": [
            {"label": "surviving sphere interior", "point": [-10.0, 0.0, 10.0],
             "distance_mm": 20.0 - math.sqrt(10.0**2 + 10.0**2), "tolerance_mm": 0.30},
            {"label": "cylindrical bore", "point": [0.0, 0.0, 1.0],
             "distance_mm": 3.0, "tolerance_mm": 0.30},
            {"label": "clip plane at x=25", "point": [27.0, 10.0, 10.0],
             "distance_mm": 2.0, "tolerance_mm": 0.30},
            {"label": "unioned box extension", "point": [23.0, 14.0, 10.0],
             "distance_mm": 1.0, "tolerance_mm": 0.30},
        ],
    },
    "bracket": {
        "volume_mm3": 19584.0,
        "volume_tolerance_mm3": 1.0,
        "watertight": True,
        "surface_distance_probes": [{
            "label": "empty inside corner",
            "point": [30.0, 0.0, -30.0],
            "distance_mm": 18.0,
            "tolerance_mm": 0.30,
        }],
    },
}


_CASE_BY_SLUG = {case["slug"]: case for case in QUALIFICATION_CASES}


def geometry_contract(slug: str) -> dict:
    """Return the shared geometry contract for one qualification case."""
    if slug not in EXPECTED_BOUNDS:
        raise KeyError(f"no geometry contract declared for {slug}")
    assessment = _BOUNDS_ASSESSMENTS[slug]
    contract = {
        "bounds": EXPECTED_BOUNDS[slug],
        "visual_boxes": EXPECTED_VISUAL_BOXES.get(
            slug,
            EXPECTED_BOUNDS[slug],
        ),
        "required_views": list(REQUIRED_VISUAL_VIEWS[slug]),
        "visual_features": EXPECTED_VISUAL_FEATURES[slug],
        "bounds_sufficient": assessment["sufficient"],
        "bounds_reason": assessment["reason"],
    }
    contract.update(_GEOMETRY_DETAILS.get(slug, {}))
    return contract


def proof_contract(slug: str) -> dict:
    """Return shared geometry plus SolidCraft-only proof expectations."""
    case = _CASE_BY_SLUG[slug]
    return {
        "case": slug,
        "geometry": geometry_contract(slug),
        "solidcraft_only": {
            "native_expectation": case["native_expectation"],
            "generated_relationship": case["lowering"],
            "q5_required": bool(case.get("q5_required")),
            "q5_reason": case["mutation"],
            "mutation": case["mutation"] if case.get("q5_required") else None,
        },
    }
