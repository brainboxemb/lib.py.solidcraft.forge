"""Forge execution-plan helpers for runtime SolidCraft result binding.

A normal document is still a commands array. When a later command needs an id
returned by an earlier command, the document also carries bindings and uses an
exact {"$ref": "logical-name"} value in command parameters.

The binding is Forge metadata. It is never sent to SolidCraft. The live/replay
executor resolves it from per-step engine.batch results before sending a
dependent phase.
"""

REFERENCE_KEY = "$ref"


def result_ref(name):
    """Return one serializable reference to a previously captured result."""
    if not isinstance(name, str) or not name:
        raise ValueError("execution-plan reference name must be non-empty text")
    return {REFERENCE_KEY: name}


def _reference_name(value):
    if not isinstance(value, dict) or REFERENCE_KEY not in value:
        return None
    if set(value) != {REFERENCE_KEY}:
        raise ValueError(
            "execution-plan $ref object must contain only '$ref'"
        )
    name = value[REFERENCE_KEY]
    if not isinstance(name, str) or not name:
        raise ValueError("execution-plan $ref must name a logical binding")
    return name


def references_in(value):
    """Return logical binding names referenced anywhere in a JSON-like value."""
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
    """Replace all execution-plan references using already captured values."""
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
    """Validate raw commands plus optional Forge runtime result bindings."""
    if not isinstance(document, dict):
        raise ValueError("SCPF execution document must be a JSON object")
    commands = document.get("commands")
    if not isinstance(commands, list):
        raise ValueError("SCPF execution document must contain a 'commands' array")
    if not commands:
        raise ValueError("SCPF execution document has no commands")

    for index, item in enumerate(commands):
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("command"), str)
            or not isinstance(item.get("params", {}), dict)
        ):
            raise ValueError(f"Invalid SCPF command at index {index}")

    bindings = document.get("bindings", {})
    if not isinstance(bindings, dict):
        raise ValueError("SCPF execution-plan 'bindings' must be an object")

    normalized = {}
    for name, spec in bindings.items():
        if not isinstance(name, str) or not name:
            raise ValueError("execution-plan binding name must be non-empty text")
        if not isinstance(spec, dict):
            raise ValueError(f"execution-plan binding {name!r} must be an object")
        if set(spec) != {"command", "field"}:
            raise ValueError(
                f"execution-plan binding {name!r} needs command and field"
            )
        command_index = spec["command"]
        field = spec["field"]
        if (
            not isinstance(command_index, int)
            or isinstance(command_index, bool)
            or not 0 <= command_index < len(commands)
        ):
            raise ValueError(
                f"execution-plan binding {name!r} has invalid command index"
            )
        if not isinstance(field, str) or not field:
            raise ValueError(
                f"execution-plan binding {name!r} has invalid result field"
            )
        normalized[name] = (command_index, field)

    for index, command in enumerate(commands):
        for name in references_in(command.get("params", {})):
            binding = normalized.get(name)
            if binding is None:
                raise ValueError(
                    f"command {index} references unknown binding {name!r}"
                )
            if binding[0] >= index:
                raise ValueError(
                    f"command {index} references binding {name!r} before "
                    "its producing command has completed"
                )
    return document


def binding_specs(document):
    """Return validated logical bindings as name -> (command index, field)."""
    validate_document(document)
    return {
        name: (spec["command"], spec["field"])
        for name, spec in document.get("bindings", {}).items()
    }
