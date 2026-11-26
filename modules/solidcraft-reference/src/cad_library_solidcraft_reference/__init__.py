"""Canonical SolidCraft command-registry capture and verification."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
from typing import Any

import yaml


MIN_COMMAND_COUNT = 100
REQUIRED_COMMANDS = frozenset(
    {
        "engine.commands",
        "solid.box",
        "solid.extrude",
        "sketch.create",
        "sketch.draw.dimensioned",
        "sketch.slot.center_to_center",
    }
)


def validate_registry(value: Any) -> list[dict[str, Any]]:
    """Validate that value looks like the complete SolidCraft command registry."""

    if not isinstance(value, list):
        raise ValueError("SolidCraft command registry must be a JSON array")
    if len(value) < MIN_COMMAND_COUNT:
        raise ValueError(
            "SolidCraft command registry is implausibly small: "
            f"{len(value)} < {MIN_COMMAND_COUNT}"
        )

    commands: list[dict[str, Any]] = []
    ids: set[str] = set()
    duplicates: set[str] = set()
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise ValueError(f"command {index} is not an object")
        command_id = row.get("id")
        label = row.get("label")
        if not isinstance(command_id, str) or not command_id:
            raise ValueError(f"command {index} has no valid id")
        if not isinstance(label, str) or not label:
            raise ValueError(f"command {command_id} has no valid label")
        if command_id in ids:
            duplicates.add(command_id)
        ids.add(command_id)
        commands.append(row)

    if duplicates:
        raise ValueError(
            "duplicate SolidCraft command ids: " + ", ".join(sorted(duplicates))
        )

    missing = sorted(REQUIRED_COMMANDS - ids)
    if missing:
        raise ValueError(
            "required SolidCraft commands missing: " + ", ".join(missing)
        )

    return commands


def normalized_registry(value: Any) -> list[dict[str, Any]]:
    """Validate and sort a registry by stable command id."""

    return sorted(validate_registry(value), key=lambda row: str(row["id"]))


def runtime_output(image: str, *command: str) -> str:
    """Run one command in an already-pulled immutable runtime image."""

    completed = subprocess.run(
        ["docker", "run", "--rm", "--pull=never", image, *command],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return completed.stdout


def capture_runtime(image: str) -> tuple[str, list[dict[str, Any]]]:
    """Pull one runtime image and capture its exact CLI version and registry."""

    subprocess.run(["docker", "pull", image], check=True)
    version = runtime_output(image, "solidcraft-cli", "--version").strip()
    registry = json.loads(runtime_output(image, "solidcraft-cli", "commands"))
    return version, normalized_registry(registry)


def _runtime_command_results(image: str, commands: list[dict[str, Any]]) -> Any:
    """Execute exact native commands in the immutable runtime and return results."""

    document = {"commands": commands}
    with tempfile.TemporaryDirectory(prefix="solidcraft-reference-") as directory:
        host = Path(directory).resolve()
        source = host / "commands.json"
        source.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--pull=never",
                "-v",
                f"{host}:/solidcraft-reference:ro",
                image,
                "solidcraft-cli",
                "run",
                "/solidcraft-reference/commands.json",
                "--param-check",
                "strict",
                "--results",
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        )
    return json.loads(completed.stdout)


def capture_describe_runtime(image: str, command: str) -> tuple[str, Any]:
    """Capture one exact engine.describe result from an immutable runtime."""

    if not isinstance(command, str) or not command.strip():
        raise ValueError("SolidCraft command id is required")
    subprocess.run(["docker", "pull", image], check=True)
    version = runtime_output(image, "solidcraft-cli", "--version").strip()
    result = _runtime_command_results(
        image,
        [
            {
                "command": "engine.describe",
                "params": {"command": command},
            }
        ],
    )
    return version, result


def write_describe_snapshot(snapshot: Path, value: Any) -> None:
    """Write one targeted engine.describe result without hand-normalizing it."""

    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def capture_describe_snapshot(
    *,
    image: str,
    version: str,
    command: str,
    snapshot: Path,
) -> Any:
    """Capture one targeted typed command contract from the immutable runtime."""

    cli_version, result = capture_describe_runtime(image, command)
    if version not in cli_version:
        raise RuntimeError(
            f"runtime version mismatch: expected {version!r} in {cli_version!r}"
        )
    write_describe_snapshot(snapshot, result)
    return result


def verify_describe_snapshot(
    *,
    image: str,
    version: str,
    command: str,
    snapshot: Path,
) -> Any:
    """Require one checked engine.describe result to equal the pinned runtime."""

    cli_version, actual = capture_describe_runtime(image, command)
    if version not in cli_version:
        raise RuntimeError(
            f"runtime version mismatch: expected {version!r} in {cli_version!r}"
        )
    captured = json.dumps(actual, indent=2, sort_keys=True)
    if not snapshot.is_file():
        raise FileNotFoundError(
            f"missing SolidCraft describe snapshot: {snapshot}\n"
            f"Captured runtime result:\n{captured}"
        )
    expected = json.loads(snapshot.read_text(encoding="utf-8"))
    if expected != actual:
        raise RuntimeError(
            f"SolidCraft describe snapshot differs from {image}: {snapshot}\n"
            f"Captured runtime result:\n{captured}"
        )
    return actual


def toolbar(row: dict[str, Any]) -> str:
    tab = str(row.get("tab") or "").strip()
    panel = str(row.get("panel") or "").strip()
    if tab and panel:
        return f"{tab} › {panel}"
    return tab or panel or "–"


def render_commands(commands: list[dict[str, Any]]) -> str:
    """Render the complete registry as a stable human-readable catalog."""

    by_area: dict[str, list[dict[str, Any]]] = {}
    for row in commands:
        area = str(row["id"]).split(".", 1)[0]
        by_area.setdefault(area, []).append(row)

    lines = [
        "# SolidCraft command registry",
        "",
        "Generated from the exact machine-readable output of "
        "`solidcraft-cli commands`.",
        "",
        f"Total registered commands: **{len(commands)}**.",
        "",
    ]
    for area in sorted(by_area):
        lines.extend(
            [
                f"## {area}",
                "",
                "| Command | Id | Toolbar | Planned |",
                "|---|---|---|---|",
            ]
        )
        for row in sorted(by_area[area], key=lambda item: str(item["id"])):
            planned = str(row.get("planned") or "")
            lines.append(
                "| "
                + str(row["label"]).replace("|", "\\|")
                + " | `"
                + str(row["id"])
                + "` | "
                + toolbar(row).replace("|", "\\|")
                + " | "
                + planned.replace("|", "\\|")
                + " |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def source_text(
    *,
    version: str,
    cli_version: str,
    upstream_commit: str,
    runtime_release: str,
    runtime_image: str,
    count: int,
) -> str:
    return f"""# SolidCraft {version} canonical reference snapshot

This directory is generated from the command registry emitted by the qualified
immutable SolidCraft runtime. It is not a hand-authored Forge migration note.

- SolidCraft release: `v{version}`
- Upstream commit: `{upstream_commit}`
- Qualified runtime release: `{runtime_release}`
- Qualified runtime image: `{runtime_image}`
- Captured CLI version: `{cli_version}`
- Registered commands: `{count}`

## Canonical evidence

- `commands.json` is the exact normalized JSON registry captured from
  `solidcraft-cli commands`.
- `commands.md` is generated from `commands.json` for human review.
- `describe/*.json`, when present, are exact targeted read-only
  `engine.describe` results captured from the same immutable runtime.

Forge compatibility conclusions must be traceable to this captured registry,
the exact runtime behavior, or separately recorded upstream source evidence.
Do not replace this directory with a manually selected command subset.
"""


def write_snapshot(
    *,
    out: Path,
    version: str,
    cli_version: str,
    upstream_commit: str,
    runtime_release: str,
    runtime_image: str,
    commands: list[dict[str, Any]],
) -> None:
    """Write the canonical machine, human and provenance files."""

    out.mkdir(parents=True, exist_ok=True)
    normalized = normalized_registry(commands)
    (out / "commands.json").write_text(
        json.dumps(normalized, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "commands.md").write_text(
        render_commands(normalized),
        encoding="utf-8",
    )
    (out / "SOURCE.md").write_text(
        source_text(
            version=version,
            cli_version=cli_version,
            upstream_commit=upstream_commit,
            runtime_release=runtime_release,
            runtime_image=runtime_image,
            count=len(normalized),
        ),
        encoding="utf-8",
    )


def capture_snapshot(
    *,
    image: str,
    version: str,
    upstream_commit: str,
    runtime_release: str,
    out: Path,
) -> int:
    """Capture and write one canonical snapshot from an immutable runtime."""

    cli_version, commands = capture_runtime(image)
    if version not in cli_version:
        raise RuntimeError(
            f"runtime version mismatch: expected {version!r} in {cli_version!r}"
        )
    write_snapshot(
        out=out,
        version=version,
        cli_version=cli_version,
        upstream_commit=upstream_commit,
        runtime_release=runtime_release,
        runtime_image=image,
        commands=commands,
    )
    return len(commands)


def verify_snapshot(*, image: str, version: str, snapshot: Path) -> int:
    """Require one checked snapshot to equal the exact immutable runtime registry."""

    cli_version, actual = capture_runtime(image)
    if version not in cli_version:
        raise RuntimeError(
            f"runtime version mismatch: expected {version!r} in {cli_version!r}"
        )
    if not snapshot.is_file():
        raise FileNotFoundError(f"missing canonical snapshot: {snapshot}")
    expected = normalized_registry(
        json.loads(snapshot.read_text(encoding="utf-8"))
    )
    if expected != actual:
        raise RuntimeError(
            f"canonical snapshot differs from {image}: {snapshot}"
        )
    return len(actual)


def root_runtime_pin(repo: Path) -> tuple[str, str]:
    """Read the authoritative SolidCraft image/version from root ci.yml."""

    data = yaml.safe_load((repo / "ci.yml").read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root ci.yml must be a mapping")
    runtimes = data.get("runtimes")
    solidcraft = runtimes.get("solidcraft") if isinstance(runtimes, dict) else None
    if not isinstance(solidcraft, dict):
        raise ValueError("root ci.yml has no runtimes.solidcraft mapping")
    image = solidcraft.get("image")
    version = solidcraft.get("version")
    if not isinstance(image, str) or not image:
        raise ValueError("root SolidCraft runtime image is invalid")
    if not isinstance(version, str) or not version:
        raise ValueError("root SolidCraft runtime version is invalid")
    return image, version


def verify_pinned_reference(repo: Path) -> int:
    """Verify the versioned checked registry selected by root Forge runtime pins."""

    image, version = root_runtime_pin(repo)
    snapshot = (
        repo
        / "docs"
        / "reference"
        / "solidcraft"
        / version
        / "commands.json"
    )
    return verify_snapshot(image=image, version=version, snapshot=snapshot)


def verify_pinned_describe(repo: Path, command: str) -> Any:
    """Verify one checked typed command contract against the root runtime pin."""

    image, version = root_runtime_pin(repo)
    snapshot = (
        repo
        / "docs"
        / "reference"
        / "solidcraft"
        / version
        / "describe"
        / f"{command}.json"
    )
    return verify_describe_snapshot(
        image=image,
        version=version,
        command=command,
        snapshot=snapshot,
    )


__all__ = [
    "MIN_COMMAND_COUNT",
    "REQUIRED_COMMANDS",
    "capture_describe_runtime",
    "capture_describe_snapshot",
    "capture_runtime",
    "capture_snapshot",
    "normalized_registry",
    "render_commands",
    "root_runtime_pin",
    "source_text",
    "toolbar",
    "validate_registry",
    "verify_describe_snapshot",
    "verify_pinned_describe",
    "verify_pinned_reference",
    "verify_snapshot",
    "write_describe_snapshot",
    "write_snapshot",
]
