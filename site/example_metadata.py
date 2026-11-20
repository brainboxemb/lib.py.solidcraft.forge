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
_REQUIRED_LISTS = ("stages", "concepts")


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
    concepts: tuple[str, ...]
    verification_summary: str
    verification_proves: tuple[str, ...]
    verification_saved_design: str | None = None
    notes: tuple[str, ...] = ()


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

    verification = data.get("verification")
    if not isinstance(verification, dict):
        raise ValueError(f"{slug}.verification must be a mapping")
    summary = _text(
        verification.get("summary"),
        f"{slug}.verification.summary",
    )
    proves = _text_list(
        verification.get("proves"),
        f"{slug}.verification.proves",
    )
    saved_design = verification.get("saved_design")
    if saved_design is not None:
        saved_design = _text(
            saved_design,
            f"{slug}.verification.saved_design",
        )

    notes_value = data.get("notes", [])
    if notes_value is None:
        notes_value = []
    if not isinstance(notes_value, list):
        raise ValueError(f"{slug}.notes must be a list when present")
    notes = tuple(
        _text(item, f"{slug}.notes[{index}]")
        for index, item in enumerate(notes_value)
    )

    return ExampleMetadata(
        slug=slug,
        **values,
        **lists,
        verification_summary=summary,
        verification_proves=proves,
        verification_saved_design=saved_design,
        notes=notes,
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
