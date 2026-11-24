"""build123d source-to-STL adapter for its isolated runtime interpreter."""
from pathlib import Path
import os
import runpy
import sys


def build(source: Path, output: Path):
    from build123d import export_stl

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
    export_stl(getattr(model, "part", model), str(output))
    if not output.is_file() or not output.stat().st_size:
        raise RuntimeError("missing or empty STL")
