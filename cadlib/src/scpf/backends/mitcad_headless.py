"""Execute experimental Forge Mitcad command documents through mitcad-cli MCP."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any


PROTOCOL = "2025-11-25"


class MitcadHeadlessError(RuntimeError):
    """Native Mitcad MCP execution failed."""


def validate_document(document: Any) -> list[dict[str, Any]]:
    if not isinstance(document, dict):
        raise MitcadHeadlessError("Mitcad command document must be an object")
    if document.get("format") != "scpf-mitcad":
        raise MitcadHeadlessError("not an scpf-mitcad command document")
    if document.get("version") != 1:
        raise MitcadHeadlessError(
            f"unsupported scpf-mitcad version: {document.get('version')!r}"
        )
    if document.get("backend") != "mitcad":
        raise MitcadHeadlessError("Mitcad command document has wrong backend")

    commands = document.get("commands")
    if not isinstance(commands, list) or not commands:
        raise MitcadHeadlessError("Mitcad command document has no commands")
    for index, command in enumerate(commands):
        if not isinstance(command, dict):
            raise MitcadHeadlessError(
                f"Mitcad command {index} is not an object"
            )
        name = command.get("cmd")
        if not isinstance(name, str) or not name:
            raise MitcadHeadlessError(
                f"Mitcad command {index} has no cmd"
            )
    return commands


class _Session:
    def __init__(self, executable: str, workspace: Path):
        try:
            self.process = subprocess.Popen(
                [executable, "mcp", "--workspace", str(workspace)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
        except OSError as exc:
            raise MitcadHeadlessError(
                f"cannot start Mitcad MCP server: {exc}"
            ) from exc
        self.next_id = 0

    def __enter__(self):
        if self.process.stdin is None or self.process.stdout is None:
            raise MitcadHeadlessError("Mitcad MCP pipes were not created")
        self.initialize()
        return self

    def __exit__(self, *_):
        if self.process.stdin is not None:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=15)
        if self.process.stdout is not None:
            self.process.stdout.close()
        if self.process.stderr is not None:
            self.process.stderr.close()

    def _send(self, value: dict[str, Any]) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(
            json.dumps(value, separators=(",", ":")) + "\n"
        )
        self.process.stdin.flush()

    def request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.next_id += 1
        request: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": self.next_id,
            "method": method,
        }
        if params is not None:
            request["params"] = params
        self._send(request)

        assert self.process.stdout is not None
        line = self.process.stdout.readline()
        if not line:
            stderr = ""
            if self.process.stderr is not None:
                stderr = self.process.stderr.read()
            raise MitcadHeadlessError(
                "Mitcad MCP closed before replying"
                + (f": {stderr.strip()}" if stderr.strip() else "")
            )
        try:
            response = json.loads(line)
        except json.JSONDecodeError as exc:
            raise MitcadHeadlessError(
                f"Mitcad MCP returned non-JSON output: {line!r}"
            ) from exc
        if response.get("id") != self.next_id:
            raise MitcadHeadlessError("Mitcad MCP response id mismatch")
        if "error" in response:
            raise MitcadHeadlessError(
                f"Mitcad MCP {method} failed: {response['error']}"
            )
        result = response.get("result")
        if not isinstance(result, dict):
            raise MitcadHeadlessError(
                f"Mitcad MCP {method} returned no result object"
            )
        return result

    def notify(self, method: str) -> None:
        self._send({"jsonrpc": "2.0", "method": method})

    def initialize(self) -> None:
        result = self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL,
                "capabilities": {},
                "clientInfo": {
                    "name": "forge-mitcad-backend",
                    "version": "1",
                },
            },
        )
        if result.get("protocolVersion") != PROTOCOL:
            raise MitcadHeadlessError(
                "unexpected Mitcad MCP protocol: "
                + str(result.get("protocolVersion"))
            )
        self.notify("notifications/initialized")

    def tool(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        result = self.request(
            "tools/call",
            {"name": name, "arguments": arguments},
        )
        structured = result.get("structuredContent")
        if not isinstance(structured, dict):
            raise MitcadHeadlessError(
                f"Mitcad tool {name} returned no structuredContent"
            )
        if result.get("isError"):
            message = structured.get("error") or structured
            raise MitcadHeadlessError(
                f"Mitcad tool {name} failed: {message}"
            )

        content = result.get("content")
        if isinstance(content, list) and content:
            first = content[0]
            text = first.get("text") if isinstance(first, dict) else None
            if isinstance(text, str):
                try:
                    textual = json.loads(text)
                except json.JSONDecodeError:
                    textual = None
                if textual is not None and textual != structured:
                    raise MitcadHeadlessError(
                        f"Mitcad tool {name} text/structured result mismatch"
                    )
        return structured


def _export_format(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    aliases = {
        "stp": "step",
        "step": "step",
        "stl": "stl",
        "obj": "obj",
        "3mf": "3mf",
        "gltf": "gltf",
        "glb": "glb",
    }
    try:
        return aliases[suffix]
    except KeyError as exc:
        raise MitcadHeadlessError(
            f"unsupported Mitcad export suffix: {path.suffix or '<none>'}"
        ) from exc


def run_document(
    document: dict[str, Any],
    *,
    save: str | Path,
    export: str | Path | None = None,
    executable: str = "mitcad-cli",
    work_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Execute one experimental command document through native Mitcad MCP.

    The MCP workspace owns all native writes. Requested output paths are copied
    out only after Mitcad reports successful save/export operations.
    """

    commands = validate_document(document)
    save = Path(save).resolve()
    save.parent.mkdir(parents=True, exist_ok=True)
    export_path = Path(export).resolve() if export is not None else None
    if export_path is not None:
        export_path.parent.mkdir(parents=True, exist_ok=True)

    owned = None
    if work_dir is None:
        owned = tempfile.TemporaryDirectory(prefix="scpf-mitcad-")
        workspace = Path(owned.name).resolve()
    else:
        workspace = Path(work_dir).resolve()
        workspace.mkdir(parents=True, exist_ok=True)

    native_save_name = "forge-output.mitcad"
    native_save = workspace / native_save_name
    native_export_name = None
    native_export = None
    if export_path is not None:
        native_export_name = "forge-output" + export_path.suffix.lower()
        native_export = workspace / native_export_name

    try:
        with _Session(executable, workspace) as session:
            created = session.tool("document_create", {})
            handle = created.get("document")
            if not isinstance(handle, str) or not handle:
                raise MitcadHeadlessError(
                    "Mitcad document_create returned no document handle"
                )

            applied = session.tool(
                "model_command",
                {
                    "document": handle,
                    "command": commands,
                    "timeline": "none",
                },
            )
            if applied.get("applied") is not True:
                raise MitcadHeadlessError(
                    "Mitcad model_command did not report applied=true"
                )
            failed = applied.get("failed_features", [])
            if failed:
                raise MitcadHeadlessError(
                    f"Mitcad model has failed features: {failed!r}"
                )

            bodies_reply = session.tool(
                "model_query",
                {
                    "document": handle,
                    "query": {
                        "query": "bodies",
                        "properties": True,
                    },
                },
            )
            bodies = bodies_reply.get("result")
            if not isinstance(bodies, list):
                raise MitcadHeadlessError(
                    "Mitcad bodies query returned no body list"
                )

            session.tool(
                "document_save",
                {
                    "document": handle,
                    "path": native_save_name,
                    "overwrite": True,
                },
            )

            export_reply = None
            if export_path is not None:
                assert native_export_name is not None
                export_reply = session.tool(
                    "model_export",
                    {
                        "document": handle,
                        "path": native_export_name,
                        "format": _export_format(export_path),
                        "overwrite": True,
                    },
                )

            session.tool(
                "document_close",
                {
                    "document": handle,
                    "discard": False,
                },
            )

        if not native_save.is_file():
            raise MitcadHeadlessError(
                "Mitcad reported save success but wrote no .mitcad file"
            )
        shutil.copy2(native_save, save)

        if export_path is not None:
            assert native_export is not None
            if not native_export.is_file():
                raise MitcadHeadlessError(
                    "Mitcad reported export success but wrote no export file"
                )
            shutil.copy2(native_export, export_path)

        return {
            "completed": len(commands),
            "bodies": bodies,
            "command_result": applied,
            "export_result": export_reply,
        }
    finally:
        if owned is not None:
            owned.cleanup()


__all__ = [
    "MitcadHeadlessError",
    "PROTOCOL",
    "run_document",
    "validate_document",
]
