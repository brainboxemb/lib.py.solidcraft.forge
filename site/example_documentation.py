"""Load preserved example-owned engineering documentation.

The documentation was migrated verbatim from the last canonical legacy
qualification case table. This loader validates structure and provenance only;
it does not infer verification facts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = ROOT / "examples"
LEGACY_CASE_SOURCE_COMMIT = "be40b09e7454a90e87d83768a9e7453c52ba5d76"

_SECTION_ORDER = (
    "Goal",
    "Forge API",
    "Forge model",
    "How Forge builds it in SolidCraft",
    "SolidCraft result",
    "Saved-design test",
    "Geometry evidence",
    "Reference notes",
)

_HEADING = re.compile(r"^(#{2,3})\s+(.+?)\s*$", re.MULTILINE)
_REFERENCE = re.compile(r"^- \*\*(.+?)\*\* — (.+)$", re.MULTILINE)


@dataclass(frozen=True)
class ExampleDocumentation:
    slug: str
    title: str
    group: str
    saved_design_required: bool
    goal: str
    forge_api: str
    forge_model: str
    lowering: str
    solidcraft_result: str
    saved_design_test: str
    bounds_sufficient: bool
    geometry_reason: str
    reference_notes: tuple[tuple[str, str], ...]


def _section_map(source: str) -> dict[str, str]:
    headings = list(_HEADING.finditer(source))
    sections: dict[str, str] = {}
    for index, match in enumerate(headings):
        name = match.group(2)
        if name not in _SECTION_ORDER:
            continue
        end = (
            headings[index + 1].start()
            if index + 1 < len(headings)
            else len(source)
        )
        sections[name] = source[match.end():end].strip()
    return sections


def load_example_documentation(example_root: Path) -> ExampleDocumentation:
    """Load one example README without interpreting its engineering content."""

    example_root = Path(example_root)
    slug = example_root.name
    path = example_root / "README.md"
    if not path.is_file():
        raise ValueError(f"{slug}: missing README.md")

    source = path.read_text(encoding="utf-8")
    if LEGACY_CASE_SOURCE_COMMIT not in source:
        raise ValueError(
            f"{slug}: README.md must preserve legacy documentation provenance"
        )

    legacy_title = re.search(
        r"^\*\*Legacy title:\*\* \x60(.+?)\x60$",
        source,
        re.MULTILINE,
    )
    if legacy_title:
        title = legacy_title.group(1)
    else:
        h1 = re.search(r"^#\s+(.+?)\s*$", source, re.MULTILINE)
        if not h1:
            raise ValueError(f"{slug}: README.md needs a title")
        title = h1.group(1)

    group = re.search(
        r"^\*\*(?:Legacy group|Group):\*\* \x60(.+?)\x60$",
        source,
        re.MULTILINE,
    )
    if not group:
        raise ValueError(f"{slug}: README.md needs preserved legacy group")

    sections = _section_map(source)
    missing = [name for name in _SECTION_ORDER if name not in sections]
    if missing:
        raise ValueError(
            f"{slug}: README.md missing preserved sections: "
            + ", ".join(missing)
        )

    geometry = sections["Geometry evidence"]
    if "Geometry-rationale provenance:" not in geometry:
        raise ValueError(
            f"{slug}: README.md needs geometry-rationale provenance"
        )
    sufficient = re.search(
        r"^\*\*Bounds sufficient:\*\* \x60(true|false)\x60$",
        geometry,
        re.MULTILINE,
    )
    if not sufficient:
        raise ValueError(f"{slug}: README.md needs preserved bounds sufficiency")
    geometry_reason = re.sub(
        r"^> Geometry-rationale provenance:.*$",
        "",
        geometry,
        count=1,
        flags=re.MULTILINE,
    )
    geometry_reason = re.sub(
        r"^\*\*Bounds sufficient:\*\* \x60(?:true|false)\x60$",
        "",
        geometry_reason,
        count=1,
        flags=re.MULTILINE,
    ).strip()
    if not geometry_reason:
        raise ValueError(f"{slug}: README.md needs preserved geometry rationale")

    references = tuple(_REFERENCE.findall(sections["Reference notes"]))
    if not references:
        raise ValueError(f"{slug}: README.md needs preserved reference notes")

    return ExampleDocumentation(
        slug=slug,
        title=title,
        group=group.group(1),
        saved_design_required=bool(
            re.search(
                r"^\*\*Saved-design required:\*\* \x60true\x60$",
                source,
                re.MULTILINE,
            )
        ),
        goal=sections["Goal"],
        forge_api=sections["Forge API"],
        forge_model=sections["Forge model"],
        lowering=sections["How Forge builds it in SolidCraft"],
        solidcraft_result=sections["SolidCraft result"],
        saved_design_test=sections["Saved-design test"],
        bounds_sufficient=sufficient.group(1) == "true",
        geometry_reason=geometry_reason,
        reference_notes=references,
    )


def discover_example_documentation(
    root: Path = EXAMPLES_ROOT,
) -> tuple[ExampleDocumentation, ...]:
    """Discover preserved documentation beside each verified example."""

    rows = [
        load_example_documentation(path)
        for path in sorted(Path(root).iterdir())
        if (path / "verification" / "verify.py").is_file()
    ]
    if not rows:
        raise ValueError(f"no verified examples found below {root}")

    slugs = [row.slug for row in rows]
    if len(slugs) != len(set(slugs)):
        raise ValueError("duplicate documented example slugs discovered")
    return tuple(rows)
