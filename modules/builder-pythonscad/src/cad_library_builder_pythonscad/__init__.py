"""Shared source-to-STL adapter for the PythonSCAD model.export contract."""
import os
from pathlib import Path
import runpy
import sys


def build(source: Path, output: Path):
    cwd, original_path = Path.cwd(), list(sys.path)
    try:
        os.chdir(source.parent)
        sys.path.insert(0, str(source.parent))
        namespace = runpy.run_path(str(source), run_name="__cad_library_model__")
    finally:
        os.chdir(cwd)
        sys.path[:] = original_path
    model = namespace.get("model")
    export = getattr(model, "export", None)
    if not callable(export):
        raise ValueError(f"{source} must expose model with export()")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)
    exported = export(str(output))
    if not output.is_file() and isinstance(exported, (str, os.PathLike)):
        candidate = Path(exported)
        if candidate.is_file():
            output.write_bytes(candidate.read_bytes())
    if not output.is_file() or not output.stat().st_size:
        raise RuntimeError("missing or empty STL")
