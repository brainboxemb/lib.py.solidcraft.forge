"""Compile trusted SCPF source and execute its native command contract."""
from pathlib import Path
import json
import shutil
import subprocess
import tempfile


def _require_artifacts(paths):
    for path in paths:
        if not path.is_file() or not path.stat().st_size:
            raise RuntimeError(f"SCPF build produced no artifact: {path.name}")


def _build_replay(document, output: Path):
    """Execute an SCPF replay document with its runtime binding semantics."""
    from scpf.headless import run_document

    target = output.parent
    target.mkdir(parents=True, exist_ok=True)
    native = target / "model.sc"
    preview = target / "model.png"
    commands = target / "solidcraft.json"
    results = target / "replay-results.json"
    replay_log = target / "replay-log.json"
    replay_work = target / "replay_work"

    commands.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    run_document(
        document,
        save=native,
        export=output,
        results_out=results,
        replay_log_out=replay_log,
        work_dir=replay_work,
    )
    subprocess.run(
        [
            "solidcraft-cli",
            "snapshot",
            str(native),
            "--out",
            str(preview),
            "--no-grid",
            "--no-axes",
        ],
        check=True,
    )
    _require_artifacts(
        (commands, native, output, preview, results, replay_log)
    )


def build(source: Path, output: Path):
    """Compile one SCPF model, preserving replay semantics when required."""
    from scpf.runner import run_script
    from scpf.replay import is_replay_document

    document = run_script(source)
    if (
        not isinstance(document, dict)
        or not isinstance(document.get("commands"), list)
    ):
        raise RuntimeError(
            "SCPF compiler did not produce a command document"
        )

    if is_replay_document(document):
        _build_replay(document, output)
        return

    from cad_library_builder_solidcraft import build as build_solidcraft

    with tempfile.TemporaryDirectory(
        prefix="scpf-commands-"
    ) as tmp:
        commands = Path(tmp) / "commands.json"
        commands.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        build_solidcraft(commands, output)
