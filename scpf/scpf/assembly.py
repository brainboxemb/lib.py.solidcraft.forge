"""Lower reusable SCPF model instances to native SolidCraft components."""
import re

from .compiler import ModelError
from .core import (
    Anchor,
    AnchorFrame,
    AnchorTopology,
    _NativeExpression,
    _native_dependencies,
    _plain_command_value,
    command_value,
    parameters_in,
    _pv as pv,
)
from .model_objects import (
    Assembly,
    ModelInstance,
    _CORNER_ANCHORS,
    _anchor_local_point,
    _anchor_origin,
    _corner_native_x,
    _corner_normal,
)
from .compiler import _compile_model_commands
from .replay import replay_document


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


def _bound_command(command_name, variable, field="occurrence", **params):
    command = _command(command_name, **params)
    command["bind"] = {variable: field}
    return command


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
    if isinstance(value, _NativeExpression):
        return _NativeExpression(
            _IDENTIFIER.sub(
                lambda match: mapping.get(match.group(0), match.group(0)),
                value,
            ),
            tuple(mapping.get(name, name) for name in value.parameters),
        )
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return [_rewrite_value(item, mapping) for item in value]
    if isinstance(value, tuple):
        return [_rewrite_value(item, mapping) for item in value]
    if isinstance(value, dict):
        return {
            key: _rewrite_value(item, mapping)
            for key, item in value.items()
        }
    return value


def _namespace_commands(
    commands,
    component_name,
    *,
    definition_number,
    external_names=(),
):
    """Namespace local parameters uniquely, but keep inherited names intact."""
    external_names = set(external_names)
    local_names = [
        command["params"]["name"]
        for command in commands
        if command["command"] == "parameters.add"
        and command["params"]["name"] not in external_names
    ]
    prefix = f"d{definition_number}_{_component_slug(component_name)}"
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


def _identity_placement(instance):
    """Return whether one occurrence can be SolidCraft's implicit first placement."""
    position = instance.placement.position
    return (
        instance.placement.rotation is None
        and not parameters_in(*position)
        and not any(pv(value) != 0 for value in position)
    )


def _ordinary_replay_order(instances, component_name, relationship_occurrence_ids):
    """Order non-relationship occurrences for replay-safe create/copy placement."""
    if any(
        instance.occurrence_id in relationship_occurrence_ids
        for instance in instances
    ):
        return list(instances), False

    first = next(
        (instance for instance in instances if _identity_placement(instance)),
        None,
    )
    if first is None:
        raise ModelError(
            f"{component_name}: replay-first Placement requires one occurrence "
            "at identity because SolidCraft component.create cannot place its "
            "first occurrence"
        )

    ordered = [first] + [
        instance
        for instance in instances
        if instance.occurrence_id != first.occurrence_id
    ]
    for instance in ordered[1:]:
        position = instance.placement.position
        if parameters_in(*position):
            raise ModelError(
                f"{component_name}: symbolic copied Placement is not replay-safe "
                "in SolidCraft 0.42; occurrence.copy translate is numeric-only"
            )
        if instance.placement.rotation is not None:
            raise ModelError(
                f"{component_name}: rotated copied Placement is not replay-safe "
                "in SolidCraft 0.42; occurrence.copy has no rotation input"
            )
    return ordered, True


def _relationship_replay_order(instances, component_name):
    """Choose the implicit first occurrence for a relationship definition."""
    for instance in instances:
        if instance.placement.rotation is not None:
            raise ModelError(
                f"{component_name}: rotated relationship Placement is not "
                "replay-safe in SolidCraft 0.42"
            )

    first = next(
        (instance for instance in instances if _identity_placement(instance)),
        None,
    )
    if first is None:
        first = next(
            (
                instance
                for instance in instances
                if instance.attachment is not None
                and not instance.attachment.as_built
            ),
            None,
        )
    if first is None:
        raise ModelError(
            f"{component_name}: SolidCraft must create the first occurrence at "
            "identity, unless a normal joint will place that first occurrence"
        )

    ordered = [first] + [
        instance
        for instance in instances
        if instance.occurrence_id != first.occurrence_id
    ]

    for index, instance in enumerate(ordered):
        attachment = instance.attachment
        if index == 0:
            if attachment is None or attachment.as_built:
                if not _identity_placement(instance):
                    raise ModelError(
                        f"{component_name}: first relationship occurrence "
                        "cannot keep non-identity Placement in replay-first mode"
                    )
            continue

        if attachment is not None and not attachment.as_built:
            continue

        position = instance.placement.position
        if parameters_in(*position):
            raise ModelError(
                f"{component_name}: symbolic Placement of a relationship target "
                "or as-built occurrence is not replay-safe in SolidCraft 0.42"
            )

    return ordered


def _occurrence_labels(assembly, names):
    """Build stable human labels without using SolidCraft browser numbering."""
    totals = {}
    for instance in assembly.instances:
        key = instance.definition.key
        totals[key] = totals.get(key, 0) + 1

    seen = {}
    labels = {}
    for instance in assembly.instances:
        key = instance.definition.key
        seen[key] = seen.get(key, 0) + 1
        component_name = names[key]
        if instance.name is not None:
            label = instance.name
        elif totals[key] == 1:
            label = component_name
        else:
            label = f"{component_name} occurrence {seen[key]}"
        labels[instance.occurrence_id] = label
    return labels


def _occurrence_replay_variables(assembly, labels):
    """Give every Forge occurrence one deterministic replay variable."""
    variables = {}
    counts = {}
    for instance in assembly.instances:
        base = _component_slug(labels[instance.occurrence_id]).lower()
        count = counts.get(base, 0) + 1
        counts[base] = count
        suffix = "" if count == 1 else f"_{count}"
        variables[instance.occurrence_id] = "$" + base + suffix
    return variables


def _validate_attachment_relationships(assembly):
    """Reject relationship states Forge cannot lower completely."""
    for instance in assembly.instances:
        attachment = instance.attachment
        if attachment is None:
            continue
        if attachment.target.attachment is not None:
            raise ModelError(
                "chained attachments are not supported yet; the parent would "
                "move when its first joint is created, before Forge creates the "
                "child joint"
            )
        if attachment.as_built:
            continue
        if (
            instance.placement.rotation is not None
            or attachment.target.placement.rotation is not None
        ):
            raise ModelError(
                "rotated Placement in a normal attachment is not supported yet; "
                "Forge cannot transform every Anchor, AnchorFrame and "
                "AnchorTopology reference through occurrence rotation"
            )


def _compile_assembly_with_dependencies(value, name):
    """Compile a root assembly into reusable components and occurrences."""
    assembly = _as_assembly(value)
    _validate_attachment_relationships(assembly)
    names = _definition_names(assembly)
    commands = []
    occurrence_labels = _occurrence_labels(assembly, names)
    occurrence_refs = _occurrence_replay_variables(
        assembly,
        occurrence_labels,
    )
    inherited_parameters = {}
    shared_materials = {}
    positioned_at_copy = set()
    grounded_occurrence_ids = set()

    # Named groups are empty native components used only for browser hierarchy.
    # They are explicitly ungrounded because SolidCraft would otherwise ground
    # the first component in a new design by default. Physical occurrences keep
    # their own grounding decision below.
    group_names = list(dict.fromkeys(
        instance.group_name
        for instance in assembly.instances
        if instance.group_name is not None
    ))
    if set(group_names) & set(names.values()):
        raise ModelError("assembly group name conflicts with a component name")
    for group_name in group_names:
        commands.append(_command(
            "component.create",
            name=group_name,
            activate=False,
            grounded=False,
        ))

    by_definition = {}
    for instance in assembly.instances:
        by_definition.setdefault(instance.definition.key, []).append(instance)

    for definition_number, (key, instances) in enumerate(
        by_definition.items(),
        start=1,
    ):
        component_name = names[key]
        definition = instances[0].definition
        parent_name = instances[0].group_name

        compiled = _compile_model_commands(
            definition.shape,
            _component_slug(component_name),
        )
        external_names = {
            parameter_name
            for parameter_name, _ in definition.external_parameters
        }
        compiled = _namespace_commands(
            compiled,
            component_name,
            definition_number=definition_number,
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

        first = instances[0]
        first_is_root = (
            first.occurrence_id
            == assembly.instances[0].occurrence_id
        )
        # SolidCraft 0.42 keeps expression-based occurrence moves
        # associative only while the occurrence is ungrounded. A grounded
        # occurrence can be moved with move_grounded=true, but its placement
        # expression does not follow later parameter changes in 0.42.
        #
        # Therefore a root occurrence whose Placement position depends on
        # parameters must remain ungrounded. Fixed/identity roots keep the
        # normal grounded behaviour.
        create_grounded = (
            first_is_root
            and first.attachment is None
            and not parameters_in(*first.placement.position)
        )
        create_params = {
            "name": component_name,
            "grounded": create_grounded,
        }
        if create_grounded:
            grounded_occurrence_ids.add(first.occurrence_id)
        if parent_name is not None:
            create_params["parent"] = parent_name
        commands.append(_bound_command(
            "component.create",
            occurrence_refs[first.occurrence_id],
            **create_params,
        ))

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

        # Create every copy before applying any later occurrence.move. A numeric
        # unrotated copy can receive its final translation directly. Symbolic
        # position or rotation is applied later through the real occurrence id
        # bound from occurrence.copy.
        for instance in instances[1:]:
            params = {"component": component_name}
            if instance.group_name != parent_name:
                params["parent"] = instance.group_name or "root"

            attachment = instance.attachment
            normal_attachment = (
                attachment is not None
                and not attachment.as_built
            )
            position = instance.placement.position
            symbolic_position = bool(parameters_in(*position))
            if (
                not normal_attachment
                and instance.placement.rotation is None
                and not symbolic_position
            ):
                concrete_position = [pv(value) for value in position]
                if any(concrete_position):
                    params["translate"] = concrete_position
                positioned_at_copy.add(instance.occurrence_id)

            commands.append(_bound_command(
                "occurrence.copy",
                occurrence_refs[instance.occurrence_id],
                **params,
            ))

    # Placement is assembly-owned occurrence pose. SolidCraft can express some
    # copies directly with occurrence.copy.translate. The remaining cases use
    # the actual occurrence id returned by component.create/occurrence.copy.
    for instance in assembly.instances:
        attachment = instance.attachment
        if attachment is not None and not attachment.as_built:
            # A normal joint determines this occurrence's pose.
            continue
        if instance.occurrence_id in positioned_at_copy:
            continue
        if _identity_placement(instance):
            continue

        position = instance.placement.position
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

        params = {
            "occurrence": occurrence_refs[instance.occurrence_id],
            "translate": list(position),
        }
        if instance.placement.rotation is not None:
            axis, degrees = instance.placement.rotation
            params["axis"] = list(axis)
            params["angle"] = f"{degrees:g} deg"
        if instance.occurrence_id in grounded_occurrence_ids:
            params["move_grounded"] = True

        commands.append(_command("occurrence.move", **params))

    for instance in assembly.instances:
        attachment = instance.attachment
        if attachment is None:
            continue

        child_id = instance.occurrence_id
        parent_id = attachment.target.occurrence_id
        if child_id not in occurrence_refs or parent_id not in occurrence_refs:
            raise ModelError(
                "Forge cannot address one of these attachment occurrences in "
                "the static SolidCraft 0.42 command document"
            )

        child_occurrence = occurrence_refs[child_id]
        parent_occurrence = occurrence_refs[parent_id]
        child_label = occurrence_labels[child_id]
        parent_label = occurrence_labels[parent_id]
        joint_name = f"Attach {child_label} to {parent_label}"

        if attachment.as_built:
            commands.append(_command(
                "joint.as_built",
                type="rigid",
                name=joint_name,
                a=parent_occurrence,
                b=child_occurrence,
            ))
            continue

        def custom_anchor_reference(model, anchor, occurrence, position):
            if isinstance(anchor, (AnchorFrame, AnchorTopology)):
                custom = anchor
            else:
                custom = dict(model.definition.anchors)[anchor]

            if isinstance(custom, AnchorTopology):
                def world(point):
                    if point is None:
                        return None
                    return [
                        point[i] + position[i]
                        for i in range(3)
                    ]

                reference = {
                    "edge": world(custom.edge),
                    "on": world(custom.on),
                }
                if custom.corner is not None:
                    reference["corner"] = world(custom.corner)
                if custom.z is not None:
                    reference["z"] = list(custom.z)
                if custom.x is not None:
                    reference["x"] = list(custom.x)
            else:
                reference = {
                    "point": [
                        custom.origin[i] + position[i]
                        for i in range(3)
                    ],
                    "z": list(custom.z),
                    "x": list(custom.x),
                }

            reference["occurrence"] = occurrence
            return reference

        parent_position = (0.0, 0.0, 0.0)
        child_position = (0.0, 0.0, 0.0)

        if isinstance(attachment.parent, Anchor):
            parent_origin = _anchor_origin(
                attachment.target,
                attachment.parent,
                parent_occurrence,
                position=parent_position,
            )
        else:
            parent_origin = custom_anchor_reference(
                attachment.target,
                attachment.parent,
                parent_occurrence,
                parent_position,
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
                "point": [
                    child_point[i] + child_position[i]
                    for i in range(3)
                ],
                "z": list(_corner_normal(attachment.child)),
                "x": list(_corner_native_x(attachment.parent)),
            }
            child_origin["occurrence"] = child_occurrence
        elif isinstance(attachment.child, Anchor):
            child_origin = _anchor_origin(
                instance,
                attachment.child,
                child_occurrence,
                position=child_position,
            )
        else:
            child_origin = custom_anchor_reference(
                instance,
                attachment.child,
                child_occurrence,
                child_position,
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
            "name": joint_name,
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
                params["angle"] = 0.0
        elif attachment.angle is not None:
            params["angle"] = attachment.angle
        elif isinstance(attachment.child, AnchorFrame):
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
    dependencies = _native_dependencies(commands)
    document = _plain_command_value(replay_document(commands))
    return document, dependencies


def compile_assembly(value, name):
    """Compile an assembly to the public replay document."""
    return _compile_assembly_with_dependencies(value, name)[0]
