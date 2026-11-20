"""Execute build123d reference models and export their final geometry."""

from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path
import traceback

from build123d import export_stl


def export_one(source: Path, target: Path) -> None:
    """Execute one source and export its final model to STL."""

    namespace = runpy.run_path(str(source))
    if "model" not in namespace:
        raise RuntimeError(f"{source} must expose final geometry as model")
    target.parent.mkdir(parents=True, exist_ok=True)
    model = namespace["model"]
    geometry = getattr(model, "part", model)
    export_stl(geometry, str(target))
    if not target.is_file() or target.stat().st_size == 0:
        raise RuntimeError(
            f"build123d did not export a non-empty STL: {target}"
        )


def run_batch(manifest_path: Path, result_path: Path) -> int:
    """Export every manifest row after importing build123d only once."""

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = manifest.get("cases")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError("build123d batch manifest has no cases")

    results = []
    failed = False
    for row in rows:
        slug = row["slug"]
        source = Path(row["source"])
        target = Path(row["target"])
        try:
            export_one(source, target)
            status = "pass"
            error = None
        except Exception as exc:  # continue so every case gets a result
            failed = True
            status = "error"
            error = "".join(
                traceback.format_exception_only(type(exc), exc)
            ).strip()
        results.append(
            {
                "slug": slug,
                "status": status,
                "error": error,
            }
        )

    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(
        json.dumps(
            {
                "schema": 1,
                "status": "fail" if failed else "pass",
                "cases": results,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path)
    parser.add_argument("target", nargs="?", type=Path)
    parser.add_argument("--batch", type=Path)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()

    if args.batch is not None:
        if args.result is None:
            parser.error("--batch requires --result")
        if args.source is not None or args.target is not None:
            parser.error("--batch does not accept source/target")
        return run_batch(args.batch, args.result)

    if args.source is None or args.target is None:
        parser.error("source and target are required")
    if args.result is not None:
        parser.error("--result requires --batch")

    export_one(args.source, args.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
