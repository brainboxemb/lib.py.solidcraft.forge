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
    priority: int
    title: str
    tagline: str
    description: str
    parameters: str
    stages: tuple[str, ...]


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()



SECTION_CONFIG = ROOT / "site" / "content" / "verification-sections.yml"


def load_section_presentation(
    path: Path = SECTION_CONFIG,
) -> dict[str, tuple[int, str, str]]:
    """Load declarative verification section priorities and labels."""

    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise ValueError("verification section config must use schema 1")
    sections = data.get("sections")
    if not isinstance(sections, dict) or not sections:
        raise ValueError("verification section config requires sections")

    result = {}
    priorities = set()
    for slug, row in sections.items():
        if not isinstance(slug, str) or not slug.strip():
            raise ValueError("verification section slug must be text")
        if not isinstance(row, dict):
            raise ValueError(f"{slug}: section config must be a mapping")
        priority = row.get("priority")
        label = row.get("label")
        description = row.get("description")
        if not isinstance(priority, int) or priority < 1:
            raise ValueError(f"{slug}.priority must be a positive integer")
        if priority in priorities:
            raise ValueError(
                f"duplicate verification section priority: {priority}"
            )
        priorities.add(priority)
        result[slug] = (
            priority,
            _text(label, f"{slug}.label"),
            _text(description, f"{slug}.description"),
        )
    return result


def section_presentation(section: str) -> tuple[int, str, str]:
    """Return configured public priority, label and description for one section slug."""

    sections = load_section_presentation()
    try:
        return sections[section]
    except KeyError as exc:
        raise ValueError(f"unknown example section: {section}") from exc


def _positive_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or value < 1:
        raise ValueError(f"{label} must be a positive integer")
    return value


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
    priority = _positive_int(data.get("priority"), f"{slug}.priority")

    allowed = set(_REQUIRED_TEXT) | set(_REQUIRED_LISTS) | {"priority"}
    unexpected = sorted(set(data) - allowed)
    if unexpected:
        raise ValueError(
            f"{slug}.model.yml contains unsupported fields: "
            + ", ".join(unexpected)
        )

    return ExampleMetadata(
        slug=slug,
        priority=priority,
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
