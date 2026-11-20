"""Load and validate example-owned presentation metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = ROOT / "examples"

_REQUIRED_TEXT = (
    "section",
    "title",
    "tagline",
    "description",
    "parameters",
)
_REQUIRED_LISTS = ("stages",)


@dataclass(frozen=True)
class ExampleMetadata:
    """Validated human-facing metadata for one Forge example."""

    slug: str
    section: str
    title: str
    tagline: str
    description: str
    parameters: str
    stages: tuple[str, ...]


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _text_list(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    return tuple(
        _text(item, f"{label}[{index}]")
        for index, item in enumerate(value)
    )


def load_example_metadata(path: Path) -> ExampleMetadata:
    """Load one example model.yml presentation contract."""

    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: model.yml must contain one mapping")

    slug = path.parent.name
    values = {
        key: _text(data.get(key), f"{slug}.{key}")
        for key in _REQUIRED_TEXT
    }
    lists = {
        key: _text_list(data.get(key), f"{slug}.{key}")
        for key in _REQUIRED_LISTS
    }


    allowed = set(_REQUIRED_TEXT) | set(_REQUIRED_LISTS)
    unexpected = sorted(set(data) - allowed)
    if unexpected:
        raise ValueError(
            f"{slug}.model.yml contains unsupported fields: "
            + ", ".join(unexpected)
        )

    return ExampleMetadata(
        slug=slug,
        **values,
        **lists,
    )


def discover_example_metadata(
    root: Path = EXAMPLES_ROOT,
) -> tuple[ExampleMetadata, ...]:
    """Discover examples from local model.yml files, with no central registry."""

    rows = [
        load_example_metadata(path)
        for path in sorted(Path(root).glob("*/model.yml"))
    ]
    if not rows:
        raise ValueError(f"no example model.yml files found below {root}")

    slugs = [row.slug for row in rows]
    if len(slugs) != len(set(slugs)):
        raise ValueError("duplicate example slugs discovered")
    return tuple(rows)
