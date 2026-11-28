"""Legacy topology query, edge-selection and modifier lowering."""

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


_CARDINAL_FACE_NORMAL = {
    Faces.TOP: [0, 0, 1],
    Faces.BOTTOM: [0, 0, -1],
    Faces.LEFT: [-1, 0, 0],
    Faces.RIGHT: [1, 0, 0],
    Faces.FRONT: [0, -1, 0],
    Faces.BACK: [0, 1, 0],
}

def _face_query_command(name, face, variable, *, select=None):
    """Bind one cardinal planar face from native SolidCraft topology."""
    selector = {
        "field": "faces",
        "where": {"plane_normal": _CARDINAL_FACE_NORMAL[face]},
        "max": "area",
    }
    if select is not None:
        selector["select"] = select
    query = _command("model.faces", body=name)
    query["bind"] = {variable: selector}
    return query


def _next_face_query_index(steps):
    return 1 + sum(command["command"] == "model.faces" for command in steps)


def _face_boundary_edge_commands(steps, selection, name):
    """Bind complete face boundaries as native {body,index} edge refs."""
    commands = []
    previous_edges = None
    start = _next_face_query_index(steps)
    for offset, face in enumerate(selection.faces):
        index = start + offset
        face_var = f"$topology_face_{index}"
        edges_var = f"$topology_edges_{index}"
        commands.append(_face_query_command(name, face, face_var))

        edge_query = _command("model.edges", body=name)
        binding = {
            "field": "edges",
            "boundary_of": face_var,
            "body": name,
        }
        if previous_edges is not None:
            binding["prepend"] = previous_edges
        edge_query["bind"] = {edges_var: binding}
        commands.append(edge_query)
        previous_edges = edges_var

    return commands, previous_edges


def _face_name_commands(steps, faces, name):
    """Bind native face names for shell from the shared Faces vocabulary."""
    commands = []
    variables = []
    start = _next_face_query_index(steps)
    for offset, face in enumerate(faces):
        variable = f"$topology_face_name_{start + offset}"
        commands.append(_face_query_command(name, face, variable, select="name"))
        variables.append(variable)
    return commands, variables


def _resolve_profile_edges(base, selection):
    """Translate named XZ profile segments/vertices to native edge picks.

    The sketch may be extruded symmetric, positive or negative along Y and
    may itself sit on a shifted Y plane. Pick points are only used to select
    the native edge when the feature is authored; the resulting SolidCraft
    fillet/chamfer remains attached to that edge after parameter edits.
    """
    if not isinstance(selection, _ProfileEdgeSelection):
        return selection
    if (
        base.get("profile") != "polygon"
        or base.get("sketch_plane") != "XZ"
        or base.get("extrusion_direction") not in (
            "symmetric", "positive", "negative"
        )
    ):
        raise ModelError(
            "named profile edges require an XZ polygon extrusion"
        )
    points = base["profile_points"]
    names = base["profile_ids"]
    if names is None:
        raise ModelError("Polygon2D must define ids= or named points to select profile edges")
    for pattern in selection.patterns:
        if not any(fnmatchcase(label, pattern) for label in names):
            raise ModelError(f"no polygon segment or vertex matches {pattern!r}")

    matches = [
        i for i, label in enumerate(names)
        if any(fnmatchcase(label, pattern) for pattern in selection.patterns)
    ]
    plane_y = pv(base.get("sketch_plane_offset", 0))
    thickness = pv(base["thickness"])
    direction = base["extrusion_direction"]
    if direction == "symmetric":
        start_y = plane_y - half(thickness)
        end_y = plane_y + half(thickness)
    elif direction == "positive":
        start_y = plane_y
        end_y = plane_y + thickness
    else:
        start_y = plane_y
        end_y = plane_y - thickness

    if selection.kind == "vertices":
        sweep_mid_y = midpoint(start_y, end_y)
        return [
            (pv(points[i][0]), sweep_mid_y, -pv(points[i][1]))
            for i in matches
        ]
    if selection.kind != "segments":
        raise ModelError(f"unsupported profile edge selection: {selection.kind}")

    picks = []
    for y in (start_y, end_y):
        for i in matches:
            a, b = points[i], points[(i + 1) % len(points)]
            picks.append((
                midpoint(pv(a[0]), pv(b[0])),
                y,
                -midpoint(pv(a[1]), pv(b[1])),
            ))
    return picks


def _resolve_direction_edges(base, selection):
    """Resolve BOSL2-style direction pairs to stable edge pick points."""
    if isinstance(selection, _DirectionSelector):
        selectors = (selection,)
    elif (
        isinstance(selection, (tuple, list))
        and selection
        and all(isinstance(item, _DirectionSelector) for item in selection)
    ):
        selectors = tuple(selection)
    else:
        return selection

    if base.get("profile") != "rectangle":
        raise ModelError("direction edge selectors require a rectangular solid")

    origin = base["origin"]
    dimensions = (
        base["width"],
        base["depth"],
        base["thickness"],
    )

    picks = []
    for selector in selectors:
        if sum(component != 0 for component in selector.vector) != 2:
            raise ModelError(
                "an edge selector must combine exactly two cardinal directions"
            )
        point = []
        for minimum, dimension, side in zip(
            origin,
            dimensions,
            selector.vector,
        ):
            if side < 0:
                point.append(minimum)
            elif side > 0:
                point.append(_dim_add(minimum, dimension))
            else:
                point.append(_dim_add(minimum, half(dimension)))
        picks.append(tuple(point))
    return picks


def _resolve_feature_edges(base, edges):
    """Resolve the public fillet/chamfer edge selectors to SolidCraft picks."""
    resolved = _resolve_profile_edges(base, edges)
    resolved = _resolve_direction_edges(base, resolved)
    if resolved is not Edges.VERTICAL:
        return resolved

    if base["profile"] != "rectangle":
        raise ModelError("vertical-edge selection requires a rectangular base")
    w, d, h = (pv(base[k]) for k in ("width", "depth", "thickness"))
    x, y, z = (pv(v) for v in base["origin"])
    return [
        [x + dx, y + dy, z + half(h)]
        for dx, dy in ((0, 0), (w, 0), (w, d), (0, d))
    ]


def _edge_params(edges):
    """Keep replay variables symbolic and validate legacy numeric picks."""
    if isinstance(edges, str):
        return edges
    picks = [[pv(v) for v in point] for point in edges]
    if not all(isfinite(v) for point in picks for v in point):
        raise ModelError("edge selection must be finite")
    return picks


def _fillet_command(base, radius, edges, name, *, vertical=False):
    r = _require_positive(radius, "fillet radius")
    if vertical:
        w, d = (pv(base[k]) for k in ("width", "depth"))
        if r * 2 >= min(w, d):
            raise ModelError("fillet radius exceeds rectangular base dimensions")
    return _command(
        "solid.fillet",
        edges=_edge_params(edges),
        radius=command_value(radius),
        body=name,
    )


def _chamfer_command(
    distance,
    edges,
    name,
    *,
    distance2=None,
    flip=False,
):
    _require_positive(distance, "chamfer distance")
    params = {
        "edges": _edge_params(edges),
        "distance": command_value(distance),
        "body": name,
    }
    if distance2 is not None:
        _require_positive(distance2, "chamfer distance2")
        params["distance2"] = command_value(distance2)
        if flip:
            params["flip"] = True
    return _command("solid.chamfer", **params)


def _shell_command(thickness, faces, name):
    _require_positive(thickness, "shell thickness")
    return _command(
        "solid.shell",
        faces=faces,
        thickness=command_value(thickness),
        body=name,
    )
