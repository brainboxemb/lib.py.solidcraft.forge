"""Internal reusable-model and assembly nodes.

User scripts keep ordinary class names such as Block() and Enclosure().
These nodes are the compiler-facing representation; users do not need to
construct Component or Occurrence objects explicitly.
"""
from dataclasses import dataclass, field, replace
import re
from itertools import count
from math import isfinite

from .core import (
    Anchor,
    AnchorFrame,
    AnchorTopology,
    Axis,
    Shape,
    _DirectionSelector,
    _selector_anchor,
    _dim_add,
    _dim_sub,
    half,
    midpoint,
    parameters_in,
    _pv as pv,
)


_OCCURRENCE_IDS = count(1)


def _next_occurrence_id():
    """Return one process-local id for a Forge occurrence."""
    return next(_OCCURRENCE_IDS)



@dataclass(frozen=True)
class ModelDefinition:
    """One reusable user-model definition before SolidCraft lowering."""

    class_name: str
    parameters: tuple[tuple[str, float], ...]
    shape: Shape
    fixed_inputs: tuple[tuple[str, object], ...] = ()
    external_parameters: tuple[tuple[str, float], ...] = ()
    input_bindings: tuple[tuple[str, str], ...] = ()
    anchors: tuple[tuple[str, AnchorFrame | AnchorTopology], ...] = ()
    features: tuple[tuple[str, Shape], ...] = ()

    @property
    def key(self):
        return (
            self.class_name,
            self.parameters,
            self.fixed_inputs,
            self.external_parameters,
            self.input_bindings,
            self.anchors,
            tuple(name for name, _ in self.features),
        )


@dataclass(frozen=True)
class _ComponentFeatureReference:
    """Definition-level reference to one explicitly exported Forge feature."""

    definition_key: tuple
    name: str


@dataclass(frozen=True)
class _ComponentParameterReference:
    """Definition-level reference to one explicitly published component parameter."""

    definition_key: tuple
    name: str


@dataclass(frozen=True)
class Attachment:
    """Associative relationship between two model occurrences."""

    target: "ModelInstance"
    parent: Anchor | str | AnchorFrame | AnchorTopology | None
    child: Anchor | str | AnchorFrame | AnchorTopology | None
    offset: tuple[object, object]
    gap: object = 0
    angle: float | None = None
    kind: str | None = None
    value: float | None = None
    limits: tuple[float, float] | None = None
    flip: bool = False
    name: str | None = None
    as_built: bool = False


def _custom_anchor(instance, name):
    try:
        return dict(instance.definition.anchors)[name]
    except KeyError as exc:
        raise ValueError(
            f"{instance.definition.class_name} has no component anchor {name!r}"
        ) from exc


def _resolve_anchor_reference(instance, value):
    """Resolve a standard, composed, named, or direct attachment frame."""
    if isinstance(value, _DirectionSelector):
        return _selector_anchor(value)
    if isinstance(value, (Anchor, AnchorFrame, AnchorTopology)):
        return value
    if isinstance(value, str):
        try:
            return Anchor(value)
        except ValueError:
            _custom_anchor(instance, value)
            return value
    raise ValueError(
        "component attach requires a cardinal selector, Anchor, AnchorFrame, "
        "AnchorTopology or anchor name"
    )


def _anchor_local_point(instance, anchor):
    if isinstance(anchor, Anchor):
        return _anchor_point(instance, anchor)
    if isinstance(anchor, AnchorFrame):
        return anchor.origin
    if isinstance(anchor, AnchorTopology):
        return anchor.corner if anchor.corner is not None else anchor.edge
    custom = _custom_anchor(instance, anchor)
    if isinstance(custom, AnchorFrame):
        return custom.origin
    return custom.corner if custom.corner is not None else custom.edge


def _unwrap_rectangular_shape(shape):
    """Follow modifiers that retain the base component's nominal bounds."""
    while shape.kind in (
        "material_assignment",
        "appearance_assignment",
        "fillet",
        "chamfer",
        "shell",
        "union",
        "difference",
    ):
        shape = shape.data[0]
    return shape


def _xz_polygon_rectangle_bounds(shape):
    """Bounds for one rectangular XZ polygon extrusion.

    Polygon2D stores XZ sketch-local coordinates as (x, -z). The explicit
    Sketch may shift its XZ plane along world Y through Sketch(offset=...).
    This helper validates the four corners instead of treating an arbitrary
    polygon bbox as a rectangular attachment target.
    """
    shape = _unwrap_rectangular_shape(shape)
    if shape.kind != "sketch_base_extrusion":
        raise ValueError("not an XZ Sketch extrusion")

    (
        _, plane, origin, plane_offset, profiles, distance, direction,
        _operations, _profile_picks, _exact_regions, rotation,
    ) = shape.data
    if plane != "XZ" or origin is not None or rotation is not None:
        raise ValueError("not a supported XZ Sketch extrusion")
    if len(profiles) != 1:
        raise ValueError("XZ attachment rectangle requires one profile")

    profile, profile_anchor, profile_offset = profiles[0]
    if profile.kind != "polygon" or profile.data[1] != "XZ":
        raise ValueError("not an XZ polygon")
    if profile_anchor is not None:
        raise ValueError("XZ attachment polygon uses authored coordinates")
    if any(pv(value) != 0 for value in profile_offset):
        raise ValueError("XZ attachment polygon must use the Sketch origin")
    plane_y = 0.0 if plane_offset is None else pv(plane_offset)

    points = profile.data[0]
    if len(points) != 4:
        raise ValueError("XZ attachment rectangle requires four vertices")
    world_points = [(pv(u), -pv(v)) for u, v in points]
    xs = [point[0] for point in world_points]
    zs = [point[1] for point in world_points]
    xmin, xmax = min(xs), max(xs)
    zmin, zmax = min(zs), max(zs)
    if xmin == xmax or zmin == zmax:
        raise ValueError("degenerate XZ attachment rectangle")
    expected = {
        (xmin, zmin), (xmin, zmax), (xmax, zmin), (xmax, zmax)
    }
    if set(world_points) != expected:
        raise ValueError("XZ polygon is not an axis-aligned rectangle")

    depth = pv(distance)
    if depth <= 0:
        raise ValueError("attachment extrusion distance must be positive")
    if direction == "positive":
        ymin, ymax = plane_y, plane_y + depth
    elif direction == "negative":
        ymin, ymax = plane_y - depth, plane_y
    elif direction == "symmetric":
        ymin, ymax = plane_y - half(depth), plane_y + half(depth)
    else:
        raise ValueError("unsupported extrusion direction")

    return ((xmin, xmax), (ymin, ymax), (zmin, zmax))


def _rectangular_bounds(instance):
    """Return local axis-aligned bounds for a supported rectangular component."""
    from .placement import _base_rectangle

    shape = _unwrap_rectangular_shape(instance.definition.shape)
    try:
        (width, depth), (x, y, z), height = _base_rectangle(shape)
    except ValueError:
        try:
            return _xz_polygon_rectangle_bounds(shape)
        except ValueError as exc:
            raise ValueError(
                "component attach requires a supported rectangular model"
            ) from exc

    return (
        (x, _dim_add(x, width)),
        (y, _dim_add(y, depth)),
        (z, _dim_add(z, height)),
    )


_CORNER_ANCHORS = {
    Anchor.FRONT_TOP_LEFT,
    Anchor.FRONT_TOP_RIGHT,
    Anchor.FRONT_BOTTOM_LEFT,
    Anchor.FRONT_BOTTOM_RIGHT,
    Anchor.BACK_TOP_LEFT,
    Anchor.BACK_TOP_RIGHT,
    Anchor.BACK_BOTTOM_LEFT,
    Anchor.BACK_BOTTOM_RIGHT,
}


def _anchor_point(instance, anchor):
    """Local point represented by one reusable-component anchor."""
    bounds = _rectangular_bounds(instance)
    (xmin, xmax), (ymin, ymax), (zmin, zmax) = bounds
    xmid = midpoint(xmin, xmax)
    ymid = midpoint(ymin, ymax)
    zmid = midpoint(zmin, zmax)
    points = {
        Anchor.CENTER: (xmid, ymid, zmid),
        Anchor.LEFT: (xmin, ymid, zmid),
        Anchor.RIGHT: (xmax, ymid, zmid),
        Anchor.FRONT: (xmid, ymin, zmid),
        Anchor.BACK: (xmid, ymax, zmid),
        Anchor.BOTTOM: (xmid, ymid, zmin),
        Anchor.TOP: (xmid, ymid, zmax),
        Anchor.FRONT_TOP_LEFT: (xmin, ymin, zmax),
        Anchor.FRONT_TOP_RIGHT: (xmax, ymin, zmax),
        Anchor.FRONT_BOTTOM_LEFT: (xmin, ymin, zmin),
        Anchor.FRONT_BOTTOM_RIGHT: (xmax, ymin, zmin),
        Anchor.BACK_TOP_LEFT: (xmin, ymax, zmax),
        Anchor.BACK_TOP_RIGHT: (xmax, ymax, zmax),
        Anchor.BACK_BOTTOM_LEFT: (xmin, ymax, zmin),
        Anchor.BACK_BOTTOM_RIGHT: (xmax, ymax, zmin),
    }
    if anchor not in points:
        raise ValueError(f"{anchor} is not a supported assembly anchor")
    return points[anchor]


def _corner_origin_points(instance, anchor):
    """Return edge, face and corner picks for a native SolidCraft corner origin.

    The chosen edge is the vertical left/right edge of the front/back face.
    Its topology stays the same when height changes; SolidCraft stores that
    edge, the face and the second corner edge by name, so the origin follows
    saved-design dimension changes symmetrically on both sides.
    """
    if anchor not in _CORNER_ANCHORS:
        raise ValueError("corner origin requires a corner Anchor")
    (xmin, xmax), (ymin, ymax), (zmin, zmax) = _rectangular_bounds(instance)
    xmid = midpoint(xmin, xmax)
    zmid = midpoint(zmin, zmax)

    front = anchor.value.startswith("front_")
    left = anchor.value.endswith("_left")
    top = "_top_" in anchor.value
    y = ymin if front else ymax
    x = xmin if left else xmax
    z = zmax if top else zmin
    edge = (x, y, zmid)
    on = (xmid, y, zmid)
    corner = (x, y, z)
    return edge, on, corner


def _corner_native_x(anchor):
    """Native SolidCraft clocking axis for one standard corner anchor."""
    mapping = {
        Anchor.FRONT_TOP_LEFT: (0.0, 0.0, -1.0),
        Anchor.FRONT_TOP_RIGHT: (-1.0, 0.0, 0.0),
        Anchor.FRONT_BOTTOM_RIGHT: (0.0, 0.0, 1.0),
        Anchor.FRONT_BOTTOM_LEFT: (1.0, 0.0, 0.0),
        Anchor.BACK_TOP_LEFT: (1.0, 0.0, 0.0),
        Anchor.BACK_TOP_RIGHT: (0.0, 0.0, -1.0),
        Anchor.BACK_BOTTOM_RIGHT: (-1.0, 0.0, 0.0),
        Anchor.BACK_BOTTOM_LEFT: (0.0, 0.0, 1.0),
    }
    try:
        return mapping[anchor]
    except KeyError as exc:
        raise ValueError("corner clocking requires a corner Anchor") from exc


def _corner_normal(anchor):
    """Outward normal of the front/back face owning a corner anchor."""
    if anchor not in _CORNER_ANCHORS:
        raise ValueError("corner normal requires a corner Anchor")
    return (
        (0.0, -1.0, 0.0)
        if anchor.value.startswith("front_")
        else (0.0, 1.0, 0.0)
    )


def _anchor_origin(instance, anchor, occurrence, *, position=None):
    """Build one SolidCraft joint-origin reference for one known occurrence."""
    if position is None:
        position = instance.placement.position

    def world(point):
        return [
            point[i] + position[i]
            for i in range(3)
        ]

    if anchor in _CORNER_ANCHORS:
        edge, on, corner = _corner_origin_points(instance, anchor)
        result = {
            "edge": world(edge),
            "on": world(on),
            "corner": world(corner),
        }
    else:
        result = {
            "face": world(_anchor_point(instance, anchor)),
        }

    result["occurrence"] = occurrence
    return result


def _face_offset(anchor, offset):
    """Map a two-value face offset into XYZ."""
    u, v = offset
    if anchor in (Anchor.LEFT, Anchor.RIGHT):
        return (0.0, u, v)
    if anchor in (Anchor.FRONT, Anchor.BACK):
        return (u, 0.0, v)
    if anchor in (Anchor.TOP, Anchor.BOTTOM):
        return (u, v, 0.0)
    if anchor is Anchor.CENTER:
        return (u, v, 0.0)
    if anchor in _CORNER_ANCHORS and u == 0 and v == 0:
        return (0.0, 0.0, 0.0)
    raise ValueError("unsupported assembly anchor")


def _normalize_rotation(axis, degrees):
    """Return one validated numeric axis-angle placement."""
    if degrees is None:
        raise ValueError("placement rotation requires an angle in degrees")
    if isinstance(axis, Axis):
        axis = axis.value
    if isinstance(axis, str):
        named_axes = {
            "X": (1, 0, 0),
            "Y": (0, 1, 0),
            "Z": (0, 0, 1),
        }
        try:
            axis = named_axes[axis]
        except KeyError as exc:
            raise ValueError(
                "placement rotation named axis must be X, Y or Z"
            ) from exc
    if not isinstance(axis, (tuple, list)) or len(axis) != 3:
        raise ValueError(
            "placement rotation axis must be X, Y, Z or an XYZ triple"
        )
    try:
        values = tuple(float(pv(value)) for value in axis)
        angle = float(pv(degrees))
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "placement rotation requires numeric axis and degrees"
        ) from exc
    if not all(isfinite(value) for value in (*values, angle)):
        raise ValueError("placement rotation requires finite values")
    if sum(value * value for value in values) <= 0:
        raise ValueError("placement rotation axis must be non-zero")
    return values, angle


@dataclass(frozen=True)
class Placement:
    """Absolute pose of one occurrence in its parent coordinate frame.

    Parameters:
        x: Absolute X position in mm. May be numeric, Parameter or Expression.
        y: Absolute Y position in mm. May be numeric, Parameter or Expression.
        z: Absolute Z position in mm. May be numeric, Parameter or Expression.
        rotation: Optional (axis, degrees) absolute rotation. axis may be X/Y/Z, Axis, or a non-zero XYZ vector.

    Use when:
        Declare the pose of a component occurrence at creation or copy time.

    Limits:
        Placement is occurrence creation state, not a relative move action.
        Coordinates, rotation axis and angle must evaluate to finite values.

    Example:
        Placement(x=160, z=20, rotation=(Axis.Z, 90))
    """

    x: object = 0
    y: object = 0
    z: object = 0
    rotation: tuple[object, object] | None = None

    def __post_init__(self):
        concrete = tuple(pv(value) for value in self.position)
        if not all(isfinite(value) for value in concrete):
            raise ValueError("placement requires finite coordinates")
        if self.rotation is not None:
            if (
                not isinstance(self.rotation, (tuple, list))
                or len(self.rotation) != 2
            ):
                raise ValueError(
                    "placement rotation must be an (axis, degrees) pair"
                )
            axis, degrees = self.rotation
            object.__setattr__(
                self,
                "rotation",
                _normalize_rotation(axis, degrees),
            )

    @property
    def position(self):
        """Return the absolute XYZ coordinates as a tuple."""
        return (self.x, self.y, self.z)

    @property
    def values(self):
        """Return the absolute XYZ coordinates as a tuple."""
        return self.position

    def __iter__(self):
        return iter(self.position)

    def __len__(self):
        return 3

    def __getitem__(self, index):
        return self.position[index]


@dataclass(frozen=True)
class ModelInstance:
    """One placed occurrence of a reusable model definition."""

    definition: ModelDefinition
    placement: Placement = Placement()
    attachment: Attachment | None = None
    group_name: str | None = None
    name: str | None = None
    flattened_parameters: tuple[str, ...] = ()
    _configuration: object | None = field(
        default=None,
        repr=False,
        compare=False,
    )
    _occurrence_id: int = field(
        default_factory=_next_occurrence_id,
        repr=False,
        compare=False,
    )

    def configure(self, *, active, columns, rows):
        """Attach one editable configuration definition to this final model."""
        from .configurations import _configure_model
        return _configure_model(
            self,
            active=active,
            columns=columns,
            rows=rows,
        )

    @property
    def occurrence_id(self):
        """Internal Forge id for this physical occurrence."""
        return self._occurrence_id

    def feature(self, name):
        """Reference one feature explicitly exported by this component definition.

        The returned value identifies Forge-authored definition history, not one
        physical occurrence and not a SolidCraft feature id. All occurrences
        that reuse this definition therefore resolve the same native feature.
        """
        if (
            not isinstance(name, str)
            or not name.isidentifier()
            or name.startswith("_")
        ):
            raise ValueError("component feature name must be a public Python identifier")
        if name not in {feature_name for feature_name, _ in self.definition.features}:
            raise ValueError(
                f"{self.definition.class_name} has no exported component feature {name!r}"
            )
        return _ComponentFeatureReference(self.definition.key, name)

    def parameter(self, name):
        """Reference one explicitly published parameter of this component definition.

        The returned value identifies a component-definition parameter, not one
        occurrence-local value and not a SolidCraft parameter name. All copies
        that reuse this definition therefore resolve the same native parameter.
        """
        if (
            not isinstance(name, str)
            or not name.isidentifier()
            or name.startswith("_")
        ):
            raise ValueError(
                "component parameter name must be a public Python identifier"
            )
        if name not in {parameter_name for parameter_name, _ in self.definition.parameters}:
            raise ValueError(
                f"{self.definition.class_name} has no published component parameter {name!r}"
            )
        return _ComponentParameterReference(self.definition.key, name)

    def group(self, name):
        """Place this occurrence in a named native subassembly component.

        Parameters:
            name: Native group/subassembly name.

        Use when:
            Give one occurrence a useful native browser/subassembly parent.

        Limits:
            Grouping changes hierarchy only. It does not align, attach or
            otherwise create a mechanical relationship. One occurrence cannot
            belong to several different groups.

        Example:
            grouped = bracket.group("Mounting brackets")
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("group name must be non-empty text")
        if self.group_name is not None and self.group_name != name:
            raise ValueError("an occurrence cannot belong to multiple groups")
        return replace(self, group_name=name)

    def copy(self, *, name=None, placement=None):
        """Create another occurrence of the same reusable definition.

        Parameters:
            name: Optional explicit Forge name for the new occurrence.
            placement: Optional absolute Placement for the new occurrence. When omitted, the source placement is inherited.

        Use when:
            Reuse one component definition for another physical occurrence.

        Limits:
            Attachment state is occurrence-specific and is not copied.

        Example:
            right = left.copy(name="right", placement=Placement(x=160))
        """
        if placement is not None and not isinstance(placement, Placement):
            raise TypeError("copy placement must be a Placement")
        return replace(
            self,
            placement=self.placement if placement is None else placement,
            attachment=None,
            name=name,
            _occurrence_id=_next_occurrence_id(),
        )

    def attach(self, target, *, parent=Anchor.RIGHT, child=Anchor.LEFT,
               offset=(0, 0), gap=0, angle=None, as_built=False,
               kind=None, value=None, limits=None, flip=False, name=None):
        """Create an associative relationship to another component occurrence.

        The default remains the existing rigid/planar attachment. Set
        kind="revolute" explicitly for one-axis rotational motion.

        Parameters:
            target: Parent component occurrence to attach to.
            parent: Attachment reference on target. Defaults to Anchor.RIGHT.
            child: Attachment reference on this occurrence. Defaults to Anchor.LEFT.
            offset: In-plane (u, v) offset in mm. Defaults to (0, 0).
            gap: Separation along the parent anchor normal, in mm.
            angle: Optional joint-frame rotation in degrees.
            as_built: Keep existing poses and create an as-built rigid joint.
            kind: Optional relationship kind. Only "revolute" is explicit.
            value: Initial revolute angle in degrees. Defaults to 0.
            limits: Optional (minimum, maximum) revolute limits in degrees.
            flip: Native joint-origin flip for a revolute relationship.
            name: Optional native joint name.

        Limits:
            Revolute relationships currently require zero in-plane offset.
            value and limits are fixed finite degree values.
            as_built=True requires all other relationship arguments to remain
            at their defaults.
        """
        if not isinstance(target, ModelInstance):
            raise TypeError("component attach target must be another model object")
        if kind not in (None, "revolute"):
            raise ValueError("component attach kind must be 'revolute' or omitted")
        if not isinstance(flip, bool):
            raise TypeError("component attach flip must be a bool")
        if name is not None:
            if not isinstance(name, str) or not name.strip():
                raise ValueError("component attach name must be non-empty")
            name = name.strip()

        if as_built:
            if (
                parent != Anchor.RIGHT
                or child != Anchor.LEFT
                or tuple(offset) != (0, 0)
                or gap != 0
                or angle is not None
                or kind is not None
                or value is not None
                or limits is not None
                or flip
                or name is not None
            ):
                raise ValueError(
                    "as-built attach does not take anchors, offset, gap, angle, "
                    "kind, value, limits, flip or name"
                )
            return replace(
                self,
                attachment=Attachment(
                    target=target,
                    parent=None,
                    child=None,
                    offset=(0.0, 0.0),
                    as_built=True,
                ),
            )

        parent = _resolve_anchor_reference(target, parent)
        child = _resolve_anchor_reference(self, child)
        if parent is Anchor.INNER_BOTTOM or child is Anchor.INNER_BOTTOM:
            raise ValueError("Anchor.INNER_BOTTOM is not an assembly face anchor")
        if not isinstance(offset, (tuple, list)) or len(offset) != 2:
            raise ValueError("component attach offset must be an (u, v) pair")
        face_offset = tuple(offset)
        face_offset_values = tuple(pv(item) for item in face_offset)
        if not all(isfinite(item) for item in face_offset_values):
            raise ValueError("component attach offset must be finite")
        if kind == "revolute" and any(item != 0 for item in face_offset_values):
            raise ValueError("revolute attach does not support in-plane offset")

        gap_value = pv(gap)
        if not isfinite(gap_value):
            raise ValueError("component attach gap must be finite")

        angle_value = None
        if angle is not None:
            angle_value = pv(angle)
            if not isfinite(angle_value):
                raise ValueError("component attach angle must be finite")

        revolute_value = None
        revolute_limits = None
        if kind == "revolute":
            revolute_value = 0.0 if value is None else float(pv(value))
            if not isfinite(revolute_value):
                raise ValueError("revolute attach value must be finite")
            if limits is not None:
                if not isinstance(limits, (tuple, list)) or len(limits) != 2:
                    raise ValueError("revolute attach limits must be a (min, max) pair")
                lower = float(pv(limits[0]))
                upper = float(pv(limits[1]))
                if not isfinite(lower) or not isfinite(upper):
                    raise ValueError("revolute attach limits must be finite")
                if lower > upper:
                    raise ValueError("revolute attach minimum limit exceeds maximum")
                if revolute_value < lower or revolute_value > upper:
                    raise ValueError("revolute attach value lies outside its limits")
                revolute_limits = (lower, upper)
        elif value is not None or limits is not None or flip:
            raise ValueError(
                "component attach value, limits and flip require kind='revolute'"
            )

        target_local = _anchor_local_point(target, parent)
        child_local = _anchor_local_point(self, child)

        tangent = (0.0, 0.0, 0.0)
        normal = (0.0, 0.0, 0.0)
        if parent in (
            Anchor.LEFT,
            Anchor.RIGHT,
            Anchor.FRONT,
            Anchor.BACK,
            Anchor.TOP,
            Anchor.BOTTOM,
            Anchor.CENTER,
        ):
            tangent = _face_offset(parent, face_offset)
            if parent is not Anchor.CENTER:
                normal = parent.vector

        normal_offset = tuple(
            0
            if component == 0
            else gap
            if component > 0
            else -gap
            for component in normal
        )
        target_world = tuple(
            _dim_add(
                _dim_add(
                    _dim_add(target_local[i], target.placement.position[i]),
                    tangent[i],
                ),
                normal_offset[i],
            )
            for i in range(3)
        )
        translation = tuple(
            _dim_sub(target_world[i], child_local[i])
            for i in range(3)
        )

        return replace(
            self,
            placement=replace(
                self.placement,
                x=translation[0],
                y=translation[1],
                z=translation[2],
            ),
            attachment=Attachment(
                target=target,
                parent=parent,
                child=child,
                offset=face_offset,
                gap=gap,
                angle=angle_value,
                kind=kind,
                value=revolute_value,
                limits=revolute_limits,
                flip=flip,
                name=name,
            ),
        )

    def with_drawing(
        self,
        *,
        name=None,
        template="iso-a4-part",
        sheet_name="Sheet 1",
        scale=None,
        gap_mm=20,
        views=None,
        properties=None,
        title_block=None,
        title_block_style=None,
        revision=None,
        notes=(),
        dimensions=(),
    ):
        """Add a native technical drawing for this component occurrence.

        The drawing belongs to the final design presentation, not to the
        reusable component definition. Calling this on a standalone occurrence
        therefore returns a one-occurrence Assembly carrying the drawing.
        """
        return Assembly((self,)).with_drawing(
            self,
            name=name,
            template=template,
            sheet_name=sheet_name,
            scale=scale,
            gap_mm=gap_mm,
            views=views,
            properties=properties,
            title_block=title_block,
            title_block_style=title_block_style,
            revision=revision,
            notes=notes,
            dimensions=dimensions,
        )

    def __add__(self, other):
        return Assembly((self,)) + other

    __or__ = __add__


@dataclass(frozen=True)
class AssemblyAnchor:
    """Named attachment reference owned by an assembly.

    The target occurrence remains the real SolidCraft attachment target; the
    reference is a standard/direct component anchor interpreted in that
    occurrence. This lets an assembly expose semantic datums without putting
    application-specific anchors on the reusable component definition.
    """

    target: ModelInstance
    reference: Anchor | str | AnchorFrame | AnchorTopology
    offset: tuple[object, object] = (0, 0)


def _drawing_xy(value, name):
    """Return one finite drawing-paper XY pair."""

    if isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be an (x, y) pair")
    try:
        values = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{name} must be an (x, y) pair") from exc
    if len(values) != 2:
        raise ValueError(f"{name} must be an (x, y) pair")
    result = tuple(float(pv(item)) for item in values)
    if not all(isfinite(item) for item in result):
        raise ValueError(f"{name} must contain finite values")
    return result


def _drawing_xyz(value, name):
    """Return one finite model-space XYZ pick."""

    if isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be an (x, y, z) point")
    try:
        values = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{name} must be an (x, y, z) point") from exc
    if len(values) != 3:
        raise ValueError(f"{name} must be an (x, y, z) point")
    result = tuple(float(pv(item)) for item in values)
    if not all(isfinite(item) for item in result):
        raise ValueError(f"{name} must contain finite values")
    return result


@dataclass(frozen=True)
class DrawingView:
    """Placement/display override for one standard drawing view."""

    at: tuple[float, float] | None = None
    scale: str | None = None
    visual_style: str | None = None

    def __post_init__(self):
        if self.at is not None:
            object.__setattr__(self, "at", _drawing_xy(self.at, "drawing view at"))
        if self.scale is not None:
            if not isinstance(self.scale, str) or not self.scale.strip():
                raise ValueError("drawing view scale must be non-empty text")
            object.__setattr__(self, "scale", self.scale.strip())
        if self.visual_style is not None:
            if self.visual_style != "shaded":
                raise ValueError(
                    "drawing view visual_style currently supports only 'shaded'"
                )


@dataclass(frozen=True)
class DrawingNote:
    """One native sheet note positioned in paper millimetres."""

    content: str
    at: tuple[float, float]
    cap_mm: float = 3.5
    align: str = "left"

    def __post_init__(self):
        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("drawing note content must be non-empty text")
        object.__setattr__(self, "content", self.content.strip())
        object.__setattr__(self, "at", _drawing_xy(self.at, "drawing note at"))
        cap = float(self.cap_mm)
        if not isfinite(cap) or not 0.5 <= cap <= 100:
            raise ValueError("drawing note cap_mm must be between 0.5 and 100")
        object.__setattr__(self, "cap_mm", cap)
        if self.align not in {"left", "centre", "right"}:
            raise ValueError(
                "drawing note align must be left, centre or right"
            )


@dataclass(frozen=True)
class DrawingRevision:
    """One native drawing revision row."""

    revision: str | None = None
    description: str | None = None
    designer: str | None = None
    checker: str | None = None
    date: str | None = None
    hidden: bool = False

    def __post_init__(self):
        values = {}
        for name in ("revision", "description", "designer", "checker", "date"):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f"drawing revision {name} must be non-empty text"
                    )
                value = value.strip()
                object.__setattr__(self, name, value)
                values[name] = value
        if not values:
            raise ValueError("drawing revision requires at least one text field")
        if not isinstance(self.hidden, bool):
            raise ValueError("drawing revision hidden must be a bool")


@dataclass(frozen=True)
class DrawingDimension:
    """One native drawing dimension resolved from model-space picks."""

    view: str
    kind: str
    a: tuple[float, float, float] | None = None
    b: tuple[float, float, float] | None = None
    edge: tuple[float, float, float] | None = None
    direction: str = "aligned"
    diameter: bool | None = None
    offset_mm: float = 10.0
    override_text: str | None = None
    decimals: int = 2
    line_through_mm: tuple[float, float] | None = None

    @classmethod
    def linear(
        cls,
        view,
        a,
        b,
        *,
        direction="aligned",
        offset_mm=10,
        override_text=None,
        decimals=2,
        line_through_mm=None,
    ):
        """Dimension two model corners/points in one drawing view."""

        return cls(
            view=view,
            kind="linear",
            a=a,
            b=b,
            direction=direction,
            offset_mm=offset_mm,
            override_text=override_text,
            decimals=decimals,
            line_through_mm=line_through_mm,
        )

    @classmethod
    def faces(
        cls,
        view,
        a,
        b,
        *,
        direction="aligned",
        offset_mm=10,
        override_text=None,
        decimals=2,
        line_through_mm=None,
    ):
        """Dimension two parallel planar model faces in one drawing view."""

        return cls(
            view=view,
            kind="faces",
            a=a,
            b=b,
            direction=direction,
            offset_mm=offset_mm,
            override_text=override_text,
            decimals=decimals,
            line_through_mm=line_through_mm,
        )

    @classmethod
    def radial(
        cls,
        view,
        edge,
        *,
        diameter=None,
        offset_mm=10,
        override_text=None,
        decimals=2,
        line_through_mm=None,
    ):
        """Dimension one circular edge seen face-on in one drawing view."""

        return cls(
            view=view,
            kind="radial",
            edge=edge,
            diameter=diameter,
            offset_mm=offset_mm,
            override_text=override_text,
            decimals=decimals,
            line_through_mm=line_through_mm,
        )

    def __post_init__(self):
        if self.view not in {"front", "top", "right", "iso"}:
            raise ValueError(
                "drawing dimension view must be front, top, right or iso"
            )
        if self.kind not in {"linear", "faces", "radial"}:
            raise ValueError(
                "drawing dimension kind must be linear, faces or radial"
            )
        if self.kind in {"linear", "faces"}:
            if self.a is None or self.b is None or self.edge is not None:
                raise ValueError(
                    f"{self.kind} drawing dimension requires a and b"
                )
            object.__setattr__(self, "a", _drawing_xyz(self.a, "dimension a"))
            object.__setattr__(self, "b", _drawing_xyz(self.b, "dimension b"))
            if self.direction not in {"aligned", "horizontal", "vertical"}:
                raise ValueError(
                    "linear drawing dimension direction must be aligned, "
                    "horizontal or vertical"
                )
            if self.diameter is not None:
                raise ValueError(
                    f"{self.kind} drawing dimension has no diameter flag"
                )
        else:
            if self.edge is None or self.a is not None or self.b is not None:
                raise ValueError("radial drawing dimension requires edge")
            object.__setattr__(
                self,
                "edge",
                _drawing_xyz(self.edge, "dimension edge"),
            )
            if self.diameter is not None and not isinstance(self.diameter, bool):
                raise ValueError("radial dimension diameter must be bool or None")

        offset = float(self.offset_mm)
        if not isfinite(offset):
            raise ValueError("drawing dimension offset_mm must be finite")
        object.__setattr__(self, "offset_mm", offset)
        if (
            isinstance(self.decimals, bool)
            or not isinstance(self.decimals, int)
            or not 0 <= self.decimals <= 6
        ):
            raise ValueError("drawing dimension decimals must be 0..6")
        if self.override_text is not None:
            if (
                not isinstance(self.override_text, str)
                or not self.override_text.strip()
            ):
                raise ValueError(
                    "drawing dimension override_text must be non-empty text"
                )
            object.__setattr__(
                self,
                "override_text",
                self.override_text.strip(),
            )
        if self.line_through_mm is not None:
            object.__setattr__(
                self,
                "line_through_mm",
                _drawing_xy(
                    self.line_through_mm,
                    "drawing dimension line_through_mm",
                ),
            )


@dataclass(frozen=True)
class ComponentDrawing:
    """One native SolidCraft drawing owned by the final design."""

    name: str
    target_occurrence_id: int
    template: str = "iso-a4-part"
    sheet_name: str = "Sheet 1"
    pdf_path: str = ""
    scale: str | None = None
    gap_mm: float = 20.0
    views: tuple[tuple[str, DrawingView], ...] = ()
    properties: tuple[tuple[str, str], ...] = ()
    title_block: tuple[tuple[str, str | None], ...] = ()
    title_block_style: str | None = None
    revision: DrawingRevision | None = None
    notes: tuple[DrawingNote, ...] = ()
    dimensions: tuple[DrawingDimension, ...] = ()


@dataclass(frozen=True)
class ExplodedView:
    """One persistent native exploded presentation owned by an Assembly."""

    name: str
    scale: float | None = None
    moves: tuple[tuple[int, tuple[float, float, float]], ...] = ()


@dataclass(frozen=True)
class Assembly:
    """Ordered collection of reusable model occurrences."""

    instances: tuple[ModelInstance, ...]
    anchors: tuple[tuple[str, AssemblyAnchor], ...] = ()
    exploded_views: tuple[ExplodedView, ...] = ()
    exploded_display: str | None = None
    exploded_display_set: bool = False
    drawings: tuple[ComponentDrawing, ...] = ()
    _configuration: object | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    def configure(self, *, active, columns, rows):
        """Attach one editable configuration definition to this final model."""
        from .configurations import _configure_model
        return _configure_model(
            self,
            active=active,
            columns=columns,
            rows=rows,
        )

    def group(self, name):
        """Wrap these assembly occurrences in a real nested native component.

        Parameters:
            name: Native subassembly/browser component name.

        Use when:
            The collection should appear as one named subassembly/browser unit
            in SolidCraft.

        Limits:
            Grouping changes native hierarchy, not placement or relationships.
            Use attach() for mechanical relationships between occurrences.

        Example:
            frame = (left + right).group("Frame")
        """
        grouped = tuple(instance.group(name) for instance in self.instances)
        remap = {
            original.occurrence_id: replacement
            for original, replacement in zip(self.instances, grouped)
        }

        # Direct attachments keep pointing at the same physical Forge
        # occurrence, but use the grouped replacement object when that target is
        # part of this Assembly. Chained attachments remain unsupported by the
        # compiler and are not rebuilt here.
        grouped = tuple(
            replace(
                instance,
                attachment=replace(
                    instance.attachment,
                    target=remap.get(
                        instance.attachment.target.occurrence_id,
                        instance.attachment.target,
                    ),
                ),
            )
            if instance.attachment is not None
            else instance
            for instance in grouped
        )
        remap = {
            instance.occurrence_id: instance
            for instance in grouped
        }

        anchors = tuple(
            (
                anchor_name,
                AssemblyAnchor(
                    target=remap[anchor.target.occurrence_id],
                    reference=anchor.reference,
                    offset=anchor.offset,
                ),
            )
            for anchor_name, anchor in self.anchors
        )
        return replace(
            self,
            instances=grouped,
            anchors=anchors,
        )

    def with_drawing(
        self,
        target,
        *,
        name=None,
        template="iso-a4-part",
        sheet_name="Sheet 1",
        scale=None,
        gap_mm=20,
        views=None,
        properties=None,
        title_block=None,
        title_block_style=None,
        revision=None,
        notes=(),
        dimensions=(),
    ):
        """Add a native technical drawing of one component occurrence.

        Compose the final Assembly first, then select the occurrence the sheet
        documents. Standard views remain native SolidCraft views; optional
        authoring data controls their paper layout, dimensions, notes and title
        information without drawing model-specific graphics in Forge.
        """
        if not isinstance(target, ModelInstance):
            raise TypeError("drawing target must be a component occurrence")
        owned = {instance.occurrence_id for instance in self.instances}
        if target.occurrence_id not in owned:
            raise ValueError("drawing target must belong to this assembly")

        if name is None:
            base = target.name or target.definition.class_name
            name = f"{base} drawing"
        if not isinstance(name, str) or not name.strip():
            raise ValueError("drawing name must be non-empty text")
        name = name.strip()
        if any(drawing.name == name for drawing in self.drawings):
            raise ValueError(f"drawing {name!r} already exists")

        pdf_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-.")
        if not pdf_stem:
            raise ValueError("drawing name cannot produce a safe PDF filename")
        pdf_path = f"drawings/{pdf_stem}.pdf"
        if any(drawing.pdf_path == pdf_path for drawing in self.drawings):
            raise ValueError(f"drawing PDF path {pdf_path!r} already exists")

        if not isinstance(template, str) or not template.strip():
            raise ValueError("drawing template must be non-empty text")
        if not isinstance(sheet_name, str) or not sheet_name.strip():
            raise ValueError("drawing sheet name must be non-empty text")

        if scale is not None:
            if not isinstance(scale, str) or not scale.strip():
                raise ValueError("drawing scale must be non-empty text")
            scale = scale.strip()
        gap = float(gap_mm)
        if not isfinite(gap) or not 0 <= gap <= 1000:
            raise ValueError("drawing gap_mm must be between 0 and 1000")

        if views is None:
            view_rows = ()
        else:
            if not isinstance(views, dict):
                raise TypeError("drawing views must be a mapping")
            allowed_views = {"front", "top", "right", "iso"}
            unknown = sorted(set(views) - allowed_views)
            if unknown:
                raise ValueError(
                    "unsupported drawing view(s): " + ", ".join(unknown)
                )
            if not all(isinstance(value, DrawingView) for value in views.values()):
                raise TypeError("drawing views must contain DrawingView values")
            view_rows = tuple(views.items())

        property_keys = {
            "project",
            "part_number",
            "revision",
            "author",
            "organization",
            "description",
            "license",
        }
        if properties is None:
            property_rows = ()
        else:
            if not isinstance(properties, dict):
                raise TypeError("drawing properties must be a mapping")
            unknown = sorted(set(properties) - property_keys)
            if unknown:
                raise ValueError(
                    "unsupported drawing property keys: " + ", ".join(unknown)
                )
            normalized = []
            for key, value in properties.items():
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f"drawing property {key} must be non-empty text"
                    )
                normalized.append((key, value.strip()))
            property_rows = tuple(normalized)

        if title_block is None:
            title_rows = ()
        else:
            if not isinstance(title_block, dict):
                raise TypeError("drawing title_block must be a mapping")
            normalized = []
            for key, value in title_block.items():
                if not isinstance(key, str) or not key.strip():
                    raise ValueError(
                        "drawing title block cell names must be non-empty text"
                    )
                if value is not None and (
                    not isinstance(value, str) or not value.strip()
                ):
                    raise ValueError(
                        f"drawing title block {key} must be text or None"
                    )
                normalized.append(
                    (key.strip(), None if value is None else value.strip())
                )
            title_rows = tuple(normalized)

        if title_block_style is not None:
            if title_block_style not in {"built-in", "compact"}:
                raise ValueError(
                    "drawing title_block_style must be 'built-in' or 'compact'"
                )

        if revision is not None and not isinstance(revision, DrawingRevision):
            raise TypeError("drawing revision must be a DrawingRevision")
        note_rows = tuple(notes)
        if not all(isinstance(item, DrawingNote) for item in note_rows):
            raise TypeError("drawing notes must contain DrawingNote values")
        dimension_rows = tuple(dimensions)
        if not all(
            isinstance(item, DrawingDimension) for item in dimension_rows
        ):
            raise TypeError(
                "drawing dimensions must contain DrawingDimension values"
            )

        return replace(
            self,
            drawings=self.drawings + (
                ComponentDrawing(
                    name=name,
                    target_occurrence_id=target.occurrence_id,
                    template=template.strip(),
                    sheet_name=sheet_name.strip(),
                    pdf_path=pdf_path,
                    scale=scale,
                    gap_mm=gap,
                    views=view_rows,
                    properties=property_rows,
                    title_block=title_rows,
                    title_block_style=title_block_style,
                    revision=revision,
                    notes=note_rows,
                    dimensions=dimension_rows,
                ),
            ),
        )

    def with_exploded_view(self, name, *, scale=None, moves=None):
        """Add one native SolidCraft exploded presentation to this Assembly.

        Define exploded views after composing the final Assembly. Use either
        automatic scale mode or explicit occurrence translations.
        """
        if len(self.instances) < 2:
            raise ValueError("exploded view requires at least two occurrences")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("exploded view name must be non-empty text")
        name = name.strip()
        if any(view.name == name for view in self.exploded_views):
            raise ValueError(f"exploded view {name!r} already exists")
        if moves is not None and scale is not None:
            raise ValueError("exploded view uses either scale or explicit moves")

        normalized_scale = None
        if scale is not None:
            if (
                isinstance(scale, bool)
                or not isinstance(scale, (int, float))
                or not isfinite(scale)
                or scale <= 0
            ):
                raise ValueError(
                    "exploded view scale must be a positive finite number"
                )
            normalized_scale = float(scale)

        normalized_moves = ()
        if moves is not None:
            if not isinstance(moves, (tuple, list)) or not moves:
                raise ValueError(
                    "exploded view moves must be a non-empty sequence"
                )
            owned = {instance.occurrence_id for instance in self.instances}
            seen = set()
            result = []
            for item in moves:
                if not isinstance(item, (tuple, list)) or len(item) != 2:
                    raise ValueError(
                        "each exploded move must be "
                        "(model_instance, (dx, dy, dz))"
                    )
                instance, translation = item
                if not isinstance(instance, ModelInstance):
                    raise TypeError(
                        "exploded move target must be a model object"
                    )
                if instance.occurrence_id not in owned:
                    raise ValueError(
                        "exploded move target must belong to this assembly"
                    )
                if instance.occurrence_id in seen:
                    raise ValueError(
                        "one occurrence cannot have two moves in one "
                        "exploded view"
                    )
                if (
                    not isinstance(translation, (tuple, list))
                    or len(translation) != 3
                ):
                    raise ValueError(
                        "exploded move translation must be an XYZ triple"
                    )
                values = []
                for value in translation:
                    if (
                        isinstance(value, bool)
                        or not isinstance(value, (int, float))
                        or not isfinite(value)
                    ):
                        raise ValueError(
                            "exploded move translation must contain fixed "
                            "finite numbers"
                        )
                    values.append(float(value))
                if not any(values):
                    raise ValueError(
                        "exploded move translation must be non-zero"
                    )
                seen.add(instance.occurrence_id)
                result.append((instance.occurrence_id, tuple(values)))
            normalized_moves = tuple(result)

        return replace(
            self,
            exploded_views=self.exploded_views + (
                ExplodedView(
                    name=name,
                    scale=normalized_scale,
                    moves=normalized_moves,
                ),
            ),
        )

    def show_exploded(self, name):
        """Show one named exploded view after the assembly is built."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("exploded view name must be non-empty text")
        name = name.strip()
        if not any(view.name == name for view in self.exploded_views):
            raise KeyError(
                f"assembly has no exploded view named {name!r}"
            )
        return replace(
            self,
            exploded_display=name,
            exploded_display_set=True,
        )

    def show_assembled(self):
        """Explicitly show the normal assembled placement."""
        return replace(
            self,
            exploded_display=None,
            exploded_display_set=True,
        )

    def with_anchor(self, name, target, reference, *, offset=(0, 0)):
        """Expose one named attachment datum owned by this assembly.

        Parameters:
            name: Public name for the assembly-owned attachment datum.
            target: Component occurrence in this Assembly that owns the real attachment reference.
            reference: Anchor, named component anchor, AnchorFrame or AnchorTopology on target.
            offset: Optional in-plane (u, v) correction passed through when attaching, in mm.

        Use when:
            A mounting/reference name belongs to the meaning of the larger
            assembly rather than to the generic reusable component itself.

        Limits:
            target must already belong to this Assembly. with_anchor() exposes a
            reference; it does not create an attachment by itself.

        Example:
            frame = (left + right).with_anchor("front_mount", left, Anchor.FRONT_TOP_LEFT)
        """
        if not isinstance(name, str) or not name.strip():
            raise ValueError("assembly anchor name must be non-empty text")
        if any(existing == name for existing, _ in self.anchors):
            raise ValueError(f"assembly anchor {name!r} already exists")
        if not isinstance(target, ModelInstance):
            raise TypeError("assembly anchor target must be a model object")
        if not any(instance is target for instance in self.instances):
            raise ValueError("assembly anchor target must belong to this assembly")
        if not isinstance(offset, (tuple, list)) or len(offset) != 2:
            raise ValueError("assembly anchor offset must be an (u, v) pair")
        if not all(isfinite(pv(value)) for value in offset):
            raise ValueError("assembly anchor offset must be finite")
        resolved = _resolve_anchor_reference(target, reference)
        return replace(
            self,
            anchors=self.anchors + (
                (
                    name,
                    AssemblyAnchor(
                        target=target,
                        reference=resolved,
                        offset=tuple(offset),
                    ),
                ),
            ),
        )

    def anchor(self, name):
        """Return one named assembly-owned attachment datum.

        Parameters:
            name: Name previously registered with with_anchor().

        Use when:
            A consumer needs the target/reference pair previously exposed with
            with_anchor() in order to create an attachment.

        Limits:
            The name must resolve to exactly one assembly-owned anchor.

        Example:
            mount = frame.anchor("front_mount")
        """
        matches = [anchor for anchor_name, anchor in self.anchors
                   if anchor_name == name]
        if len(matches) != 1:
            raise KeyError(f"assembly has no unique anchor named {name!r}")
        return matches[0]

    def resolve(self, name):
        """Return one explicitly named occurrence."""
        matches = [instance for instance in self.instances if instance.name == name]
        if len(matches) != 1:
            raise KeyError(f"assembly has no unique object named {name!r}")
        return matches[0]

    def __getattr__(self, name):
        matches = [instance for instance in self.instances if instance.name == name]
        if len(matches) == 1:
            return matches[0]
        raise AttributeError(name)

    def __post_init__(self):
        if not self.instances:
            raise ValueError("assembly must contain at least one model instance")
        if not all(isinstance(item, ModelInstance) for item in self.instances):
            raise TypeError("assembly items must be model instances")

        occurrence_ids = [instance.occurrence_id for instance in self.instances]
        if len(set(occurrence_ids)) != len(occurrence_ids):
            raise ValueError(
                "the same Forge occurrence cannot appear twice in one assembly; "
                "use .copy() for another physical occurrence"
            )

        names = [instance.name for instance in self.instances if instance.name is not None]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise ValueError(
                "assembly object names must be unique: " + ", ".join(duplicates)
            )

        anchor_names = [name for name, _ in self.anchors]
        duplicate_anchors = sorted({
            name for name in anchor_names if anchor_names.count(name) > 1
        })
        if duplicate_anchors:
            raise ValueError(
                "assembly anchor names must be unique: "
                + ", ".join(duplicate_anchors)
            )
        for name, anchor in self.anchors:
            if not isinstance(anchor, AssemblyAnchor):
                raise TypeError(f"assembly anchor {name!r} is invalid")
            if not any(instance is anchor.target for instance in self.instances):
                raise ValueError(
                    f"assembly anchor {name!r} target is not in this assembly"
                )

        view_names = [view.name for view in self.exploded_views]
        duplicate_views = sorted({
            name for name in view_names if view_names.count(name) > 1
        })
        if duplicate_views:
            raise ValueError(
                "exploded view names must be unique: "
                + ", ".join(duplicate_views)
            )
        owned_occurrences = {
            instance.occurrence_id for instance in self.instances
        }
        for view in self.exploded_views:
            if not isinstance(view, ExplodedView):
                raise TypeError("assembly exploded view is invalid")
            for occurrence_id, _translation in view.moves:
                if occurrence_id not in owned_occurrences:
                    raise ValueError(
                        f"exploded view {view.name!r} references an "
                        "occurrence outside this assembly"
                    )
        if self.exploded_display_set and self.exploded_display is not None:
            if self.exploded_display not in view_names:
                raise ValueError(
                    f"shown exploded view {self.exploded_display!r} "
                    "is not defined"
                )

        drawing_names = [drawing.name for drawing in self.drawings]
        duplicate_drawings = sorted({
            name for name in drawing_names if drawing_names.count(name) > 1
        })
        if duplicate_drawings:
            raise ValueError(
                "drawing names must be unique: " + ", ".join(duplicate_drawings)
            )
        for drawing in self.drawings:
            if not isinstance(drawing, ComponentDrawing):
                raise TypeError("assembly drawing is invalid")
            if drawing.target_occurrence_id not in owned_occurrences:
                raise ValueError(
                    f"drawing {drawing.name!r} target is not in this assembly"
                )

    def __add__(self, other):
        if self.exploded_views or self.exploded_display_set or self.drawings:
            raise ValueError(
                "compose the final assembly before defining presentation state"
            )
        if isinstance(other, ModelInstance):
            return Assembly(self.instances + (other,), self.anchors)
        if isinstance(other, Assembly):
            if (
                other.exploded_views
                or other.exploded_display_set
                or other.drawings
            ):
                raise ValueError(
                    "compose the final assembly before defining presentation state"
                )
            return Assembly(
                self.instances + other.instances,
                self.anchors + other.anchors,
            )
        return NotImplemented

    __or__ = __add__
