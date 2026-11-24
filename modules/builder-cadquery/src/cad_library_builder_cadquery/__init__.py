"""CadQuery source-to-STL adapter; CAD dependencies live in reference runtime."""
from pathlib import Path
import runpy
import sys
import os


def build(source: Path, output: Path):
    import cadquery

    cwd, original_path = Path.cwd(), list(sys.path)
    try:
        os.chdir(source.parent)
        sys.path.insert(0, str(source.parent))
        namespace = runpy.run_path(str(source), run_name="__cad_library_model__")
    finally:
        os.chdir(cwd)
        sys.path[:] = original_path
    if "model" not in namespace:
        raise ValueError(f"{source} must expose model")
    model = namespace["model"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    if isinstance(model, cadquery.Assembly):
        model.export(str(output), exportType="STL")
    else:
        cadquery.exporters.export(model, str(output))
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("missing or empty STL")
