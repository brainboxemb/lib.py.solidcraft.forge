"""Direct SolidCraft command-document builder."""
from pathlib import Path
import os
import re
import shutil
import subprocess

_VERSION = re.compile(r"(?<!\d)(\d+\.\d+\.\d+)(?!\d)")


def _qualified_version():
    expected = os.environ.get("CAD_LIBRARY_RUNTIME_VERSION", "").strip()
    if not expected:
        raise RuntimeError("CAD_LIBRARY_RUNTIME_VERSION is required")
    result = subprocess.run(["solidcraft-cli", "--version"], check=True, capture_output=True, text=True)
    match = _VERSION.search((result.stdout or "") + " " + (result.stderr or ""))
    if match is None or match.group(1) != expected:
        actual = match.group(1) if match else "unknown"
        raise RuntimeError(f"SolidCraft runtime {actual} differs from expected {expected}")
    return expected


def build(source: Path, output: Path):
    _qualified_version()
    target = output.parent
    target.mkdir(parents=True, exist_ok=True)
    native = target / "model.sc"
    preview = target / "model.png"
    commands = target / "solidcraft.json"
    shutil.copy2(source, commands)
    subprocess.run(["solidcraft-cli", "run", str(source), "--save", str(native), "--quiet"], check=True)
    subprocess.run(["solidcraft-cli", "run", "--in", str(native), "--out", str(output), "--quality", "fine", "--quiet"], check=True)
    subprocess.run(["solidcraft-cli", "snapshot", str(native), "--out", str(preview), "--no-grid", "--no-axes"], check=True)
    for path in (native, output, preview, commands):
        if not path.is_file() or not path.stat().st_size:
            raise RuntimeError(f"SolidCraft produced no artifact: {path.name}")
