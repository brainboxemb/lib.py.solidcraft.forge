"""Generic body-history semantic IR.

Private domain module behind the stable :mod:`scpf.ir` compatibility facade.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from ..core import Shape, _pv as pv
from .base import BodyIR
from .operations import FaceSetIR

class ShellIR(BodyIR):
    """Uniform wall shell over one typed body result."""

    base: BodyIR
    thickness: Any
    open_faces: FaceSetIR
    source_kind: str = "shell"

    def __post_init__(self):
        if not isinstance(self.base, BodyIR):
            raise ValueError("ShellIR base must be one typed BodyIR result")
        if (
            isinstance(self.thickness, bool)
            or not isfinite(pv(self.thickness))
            or pv(self.thickness) <= 0
        ):
            raise ValueError("ShellIR thickness must be one positive CAD dimension")
        if not isinstance(self.open_faces, FaceSetIR):
            raise ValueError("ShellIR open_faces must be FaceSetIR")


@dataclass(frozen=True)
class TranslationIR(BodyIR):
    """One semantic XYZ translation of an already-typed body."""

    body: BodyIR
    offset: tuple[Any, Any, Any]
    source_kind: str = "translated"

    def __post_init__(self):
        if not isinstance(self.body, BodyIR):
            raise ValueError("TranslationIR body must be typed BodyIR")
        if (
            not isinstance(self.offset, tuple)
            or len(self.offset) != 3
            or any(
                isinstance(value, bool) or not isfinite(pv(value))
                for value in self.offset
            )
        ):
            raise ValueError(
                "TranslationIR offset must contain three finite CAD dimensions"
            )


@dataclass(frozen=True)
class BooleanIR(BodyIR):
    """Recursive CSG composition over already-typed semantic body histories."""

    operation: str
    target: BodyIR
    tool: BodyIR
    source_kind: str = "boolean"

    def __post_init__(self):
        if self.operation not in {"join", "cut", "intersect"}:
            raise ValueError(
                "BooleanIR operation must be join, cut or intersect"
            )
        if not isinstance(self.target, BodyIR):
            raise ValueError("BooleanIR target must be typed BodyIR")
        if not isinstance(self.tool, BodyIR):
            raise ValueError("BooleanIR tool must be typed BodyIR")


@dataclass(frozen=True)
class LegacyShapeIR:
    """Transitional wrapper for stable SolidCraft surface not migrated yet."""

    shape: Shape
    source_kind: str


IRNode = BodyIR | LegacyShapeIR


@dataclass(frozen=True)
