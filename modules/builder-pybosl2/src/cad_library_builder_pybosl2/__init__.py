"""pyBOSL2 uses the PythonSCAD export contract."""
from pathlib import Path


def build(source: Path, output: Path):
    from cad_library_builder_pythonscad import build as export_model
    return export_model(source, output)
