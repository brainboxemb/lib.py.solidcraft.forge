"""Forge execution-document helpers for runtime SolidCraft result binding.

A normal Forge execution document contains a commands array. When a later
command needs a value returned by an earlier native command, the document also
contains explicit bindings and the later command uses a serializable
{"$ref": "logical-name"} value.

Logical references are Forge data. They are resolved by an executor and are
never sent to SolidCraft.
"""

REFERENCE_KEY = "$ref"


def result_ref(name):
    """Return a serializable reference to one captured native result field."""
    if not isinstance(name, str) or not name:
        raise ValueError("execution reference name must be non-empty text")
    return {REFERENCE_KEY: name}


def _reference_name(value):
    if not isinstance(value, dict) or REFERENCE_KEY not in value:
        return None
    if set(value) != {REFERENCE_KEY}:
        raise ValueError("execution $ref object must contain only '$ref'")
    name = value[REFERENCE_KEY]
    if not isinstance(name, str) or not name:
        raise ValueError("execution $ref must name a logical binding")
    return name


def references_in(value):
    """Return all logical binding names referenced in a JSON-like value."""
    name = _reference_name(value)
    if name is not None:
        return {name}
    if isinstance(value, dict):
        result = set()
        for item in value.values():
            result.update(references_in(item))
        return result
    if isinstance(value, (list, tuple)):
        result = set()
        for item in value:
            result.update(references_in(item))
        return result
    return set()


def resolve_references(value, resolved):
    """Replace logical references using already captured native values."""
    name = _reference_name(value)
    if name is not None:
        if name not in resolved:
            raise KeyError(name)
        return resolved[name]
    if isinstance(value, dict):
        return {
            key: resolve_references(item, resolved)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [resolve_references(item, resolved) for item in value]
    if isinstance(value, tuple):
        return [resolve_references(item, resolved) for item in value]
    return value


def validate_document(document):
    """Validate raw commands plus optional runtime result bindings."""
    if not isinstance(document, dict):
        raise ValueError("SCPF execution document must be a JSON object")
    unknown = set(document) - {"commands", "bindings"}
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"unknown SCPF execution document field(s): {names}")

    commands = document.get("commands")
    if not isinstance(commands, list):
        raise ValueError("SCPF execution document must contain a 'commands' array")
    if not commands:
        raise ValueError("SCPF execution document has no commands")

    for index, item in enumerate(commands):
        if (
            not isinstance(item, dict)
            or set(item) - {"command", "params"}
            or not isinstance(item.get("command"), str)
            or not item["command"]
            or not isinstance(item.get("params", {}), dict)
        ):
            raise ValueError(f"invalid SCPF command at index {index}")

    bindings = document.get("bindings", {})
    if not isinstance(bindings, dict):
        raise ValueError("SCPF execution-document 'bindings' must be an object")

    normalized = {}
    for name, spec in bindings.items():
        if not isinstance(name, str) or not name:
            raise ValueError("execution binding name must be non-empty text")
        if not isinstance(spec, dict) or set(spec) != {"command", "field"}:
            raise ValueError(
                f"execution binding {name!r} needs exactly command and field"
            )
        command_index = spec["command"]
        field = spec["field"]
        if (
            not isinstance(command_index, int)
            or isinstance(command_index, bool)
            or not 0 <= command_index < len(commands)
        ):
            raise ValueError(
                f"execution binding {name!r} has invalid command index"
            )
        if not isinstance(field, str) or not field:
            raise ValueError(
                f"execution binding {name!r} has invalid result field"
            )
        normalized[name] = (command_index, field)

    referenced = set()
    for index, command in enumerate(commands):
        names = references_in(command.get("params", {}))
        referenced.update(names)
        for name in names:
            producer = normalized.get(name)
            if producer is None:
                raise ValueError(
                    f"command {index} references unknown binding {name!r}"
                )
            if producer[0] >= index:
                raise ValueError(
                    f"command {index} references binding {name!r} before "
                    "its producing command has completed"
                )

    unused = set(normalized) - referenced
    if unused:
        names = ", ".join(sorted(unused))
        raise ValueError(f"unused execution binding(s): {names}")

    return document


def binding_specs(document):
    """Return validated logical bindings as name -> (command index, field)."""
    validate_document(document)
    return {
        name: (spec["command"], spec["field"])
        for name, spec in document.get("bindings", {}).items()
    }


def requires_runtime_binding(document):
    """Return True when this document cannot be a raw static native plan."""
    validate_document(document)
    return any(
        references_in(command.get("params", {}))
        for command in document["commands"]
    )
