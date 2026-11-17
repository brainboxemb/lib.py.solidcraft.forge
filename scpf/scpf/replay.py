"""Replay helpers for SCPF command documents.

A replay variable such as $board_2 stands for a SolidCraft value that is only
known while the file is being executed. Replay v2 also allows selecting one
record from a command result and referring to fields on that bound record, for
example $top_face.point and $top_face.index.

The replay file keeps variables symbolic; the per-run log records the concrete
values returned by SolidCraft.
"""
import hashlib
import json
import re


REPLAY_FORMAT = "scpf-replay"
REPLAY_VERSION = 2
_SUPPORTED_REPLAY_VERSIONS = (1, 2)
_VARIABLE = re.compile(r"^\$[A-Za-z_][A-Za-z0-9_]*$")
_FIELD = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def replay_document(commands):
    """Return a versioned SCPF replay document."""
    return {
        "format": REPLAY_FORMAT,
        "version": REPLAY_VERSION,
        "commands": commands,
    }


def is_replay_document(document):
    return document.get("format") == REPLAY_FORMAT


def replay_hash(document):
    encoded = json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _variable_reference(value):
    """Return (root variable, field path) for one exact replay reference."""
    if not isinstance(value, str):
        return None
    parts = value.split(".")
    if not parts or not _VARIABLE.fullmatch(parts[0]):
        return None
    if any(not _FIELD.fullmatch(field) for field in parts[1:]):
        return None
    return parts[0], tuple(parts[1:])


def variables_in(value):
    """Return replay-variable roots contained in a JSON value."""
    found = set()

    def visit(item):
        reference = _variable_reference(item)
        if reference is not None:
            found.add(reference[0])
        elif isinstance(item, dict):
            for child in item.values():
                visit(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                visit(child)

    visit(value)
    return found


def resolve_value(value, variables):
    """Replace replay references with values from this run."""
    reference = _variable_reference(value)
    if reference is not None:
        variable, fields = reference
        if variable not in variables:
            raise ValueError(f"replay variable {variable} has not been bound yet")
        resolved = variables[variable]
        for field in fields:
            if not isinstance(resolved, dict) or field not in resolved:
                raise ValueError(
                    f"replay variable reference {value} has no field {field!r}"
                )
            resolved = resolved[field]
        return resolved
    if isinstance(value, dict):
        return {key: resolve_value(item, variables) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_value(item, variables) for item in value]
    if isinstance(value, tuple):
        return [resolve_value(item, variables) for item in value]
    return value


def _validate_binding_spec(spec, *, version, variable, index):
    if isinstance(spec, str):
        if not spec:
            raise ValueError(
                f"invalid result field for {variable} at command index {index}"
            )
        return
    if version < 2 or not isinstance(spec, dict):
        raise ValueError(
            f"invalid result binding for {variable} at command index {index}"
        )
    allowed = {"field", "where", "max", "select"}
    unknown = set(spec) - allowed
    if unknown:
        raise ValueError(
            f"unknown binding selector key(s) for {variable}: "
            + ", ".join(sorted(unknown))
        )
    field = spec.get("field")
    if not isinstance(field, str) or not field:
        raise ValueError(
            f"binding selector for {variable} needs a non-empty field"
        )
    where = spec.get("where", {})
    if not isinstance(where, dict):
        raise ValueError(f"binding selector where for {variable} must be an object")
    for key in where:
        if not isinstance(key, str) or not key:
            raise ValueError(f"binding selector where keys for {variable} must be text")
    for key in ("max", "select"):
        value = spec.get(key)
        if value is not None and (not isinstance(value, str) or not value):
            raise ValueError(f"binding selector {key} for {variable} must be text")


def validate_replay_document(document):
    """Validate native command JSON or the versioned SCPF replay extension."""
    if not isinstance(document, dict) or not isinstance(document.get("commands"), list):
        raise ValueError("SolidCraft JSON must contain a 'commands' array")
    if not document["commands"]:
        raise ValueError("SolidCraft JSON has no commands")

    replay = is_replay_document(document)
    version = document.get("version")
    if replay:
        if version not in _SUPPORTED_REPLAY_VERSIONS:
            raise ValueError(
                f"unsupported SCPF replay version {version!r}; "
                f"supported versions are {_SUPPORTED_REPLAY_VERSIONS}"
            )
    elif "format" in document or "version" in document:
        raise ValueError("unknown replay document format")

    declared = set()
    for index, item in enumerate(document["commands"]):
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("command"), str)
            or not isinstance(item.get("params", {}), dict)
        ):
            raise ValueError(f"invalid command at index {index}")

        bind = item.get("bind")
        if bind is not None and not replay:
            raise ValueError("command bindings require an scpf-replay document")
        if bind is not None:
            if not isinstance(bind, dict) or not bind:
                raise ValueError(f"invalid bind map at command index {index}")
            for variable, spec in bind.items():
                if not isinstance(variable, str) or not _VARIABLE.fullmatch(variable):
                    raise ValueError(
                        f"invalid replay variable {variable!r} at command index {index}"
                    )
                if variable in declared:
                    raise ValueError(f"replay variable {variable} is bound more than once")
                _validate_binding_spec(
                    spec,
                    version=version,
                    variable=variable,
                    index=index,
                )

        if replay:
            unknown = variables_in(item.get("params", {})) - declared
            if unknown:
                names = ", ".join(sorted(unknown))
                raise ValueError(
                    f"command index {index} uses replay variable(s) before binding: {names}"
                )
            if bind:
                declared.update(bind)

    return document


def resolved_command(item, variables):
    """Return the native SolidCraft command for one replay step."""
    return {
        "command": item["command"],
        "params": resolve_value(item.get("params", {}), variables),
    }


def replay_chunks(commands):
    """Split commands only where a later step needs a newly bound variable."""
    chunks = []
    current = []
    available = set()
    pending = set()

    for item in commands:
        needed = variables_in(item.get("params", {}))
        if not needed <= available:
            if current:
                chunks.append(current)
                available.update(pending)
                current = []
                pending = set()
            if not needed <= available:
                names = ", ".join(sorted(needed - available))
                raise ValueError(
                    f"replay command needs unresolved variable(s): {names}"
                )

        current.append(item)
        pending.update(item.get("bind", {}))

    if current:
        chunks.append(current)
    return chunks


def _binding_value(result, spec, *, command, variable):
    if not isinstance(result, dict):
        raise ValueError(f"{command} did not return an object for {variable}")

    if isinstance(spec, str):
        if spec not in result:
            raise ValueError(
                f"{command} did not return field {spec!r} needed for {variable}"
            )
        return result[spec]

    field = spec["field"]
    if field not in result:
        raise ValueError(
            f"{command} did not return field {field!r} needed for {variable}"
        )
    value = result[field]
    where = spec.get("where", {})
    maximum = spec.get("max")
    select = spec.get("select")
    if not where and maximum is None and select is None:
        return value

    if not isinstance(value, list):
        raise ValueError(
            f"{command} field {field!r} is not a list for selector {variable}"
        )
    candidates = [
        item for item in value
        if isinstance(item, dict)
        and all(item.get(key) == expected for key, expected in where.items())
    ]
    if not candidates:
        raise ValueError(
            f"{command} selector for {variable} matched no {field!r} records"
        )

    if maximum is not None:
        scored = [
            (item.get(maximum), item)
            for item in candidates
            if isinstance(item.get(maximum), (int, float))
        ]
        if not scored:
            raise ValueError(
                f"{command} selector for {variable} has no numeric {maximum!r}"
            )
        best = max(score for score, _ in scored)
        candidates = [item for score, item in scored if score == best]

    if len(candidates) != 1:
        raise ValueError(
            f"{command} selector for {variable} matched {len(candidates)} records"
        )

    selected = candidates[0]
    if select is not None:
        if select not in selected:
            raise ValueError(
                f"{command} selected record has no field {select!r} for {variable}"
            )
        selected = selected[select]
    if selected is None:
        raise ValueError(f"{command} selector for {variable} resolved to null")
    return selected


def apply_bindings(items, results, variables):
    """Bind replay variables from one completed native batch."""
    if not isinstance(results, list) or len(results) != len(items):
        raise ValueError(
            "SolidCraft batch did not return one result per replay command"
        )

    bound_per_command = []
    for item, result in zip(items, results):
        bindings = {}
        for variable, spec in item.get("bind", {}).items():
            value = _binding_value(
                result,
                spec,
                command=item["command"],
                variable=variable,
            )
            variables[variable] = value
            bindings[variable] = value
        bound_per_command.append(bindings)
    return bound_per_command


def replay_log(document, variables, entries):
    """Build the diagnostic log for one concrete replay run."""
    return {
        "format": "scpf-replay-log",
        "version": 1,
        "replay_sha256": replay_hash(document),
        "variables": dict(variables),
        "commands": entries,
        "completed": len(entries),
    }
