"""Legacy named-feature and native history identity lowering."""

from math import isfinite
from fnmatch import fnmatchcase
from ...core import (
    Shape,
    Edges,
    Faces,
    Depth,
    Anchor,
    Parameter,
    _DirectionSelector,
    _ProfileEdgeSelection,
    _FaceBoundarySelection,
    _dim_add,
    _dim_abs,
    _dim_sub,
    _cylinder_base_from_anchor,
    half,
    midpoint,
    _pv as pv,
    command_value,
    number_text,
    parameters_in,
    _hole_spec,
)
from ..errors import ModelError, _require_positive
from ..legacy import _command, _collect, _param_commands
from ...placement import (
    _anchored_features,
    _base_rectangle,
    _base_rectangle_center,
    _combine,
    _shell_thickness,
)
from ...sketches import (
    compile_base,
    compile_connected_profile,
    compile_open_chain,
    compile_open_chain_with_curves,
    compile_standalone_sketch,
    _extrude_profile_params,
    _polygon_profile_command,
    _sketch_plane_frame,
)


_AUTO_HISTORY_FEATURE_NAMES = {
    "solid.box": "Box",
    "solid.sphere": "Sphere",
    "solid.cylinder": "Cylinder",
    "solid.cone": "Cone",
    "solid.revolve": "Revolve",
    "solid.hole": "Hole",
}


def _to_commands(*args, **kwargs):
    """Late bridge to the recursive dispatcher without an eager import cycle."""
    from .dispatch import _to_commands as implementation
    return implementation(*args, **kwargs)


def _applied_feature_prefix(root, source):
    """Return the model-history prefix ending at the exact applied source."""
    if not isinstance(root, Shape):
        return None
    if root is source:
        return root
    if root.kind in ("exported_feature", "named_feature"):
        return _applied_feature_prefix(root.data[0], source)

    if root.kind in ("rectangular_pattern", "circular_pattern"):
        return _applied_feature_prefix(root.data[0], source)

    if root.kind in (
        "fillet", "chamfer", "shell", "material_assignment", "solid_transform"
    ):
        return _applied_feature_prefix(root.data[0], source)

    if root.kind in ("union", "difference", "intersection"):
        original, added = root.data
        candidate = added.data[0] if added.kind == "labeled" else added
        if candidate is source:
            return root
        return _applied_feature_prefix(original, source)

    return None


def _native_feature_name(root, feature, model_name):
    """Resolve an applied Forge Shape to its SolidCraft history identity.

    Explicit Sketch extrusions already carry their authored feature name.
    Native primitives such as Hole/Cylinder/Cone use SolidCraft's deterministic
    type-local history names (Hole1, Cylinder2, ...), derived from the exact
    history prefix that applies the source feature.
    """
    prefix = _applied_feature_prefix(root, feature)
    if prefix is None:
        raise ModelError(
            "pattern source must be one already-applied native history feature"
        )

    commands, _ = _to_commands(prefix, model_name)
    if not commands:
        raise ModelError("pattern source produced no native history feature")

    last = commands[-1]
    params = last.get("params", {})
    explicit_name = params.get("name")
    if isinstance(explicit_name, str) and explicit_name:
        return explicit_name

    command = last.get("command")
    base_name = _AUTO_HISTORY_FEATURE_NAMES.get(command)
    if base_name is None:
        raise ModelError(
            "pattern source does not expose a stable native history-feature "
            f"identity: {feature.kind}"
        )
    ordinal = sum(row.get("command") == command for row in commands)
    if ordinal < 1:
        raise ModelError("pattern source native history ordinal is missing")
    return f"{base_name}{ordinal}"


def _named_feature_parent(shape):
    """Return the history state immediately before one scoped feature."""
    if not isinstance(shape, Shape):
        return None
    if shape.kind in (
        "translated",
        "placed3d",
        "anchored",
        "labeled",
        "material_assignment",
        "appearance_assignment",
        "exported_feature",
    ):
        return _named_feature_parent(shape.data[0])
    if shape.kind in (
        "union",
        "difference",
        "intersection",
        "fillet",
        "chamfer",
        "shell",
        "rectangular_pattern",
        "circular_pattern",
        "sheet_fold",
        "sheet_edge_flange",
        "sheet_hem",
        "sheet_path_flange",
        "sheet_perforate",
        "solid_transform",
    ):
        return shape.data[0]
    return None


def _named_feature_commands(steps, feature_name, suppressed, *, start=0):
    """Validate one native history result and apply its explicit initial state."""
    candidates = [
        index
        for index in range(start, len(steps))
        if steps[index]["command"].startswith(("solid.", "sheet."))
    ]
    if len(candidates) != 1:
        raise ModelError(
            f"feature {feature_name!r} must lower to exactly one native "
            "solid/sheet history feature"
        )
    if not suppressed:
        return steps

    target = candidates[0]
    variable = f"$feature_{feature_name}_name"
    if any(variable in command.get("bind", {}) for command in steps):
        raise ModelError(f"duplicate named feature {feature_name!r}")

    steps = [dict(command) for command in steps]
    binding = dict(steps[target].get("bind", {}))
    binding[variable] = "name"
    steps[target]["bind"] = binding
    steps.append(
        _command(
            "timeline.suppress",
            features=[variable],
            suppressed=True,
        )
    )
    return steps
