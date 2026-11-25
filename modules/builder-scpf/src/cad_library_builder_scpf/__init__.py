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


def _drawing_exports(document):
    artifacts = document.get("artifacts", {})
    drawings = artifacts.get("drawings", [])
    if not isinstance(drawings, list):
        raise RuntimeError("SCPF drawing artifacts must be a list")
    result = []
    seen = set()
    for index, item in enumerate(drawings):
        if (
            not isinstance(item, dict)
            or set(item) != {
                "name", "drawing", "sheet", "orientation", "pdf", "png",
            }
        ):
            raise RuntimeError(f"invalid SCPF drawing artifact at index {index}")
        variable = item["drawing"]
        sheet_variable = item["sheet"]
        orientation_variable = item["orientation"]
        relative = Path(item["pdf"])
        preview = Path(item["png"])
        if (
            not isinstance(variable, str)
            or not variable.startswith("$")
            or not isinstance(sheet_variable, str)
            or not sheet_variable.startswith("$")
            or not isinstance(orientation_variable, str)
            or not orientation_variable.startswith("$")
            or relative.is_absolute()
            or preview.is_absolute()
            or ".." in relative.parts
            or ".." in preview.parts
            or relative.suffix.lower() != ".pdf"
            or preview.suffix.lower() != ".png"
            or relative.with_suffix(".png") != preview
            or not relative.parts
            or relative.parts[0] != "drawings"
            or not preview.parts
            or preview.parts[0] != "drawings"
        ):
            raise RuntimeError(f"invalid SCPF drawing artifact at index {index}")
        keys = (relative.as_posix(), preview.as_posix())
        if any(key in seen for key in keys):
            raise RuntimeError(
                f"duplicate SCPF drawing artifact: {relative.as_posix()}"
            )
        seen.update(keys)
        result.append(
            (
                item["name"],
                variable,
                sheet_variable,
                orientation_variable,
                relative,
                preview,
            )
        )
    return result


def _export_drawings(document, variables, native: Path, target: Path, replay_work: Path):
    exports = _drawing_exports(document)
    produced = []
    for index, (
        name,
        variable,
        sheet_variable,
        orientation_variable,
        relative,
        preview_relative,
    ) in enumerate(exports, start=1):
        for required in (variable, sheet_variable, orientation_variable):
            if required not in variables:
                raise RuntimeError(
                    f"unbound drawing artifact variable: {required}"
                )
        if variables[orientation_variable] != "landscape":
            raise RuntimeError(
                f"SCPF drawing sheet is not landscape: {name}"
            )
        pdf = target / relative
        png = target / preview_relative
        pdf.parent.mkdir(parents=True, exist_ok=True)
        script = replay_work / f"drawing-export-{index}.json"
        checkpoint = replay_work / f"drawing-export-{index}.sc"
        script.write_text(
            json.dumps(
                {
                    "commands": [
                        {
                            "command": "drawing.open",
                            "params": {"drawing": variables[variable]},
                        },
                        {
                            "command": "drawing.export",
                            "params": {
                                "format": "pdf",
                                "path": str(pdf.resolve()),
                            },
                        },
                        {
                            "command": "drawing.export",
                            "params": {
                                "sheet": variables[sheet_variable],
                                "format": "png",
                                "path": str(png.resolve()),
                                "dpi": 144,
                            },
                        },
                        {"command": "drawing.close", "params": {}},
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        subprocess.run(
            [
                "solidcraft-cli",
                "run",
                str(script),
                "--in",
                str(native),
                "--save",
                str(checkpoint),
                "--quiet",
            ],
            check=True,
        )
        _require_artifacts((pdf, png))
        if pdf.read_bytes()[:5] != b"%PDF-":
            raise RuntimeError(f"SCPF drawing export is not a PDF: {name}")
        if png.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            raise RuntimeError(
                f"SCPF drawing preview export is not a PNG: {name}"
            )
        produced.extend((pdf, png))
    return tuple(produced)


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
    replay_result = run_document(
        document,
        save=native,
        export=output,
        results_out=results,
        replay_log_out=replay_log,
        work_dir=replay_work,
    )
    _export_drawings(
        document,
        replay_result.get("variables", {}),
        native,
        target,
        replay_work,
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
