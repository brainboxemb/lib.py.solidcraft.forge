"""Send compiled CAD commands to an already running SolidCraft desktop app.

This is a small client for SolidCraft's *existing* authenticated control
protocol, not an MCP server. It never starts a headless CAD session.

Protocol: https://docs.solidcraft.io/dev/control-protocol.html
"""
import json
import os
from pathlib import Path
import socket
import sys

from .replay import (
    apply_bindings,
    is_replay_document,
    replay_chunks,
    replay_log,
    resolved_command,
    validate_replay_document,
)


class LiveError(RuntimeError):
    """Live SolidCraft connection or command execution failed."""


def control_directory():
    override = os.environ.get("SOLIDCRAFT_CONTROL_DIR")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if not base:
            raise LiveError("LOCALAPPDATA is not set. Pass a control directory.")
        return Path(base) / "SolidCraft" / "control"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "SolidCraft" / "control"
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "solidcraft" / "control"


def locate_port(directory):
    path = directory / "current.port"
    try:
        value = path.read_text(encoding="ascii").strip()
        port = int(value)
    except (OSError, ValueError) as exc:
        raise LiveError(
            f"No live SolidCraft port in {path}. Start the SolidCraft GUI "
            "and enable Preferences > Assistant > Let AI agents connect."
        ) from exc
    if not 1 <= port <= 65535:
        raise LiveError(f"Invalid SolidCraft control port in {path}: {port}")
    return port


def parse_connect(connect, directory):
    if connect is True or connect == "auto":
        return locate_port(directory)
    if isinstance(connect, int):
        port = connect
    elif isinstance(connect, str):
        address = connect.removeprefix("127.0.0.1:")
        try:
            port = int(address)
        except ValueError as exc:
            raise LiveError("Use --connect or --connect 127.0.0.1:PORT") from exc
    else:
        raise LiveError("Invalid --connect value")
    if not 1 <= port <= 65535:
        raise LiveError("Control port must be 1..65535")
    return port


def read_launch_token(directory, port):
    env_token = os.environ.get("SOLIDCRAFT_CONTROL_TOKEN")
    if env_token:
        return env_token
    path = directory / f"{port}.token"
    try:
        token = path.read_text(encoding="ascii").strip()
    except OSError as exc:
        raise LiveError(
            f"No SolidCraft authentication token at {path}. "
            "The GUI may not be running, or the token path differs."
        ) from exc
    if not token:
        raise LiveError(f"Empty SolidCraft token: {path}")
    return token


def _read_reply(connection):
    # The control protocol has one JSON object per newline. A batch can
    # take some time in the GUI; a timeout is NOT proof that nothing happened.
    with connection.makefile("rb") as stream:
        line = stream.readline(16 * 1024 * 1024 + 1)
    if not line:
        raise LiveError("SolidCraft closed the control connection without a reply")
    if len(line) > 16 * 1024 * 1024:
        raise LiveError("SolidCraft response exceeded 16 MiB")
    try:
        answer = json.loads(line)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LiveError("Invalid response from SolidCraft control channel") from exc
    if answer.get("id") != 1 or "ok" not in answer:
        raise LiveError("Unexpected control-channel response")
    return answer


def _send_request(method, params, *, connect="auto", directory=None, timeout=3610):
    """Send one authenticated request to the running SolidCraft GUI."""
    directory = Path(directory) if directory is not None else control_directory()
    port = parse_connect(connect, directory)
    token = read_launch_token(directory, port)
    request = {
        "id": 1,
        "method": method,
        "token": token,
        "params": params,
    }
    encoded = (json.dumps(request, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    if len(encoded) > 16 * 1024 * 1024:
        raise LiveError("Control request exceeds SolidCraft protocol limit")
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=5) as connection:
            connection.settimeout(timeout)
            connection.sendall(encoded)
            answer = _read_reply(connection)
    except (ConnectionRefusedError, ConnectionResetError, OSError) as exc:
        if isinstance(exc, socket.timeout):
            raise LiveError(
                "Control channel timed out. The request MAY STILL BE RUNNING in "
                "SolidCraft. Inspect the app; do not send it again blindly."
            ) from exc
        raise LiveError(
            f"Cannot talk to the running SolidCraft GUI at 127.0.0.1:{port}: {exc}"
        ) from exc

    if not answer["ok"]:
        raise LiveError(
            f"SolidCraft rejected {method}: {answer.get('error', answer)}"
        )
    return answer.get("result")


def new_design(*, name=None, connect="auto", directory=None, timeout=60):
    """Replace the active GUI design with a new empty SolidCraft design."""
    if name is not None and (not isinstance(name, str) or not name.strip()):
        raise LiveError("New design name must be non-empty text")
    command_params = {} if name is None else {"name": name}
    result = _send_request(
        "engine.execute",
        {
            "command": "file.new",
            "params": command_params,
            "param_check": "strict",
        },
        connect=connect,
        directory=directory,
        timeout=timeout,
    )
    if not isinstance(result, dict) or not isinstance(result.get("name"), str):
        raise LiveError(f"Unexpected file.new result: {result!r}")
    return result

def send_commands(commands, *, connect="auto", directory=None, timeout=3610):
    """Execute native command plan *in the open GUI* as one rollback batch.

    On command failure the server normally rolls back all changes. No new
    tab, GUI launch or file save is performed. The active design is modified
    on success; the user should start with a new blank design.
    """
    if not isinstance(commands, list) or not commands:
        raise LiveError("No commands to send")
    if len(commands) > 10000:
        raise LiveError("SolidCraft engine.batch supports at most 10,000 commands")
    for index, entry in enumerate(commands):
        if not isinstance(entry, dict) or not isinstance(entry.get("command"), str):
            raise LiveError(f"Invalid command at index {index}")
        if not isinstance(entry.get("params", {}), dict):
            raise LiveError(f"Invalid command parameters at index {index}")
    result = _send_request(
        "engine.batch",
        {
            "commands": commands,
            "rollback": True,
            "param_check": "strict",
        },
        connect=connect,
        directory=directory,
        timeout=timeout,
    )
    if not isinstance(result, dict):
        raise LiveError(f"Unexpected batch result: {result!r}")
    if result.get("failed") is not None:
        failed = result["failed"]
        rolled_back = result.get("rolled_back", False)
        raise LiveError(
            f"SolidCraft command failed at step {failed.get('index')}: "
            f"{failed.get('command')}: {failed.get('error')}. "
            f"Rolled back: {rolled_back}"
        )
    if result.get("completed") != len(commands):
        raise LiveError(f"SolidCraft reported only {result.get('completed')} of {len(commands)} completed commands")
    return result



def _execute(command, params, *, connect="auto", directory=None, timeout=3610):
    """Execute one SolidCraft command and return its native result."""
    return _send_request(
        "engine.execute",
        {
            "command": command,
            "params": params,
            "param_check": "strict",
        },
        connect=connect,
        directory=directory,
        timeout=timeout,
    )


def send_document(document, *, connect="auto", directory=None, timeout=3610):
    """Execute a native or SCPF replay document.

    SCPF replay variables are bound from SolidCraft command results during this
    run. When variables require more than one native batch, a SolidCraft
    checkpoint makes the complete replay atomic across those batches.
    """
    try:
        validate_replay_document(document)
    except ValueError as exc:
        raise LiveError(str(exc)) from exc

    commands = document["commands"]
    if not is_replay_document(document):
        result = send_commands(
            commands,
            connect=connect,
            directory=directory,
            timeout=timeout,
        )
        entries = [
            {
                "index": index,
                "command": item["command"],
                "resolved_params": item.get("params", {}),
            }
            for index, item in enumerate(commands)
        ]
        result = dict(result)
        result["variables"] = {}
        result["replay_log"] = replay_log(document, {}, entries)
        return result

    try:
        chunks = replay_chunks(commands)
    except ValueError as exc:
        raise LiveError(str(exc)) from exc
    has_bindings = any(item.get("bind") for item in commands)
    checkpoint = None
    variables = {}
    entries = []
    completed = 0

    if has_bindings and len(chunks) > 1:
        checkpoint_result = _execute(
            "edit.checkpoint",
            {},
            connect=connect,
            directory=directory,
            timeout=timeout,
        )
        if (
            not isinstance(checkpoint_result, dict)
            or not isinstance(checkpoint_result.get("checkpoint"), int)
        ):
            raise LiveError(
                f"Unexpected edit.checkpoint result: {checkpoint_result!r}"
            )
        checkpoint = checkpoint_result["checkpoint"]

    try:
        command_index = 0
        for chunk in chunks:
            native = [
                resolved_command(item, variables)
                for item in chunk
            ]
            batch = send_commands(
                native,
                connect=connect,
                directory=directory,
                timeout=timeout,
            )
            results = batch.get("results")
            try:
                bindings_for_chunk = apply_bindings(
                    chunk,
                    results,
                    variables,
                )
            except ValueError as exc:
                raise LiveError(str(exc)) from exc

            for item, native_item, bindings in zip(
                chunk, native, bindings_for_chunk
            ):
                entry = {
                    "index": command_index,
                    "command": item["command"],
                    "resolved_params": native_item["params"],
                }
                if bindings:
                    entry["bindings"] = bindings
                entries.append(entry)
                command_index += 1
            completed += len(chunk)

    except Exception as exc:
        if checkpoint is not None:
            try:
                _execute(
                    "edit.restore_checkpoint",
                    {"checkpoint": checkpoint},
                    connect=connect,
                    directory=directory,
                    timeout=timeout,
                )
            except Exception as restore_exc:
                raise LiveError(
                    f"{exc}; restoring replay checkpoint also failed: "
                    f"{restore_exc}"
                ) from exc
        raise

    if checkpoint is not None:
        _execute(
            "edit.restore_checkpoint",
            {"checkpoint": checkpoint, "forget": True},
            connect=connect,
            directory=directory,
            timeout=timeout,
        )

    return {
        "completed": completed,
        "variables": dict(variables),
        "replay_log": replay_log(document, variables, entries),
    }
