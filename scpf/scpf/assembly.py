"""Lower reusable SCPF model instances to native SolidCraft components."""
import re

from .compiler import ModelError
from .core import Anchor, AnchorFrame, AnchorTopology, command_value, parameters_in, pv
from .model_objects import (
    Assembly,
    ModelInstance,
    _CORNER_ANCHORS,
    _anchor_local_point,
    _anchor_origin,
    _corner_native_x,
    _corner_normal,
)
from .compiler import compile_model


_IDENTIFIER = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")


def _command_value(value):
    """Lower symbolic dimensions recursively in assembly command parameters."""
    if isinstance(value, dict):
        return {key: _command_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_command_value(item) for item in value]
    return command_value(value)


def _command(command_name, **params):
    return {
        "command": command_name,
        "params": _command_value(params),
    }


def _concrete_joint_reference(reference):
    """Evaluate topology pick coordinates at authoring time.

    SolidCraft 0.30.1 keeps the selected topology associative, but its joint
    origin pick coordinates themselves are numeric. Joint offset/value
    expressions remain symbolic.
    """
    if not isinstance(reference, dict):
        return reference
    result = dict(reference)
    for key in ("point", "face", "circle", "edge", "on", "corner"):
        value = result.get(key)
        if isinstance(value, (list, tuple)):
            result[key] = [pv(item) for item in value]
    return result


def _component_slug(name):
    text = re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_")
    if not text:
        text = "component"
    if text[0].isdigit():
        text = "_" + text
    return text


def _rewrite_value(value, mapping):
    if isinstance(value, str):
        return _IDENTIFIER.sub(lambda m: mapping.get(m.group(0), m.group(0)), value)
    if isinstance(value, list):
        return [_rewrite_value(item, mapping) for item in value]
    if isinstance(value, tuple):
        return [_rewrite_value(item, mapping) for item in value]
    if isinstance(value, dict):
        return {key: _rewrite_value(item, mapping) for key, item in value.items()}
    return value


def _namespace_commands(commands, component_name, external_names=()):
    """Namespace local component parameters, but keep inherited names intact."""
    external_names = set(external_names)
    local_names = [
        command["params"]["name"]
        for command in commands
        if command["command"] == "parameters.add"
        and command["params"]["name"] not in external_names
    ]
    prefix = _component_slug(component_name)
    mapping = {name: f"{prefix}_{name}" for name in local_names}

    result = []
    for command in commands:
        params = dict(command["params"])
        if command["command"] == "parameters.add":
            if params["name"] in mapping:
                params["name"] = mapping[params["name"]]
        else:
            params = _rewrite_value(params, mapping)
        result.append({"command": command["command"], "params": params})
    return result


def _as_assembly(value):
    if isinstance(value, ModelInstance):
        return Assembly((value,))
    if isinstance(value, Assembly):
        return value
    raise TypeError("assembly result must contain reusable model instances")


def _definition_names(assembly):
    """Assign stable component names in first-occurrence order."""
    names = {}
    class_counts = {}
    for instance in assembly.instances:
        key = instance.definition.key
        if key in names:
            continue
        base = instance.definition.class_name
        count = class_counts.get(base, 0) + 1
        class_counts[base] = count
        names[key] = base if count == 1 else f"{base} {count}"
    return names


def compile_assembly(value, name):
    """Compile a root assembly into reusable components and occurrences."""
    assembly = _as_assembly(value)
    names = _definition_names(assembly)
    commands = []
    occurrence_names = {}
    custom_origin_names = {}
    inherited_parameters = {}
    shared_materials = {}

    # Unrotated named AnchorFrames can be supplied directly to joint.create
    # as an inline occurrence/point/z/x reference. That avoids creating a
    # persistent native joint.origin (and its visible RGB axes). Keep the
    # existing native-origin route only for explicitly rotated occurrences,
    # where SolidCraft can own the local-to-world transform.
    required_custom_origins = set()
    for instance in assembly.instances:
        attachment = instance.attachment
        if attachment is None or attachment.as_built:
            continue
        if (
            isinstance(attachment.parent, str)
            and attachment.target.placement.rotation is not None
        ):
            parent_anchor = dict(attachment.target.definition.anchors)[
                attachment.parent
            ]
            if isinstance(parent_anchor, AnchorTopology):
                raise ModelError(
                    "AnchorTopology on explicitly rotated occurrences "
                    "is not supported yet"
                )
            required_custom_origins.add(
                (id(attachment.target), attachment.parent)
            )
        if (
            isinstance(attachment.child, str)
            and instance.placement.rotation is not None
        ):
            child_anchor = dict(instance.definition.anchors)[attachment.child]
            if isinstance(child_anchor, AnchorTopology):
                raise ModelError(
                    "AnchorTopology on explicitly rotated occurrences "
                    "is not supported yet"
                )
            required_custom_origins.add((id(instance), attachment.child))

    # Named groups are actual empty native components, not just labels in
    # Python. Child component definitions are created under their parent.
    #
    # Grouping is browser/hierarchy structure, not a mechanical constraint.
    # Independent groups are grounded so their child Placement stays in the
    # root coordinate frame. But if a grouped child attaches to an occurrence
    # outside that group, the native group must remain free: grounding that
    # parent frame over-constrains the external joint graph and prevents the
    # attached children from following a moving target.
    group_names = list(dict.fromkeys(
        instance.group_name
        for instance in assembly.instances
        if instance.group_name is not None
    ))
    if set(group_names) & set(names.values()):
        raise ModelError("assembly group name conflicts with a component name")

    externally_attached_groups = {
        instance.group_name
        for instance in assembly.instances
        if (
            instance.group_name is not None
            and instance.attachment is not None
            and instance.attachment.target.group_name != instance.group_name
        )
    }
    for group_name in group_names:
        commands.append(_command(
            "component.create",
            name=group_name,
            activate=False,
            grounded=group_name not in externally_attached_groups,
        ))

    by_definition = {}
    for instance in assembly.instances:
        by_definition.setdefault(instance.definition.key, []).append(instance)

    for key, instances in by_definition.items():
        definition = instances[0].definition
        component_name = names[key]
        parent_names = {instance.group_name for instance in instances}
        if len(parent_names) != 1:
            raise ModelError(
                f"{component_name}: one reusable definition cannot currently "
                "be placed under multiple assembly parents"
            )
        parent_name = instances[0].group_name

        compiled = compile_model(
            definition.shape,
            _component_slug(component_name),
        )["commands"]
        external_names = {
            parameter_name
            for parameter_name, _ in definition.external_parameters
        }
        compiled = _namespace_commands(
            compiled,
            component_name,
            external_names=external_names,
        )
        parameter_commands = [
            command for command in compiled
            if command["command"] == "parameters.add"
        ]
        geometry_commands = [
            command for command in compiled
            if command["command"] != "parameters.add"
        ]

        for command in parameter_commands:
            parameter_name = command["params"]["name"]
            if parameter_name in external_names:
                expression = command["params"]["expression"]
                previous = inherited_parameters.setdefault(
                    parameter_name,
                    expression,
                )
                if previous != expression:
                    raise ModelError(
                        f"conflicting inherited parameter {parameter_name}"
                    )
                if previous == expression and any(
                    existing["command"] == "parameters.add"
                    and existing["params"]["name"] == parameter_name
                    for existing in commands
                ):
                    continue
            commands.append(command)
        first_is_root = (
            instances[0] is assembly.instances[0] and parent_name is None
        )
        first_has_symbolic_move = bool(
            parameters_in(*instances[0].placement.position)
        )
        create_params = {
            "name": component_name,
            "grounded": first_is_root and not first_has_symbolic_move,
        }
        if parent_name is not None:
            create_params["parent"] = parent_name
        commands.append(_command("component.create", **create_params))
        for command in geometry_commands:
            if command["command"] == "material.create":
                material_name = command["params"]["name"]
                previous = shared_materials.get(material_name)
                if previous is None:
                    shared_materials[material_name] = command["params"]
                    commands.append(command)
                elif previous != command["params"]:
                    raise ModelError(
                        f"material {material_name!r} is defined differently "
                        "by multiple components"
                    )
                continue
            commands.append(command)
        commands.append(_command("component.activate", component="root"))

        # Copies are created while the definition's first occurrence is still
        # at native identity. A concrete, unrotated Placement can therefore be
        # supplied directly to occurrence.copy without a later move.
        #
        # Do not pre-translate a rotated copy. SolidCraft 0.42 applies the
        # later occurrence rotation to an already-copied translation, which
        # changes the declared parent-frame position. Rotated copies are made
        # at identity and receive translation + rotation together below.
        #
        # Parameter-driven placement likewise needs a later native operation.
        occurrences = []
        copy_positioned = set()
        for index, instance in enumerate(instances, start=1):
            native_name = f"{component_name}:{index}"
            occurrence_names[id(instance)] = native_name
            occurrences.append((instance, native_name))
            if index > 1:
                position = instance.placement.position
                symbolic_position = bool(parameters_in(*position))
                params = {"component": component_name}
                if (
                    not symbolic_position
                    and instance.placement.rotation is None
                ):
                    concrete_position = [pv(value) for value in position]
                    if any(concrete_position):
                        params["translate"] = concrete_position
                    copy_positioned.add(id(instance))
                commands.append(_command("occurrence.copy", **params))

        # Only explicitly rotated custom anchors need a persistent native
        # joint.origin. Author those while occurrences are still at identity;
        # SolidCraft then owns the local-to-world transform when the occurrence
        # is rotated. Unrotated AnchorFrames are inlined later in joint.create.
        for instance, native_name in occurrences:
            for anchor_name, frame in instance.definition.anchors:
                anchor_key = (id(instance), anchor_name)
                if anchor_key not in required_custom_origins:
                    continue
                origin_name = f"{native_name}.{anchor_name}"
                custom_origin_names[anchor_key] = origin_name
                frame_origin = list(frame.origin)
                if id(instance) in copy_positioned:
                    frame_origin = [
                        frame.origin[i] + pv(instance.placement.position[i])
                        for i in range(3)
                    ]
                commands.append(_command(
                    "joint.origin",
                    name=origin_name,
                    occurrence=native_name,
                    frame={
                        "origin": frame_origin,
                        "z": list(frame.z),
                        "x": list(frame.x),
                    },
                ))

        # Remaining placement work is only what creation-time placement
        # cannot safely express: the definition's first occurrence, symbolic
        # position, or any Placement that includes rotation. A symbolic seed
        # Placement remains symbolic even when that occurrence also carries an
        # Attachment; the later joint owns the semantic relationship, not the
        # parameter-dependency representation of the seed pose. Public
        # Placement semantics do not prescribe this native command choice.
        for instance, native_name in occurrences:
            position = instance.placement.position
            rotation = instance.placement.rotation
            positioned_at_copy = id(instance) in copy_positioned
            symbolic_position = bool(parameters_in(*position))
            expressed_move = symbolic_position

            if rotation is None and positioned_at_copy:
                continue
            if rotation is None and not any(position):
                continue

            for parameter in parameters_in(*position):
                if not any(
                    command["command"] == "parameters.add"
                    and command["params"]["name"] == parameter.name
                    for command in commands
                ):
                    commands.append(_command(
                        "parameters.add",
                        name=parameter.name,
                        expression=f"{parameter.value:g} mm",
                    ))

            if positioned_at_copy:
                translate = [0.0, 0.0, 0.0]
            elif expressed_move:
                translate = list(position)
            else:
                translate = [pv(value) for value in position]

            params = {
                "occurrence": native_name,
                "translate": translate,
            }
            if rotation is not None:
                axis, degrees = rotation
                params.update(axis=list(axis), angle=f"{degrees:g} deg")
            if (
                instance is assembly.instances[0]
                and parent_name is None
                and not expressed_move
            ):
                params["move_grounded"] = True
            commands.append(_command("occurrence.move", **params))

    for instance in assembly.instances:
        attachment = instance.attachment
        if attachment is None:
            continue
        child_occurrence = occurrence_names.get(id(instance))
        parent_occurrence = occurrence_names.get(id(attachment.target))
        if child_occurrence is None or parent_occurrence is None:
            raise ModelError("component attach target must be part of the assembly")

        if attachment.as_built:
            commands.append(_command(
                "joint.as_built",
                type="rigid",
                name=f"Attach {child_occurrence} to {parent_occurrence}",
                a=parent_occurrence,
                b=child_occurrence,
            ))
            continue

        def custom_anchor_reference(model, anchor, occurrence):
            if isinstance(anchor, (AnchorFrame, AnchorTopology)):
                if model.placement.rotation is not None:
                    kind = type(anchor).__name__
                    raise ModelError(
                        f"direct {kind} attachments on explicitly rotated "
                        "occurrences are not supported yet"
                    )
                custom = anchor
            else:
                custom = dict(model.definition.anchors)[anchor]
                if model.placement.rotation is not None:
                    if isinstance(custom, AnchorTopology):
                        raise ModelError(
                            "AnchorTopology on explicitly rotated occurrences "
                            "is not supported yet"
                        )
                    return custom_origin_names[(id(model), anchor)]

            if isinstance(custom, AnchorTopology):
                def world(point):
                    if point is None:
                        return None
                    return [
                        point[i] + model.placement.position[i]
                        for i in range(3)
                    ]

                reference = {
                    "occurrence": occurrence,
                    "edge": world(custom.edge),
                    "on": world(custom.on),
                }
                if custom.corner is not None:
                    reference["corner"] = world(custom.corner)
                if custom.z is not None:
                    reference["z"] = list(custom.z)
                if custom.x is not None:
                    reference["x"] = list(custom.x)
                return reference

            return {
                "occurrence": occurrence,
                "point": [
                    custom.origin[i] + model.placement.position[i]
                    for i in range(3)
                ],
                "z": list(custom.z),
                "x": list(custom.x),
            }

        if isinstance(attachment.parent, Anchor):
            parent_origin = _anchor_origin(
                attachment.target,
                attachment.parent,
                parent_occurrence,
            )
        else:
            parent_origin = custom_anchor_reference(
                attachment.target,
                attachment.parent,
                parent_occurrence,
            )
        explicit_corner_pair = (
            isinstance(attachment.parent, Anchor)
            and isinstance(attachment.child, Anchor)
            and attachment.parent in _CORNER_ANCHORS
            and attachment.child in _CORNER_ANCHORS
        )
        if explicit_corner_pair:
            child_point = _anchor_local_point(instance, attachment.child)
            child_origin = {
                "occurrence": child_occurrence,
                "point": [
                    child_point[i] + instance.placement.position[i]
                    for i in range(3)
                ],
                "z": list(_corner_normal(attachment.child)),
                "x": list(_corner_native_x(attachment.parent)),
            }
        elif isinstance(attachment.child, Anchor):
            child_origin = _anchor_origin(
                instance,
                attachment.child,
                child_occurrence,
            )
        else:
            child_origin = custom_anchor_reference(
                instance,
                attachment.child,
                child_occurrence,
            )
        for parameter in parameters_in(
            attachment.gap,
            *attachment.offset,
        ):
            if not any(
                command["command"] == "parameters.add"
                and command["params"]["name"] == parameter.name
                for command in commands
            ):
                commands.append(_command(
                    "parameters.add",
                    name=parameter.name,
                    expression=f"{parameter.value:g} mm",
                ))

        has_planar_offset = (
            any(pv(value) != 0 for value in attachment.offset)
            or bool(parameters_in(*attachment.offset))
        )
        parent_origin = _concrete_joint_reference(parent_origin)
        child_origin = _concrete_joint_reference(child_origin)

        params = {
            "type": "planar" if has_planar_offset else "rigid",
            "name": f"Attach {child_occurrence} to {parent_occurrence}",
            "a": parent_origin,
            "b": child_origin,
        }
        if attachment.gap != 0:
            params["offset"] = command_value(attachment.gap)
        if has_planar_offset:
            u, v = attachment.offset
            params["values"] = [
                command_value(u),
                command_value(v),
                attachment.angle if attachment.angle is not None else 0.0,
            ]
            if (
                isinstance(attachment.parent, AnchorFrame)
                and isinstance(attachment.child, AnchorFrame)
            ):
                # Both sides already define complete local frames. Prevent
                # SolidCraft from choosing its automatic optional half-turn;
                # the authored X directions are the intended clocking.
                params["angle"] = 0.0
        elif attachment.angle is not None:
            params["angle"] = attachment.angle
        elif isinstance(attachment.child, AnchorFrame):
            # An explicit child frame already defines its complete clocking.
            # Prevent SolidCraft from choosing an optional automatic half-turn.
            params["angle"] = 0.0
        commands.append(_command("joint.create", **params))

    # Keep the finished assembly view clean. Joint glyph visibility is only
    # presentation state in SolidCraft: hidden joints continue to constrain
    # and drive their occurrences. Users can re-enable the Joints folder eye
    # in the Browser whenever they want to inspect the assembly relations.
    if any(
        command["command"] in ("joint.create", "joint.as_built")
        for command in commands
    ):
        commands.append(_command(
            "browser.visibility",
            folder="joints",
            visible=False,
        ))

    if not commands:
        raise ModelError(f"{name} contains no component instances")
    return {"commands": commands}
