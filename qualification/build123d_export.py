"""Execute one build123d reference model and export its final geometry."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

from build123d import export_stl


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: build123d_export.py SOURCE.py TARGET.stl")
    source = Path(sys.argv[1])
    target = Path(sys.argv[2])
    namespace = runpy.run_path(str(source))
    if "model" not in namespace:
        raise RuntimeError(f"{source} must expose final geometry as model")
    target.parent.mkdir(parents=True, exist_ok=True)
    export_stl(namespace["model"], str(target))
    if not target.is_file() or target.stat().st_size == 0:
        raise RuntimeError(f"build123d did not export a non-empty STL: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
