"""Project source-owned documentation into the Hugo site."""

from pathlib import Path
import json
import re
import shutil


_MD_LINK = re.compile(r"\(([^()\s]+)\.md(#[^)]+)?\)")


def _title_and_body(text: str, fallback: str) -> tuple[str, str]:
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
        body = "\n".join(lines[1:]).lstrip("\n")
        return title or fallback, body
    return fallback, text


def _rewrite_markdown_links(text: str) -> str:
    def replace(match):
        path = match.group(1)
        fragment = match.group(2) or ""
        if path.endswith("/README"):
            path = path[:-len("README")]
        elif path == "README":
            path = "./"
        elif path.endswith("/SOURCE"):
            path = path[:-len("SOURCE")]
        elif path == "SOURCE":
            path = "./"
        else:
            path += "/"
        return f"({path}{fragment})"
    return _MD_LINK.sub(replace, text)


def _target_markdown(site: Path, relative: Path) -> Path:
    parent = site / "content" / "docs" / "reference" / relative.parent
    if relative.name == "README.md":
        return parent / "_index.md"
    if relative.name == "SOURCE.md":
        return parent / "_index.md"
    return parent / relative.stem / "index.md"


def prepare_documentation(source_root: Path, site: Path) -> None:
    """Publish retained external references without making Pages their owner."""

    reference = source_root / "docs" / "reference"
    if not reference.is_dir():
        return

    for source in sorted(reference.rglob("*")):
        if not source.is_file():
            continue
        relative = source.relative_to(reference)
        if source.suffix == ".md":
            text = source.read_text(encoding="utf-8")
            title, body = _title_and_body(text, source.stem.replace("-", " ").title())
            target = _target_markdown(site, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                "---\n"
                f"title: {json.dumps(title)}\n"
                "---\n\n"
                + _rewrite_markdown_links(body).rstrip()
                + "\n",
                encoding="utf-8",
            )
        elif source.suffix == ".json":
            target = site / "static" / "docs" / "reference" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
