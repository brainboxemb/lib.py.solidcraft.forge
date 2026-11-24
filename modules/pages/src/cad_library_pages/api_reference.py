"""Project the SCPF API reference without importing or executing scpf."""

from __future__ import annotations

import ast
import json
from pathlib import Path


def _frontmatter(title: str) -> str:
    return "---\n" + f"title: {json.dumps(title)}\n" + "---\n\n"


def _public_exports(source_root: Path) -> set[str]:
    init = source_root / "cadlib" / "src" / "scpf" / "__init__.py"
    tree = ast.parse(init.read_text(encoding="utf-8"), filename=str(init))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets):
            continue
        return {str(item) for item in ast.literal_eval(node.value)}
    raise ValueError("cadlib/src/scpf/__init__.py has no literal __all__")


def _source_symbols(source_root: Path) -> tuple[set[str], dict[str, set[str]]]:
    names: set[str] = set()
    methods: dict[str, set[str]] = {}
    package = source_root / "cadlib" / "src" / "scpf"
    for path in sorted(package.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
            elif isinstance(node, ast.ClassDef):
                names.add(node.name)
                methods.setdefault(node.name, set()).update(
                    child.name
                    for child in node.body
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                )
    return names, methods


def _manifest_targets(manifest: dict) -> set[str]:
    targets: set[str] = set()
    for row in manifest["references"]:
        if row["kind"] == "group":
            targets.update(member["name"] for member in row.get("members", []))
        elif "." not in row["name"]:
            targets.add(row["name"])
        targets.update(row.get("aliases", []))
    return targets


def _validate_manifest(source_root: Path, manifest: dict) -> None:
    exports = _public_exports(source_root)
    names, methods = _source_symbols(source_root)
    targets = _manifest_targets(manifest)
    missing_exports = sorted(exports - targets)
    if missing_exports:
        raise ValueError("API reference misses public exports: " + ", ".join(missing_exports))

    for row in manifest["references"]:
        name = row["name"]
        if row["kind"] == "group":
            continue
        if "." in name:
            owner, member = name.split(".", 1)
            if owner not in methods or member not in methods[owner]:
                raise ValueError(f"API reference target missing from source: {name}")
        elif name not in exports and name not in names:
            raise ValueError(f"API reference target missing from source: {name}")


def _render_reference(row: dict) -> str:
    lines = [_frontmatter(row["name"]), row.get("summary", "").strip(), ""]
    guide = row.get("guide")
    if guide:
        lines += [f"[Related guide](../../{guide})", ""]

    if row["kind"] == "group":
        lines += ["## Members", ""]
        for member in row.get("members", []):
            lines.append(f"### {member['name']}")
            if member.get("summary"):
                lines.append(member["summary"])
            if member.get("signature"):
                lines += ["", "```python", member["signature"], "```"]
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    signature = row.get("signature")
    if signature:
        lines += ["## Signature", "", "```python", signature, "```", ""]
    if row.get("use_when"):
        lines += ["## Use when", "", row["use_when"], ""]
    if row.get("limits"):
        lines += ["## Limits", "", row["limits"], ""]
    if row.get("parameters"):
        lines += ["## Parameters", ""]
        for parameter in row["parameters"]:
            lines.append(f"- `{parameter['name']}` — {parameter['description']}")
        lines.append("")
    if row.get("members"):
        lines += ["## Members", ""]
        for member in row["members"]:
            lines.append(f"- `{member['name']}` = `{member['value']}`")
        lines.append("")
    if row.get("aliases"):
        lines += ["## Aliases", "", ", ".join(f"`{name}`" for name in row["aliases"]), ""]
    if row.get("example"):
        lines += ["## Example", "", "```python", row["example"], "```", ""]
    return "\n".join(lines).rstrip() + "\n"


def _prepare_api_design_contract(source_root: Path, site: Path) -> None:
    source = source_root / "docs" / "api.md"
    if not source.is_file():
        return
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = "Forge API"
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip() or title
        text = "\n".join(lines[1:]).lstrip("\n")
    target = site / "content" / "api-design-contract.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "---\n"
        f"title: {json.dumps(title)}\n"
        "url: /api-design-contract.html\n"
        "---\n\n"
        + text.rstrip() + "\n",
        encoding="utf-8",
    )


def prepare_api_reference(source_root: Path, site: Path) -> None:
    _prepare_api_design_contract(source_root, site)
    manifest_path = source_root / "docs" / "api-reference.json"
    if not manifest_path.is_file():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    _validate_manifest(source_root, manifest)

    root = site / "content" / "reference"
    root.mkdir(parents=True, exist_ok=True)
    (root / "_index.md").write_text(
        _frontmatter("SCPF API Reference")
        + "Reference for the public SCPF Python surface.\n\n"
        + "The descriptive contract is retained from the accepted historical Forge reference. "
        + "NEW validates every referenced public symbol statically against `cadlib/src/scpf` during the Pages build.\n",
        encoding="utf-8",
    )
    for row in manifest["references"]:
        target = root / row["name"] / "index.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_render_reference(row), encoding="utf-8")

    static = site / "static" / "reference"
    static.mkdir(parents=True, exist_ok=True)
    (static / "api.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
