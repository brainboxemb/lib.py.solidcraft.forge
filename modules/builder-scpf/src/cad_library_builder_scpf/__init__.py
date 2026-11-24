"""Compile trusted SCPF source then delegate native execution to builder-solidcraft."""
from pathlib import Path
import json
import tempfile


def build(source: Path, output: Path):
    from scpf.runner import run_script
    from cad_library_builder_solidcraft import build as build_solidcraft

    document = run_script(source)
    if (
        not isinstance(document, dict)
        or not isinstance(document.get("commands"), list)
    ):
        raise RuntimeError(
            "SCPF compiler did not produce a command document"
        )

    with tempfile.TemporaryDirectory(
        prefix="scpf-commands-"
    ) as tmp:
        commands = Path(tmp) / "commands.json"
        commands.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        build_solidcraft(commands, output)
