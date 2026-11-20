"""Load and validate declarative cheatsheet content."""

from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CHEATSHEET_CONFIG = ROOT / "site" / "content" / "cheatsheet.yml"


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.rstrip()


def load_cheatsheet(path: Path = CHEATSHEET_CONFIG):
    """Return cheatsheet groups in the renderer's tuple shape."""

    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise ValueError("cheatsheet config must use schema 1")
    groups = data.get("groups")
    if not isinstance(groups, list) or not groups:
        raise ValueError("cheatsheet config requires groups")

    result = []
    for group_index, group in enumerate(groups):
        if not isinstance(group, dict):
            raise ValueError(f"groups[{group_index}] must be a mapping")
        heading = _text(group.get("heading"), f"groups[{group_index}].heading")
        items = group.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError(f"{heading}.items must be a non-empty list")

        rendered_items = []
        for item_index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(
                    f"{heading}.items[{item_index}] must be a mapping"
                )
            title = _text(item.get("title"), f"{heading}.items[{item_index}].title")
            description = _text(
                item.get("description"),
                f"{heading}.items[{item_index}].description",
            )
            snippet = _text(
                item.get("snippet"),
                f"{heading}.items[{item_index}].snippet",
            )
            linked = item.get("example")
            if linked is not None and (
                not isinstance(linked, str) or not linked.strip()
            ):
                raise ValueError(
                    f"{heading}.items[{item_index}].example must be text or null"
                )
            rendered_items.append(
                (title, description, snippet, linked.strip() if linked else None)
            )
        result.append((heading, tuple(rendered_items)))

    return tuple(result)
