"""Legacy feature-tree routing detection."""

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


def _is_pure_csg_tree(shape):
    """Return whether a Shape can be compiled entirely by the primitive CSG path."""
    if not isinstance(shape, Shape):
        return False
    from ...csg import CSG_PRIMITIVE_KINDS
    if shape.kind in CSG_PRIMITIVE_KINDS or shape.kind == "placed_box":
        return True
    if shape.kind == "placed3d":
        return shape.data[0].kind in ("cylinder", "cone")
    if shape.kind == "translated":
        return _is_pure_csg_tree(shape.data[0])
    if shape.kind in ("union", "difference", "intersection"):
        return (
            _is_pure_csg_tree(shape.data[0])
            and _is_pure_csg_tree(shape.data[1])
        )
    return False


def _is_feature_tree(shape):
    """Return whether this Shape needs ordered feature lowering.

    Pure primitive CSG combinations stay on the CSG compiler regardless of
    which primitive happens to be on the left. A later native feature can wrap
    such a CSG body without changing how that base body was constructed.
    """
    if not isinstance(shape, Shape):
        return False
    if (
        shape.kind in ("union", "difference", "intersection")
        and _is_pure_csg_tree(shape)
    ):
        return False
    if shape.kind in (
        "exported_feature",
        "named_feature",
        "box",
        "placed_box",
        "tapered_box",
        "sketch_base_extrusion",
        "sketch_base_revolve",
        "sketch_open_chain",
        "sheet_base",
        "sheet_contour_flange",
        "sheet_edge_flange",
        "sheet_hem",
        "sheet_path_flange",
        "sheet_perforate",
        "sheet_fold",
    ):
        return True
    if shape.kind in (
        "fillet", "chamfer", "shell", "union", "difference", "intersection",
        "material_assignment", "appearance_assignment",
        "rectangular_pattern", "circular_pattern",
    ):
        return True
    return False
