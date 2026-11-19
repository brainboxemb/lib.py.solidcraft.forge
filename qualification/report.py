#!/usr/bin/env python3
"""Render a compact Markdown report from semantic qualification results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _status(check: dict) -> str:
    return str(check.get("status", "missing")).upper()


def render(data: dict) -> str:
    """Return one human-readable report without historical numbered levels."""

    lines = [
        "# Forge qualification report",
        "",
        "| Case | Integration | Native model | Geometry | Saved design | Visual | Overall |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for slug, case in data.get("cases", {}).items():
        checks = case.get("checks", {})
        lines.append(
            "| "
            + " | ".join(
                (
                    slug,
                    _status(checks.get("integration", {})),
                    _status(checks.get("native_model", {})),
                    _status(checks.get("geometry", {})),
                    _status(checks.get("saved_design", {})),
                    _status(checks.get("visual", {})),
                    str(case.get("status", "missing")).upper(),
                )
            )
            + " |"
        )

    lines.extend(("", "## Visual evidence", ""))
    for slug, case in data.get("cases", {}).items():
        images = case.get("checks", {}).get("visual", {}).get("images", [])
        if images:
            lines.append(f"- **{slug}:** " + ", ".join(images))
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.results.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(data), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
