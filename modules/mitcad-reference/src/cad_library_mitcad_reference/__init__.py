"""Capture and verify version-pinned Mitcad MCP references."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any, TextIO


PROTOCOL = "2025-11-25"
REFERENCE_URI = "mitcad://reference/commands"
MIN_COMMAND_COUNT = 50
REQUIRED_COMMANDS = frozenset({"add_feature", "add_parameter", "edit_feature"})
REQUIRED_FEATURES = frozenset({"box", "extrude", "fillet"})


class MitcadReferenceError(RuntimeError):
    """A Mitcad reference capture or verification failed."""


def git_blob_sha(text: str) -> str:
    raw = text.encode("utf-8")
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def validate_catalog(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Mitcad model_reference catalog must be an object")
    commands = value.get("commands")
    queries = value.get("queries")
    features = value.get("features")
    if not all(isinstance(items, list) for items in (commands, queries, features)):
        raise ValueError("Mitcad catalog must contain commands, queries and features")
    if len(commands) < MIN_COMMAND_COUNT:
        raise ValueError(
            f"Mitcad command catalog is implausibly small: {len(commands)}"
        )
    missing_commands = sorted(REQUIRED_COMMANDS - set(commands))
    missing_features = sorted(REQUIRED_FEATURES - set(features))
    if missing_commands:
        raise ValueError(
            "required Mitcad commands missing: " + ", ".join(missing_commands)
        )
    if missing_features:
        raise ValueError(
            "required Mitcad features missing: " + ", ".join(missing_features)
        )
    return value


class _Session:
    def __init__(self, executable: str, workspace: Path):
        self.process = subprocess.Popen(
            [executable, "mcp", "--workspace", str(workspace)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        self.next_id = 0

    def __enter__(self):
        if self.process.stdin is None or self.process.stdout is None:
            raise MitcadReferenceError("Mitcad MCP pipes were not created")
        return self

    def __exit__(self, *_):
        if self.process.stdin is not None:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=10)
        if self.process.stdout is not None:
            self.process.stdout.close()
        if self.process.stderr is not None:
            self.process.stderr.close()

    @property
    def stdin(self) -> TextIO:
        assert self.process.stdin is not None
        return self.process.stdin

    @property
    def stdout(self) -> TextIO:
        assert self.process.stdout is not None
        return self.process.stdout

    def send(self, message: dict[str, Any]) -> None:
        self.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.stdin.flush()

    def request(self, method: str, params: dict[str, Any] | None = None):
        self.next_id += 1
        message: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": self.next_id,
            "method": method,
        }
        if params is not None:
            message["params"] = params
        self.send(message)
        line = self.stdout.readline()
        if not line:
            stderr = ""
            if self.process.stderr is not None:
                stderr = self.process.stderr.read()
            raise MitcadReferenceError(
                "Mitcad MCP closed before replying: " + stderr.strip()
            )
        response = json.loads(line)
        if response.get("id") != self.next_id:
            raise MitcadReferenceError("Mitcad MCP response id mismatch")
        if "error" in response:
            raise MitcadReferenceError(
                f"Mitcad MCP {method} failed: {response['error']}"
            )
        return response["result"]

    def notify(self, method: str) -> None:
        self.send({"jsonrpc": "2.0", "method": method})

    def initialize(self) -> None:
        result = self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL,
                "capabilities": {},
                "clientInfo": {
                    "name": "forge-mitcad-reference",
                    "version": "1",
                },
            },
        )
        if result.get("protocolVersion") != PROTOCOL:
            raise MitcadReferenceError(
                "unexpected Mitcad MCP protocol: "
                + str(result.get("protocolVersion"))
            )
        self.notify("notifications/initialized")


def _structured_tool_result(result: dict[str, Any]) -> dict[str, Any]:
    structured = result.get("structuredContent")
    if not isinstance(structured, dict):
        raise MitcadReferenceError(
            "model_reference returned no structuredContent"
        )
    content = result.get("content")
    if isinstance(content, list) and content:
        text = content[0].get("text") if isinstance(content[0], dict) else None
        if isinstance(text, str) and json.loads(text) != structured:
            raise MitcadReferenceError(
                "model_reference text and structured content differ"
            )
    return structured


def capture_runtime(
    executable: str,
    *,
    workspace: Path | None = None,
) -> tuple[str, str, dict[str, Any]]:
    version = subprocess.run(
        [executable, "--version"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()

    owned = None
    if workspace is None:
        owned = tempfile.TemporaryDirectory(prefix="forge-mitcad-reference-")
        workspace = Path(owned.name)
    else:
        workspace.mkdir(parents=True, exist_ok=True)

    try:
        with _Session(executable, workspace) as session:
            session.initialize()
            resource = session.request(
                "resources/read", {"uri": REFERENCE_URI}
            )
            contents = resource.get("contents")
            if not isinstance(contents, list) or not contents:
                raise MitcadReferenceError(
                    "Mitcad command-reference resource is empty"
                )
            text = contents[0].get("text")
            if not isinstance(text, str) or not text.strip():
                raise MitcadReferenceError(
                    "Mitcad command-reference resource has no text"
                )
            tool = session.request(
                "tools/call",
                {"name": "model_reference", "arguments": {}},
            )
            catalog = validate_catalog(_structured_tool_result(tool))
            return version, text, catalog
    finally:
        if owned is not None:
            owned.cleanup()


def verify_source_snapshot(
    snapshot: Path,
    *,
    reference_blob: str,
) -> None:
    reference = snapshot / "commands.md"
    if not reference.is_file():
        raise FileNotFoundError(f"missing Mitcad command reference: {reference}")
    actual = git_blob_sha(reference.read_text(encoding="utf-8"))
    if actual != reference_blob:
        raise MitcadReferenceError(
            f"Mitcad source reference blob mismatch: {actual} != "
            f"{reference_blob}"
        )


def source_text(
    *,
    version: str,
    upstream_commit: str,
    release_tag: str,
    source_reference_blob: str,
    runtime_reference_blob: str | None,
    captured_cli: str | None,
) -> str:
    runtime = (
        f"- Captured CLI version: `{captured_cli}`\n"
        if captured_cli
        else "- Runtime machine catalog: not captured\n"
    )
    runtime_blob = runtime_reference_blob or "not captured"
    return f"""# Mitcad {version} reference snapshot

This directory is pinned to the exact Mitcad release source and runtime used by
Forge's experimental backend work.

- Mitcad release: `{release_tag}`
- Upstream commit: `{upstream_commit}`
- Upstream command-reference blob: `{source_reference_blob}`
- Live MCP command-resource blob: `{runtime_blob}`
{runtime}
## Evidence

- `commands.md` is the exact upstream `core/model-api/src/commands.md`
  blob from the release tag; it is the complete source reference.
- Mitcad's live `mitcad://reference/commands` resource is generated from
  that source but filters entries outside the server vocabulary; its exact
  runtime text is therefore tracked separately as `runtime-commands.md`.
- `commands.json` is the exact no-argument `model_reference` structured
  catalog captured from `mitcad-cli mcp`.

Do not edit a checked version snapshot by hand. Add a new version directory
when the Mitcad target changes.
"""


def write_snapshot(
    *,
    out: Path,
    version: str,
    upstream_commit: str,
    release_tag: str,
    source_reference_blob: str,
    runtime_reference_blob: str,
    cli_version: str,
    reference: str,
    catalog: dict[str, Any],
) -> None:
    verify_source_snapshot(out, reference_blob=source_reference_blob)
    actual_runtime_blob = git_blob_sha(reference)
    if actual_runtime_blob != runtime_reference_blob:
        raise MitcadReferenceError(
            "runtime command resource differs from the pinned runtime blob: "
            f"{actual_runtime_blob} != {runtime_reference_blob}"
        )
    (out / "runtime-commands.md").write_text(reference, encoding="utf-8")
    (out / "commands.json").write_text(
        json.dumps(validate_catalog(catalog), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "SOURCE.md").write_text(
        source_text(
            version=version,
            upstream_commit=upstream_commit,
            release_tag=release_tag,
            source_reference_blob=source_reference_blob,
            runtime_reference_blob=runtime_reference_blob,
            captured_cli=cli_version,
        ),
        encoding="utf-8",
    )


def capture_snapshot(
    *,
    executable: str,
    version: str,
    upstream_commit: str,
    release_tag: str,
    source_reference_blob: str,
    runtime_reference_blob: str,
    out: Path,
) -> int:
    cli_version, reference, catalog = capture_runtime(executable)
    if version not in cli_version:
        raise MitcadReferenceError(
            f"Mitcad CLI version mismatch: expected {version!r} in "
            f"{cli_version!r}"
        )
    write_snapshot(
        out=out,
        version=version,
        upstream_commit=upstream_commit,
        release_tag=release_tag,
        source_reference_blob=source_reference_blob,
        runtime_reference_blob=runtime_reference_blob,
        cli_version=cli_version,
        reference=reference,
        catalog=catalog,
    )
    return len(catalog["commands"])


def verify_runtime_snapshot(
    *,
    executable: str,
    version: str,
    snapshot: Path,
    source_reference_blob: str,
    runtime_reference_blob: str,
) -> int:
    cli_version, reference, catalog = capture_runtime(executable)
    if version not in cli_version:
        raise MitcadReferenceError(
            f"Mitcad CLI version mismatch: expected {version!r} in "
            f"{cli_version!r}"
        )
    verify_source_snapshot(snapshot, reference_blob=source_reference_blob)
    actual_runtime_blob = git_blob_sha(reference)
    if actual_runtime_blob != runtime_reference_blob:
        raise MitcadReferenceError(
            "live Mitcad command resource differs from pinned runtime "
            f"reference: {actual_runtime_blob} != {runtime_reference_blob}"
        )
    runtime_path = snapshot / "runtime-commands.md"
    if runtime_path.is_file():
        expected_runtime = runtime_path.read_text(encoding="utf-8")
        if expected_runtime != reference:
            raise MitcadReferenceError(
                "live Mitcad command resource differs from runtime-commands.md"
            )
    catalog_path = snapshot / "commands.json"
    if not catalog_path.is_file():
        raise FileNotFoundError(
            "runtime verification requires captured commands.json"
        )
    expected = validate_catalog(
        json.loads(catalog_path.read_text(encoding="utf-8"))
    )
    if expected != validate_catalog(catalog):
        raise MitcadReferenceError(
            "live Mitcad model_reference catalog differs from snapshot"
        )
    return len(catalog["commands"])


__all__ = [
    "MIN_COMMAND_COUNT",
    "MitcadReferenceError",
    "PROTOCOL",
    "REFERENCE_URI",
    "REQUIRED_COMMANDS",
    "REQUIRED_FEATURES",
    "capture_runtime",
    "capture_snapshot",
    "git_blob_sha",
    "source_text",
    "validate_catalog",
    "verify_runtime_snapshot",
    "verify_source_snapshot",
    "write_snapshot",
]
