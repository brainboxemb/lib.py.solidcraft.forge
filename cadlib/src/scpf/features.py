"""Ordered CAD features -> native SolidCraft commands.

Works on Box and explicit Sketch extrusions. Every feature is compiled
from its operation, not from a named example such as Plate.
"""
from math import isfinite
from fnmatch import fnmatchcase
from .core import (
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
from .compiler import ModelError, _command, _collect, _param_commands, _require_positive
from .placement import (
    _anchored_features,
    _base_rectangle,
    _base_rectangle_center,
    _combine,
    _shell_thickness,
)
from .sketches import (
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
    from .csg import CSG_PRIMITIVE_KINDS
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


def _hole_commands(feature, position, name, refs=None):
    """Compile one explicitly positioned Hole-family feature."""
    if feature.kind != "hole":
        raise ModelError("native hole operation requires a Hole-family feature")
    spec = _hole_spec(feature)
    hole_type = spec["type"]
    diameter = spec["diameter"]
    depth = spec["depth"]
    direction = spec["direction"]
    counterbore_d = spec["counterbore_diameter"]
    counterbore_depth = spec["counterbore_depth"]
    countersink_d = spec["countersink_diameter"]
    countersink_angle = spec["countersink_angle"]
    thread = spec["thread"]
    hand = spec["hand"]
    thread_depth = spec["thread_depth"]
    modeled = spec["modeled"]
    ease_out = spec["ease_out"]

    point = tuple(position)
    concrete_point = [pv(v) for v in point]
    if not all(isfinite(v) for v in concrete_point):
        raise ModelError("hole position must be finite")

    direction_vector = (
        _vector(direction, "hole direction") if direction is not None else None
    )

    params = {
        "position": (
            [command_value(v) for v in point]
            if direction_vector is not None
            else [pv(v) for v in point]
        ),
        "targets": [name],
    }
    if diameter is not None:
        _require_positive(diameter, "hole diameter")
        params["diameter"] = command_value(diameter)
    if depth is not Depth.THROUGH_ALL:
        _require_positive(depth, "hole depth")
        params["depth"] = command_value(depth)
    if direction_vector is not None:
        params["direction"] = direction_vector
    if refs:
        params["references"] = refs

    if hole_type == "simple":
        pass
    elif hole_type == "counterbore":
        _require_positive(counterbore_d, "counterbore diameter")
        _require_positive(counterbore_depth, "counterbore depth")
        if pv(counterbore_d) <= pv(diameter):
            raise ModelError(
                "counterbore diameter must exceed hole diameter"
            )
        params.update(
            type="counterbore",
            cb_diameter=command_value(counterbore_d),
            cb_depth=command_value(counterbore_depth),
        )
    elif hole_type == "countersink":
        _require_positive(countersink_d, "countersink diameter")
        if pv(countersink_d) <= pv(diameter):
            raise ModelError(
                "countersink diameter must exceed hole diameter"
            )
        angle = pv(countersink_angle)
        if not isfinite(angle) or angle <= 0 or angle >= 180:
            raise ModelError(
                "countersink angle must be between 0 and 180 degrees"
            )
        params.update(
            type="countersink",
            cs_diameter=command_value(countersink_d),
            cs_angle=command_value(countersink_angle),
        )
    elif hole_type == "threaded":
        params["thread"] = thread
        if hand != "right":
            params["hand"] = hand
        if thread_depth is not None:
            _require_positive(thread_depth, "thread depth")
            params["thread_depth"] = command_value(thread_depth)
        if modeled:
            params["modeled"] = True
        if ease_out is not None:
            params["ease_out"] = (
                command_value(ease_out)
                if not isinstance(ease_out, str)
                else ease_out
            )
    else:
        raise ModelError(f"unsupported Hole-family type {hole_type}")

    return [_command("solid.hole", **params)]


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


def _vector(values, label):
    concrete = [pv(v) for v in values]
    if len(concrete) != 3 or not all(isfinite(v) for v in concrete):
        raise ModelError(f"{label} must be a finite 3D direction")
    if concrete == [0, 0, 0]:
        raise ModelError(f"{label} cannot be the zero vector")
    return concrete


def _plastic_feature_command(feature, position, name):
    """Compile one native SolidCraft plastic feature at an explicit face pick."""
    point = [pv(v) for v in position]
    if not all(isfinite(v) for v in point):
        raise ModelError("plastic feature position must be finite")

    if feature.kind == "lip":
        width, height = feature.data
        _require_positive(width, "lip width")
        _require_positive(height, "lip height")
        return _command(
            "plastic.lip",
            face=point,
            width=command_value(width),
            height=command_value(height),
            body=name,
        )

    if feature.kind == "snap_fit":
        length, thickness, width, catch_depth, catch_length, hook, direction = feature.data
        for value, label in (
            (length, "snap-fit length"),
            (thickness, "snap-fit thickness"),
            (width, "snap-fit width"),
            (catch_depth, "snap-fit catch depth"),
            (catch_length, "snap-fit catch length"),
        ):
            _require_positive(value, label)
        params = dict(
            position=point,
            hook=_vector(hook, "snap-fit hook"),
            length=command_value(length),
            thickness=command_value(thickness),
            width=command_value(width),
            catch_depth=command_value(catch_depth),
            catch_length=command_value(catch_length),
            body=name,
        )
        if direction is not None:
            params["direction"] = _vector(direction, "snap-fit direction")
        return _command("plastic.snap_fit", **params)

    if feature.kind == "boss":
        diameter, height, hole_diameter, direction = feature.data
        _require_positive(diameter, "boss diameter")
        _require_positive(height, "boss height")
        params = dict(
            position=point,
            diameter=command_value(diameter),
            height=command_value(height),
            body=name,
        )
        if hole_diameter is not None:
            _require_positive(hole_diameter, "boss hole diameter")
            params["hole_diameter"] = command_value(hole_diameter)
        if direction is not None:
            params["direction"] = _vector(direction, "boss direction")
        return _command("plastic.boss", **params)

    if feature.kind == "rest":
        width, height, length, along, direction = feature.data
        _require_positive(width, "rest width")
        _require_positive(height, "rest height")
        params = dict(
            position=point,
            width=command_value(width),
            height=command_value(height),
            body=name,
        )
        if length is not None:
            _require_positive(length, "rest length")
            params["length"] = command_value(length)
        if along is not None:
            params["along"] = _vector(along, "rest along")
        if direction is not None:
            params["direction"] = _vector(direction, "rest direction")
        return _command("plastic.rest", **params)

    raise ModelError(f"unsupported plastic feature {feature.kind}")


def _attached_hole_commands(child, target, parent_anchor, resolved, name):
    """Compile Hole intent as one editable sketch plus one cut feature."""
    feature = child
    if feature.kind != "hole":
        raise ModelError("expected Hole feature")
    if parent_anchor is not Anchor.TOP:
        raise ModelError("Hole.attach() currently starts drilling from Anchor.TOP")

    spec = _hole_spec(feature)
    hole_type = spec["type"]
    diameter = spec["diameter"]
    depth = spec["depth"]
    hole_direction = spec["direction"]
    _require_positive(diameter, "hole diameter")
    if hole_type != "simple" or hole_direction is not None:
        raise ModelError(
            "non-simple or directional Hole-family features currently require explicit .at() placement"
        )
    (_, _), (_, _, origin_z), thickness = _base_rectangle(target)
    base_top = thickness if pv(origin_z) == 0 else _combine(origin_z, thickness)
    entry_z = base_top
    on_base_top = True

    # If the current body ends in a centered Cylinder attached to its top,
    # the next Hole starts on that boss top. Keep the symbolic height so the
    # generated Bore sketch remains parametrically tied to the base thickness.
    if target.kind == "union":
        previous, attached = target.data
        if attached.kind == "anchored":
            boss, boss_parent, boss_parent_anchor, boss_child_anchor, boss_offset = attached.data
            if (boss.kind == "cylinder" and boss_parent == previous
                    and boss_parent_anchor is Anchor.TOP
                    and boss_child_anchor is Anchor.BOTTOM
                    and all(pv(v) == 0 for v in boss_offset)):
                boss_height, _, boss_axis, _boss_origin = boss.data
                if boss_axis != "Z":
                    raise ModelError("attached boss Cylinder must use Axis.Z")
                entry_z = (base_top + boss_height
                           if isinstance(boss_height, (int, float))
                           else _combine(base_top, boss_height))
                on_base_top = False

    if depth is Depth.THROUGH_ALL:
        if on_base_top:
            # Preserve the editable Sample Plate convention: XY/base-plane
            # sketch and positive cut through the plate thickness.
            sketch_z = origin_z
            distance = thickness
            direction = "positive"
        else:
            # A bore starting on a joined boss is sketched at its entry face
            # and cuts back through the complete current height.
            sketch_z = entry_z
            distance = (entry_z if pv(origin_z) == 0
                        else _combine(entry_z, -pv(origin_z)))
            direction = "negative"
    else:
        _require_positive(depth, "hole depth")
        sketch_z = entry_z
        distance = depth
        direction = "negative"

    label = "Bore" if not on_base_top else "Hole"
    plane = {"plane": "XY", "name": label}
    if pv(sketch_z):
        plane["offset"] = command_value(sketch_z)

    operations = [_command("sketch.create", **plane)]
    for primitive, position, _refs in resolved:
        hole_diameter = _hole_spec(primitive)["diameter"]
        operations.append(_command(
            "sketch.circle.center",
            center=position[:2],
            diameter=command_value(hole_diameter),
        ))
    operations.extend([
        _command("sketch.finish"),
        _command("solid.extrude",
                 distance=command_value(distance),
                 direction=direction,
                 operation="cut",
                 targets=[name],
                 name=label),
    ])
    return operations


def _attached_commands(shape, original, feature, name, *, feature_name=None):
    child, target, parent_anchor, child_anchor, offset = feature.data
    if target != original:
        raise ModelError("attached feature must target the body being modified")
    try:
        resolved = _anchored_features(feature)
    except (ValueError, TypeError) as exc:
        raise ModelError(str(exc)) from exc

    attached_primitive = child
    if attached_primitive.kind == "hole":
        return _attached_hole_commands(
            child, target, parent_anchor, resolved, name)
    if attached_primitive.kind in ("lip", "snap_fit", "boss", "rest"):
        if shape.kind != "union":
            raise ModelError("plastic features are added with +")
        return [
            _plastic_feature_command(primitive, position, name)
            for primitive, position, _refs in resolved
        ]

    operations = []
    for primitive, position, refs in resolved:
        height, diameter, axis, _constructor_anchor = primitive.data
        _require_positive(height, "cylinder height")
        _require_positive(diameter, "cylinder diameter")
        if axis != "Z":
            raise ModelError("attached Cylinder must use Axis.Z")
        params = dict(
            height=command_value(height),
            diameter=command_value(diameter),
            base=position,
            axis=axis,
            operation="join" if shape.kind == "union" else "cut",
            targets=[name],
        )
        if refs:
            params["references"] = refs
        if feature_name is not None:
            params["name"] = feature_name
        operations.append(_command("solid.cylinder", **params))
    return operations


def _explicit_sketch_commands(
    shape,
    original,
    feature,
    name,
    *,
    face_query_index=None,
    sketch_index=1,
):
    """Compile an explicitly authored named sketch and its extrusion."""
    (
        sketch_name,
        target,
        parent_anchor,
        plane_info,
        profiles,
        distance,
        direction,
        sketch_operations,
        profile_picks,
        exact_regions,
    ) = feature.data
    plane_name, sketch_origin, sketch_rotation = plane_info
    if target != original:
        raise ModelError("explicit Sketch must target the body being modified")
    if shape.kind not in ("union", "difference"):
        raise ModelError("explicit Sketch extrusion must be added or subtracted")

    if plane_name is not None:
        if sketch_origin is not None or sketch_rotation is not None:
            plane = dict(
                plane=_sketch_plane_frame(
                    plane_name,
                    origin=sketch_origin,
                    rotation=sketch_rotation,
                ),
                name=sketch_name,
            )
        else:
            plane = dict(plane=plane_name, name=sketch_name)
        relative_origin = (0, 0)
        commands = [_command("sketch.create", **plane)]
    else:
        if parent_anchor is Anchor.TOP:
            if face_query_index is None:
                raise ModelError("attached TOP Sketch needs a face query index")
            point_var = f"$face_point_{face_query_index}"
            index_var = f"$face_index_{face_query_index}"
            selector = {
                "field": "faces",
                "where": {"plane_normal": [0, 0, 1]},
                "max": "area",
            }
            face_query = _command("model.faces", body=name)
            face_query["bind"] = {
                point_var: {**selector, "select": "point"},
                index_var: {**selector, "select": "index"},
            }
            plane = dict(
                plane={
                    "face": point_var,
                    "body": name,
                    "index": index_var,
                },
                project_edges=False,
                name=sketch_name,
            )
            relative_origin = (0, 0)
            commands = [face_query, _command("sketch.create", **plane)]
        else:
            try:
                (width, depth), (x, y, z), thickness = _base_rectangle(target)
            except ValueError as exc:
                raise ModelError(
                    "BOTTOM/CENTER attached Sketch currently requires "
                    "a rectangular solid"
                ) from exc
            if thickness is None:
                raise ModelError(
                    "BOTTOM/CENTER attached Sketch currently requires "
                    "a rectangular solid"
                )
            if parent_anchor is Anchor.BOTTOM:
                plane_z = z
            elif parent_anchor is Anchor.INNER_BOTTOM:
                wall = _shell_thickness(target)
                if wall is None:
                    raise ModelError("Anchor.INNER_BOTTOM requires a shelled body")
                plane_z = _combine(z, wall)
            elif parent_anchor is Anchor.CENTER:
                plane_z = _combine(z, half(thickness))
            else:
                raise ModelError("unsupported explicit Sketch anchor")

            plane = dict(plane="XY", name=sketch_name)
            if pv(plane_z):
                plane["offset"] = command_value(plane_z)
            center_x, center_y, _ = _base_rectangle_center(target)
            relative_origin = (center_x, center_y)
            commands = [_command("sketch.create", **plane)]

    referenced_sources = {
        id(operation.data[0])
        for operation in sketch_operations
        if operation.kind in ("sketch_pattern_rectangular", "sketch_mirror")
    }
    profile_variables = {
        id(profile): f"$sketch_{sketch_index}_profile_{index}"
        for index, (profile, _anchor, _offset) in enumerate(profiles, start=1)
        if id(profile) in referenced_sources
    }
    operation_variables = {
        id(operation): f"$sketch_{sketch_index}_operation_{index}"
        for index, operation in enumerate(sketch_operations, start=1)
    }

    def append_profile(command, profile):
        variable = profile_variables.get(id(profile))
        if variable is not None:
            command.setdefault("bind", {})[variable] = "curves"
        commands.append(command)

    def source_variable(source):
        variable = profile_variables.get(id(source))
        if variable is None:
            variable = operation_variables.get(id(source))
        if variable is None:
            raise ModelError(
                "sketch pattern/mirror source is not available in this Sketch"
            )
        return variable

    for profile_index, (profile, profile_anchor, offset) in enumerate(
        profiles, start=1
    ):
        ox = _combine(relative_origin[0], offset[0])
        oy = _combine(relative_origin[1], offset[1])

        if profile.kind == "circle":
            if profile_anchor not in (None, Anchor.CENTER):
                raise ModelError("Circle2D sketch anchor must be CENTER")
            diameter = profile.data[0]
            _require_positive(diameter, "sketch circle diameter")
            append_profile(
                _command(
                    "sketch.circle.center",
                    center=[command_value(ox), command_value(oy)],
                    diameter=command_value(diameter),
                ),
                profile,
            )
            continue

        if profile.kind in ("rectangle", "rounded_rectangle"):
            rectangle_width, rectangle_height = profile.data[:2]
            _require_positive(rectangle_width, "sketch rectangle width")
            _require_positive(rectangle_height, "sketch rectangle height")
            if profile_anchor is Anchor.CENTER:
                x0 = _combine(ox, -half(rectangle_width))
                y0 = _combine(oy, -half(rectangle_height))
                x1 = _combine(ox, half(rectangle_width))
                y1 = _combine(oy, half(rectangle_height))
            else:
                x0, y0 = ox, oy
                x1 = _combine(ox, rectangle_width)
                y1 = _combine(oy, rectangle_height)
            params = dict(
                p0=[command_value(x0), command_value(y0)],
                p1=[command_value(x1), command_value(y1)],
            )
            if profile.kind == "rounded_rectangle":
                radius = profile.data[2]
                _require_positive(radius, "sketch rounded rectangle radius")
                if pv(radius) * 2 >= min(
                        pv(rectangle_width), pv(rectangle_height)):
                    raise ModelError("rounded rectangle radius exceeds half the shorter side")
                params["radius"] = command_value(radius)
                command = "sketch.rectangle.rounded"
            else:
                command = "sketch.rectangle.two_point"
            append_profile(_command(command, **params), profile)
            continue

        if profile.kind == "polygon":
            if profile_anchor is not None:
                raise ModelError(
                    "Polygon2D uses authored sketch coordinates; "
                    "semantic CENTER is not supported yet"
                )
            append_profile(
                _polygon_profile_command(
                    profile,
                    plane=plane_name or "XY",
                    offset=(ox, oy),
                ),
                profile,
            )
            continue

        if profile.kind == "text":
            if profile_anchor is not None:
                raise ModelError(
                    "Text2D uses its native insertion point; "
                    "semantic CENTER is not supported yet"
                )
            text, height, font = profile.data
            _require_positive(height, "sketch text height")
            append_profile(
                _command(
                    "sketch.text", text=text,
                    at=[command_value(ox), command_value(oy)],
                    height=command_value(height), font=font,
                ),
                profile,
            )
            continue

        if profile.kind == "connected_profile":
            if profile_anchor is not None:
                raise ModelError(
                    "connected profiles use authored sketch coordinates"
                )
            if id(profile) in referenced_sources:
                raise ModelError(
                    "sketch pattern/mirror does not yet support connected profiles"
                )
            connected, _meta = compile_connected_profile(
                profile,
                offset=(ox, oy),
            )
            commands.extend(connected)
            continue

        if profile.kind in (
            "slot_center_to_center",
            "slot_overall",
            "slot_center_point",
            "slot_arc_three_point",
            "slot_arc_center",
        ):
            if profile_anchor is not None:
                raise ModelError(
                    "native Slot profiles use authored sketch coordinates"
                )

            def slot_intent(point):
                return (
                    _combine(ox, point[0]),
                    _combine(oy, point[1]),
                )

            def direct_slot_point(point):
                values = [
                    command_value(value)
                    for value in slot_intent(point)
                ]
                if any(isinstance(value, str) for value in values):
                    raise ModelError(
                        "native Slot point coordinates currently require "
                        "fixed values"
                    )
                return values

            def seed_point(intent):
                return [pv(intent[0]), pv(intent[1])]

            def same_intent(left, right):
                return command_value(left) == command_value(right)

            def emit_parametric_straight_slot(
                command_name,
                point_key_a,
                point_a,
                point_key_b,
                point_b,
                width,
                *,
                center_point=False,
            ):
                intent_a = slot_intent(point_a)
                intent_b = slot_intent(point_b)
                dx = pv(intent_b[0]) - pv(intent_a[0])
                dy = pv(intent_b[1]) - pv(intent_a[1])
                tolerance = 1e-9

                if abs(dy) <= tolerance and abs(dx) > tolerance:
                    axis = 0
                    mode = "horizontal"
                    if not same_intent(intent_a[1], intent_b[1]):
                        raise ModelError(
                            "parametric horizontal Slot endpoints must share "
                            "the same y-coordinate intent"
                        )
                elif abs(dx) <= tolerance and abs(dy) > tolerance:
                    axis = 1
                    mode = "vertical"
                    if not same_intent(intent_a[0], intent_b[0]):
                        raise ModelError(
                            "parametric vertical Slot endpoints must share "
                            "the same x-coordinate intent"
                        )
                else:
                    raise ModelError(
                        "parametric straight Slot endpoints currently require "
                        "a horizontal or vertical axis"
                    )

                delta = _dim_abs(
                    _dim_sub(intent_b[axis], intent_a[axis])
                )
                if center_point:
                    # SolidCraft 0.45 defines center-point Slot length as
                    # the complete straight centre-line length, while authored
                    # end is one half-length away from center.
                    delta = delta * 2

                middle = (
                    intent_a
                    if center_point
                    else (
                        midpoint(intent_a[0], intent_b[0]),
                        midpoint(intent_a[1], intent_b[1]),
                    )
                )

                params = {
                    point_key_a: seed_point(intent_a),
                    point_key_b: seed_point(intent_b),
                    "width": command_value(width),
                }
                centre_line = (
                    f"$sketch_{sketch_index}_slot_"
                    f"{profile_index}_centre_line"
                )
                middle_point = (
                    f"$sketch_{sketch_index}_slot_"
                    f"{profile_index}_middle"
                )

                dimensioned = _command(
                    "sketch.draw.dimensioned",
                    command=command_name,
                    params=params,
                    dimensions={"length": command_value(delta)},
                )
                dimensioned["bind"] = {
                    centre_line: "centre_line",
                    middle_point: "middle",
                }
                append_profile(dimensioned, profile)

                commands.append(_command(
                    "sketch.constraint.horizontal_vertical",
                    line=centre_line,
                    mode=mode,
                ))
                commands.append(_command(
                    "sketch.dimension",
                    entities=["origin", middle_point],
                    type="horizontal",
                    value=command_value(_dim_abs(middle[0])),
                ))
                commands.append(_command(
                    "sketch.dimension",
                    entities=["origin", middle_point],
                    type="vertical",
                    value=command_value(_dim_abs(middle[1])),
                ))

            if profile.kind == "slot_center_to_center":
                p0, p1, width = profile.data
                intents = (slot_intent(p0), slot_intent(p1))
                if parameters_in(*(intents[0] + intents[1])):
                    emit_parametric_straight_slot(
                        "sketch.slot.center_to_center",
                        "p0",
                        p0,
                        "p1",
                        p1,
                        width,
                    )
                    continue
                params = dict(
                    p0=direct_slot_point(p0),
                    p1=direct_slot_point(p1),
                    width=command_value(width),
                )
                command = "sketch.slot.center_to_center"
            elif profile.kind == "slot_overall":
                p0, p1, width = profile.data
                intents = (slot_intent(p0), slot_intent(p1))
                if parameters_in(*(intents[0] + intents[1])):
                    emit_parametric_straight_slot(
                        "sketch.slot.overall",
                        "p0",
                        p0,
                        "p1",
                        p1,
                        width,
                    )
                    continue
                params = dict(
                    p0=direct_slot_point(p0),
                    p1=direct_slot_point(p1),
                    width=command_value(width),
                )
                command = "sketch.slot.overall"
            elif profile.kind == "slot_center_point":
                center, end, width = profile.data
                intents = (slot_intent(center), slot_intent(end))
                if parameters_in(*(intents[0] + intents[1])):
                    emit_parametric_straight_slot(
                        "sketch.slot.center_point",
                        "center",
                        center,
                        "end",
                        end,
                        width,
                        center_point=True,
                    )
                    continue
                params = dict(
                    center=direct_slot_point(center),
                    end=direct_slot_point(end),
                    width=command_value(width),
                )
                command = "sketch.slot.center_point"
            elif profile.kind == "slot_arc_three_point":
                start, through, end, width = profile.data
                params = dict(
                    start=direct_slot_point(start),
                    through=direct_slot_point(through),
                    end=direct_slot_point(end),
                    width=command_value(width),
                )
                command = "sketch.slot.arc_three_point"
            else:
                center, start, end, sweep, width = profile.data
                params = dict(
                    center=direct_slot_point(center),
                    start=direct_slot_point(start),
                    width=command_value(width),
                )
                if end is not None:
                    params["end"] = direct_slot_point(end)
                else:
                    params["sweep"] = sweep
                command = "sketch.slot.arc_center"

            append_profile(_command(command, **params), profile)
            continue

        raise ModelError(
            "explicit Sketch supports Circle2D, Rectangle2D, RoundedRectangle2D, "
            "Polygon2D, connected profiles, Text2D or native Slot*2D profiles"
        )

    for operation in sketch_operations:
        variable = operation_variables[id(operation)]
        if operation.kind == "sketch_pattern_rectangular":
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
                reversed1,
                reversed2,
            ) = operation.data
            params = {
                "entities": source_variable(source),
                "count": command_value(count),
                "spacing": command_value(spacing),
                "dir": list(dir1),
            }
            has_second_direction = (
                pv(count2) != 1
                or bool(parameters_in(count2))
            )
            if has_second_direction:
                params["count2"] = command_value(count2)
                if spacing2 is not None:
                    params["spacing2"] = command_value(spacing2)
                if dir2 is not None:
                    params["dir2"] = list(dir2)
            if alignment != "right":
                params["alignment"] = alignment
            if has_second_direction and alignment2 != "right":
                params["alignment2"] = alignment2
            if reversed1:
                params["reversed"] = True
            if has_second_direction and reversed2:
                params["reversed2"] = True
            command = _command("sketch.pattern.rectangular", **params)
        elif operation.kind == "sketch_mirror":
            source, line = operation.data
            command = _command(
                "sketch.mirror",
                entities=source_variable(source),
                line=line,
            )
        else:
            raise ModelError(
                f"unsupported explicit Sketch operation {operation.kind}"
            )
        if operation.kind == "sketch_pattern_rectangular":
            command["bind"] = {
                variable: {
                    "field": "curves",
                    "prepend": source_variable(source),
                }
            }
        else:
            command["bind"] = {variable: "curves"}
        commands.append(command)

    commands.append(_command("sketch.finish"))

    extrude = dict(
        operation="join" if shape.kind == "union" else "cut",
        targets=[name],
        name=sketch_name,
    )
    if distance is Depth.THROUGH_ALL:
        if shape.kind != "difference":
            raise ModelError("Depth.THROUGH_ALL is only supported for Sketch cuts")
        extrude["through_all"] = True
        extrude["direction"] = direction
    else:
        extrude["distance"] = command_value(distance)
        extrude["direction"] = direction

    extrude.update(
        _extrude_profile_params(profile_picks, exact_regions)
    )
    commands.append(_command("solid.extrude", **extrude))
    return commands


def _pattern_count_parameter_names(node, found=None):
    """Collect direct Parameters used as native dimensionless pattern counts."""
    if found is None:
        found = set()
    if isinstance(node, Shape):
        if node.kind == "rectangular_pattern":
            (
                original, _sources,
                _dir1, count1, _spacing1,
                _dir2, count2, _spacing2,
                _alignment, _alignment2,
                _reversed1, _reversed2,
            ) = node.data
            found.update(param.name for param in parameters_in(count1, count2))
            _pattern_count_parameter_names(original, found)
            return found
        if node.kind == "circular_pattern":
            (
                original, _sources, _axis, count, _angle,
                _alignment, _reversed,
            ) = node.data
            found.update(param.name for param in parameters_in(count))
            _pattern_count_parameter_names(original, found)
            return found
        if node.kind == "sketch_pattern_rectangular":
            (
                source, count1, _spacing1, _dir1,
                count2, _spacing2, _dir2,
                _alignment, _alignment2,
                _reversed1, _reversed2,
            ) = node.data
            found.update(param.name for param in parameters_in(count1, count2))
            _pattern_count_parameter_names(source, found)
            return found
        _pattern_count_parameter_names(node.data, found)
    elif isinstance(node, (tuple, list)):
        for item in node:
            _pattern_count_parameter_names(item, found)
    return found


def _non_count_parameter_names(node, found=None):
    """Collect parameter uses outside rectangular-pattern count fields."""
    if found is None:
        found = set()
    if isinstance(node, Shape):
        if node.kind == "hole":
            spec = _hole_spec(node)
            for field in (
                "diameter",
                "depth",
                "direction",
                "counterbore_diameter",
                "counterbore_depth",
                "countersink_diameter",
                "thread_depth",
                "ease_out",
            ):
                candidate = spec[field]
                if candidate is Depth.THROUGH_ALL or isinstance(candidate, str):
                    continue
                _non_count_parameter_names(candidate, found)
            return found
        if node.kind == "rectangular_pattern":
            (
                original, _sources,
                dir1, _count1, spacing1,
                dir2, _count2, spacing2,
                alignment, alignment2,
                reversed1, reversed2,
            ) = node.data
            _non_count_parameter_names(original, found)
            _non_count_parameter_names(
                (dir1, spacing1, dir2, spacing2,
                 alignment, alignment2, reversed1, reversed2),
                found,
            )
            return found
        if node.kind == "circular_pattern":
            (
                original, _sources, axis, _count, _angle,
                alignment, reversed,
            ) = node.data
            _non_count_parameter_names(original, found)
            _non_count_parameter_names((axis, alignment, reversed), found)
            return found
        if node.kind == "sketch_base_revolve":
            (
                sketch_name,
                plane,
                origin,
                plane_offset,
                profiles,
                _angle,
                axis,
                direction,
                operations,
                rotation,
            ) = node.data
            _non_count_parameter_names(
                (
                    sketch_name,
                    plane,
                    origin,
                    plane_offset,
                    profiles,
                    axis,
                    direction,
                    operations,
                    rotation,
                ),
                found,
            )
            return found
        if node.kind == "sheet_base":
            (
                sketch_name,
                plane,
                origin,
                plane_offset,
                profiles,
                operations,
                thickness,
                bend_radius,
                _k_factor,
                rule_name,
            ) = node.data
            _non_count_parameter_names(
                (
                    sketch_name,
                    plane,
                    origin,
                    plane_offset,
                    profiles,
                    operations,
                    thickness,
                    bend_radius,
                    rule_name,
                ),
                found,
            )
            return found
        if node.kind == "sheet_contour_flange":
            (
                contour,
                distance,
                thickness,
                bend_radius,
                _k_factor,
                rule_name,
                flip,
                reverse,
            ) = node.data
            _non_count_parameter_names(
                (
                    contour,
                    distance,
                    thickness,
                    bend_radius,
                    rule_name,
                    flip,
                    reverse,
                ),
                found,
            )
            return found
        if node.kind == "sheet_edge_flange":
            original, edges, height, _angle, height_from, position, flip = node.data
            _non_count_parameter_names(original, found)
            _non_count_parameter_names(
                (edges, height, height_from, position, flip),
                found,
            )
            return found
        if node.kind == "sheet_hem":
            original, edges, length, gap, flip = node.data
            _non_count_parameter_names(original, found)
            _non_count_parameter_names((edges, length, gap, flip), found)
            return found
        if node.kind == "sheet_path_flange":
            original, edge, path, radius = node.data
            _non_count_parameter_names(original, found)
            _non_count_parameter_names((edge, path, radius), found)
            return found
        if node.kind == "sheet_perforate":
            original, diameter, pitch, margin, pattern = node.data
            _non_count_parameter_names(original, found)
            _non_count_parameter_names(
                (diameter, pitch, margin, pattern),
                found,
            )
            return found
        if node.kind == "sheet_fold":
            original, line, _angle, fixed, position, flip = node.data
            _non_count_parameter_names(original, found)
            _non_count_parameter_names((line, fixed, position, flip), found)
            return found
        if node.kind == "sketch_pattern_rectangular":
            (
                source, _count1, spacing1, dir1,
                _count2, spacing2, dir2,
                alignment, alignment2,
                reversed1, reversed2,
            ) = node.data
            _non_count_parameter_names(source, found)
            _non_count_parameter_names(
                (dir1, spacing1, dir2, spacing2,
                 alignment, alignment2, reversed1, reversed2),
                found,
            )
            return found
        _non_count_parameter_names(node.data, found)
    elif isinstance(node, (tuple, list)):
        for item in node:
            _non_count_parameter_names(item, found)
    else:
        found.update(param.name for param in parameters_in(node))
    return found


def _pattern_angle_parameter_names(node, found=None):
    """Collect direct Parameters used as native angle fields in degrees."""
    if found is None:
        found = set()
    if isinstance(node, Shape):
        if node.kind == "hole":
            angle = _hole_spec(node)["countersink_angle"]
            if angle is not None:
                found.update(param.name for param in parameters_in(angle))
            return found
        if node.kind == "sketch_base_revolve":
            (
                _sketch_name,
                _plane,
                _origin,
                _plane_offset,
                _profiles,
                angle,
                _axis,
                _direction,
                _operations,
                _rotation,
            ) = node.data
            found.update(param.name for param in parameters_in(angle))
            return found
        if node.kind == "sheet_edge_flange":
            original, _edges, _height, angle, _height_from, _position, _flip = node.data
            found.update(param.name for param in parameters_in(angle))
            _pattern_angle_parameter_names(original, found)
            return found
        if node.kind == "sheet_fold":
            original, _line, angle, _fixed, _position, _flip = node.data
            found.update(param.name for param in parameters_in(angle))
            _pattern_angle_parameter_names(original, found)
            return found
        if node.kind == "circular_pattern":
            (
                original, _sources, _axis, _count, angle,
                _alignment, _reversed,
            ) = node.data
            found.update(param.name for param in parameters_in(angle))
            _pattern_angle_parameter_names(original, found)
            return found
        _pattern_angle_parameter_names(node.data, found)
    elif isinstance(node, (tuple, list)):
        for item in node:
            _pattern_angle_parameter_names(item, found)
    return found


def _sheet_dimensionless_parameter_names(node, found=None):
    """Collect direct Parameters used as dimensionless sheet-rule values."""
    if found is None:
        found = set()
    if isinstance(node, Shape):
        if node.kind == "sheet_base":
            (
                _sketch_name,
                _plane,
                _origin,
                _plane_offset,
                _profiles,
                _operations,
                _thickness,
                _bend_radius,
                k_factor,
                _rule_name,
            ) = node.data
            found.update(param.name for param in parameters_in(k_factor))
            return found
        if node.kind == "sheet_contour_flange":
            (
                _contour,
                _distance,
                _thickness,
                _bend_radius,
                k_factor,
                _rule_name,
                _flip,
                _reverse,
            ) = node.data
            found.update(param.name for param in parameters_in(k_factor))
            return found
        _sheet_dimensionless_parameter_names(node.data, found)
    elif isinstance(node, (tuple, list)):
        for item in node:
            _sheet_dimensionless_parameter_names(item, found)
    return found


_AUTO_HISTORY_FEATURE_NAMES = {
    "solid.box": "Box",
    "solid.sphere": "Sphere",
    "solid.cylinder": "Cylinder",
    "solid.cone": "Cone",
    "solid.revolve": "Revolve",
    "solid.hole": "Hole",
}


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

    if root.kind in ("fillet", "chamfer", "shell", "material_assignment"):
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


def _to_commands(shape, name):
    if shape.kind == "named_feature":
        source, feature_name, suppressed = shape.data
        steps, base = _to_commands(source, name)
        parent = _named_feature_parent(source)
        start = 0
        if parent is not None:
            parent_steps, _ = _to_commands(parent, name)
            start = len(parent_steps)
        return _named_feature_commands(
            steps,
            feature_name,
            suppressed,
            start=start,
        ), base
    if shape.kind == "exported_feature":
        return _to_commands(shape.data[0], name)
    if shape.kind == "sketch_open_chain":
        return compile_open_chain(shape)

    if shape.kind == "sheet_contour_flange":
        (
            contour,
            distance,
            thickness,
            bend_radius,
            k_factor,
            rule_name,
            flip,
            reverse,
        ) = shape.data

        _require_positive(distance, "contour flange distance")
        _require_positive(thickness, "contour flange thickness")
        _require_positive(bend_radius, "contour flange bend radius")
        k = pv(k_factor)
        if not 0 < k < 1:
            raise ModelError(
                "contour flange k_factor must be between 0 and 1"
            )

        sketch, meta, curves = compile_open_chain_with_curves(contour)
        rule = _command(
            "sheet.manage_rules",
            name=rule_name,
            thickness=command_value(thickness),
            k_factor=command_value(k_factor),
            bend_radius=command_value(bend_radius),
            active=True,
        )
        params = {
            "type": "contour",
            "sketch": meta["sketch_name"],
            "curves": curves,
            "distance": command_value(distance),
            "rule": rule_name,
            "body_name": name,
        }
        if flip:
            params["flip"] = True
        if reverse:
            params["reverse"] = True

        meta.update(
            {
                "sheet": True,
                "thickness": thickness,
                "bend_radius": bend_radius,
                "k_factor": k_factor,
                "rule_name": rule_name,
            }
        )
        return [
            rule,
            *sketch,
            _command("sheet.flange", **params),
        ], meta

    if shape.kind == "sheet_base":
        (
            sketch_name,
            plane,
            origin,
            plane_offset,
            profiles,
            operations,
            thickness,
            bend_radius,
            k_factor,
            rule_name,
        ) = shape.data
        _require_positive(thickness, "sheet metal thickness")
        _require_positive(bend_radius, "sheet metal bend radius")
        k = pv(k_factor)
        if not 0 < k < 1:
            raise ModelError("sheet metal k_factor must be between 0 and 1")

        sketch, meta = compile_standalone_sketch(
            sketch_name,
            plane,
            origin,
            plane_offset,
            profiles,
            operations,
        )
        rule = _command(
            "sheet.manage_rules",
            name=rule_name,
            thickness=command_value(thickness),
            k_factor=command_value(k_factor),
            bend_radius=command_value(bend_radius),
            active=True,
        )
        base = _command(
            "sheet.flange",
            type="base",
            sketch=sketch_name,
            rule=rule_name,
            body_name=name,
        )
        meta.update(
            {
                "sheet": True,
                "thickness": thickness,
                "bend_radius": bend_radius,
                "k_factor": k_factor,
                "rule_name": rule_name,
            }
        )
        return [rule, *sketch, base], meta

    if shape.kind == "sheet_edge_flange":
        (
            original,
            edges,
            height,
            angle,
            height_from,
            position,
            flip,
        ) = shape.data
        steps, base = _to_commands(original, name)
        if not base or not base.get("sheet"):
            raise ModelError("sheet flange requires existing sheet material")
        params = {
            "type": "edge",
            "edges": [
                [command_value(value) for value in point]
                for point in edges
            ],
            "height": command_value(height),
            "angle": command_value(angle),
            "body": name,
        }
        if height_from is not None:
            params["height_from"] = height_from
        if position is not None:
            params["position"] = position
        if flip:
            params["flip"] = True
        return steps + [_command("sheet.flange", **params)], base

    if shape.kind == "sheet_hem":
        original, edges, length, gap, flip = shape.data
        steps, base = _to_commands(original, name)
        if not base or not base.get("sheet"):
            raise ModelError("sheet hem requires existing sheet material")
        params = {
            "edges": [
                [command_value(value) for value in point]
                for point in edges
            ],
            "length": command_value(length),
            "body": name,
        }
        if gap is not None:
            params["gap"] = command_value(gap)
        if flip:
            params["flip"] = True
        return steps + [_command("sheet.hem", **params)], base

    if shape.kind == "sheet_path_flange":
        original, edge, path, radius = shape.data
        steps, base = _to_commands(original, name)
        if not base or not base.get("sheet"):
            raise ModelError(
                "sheet path flange requires existing sheet material"
            )
        sketch, meta, curves = compile_open_chain_with_curves(path)
        params = {
            "edge": [command_value(value) for value in edge],
            "sketch": meta["sketch_name"],
            "curves": curves,
            "body": name,
        }
        if radius is not None:
            params["radius"] = command_value(radius)
        return steps + sketch + [
            _command("sheet.path_flange", **params)
        ], base

    if shape.kind == "sheet_perforate":
        original, diameter, pitch, margin, pattern = shape.data
        steps, base = _to_commands(original, name)
        if not base or not base.get("sheet"):
            raise ModelError(
                "sheet perforation requires existing sheet material"
            )
        params = {
            "diameter": command_value(diameter),
            "pitch": command_value(pitch),
            "body": name,
        }
        if margin is not None:
            params["margin"] = command_value(margin)
        if pattern != "staggered":
            params["pattern"] = pattern
        return steps + [_command("sheet.perforate", **params)], base

    if shape.kind == "sheet_fold":
        original, line, angle, fixed, position, flip = shape.data
        steps, base = _to_commands(original, name)
        params = {
            "angle": command_value(angle),
            "position": position,
            "flip": flip,
            "body": name,
        }
        if isinstance(line, Shape):
            if line.kind != "sketch_open_chain":
                raise ModelError(
                    "associative sheet fold requires a Sketch.line(...) Shape"
                )
            segments = line.data[4]
            if len(segments) != 1 or segments[0][0] != "line":
                raise ModelError(
                    "associative sheet fold requires exactly one straight Sketch line"
                )
            sketch, meta = compile_open_chain(line)
            steps += sketch
            params["sketch"] = meta["sketch_name"]
            params["curve"] = "l1"
        else:
            params["points"] = [
                [command_value(v) for v in point]
                for point in line
            ]
        if fixed is not None:
            params["fixed"] = [command_value(v) for v in fixed]
        return steps + [_command("sheet.fold", **params)], base

    if shape.kind in ("box", "placed_box", "tapered_box", "sketch_base_extrusion", "sketch_base_revolve"):
        return compile_base(shape, name)
    if _is_pure_csg_tree(shape):
        from .csg import _csg_new
        return _csg_new(shape, name), None
    if shape.kind == "circular_pattern":
        (
            original, sources, axis, count, angle,
            alignment, reversed,
        ) = shape.data
        steps, base = _to_commands(original, name)
        if isinstance(axis, str):
            native_axis = axis
        else:
            origin, direction = axis
            native_axis = {
                "origin": [command_value(value) for value in origin],
                "dir": list(direction),
            }
        params = dict(
            features=[
                _native_feature_name(original, source, name)
                for source in sources
            ],
            axis=native_axis,
            count=command_value(count),
            alignment=alignment,
            reversed=reversed,
        )
        if angle is not None:
            params["angle"] = (
                command_value(angle)
                if isinstance(angle, Parameter)
                else f"{number_text(angle)} deg"
            )
        return steps + [_command("solid.pattern.circular", **params)], base
    if shape.kind == "rectangular_pattern":
        (
            original, sources,
            dir1, count1, spacing1,
            dir2, count2, spacing2,
            alignment, alignment2,
            reversed1, reversed2,
        ) = shape.data
        steps, base = _to_commands(original, name)
        params = dict(
            features=[
                _native_feature_name(original, source, name)
                for source in sources
            ],
            dir1=list(dir1),
            count1=command_value(count1),
            spacing1=command_value(spacing1),
            alignment=alignment,
            reversed=reversed1,
        )
        if dir2 is not None:
            params.update(
                dir2=list(dir2),
                count2=command_value(count2),
                spacing2=command_value(spacing2),
                alignment2=alignment2,
                reversed2=reversed2,
            )
        return steps + [_command("solid.pattern.rectangular", **params)], base
    if shape.kind == "material_assignment":
        base_shape, material, density, color = shape.data
        steps, base = _to_commands(base_shape, name)
        creation = dict(name=material, density_g_cm3=density)
        if color is not None:
            creation["color"] = color
        return steps + [
            _command("material.create", **creation),
            _command("material.assign", bodies=[name], material=material),
        ], base
    if shape.kind == "appearance_assignment":
        base_shape, color = shape.data
        steps, base = _to_commands(base_shape, name)
        return steps + [
            _command("appearance.assign", bodies=[name], color=color),
        ], base
    if shape.kind == "shell":
        original, thickness, faces = shape.data
        steps, base = _to_commands(original, name)
        topology, resolved = _face_name_commands(steps, faces, name)
        return steps + topology + [
            _shell_command(thickness, resolved, name)
        ], base
    if shape.kind == "fillet":
        original, radius, edges = shape.data
        steps, base = _to_commands(original, name)
        topology = []
        if isinstance(edges, _FaceBoundarySelection):
            topology, resolved = _face_boundary_edge_commands(steps, edges, name)
        else:
            resolved = _resolve_feature_edges(base, edges)
        return steps + topology + [
            _fillet_command(
                base,
                radius,
                resolved,
                name,
                vertical=(edges is Edges.VERTICAL),
            )
        ], base
    if shape.kind == "chamfer":
        original, distance, edges, distance2, flip = shape.data
        steps, base = _to_commands(original, name)
        topology = []
        if isinstance(edges, _FaceBoundarySelection):
            topology, resolved = _face_boundary_edge_commands(steps, edges, name)
        else:
            resolved = _resolve_feature_edges(base, edges)
        return steps + topology + [
            _chamfer_command(
                distance,
                resolved,
                name,
                distance2=distance2,
                flip=flip,
            )
        ], base
    if shape.kind in ("union", "difference", "intersection"):
        original, added = shape.data
        steps, base = _to_commands(original, name)

        feature_name = None
        named_state = None
        if added.kind == "named_feature":
            added, named_name, named_suppressed = added.data
            named_state = (named_name, named_suppressed)
        elif added.kind == "exported_feature":
            added, _export_name = added.data

        def finish(added_steps):
            combined = steps + added_steps
            if named_state is None:
                return combined, base
            named_name, named_suppressed = named_state
            return _named_feature_commands(
                combined,
                named_name,
                named_suppressed,
                start=len(steps),
            ), base

        if added.kind == "labeled":
            added, feature_name = added.data
        if added.kind == "anchored":
            return finish(
                _attached_commands(
                    shape,
                    original,
                    added,
                    name,
                    feature_name=feature_name,
                )
            )
        if added.kind in ("sketch_base_extrusion", "sketch_base_revolve"):
            operation = {
                "union": "join",
                "difference": "cut",
                "intersection": "intersect",
            }[shape.kind]
            added_steps, _ = compile_base(
                added,
                name,
                operation=operation,
            )
            return finish(added_steps)
        if added.kind == "explicit_sketch_extrusion":
            face_query_index = 1 + sum(
                command["command"] == "model.faces"
                for command in steps
            )
            sketch_index = 1 + sum(
                command["command"] == "sketch.create"
                for command in steps
            )
            return finish(
                _explicit_sketch_commands(
                    shape,
                    original,
                    added,
                    name,
                    face_query_index=face_query_index,
                    sketch_index=sketch_index,
                )
            )
        if added.kind == "placed3d" and added.data[0].kind in (
                "lip", "snap_fit", "boss", "rest"):
            if shape.kind != "union":
                raise ModelError("plastic features are added with +")
            plastic, x, y, z = added.data
            return finish([
                _plastic_feature_command(plastic, (x, y, z), name)
            ])
        if added.kind == "placed3d" and added.data[0].kind == "hole":
            hole, x, y, z = added.data
            return finish(_hole_commands(hole, (x, y, z), name))
        if added.kind == "hole":
            raise ModelError("Hole must be positioned with .attach() or .at()")
        if added.kind in ("lip", "snap_fit", "boss", "rest"):
            raise ModelError(
                f"{added.kind} must be positioned with .attach() or .at()"
            )
        primitive_kind = (
            added.data[0].kind if added.kind == "placed3d" else added.kind
        )
        if primitive_kind in ("cylinder", "cone") and added.kind in (
                "cylinder", "cone", "placed3d"):
            from .csg import _csg_apply
            operation = {
                "union": "join",
                "difference": "cut",
                "intersection": "intersect",
            }[shape.kind]
            return finish(_csg_apply(added, name, operation))
        raise ModelError(f"unsupported CAD feature {added.kind}")
    raise ModelError(f"unsupported CAD solid {shape.kind}")


def compile_features(shape, name):
    """Compile native commands with deterministic, source-oriented parameters."""
    steps, _ = _to_commands(shape, name)
    # On an extruded polygon the sweep distance is the first independent
    # dimension of the feature. Keep it before coordinates of its profile.
    # XY rectangular footprints instead list their plan dimensions first.
    root = shape
    while root.kind in (
        "exported_feature", "named_feature", "fillet", "chamfer", "shell", "union", "difference",
        "material_assignment", "appearance_assignment",
    ):
        root = root.data[0]
    if root.kind == "sketch_base_extrusion":
        profiles = root.data[4]
        profile = profiles[0][0] if len(profiles) == 1 else None
        if profile is not None and profile.kind == "polygon":
            parameters = _collect((root.data[5], shape))
        else:
            parameters = _collect(shape)
    else:
        parameters = _collect(shape)

    count_parameters = _pattern_count_parameter_names(shape)
    angle_parameters = _pattern_angle_parameter_names(shape)
    sheet_dimensionless_parameters = _sheet_dimensionless_parameter_names(shape)
    normal_parameters = _non_count_parameter_names(shape)

    shared_roles = count_parameters & angle_parameters
    if shared_roles:
        names = ", ".join(sorted(shared_roles))
        raise ModelError(
            "pattern parameter(s) used as both count and angle: "
            f"{names}; use separate model parameters"
        )

    mixed_counts = count_parameters & normal_parameters
    if mixed_counts:
        names = ", ".join(sorted(mixed_counts))
        raise ModelError(
            "pattern count parameter(s) also used as millimetre dimensions: "
            f"{names}; use separate model parameters for count and length"
        )

    mixed_dimensionless = (
        sheet_dimensionless_parameters & normal_parameters
    )
    if mixed_dimensionless:
        names = ", ".join(sorted(mixed_dimensionless))
        raise ModelError(
            "sheet dimensionless parameter(s) also used as millimetre "
            f"dimensions: {names}; use separate model parameters"
        )

    mixed_angles = angle_parameters & normal_parameters
    if mixed_angles:
        names = ", ".join(sorted(mixed_angles))
        raise ModelError(
            "circular pattern angle parameter(s) also used as millimetre "
            f"dimensions: {names}; use separate model parameters for angle "
            "and length"
        )

    dimensionless_parameters = count_parameters | sheet_dimensionless_parameters
    units = {parameter: "" for parameter in dimensionless_parameters}
    units.update({parameter: "deg" for parameter in angle_parameters})
    return _param_commands(parameters, units=units) + steps
