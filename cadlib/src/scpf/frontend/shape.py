"""Shape authoring, feature scopes and feature-tree helpers."""

from contextvars import ContextVar
from dataclasses import dataclass, field
from math import isfinite
from typing import Any

from .scalars import (
    Parameter, Expression, _pv, _dim_add, _dim_sub,
    half, left, right, front, back,
)
from .selectors import (
    Anchor, Axis, AxisLine, Edges, Faces, _BoundOffset,
    _direction_selector, _feature_edge_selection, _pattern_direction,
)

_ACTIVE_FEATURE_SCOPE = ContextVar("scpf_active_feature_scope", default=None)
def _feature_history_step_count(node, created_ids):
    """Count authored history steps on one feature scope's result spine."""
    if not isinstance(node, Shape):
        return 0
    if node.kind in _FEATURE_TRANSPARENT_KINDS:
        return _feature_history_step_count(node.data[0], created_ids)
    if node.kind in _FEATURE_HISTORY_CHAIN_KINDS:
        return (
            (1 if id(node) in created_ids else 0)
            + _feature_history_step_count(node.data[0], created_ids)
        )
    return 1 if id(node) in created_ids else 0

class _FeatureHandle:
    """Reference one named Forge-authored history feature."""

    def __init__(self, name, suppressed):
        self.name = name
        self.suppressed = suppressed
        self._shape = None

    @property
    def shape(self):
        if self._shape is None:
            raise RuntimeError("feature handle is not bound until its scope exits")
        return self._shape

class _FeatureScope(_FeatureHandle):
    """Capture exactly one Forge history step and name its result."""

    def __init__(self, name, suppressed):
        if (
            not isinstance(name, str)
            or not name.isidentifier()
            or name.startswith("_")
        ):
            raise ValueError("feature name must be a public Python identifier")
        if not isinstance(suppressed, bool):
            raise TypeError("feature suppressed must be True or False")
        super().__init__(name, suppressed)
        self._created = []
        self._token = None

    def _register(self, shape):
        self._created.append(shape)

    def __enter__(self):
        if _ACTIVE_FEATURE_SCOPE.get() is not None:
            raise RuntimeError("feature scopes cannot be nested")
        self._token = _ACTIVE_FEATURE_SCOPE.set(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        token = self._token
        self._token = None
        if token is not None:
            _ACTIVE_FEATURE_SCOPE.reset(token)
        if exc_type is not None:
            return False

        created = tuple(self._created)
        terminals = [
            shape
            for shape in created
            if not any(
                other is not shape and _shape_contains(other, shape)
                for other in created
            )
        ]
        if len(terminals) != 1:
            raise ValueError(
                "feature scope must produce exactly one terminal Shape"
            )

        terminal = terminals[0]
        created_ids = {id(shape) for shape in created}
        if _feature_history_step_count(terminal, created_ids) != 1:
            raise ValueError(
                "feature scope must author exactly one CAD history feature"
            )

        source = Shape(
            terminal.kind,
            terminal.data,
            _configuration=terminal._configuration,
        )
        object.__setattr__(terminal, "kind", "named_feature")
        object.__setattr__(
            terminal,
            "data",
            (source, self.name, self.suppressed),
        )
        self._shape = terminal
        return False

def feature(name, *, suppressed=False):
    """Author and name exactly one suppressible CAD history feature.

    Parameters:
        name: Component-local public feature identity.
        suppressed: Initial history state before any final-model configuration.

    Use when:
        A normal CAD operation should become a stable semantic feature that a
        final model can configure directly. The scope captures exactly one
        history operation; helper Sketch/profile construction should happen
        outside the scope.

    Example:
        with feature("panel_pin", suppressed=True) as panel_pin:
            body = body - cutter
        model.configure(
            active="Small",
            columns=(panel_pin,),
            rows={"Small": (True,), "Large": (False,)},
        )
    """
    return _FeatureScope(name, suppressed)


@dataclass(frozen=True)

@dataclass(frozen=True)
class Shape:
    """Store Forge authoring geometry and feature intent before IR normalization.

    Parameters:
        kind: Forge node type. Public constructors set this; normal model code should not invent kind values.
        data: Data stored for that node type. Public constructors and methods build this payload.

    Use when:
        Shape values are normally returned by constructors such as Box(),
        Cylinder(), Hole() and Sketch.extrude(), then transformed or combined
        with the supported Shape methods/operators.

    Limits:
        Shape is Forge's frontend authoring representation, not a native CAD
        BRep. The runner normalizes final Shape intent into semantic ModelIR
        before backend lowering; the selected native CAD engine owns final BRep
        and feature history. Users normally do not instantiate Shape(kind, data)
        directly.

    Example:
        body = Box(80, 50, 12)
    """

    kind: str
    data: Any
    _configuration: object | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    def __post_init__(self):
        scope = _ACTIVE_FEATURE_SCOPE.get()
        if scope is not None:
            scope._register(self)

    def __getattr__(self, name):
        if name == "group":
            raise AttributeError(
                "Shape has no group(). group() changes SolidCraft browser "
                "hierarchy for component occurrences or Assemblies. Keep one "
                "physical part's geometry as a Shape; model separate physical "
                "parts as components/occurrences."
            )
        raise AttributeError(f"Shape has no attribute {name!r}")

    def _csg_operand(self, other, operator):
        other = _shape(other)
        if (
            self.kind in ("material_assignment", "appearance_assignment")
            or other.kind in ("material_assignment", "appearance_assignment")
        ):
            raise TypeError(
                f"material/appearance-assigned Shapes cannot be combined with {operator}. "
                "Finish one physical part's Shape geometry before calling "
                "with_material() or with_appearance(). For separate physical "
                "parts, use component occurrences in an Assembly."
            )
        return other

    def __and__(self, other):
        return Shape("intersection", (self, self._csg_operand(other, "&")))

    def __add__(self, other):
        return Shape("union", (self, self._csg_operand(other, "+")))

    def __or__(self, other):
        return self + other

    def __sub__(self, other):
        return Shape("difference", (self, self._csg_operand(other, "-")))

    def configure(self, *, active, columns, rows):
        """Attach one editable configuration definition to this final model.

        Configuration is final-model presentation/behavior metadata. The Shape
        itself remains the return value so normal model code can build first,
        call configure(), and then return the model.
        """
        from ..configurations import _configure_model
        return _configure_model(
            self,
            active=active,
            columns=columns,
            rows=rows,
        )

    def export_feature(self, name):
        """Export this Forge-authored feature through a reusable component.

        The export name is component-local Forge API identity. It is not a
        SolidCraft history name and is resolved only after the component
        definition has been compiled.
        """
        if (
            not isinstance(name, str)
            or not name.isidentifier()
            or name.startswith("_")
        ):
            raise ValueError("exported feature name must be a public Python identifier")
        return Shape("exported_feature", (self, name))

    def move(self, x=0, y=0, z=0):
        """Translate a CSG shape by millimetres.

        Translates all primitives in a composite CSG model together.
        General feature-based box placement is not implemented yet.
        """
        offsets = (_pv(x), _pv(y), _pv(z))
        if not all(isfinite(v) for v in offsets):
            raise ValueError("move() requires finite coordinates")
        if self.kind in ("fillet", "shell", "rectangular_pattern", "circular_pattern"):
            raise ValueError("move() currently supports only primitive and CSG shapes")
        return Shape("translated", (self, offsets))

    def taper(self, *, from_z, inset):
        """Make a box with a flat front and continuously tapered rear walls.

        from_z is measured from the Box bottom face, independent of the Box
        anchor. The rear perimeter retreats by inset per side from that section
        to the Box top face. This produces native editable sketches and loft.
        """
        if self.kind != "box":
            raise ValueError("taper() currently requires a Box")
        width, height, depth, _anchor = self.data
        if not 0 < _pv(from_z) < _pv(depth):
            raise ValueError("taper from_z must lie within the box depth")
        if not 0 < _pv(inset) * 2 < min(_pv(width), _pv(height)):
            raise ValueError("taper inset must be below half the footprint")
        return Shape("tapered_box", (self, from_z, inset))

    def contour_flange(
        self,
        *,
        distance,
        thickness,
        bend_radius,
        k_factor=0.5,
        rule_name="Forge Sheet",
        flip=False,
        reverse=False,
    ):
        """Create a native contour-flange sheet from an open Sketch chain.

        The receiver must be the Shape returned by Sketch.chain(...).finish().
        Material dimensions define the sheet rule used by the new body; the
        contour feature itself receives only that rule name.
        """
        if self.kind != "sketch_open_chain":
            raise ValueError(
                "contour_flange() requires a finished open connected Sketch chain"
            )

        distance_value = _pv(distance)
        if not isfinite(distance_value) or distance_value <= 0:
            raise ValueError("contour flange distance must be positive")

        thickness_value = _pv(thickness)
        if not isfinite(thickness_value) or thickness_value <= 0:
            raise ValueError("contour flange thickness must be positive")

        radius_value = _pv(bend_radius)
        if not isfinite(radius_value) or radius_value <= 0:
            raise ValueError("contour flange bend_radius must be positive")

        k_value = _pv(k_factor)
        if not isfinite(k_value) or not 0 < k_value < 1:
            raise ValueError(
                "contour flange k_factor must be between 0 and 1"
            )

        if not isinstance(rule_name, str) or not rule_name.strip():
            raise ValueError("contour flange rule_name must be non-empty")
        if not isinstance(flip, bool):
            raise TypeError("contour flange flip must be True or False")
        if not isinstance(reverse, bool):
            raise TypeError("contour flange reverse must be True or False")

        return Shape(
            "sheet_contour_flange",
            (
                self,
                distance,
                thickness,
                bend_radius,
                k_factor,
                rule_name,
                flip,
                reverse,
            ),
        )

    def flange(
        self,
        *,
        edges,
        height,
        angle=90,
        height_from=None,
        position=None,
        flip=False,
    ):
        """Add a native edge flange to existing sheet material.

        Parameters:
            edges: Non-empty sequence of fixed XYZ pick points on sheet edges.
            height: Positive flange height in mm.
            angle: Bend angle in degrees. Defaults to 90.
            height_from: Optional native height datum: "outer", "inner" or "tangent".
            position: Optional native bend position: "inside", "outside", "middle", "material_outside" or "tangent".
            flip: Reverse the flange side when True. Defaults to False.

        Use when:
            Grow new sheet material from one or more existing sheet edges while
            inheriting thickness, K-factor and bend radius from the sheet rule.

        Limits:
            This first slice accepts explicit fixed XYZ edge pick points only.
            Per-edge segment dictionaries, corner relief overrides, chained
            bends and radius overrides are intentionally not exposed.
        """
        if not isinstance(edges, (list, tuple)) or not edges:
            raise ValueError(
                "sheet flange edges must be a non-empty sequence of XYZ points"
            )
        normalized_edges = []
        for point in edges:
            if not isinstance(point, (list, tuple)) or len(point) != 3:
                raise ValueError(
                    "each sheet flange edge pick must have x, y and z"
                )
            values = []
            for coordinate in point:
                if (
                    isinstance(coordinate, bool)
                    or not isinstance(coordinate, (int, float))
                    or not isfinite(coordinate)
                ):
                    raise ValueError(
                        "sheet flange edge picks must contain fixed finite numbers"
                    )
                values.append(float(coordinate))
            normalized_edges.append(tuple(values))

        height_value = _pv(height)
        if not isfinite(height_value) or height_value <= 0:
            raise ValueError("sheet flange height must be positive")

        angle_value = _pv(angle)
        if (
            not isfinite(angle_value)
            or angle_value == 0
            or abs(angle_value) >= 180
        ):
            raise ValueError(
                "sheet flange angle must be non-zero and below 180 degrees"
            )

        if height_from not in (None, "outer", "inner", "tangent"):
            raise ValueError(
                "sheet flange height_from must be outer, inner, tangent or None"
            )
        if position not in (
            None,
            "inside",
            "outside",
            "middle",
            "material_outside",
            "tangent",
        ):
            raise ValueError(
                "sheet flange position must be inside, outside, middle, "
                "material_outside, tangent or None"
            )
        if not isinstance(flip, bool):
            raise TypeError("sheet flange flip must be True or False")

        return Shape(
            "sheet_edge_flange",
            (
                self,
                tuple(normalized_edges),
                height,
                angle,
                height_from,
                position,
                flip,
            ),
        )

    def perforate(
        self,
        *,
        diameter,
        pitch,
        margin=None,
        pattern="staggered",
    ):
        """Add a native whole-sheet perforation field.

        Parameters:
            diameter: Positive perforation diameter in mm.
            pitch: Positive centre-to-centre perforation pitch in mm.
            margin: Optional positive clear margin in mm. When omitted,
                SolidCraft uses the perforation diameter.
            pattern: Native perforation layout: "staggered" or "square".
                Defaults to "staggered".

        Use when:
            Describe manufacturing perforations that belong to sheet flat-pattern,
            DXF and measured-volume semantics without cutting repeated B-rep holes.

        Limits:
            This first slice covers the whole sheet only. Sketch/profile-bounded
            local perforation regions are intentionally outside the contract.
        """
        diameter_value = _pv(diameter)
        if not isfinite(diameter_value) or diameter_value <= 0:
            raise ValueError("sheet perforation diameter must be positive")

        pitch_value = _pv(pitch)
        if not isfinite(pitch_value) or pitch_value <= 0:
            raise ValueError("sheet perforation pitch must be positive")

        if margin is not None:
            margin_value = _pv(margin)
            if not isfinite(margin_value) or margin_value <= 0:
                raise ValueError(
                    "sheet perforation margin must be positive when provided"
                )

        if pattern not in ("staggered", "square"):
            raise ValueError(
                "sheet perforation pattern must be staggered or square"
            )

        return Shape(
            "sheet_perforate",
            (
                self,
                diameter,
                pitch,
                margin,
                pattern,
            ),
        )

    def path_flange(
        self,
        *,
        edge,
        path,
        radius=None,
    ):
        """Add a native path flange to existing sheet material.

        Parameters:
            edge: Fixed XYZ pick point on the existing sheet edge.
            path: Finished open connected Sketch chain describing the flange
                path across that edge.
            radius: Optional positive bend radius in mm. When omitted,
                SolidCraft inherits the active sheet rule.

        Use when:
            Create a multi-leg native flange from an existing sheet edge using
            one reusable open Sketch path.

        Limits:
            The initial SolidCraft 0.45 contract accepts line-only open chains.
            Tangent arcs and generic edge selectors are intentionally rejected
            until the native path-flange runtime proves those contracts.
        """
        if not isinstance(edge, (list, tuple)) or len(edge) != 3:
            raise ValueError("sheet path flange edge must have x, y and z")
        normalized_edge = []
        for coordinate in edge:
            if (
                isinstance(coordinate, bool)
                or not isinstance(coordinate, (int, float))
                or not isfinite(coordinate)
            ):
                raise ValueError(
                    "sheet path flange edge must contain fixed finite numbers"
                )
            normalized_edge.append(float(coordinate))

        if not isinstance(path, Shape) or path.kind != "sketch_open_chain":
            raise ValueError(
                "sheet path flange path must be a finished open connected Sketch chain"
            )
        segments = path.data[4]
        if not segments or any(segment[0] != "line" for segment in segments):
            raise ValueError(
                "sheet path flange currently requires a non-empty line-only Sketch chain"
            )

        if radius is not None:
            radius_value = _pv(radius)
            if not isfinite(radius_value) or radius_value <= 0:
                raise ValueError(
                    "sheet path flange radius must be positive when provided"
                )

        return Shape(
            "sheet_path_flange",
            (
                self,
                tuple(normalized_edge),
                path,
                radius,
            ),
        )

    def hem(
        self,
        *,
        edges,
        length,
        gap=None,
        flip=False,
    ):
        """Add a native hem to existing sheet material.

        Parameters:
            edges: Non-empty sequence of fixed XYZ pick points on sheet edges.
            length: Positive hem length in mm, measured to the outer face.
            gap: Optional positive clearance in mm between the returned leg and
                the face it folds over. When omitted, SolidCraft uses the sheet
                rule.
            flip: Reverse the hem side when True. Defaults to False.

        Use when:
            Fold one or more existing sheet edges back on the sheet while
            preserving native sheet-metal history and the inherited rule.

        Limits:
            This first slice accepts explicit fixed XYZ edge pick points only.
            Generic edge selectors and compound hem profiles are intentionally
            outside this contract.
        """
        if not isinstance(edges, (list, tuple)) or not edges:
            raise ValueError(
                "sheet hem edges must be a non-empty sequence of XYZ points"
            )
        normalized_edges = []
        for point in edges:
            if not isinstance(point, (list, tuple)) or len(point) != 3:
                raise ValueError("each sheet hem edge pick must have x, y and z")
            values = []
            for coordinate in point:
                if (
                    isinstance(coordinate, bool)
                    or not isinstance(coordinate, (int, float))
                    or not isfinite(coordinate)
                ):
                    raise ValueError(
                        "sheet hem edge picks must contain fixed finite numbers"
                    )
                values.append(float(coordinate))
            normalized_edges.append(tuple(values))

        length_value = _pv(length)
        if not isfinite(length_value) or length_value <= 0:
            raise ValueError("sheet hem length must be positive")

        if gap is not None:
            gap_value = _pv(gap)
            if not isfinite(gap_value) or gap_value <= 0:
                raise ValueError("sheet hem gap must be positive when provided")

        if not isinstance(flip, bool):
            raise TypeError("sheet hem flip must be True or False")

        return Shape(
            "sheet_hem",
            (
                self,
                tuple(normalized_edges),
                length,
                gap,
                flip,
            ),
        )

    def fold(
        self,
        *,
        line,
        angle=90,
        fixed=None,
        position="centerline",
        flip=False,
    ):
        """Fold existing sheet material along one straight line.

        Parameters:
            line: Either two fixed XY/XYZ points or the Shape returned by
                `Sketch.line(...)`. The Sketch-line form preserves native
                associativity when its endpoints use Parameters/Expressions.
            angle: Bend angle in degrees. Defaults to 90.
            fixed: Optional XYZ point on the side that must stay fixed.
            position: Native bend-line position: "centerline", "start", "end" or "mould". Defaults to "centerline".
            flip: Fold to the opposite side when True. Defaults to False.

        Use when:
            Bend material that already exists in a sheet blank. Dimensions and
            bend allowance come from the sheet's shared rule. Prefer an authored
            Sketch line when the bend line must follow later parameter edits.

        Limits:
            One straight fold line is supported. Fixed-point input remains
            numeric-only; associative input must be one `Sketch.line(...)`
            result.

        Example:
            with Sketch(name="Fold line", plane="XY") as fold_sketch:
                fold_line = fold_sketch.line(
                    start=(20, -(depth / 2)),
                    end=(20, depth / 2),
                )
            sheet.fold(
                line=fold_line,
                angle=90,
                fixed=(-20, 0, 0),
            )
        """
        if isinstance(line, Shape):
            if line.kind != "sketch_open_chain":
                raise ValueError(
                    "fold line Shape must be returned by Sketch.line(...)"
                )
            _name, _plane, _offset, _start, segments = line.data
            if len(segments) != 1 or segments[0][0] != "line":
                raise ValueError(
                    "fold Sketch line must contain exactly one straight line"
                )
            fold_line = line
        else:
            if not isinstance(line, (list, tuple)) or len(line) != 2:
                raise ValueError(
                    "fold line must contain exactly two points or use Sketch.line(...)"
                )

            def point3(value, label):
                if not isinstance(value, (list, tuple)) or len(value) not in (2, 3):
                    raise ValueError(f"{label} must be an XY or XYZ point")
                result = tuple(value) if len(value) == 3 else (value[0], value[1], 0)
                if not all(
                    isinstance(v, (int, float)) and not isinstance(v, bool)
                    for v in result
                ):
                    raise ValueError(
                        f"{label} coordinates must be fixed numbers; "
                        "associative fold lines require Sketch.line(...)"
                    )
                if not all(isfinite(v) for v in result):
                    raise ValueError(f"{label} must contain finite coordinates")
                return result

            p0 = point3(line[0], "fold line point")
            p1 = point3(line[1], "fold line point")
            if tuple(_pv(v) for v in p0) == tuple(_pv(v) for v in p1):
                raise ValueError("fold line points must be different")
            fold_line = (p0, p1)

        value = _pv(angle)
        if not isfinite(value) or value == 0 or abs(value) >= 180:
            raise ValueError("fold angle must be non-zero and below 180 degrees")

        if position not in ("centerline", "start", "end", "mould"):
            raise ValueError(
                "fold position must be centerline, start, end or mould"
            )
        if not isinstance(flip, bool):
            raise TypeError("fold flip must be True or False")

        def fixed_point3(value):
            if not isinstance(value, (list, tuple)) or len(value) not in (2, 3):
                raise ValueError("fold fixed must be an XY or XYZ point")
            result = tuple(value) if len(value) == 3 else (value[0], value[1], 0)
            if not all(
                isinstance(v, (int, float)) and not isinstance(v, bool)
                for v in result
            ):
                raise ValueError("fold fixed coordinates must be fixed numbers")
            if not all(isfinite(v) for v in result):
                raise ValueError("fold fixed must contain finite coordinates")
            return result

        fixed_point = None if fixed is None else fixed_point3(fixed)
        return Shape(
            "sheet_fold",
            (self, fold_line, angle, fixed_point, position, flip),
        )

    def fillet(self, radius, *, edges=Edges.VERTICAL):
        """Round selected solid edges with one radius.

        Parameters:
            radius: Fillet radius in mm.
            edges: Edge selection. Use Edges.from_faces(...) for native face-boundary topology, Edges.VERTICAL, a supported two-direction Box edge selector such as FRONT + LEFT, Edges.from_profile(...), Edges.from_vertices(...) or a non-empty sequence of XYZ edge pick points. Defaults to Edges.VERTICAL.

        Use when:
            Round one or more edges of a supported feature-based body. Fillet
            and chamfer use the same edge-selection forms.

        Limits:
            Edges.from_faces() resolves native SolidCraft topology for supported planar
            cardinal faces. Edges.VERTICAL and cardinal Box edge selectors
            require a supported rectangular body. Named profile/vertex
            selectors require matching Polygon2D ids in a supported extrusion.

        Example:
            body = Box(80, 50, 15)
            rounded = body.fillet(3, edges=Edges.VERTICAL)
        """
        _pv(radius)
        return Shape(
            "fillet",
            (self, radius, _feature_edge_selection(edges, operation="fillet")),
        )

    def chamfer(
        self,
        distance,
        *,
        distance2=None,
        flip=False,
        edges=Edges.VERTICAL,
    ):
        """Chamfer selected solid edges by equal or two native distances.

        Parameters:
            distance: Primary chamfer distance in mm.
            distance2: Optional secondary distance along the adjacent face. Omit for the existing equal-distance chamfer.
            flip: Swap which adjacent face receives the primary/secondary distance. Only meaningful with distance2. Defaults to False.
            edges: Edge selection. Use Edges.from_faces(...) for native face-boundary topology, Edges.VERTICAL, a supported two-direction Box edge selector such as FRONT + LEFT, Edges.from_profile(...), Edges.from_vertices(...) or a non-empty sequence of XYZ edge pick points. Defaults to Edges.VERTICAL.

        Use when:
            Bevel one or more edges of a supported feature-based body. Supply
            distance2 for an asymmetric native two-distance chamfer. Chamfer
            and fillet use the same edge-selection forms.

        Limits:
            Edges.from_faces() resolves native SolidCraft topology for supported planar
            cardinal faces. Edges.VERTICAL and cardinal Box edge selectors
            require a supported rectangular body. Named profile/vertex
            selectors require matching Polygon2D ids in a supported extrusion.
            flip=True requires distance2 because equal-distance chamfers have
            no meaningful primary/secondary face ordering.

        Example:
            body = Box(80, 50, 15)
            bevelled = body.chamfer(
                0.18,
                distance2=0.65,
                edges=Edges.VERTICAL,
            )
        """
        _pv(distance)
        if distance2 is not None:
            _pv(distance2)
        if not isinstance(flip, bool):
            raise TypeError("chamfer flip must be True or False")
        if flip and distance2 is None:
            raise ValueError("chamfer flip requires distance2")
        return Shape(
            "chamfer",
            (
                self,
                distance,
                _feature_edge_selection(edges, operation="chamfer"),
                distance2,
                flip,
            ),
        )

    def shell(self, thickness, *, open=Faces.TOP):
        """Hollow a supported solid and leave selected Faces open.

        Parameters:
            thickness: Wall thickness in mm.
            open: Face to remove, or a non-empty sequence of Faces values. Defaults to Faces.TOP.

        Use when:
            Create an enclosure-like body with an even wall thickness while
            removing one or more named planar faces.

        Limits:
            open= must be one Faces value or a non-empty sequence of Faces
            values. Support still depends on the underlying feature tree.

        Example:
            Box(80, 50, 30).shell(2, open=Faces.TOP)
        """
        _pv(thickness)
        if isinstance(open, Faces):
            faces = (open,)
        elif isinstance(open, (list, tuple)) and open:
            try:
                faces = tuple(Faces(face) for face in open)
            except ValueError as exc:
                raise ValueError("shell open faces must use Faces values") from exc
        else:
            raise ValueError("shell open must be a Faces value or non-empty sequence")
        return Shape("shell", (self, thickness, faces))

    def with_material(self, name, *, density_g_cm3, color=None):
        """Assign one design-owned physical material to the final body."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("material name must be a non-empty string")
        if not isinstance(density_g_cm3, (int, float)) or not 0 < density_g_cm3 <= 1000:
            raise ValueError("material density must be in (0, 1000] g/cm3")
        if color is not None and (not isinstance(color, str) or
                                  len(color) != 7 or color[0] != "#" or
                                  any(c not in "0123456789abcdefABCDEF" for c in color[1:])):
            raise ValueError("material color must be a #RRGGBB hex string")
        return Shape("material_assignment", (self, name, density_g_cm3, color))

    def with_appearance(self, color):
        """Assign a fixed display appearance color to the final body.

        Parameters:
            color: Hex display color in #RRGGBB form.

        Use when:
            The authored model should open with a specific visual color while
            physical material and BOM semantics remain unchanged.

        Limits:
            This first public contract assigns one opaque fixed color to the
            final body. Apply it after all geometry operations.
        """
        if (
            not isinstance(color, str)
            or len(color) != 7
            or color[0] != "#"
            or any(c not in "0123456789abcdefABCDEF" for c in color[1:])
        ):
            raise ValueError("appearance color must be a #RRGGBB hex string")
        return Shape("appearance_assignment", (self, color.upper()))

    def at(self, x=0, y=0, z=0, *, anchor=Anchor.CENTER, child=Anchor.CENTER):
        """Place a shape at absolute coordinates or align it to another Shape.

        Parameters:
            x: Absolute X coordinate in mm, or a target Shape for shape-to-shape alignment.
            y: Absolute Y coordinate in mm. Leave at 0 when x is a target Shape.
            z: Absolute Z coordinate in mm. Leave at 0 when x is a target Shape.
            anchor: Datum on this primitive that is placed at the requested coordinate. Defaults to Anchor.CENTER.
            child: Child datum for shape-to-shape alignment. Currently only Anchor.CENTER is supported.

        Use when:
            Use shape.at(x, y, z) for geometric placement. Box, Cylinder,
            Cone and Sphere support their documented anchors. Use shape.at(target) for the
            supported shape-to-shape CENTER alignment.

        Limits:
            Shape-to-shape alignment currently supports CENTER-to-CENTER only.
            at() is geometric placement/alignment; selecting a support face for
            a feature is the job of Shape.on().

        Example:
            pin = Cylinder(d=8, h=20, axis=Axis.X).at(10, 0, 5, anchor=Anchor.LEFT)
            centered = Sphere(5).at(body)
        """
        if isinstance(x, Shape):
            if y != 0 or z != 0:
                raise ValueError(
                    "at(target, ...) does not accept coordinate y/z arguments"
                )
            try:
                anchor = Anchor(anchor)
                child = Anchor(child)
            except ValueError as exc:
                raise ValueError("at() requires valid Anchor values") from exc
            if anchor is not Anchor.CENTER or child is not Anchor.CENTER:
                raise ValueError(
                    "shape-to-shape at() currently supports CENTER-to-CENTER only"
                )
            target_center = _shape_center(x)
            child_center = _shape_center(self)
            delta = tuple(
                _dim_sub(target_center[i], child_center[i])
                for i in range(3)
            )
            return Shape("translated", (self, delta))

        if self.kind == "box":
            if child is not Anchor.CENTER:
                raise ValueError("child= is only valid for shape-to-shape at()")
            selector = _direction_selector(anchor)
            return Shape("placed_box", (self, x, y, z, selector))

        if self.kind == "cylinder":
            if child is not Anchor.CENTER:
                raise ValueError("child= is only valid for shape-to-shape at()")
            height, diameter, axis, _origin_anchor = self.data
            selected = _direction_selector(anchor)
            placed = Shape("cylinder", (height, diameter, axis, selected))
            return Shape("placed3d", (placed, x, y, z))

        if self.kind == "cone":
            if child is not Anchor.CENTER:
                raise ValueError("child= is only valid for shape-to-shape at()")
            height, diameter, top_diameter, axis, _origin_anchor = self.data
            selected = _direction_selector(anchor)
            _cone_base_from_anchor(height, axis, (0, 0, 0), selected)
            placed = Shape(
                "cone",
                (height, diameter, top_diameter, axis, selected),
            )
            return Shape("placed3d", (placed, x, y, z))

        if self.kind == "sphere":
            if child is not Anchor.CENTER:
                raise ValueError("child= is only valid for shape-to-shape at()")
            radius, _origin_anchor = self.data
            selected = _direction_selector(anchor)
            placed = Shape("sphere", (radius, selected))
            return Shape("translated", (placed, (x, y, z)))

        if anchor is not Anchor.CENTER or child is not Anchor.CENTER:
            raise ValueError(
                "anchor/child are only valid for geometric primitives or "
                "shape-to-shape at()"
            )
        if self.kind not in (
            "circle", "rectangle", "polygon", "positioned", "cylinder", "hole",
            "lip", "snap_fit", "boss", "rest",
        ):
            raise ValueError("at() does not support this shape")
        return Shape(
            "placed3d" if self.kind in (
                "cylinder", "hole", "lip", "snap_fit", "boss", "rest"
            ) else "positioned",
            (self, x, y, z),
        )

    def rectangular_pattern(
        self,
        feature,
        *,
        count,
        spacing,
        direction=Axis.X,
        count2=None,
        spacing2=None,
        direction2=Axis.Y,
        alignment="right",
        alignment2="right",
        reversed=False,
        reversed2=False,
    ):
        """Pattern an existing native history feature in one or two directions.

        Parameters:
            feature: Existing applied feature Shape, or a non-empty sequence of applied feature Shapes. Forge resolves each source to its native history feature.
            count: Number of instances in the first direction. Use a positive integer or direct Parameter.
            spacing: Instance spacing in the first direction, in mm.
            direction: First pattern direction as Axis.X/Y/Z or a non-zero XYZ vector. Defaults to Axis.X.
            count2: Optional instance count for the second direction.
            spacing2: Optional spacing for the second direction, in mm.
            direction2: Second pattern direction as Axis.X/Y/Z or a non-zero XYZ vector. Defaults to Axis.Y.
            alignment: First-direction native alignment: "left", "center" or "right". Defaults to "right".
            alignment2: Second-direction native alignment: "left", "center" or "right". Defaults to "right".
            reversed: Reverse the first native pattern direction. Defaults to False.
            reversed2: Reverse the second native pattern direction. Defaults to False.

        Use when:
            Repeat an already-created native feature while keeping one editable
            SolidCraft rectangular-pattern history feature.

        Limits:
            The source feature must already be part of this Shape. Supplying a
            second direction requires both count2 and spacing2.

        Example:
            plate.rectangular_pattern(cut, count=3, spacing=24, direction=Axis.X, count2=2, spacing2=28)
        """
        sources = _feature_pattern_sources(self, feature, "rectangular_pattern")

        count = _pattern_count(count, "rectangular_pattern count")
        if _pv(spacing) <= 0:
            raise ValueError("rectangular_pattern spacing must be positive")
        dir1 = _pattern_direction(direction, "rectangular_pattern direction")

        second_requested = count2 is not None or spacing2 is not None
        if second_requested and (count2 is None or spacing2 is None):
            raise ValueError(
                "rectangular_pattern second direction requires count2 and spacing2"
            )
        if second_requested:
            count2 = _pattern_count(count2, "rectangular_pattern count2")
            if _pv(spacing2) <= 0:
                raise ValueError("rectangular_pattern spacing2 must be positive")
            dir2 = _pattern_direction(direction2, "rectangular_pattern direction2")
        else:
            count2 = spacing2 = dir2 = None

        if alignment not in ("left", "center", "right"):
            raise ValueError("rectangular_pattern alignment must be left, center or right")
        if second_requested and alignment2 not in ("left", "center", "right"):
            raise ValueError("rectangular_pattern alignment2 must be left, center or right")
        if not isinstance(reversed, bool) or not isinstance(reversed2, bool):
            raise TypeError("rectangular_pattern reversed flags must be bool")

        return Shape(
            "rectangular_pattern",
            (
                self, sources,
                dir1, count, spacing,
                dir2, count2, spacing2,
                alignment, alignment2,
                reversed, reversed2,
            ),
        )

    def circular_pattern(
        self,
        feature,
        *,
        count,
        axis=Axis.Z,
        angle=None,
        origin=None,
        alignment="right",
        reversed=False,
    ):
        """Pattern an existing native history feature around a fixed axis.

        Parameters:
            feature: Existing applied feature Shape, or a non-empty sequence of applied feature Shapes. Forge resolves each source to its native history feature.
            count: Total number of instances including the original. Use a positive integer or direct Parameter.
            axis: Rotation axis as Axis.X/Y/Z, AxisLine, or a non-zero fixed XYZ direction. Defaults to Axis.Z.
            angle: Optional total pattern angle in degrees, as a fixed number or direct Parameter. Omit it for SolidCraft's native 360-degree default.
            origin: Optional legacy XYZ point for a shifted fixed axis. Prefer AxisLine when the axis is shared or parameter-driven. Omit origin when axis is AxisLine.
            alignment: Native alignment: "left", "center" or "right". Defaults to "right".
            reversed: Reverse the native pattern direction. Defaults to False.

        Use when:
            Repeat an already-created native feature around an axis while
            keeping one editable SolidCraft circular-pattern history feature,
            for example a Hole-based bolt circle.

        Limits:
            The source feature must already be part of this Shape. Axis values
            cover principal or fixed XYZ axes. Native construction-axis,
            edge-axis and face-axis selectors are not exposed yet.

        Example:
            flange.circular_pattern(bolt_cut, count=6, axis=Axis.Z)
        """
        sources = _feature_pattern_sources(self, feature, "circular_pattern")
        count = _pattern_count(count, "circular_pattern count")
        axis_spec = _circular_pattern_axis(axis, origin)
        angle = _pattern_angle(angle, "circular_pattern angle")
        if alignment not in ("left", "center", "right"):
            raise ValueError(
                "circular_pattern alignment must be left, center or right"
            )
        if not isinstance(reversed, bool):
            raise TypeError("circular_pattern reversed must be bool")
        return Shape(
            "circular_pattern",
            (
                self,
                sources,
                axis_spec,
                count,
                angle,
                alignment,
                reversed,
            ),
        )

    def on(self, target, *, face=Faces.TOP, offset=(0, 0)):
        """Place a supported within-component feature on a target face.

        Parameters:
            target: Existing Shape that receives the feature.
            face: Cardinal target surface from the shared Faces vocabulary. Defaults to Faces.TOP.
            offset: In-plane offset from the target face centre, in mm. Defaults to (0, 0).

        Use when:
            Put a Hole or another supported feature on an existing Shape and
            describe its entry/support surface with the same Faces values used
            by shell() and Edges.from_faces().

        Limits:
            All six Faces values are accepted as topology intent. Individual
            placement lowerings may still reject a side face when that native
            SolidCraft placement path has not been qualified yet. Component
            assembly attachment uses Anchor instead.

        Example:
            Hole(d=8).on(plate, face=Faces.TOP, offset=(20, 0))
        """
        try:
            face = Faces(face)
        except ValueError as exc:
            raise ValueError("on() face must be a Faces value") from exc
        face_to_anchor = {
            Faces.TOP: Anchor.TOP,
            Faces.BOTTOM: Anchor.BOTTOM,
            Faces.LEFT: Anchor.LEFT,
            Faces.RIGHT: Anchor.RIGHT,
            Faces.FRONT: Anchor.FRONT,
            Faces.BACK: Anchor.BACK,
        }
        return self._anchor_to(target, face_to_anchor[face], Anchor.BOTTOM, offset)

    def attach(self, target, *, parent=Anchor.TOP, child=Anchor.BOTTOM,
               offset=(0, 0)):
        """Anchor a supported feature explicitly to another Shape.

        Parameters:
            target: Existing parent Shape that receives the feature.
            parent: Anchor on the target Shape. Defaults to Anchor.TOP.
            child: Anchor on the feature being placed. Defaults to Anchor.BOTTOM.
            offset: In-plane (x, y) offset on the parent anchor surface, in mm. Defaults to (0, 0).

        Use when:
            Use this lower-level feature-placement form when parent/child
            Anchor references are required explicitly.

        Limits:
            This is legacy within-component feature anchoring. Prefer on() for
            simple face placement. It is separate from component occurrence
            attachment used by assemblies.

        Example:
            Boss(d=7, h=12).attach(case, parent=Anchor.INNER_BOTTOM, offset=(10, 10))
        """
        return self._anchor_to(target, parent, child, offset)

    def _anchor_to(self, target, parent_anchor, child_anchor, offset):
        if self.kind not in (
            "cylinder", "linear_repeat", "hole",
            "lip", "snap_fit", "boss", "rest",
        ):
            raise ValueError(
                "attach() supports Cylinder, Hole, plastic features and their supported patterns"
            )
        if not isinstance(target, Shape):
            raise TypeError("anchor target must be an existing Shape")
        try:
            parent_anchor = Anchor(parent_anchor)
            child_anchor = Anchor(child_anchor)
        except ValueError as exc:
            raise ValueError("unknown parent or child anchor") from exc
        if not isinstance(offset, (tuple, list)) or len(offset) != 2:
            raise ValueError("offset must be a pair (x, y)")
        for index, value in enumerate(offset):
            if isinstance(value, _BoundOffset):
                expected_axis = "X" if index == 0 else "Y"
                if value.axis != expected_axis:
                    raise ValueError(
                        f"offset position {index} requires {expected_axis} bounds"
                    )
                if not isfinite(_pv(value.delta)):
                    raise ValueError("bound offset must be finite")
            else:
                _pv(value)
        return Shape(
            "anchored",
            (self, target, parent_anchor, child_anchor, tuple(offset)),
        )

def _shape(value):
    if not isinstance(value, Shape):
        raise TypeError("boolean operations require a Shape")
    return value
