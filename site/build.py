#!/usr/bin/env python3
"""Build Forge documentation from self-describing examples and API sources.

Human example intent comes from local model.yml files. Exact verification
contracts remain in verification/verify.py. Stable Pages attaches accepted
build/main evidence separately.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scpf"))

from scpf.runner import run_script
from scpf.version import TESTED_SOLIDCRAFT_VERSION
from guides import GUIDES
from example_metadata import discover_example_metadata
from example_documentation import discover_example_documentation
from html_writer import (
    CAD_SITE,
    LIBRARY_URL,
    cheatsheet_link,
    escape,
    guide_chapter_content,
    guide_overview_content,
    guide_sections,
    guide_shell,
    list_items,
    page,
    plain_text,
    reference_enum_content,
    reference_group_content,
    reference_method_content,
    reference_notes,
    reference_shell,
    render_template,
)
from api_coverage import (
    EXPORT_COVERAGE,
    CAPABILITY_COVERAGE,
    coverage_rank,
)
from capability_map import CAPABILITY_GROUPS, SOLIDCRAFT_CAPABILITIES
from api_reference import (
    ENUM_REFERENCES,
    GROUP_REFERENCES,
    METHOD_REFERENCES,
    anchor_aliases,
    api_manifest,
    enum_members,
    group_members,
    references_for_guide,
)

CHEATSHEET = [
    ("Model classes", [
        ("class Example: ... build(self)", "Write a Python model. No main() or show() is required.",
         "class SimpleBox:\n    def build(self):\n        return Box(40, 30, 10)", "simple-box"),
        ("Model parameters", "Numeric model fields become named SolidCraft parameters.",
         "length = 40.0\nBox(self.length, 30, 10)", "simple-box"),
    ]),
    ("Shapes and sketches", [
        ("Box(length, width, height, *, anchor=CENTER)", "Native Box centred on XYZ by default; choose anchor=BOTTOM for a bottom-face datum at Z=0.",
         "Box(40, 30, 10)", "simple-box"),
        ("Rectangle2D(width, depth)", "Planar XY profile authored inside a Sketch.",
         "with Sketch(plane='XY') as sketch:\n    Rectangle2D(100, 60)", "anchored-holes"),
        ("Circle2D(d=...)", "A round 2D profile authored inside a Sketch.",
         "with Sketch(plane='XY') as sketch:\n    Circle2D(d=8)", None),
        ("Polygon2D(points, plane=...)", "A closed profile on XY, XZ or YZ.",
         "Polygon2D([(0,0), (40,0), (0,30)], plane='XZ')", None),
        ("Cylinder(d=..., h=..., axis=..., anchor=CENTER)", "Native cylinder centred by default; choose an axial anchor such as BOTTOM or LEFT when that end should define the datum.",
         "Cylinder(d=24, h=14, axis=Axis.X, anchor=LEFT)", None),
        ("Sphere(radius, *, anchor=CENTER)", "Native sphere centred by default; cardinal anchors select tangent datums.",
         "Sphere(12, anchor=LEFT)", None),
    ]),
    ("Features and placement", [
        ("sketch.extrude(distance)", "Extrude an explicitly authored Sketch into editable native solid history.",
         "with Sketch(plane='XY') as sketch:\n    Rectangle2D(80, 50)\nplate = sketch.extrude(8)", "anchored-holes"),
        ("sketch.extrude(..., profiles=[...])", "Extrude or cut only the closed Sketch regions selected by fixed sketch-local points.",
         "cut = sketch.extrude(Depth.THROUGH_ALL, profiles=[(-30, 0), (30, 0)], exact_regions=True)", None),
        ("Sketch.sheet_metal(...)", "Create a native flat sheet from a closed XY Sketch with an explicit sheet rule.",
         "sheet = sketch.sheet_metal(thickness=2, bend_radius=2, k_factor=0.5)", None),
        ("Shape.fold(...)", "Fold existing sheet material along one straight line while keeping native sheet history.",
         "sheet = sheet.fold(line=((20,-20,0),(20,20,0)), angle=90, fixed=(-30,0,0))", None),
        ("Sketch.rectangular_pattern(...)", "Repeat a profile or earlier Sketch result as a native rectangular sketch pattern.",
         "row = sketch.rectangular_pattern(seed, count=4, spacing=25, direction=Axis.X)", None),
        ("Sketch.mirror(...)", "Mirror a profile, pattern result or earlier mirror result over the Sketch X or Y axis.",
         "sketch.mirror(row, axis=Axis.Y)", None),
        ("Hole(d=..., depth=...)", "A native hole. THROUGH_ALL follows the target body.",
         "Hole(d=8, depth=Depth.THROUGH_ALL)", "anchored-holes"),
        ("shape.rectangular_pattern(...)", "Repeat an already-applied native feature in one or two linear directions.",
         "plate.rectangular_pattern(cut, count=4, spacing=20, direction=Axis.X)", None),
        ("shape.circular_pattern(...)", "Repeat an already-applied native feature around a fixed axis.",
         "plate.circular_pattern(cut, count=6, axis=Axis.Z)", None),
        ("shape.at(target, anchor=..., child=...)", "Place a direct CSG shape anchor on another shape anchor; CENTER-to-CENTER is supported first.",
         "Cylinder(d=8, h=50, axis=Axis.X).at(body)", "primitive-csg"),
        ("shape.on(target, face=...)", "Place a feature on a selected face of another shape.",
         "Hole(d=8, depth=Depth.THROUGH_ALL).on(plate, face=Faces.TOP)", "anchored-holes"),
        ("TOP + LEFT / BOTTOM + RIGHT", "Combine cardinal directions to identify one edge of an axis-aligned rectangular solid.",
         "body.fillet(2, edges=[BOTTOM + LEFT, BOTTOM + RIGHT])", None),
        ("Box(...).at(..., anchor=...)", "Place a native Box by a face, edge or corner anchor without creating a Sketch.",
         "Box(80, 50, 12).at(0, 0, 0, anchor=FRONT + BOTTOM)", None),
        ("shape.fillet(...)", "Round selected edges of a feature-based body.",
         "body.fillet(2, edges=Edges.VERTICAL)", None),
        ("shape.chamfer(...)", "Bevel selected edges using the same edge selectors as fillet.",
         "body.chamfer(2, edges=Edges.VERTICAL)", None),
        ("shape.shell(...)", "Create an open-sided shell (supported feature trees only).",
         "Box(80, 50, 30).shell(2, open=Faces.TOP)", None),
        ("a + b / a - b / a & b", "Join, cut or intersect supported shapes; operation support depends on the shape types.",
         "body + Hole(d=8).at(0, 0, 10)", None),
    ]),
    ("Reusable components", [
        ("copy(placement=Placement(...))", "Create another occurrence of the same component definition at a declared pose.",
         "second = first.copy(placement=Placement(x=40))", "components"),
        ("model.attach(...)", "Fix one reusable component to another through explicit attachment references.",
         "right = Block().attach(left, parent=Anchor.RIGHT, child=Anchor.LEFT)", "components"),
        ("attach(offset=(u, v))", "Keep an in-plane attachment offset associative; parameter expressions become native planar-joint values.",
         "part.attach(base, parent=Anchor.FRONT_TOP_LEFT, child=mount, offset=(0, -wall + 12))", "components"),
        ("assembly.with_anchor(...) / anchor(...)", "Expose a semantic attachment datum owned by an assembly without adding application-specific anchors to a generic component.",
         "frame = (left + right).with_anchor(\"front_top_left\", left, ref)\nparent = frame.anchor(\"front_top_left\")", "components"),
        ("corner anchors", "Use one of the eight rectangular corner references when attaching components.",
         "marker = Marker().attach(base, parent=Anchor.FRONT_TOP_RIGHT, child=Anchor.BACK_TOP_RIGHT)", "corner-anchor"),
        ("AnchorFrame", "Define an oriented local attachment frame. Return it from anchors() when the datum belongs to the reusable component, or pass it directly to attach() when it belongs only to the assembly.",
         "mount = AnchorFrame(origin=(0,0,-12), z=(0,1,0), x=(0,0,-1))\npart.attach(base, parent=Anchor.FRONT_TOP_LEFT, child=mount)", "custom-anchor"),
        ("AnchorTopology", "Keep a named or assembly-local attachment reference on a planar-face edge or one of its endpoints so SolidCraft can follow changing geometry.",
         "def anchors(self):\n    return {\"mount\": AnchorTopology(edge=(0,10,5), on=(0,10,10), corner=(0,0,5))}", "custom-anchor"),
        ("Placement(rotation=(axis, degrees))", "Give a component occurrence one absolute axis-angle orientation.",
         "second = first.copy(placement=Placement(x=40, rotation=(Z, 180)))", None),
    ]),
    ("Compile and inspect", [
        ("python -m scpf ... --out", "Compile a model to SolidCraft command JSON; no SolidCraft app needed.",
         "python -m scpf examples/simple-box/scpf/model.py --out output/box.json", "simple-box"),
        ("python -m scpf replay ...", "Send existing command JSON to an open SolidCraft session; does not recompile.",
         "python -m scpf replay output/box.json", None),
        ("python -m scpf ... --connect", "Execute a model in an open SolidCraft GUI document.",
         "python -m scpf examples/simple-box/scpf/model.py --connect", None),
    ]),
]


def _search_entry(title, kind, url, summary, *, symbol=None, aliases=(), keywords=()):
    entry = {
        "title": title,
        "kind": kind,
        "url": url,
        "summary": plain_text(summary),
        "aliases": sorted({str(value) for value in aliases if value}),
        "keywords": plain_text(" ".join(str(value) for value in keywords if value)),
    }
    if symbol:
        entry["symbol"] = symbol
    return entry


def _api_search_fields(row):
    keywords = [
        row.get("signature", ""),
        row.get("use_when", ""),
        row.get("limits", ""),
        row.get("example", ""),
    ]
    aliases = [row.get("name", "")]
    name = row.get("name", "")
    if "." in name:
        aliases.append(name.rsplit(".", 1)[-1])
    for parameter in row.get("parameters", ()):
        aliases.append(parameter["name"])
        keywords.extend((parameter["name"], parameter["description"]))
    return aliases, keywords


def _api_search_entries():
    entries = []
    for reference in api_manifest()["references"]:
        if reference["kind"] == "group":
            members = reference["members"]
            guide = reference.get("guide")
        else:
            members = (reference,)
            guide = reference.get("guide")

        for member in members:
            name = member["name"]
            aliases, keywords = _api_search_fields(member)
            entries.append(_search_entry(
                name,
                "API Reference",
                member["reference"],
                member.get("summary", ""),
                symbol=name,
                aliases=aliases,
                keywords=keywords,
            ))
            if guide:
                entries.append(_search_entry(
                    f"{name} · API Guide",
                    "API Guide",
                    guide,
                    member.get("summary", ""),
                    aliases=aliases,
                    keywords=keywords,
                ))

            if member["kind"] == "enum":
                for enum_member in member.get("members", ()):
                    enum_name = f"{name}.{enum_member['name']}"
                    entries.append(_search_entry(
                        enum_name,
                        "API Reference",
                        f"reference/{name}/#{enum_name}",
                        f"{enum_name} has value {enum_member['value']}.",
                        aliases=(enum_member["name"],),
                        keywords=(member.get("summary", ""), enum_member["value"]),
                    ))
                    if guide:
                        entries.append(_search_entry(
                            f"{enum_name} · API Guide",
                            "API Guide",
                            guide,
                            member.get("summary", ""),
                            aliases=(enum_name, enum_member["name"]),
                            keywords=(enum_member["value"],),
                        ))

            if name == "Anchor":
                for alias in member.get("aliases", ()):
                    entries.append(_search_entry(
                        alias,
                        "API Reference",
                        "reference/Anchor/",
                        f"Convenience alias for Anchor.{alias}.",
                        symbol=alias,
                        aliases=(f"Anchor.{alias}",),
                        keywords=(member.get("summary", ""),),
                    ))
    return entries


def _guide_search_entries():
    entries = []
    for chapter in GUIDES:
        body = chapter["body"]
        entries.append(_search_entry(
            chapter["title"],
            "API Guide",
            f"guide/{chapter['slug']}/",
            chapter["summary"],
            aliases=(chapter["slug"],),
            keywords=(plain_text(body),),
        ))
        for anchor, heading, section in guide_sections(body):
            entries.append(_search_entry(
                heading,
                "API Guide",
                f"guide/{chapter['slug']}/#{anchor}",
                chapter["title"],
                aliases=(anchor,),
                keywords=(chapter["summary"], section),
            ))
    return entries


def _search_slug(value):
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return slug or "item"


def _cheatsheet_anchor(heading, title):
    return f"cheat-{_search_slug(heading)}-{_search_slug(title)}"


def _cheatsheet_search_entries():
    entries = []
    for heading, items in CHEATSHEET:
        for title, description, snippet, _linked in items:
            anchor = _cheatsheet_anchor(heading, title)
            entries.append(_search_entry(
                title,
                "Cheatsheet",
                f"cheatsheet/#{anchor}",
                description,
                aliases=(heading,),
                keywords=(snippet,),
            ))
    return entries


def _example_search_entries():
    """Return search rows from example-owned metadata and preserved docs."""

    documentation = {
        row.slug: row
        for row in discover_example_documentation()
    }
    return [
        _search_entry(
            row.title,
            "Example",
            f"examples/{row.slug}/",
            row.description,
            aliases=(row.tagline, row.section),
            keywords=(
                documentation[row.slug].goal,
                documentation[row.slug].forge_api,
                documentation[row.slug].forge_model,
                documentation[row.slug].lowering,
                documentation[row.slug].solidcraft_result,
                documentation[row.slug].saved_design_test,
                *(
                    note
                    for _name, note
                    in documentation[row.slug].reference_notes
                ),
            ),
        )
        for row in discover_example_metadata()
    ]


def build_search_index():
    """Build the client-side documentation search index from site sources."""
    entries = (
        _api_search_entries()
        + _guide_search_entries()
        + _cheatsheet_search_entries()
        + _example_search_entries()
    )
    seen = set()
    unique = []
    for entry in entries:
        key = (entry["kind"], entry["url"], entry["title"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
    return {
        "schema": 1,
        "generated_from": "public API docstrings, API Guide, Cheatsheet, example model.yml metadata and local README engineering documentation",
        "entries": unique,
    }


def scpf_version():
    """Return the Forge package version declared by this source tree."""

    data = tomllib.loads(
        (ROOT / "scpf" / "pyproject.toml").read_text(encoding="utf-8")
    )
    return data["project"]["version"]


def build(
    out,
    sha,
    native_root=None,
    diagram_root=None,
    reference_evidence_root=None,
    evidence_sha=None,
    build_scope=None,
    build_manifest=None,
    build_commit=None,
):
    """Compile the source-driven site.

    Legacy evidence arguments remain accepted during the #548 -> #497
    transition. #497 replaces them with explicit durable build/main loading.
    """
    # #497 consumes build/main through a new explicit evidence loader.
    # Legacy evidence arguments remain accepted until that cut-over so callers
    # do not break while source architecture is cleaned up.

    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "site" / "style.css", out / "style.css")
    shutil.copytree(
        ROOT / "site" / "static",
        out / "static",
        dirs_exist_ok=True,
    )
    (out / "search-index.json").write_text(
        json.dumps(build_search_index(), indent=2) + "\n",
        encoding="utf-8",
    )
    (out / ".nojekyll").write_text("", encoding="utf-8")
    cards = []
    qualification_cards = []
    manifest = {
        "library_commit": sha,
        "examples": {},
    }
    example_rows = discover_example_metadata()
    documentation_by_slug = {
        row.slug: row
        for row in discover_example_documentation()
    }
    if set(documentation_by_slug) != {row.slug for row in example_rows}:
        raise ValueError(
            "example metadata/documentation catalogs do not match"
        )

    for info in example_rows:
        slug = info.slug
        documentation = documentation_by_slug[slug]
        source_path = ROOT / "examples" / slug / "scpf" / "model.py"
        commands = run_script(source_path)
        assert commands.get("commands"), f"{slug}: empty command list"

        dest = out / "examples" / slug
        dest.mkdir(parents=True, exist_ok=True)
        source = source_path.read_text(encoding="utf-8")
        (dest / "model.py").write_text(source, encoding="utf-8")
        (dest / "commands.json").write_text(
            json.dumps(commands, indent=2) + "\n",
            encoding="utf-8",
        )
        count = len(commands["commands"])

        screenshot = (
            native_root / slug / "model.png"
            if native_root is not None
            else None
        )
        if (
            screenshot is not None
            and screenshot.is_file()
            and screenshot.stat().st_size > 0
        ):
            shutil.copyfile(screenshot, dest / "preview.png")
            page_preview = "preview.png"
            card_preview = f"examples/{slug}/preview.png"
            qualification_preview = f"../examples/{slug}/preview.png"
            preview_kind = "native-snapshot"
            preview_caption = (
                f"Native SolidCraft {TESTED_SOLIDCRAFT_VERSION} render "
                "from supplied accepted evidence."
            )
        else:
            page_preview = "../../static/example-placeholder.svg"
            card_preview = "static/example-placeholder.svg"
            qualification_preview = "../static/example-placeholder.svg"
            preview_kind = "source-only-placeholder"
            preview_caption = (
                "Source-only preview. Native images are supplied by accepted "
                "durable build evidence."
            )

        manifest["examples"][slug] = {
            "source": f"examples/{slug}/model.py",
            "commands": f"examples/{slug}/commands.json",
            "command_count": count,
            "preview_kind": preview_kind,
        }

        timeline = list_items(
            (row["command"] for row in commands["commands"]),
            code=True,
        )
        stages = list_items(info.stages)
        reference_notes_html = reference_notes(
            documentation.reference_notes
        )
        source_url = (
            f"{LIBRARY_URL}/blob/main/examples/{slug}/scpf/model.py"
        )

        body = render_template(
            "example.html",
            title=escape(info.title),
            section=escape(info.section),
            tagline=escape(info.tagline),
            description=escape(info.description),
            parameters=escape(info.parameters),
            command_summary=escape(
                f"{count} generated SolidCraft commands"
            ),
            preview_path=escape(page_preview),
            preview_caption=escape(preview_caption),
            stages=stages,
            documentation_goal=escape(documentation.goal),
            forge_api=escape(documentation.forge_api),
            forge_model=escape(documentation.forge_model),
            lowering=escape(documentation.lowering),
            solidcraft_result=escape(documentation.solidcraft_result),
            saved_design_test=escape(documentation.saved_design_test),
            reference_notes=reference_notes_html,
            source=escape(source),
            source_url=escape(source_url),
            timeline=timeline,
        )
        (dest / "index.html").write_text(
            page(
                info.title,
                body,
                stylesheet="../../style.css",
                home="../../",
                cheatsheet="../../cheatsheet/",
            ),
            encoding="utf-8",
        )

        card_values = {
            "slug": escape(slug),
            "title": escape(info.title),
            "section": escape(info.section),
            "description": escape(info.description),
            "command_summary": escape(
                f"{count} generated SolidCraft commands"
            ),
        }
        cards.append(
            render_template(
                "example-card.html",
                **card_values,
                example_url=f"examples/{escape(slug)}/",
                preview_url=escape(card_preview),
            )
        )
        qualification_cards.append(
            render_template(
                "example-card.html",
                **card_values,
                example_url=f"../examples/{escape(slug)}/",
                preview_url=escape(qualification_preview),
            )
        )

    # Expanded, navigable documentation remains separate from tiny smoke-test
    # examples and from the quick cheatsheet. Relevant API facts are repeated
    # inline from the generated reference data so ordinary guide use does not
    # require a click for every enum value or signature.
    guide_root = out / "guide"
    guide_root.mkdir(exist_ok=True)
    for chapter in GUIDES:
        slug = chapter["slug"]
        dest = guide_root / slug
        dest.mkdir(exist_ok=True)
        content = guide_chapter_content(chapter)
        body = guide_shell(content, active=slug, prefix="../")
        (dest / "index.html").write_text(
            page(chapter["title"], body, stylesheet="../../style.css",
                 home="../../", cheatsheet="../../cheatsheet/"),
            encoding="utf-8",
        )
    guide_overview = guide_overview_content()
    guide_index = guide_shell(
        guide_overview,
        active="overview",
        prefix="",
    )
    (guide_root / "index.html").write_text(
        page("API Guide", guide_index, stylesheet="../style.css",
             home="../", cheatsheet="../cheatsheet/"), encoding="utf-8"
    )

    # Complete public API lookup. Facts and explanatory text are derived
    # from the implementation/docstrings; this block only renders them.
    reference_root = out / "reference"
    reference_root.mkdir(exist_ok=True)
    for spec in ENUM_REFERENCES:
        slug = spec["slug"]
        dest = reference_root / slug
        dest.mkdir(exist_ok=True)
        content = reference_enum_content(spec)
        body = reference_shell(content, active=slug, prefix="../")
        (dest / "index.html").write_text(
            page(spec["title"], body, stylesheet="../../style.css",
                 home="../../", cheatsheet="../../cheatsheet/"),
            encoding="utf-8",
        )
    for spec in METHOD_REFERENCES:
        slug = spec["slug"]
        dest = reference_root / slug
        dest.mkdir(exist_ok=True)
        content = reference_method_content(spec)
        body = reference_shell(content, active=slug, prefix="../")
        (dest / "index.html").write_text(
            page(spec["title"], body, stylesheet="../../style.css",
                 home="../../", cheatsheet="../../cheatsheet/"),
            encoding="utf-8",
        )
    for spec in GROUP_REFERENCES:
        slug = spec["slug"]
        dest = reference_root / slug
        dest.mkdir(exist_ok=True)
        content = reference_group_content(spec)
        body = reference_shell(content, active=slug, prefix="../")
        (dest / "index.html").write_text(
            page(spec["title"], body, stylesheet="../../style.css",
                 home="../../", cheatsheet="../../cheatsheet/"),
            encoding="utf-8",
        )
    # Compact machine-readable lookup for agents is generated from exactly the
    # same objects/docstrings as the human reference.
    (reference_root / "api.json").write_text(
        json.dumps(api_manifest(), indent=2) + "\n",
        encoding="utf-8",
    )

    contract_source = (ROOT / "docs" / "api.md").read_text(encoding="utf-8")
    contract_body = render_template(
        "api-design-contract.html",
        contract_source=escape(contract_source),
    )
    (out / "api-design-contract.html").write_text(
        page(
            "API design contract",
            contract_body,
            stylesheet="style.css",
            home="./",
            cheatsheet="cheatsheet/",
        ),
        encoding="utf-8",
    )

    reference_overview = render_template("reference-overview.html")
    reference_index = reference_shell(
        reference_overview,
        active="overview",
        prefix="",
    )
    (reference_root / "index.html").write_text(
        page("API Reference", reference_index, stylesheet="../style.css",
             home="../", cheatsheet="../cheatsheet/"),
        encoding="utf-8",
    )

    # Qualification source pages are derived from the same local example
    # metadata. #497 attaches accepted build/main status and measurements.
    qualification_root = out / "qualification"
    qualification_root.mkdir(exist_ok=True)
    qualification_manifest = {}

    for info in example_rows:
        slug = info.slug
        documentation = documentation_by_slug[slug]
        case_dir = qualification_root / slug
        case_dir.mkdir(exist_ok=True)
        reference_notes_html = reference_notes(
            documentation.reference_notes
        )
        verification_url = (
            f"{LIBRARY_URL}/blob/main/examples/{slug}/verification/verify.py"
        )
        body = render_template(
            "qualification-case.html",
            slug=escape(slug),
            title=escape(info.title),
            section=escape(info.section),
            documentation_goal=escape(documentation.goal),
            forge_api=escape(documentation.forge_api),
            forge_model=escape(documentation.forge_model),
            lowering=escape(documentation.lowering),
            solidcraft_result=escape(documentation.solidcraft_result),
            saved_design_test=escape(documentation.saved_design_test),
            reference_notes=reference_notes_html,
            verification_url=escape(verification_url),
        )
        (case_dir / "index.html").write_text(
            page(
                info.title,
                body,
                stylesheet="../../style.css",
                home="../../",
                cheatsheet="../../cheatsheet/",
            ),
            encoding="utf-8",
        )
        qualification_manifest[slug] = {
            "title": info.title,
            "documentation_source": f"examples/{slug}/README.md",
            "verification_source": (
                f"examples/{slug}/verification/verify.py"
            ),
            "evidence_source": "build/main",
        }

    qualification_index = render_template(
        "qualification-index.html",
        example_count=len(example_rows),
        cards="".join(qualification_cards),
    )
    (qualification_root / "index.html").write_text(
        page(
            "Qualification",
            qualification_index,
            stylesheet="../style.css",
            home="../",
            cheatsheet="../cheatsheet/",
        ),
        encoding="utf-8",
    )
    (qualification_root / "manifest.json").write_text(
        json.dumps(
            {
                "library_commit": sha,
                "evidence_source": "build/main",
                "cases": qualification_manifest,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    sections = []
    example_slugs = {row.slug for row in example_rows}
    for heading, items in CHEATSHEET:
        boxes = []
        for title, description, snippet, linked in items:
            link = cheatsheet_link(linked, example_slugs)
            boxes.append(
                render_template(
                    "cheatsheet-item.html",
                    anchor=escape(_cheatsheet_anchor(heading, title)),
                    title=escape(title),
                    description=escape(description),
                    snippet=escape(snippet),
                    link=link,
                )
            )
        sections.append(
            render_template(
                "cheatsheet-section.html",
                heading=escape(heading),
                items="".join(boxes),
            )
        )
    cheat = render_template(
        "cheatsheet.html",
        solidcraft_version=escape(TESTED_SOLIDCRAFT_VERSION),
        sections="".join(sections),
    )

    (out / "cheatsheet").mkdir(exist_ok=True)
    (out / "cheatsheet" / "index.html").write_text(
        page("Cheatsheet", cheat, stylesheet="../style.css", home="../", cheatsheet="./"),
        encoding="utf-8")

    home = render_template(
        "home.html",
        solidcraft_version=escape(TESTED_SOLIDCRAFT_VERSION),
        cad_site=escape(CAD_SITE),
        example_count=len(example_rows),
        cards="".join(cards),
        source_sha=escape(sha),
    )

    (out / "index.html").write_text(
        page("Examples & cheatsheet", home, stylesheet="style.css", home="./", cheatsheet="cheatsheet/"),
        encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "output" / "site")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--evidence-sha", help="Qualified source commit for reused evidence")
    parser.add_argument("--native", type=Path, help="Source-matched native screenshot directory")
    parser.add_argument("--diagram-root", type=Path, help="Generated qualification setup diagrams")
    parser.add_argument("--references", type=Path, help="Source-matched qualification reference evidence")
    parser.add_argument(
        "--build-scope",
        help="Generated build branch scope, for example main or pr/326",
    )
    parser.add_argument(
        "--build-manifest",
        type=Path,
        help="Generic durable build/main build.json; detailed evidence mapping is handled by stable Pages",
    )
    parser.add_argument(
        "--build-commit",
        help="Immutable build branch commit used in evidence links",
    )
    options = parser.parse_args()
    build(
        options.out,
        options.source_sha,
        native_root=options.native,
        diagram_root=options.diagram_root,
        reference_evidence_root=options.references,
        evidence_sha=options.evidence_sha,
        build_scope=options.build_scope,
        build_manifest=options.build_manifest,
        build_commit=options.build_commit,
    )
    print(f"Built independent SCPF library site: {options.out}")
