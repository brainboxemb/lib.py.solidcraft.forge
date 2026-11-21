"""Experimental explicit Sketch scope.

The scope owns editable 2D profiles. 3D operations are applied afterwards,
so authoring a sketch remains distinct from extruding/cutting it.
"""
from contextvars import ContextVar
from math import isfinite

from .core import Anchor, Axis, Depth, Shape, _pv as pv

_ACTIVE_SKETCH = ContextVar("scpf_active_sketch", default=None)

_COORDINATE_DEFINED_PROFILE_KINDS = frozenset(
    {
        "polygon",
        "text",
        "slot_center_to_center",
        "slot_overall",
        "slot_center_point",
        "slot_arc_three_point",
        "slot_arc_center",
    }
)


def _coordinate_defined(profile):
    """Return whether a 2D profile owns authored sketch-local coordinates."""

    return profile.kind in _COORDINATE_DEFINED_PROFILE_KINDS


def register_profile(profile):
    """Capture authored 2D geometry only while an explicit Sketch is active."""
    sketch = _ACTIVE_SKETCH.get()
    if sketch is not None:
        # Polygon vertices and text insertion points already carry their own
        # sketch-local placement. Dimension-defined primitives use the semantic
        # Sketch centre by default.
        anchor = None if _coordinate_defined(profile) else Anchor.CENTER
        sketch._store_profile(profile, anchor=anchor, offset=(0, 0))
    return profile


class Sketch:
    """Create an explicit named 2D sketch scope.

    Parameters:
        name: Native sketch name. Defaults to "Profile".
        on: Optional existing Shape whose surface supports the sketch.
        parent: Anchor selecting the supporting surface when on= is used. Defaults to Anchor.TOP.
        plane: Explicit sketch plane: "XY", "XZ" or "YZ". Defaults to "XY" when on= is not used. With on=, an explicit plane is world-based while on= still selects the body modified by the extrusion.
        origin: Optional explicit 3D origin for an explicit plane, in mm. May be used with on= when the Sketch should modify an existing body from a fixed world plane.
        offset: Optional signed offset from a standalone origin plane, in mm.

    Use when:
        Author one or more 2D profiles before creating a 3D extrusion. A
        Sketch may be standalone on XY/XZ/YZ or supported by an existing Shape.

    Limits:
        Sketch(on=target) selects the body modified by the later extrusion.
        With the default parent=Anchor.TOP, Forge selects the largest +Z planar
        face at replay time. An explicit plane/origin bypasses face lookup.
        BOTTOM/CENTER relative placement still requires supported base metadata.
        offset remains a standalone-plane option. Leave the with-scope before
        extruding.

    Example:
        with Sketch(name="Base", plane="XY") as sketch:
            Rectangle2D(80, 50)
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
        self._operations = []
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

        Parameters:
            profile: Supported 2D Shape such as Rectangle2D, Circle2D, Polygon2D or a Slot constructor result.
            anchor: Optional profile datum. Dimension-defined profiles default to Anchor.CENTER; coordinate-defined profiles keep their own coordinates.
            offset: Sketch-local (u, v) displacement in mm. Defaults to (0, 0).

        Use when:
            Add a profile explicitly or apply a deliberate sketch-local
            offset. Dimension-defined profiles default to semantic CENTER.
            Polygon2D, Text2D and native Slot profiles keep their authored
            coordinates.

        Limits:
            Explicit Anchor.CENTER is supported for Circle2D, Rectangle2D and
            RoundedRectangle2D. Polygon2D, Text2D and native Slot profiles
            define their own sketch-local coordinates; leave anchor=None for
            those profile types.

        Example:
            sketch.add(Circle2D(d=8), anchor=Anchor.CENTER, offset=(20, 0))
        """
        if self._closed:
            raise ValueError("cannot add geometry after leaving the Sketch scope")
        if not isinstance(profile, Shape) or profile.kind not in (
            "circle",
            "rectangle",
            "rounded_rectangle",
            "text",
            "polygon",
            "slot_center_to_center",
            "slot_overall",
            "slot_center_point",
            "slot_arc_three_point",
            "slot_arc_center",
        ):
            raise ValueError(
                "Sketch supports Circle2D, Rectangle2D, Polygon2D, "
                "RoundedRectangle2D, Text2D or native Slot profiles"
            )

        coordinate_defined = _coordinate_defined(profile)
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

    def _require_entity_source(self, source):
        """Require one profile or sketch-operation result from this Sketch."""
        if not isinstance(source, Shape):
            raise TypeError("sketch pattern/mirror source must be sketch geometry")
        if any(profile is source for profile, _anchor, _offset in self._profiles):
            return source
        if any(operation is source for operation in self._operations):
            return source
        raise ValueError("sketch pattern/mirror source must belong to this Sketch")

    @staticmethod
    def _pattern_direction(direction, label):
        if isinstance(direction, Axis):
            if direction is Axis.X:
                return (1.0, 0.0)
            if direction is Axis.Y:
                return (0.0, 1.0)
            raise ValueError(f"{label} supports Axis.X or Axis.Y in a 2D Sketch")
        if not isinstance(direction, (tuple, list)) or len(direction) != 2:
            raise ValueError(
                f"{label} must be Axis.X, Axis.Y or a fixed (x, y) vector"
            )
        vector = tuple(float(pv(value)) for value in direction)
        if not all(isfinite(value) for value in vector):
            raise ValueError(f"{label} must contain finite numeric values")
        if sum(value * value for value in vector) <= 0:
            raise ValueError(f"{label} must be non-zero")
        return vector

    def rectangular_pattern(
        self,
        source,
        *,
        count,
        spacing,
        direction=Axis.X,
        count2=1,
        spacing2=None,
        direction2=None,
        alignment="right",
        alignment2="right",
        reversed=False,
        reversed2=False,
    ):
        """Repeat a profile or earlier Sketch result with a native rectangular pattern.

        Parameters:
            source: A profile already in this Sketch, or a result returned by rectangular_pattern() or mirror() in the same Sketch.
            count: Number of instances in the first direction, including the original. Use a whole number from 1 to 500; a dimensionless Parameter may remain editable in SolidCraft.
            spacing: Distance between instances in the first direction, in mm. A length Parameter may remain editable in SolidCraft.
            direction: First sketch-local direction: Axis.X, Axis.Y or a fixed non-zero (x, y) vector. Defaults to Axis.X.
            count2: Number of instances in the second direction, including the original. Use a whole number from 1 to 500. Defaults to 1.
            spacing2: Optional distance between instances in the second direction, in mm. When omitted, SolidCraft uses the first spacing.
            direction2: Optional second sketch-local direction: Axis.X, Axis.Y or a fixed non-zero (x, y) vector. When omitted, SolidCraft uses the direction perpendicular to the first.
            alignment: Position of the original along the first direction: "left", "center" or "right". Defaults to "right".
            alignment2: Position of the original along the second direction: "left", "center" or "right". Defaults to "right".
            reversed: Reverse placement along the first direction. Defaults to False.
            reversed2: Reverse placement along the second direction. Defaults to False.

        Use when:
            Repeat one Circle, Slot or other supported profile without drawing
            every copy separately. The returned Sketch result represents the
            source plus its copies and may be passed to mirror() or another
            supported Sketch operation.

        Limits:
            The operation must be authored inside the active Sketch. Current
            native qualification covers attached Sketch(on=...) use. The two
            counts may create at most 500 instances in total. Per-instance
            suppression is not supported. SolidCraft 0.42 stores the curves
            selected by a mirror when that mirror is created. If a pattern
            later creates extra curves after its count changes, those new
            curves are not added to that existing mirror automatically.

        Example:
            with Sketch(name="Holes", on=board, parent=Anchor.TOP) as sketch:
                circle = Circle2D(d=8)
                row = sketch.rectangular_pattern(
                    circle, count=4, spacing=25, direction=Axis.X
                )

            with Sketch(name="Slots", on=board, parent=Anchor.TOP) as sketch:
                slot = SlotCenterToCenter2D((0, 0), (20, 0), 8)
                pair = sketch.rectangular_pattern(
                    slot, count=2, spacing=30, direction=Axis.Y
                )
        """
        if self._closed or self._token is None:
            raise ValueError("sketch pattern must be authored inside the Sketch scope")
        source = self._require_entity_source(source)
        if isinstance(count, bool):
            raise ValueError("sketch pattern count must be a whole number from 1 to 500")
        if isinstance(count2, bool):
            raise ValueError("sketch pattern count2 must be a whole number from 1 to 500")
        count_value = pv(count)
        count2_value = pv(count2)
        if (
            not isfinite(count_value)
            or not 1 <= count_value <= 500
            or not count_value.is_integer()
        ):
            raise ValueError("sketch pattern count must be a whole number from 1 to 500")
        if (
            not isfinite(count2_value)
            or not 1 <= count2_value <= 500
            or not count2_value.is_integer()
        ):
            raise ValueError("sketch pattern count2 must be a whole number from 1 to 500")
        if count_value * count2_value > 500:
            raise ValueError("sketch pattern supports at most 500 total instances")
        if not isfinite(pv(spacing)):
            raise ValueError("sketch pattern spacing must be finite")
        if spacing2 is not None and not isfinite(pv(spacing2)):
            raise ValueError("sketch pattern spacing2 must be finite")
        if alignment not in ("left", "center", "right"):
            raise ValueError("sketch pattern alignment must be left, center or right")
        if alignment2 not in ("left", "center", "right"):
            raise ValueError("sketch pattern alignment2 must be left, center or right")
        if not isinstance(reversed, bool) or not isinstance(reversed2, bool):
            raise TypeError("sketch pattern reversed flags must be True or False")

        dir1 = self._pattern_direction(direction, "sketch pattern direction")
        dir2 = (
            None
            if direction2 is None
            else self._pattern_direction(direction2, "sketch pattern direction2")
        )
        operation = Shape(
            "sketch_pattern_rectangular",
            (
                source,
                count,
                spacing,
                dir1,
                count2,
                spacing2,
                dir2,
                alignment,
                alignment2,
                reversed,
                reversed2,
            ),
        )
        self._operations.append(operation)
        return operation

    def mirror(self, source, *, axis):
        """Mirror a profile or earlier Sketch result over the sketch X or Y axis.

        Parameters:
            source: A profile already in this Sketch, or a result returned by rectangular_pattern() or mirror() in the same Sketch.
            axis: Mirror axis. Use Axis.X, Axis.Y, "x" or "y".

        Use when:
            Create symmetric sketch geometry from a Circle, Slot, pattern result
            or earlier mirror result. The returned Sketch result contains the
            mirrored copies and may be used by a later supported Sketch
            operation.

        Limits:
            The operation must be authored inside the active Sketch. Current
            native qualification covers attached Sketch(on=...) use. Only the
            sketch X and Y origin axes are supported. SolidCraft 0.42 stores
            the curves selected when the mirror is created. If an upstream
            pattern later creates extra curves after its count changes, those
            new curves are not added to that existing mirror automatically.

        Example:
            with Sketch(name="Holes", on=board, parent=Anchor.TOP) as sketch:
                circle = Circle2D(d=8)
                sketch.mirror(circle, axis=Axis.Y)

            with Sketch(name="Slots", on=board, parent=Anchor.TOP) as sketch:
                slot = SlotCenterToCenter2D((0, 0), (20, 0), 8)
                pair = sketch.rectangular_pattern(
                    slot, count=2, spacing=30, direction=Axis.X
                )
                sketch.mirror(pair, axis=Axis.X)
        """
        if self._closed or self._token is None:
            raise ValueError("sketch mirror must be authored inside the Sketch scope")
        source = self._require_entity_source(source)
        if isinstance(axis, Axis):
            if axis not in (Axis.X, Axis.Y):
                raise ValueError("sketch mirror axis must be Axis.X or Axis.Y")
            line = axis.value.lower()
        elif isinstance(axis, str) and axis.lower() in ("x", "y"):
            line = axis.lower()
        else:
            raise ValueError("sketch mirror axis must be Axis.X, Axis.Y, 'x' or 'y'")
        operation = Shape("sketch_mirror", (source, line))
        self._operations.append(operation)
        return operation

    def sheet_metal(
        self,
        *,
        thickness,
        bend_radius,
        k_factor=0.5,
        rule_name="Forge Sheet",
    ):
        """Create a native sheet-metal body from this closed flat Sketch.

        Parameters:
            thickness: Sheet thickness in mm.
            bend_radius: Default inside bend radius in mm.
            k_factor: Neutral-axis K-factor. Must be greater than 0 and less than 1. Defaults to 0.5.
            rule_name: Native SolidCraft sheet-rule name. Defaults to "Forge Sheet".

        Use when:
            Start a fabricated sheet part from its flat blank before applying
            holes, folds, hems or other sheet-metal features.

        Limits:
            The first qualified form requires one standalone XY Sketch with one
            closed profile. Leave the Sketch scope before creating the sheet.

        Example:
            with Sketch(name="Blank", plane="XY") as blank:
                Rectangle2D(80, 40)
            sheet = blank.sheet_metal(
                thickness=2,
                bend_radius=2,
                k_factor=0.5,
            )
        """
        if not self._closed:
            raise ValueError("leave the Sketch scope before creating sheet metal")
        if self.on is not None:
            raise ValueError("sheet_metal() requires a standalone Sketch")
        if self.plane != "XY":
            raise ValueError("sheet_metal() currently requires an XY Sketch")
        if len(self._profiles) != 1:
            raise ValueError(
                "sheet_metal() currently requires exactly one closed profile"
            )
        if pv(thickness) <= 0:
            raise ValueError("sheet metal thickness must be positive")
        if pv(bend_radius) <= 0:
            raise ValueError("sheet metal bend_radius must be positive")
        k = pv(k_factor)
        if not isfinite(k) or not 0 < k < 1:
            raise ValueError("sheet metal k_factor must be between 0 and 1")
        if not isinstance(rule_name, str) or not rule_name.strip():
            raise ValueError("sheet metal rule_name must be non-empty")

        return Shape(
            "sheet_base",
            (
                self.name,
                self.plane,
                self.origin,
                self.offset,
                tuple(self._profiles),
                tuple(self._operations),
                thickness,
                bend_radius,
                k_factor,
                rule_name,
            ),
        )

    def extrude(
        self,
        distance,
        *,
        sym=False,
        profiles=None,
        exact_regions=False,
    ):
        """Extrude selected profiles from a completed Sketch.

        Parameters:
            distance: Extrusion distance in mm, or Depth.THROUGH_ALL for an attached Sketch. Positive finite distances follow the plane normal; negative reverses it. THROUGH_ALL cuts through the attached target from the selected support face.
            sym: When True, split a positive distance equally across both sides of the sketch plane. Defaults to False.
            profiles: Optional non-empty sequence of fixed sketch-local (x, y) points. Each point selects the closed profile containing it. Leave None to extrude every profile.
            exact_regions: When True, each profile point selects exactly the SolidCraft region containing that point. Only valid together with profiles=. Defaults to False.

        Use when:
            Leave the Sketch context and create or cut material normal to the
            sketch plane. Use profiles= when the Sketch contains more closed
            regions than the extrusion should use.

        Limits:
            A standalone Sketch requires a finite non-zero distance.
            Depth.THROUGH_ALL is only meaningful for a Sketch attached to an
            existing Shape and cannot be combined with sym=True. Profile pick
            points must be fixed finite numbers; Parameters and expressions are
            not accepted because SolidCraft 0.42 profile points are numeric.

        Example:
            cut = sketch.extrude(
                Depth.THROUGH_ALL,
                profiles=[(-30, 0), (-10, 0), (30, 0)],
                exact_regions=True,
            )
        """
        if not self._closed:
            raise ValueError("leave the Sketch scope before extruding it")
        if not isinstance(sym, bool):
            raise TypeError("Sketch extrusion sym must be True or False")
        if not isinstance(exact_regions, bool):
            raise TypeError(
                "Sketch extrusion exact_regions must be True or False"
            )

        if profiles is None:
            profile_picks = None
            if exact_regions:
                raise ValueError(
                    "Sketch extrusion exact_regions requires profiles="
                )
        else:
            if not isinstance(profiles, (list, tuple)) or not profiles:
                raise ValueError(
                    "Sketch extrusion profiles must be a non-empty sequence "
                    "of (x, y) points"
                )
            normalized = []
            for point in profiles:
                if not isinstance(point, (list, tuple)) or len(point) != 2:
                    raise ValueError(
                        "each Sketch extrusion profile point must have x and y"
                    )
                values = []
                for coordinate in point:
                    if (
                        isinstance(coordinate, bool)
                        or not isinstance(coordinate, (int, float))
                        or not isfinite(coordinate)
                    ):
                        raise ValueError(
                            "Sketch extrusion profile points must contain "
                            "fixed finite numbers"
                        )
                    values.append(float(coordinate))
                normalized.append(tuple(values))
            profile_picks = tuple(normalized)

        if distance is Depth.THROUGH_ALL:
            if sym:
                raise ValueError("Depth.THROUGH_ALL cannot be combined with sym=True")
            native_distance = distance
            # SolidCraft defaults through-all extrusion to the positive sketch
            # normal. A TOP support face points away from the target body, so
            # that cut must explicitly run in the negative direction.
            direction = (
                "negative"
                if self.on is not None
                and self.plane is None
                and self.parent is Anchor.TOP
                else "positive"
            )
        else:
            value = pv(distance)
            if value == 0:
                raise ValueError("Sketch extrusion distance must be non-zero")
            if sym:
                if value < 0:
                    raise ValueError(
                        "symmetric Sketch extrusion distance must be positive"
                    )
                native_distance = distance
                direction = "symmetric"
            elif value < 0:
                native_distance = -distance
                direction = "negative"
            else:
                native_distance = distance
                direction = "positive"

        if self.on is None:
            if distance is Depth.THROUGH_ALL:
                raise ValueError("standalone Sketch requires a finite extrusion distance")
            data = (
                self.name,
                self.plane,
                self.origin,
                self.offset,
                tuple(self._profiles),
                native_distance,
                direction,
                tuple(self._operations),
                profile_picks,
                exact_regions,
            )
            return Shape("sketch_base_extrusion", data)

        data = (
            self.name,
            self.on,
            self.parent,
            (self.plane, self.origin),
            tuple(self._profiles),
            native_distance,
            direction,
            tuple(self._operations),
            profile_picks,
            exact_regions,
        )
        return Shape("explicit_sketch_extrusion", data)
