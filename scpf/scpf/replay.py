"""Replay helpers for SCPF command documents.

A replay variable such as $board_2 stands for a SolidCraft id that is only
known while the file is being executed. The replay file keeps the variable;
the per-run log records the concrete value returned by SolidCraft.
"""
import hashlib
import json
import re


REPLAY_FORMAT = "scpf-replay"
REPLAY_VERSION = 1
_VARIABLE = re.compile(r"^\$[A-Za-z_][A-Za-z0-9_]*$")


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


def variables_in(value):
    """Return exact replay-variable strings contained in a JSON value."""
    found = set()

    def visit(item):
        if isinstance(item, str):
            if _VARIABLE.fullmatch(item):
                found.add(item)
        elif isinstance(item, dict):
            for child in item.values():
                visit(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                visit(child)

    visit(value)
    return found


def resolve_value(value, variables):
    """Replace exact replay-variable strings with values from this run."""
    if isinstance(value, str) and _VARIABLE.fullmatch(value):
        if value not in variables:
            raise ValueError(f"replay variable {value} has not been bound yet")
        return variables[value]
    if isinstance(value, dict):
        return {key: resolve_value(item, variables) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve_value(item, variables) for item in value]
    if isinstance(value, tuple):
        return [resolve_value(item, variables) for item in value]
    return value


def validate_replay_document(document):
    """Validate native command JSON or the versioned SCPF replay extension."""
    if not isinstance(document, dict) or not isinstance(document.get("commands"), list):
        raise ValueError("SolidCraft JSON must contain a 'commands' array")
    if not document["commands"]:
        raise ValueError("SolidCraft JSON has no commands")

    replay = is_replay_document(document)
    if replay:
        if document.get("version") != REPLAY_VERSION:
            raise ValueError(
                f"unsupported SCPF replay version {document.get('version')!r}; "
                f"expected {REPLAY_VERSION}"
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
            for variable, field in bind.items():
                if not isinstance(variable, str) or not _VARIABLE.fullmatch(variable):
                    raise ValueError(
                        f"invalid replay variable {variable!r} at command index {index}"
                    )
                if variable in declared:
                    raise ValueError(f"replay variable {variable} is bound more than once")
                if not isinstance(field, str) or not field:
                    raise ValueError(
                        f"invalid result field for {variable} at command index {index}"
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
