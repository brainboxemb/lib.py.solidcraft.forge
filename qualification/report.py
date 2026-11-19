#!/usr/bin/env python3
"""Render the semantic Forge qualification report from one external template."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from string import Template


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "qualification" / "templates" / "report.md"


def _status(check: dict) -> str:
    """Return a compact uppercase check status."""

    return str(check.get("status", "missing")).upper()


def render(data: dict) -> str:
    """Render one human-readable report from semantic case checks."""

    rows = []
    images = []
    for slug, case in data.get("cases", {}).items():
        checks = case.get("checks", {})
        rows.append(
            "| "
            + " | ".join(
                (
                    slug,
                    str(case.get("status", "missing")).upper(),
                    _status(checks.get("tool_verify", {})),
                    _status(checks.get("model_verify", {})),
                    _status(checks.get("geometry", {})),
                    _status(checks.get("saved_design", {})),
                    _status(checks.get("visual", {})),
                )
            )
            + " |"
        )
        visual_images = checks.get("visual", {}).get("images", [])
        if visual_images:
            images.append(
                f"### {slug}\n\n"
                + "\n".join(
                    f"- [{name}](../model_verify/{slug}/{name})"
                    for name in visual_images
                )
            )

    template = Template(TEMPLATE.read_text(encoding="utf-8"))
    return template.substitute(
        forge_version=data.get("forge_version", ""),
        solidcraft_version=data.get("solidcraft_version", ""),
        source_commit=data.get("source_commit", ""),
        qualified_at=data.get("qualified_at", ""),
        schema_version=data.get("schema_version", ""),
        case_rows="\n".join(rows),
        image_sections="\n\n".join(images) or "No visual evidence.",
    )


def main() -> int:
    """Render a results JSON file to Markdown."""

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
