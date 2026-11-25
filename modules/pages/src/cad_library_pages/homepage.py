"""Generate and validate the Hugo homepage manifest from repository source metadata."""

from __future__ import annotations

import json
from pathlib import Path
import re
from string import Template

import yaml


_ROUTE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*")
_SECTION = re.compile(r"[a-z0-9][a-z0-9_-]*")
_BLOCK_TYPES = {"hero", "flow", "links", "catalogue"}


def _text(value, *, where: str, context: dict[str, str]) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where} must be a non-empty string")
    try:
        return Template(value.strip()).substitute(context)
    except KeyError as exc:
        raise ValueError(f"{where} references unknown generated value: {exc.args[0]}") from exc


def _destination(value, *, where: str, context: dict[str, str]) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{where} must be a mapping")
    label = _text(value.get("label"), where=f"{where}.label", context=context)
    route = value.get("route")
    url = value.get("url")
    if (route is None) == (url is None):
        raise ValueError(f"{where} must declare exactly one of route or url")
    result = {"label": label, "primary": bool(value.get("primary", False))}
    if route is not None:
        route = _text(route, where=f"{where}.route", context=context)
        if route.startswith("/") or "://" in route or ".." in route.split("/") or not _ROUTE.fullmatch(route):
            raise ValueError(f"{where}.route must be a safe base-relative Hugo route")
        result.update(route=route, external=False)
    else:
        url = _text(url, where=f"{where}.url", context=context)
        if not re.fullmatch(r"https://[^\s]+", url):
            raise ValueError(f"{where}.url must be an absolute https URL")
        result.update(url=url, external=True)
    return result


def _block(value, *, index: int, context: dict[str, str]) -> dict:
    where = f"blocks[{index}]"
    if not isinstance(value, dict):
        raise ValueError(f"{where} must be a mapping")
    block_type = _text(value.get("type"), where=f"{where}.type", context=context)
    if block_type not in _BLOCK_TYPES:
        raise ValueError(f"{where}.type is not supported: {block_type}")

    if block_type == "hero":
        result = {
            "type": block_type,
            "eyebrow": _text(value.get("eyebrow"), where=f"{where}.eyebrow", context=context),
            "title": _text(value.get("title"), where=f"{where}.title", context=context),
            "lead": _text(value.get("lead"), where=f"{where}.lead", context=context),
            "badges": [],
            "actions": [],
        }
        badges = value.get("badges", [])
        if not isinstance(badges, list):
            raise ValueError(f"{where}.badges must be a list")
        result["badges"] = [
            _text(item, where=f"{where}.badges[{i}]", context=context)
            for i, item in enumerate(badges)
        ]
        actions = value.get("actions", [])
        if not isinstance(actions, list):
            raise ValueError(f"{where}.actions must be a list")
        result["actions"] = [
            _destination(item, where=f"{where}.actions[{i}]", context=context)
            for i, item in enumerate(actions)
        ]
        return result

    title = _text(value.get("title"), where=f"{where}.title", context=context)
    description = _text(
        value.get("description"), where=f"{where}.description", context=context
    )

    if block_type == "flow":
        steps = value.get("steps")
        if not isinstance(steps, list) or len(steps) < 2:
            raise ValueError(f"{where}.steps must contain at least two steps")
        normalized = []
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                raise ValueError(f"{where}.steps[{i}] must be a mapping")
            normalized.append({
                "title": _text(
                    step.get("title"),
                    where=f"{where}.steps[{i}].title",
                    context=context,
                ),
                "description": _text(
                    step.get("description"),
                    where=f"{where}.steps[{i}].description",
                    context=context,
                ),
            })
        return {
            "type": block_type,
            "title": title,
            "description": description,
            "steps": normalized,
        }

    if block_type == "links":
        items = value.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError(f"{where}.items must contain at least one destination")
        normalized = []
        for i, item in enumerate(items):
            destination = _destination(
                item, where=f"{where}.items[{i}]", context=context
            )
            destination["description"] = _text(
                item.get("description"),
                where=f"{where}.items[{i}].description",
                context=context,
            )
            kicker = item.get("kicker")
            if kicker is not None:
                destination["kicker"] = _text(
                    kicker, where=f"{where}.items[{i}].kicker", context=context
                )
            normalized.append(destination)
        return {
            "type": block_type,
            "title": title,
            "description": description,
            "items": normalized,
        }

    section = _text(value.get("section"), where=f"{where}.section", context=context)
    if not _SECTION.fullmatch(section):
        raise ValueError(f"{where}.section must be a simple Hugo section id")
    return {
        "type": block_type,
        "title": title,
        "description": description,
        "section": section,
    }


def homepage_manifest(
    source_root: Path, *, context: dict[str, str] | None = None
) -> dict:
    source = source_root.resolve() / "site/home.yml"
    raw = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    if raw.get("schema") != 1:
        raise ValueError(f"unsupported homepage schema: {source}")
    blocks = raw.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        raise ValueError(f"homepage must declare at least one block: {source}")
    values = context or {}
    return {
        "schema": 1,
        "blocks": [
            _block(block, index=i, context=values)
            for i, block in enumerate(blocks)
        ],
    }


def prepare_homepage(
    source_root: Path,
    site: Path,
    *,
    context: dict[str, str] | None = None,
) -> None:
    data = site / "data"
    data.mkdir(parents=True, exist_ok=True)
    (data / "home.json").write_text(
        json.dumps(
            homepage_manifest(source_root, context=context),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
