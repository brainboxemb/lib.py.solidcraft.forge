"""Canonical human-facing model metadata shared by Forge and CAD consumers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


MODEL_PURPOSES = ("example", "verification")

MODEL_METADATA_FIELDS = (
    "purpose",
    "section",
    "priority",
    "title",
    "tagline",
    "description",
    "parameters",
    "stages",
)


@dataclass(frozen=True)
class ModelMetadata:
    """Validated canonical model.yml values, independent of the YAML loader."""

    purpose: tuple[str, ...]
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


def _purpose(value: Any, label: str) -> tuple[str, ...]:
    values = [value] if isinstance(value, str) else value
    if not isinstance(values, list) or not values:
        raise ValueError(
            f"{label} must be 'example', 'verification', or a non-empty list"
        )
    normalized = tuple(
        _text(item, f"{label}[{index}]")
        for index, item in enumerate(values)
    )
    unknown = sorted(set(normalized) - set(MODEL_PURPOSES))
    if unknown:
        raise ValueError(
            f"{label} contains unsupported values: " + ", ".join(unknown)
        )
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{label} must not contain duplicate values")
    return tuple(item for item in MODEL_PURPOSES if item in normalized)


def _positive_int(value: Any, label: str) -> int:
    if type(value) is not int or value < 1:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _text_list(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    return tuple(
        _text(item, f"{label}[{index}]")
        for index, item in enumerate(value)
    )


def validate_model_metadata(
    data: Mapping[str, Any],
    *,
    label: str = "model.yml",
) -> ModelMetadata:
    """Validate one already-parsed canonical model.yml mapping.

    YAML parsing deliberately belongs to the caller. The canonical contract is
    exact and rejects consumer-specific extension fields.
    """

    if not isinstance(data, Mapping):
        raise ValueError(f"{label} must contain one mapping")

    unexpected = sorted(set(data) - set(MODEL_METADATA_FIELDS))
    if unexpected:
        raise ValueError(
            f"{label} contains unsupported fields: " + ", ".join(unexpected)
        )

    missing = [field for field in MODEL_METADATA_FIELDS if field not in data]
    if missing:
        raise ValueError(
            f"{label} is missing required fields: " + ", ".join(missing)
        )

    return ModelMetadata(
        purpose=_purpose(data["purpose"], f"{label}.purpose"),
        section=_text(data["section"], f"{label}.section"),
        priority=_positive_int(data["priority"], f"{label}.priority"),
        title=_text(data["title"], f"{label}.title"),
        tagline=_text(data["tagline"], f"{label}.tagline"),
        description=_text(data["description"], f"{label}.description"),
        parameters=_text(data["parameters"], f"{label}.parameters"),
        stages=_text_list(data["stages"], f"{label}.stages"),
    )
