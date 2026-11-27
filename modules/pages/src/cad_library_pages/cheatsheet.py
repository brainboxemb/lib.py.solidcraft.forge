"""Project the source-owned SCPF cheatsheet into Hugo."""

from pathlib import Path
import yaml


def _model_link(source_root: Path, model_id: str) -> str | None:
    meta_path = source_root / "models" / model_id / "model.yml"
    if not meta_path.is_file():
        return None
    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
    purposes = meta.get("purpose", [])
    if isinstance(purposes, str):
        purposes = [purposes]
    if "example" in purposes:
        return f"../examples/{model_id}/"
    if "verification" in purposes:
        return f"../verification/{model_id}/"
    return None


def prepare_cheatsheet(source_root: Path, site: Path) -> None:
    source = source_root / "site" / "source" / "cheatsheet.yml"
    if not source.is_file():
        return

    data = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    if data.get("schema") != 1 or not isinstance(data.get("groups"), list):
        raise ValueError(f"invalid cheatsheet source: {source}")

    lines = [
        "---",
        "title: Cheatsheet",
        "---",
        "",
        "Quick lookup for the public SCPF authoring API.",
        "",
    ]
    for group in data["groups"]:
        heading = group.get("heading")
        items = group.get("items")
        if not isinstance(heading, str) or not isinstance(items, list):
            raise ValueError("invalid cheatsheet group")
        lines += [f"## {heading}", ""]
        for item in items:
            title = item.get("title")
            description = item.get("description", "")
            snippet = item.get("snippet", "")
            if not isinstance(title, str):
                raise ValueError("invalid cheatsheet item")
            lines += [f"### {title}", "", str(description).strip(), ""]
            if snippet:
                lines += ["~~~python", str(snippet).rstrip(), "~~~", ""]
            model_id = item.get("example")
            if isinstance(model_id, str) and model_id:
                link = _model_link(source_root, model_id)
                if link:
                    lines += [f"[Related model]({link})", ""]

    target = site / "content" / "cheatsheet" / "_index.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
