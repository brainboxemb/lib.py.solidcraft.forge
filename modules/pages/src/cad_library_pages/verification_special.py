"""Project special Verification routes from source declarations and durable evidence."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import re
import shutil

import yaml

from .guides import html_to_markdown


_RANK = {"Unit": 1, "Integration": 2, "Native": 3, "Geometry": 4, "Saved design": 5, "Visual": 6}


def _literal_assignment(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                return ast.literal_eval(node.value)
    raise ValueError(f"{path} has no literal assignment {name}")


def _purposes(meta: dict) -> list[str]:
    raw = meta.get("purpose", [])
    return [raw] if isinstance(raw, str) else list(raw)


def _verification_owners(source_root: Path) -> dict[str, dict]:
    owners = {}
    for model_yml in sorted((source_root / "models").glob("*/model.yml")):
        meta = yaml.safe_load(model_yml.read_text(encoding="utf-8")) or {}
        if "verification" not in _purposes(meta):
            continue
        owner = model_yml.parent.name
        owners[owner] = meta
    return owners


def _evidence(build_scope: Path | None, owner: str) -> dict | None:
    if build_scope is None:
        return None
    root = build_scope / "models" / owner
    result_path = root / "result.json"
    source_path = root / "source.json"
    if not result_path.is_file():
        return None
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("id") != owner:
        raise ValueError(f"durable result id mismatch: {owner}")
    result["_source_sha"] = (
        json.loads(source_path.read_text(encoding="utf-8")).get("source_sha")
        if source_path.is_file() else None
    )
    return result


def _case_links(cases: list[str]) -> str:
    if not cases:
        return "—"
    return ", ".join(f"[`{slug}`](../{slug}/)" for slug in cases)


def _coverage_page(source_root: Path, build_scope: Path | None) -> str:
    declaration = source_root / "docs" / "verification" / "api-coverage.py"
    exports = _literal_assignment(declaration, "EXPORT_COVERAGE")
    capabilities = _literal_assignment(declaration, "CAPABILITY_COVERAGE")
    owners = _verification_owners(source_root)

    referenced = set()
    for _name, (_target, _current, cases, _note) in exports.items():
        referenced.update(cases)
    for _group, _capability, _target, _current, cases, _note in capabilities:
        referenced.update(cases)
    unknown = sorted(referenced - set(owners))
    if unknown:
        raise ValueError("verification coverage references unknown owners: " + ", ".join(unknown))

    lines = [
        "---",
        "title: Verification coverage",
        "---",
        "",
        "This page projects the source-owned SCPF coverage declarations onto the current Verification owner graph.",
        "Linked owner status comes from the current durable build scope when one is available.",
        "",
        "## Public Python API exports",
        "",
        "| API | Target | Declared current | Current owner evidence | Cases | Notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for name, (target, current, cases, note) in exports.items():
        evidence = []
        for slug in cases:
            result = _evidence(build_scope, slug)
            evidence.append("pass" if result and result.get("status") == "pass" else "not available")
        evidence_text = ", ".join(evidence) if evidence else "source-level"
        lines.append(f"| `{name}` | {target} | {current} | {evidence_text} | {_case_links(cases)} | {note} |")

    lines += [
        "",
        "## Capability coverage",
        "",
        "| Area | Capability | Target | Declared current | Current owner evidence | Cases | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for group, capability, target, current, cases, note in capabilities:
        evidence = []
        for slug in cases:
            result = _evidence(build_scope, slug)
            evidence.append("pass" if result and result.get("status") == "pass" else "not available")
        evidence_text = ", ".join(evidence) if evidence else "source-level"
        lines.append(f"| {group} | `{capability}` | {target} | {current} | {evidence_text} | {_case_links(cases)} | {note} |")
    return "\n".join(lines).rstrip() + "\n"


def _results_page(source_root: Path, build_scope: Path | None) -> str:
    owners = _verification_owners(source_root)
    lines = [
        "---",
        "title: Verification results",
        "---",
        "",
        "One current row per Verification owner. Status and counts are read from durable build evidence; Pages does not execute CAD.",
        "",
        "| Owner | Status | Source | Primary | Implementations | Passing verification stages |",
        "| --- | --- | --- | --- | ---: | ---: |",
    ]
    for owner in sorted(owners):
        result = _evidence(build_scope, owner)
        if result is None:
            lines.append(f"| [`{owner}`](../{owner}/) | not available | — | — | — | — |")
            continue
        implementations = result.get("implementations", {})
        stages = 0
        for state in implementations.values():
            for stage in (state.get("verification_stages") or {}).values():
                if isinstance(stage, dict) and stage.get("status") == "pass":
                    stages += 1
        source = result.get("_source_sha") or "—"
        source = source[:12] if source != "—" else source
        lines.append(
            f"| [`{owner}`](../{owner}/) | {result.get('status', 'unknown')} | `{source}` | "
            f"`{result.get('primary', '—')}` | {len(implementations)} | {stages} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _joint_anatomy_page(source_root: Path, site: Path) -> None:
    source = source_root / "docs" / "verification" / "joint-anatomy"
    body_path = source / "body.html"
    if not body_path.is_file():
        return
    html = body_path.read_text(encoding="utf-8")
    panel = html.find('<section class="panel">')
    if panel >= 0:
        html = html[panel:]
    html = html.replace("$solidcraft_version", "0.48.1")
    html = html.replace("$source_sha", "current source")
    html = html.replace("$diagram_raw_base/", "")
    html = html.replace("$diagram_blob_base/", "")
    target = site / "content" / "verification" / "joint-anatomy" / "index.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "---\ntitle: Joint anatomy\n---\n\n"
        + html_to_markdown(html),
        encoding="utf-8",
    )

    static = site / "static" / "verification" / "joint-anatomy"
    static.mkdir(parents=True, exist_ok=True)
    for asset in sorted(source.iterdir()):
        if asset.is_file() and asset.name != "body.html":
            shutil.copyfile(asset, static / asset.name)


def prepare_verification_special(source_root: Path, site: Path, build_scope: Path | None) -> None:
    _joint_anatomy_page(source_root, site)
    verification = site / "content" / "verification"

    declaration = source_root / "docs" / "verification" / "api-coverage.py"
    if declaration.is_file():
        (verification / "coverage").mkdir(parents=True, exist_ok=True)
        (verification / "coverage" / "index.md").write_text(
            _coverage_page(source_root, build_scope), encoding="utf-8"
        )

    if (source_root / "models").is_dir():
        (verification / "results").mkdir(parents=True, exist_ok=True)
        (verification / "results" / "index.md").write_text(
            _results_page(source_root, build_scope), encoding="utf-8"
        )
