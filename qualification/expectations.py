"""Compatibility exports plus mutation-only expected geometry.

Baseline and Q6 visual geometry live in qualification.geometry_contracts so Q4,
independent references and goal overlays share one declaration. Q5 mutation
bounds remain here because they describe post-mutation state rather than the
baseline geometry contract.
"""

from qualification.geometry_contracts import EXPECTED_BOUNDS, EXPECTED_VISUAL_BOXES


EXPECTED_MUTATION_BOUNDS = {
    "simple-box": [
        {"label": "SimpleBox", "min": [-25, -15, 0], "max": [25, 15, 10]},
    ],
    "repeated-parent-attachments": [
        {"label": "left Parent", "min": [-10, -10, 0], "max": [10, 10, 60]},
        {"label": "right Parent", "min": [50, -10, 0], "max": [70, 10, 60]},
        {"label": "left Marker", "min": [-5, -5, 60], "max": [5, 5, 70]},
        {"label": "right Marker", "min": [55, -5, 60], "max": [65, 5, 70]},
    ],
    "assembly-owned-anchor": [
        {"label": "Base", "min": [-40, -15, 0], "max": [40, 15, 40]},
        {"label": "Companion", "min": [65, -5, 0], "max": [75, 5, 10]},
        {"label": "Marker", "min": [30, -25, 30], "max": [40, -15, 40]},
    ],
    "anchor-topology-mutation": [
        {"label": "Board", "min": [-40, -10, 0], "max": [40, 10, 40]},
        {"label": "Marker", "min": [-45, -20, 35], "max": [-35, -10, 45]},
    ],
    "parent-derived-child-size": [
        {"label": "ParentBlock", "min": [-80, -60, 0], "max": [80, 60, 10]},
        {"label": "DerivedChild", "min": [-40, -30, 20], "max": [40, 30, 26]},
    ],
    "parameter-scope": [
        {"label": "local", "min": [-20, -10, 0], "max": [20, 10, 10]},
        {"label": "override", "min": [70, -10, 0], "max": [130, 10, 10]},
        {"label": "shared_a", "min": [170, -10, 0], "max": [270, 10, 10]},
        {"label": "shared_b", "min": [290, -10, 0], "max": [390, 10, 10]},
        {"label": "derived", "min": [435, -10, 0], "max": [485, 10, 10]},
    ],
    "parametric-attach": [
        {"label": "Base", "min": [-20, -15, 0], "max": [20, 15, 10]},
        {"label": "Block", "min": [50, -10, 0], "max": [70, 10, 10]},
    ],
    "parametric-offset": [
        {"label": "Base", "min": [-20, -15, 0], "max": [20, 15, 20]},
        {"label": "Marker", "min": [10, -25, 20], "max": [20, -15, 30]},
    ],
    "parametric-anchor": [
        {"label": "Base", "min": [-40, -15, 0], "max": [40, 15, 10]},
        {"label": "Block", "min": [40, -10, 0], "max": [60, 10, 10]},
    ],
    "corner-anchor": [
        {"label": "Base", "min": [-40, -15, 0], "max": [40, 15, 40]},
        {"label": "Marker", "min": [30, -25, 30], "max": [40, -15, 40]},
    ],
    "four-corner-l": [
        {"label": "FrameBlock", "min": [-80, -60, 0], "max": [80, 60, 60]},
        {"label": "front-left", "min": [-84, -64, 22], "max": [-52, -32, 38]},
        {"label": "front-right", "min": [52, -64, 22], "max": [84, -32, 38]},
        {"label": "rear-right", "min": [52, 32, 22], "max": [84, 64, 38]},
        {"label": "rear-left", "min": [-84, 32, 22], "max": [-52, 64, 38]},
    ],
    "eight-flightcase-corners": [
        {"label": "CaseBlock", "min": [-80, -60, 0], "max": [80, 60, 90]},
        {"label": "front bottom-left", "min": [-84, -64, -4], "max": [-60, -40, 20]},
        {"label": "front bottom-right", "min": [60, -64, -4], "max": [84, -40, 20]},
        {"label": "rear bottom-right", "min": [60, 40, -4], "max": [84, 64, 20]},
        {"label": "rear bottom-left", "min": [-84, 40, -4], "max": [-60, 64, 20]},
        {"label": "front top-left", "min": [-84, -64, 70], "max": [-60, -40, 94]},
        {"label": "front top-right", "min": [60, -64, 70], "max": [84, -40, 94]},
        {"label": "rear top-right", "min": [60, 40, 70], "max": [84, 64, 94]},
        {"label": "rear top-left", "min": [-84, 40, 70], "max": [-60, 64, 94]},
    ],
    "eight-corner-brackets": [
        {"label": "FrameBlock", "min": [-80, -60, 0], "max": [80, 60, 90]},
        {"label": "front-left bottom", "min": [-84, -64, 0], "max": [-52, -32, 16]},
        {"label": "front-left top", "min": [-84, -64, 74], "max": [-52, -32, 90]},
        {"label": "front-right bottom", "min": [52, -64, 0], "max": [84, -32, 16]},
        {"label": "front-right top", "min": [52, -64, 74], "max": [84, -32, 90]},
        {"label": "rear-right bottom", "min": [52, 32, 0], "max": [84, 64, 16]},
        {"label": "rear-right top", "min": [52, 32, 74], "max": [84, 64, 90]},
        {"label": "rear-left bottom", "min": [-84, 32, 0], "max": [-52, 64, 16]},
        {"label": "rear-left top", "min": [-84, 32, 74], "max": [-52, 64, 90]},
    ],
    "sketch-pattern-mirror": [
        {"label": "SketchPatternMirror", "min": [-120, -80, 0], "max": [120, 80, 5]},
    ],
    "selective-profile-extrude": [
        {"label": "SelectiveProfileExtrude", "min": [-60, -30, 0], "max": [60, 30, 5]},
    ],
    "rectangular-pattern": [
        {"label": "RectangularPattern", "min": [-60, -40, 0], "max": [60, 40, 4]},
    ],
    "xz-anchor": [
        {"label": "Board", "min": [-40, 0, 0], "max": [40, 12, 40]},
        {"label": "right Marker", "min": [30, -10, 30], "max": [40, 0, 40]},
        {"label": "left Marker", "min": [-40, -10, 30], "max": [-30, 0, 40]},
    ],
}
