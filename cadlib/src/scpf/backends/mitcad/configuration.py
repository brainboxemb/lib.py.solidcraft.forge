"""Mitcad lowering for saved configuration semantics."""
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


def _private_suppression_parameter(model: ModelIR) -> str:
    """Choose one backend-private driver outside semantic model parameters."""
    taken = {parameter.name for parameter in model.parameters}
    stem = "__forge_suppress_root"
    if stem not in taken:
        return stem
    index = 2
    while f"{stem}_{index}" in taken:
        index += 1
    return f"{stem}_{index}"


def _mitcad_configuration_commands(
    model: ModelIR,
    configuration: ConfigurationIR,
    *,
    feature_binding: str,
) -> list[dict]:
    """Lower suppression-only semantic configuration to native Mitcad state."""
    if (
        len(configuration.columns) != 1
        or not isinstance(configuration.columns[0], SuppressionColumnIR)
    ):
        raise ModelError(
            "Mitcad ConfigurationIR currently requires one suppression column"
        )
    resolve_feature_ref(model.root, configuration.columns[0].feature)
    if any(len(row.cells) != 1 for row in configuration.rows):
        raise ModelError(
            "Mitcad ConfigurationIR currently requires one suppression cell per row"
        )

    driver = _private_suppression_parameter(model)
    return [
        {
            "cmd": "add_parameter",
            "name": driver,
            "unit": "",
            "expression": "0",
        },
        {
            "cmd": "set_configurations",
            "configurations": {
                "options": [],
                "closed": True,
                "parameters": [driver],
                "default": configuration.active,
                "rows": [
                    {
                        "name": row.name,
                        "values": {
                            driver: "1" if row.cells[0] else "0",
                        },
                    }
                    for row in configuration.rows
                ],
            },
        },
        {
            "cmd": "suppress_feature",
            "uid": {"ref": f"{feature_binding}.uid"},
            "expression": f"{driver} > 0",
        },
        {
            "cmd": "apply_configuration",
            "name": configuration.active,
        },
    ]


def _qualified_configuration_slice(configuration: ConfigurationIR) -> bool:
    """Return whether Mitcad supports this typed configuration subset."""
    return (
        isinstance(configuration, ConfigurationIR)
        and len(configuration.columns) == 1
        and isinstance(configuration.columns[0], SuppressionColumnIR)
    )
