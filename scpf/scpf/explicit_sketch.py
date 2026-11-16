"""Experimental explicit Sketch scope.

The scope owns editable 2D profiles. 3D operations are applied afterwards,
so authoring a sketch remains distinct from extruding/cutting it.
"""
from contextvars import ContextVar

from .core import Anchor, Depth, Direction, Shape, _pv as pv

_ACTIVE_SKETCH = ContextVar("scpf_active_sketch", default=None)


def register_profile(profile):
    """Capture authored 2D geometry only while an explicit Sketch is active."""
    sketch = _ACTIVE_SKETCH.get()
    if sketch is not None:
        # Polygon vertices and text insertion points already carry their own
        # sketch-local placement. Dimension-defined primitives use the semantic
        # Sketch centre by default.
        anchor = (
            None
            if profile.kind in ("polygon", "text")
            else Anchor.CENTER
        )
        sketch._store_profile(profile, anchor=anchor, offset=(0, 0))
    return profile


class Sketch:
    """Create an explicit named 2D sketch scope.

    Use when:
        Author one or more 2D profiles before creating a 3D extrusion. A
        Sketch may be standalone on XY/XZ/YZ or supported by an existing Shape.

    Limits:
        Sketch(on=target) selects the supporting shape; profile placement
        inside the sketch is a separate operation. Leave the with-scope before
        extruding.
    """

    def __init__(self, *, name="Profile", on=None, parent=Anchor.TOP, plane=None, origin=None, offset=None):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Sketch name must be non-empty")
        if on is not None and not isinstance(on, Shape):
            raise TypeError("Sketch on= must be an existing Shape")
        if on is None and plane is None:
            plane = "XY"
        try:
            parent = Anchor(parent)
        except ValueError as exc:
            raise ValueError("Sketch parent must be an Anchor") from exc
        if plane is not None and plane not in ("XY", "XZ", "YZ"):
            raise ValueError("Sketch plane must be XY, XZ or YZ")
        self.name = name
        self.on = on
        self.parent = parent
        if origin is not None:
            if plane not in ("XY", "XZ", "YZ"):
                raise ValueError("Sketch origin requires an explicit XY, XZ or YZ plane")
            if not isinstance(origin, (list, tuple)) or len(origin) != 3:
                raise ValueError("Sketch origin must be a 3D coordinate")
            for coordinate in origin:
                pv(coordinate)
        self.origin = tuple(origin) if origin is not None else None
        if offset is not None:
            if on is not None or origin is not None:
                raise ValueError("Sketch offset requires a standalone plane")
            pv(offset)
        self.offset = offset
        self.plane = plane
        self._profiles = []
        self._closed = False
        self._token = None

    def __enter__(self):
        if self._closed or self._token is not None:
            raise ValueError("Sketch scope cannot be re-entered")
        self._token = _ACTIVE_SKETCH.set(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _ACTIVE_SKETCH.reset(self._token)
        self._token = None
        if exc_type is None:
            if not self._profiles:
                raise ValueError("Sketch must contain at least one profile")
            self._closed = True
        return False

    def _store_profile(self, profile, *, anchor, offset):
        """Store one profile placement without applying public anchor defaults."""
        self._profiles = [
            row for row in self._profiles
            if row[0] is not profile
        ]
        self._profiles.append((profile, anchor, tuple(offset)))

    def add(self, profile, *, anchor=None, offset=(0, 0)):
        """Add and place a supported 2D profile in this Sketch.

        Use when:
            Add a profile explicitly or apply a deliberate sketch-local
            offset. Dimension-defined profiles default to semantic CENTER.
            Polygon2D and Text2D keep their authored/insertion coordinates.

        Limits:
            Explicit Anchor.CENTER is supported for Circle2D, Rectangle2D and
            RoundedRectangle2D. Polygon2D and Text2D do not have a qualified
            semantic centre yet; leave anchor=None for those profile types.
        """
        if self._closed:
            raise ValueError("cannot add geometry after leaving the Sketch scope")
        if not isinstance(profile, Shape) or profile.kind not in (
            "circle",
            "rectangle",
            "rounded_rectangle",
            "text",
            "polygon",
        ):
            raise ValueError(
                "Sketch supports Circle2D, Rectangle2D, Polygon2D, "
                "RoundedRectangle2D or Text2D profiles"
            )

        coordinate_defined = profile.kind in ("polygon", "text")
        if anchor is None:
            anchor = None if coordinate_defined else Anchor.CENTER
        else:
            try:
                anchor = Anchor(anchor)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "Sketch profile anchor must be Anchor.CENTER or None"
                ) from exc
            if anchor is not Anchor.CENTER:
                raise ValueError(
                    "Sketch profile anchor currently supports CENTER only"
                )
            if coordinate_defined:
                raise ValueError(
                    f"{profile.kind} profiles define their own sketch-local "
                    "coordinates; CENTER is not supported for this profile yet"
                )

        if not isinstance(offset, (tuple, list)) or len(offset) != 2:
            raise ValueError("Sketch offset must be an (x, y) pair")
        for value in offset:
            pv(value)

        # The constructor may already have been captured automatically inside
        # this scope. Explicit add() replaces that placement.
        self._store_profile(
            profile,
            anchor=anchor,
            offset=tuple(offset),
        )
        return profile

    def extrude(self, distance, *, direction=Direction.POSITIVE):
        """Extrude a completed Sketch into a supported 3D feature.

        Use when:
            Leave the Sketch context and then create material using a finite
            distance and, when needed, a Direction relative to the sketch plane.

        Limits:
            A standalone Sketch requires a finite distance. Depth.THROUGH_ALL
            is only meaningful for a Sketch attached to an existing Shape.
        """
        if not self._closed:
            raise ValueError("leave the Sketch scope before extruding it")
        if distance is not Depth.THROUGH_ALL and pv(distance) <= 0:
            raise ValueError("Sketch extrusion distance must be positive or Depth.THROUGH_ALL")
        try:
            direction = Direction(direction)
        except ValueError as exc:
            raise ValueError("invalid Sketch extrusion direction") from exc
        if self.on is None:
            if distance is Depth.THROUGH_ALL:
                raise ValueError("standalone Sketch requires a finite extrusion distance")
            return Shape(
                "sketch_base_extrusion",
                (self.name, self.plane, self.origin, self.offset, tuple(self._profiles), distance, direction.value),
            )
        return Shape(
            "explicit_sketch_extrusion",
            (
                self.name,
                self.on,
                self.parent,
                (self.plane, self.origin),
                tuple(self._profiles),
                distance,
                direction.value,
            ),
        )
