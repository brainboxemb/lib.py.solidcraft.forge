"""Experimental SCPF-to-Mitcad native builder."""
from pathlib import Path
import os


def _require_artifact(path: Path):
    if not path.is_file() or not path.stat().st_size:
        raise RuntimeError(f"Mitcad build produced no artifact: {path.name}")


def build(source: Path, output: Path):
    """Compile trusted SCPF source to native Mitcad and STL artifacts.

    The runtime owns the Mitcad executable. This builder never downloads or
    installs a CAD runtime; it expects `mitcad-cli` on PATH unless the runtime
    explicitly supplies CAD_LIBRARY_MITCAD_EXECUTABLE.
    """
    from scpf.runner import run_script
    from scpf.backends.mitcad_headless import run_document, validate_document

    document = run_script(source, backend="mitcad")
    validate_document(document)

    target = output.parent
    target.mkdir(parents=True, exist_ok=True)
    native = target / "model.mitcad"
    executable = os.environ.get(
        "CAD_LIBRARY_MITCAD_EXECUTABLE",
        "mitcad-cli",
    ).strip()
    if not executable:
        raise RuntimeError("CAD_LIBRARY_MITCAD_EXECUTABLE must not be empty")

    run_document(
        document,
        save=native,
        export=output,
        executable=executable,
        work_dir=target / "mitcad-work",
    )
    _require_artifact(native)
    _require_artifact(output)
