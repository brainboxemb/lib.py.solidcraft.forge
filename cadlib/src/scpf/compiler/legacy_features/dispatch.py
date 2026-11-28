"""Legacy ordered-feature recursive dispatch and compilation."""

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
from .detect import _is_pure_csg_tree
from .topology import (
    _face_boundary_edge_commands,
    _face_name_commands,
    _resolve_feature_edges,
    _fillet_command,
    _chamfer_command,
    _shell_command,
)
from .features import (
    _hole_commands,
    _plastic_feature_command,
    _attached_commands,
)
from .sketch import _explicit_sketch_commands
from .parameters import (
    _pattern_count_parameter_names,
    _non_count_parameter_names,
    _pattern_angle_parameter_names,
    _sheet_dimensionless_parameter_names,
)
from .history import (
    _native_feature_name,
    _named_feature_parent,
    _named_feature_commands,
)


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
        from ...csg import _csg_new
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

    if shape.kind == "solid_transform":
        original, translate, axis, angle, origin = shape.data
        steps, base = _to_commands(original, name)
        params = {"bodies": [name]}
        if any(pv(value) != 0 for value in translate):
            params["translate"] = [
                command_value(value) for value in translate
            ]
        if pv(angle) != 0:
            params["axis"] = list(axis)
            params["angle"] = (
                command_value(angle)
                if parameters_in(angle)
                else f"{number_text(angle)} deg"
            )
            params["origin"] = [
                command_value(value) for value in origin
            ]
        return steps + [_command("solid.move", **params)], base
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
            from ...csg import _csg_apply
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
