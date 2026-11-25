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
                "inspect", "expected",
            }
        ):
            raise RuntimeError(f"invalid SCPF drawing artifact at index {index}")
        variable = item["drawing"]
        sheet_variable = item["sheet"]
        orientation_variable = item["orientation"]
        relative = Path(item["pdf"])
        preview = Path(item["png"])
        inspect = Path(item["inspect"])
        expected = item["expected"]
        if (
            not isinstance(variable, str)
            or not variable.startswith("$")
            or not isinstance(sheet_variable, str)
            or not sheet_variable.startswith("$")
            or not isinstance(orientation_variable, str)
            or not orientation_variable.startswith("$")
            or relative.is_absolute()
            or preview.is_absolute()
            or inspect.is_absolute()
            or ".." in relative.parts
            or ".." in preview.parts
            or ".." in inspect.parts
            or relative.suffix.lower() != ".pdf"
            or preview.suffix.lower() != ".png"
            or relative.with_suffix(".png") != preview
            or relative.with_suffix(".json") != inspect
            or not isinstance(expected, dict)
            or not relative.parts
            or relative.parts[0] != "drawings"
            or not preview.parts
            or preview.parts[0] != "drawings"
            or not inspect.parts
            or inspect.parts[0] != "drawings"
        ):
            raise RuntimeError(f"invalid SCPF drawing artifact at index {index}")
        keys = (
            relative.as_posix(),
            preview.as_posix(),
            inspect.as_posix(),
        )
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
                inspect,
                expected,
            )
        )
    return result


def _title_block_cells(sheet):
    cells = sheet.get("title_block_cells", [])
    if not isinstance(cells, list):
        return {}
    return {
        row.get("name"): row.get("text")
        for row in cells
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }


def _validate_drawing_inspection(
    name,
    inspection,
    expected,
    *,
    variables,
    view_inspections,
):
    """Validate the saved native drawing against the compiled authoring intent."""
    if not isinstance(inspection, dict):
        raise RuntimeError(f"SCPF drawing inspection is invalid: {name}")
    sheets = inspection.get("sheets", [])
    if not isinstance(sheets, list) or len(sheets) != 1:
        raise RuntimeError(
            f"SCPF drawing must contain exactly one qualified sheet: {name}"
        )
    sheet = sheets[0]
    if sheet.get("orientation") != expected.get("orientation"):
        raise RuntimeError(
            f"SCPF drawing orientation mismatch: {name}"
        )
    views = sheet.get("views", [])
    if not isinstance(views, list) or len(views) != expected.get("view_count"):
        raise RuntimeError(
            f"SCPF drawing view count mismatch: {name}"
        )
    dimension_count = sum(
        len(view.get("dimensions", []))
        for view in views
        if isinstance(view, dict)
        and isinstance(view.get("dimensions", []), list)
    )
    if dimension_count != expected.get("dimension_count"):
        raise RuntimeError(
            f"SCPF drawing dimension count mismatch: {name}"
        )
    notes = sheet.get("notes", [])
    if not isinstance(notes, list) or len(notes) != expected.get("note_count"):
        raise RuntimeError(
            f"SCPF drawing note count mismatch: {name}"
        )

    properties = inspection.get("properties", {})
    for key, value in expected.get("properties", {}).items():
        if properties.get(key) != value:
            raise RuntimeError(
                f"SCPF drawing property {key!r} mismatch: {name}"
            )

    overrides = sheet.get("title_block_overrides", {})
    for key, value in expected.get("title_block", {}).items():
        if overrides.get(key) != value:
            raise RuntimeError(
                f"SCPF drawing title-block {key!r} mismatch: {name}"
            )

    revision = expected.get("revision")
    rows = inspection.get("revisions", {}).get("rows", [])
    if revision is None:
        if rows:
            raise RuntimeError(
                f"SCPF drawing has unexpected revision rows: {name}"
            )
    else:
        if not isinstance(rows, list) or len(rows) != 1:
            raise RuntimeError(
                f"SCPF drawing revision count mismatch: {name}"
            )
        for key, value in revision.items():
            if rows[0].get(key) != value:
                raise RuntimeError(
                    f"SCPF drawing revision {key!r} mismatch: {name}"
                )

        cells = _title_block_cells(sheet)
        derived = {
            "revision": revision.get("revision"),
            "created_by": revision.get("designer"),
            "approved_by": revision.get("checker"),
            "date_of_issue": revision.get("date"),
        }
        for key, value in derived.items():
            if value is not None and cells.get(key) != value:
                raise RuntimeError(
                    f"SCPF drawing rendered title-block {key!r} mismatch: {name}"
                )

    cells = _title_block_cells(sheet)
    for variable, expected_style in expected.get("view_styles", {}).items():
        view_id = variables.get(variable)
        if not isinstance(view_id, str):
            raise RuntimeError(
                f"SCPF drawing styled view variable is unbound: {variable}"
            )
        view = view_inspections.get(view_id)
        if view is None:
            raise RuntimeError(
                f"SCPF drawing produced no native view inspection: {name}: {variable}"
            )
        if view.get("settings", {}).get("visual_style") != expected_style:
            raise RuntimeError(
                f"SCPF drawing view style mismatch: {name}: {variable}"
            )

    property_cells = {
        "part_number": "identification_number",
        "organization": "legal_owner",
    }
    overridden = expected.get("title_block", {})
    for prop, cell in property_cells.items():
        if cell in overridden:
            continue
        value = expected.get("properties", {}).get(prop)
        if value is not None and cells.get(cell) != value:
            raise RuntimeError(
                f"SCPF drawing rendered title-block {cell!r} mismatch: {name}"
            )


def _drawing_view_inspections(replay_results):
    """Return final native drawing.view.inspect results keyed by view id."""
    by_view = {}
    if not isinstance(replay_results, list):
        return by_view
    for result in replay_results:
        if (
            isinstance(result, dict)
            and isinstance(result.get("view"), str)
            and isinstance(result.get("settings"), dict)
        ):
            by_view[result["view"]] = result
    return by_view


def _drawing_inspections(replay_results):
    """Return the last full native inspection for each drawing name."""
    by_name = {}
    if not isinstance(replay_results, list):
        return by_name
    for result in replay_results:
        if (
            isinstance(result, dict)
            and isinstance(result.get("name"), str)
            and isinstance(result.get("sheets"), list)
            and isinstance(result.get("properties"), dict)
        ):
            by_name[result["name"]] = result
    return by_name


def _export_drawings(
    document,
    variables,
    native: Path,
    target: Path,
    replay_work: Path,
    replay_results,
):
    exports = _drawing_exports(document)
    inspections = _drawing_inspections(replay_results)
    view_inspections = _drawing_view_inspections(replay_results)
    produced = []
    for index, (
        name,
        variable,
        sheet_variable,
        orientation_variable,
        relative,
        preview_relative,
        inspect_relative,
        expected,
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
        inspect = target / inspect_relative
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
        inspection = inspections.get(name)
        if inspection is None:
            raise RuntimeError(
                f"SCPF drawing replay produced no final inspection: {name}"
            )
        _validate_drawing_inspection(
            name,
            inspection,
            expected,
            variables=variables,
            view_inspections=view_inspections,
        )
        inspect.write_text(
            json.dumps(inspection, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _require_artifacts((pdf, png, inspect))
        if pdf.read_bytes()[:5] != b"%PDF-":
            raise RuntimeError(f"SCPF drawing export is not a PDF: {name}")
        if png.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            raise RuntimeError(
                f"SCPF drawing preview export is not a PNG: {name}"
            )
        produced.extend((pdf, png, inspect))
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
    replay_results = json.loads(results.read_text(encoding="utf-8"))
    _export_drawings(
        document,
        replay_result.get("variables", {}),
        native,
        target,
        replay_work,
        replay_results,
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
