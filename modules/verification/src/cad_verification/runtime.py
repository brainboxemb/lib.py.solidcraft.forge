"""Runtime-facing verification adapter entrypoint."""
from pathlib import Path


def run(adapter: str, artifact: Path, definition: Path, output: Path, *, verification_id: str):
    if adapter == "mesh-geometry":
        from .geometry import load_geometry_contract, run_mesh_geometry_verification
        return run_mesh_geometry_verification(
            artifact, output, load_geometry_contract(definition), verification_id=verification_id
        )
    raise ValueError(f"unsupported verification adapter: {adapter}")
