"""Mitcad lowering for sketches, reference geometry and sketch relations."""
from __future__ import annotations

from math import isfinite

from ...compiler import ModelError, _require_positive
from ...core import (
    Expression,
    Parameter,
    Shape,
    _DirectionSelector,
    _dim_add,
    _box_corner_from_anchor,
    _cone_base_from_anchor,
    _native_dependencies,
    _native_expression,
    _plain_command_value,
    _pv as pv,
    _sphere_center_from_anchor,
    command_value,
    number_text,
    parameters_in,
)
from ...ir import (
    AxisLineIR,
    BooleanIR,
    BoxIR,
    ChamferIR,
    CircleProfileIR,
    ConfigurationIR,
    ConeIR,
    CylinderIR,
    ExtrudeIR,
    FaceBoundaryIR,
    FeatureRefIR,
    FilletIR,
    LegacyShapeIR,
    ModelIR,
    PlacementIR,
    PlaneIR,
    ParallelEdgeSetIR,
    PolygonProfileIR,
    RegionIR,
    RevolveIR,
    SketchRelationsIR,
    SphereIR,
    SuppressionColumnIR,
    TranslationIR,
    _region_interior_point,
    normalize_shape,
    resolve_feature_ref,
)
from ...scalar_ir import (
    ScalarBinaryIR,
    ScalarLiteralIR,
    ScalarParameterRefIR,
    ScalarUnaryIR,
    is_affine_scalar_expression,
    scalar_parameter_names,
)


from .common import _role_command_value

FORMAT = "scpf-mitcad"
VERSION = 1

_FACE_NORMALS = {
    "top": [0, 0, 1],
    "bottom": [0, 0, -1],
    "left": [-1, 0, 0],
    "right": [1, 0, 0],
    "front": [0, -1, 0],
    "back": [0, 1, 0],
}

_PLANE_NORMAL_INDEX = {"XY": 2, "XZ": 1, "YZ": 0}


def _principal_plane_offset(plane: PlaneIR, *, label: str):
    """Return one bounded principal-plane offset without baking symbols."""
    if not isinstance(plane, PlaneIR):
        raise ModelError(f"{label} requires PlaneIR")
    normal = _PLANE_NORMAL_INDEX[plane.orientation]
    for index, value in enumerate(plane.origin):
        if index == normal:
            continue
        if parameters_in(value) or abs(pv(value)) > 1e-12:
            raise ModelError(
                f"{label} currently requires zero in-plane PlaneIR origin"
            )
    return plane.origin[normal]


def _mitcad_offset_plane(
    orientation: str,
    offset,
    *,
    label: str,
    binding: str = "plane",
):
    """Lower one principal offset plane; native identity stays transport only."""
    if orientation not in ("XY", "XZ", "YZ"):
        raise ModelError(f"Mitcad {label} requires a principal plane")
    if not parameters_in(offset) and abs(pv(offset)) <= 1e-12:
        return [], orientation.lower()

    return [
        {
            "cmd": "add_feature",
            "as": binding,
            "def": {
                "type": "construction_plane",
                "definition": {
                    "type": "offset",
                    "plane": orientation.lower(),
                    "distance": command_value(offset),
                },
            },
        }
    ], {"ref": f"{binding}.uid"}


def _mitcad_sketch_plane(plane: PlaneIR):
    """Lower PlaneIR through the shared principal-plane transport."""
    offset = _principal_plane_offset(
        plane,
        label="Mitcad Sketch IR",
    )
    return _mitcad_offset_plane(
        plane.orientation,
        offset,
        label="Sketch IR",
    )


def _same_semantic_value(left, right) -> bool:
    """Compare authored scalar intent without using current values as identity."""
    return str(command_value(left)) == str(command_value(right))


def _sketch_relations_transport(
    relations: SketchRelationsIR,
    model: ModelIR | None = None,
):
    """Lower explicit semantic Sketch relations to Mitcad-native solver data."""
    if not isinstance(relations, SketchRelationsIR):
        raise ModelError("Mitcad Sketch relations require SketchRelationsIR")

    coordinate_mode = bool(relations.coordinate_dimensions)
    entities = []
    point_ids = []

    if coordinate_mode:
        # A fixed origin entity is native solver transport. Semantic coordinate
        # dimensions reference the Sketch origin, not this Mitcad uid.
        entities.append(
            {
                "id": "p1",
                "type": "point",
                "at": [0.0, 0.0],
                "fixed": True,
            }
        )
        point_start = 2
    else:
        point_start = 1

    for index, point in enumerate(relations.points, start=point_start):
        point_id = f"p{index}"
        point_ids.append(point_id)
        at = [float(pv(value)) for value in point.position]
        if any(not isfinite(value) for value in at):
            raise ModelError("Mitcad Sketch relation points require finite seed values")
        entity = {
            "id": point_id,
            "type": "point",
            "at": at,
        }
        if not coordinate_mode and index == 1:
            # Solver anchoring for the #440 rectangle remains backend transport.
            if any(
                parameters_in(value) or abs(pv(value)) > 1e-12
                for value in point.position
            ):
                raise ModelError(
                    "Mitcad #440 Sketch relations require the first semantic point at origin"
                )
            entity["fixed"] = True
        entities.append(entity)

    first_curve = point_start + len(point_ids)
    curve_ids = []
    for offset, line in enumerate(relations.lines):
        curve_id = f"c{first_curve + offset}"
        curve_ids.append(curve_id)
        entities.append(
            {
                "id": curve_id,
                "type": "line",
                "start": point_ids[line.start],
                "end": point_ids[line.end],
            }
        )

    first_relation = first_curve + len(curve_ids)
    constraints = [
        {
            "id": f"k{first_relation + offset}",
            "type": constraint.orientation,
            "line": curve_ids[constraint.line],
        }
        for offset, constraint in enumerate(relations.constraints)
    ]
    first_dimension = first_relation + len(constraints)
    dimensions = [
        {
            "id": f"k{first_dimension + offset}",
            "type": "length",
            "line": curve_ids[dimension.line],
            "value": _role_command_value(model, dimension.value, "length"),
        }
        for offset, dimension in enumerate(relations.dimensions)
    ]

    coordinate_start = first_dimension + len(dimensions)
    for offset, dimension in enumerate(relations.coordinate_dimensions):
        dimensions.append(
            {
                "id": f"k{coordinate_start + offset}",
                "type": (
                    "horizontal_distance"
                    if dimension.axis == "x"
                    else "vertical_distance"
                ),
                "a": "p1",
                "b": point_ids[dimension.point],
                "signed": True,
                "value": _role_command_value(model, dimension.value, "length"),
            }
        )

    return entities, constraints, dimensions


def _next_sketch_entity_number(entities: list[dict]) -> int:
    numbers = []
    for entity in entities:
        uid = entity.get("id")
        if (
            isinstance(uid, str)
            and len(uid) > 1
            and uid[0] in {"p", "c", "t"}
            and uid[1:].isdigit()
        ):
            numbers.append(int(uid[1:]))
    return max(numbers, default=0) + 1


def _next_sketch_relation_number(
    constraints: list[dict],
    dimensions: list[dict],
) -> int:
    numbers = []
    for relation in (*constraints, *dimensions):
        uid = relation.get("id")
        if (
            isinstance(uid, str)
            and uid.startswith("k")
            and uid[1:].isdigit()
        ):
            numbers.append(int(uid[1:]))
    return max(numbers, default=0) + 1


def _shifted_xy_axis_transport(
    axis: AxisLineIR,
    plane: PlaneIR,
    entities: list[dict],
    constraints: list[dict],
    dimensions: list[dict],
) -> dict:
    """Append Mitcad-only construction geometry for one shifted XY axis."""
    if axis.direction not in {"X", "Y"}:
        raise ModelError(
            "Mitcad shifted AxisLineIR on XY requires X or Y direction"
        )
    if (
        plane.orientation != "XY"
        or not _same_semantic_value(axis.origin[2], plane.origin[2])
    ):
        raise ModelError(
            "Mitcad shifted AxisLineIR must lie in the semantic XY PlaneIR"
        )

    next_entity = _next_sketch_entity_number(entities)
    origin_id = f"p{next_entity}"
    first_id = f"p{next_entity + 1}"
    second_id = f"p{next_entity + 2}"
    curve_id = f"c{next_entity + 3}"

    entities.append(
        {
            "id": origin_id,
            "type": "point",
            "at": [0.0, 0.0],
            "fixed": True,
        }
    )

    if axis.direction == "Y":
        offset = axis.origin[0]
        offset_value = float(pv(offset))
        first = [offset_value, -1.0]
        second = [offset_value, 1.0]
        orientation = "vertical"
        offset_dimension = "horizontal_distance"
        along_dimension = "vertical_distance"
    else:
        offset = axis.origin[1]
        offset_value = float(pv(offset))
        first = [-1.0, offset_value]
        second = [1.0, offset_value]
        orientation = "horizontal"
        offset_dimension = "vertical_distance"
        along_dimension = "horizontal_distance"

    entities.extend(
        [
            {"id": first_id, "type": "point", "at": first},
            {"id": second_id, "type": "point", "at": second},
            {
                "id": curve_id,
                "type": "line",
                "start": first_id,
                "end": second_id,
                "construction": True,
            },
        ]
    )

    next_relation = _next_sketch_relation_number(
        constraints,
        dimensions,
    )
    constraints.append(
        {
            "id": f"k{next_relation}",
            "type": orientation,
            "line": curve_id,
        }
    )
    dimensions.extend(
        [
            {
                "id": f"k{next_relation + 1}",
                "type": offset_dimension,
                "a": origin_id,
                "b": first_id,
                "signed": True,
                "value": command_value(offset),
            },
            {
                "id": f"k{next_relation + 2}",
                "type": along_dimension,
                "a": origin_id,
                "b": first_id,
                "signed": True,
                "value": -1.0,
            },
            {
                "id": f"k{next_relation + 3}",
                "type": along_dimension,
                "a": origin_id,
                "b": second_id,
                "signed": True,
                "value": 1.0,
            },
        ]
    )

    return {
        "sketch": {"ref": "sk.uid"},
        "curve": curve_id,
    }


def _mitcad_revolve_axis(
    node: RevolveIR,
    entities: list[dict],
    constraints: list[dict],
    dimensions: list[dict],
):
    axis = node.axis
    if not isinstance(axis, AxisLineIR):
        raise ModelError("Mitcad RevolveIR requires AxisLineIR")

    if all(
        not parameters_in(value) and abs(pv(value)) <= 1e-12
        for value in axis.origin
    ):
        return axis.direction.lower()

    if node.sketch.plane.orientation != "XY":
        raise ModelError(
            "Mitcad shifted AxisLineIR transport currently requires an XY Sketch"
        )
    return _shifted_xy_axis_transport(
        axis,
        node.sketch.plane,
        entities,
        constraints,
        dimensions,
    )
