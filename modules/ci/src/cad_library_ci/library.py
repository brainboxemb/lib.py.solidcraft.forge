"""Independent library owner using the same source-test mechanism as modules."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from .config import ConfigError, mapping
from .items import PythonModule


def library_owner(repo: Path):
    root = repo / "cadlib"
    config = mapping(root / "ci.yml")
    if config.get("id") != "cadlib" or config.get("kind") != "library":
        raise ConfigError("invalid cadlib owner")
    if not (root / "pyproject.toml").is_file():
        raise ConfigError("cadlib requires pyproject.toml")
    return PythonModule("cadlib", root, "self", ("cadlib/**",))


def build_wheel(library, output: Path):
    """Build a wheel in an isolated source copy; do not install the library."""
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    for old in output.glob("*.whl"):
        old.unlink()
    with tempfile.TemporaryDirectory(prefix="cadlib-package-") as tmp:
        source = Path(tmp) / "cadlib"
        shutil.copytree(library.root, source, ignore=shutil.ignore_patterns("__pycache__", "*.egg-info", "build", "dist", ".venv"))
        subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", str(output), str(source)], check=True)
    if len(list(output.glob("*.whl"))) != 1:
        raise RuntimeError("cadlib qualification must produce exactly one wheel")
