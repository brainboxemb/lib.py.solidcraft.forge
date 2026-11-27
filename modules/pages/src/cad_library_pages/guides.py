"""Project authored Guide chapters into Hugo."""

from html.parser import HTMLParser
from pathlib import Path
import json
import re


class _GuideMarkdown(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.in_pre = False
        self.list_stack = []
        self.link_stack = []
        self.table_rows = None
        self.table_row = None
        self.table_cell = None

    def _append(self, value):
        if self.table_cell is not None:
            self.table_cell.append(value)
        else:
            self.out.append(value)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table":
            self.table_rows = []
        elif tag == "tr" and self.table_rows is not None:
            self.table_row = []
        elif tag in {"th", "td"} and self.table_row is not None:
            self.table_cell = []
        elif tag == "h2":
            self._append("\n## ")
        elif tag == "h3":
            self._append("\n### ")
        elif tag == "p":
            pass
        elif tag == "br":
            self._append("\n")
        elif tag == "pre":
            self.in_pre = True
            self._append("\n~~~python\n")
        elif tag == "code":
            if not self.in_pre:
                self._append("`")
        elif tag == "strong":
            self._append("**")
        elif tag == "em":
            self._append("*")
        elif tag == "a":
            href = attrs.get("href", "")
            self.link_stack.append(href)
            self._append("[")
        elif tag == "img":
            src = attrs.get("src", "")
            alt = attrs.get("alt", "")
            self._append(f"![{alt}]({src})")
        elif tag in {"ol", "ul"}:
            self.list_stack.append(tag)
        elif tag == "li":
            kind = self.list_stack[-1] if self.list_stack else "ul"
            prefix = "1. " if kind == "ol" else "- "
            self._append("  " * max(0, len(self.list_stack) - 1) + prefix)
        elif tag in {"figure", "figcaption"}:
            self._append("\n\n")

    def handle_endtag(self, tag):
        if tag in {"th", "td"} and self.table_cell is not None:
            cell = "".join(self.table_cell)
            cell = re.sub(r"\s+", " ", cell).strip().replace("|", "\\|")
            self.table_row.append(cell)
            self.table_cell = None
        elif tag == "tr" and self.table_row is not None:
            if self.table_row:
                self.table_rows.append(self.table_row)
            self.table_row = None
        elif tag == "table" and self.table_rows is not None:
            rows = self.table_rows
            self.table_rows = None
            if rows:
                width = max(len(row) for row in rows)
                rows = [row + [""] * (width - len(row)) for row in rows]
                self.out.append("\n| " + " | ".join(rows[0]) + " |\n")
                self.out.append("| " + " | ".join(["---"] * width) + " |\n")
                for row in rows[1:]:
                    self.out.append("| " + " | ".join(row) + " |\n")
                self.out.append("\n")
        elif tag in {"h2", "h3"}:
            self._append("\n")
        elif tag == "p":
            self._append("\n\n")
        elif tag == "pre":
            self._append("\n~~~\n\n")
            self.in_pre = False
        elif tag == "code":
            if not self.in_pre:
                self._append("`")
        elif tag == "strong":
            self._append("**")
        elif tag == "em":
            self._append("*")
        elif tag == "a":
            href = self.link_stack.pop() if self.link_stack else ""
            self._append(f"]({href})")
        elif tag in {"ol", "ul"}:
            if self.list_stack:
                self.list_stack.pop()
            self._append("\n")
        elif tag == "li":
            self._append("\n")
        elif tag in {"div", "section", "figure", "figcaption"}:
            self._append("\n")

    def handle_data(self, data):
        if self.in_pre:
            self._append(data)
            return
        if not data or data.isspace():
            return
        self._append(re.sub(r"\s+", " ", data))

    def markdown(self):
        text = "".join(self.out)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"


def html_to_markdown(text: str) -> str:
    parser = _GuideMarkdown()
    parser.feed(text)
    parser.close()
    return parser.markdown()


def prepare_guides(source_root: Path, site: Path) -> None:
    guide_root = source_root / "site" / "source" / "guide"
    index = guide_root / "index.json"
    if not index.is_file():
        return

    data = json.loads(index.read_text(encoding="utf-8"))
    if data.get("schema") != 1 or not isinstance(data.get("guides"), list):
        raise ValueError(f"invalid guide index: {index}")

    seen = set()
    overview = [
        "---",
        "title: Guide",
        "---",
        "",
        "The SCPF Guide explains the public Forge modelling workflow, core API concepts and native SolidCraft-oriented authoring patterns.",
        "",
    ]

    for row in data["guides"]:
        slug = row.get("slug")
        title = row.get("title")
        summary = row.get("summary", "")
        body_name = Path(str(row.get("body", ""))).name
        if (
            not isinstance(slug, str)
            or not slug
            or slug in seen
            or not isinstance(title, str)
            or not title
            or not body_name
        ):
            raise ValueError("invalid guide entry")
        seen.add(slug)

        body = guide_root / body_name
        if not body.is_file():
            raise ValueError(f"missing guide body: {body}")

        target = site / "content" / "guide" / slug / "index.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "---\n"
            f"title: {json.dumps(title)}\n"
            f"description: {json.dumps(str(summary))}\n"
            "---\n\n"
            + html_to_markdown(body.read_text(encoding="utf-8")),
            encoding="utf-8",
        )
        overview += [
            f"## [{title}]({slug}/)",
            "",
            str(summary).strip(),
            "",
        ]

    index_target = site / "content" / "guide" / "_index.md"
    index_target.parent.mkdir(parents=True, exist_ok=True)
    index_target.write_text("\n".join(overview).rstrip() + "\n", encoding="utf-8")
