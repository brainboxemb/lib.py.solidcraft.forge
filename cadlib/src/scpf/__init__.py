"""SCPF: readable Python CAD model descriptions compiled to SolidCraft."""
from .core import (
    Box, Cylinder, Cone, Sphere, Hole, CounterboreHole, CountersinkHole, ThreadedHole, Lip, SnapFit, Boss, Rest, Depth,
    Rectangle2D, RoundedRectangle2D, Circle2D, Polygon2D,
    SlotCenterToCenter2D, SlotOverall2D, SlotCenterPoint2D,
    SlotArcThreePoint2D, SlotArcCenter2D,
    Shape, Parameter, Edges, Faces, Anchor, AnchorFrame, AnchorTopology, Axis, AxisLine, X, Y, Z, CENTER, TOP, BOTTOM, LEFT, RIGHT, FRONT, BACK, up, down, left, right, front, back, half, midpoint, pv,
)
from .compiler import compile_model, ModelError
from . import cadmath
from .configurations import Configure, Param, Suppress
from .explicit_sketch import Sketch
from .runner import run_script, component, assembly, ModelParameterWarning
from .model_objects import (
    DrawingDimension,
    DrawingNote,
    DrawingRevision,
    DrawingView,
    Placement,
)

__all__ = [
    "Box", "Cylinder", "Cone", "Sphere", "Hole", "CounterboreHole", "CountersinkHole", "ThreadedHole", "Lip", "SnapFit", "Boss", "Rest",
    "Depth", "Rectangle2D", "RoundedRectangle2D", "Circle2D", "Polygon2D",
    "SlotCenterToCenter2D", "SlotOverall2D", "SlotCenterPoint2D",
    "SlotArcThreePoint2D", "SlotArcCenter2D", "Shape", "Parameter",
    "Edges", "Faces", "Anchor", "AnchorFrame", "AnchorTopology", "Axis", "AxisLine", "X", "Y", "Z", "CENTER", "TOP", "BOTTOM", "LEFT", "RIGHT", "FRONT", "BACK", "up", "down", "left", "right", "front", "back", "half", "midpoint", "pv",
    "Sketch", "Placement", "DrawingView", "DrawingNote", "DrawingRevision",
    "DrawingDimension", "compile_model", "run_script", "component", "assembly",
    "ModelParameterWarning", "ModelError", "Configure", "Param", "Suppress", "cadmath",
]
