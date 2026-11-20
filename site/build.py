#!/usr/bin/env python3
"""Build a *library* API site from self-contained, regression-tested SCPF samples.

The complete mechanical CAD catalog belongs to 2026-011-02.cad.solidcraft.
This site deliberately contains only tiny fixtures and the SCPF cheatsheet.
"""
import argparse
import html
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tomllib
from string import Template

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scpf"))

from scpf.runner import run_script
from scpf.version import TESTED_SOLIDCRAFT_VERSION
from guides import GUIDES
from example_metadata import discover_example_metadata
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

LIBRARY_URL = "https://github.com/brainboxemb/lib.py.solidcraft.forge"
ACTIVE_BUILD_COMMIT = "build"
CAD_SITE = "https://brainboxemb.github.io/2026-011-02.cad.solidcraft/"

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


def escape(value):
    return html.escape(str(value), quote=True)


def _plain_search_text(value):
    """Return compact visible text from generated HTML or plain strings."""
    text = re.sub(r"<[^>]+>", " ", str(value))
    return " ".join(html.unescape(text).split())


def _search_entry(title, kind, url, summary, *, symbol=None, aliases=(), keywords=()):
    entry = {
        "title": title,
        "kind": kind,
        "url": url,
        "summary": _plain_search_text(summary),
        "aliases": sorted({str(value) for value in aliases if value}),
        "keywords": _plain_search_text(" ".join(str(value) for value in keywords if value)),
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


_GUIDE_HEADING = re.compile(
    r'<h([23])\s+id="([^"]+)">(.*?)</h\1>',
    re.IGNORECASE | re.DOTALL,
)


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
            keywords=(_plain_search_text(body),),
        ))
        headings = list(_GUIDE_HEADING.finditer(body))
        for index, match in enumerate(headings):
            next_start = (
                headings[index + 1].start()
                if index + 1 < len(headings)
                else len(body)
            )
            heading = _plain_search_text(match.group(3))
            section = _plain_search_text(body[match.end():next_start])
            entries.append(_search_entry(
                heading,
                "API Guide",
                f"guide/{chapter['slug']}/#{match.group(2)}",
                chapter["title"],
                aliases=(match.group(2),),
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
    """Return search rows from example-owned metadata."""

    return [
        _search_entry(
            row.title,
            "Example",
            f"examples/{row.slug}/",
            row.description,
            aliases=(row.tagline, row.section),
            keywords=(*row.concepts, *row.verification_proves),
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
        "generated_from": "public API docstrings, API Guide, Cheatsheet and example model.yml metadata",
        "entries": unique,
    }


def page(title, body, *, stylesheet, home, cheatsheet):
    """Render the shared site shell from an external template."""

    template = Template(
        (ROOT / "site" / "templates" / "page.html").read_text(
            encoding="utf-8"
        )
    )
    return template.substitute(
        title=escape(title),
        body=body,
        stylesheet=escape(stylesheet),
        home=escape(home),
        cheatsheet=escape(cheatsheet),
        library_url=escape(LIBRARY_URL),
        cad_site=escape(CAD_SITE),
    )


def build_scope_from_environment():
    """Return the technical evidence scope for this site build.

    Presentation-only builds reuse the last qualified main output. A workflow
    that actually produces new PR technical evidence must set
    SCPF_BUILD_SCOPE=pr/<number> explicitly.
    """
    return os.environ.get("SCPF_BUILD_SCOPE", "main").strip("/") or "main"


def build_blob_url(scope, relative=""):
    relative = str(relative).lstrip("/")
    base = f"{LIBRARY_URL}/blob/{ACTIVE_BUILD_COMMIT}/{scope}"
    return f"{base}/{relative}" if relative else base


def build_raw_url(scope, relative=""):
    relative = str(relative).lstrip("/")
    base = (
        "https://raw.githubusercontent.com/brainboxemb/"
        f"lib.py.solidcraft.forge/{ACTIVE_BUILD_COMMIT}/{scope}"
    )
    return f"{base}/{relative}" if relative else base


def evidence_scope(build_manifest_data, slug, implementation, fallback):
    record = (
        ((build_manifest_data.get("cases") or {}).get(slug) or {})
        .get("implementations", {})
        .get(implementation)
    )
    if record and record.get("build_scope"):
        return record["build_scope"]
    return fallback


def text(path):
    return path.read_text(encoding="utf-8")


def render_template(name, **values):
    """Render one external site template."""

    template_path = ROOT / "site" / "templates" / name
    return Template(text(template_path)).substitute(values)


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
    """Compile the public site and attach verified qualification evidence.

    sha is the current site/source commit. evidence_sha is the already
    qualified Forge/API commit that produced native/reference evidence.
    They are normally equal; site-only rebuilds may reuse older evidence.
    """
    global ACTIVE_BUILD_COMMIT
    evidence_sha = evidence_sha or sha
    build_scope = build_scope or build_scope_from_environment()
    ACTIVE_BUILD_COMMIT = build_commit or os.environ.get("SCPF_BUILD_COMMIT", "build")
    build_output_url = build_blob_url(build_scope)
    build_manifest_data = {}
    if build_manifest is not None:
        build_manifest_data = json.loads(
            Path(build_manifest).read_text(encoding="utf-8")
        )
        evidence_sha = (
            build_manifest_data.get("source_commit")
            or evidence_sha
        )

    verified = False
    metadata = {}
    forge_version = scpf_version()
    qualified_at = "attached by stable Pages from durable build/main"

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

    for info in example_rows:
        slug = info.slug
        source_path = ROOT / "examples" / slug / "scpf" / "model.py"
        commands = run_script(source_path)
        assert commands.get("commands"), f"{slug}: empty command list"

        dest = out / "examples" / slug
        dest.mkdir(parents=True, exist_ok=True)
        source = text(source_path)
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

        timeline = "".join(
            f"<li><code>{escape(row['command'])}</code></li>"
            for row in commands["commands"]
        )
        stages = "".join(
            f"<li>{escape(value)}</li>" for value in info.stages
        )
        proves = "".join(
            f"<li>{escape(value)}</li>"
            for value in info.verification_proves
        )
        concept_tags = "".join(
            f'<span class="tag">{escape(value)}</span>'
            for value in info.concepts
        )
        saved_design = (
            "<h3>Saved design</h3>"
            f"<p>{escape(info.verification_saved_design)}</p>"
            if info.verification_saved_design
            else ""
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
            concept_tags=concept_tags,
            stages=stages,
            verification_summary=escape(info.verification_summary),
            verification_proves=proves,
            saved_design=saved_design,
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
            "concept_tags": concept_tags,
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
    def guide_sidebar(*, active=None, prefix=""):
        active_chapter = next(
            (chapter for chapter in GUIDES if chapter["slug"] == active),
            None,
        )

        def nav_link(slug, title):
            cls = ' class="active"' if slug == active else ""
            link = (
                f'<a{cls} href="{escape(prefix + slug + "/")}">'
                f'{escape(title)}</a>'
            )
            if slug == active and active_chapter is not None:
                headings = re.findall(
                    r'<h2 id="([^"]+)">([^<]+)</h2>',
                    active_chapter["body"],
                )
                if headings:
                    link += (
                        '<div class="guide-subnav">'
                        + "".join(
                            f'<a href="#{escape(anchor)}">{escape(title)}</a>'
                            for anchor, title in headings
                        )
                        + '</div>'
                    )
            return link

        overview_cls = ' class="active"' if active == "overview" else ""
        return (
            '<aside class="guide-sidebar">'
            '<h2>API Guide</h2>'
            f'<a{overview_cls} href="{escape(prefix or "./")}">Overview</a>'
            + "".join(
                nav_link(chapter["slug"], chapter["title"])
                for chapter in GUIDES
            )
            + '</aside>'
        )

    def guide_shell(content, *, active, prefix):
        return (
            '<main class="wrap guide-layout">'
            + guide_sidebar(active=active, prefix=prefix)
            + '<article class="guide-article">'
            + content
            + '</article></main>'
        )

    def _member_details(member, *, compact=False):
        if member["kind"] == "enum":
            return (
                '<div class="guide-api-members">'
                + " · ".join(
                    f'<code>{escape(member["name"])}.{escape(row["name"])}</code>'
                    for row in member["members"]
                )
                + '</div>'
            )
        if member["kind"] == "constant":
            return f'<p><code>{escape(member["name"])} = {escape(member["value"])}</code></p>'
        if member.get("signature"):
            css = ' class="guide-api-signature"' if compact else ""
            return f'<pre{css}><code>{escape(member["signature"])}</code></pre>'
        return ""

    def _parameter_details(member, *, heading="Parameters"):
        parameters = member.get("parameters") or []
        if not parameters:
            return ""
        rows = "".join(
            "<tr>"
            f"<td><code>{escape(row['name'])}</code></td>"
            f"<td>{escape(row['description'])}</td>"
            "</tr>"
            for row in parameters
        )
        return (
            f"<h3>{escape(heading)}</h3>"
            '<table class="api-table"><thead><tr><th>Argument</th><th>Meaning</th></tr></thead>'
            f"<tbody>{rows}</tbody></table>"
        )

    def _example_details(member):
        example = member.get("example") or ""
        if not example:
            return ""
        return "<h3>Example</h3>" + f"<pre><code>{escape(example)}</code></pre>"

    def _guide_group_details(spec):
        rows = []
        for member in group_members(spec):
            rows.append(
                f'<div class="guide-api-group-member" id="api-{escape(member["name"])}">'
                f'<h4><code>{escape(member["name"])}</code></h4>'
                + _member_details(member, compact=True)
                + (f'<p>{escape(member["summary"])}</p>' if member["summary"] else "")
                + (
                    f'<p><strong>Use when:</strong> {escape(member["use_when"])}</p>'
                    if member["use_when"] else ""
                )
                + (
                    f'<p><strong>Current limits:</strong> {escape(member["limits"])}</p>'
                    if member["limits"] else ""
                )
                + (
                    f'<p><a href="../../reference/{escape(spec["slug"])}/#{escape(member["name"])}">'
                    'Detailed parameter reference →</a></p>'
                    if member.get("parameters") else ""
                )
                + '</div>'
            )
        return '<div class="guide-api-group-members">' + "".join(rows) + '</div>'

    def guide_api_summary(slug):
        specs = references_for_guide(slug)
        if not specs:
            return ""
        cards = []
        for spec in specs:
            if spec["kind"] == "enum":
                details = (
                    '<div class="guide-api-members">'
                    + " · ".join(
                        f'<code>{escape(spec["slug"])}.{escape(name)}</code>'
                        for name, _value in enum_members(spec)
                    )
                    + '</div>'
                )
            elif spec["kind"] == "group":
                details = _guide_group_details(spec)
            else:
                details = (
                    f'<pre class="guide-api-signature"><code>'
                    f'{escape(spec["signature"])}</code></pre>'
                )
            cards.append(
                '<article class="guide-api-item">'
                f'<h3><a href="../../reference/{escape(spec["slug"])}/">'
                f'{escape(spec["title"])}</a></h3>'
                f'<p>{escape(spec["summary"])}</p>'
                + details
                + (
                    f'<p><strong>Use when:</strong> {escape(spec["use_when"])}</p>'
                    if spec.get("use_when") else ""
                )
                + (
                    f'<p><strong>Current limits:</strong> {escape(spec["limits"])}</p>'
                    if spec.get("limits") else ""
                )
                + '</article>'
            )
        return (
            '<section class="guide-api-summary">'
            '<h2>API on this page</h2>'
            '<p class="guide-api-intro">These values and signatures are generated '
            'from the current Python API. They are shown here so the normal guide '
            'flow does not require opening the reference for every detail.</p>'
            '<div class="guide-api-grid">' + "".join(cards) + '</div></section>'
        )

    for chapter in GUIDES:
        slug = chapter["slug"]
        dest = guide_root / slug
        dest.mkdir(exist_ok=True)
        content = (
            f'<p class="crumb"><a href="../">API Guide</a> / {escape(chapter["title"])}</p>'
            + f'<h1>{escape(chapter["title"])}</h1>'
            + f'<p class="guide-lead">{escape(chapter["summary"])}</p>'
            + chapter["body"]
            + guide_api_summary(slug)
        )
        body = guide_shell(content, active=slug, prefix="../")
        (dest / "index.html").write_text(
            page(chapter["title"], body, stylesheet="../../style.css",
                 home="../../", cheatsheet="../../cheatsheet/"),
            encoding="utf-8",
        )
    guide_overview = (
        '<p class="crumb">API Guide / Overview</p>'
        '<h1>API Guide</h1>'
        '<p class="guide-lead">Learn the modelling concepts, understand when to '
        'use them, and see the generated native SolidCraft behaviour.</p>'
        '<section class="panel"><h2>Start here</h2>'
        '<p>Use the chapter navigation on the left. The layout remains the same '
        'while you move through the guide, so you can switch directly between '
        'components, assemblies, features, transformations and other topics '
        'without returning to a separate overview page.</p>'
        '<p>Use the <a href="../reference/">API Reference</a> when you already '
        'know the concept and need exact signatures, enum values or limits. '
        'Use the <a href="../cheatsheet/">Cheatsheet</a> for the shortest lookup.</p>'
        '</section>'
    )
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
    def reference_sidebar(*, active=None, prefix=""):
        def nav_link(slug, title):
            cls = ' class="active"' if slug == active else ""
            link = (
                f'<a{cls} href="{escape(prefix + slug + "/")}">'
                f'{escape(title)}</a>'
            )
            if slug == active:
                group = next(
                    (spec for spec in GROUP_REFERENCES if spec["slug"] == slug),
                    None,
                )
                if group is not None:
                    link += (
                        '<div class="reference-subnav">'
                        + "".join(
                            f'<a href="#{escape(member["name"])}">'
                            f'{escape(member["name"])}</a>'
                            for member in group_members(group)
                        )
                        + '</div>'
                    )
            return link

        component_methods = [
            spec for spec in METHOD_REFERENCES
            if (
                spec["slug"] in {"component", "assembly"}
                or spec["slug"].startswith("Occurrence.")
                or spec["slug"].startswith("Assembly.")
            )
        ]
        shape_methods = [
            spec for spec in METHOD_REFERENCES
            if spec not in component_methods
        ]

        overview_cls = ' class="active"' if active == "overview" else ""
        return (
            '<aside class="reference-sidebar">'
            '<h2>API Reference</h2>'
            f'<a{overview_cls} href="{escape(prefix or "./")}">Overview</a>'
            '<h3>Browse by task</h3>'
            + "".join(
                nav_link(spec["slug"], spec["title"])
                for spec in GROUP_REFERENCES
            )
            + '<h3>Selectors</h3>'
            + "".join(
                nav_link(spec["slug"], spec["title"])
                for spec in ENUM_REFERENCES
            )
            + '<h3>Components &amp; assemblies</h3>'
            + "".join(
                nav_link(spec["slug"], spec["title"])
                for spec in component_methods
            )
            + '<h3>Shape &amp; sketch</h3>'
            + "".join(
                nav_link(spec["slug"], spec["title"])
                for spec in shape_methods
            )
            + '</aside>'
        )

    def reference_shell(content, *, active, prefix):
        return (
            '<main class="wrap reference-layout">'
            + reference_sidebar(active=active, prefix=prefix)
            + '<article class="reference-article">'
            + content
            + '</article></main>'
        )

    for spec in ENUM_REFERENCES:
        slug = spec["slug"]
        dest = reference_root / slug
        dest.mkdir(exist_ok=True)
        rows = "".join(
            f'<tr id="{escape(slug + "." + name)}">'
            f"<td><code>{escape(slug)}.{escape(name)}</code></td>"
            f"<td><code>{escape(str(value))}</code></td>"
            "</tr>"
            for name, value in enum_members(spec)
        )
        content = (
            '<p class="crumb"><a href="../">API Reference</a> / '
            + escape(spec["title"]) + '</p>'
            + '<section class="hero small"><p class="eyebrow">Generated SCPF API reference</p>'
            + f'<h1>{escape(spec["title"])}</h1><p>{escape(spec["summary"])}</p></section>'
            + '<section class="panel">'
            + (
                f'<h2>When to use it</h2><p>{escape(spec["use_when"])}</p>'
                if spec["use_when"] else ""
            )
            + '<h2>Members</h2>'
            + '<table class="api-table"><thead><tr><th>Name</th><th>Value</th></tr></thead>'
            + f'<tbody>{rows}</tbody></table>'
            + (
                '<h2>Convenience aliases</h2><p>'
                + " · ".join(f'<code>{escape(name)}</code>' for name in anchor_aliases())
                + '</p>'
                if spec["slug"] == "Anchor" else ""
            )
            + _parameter_details(spec, heading="Parameters")
            + _example_details(spec)
            + (
                f'<h2>Current limits</h2><p>{escape(spec["limits"])}</p>'
                if spec["limits"] else ""
            )
            + f'<p><a href="../../guide/{escape(spec["guide"])}/#{escape(spec["guide_anchor"])}">'
              'Worked usage in the guide →</a> · '
              '<a href="../../api-design-contract.html">Cross-object API design rules →</a></p>'
            + '</section>'
        )
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
        content = (
            '<p class="crumb"><a href="../">API Reference</a> / '
            + escape(spec["title"]) + '</p>'
            + '<section class="hero small"><p class="eyebrow">Generated SCPF API reference</p>'
            + f'<h1>{escape(spec["title"])}</h1><p>{escape(spec["summary"])}</p></section>'
            + '<section class="panel"><h2>Current Python signature</h2>'
            + f'<pre><code>{escape(spec["signature"])}</code></pre>'
            + (
                f'<h2>When to use it</h2><p>{escape(spec["use_when"])}</p>'
                if spec["use_when"] else ""
            )
            + (
                f'<h2>Current limits</h2><p>{escape(spec["limits"])}</p>'
                if spec["limits"] else ""
            )
            + f'<p><a href="../../guide/{escape(spec["guide"])}/#{escape(spec["guide_anchor"])}">'
              'Worked usage in the guide →</a> · '
              '<a href="../../api-design-contract.html">Cross-object API design rules →</a></p>'
            + '</section>'
        )
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
        member_sections = []
        for member in group_members(spec):
            member_sections.append(
                f'<section class="panel api-group-member" id="{escape(member["name"])}">'
                f'<h2><code>{escape(member["name"])}</code></h2>'
                + _member_details(member)
                + (f'<p>{escape(member["summary"])}</p>' if member["summary"] else "")
                + (
                    f'<h3>When to use it</h3><p>{escape(member["use_when"])}</p>'
                    if member["use_when"] else ""
                )
                + _parameter_details(member)
                + _example_details(member)
                + (
                    f'<h3>Current limits</h3><p>{escape(member["limits"])}</p>'
                    if member["limits"] else ""
                )
                + '</section>'
            )
        guide_link = (
            f'<p><a href="../../guide/{escape(spec["guide"])}/#{escape(spec["guide_anchor"])}">'
            'Worked usage in the guide →</a> · '
            '<a href="../../api-design-contract.html">Cross-object API design rules →</a></p>'
            if spec.get("guide")
            else '<p><a href="../../api-design-contract.html">Cross-object API design rules →</a></p>'
        )
        content = (
            '<p class="crumb"><a href="../">API Reference</a> / '
            + escape(spec["title"]) + '</p>'
            + '<section class="hero small"><p class="eyebrow">Generated SCPF API reference</p>'
            + f'<h1>{escape(spec["title"])}</h1><p>{escape(spec["summary"])}</p>'
            + guide_link + '</section>'
            + "".join(member_sections)
        )
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
    (out / "api-design-contract.html").write_text(
        page(
            "API design contract",
            '<main class="wrap"><p class="crumb"><a href="reference/">API Reference</a> / '
            'API design contract</p><section class="hero small">'
            '<p class="eyebrow">Cross-object design rules</p><h1>Forge API design contract</h1>'
            '<p>Design rules that span several public objects live here. Exact '
            'names, signatures, enum values and object-specific semantics come '
            'from the Python implementation and public docstrings.</p>'
            '</section><section class="panel"><pre><code>'
            + escape(contract_source) + '</code></pre></section></main>',
            stylesheet="style.css", home="./", cheatsheet="cheatsheet/",
        ),
        encoding="utf-8",
    )

    reference_overview = (
        '<p class="crumb">API Reference / Overview</p>'
        '<section class="hero small">'
        '<p class="eyebrow">Complete generated lookup</p><h1>API Reference</h1>'
        '<p>Use the navigation on the left for direct access to task groups, '
        'selectors and exact public API operations. The layout stays the same '
        'while you move through the reference.</p>'
        '<p>If you are still deciding which modelling concept to use, start with '
        '<a href="../guide/">the API Guide</a>.</p>'
        '</section>'
        '<section class="panel"><h2>How to use this reference</h2>'
        '<p><strong>Browse by task</strong> keeps related constructors and helpers '
        'together. <strong>Selectors</strong> contains complete generated values '
        'such as Anchor and Faces. <strong>Core API</strong> gives exact current '
        'signatures for components, assemblies, shapes and sketches.</p>'
        '<p><a href="api.json">Machine-readable API index →</a> · '
        '<a href="../api-design-contract.html">Cross-object API design rules →</a></p>'
        '</section>'
    )
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
        case_dir = qualification_root / slug
        case_dir.mkdir(exist_ok=True)
        proves = "".join(
            f"<li>{escape(value)}</li>"
            for value in info.verification_proves
        )
        saved_design = (
            "<h3>Saved design</h3>"
            f"<p>{escape(info.verification_saved_design)}</p>"
            if info.verification_saved_design
            else ""
        )
        verification_url = (
            f"{LIBRARY_URL}/blob/main/examples/{slug}/verification/verify.py"
        )
        body = render_template(
            "qualification-case.html",
            slug=escape(slug),
            title=escape(info.title),
            section=escape(info.section),
            verification_summary=escape(info.verification_summary),
            verification_proves=proves,
            saved_design=saved_design,
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
    for heading, items in CHEATSHEET:
        boxes = []
        for title, description, snippet, linked in items:
            ref = (f'<p class="tip"><a href="../examples/{linked}/">View working example →</a></p>'
                   if linked in {row.slug for row in example_rows} else "")
            anchor = _cheatsheet_anchor(heading, title)
            boxes.append(f"""<article class="reference" id="{escape(anchor)}"><h3><code>{escape(title)}</code></h3>
<p>{escape(description)}</p><pre><code>{escape(snippet)}</code></pre>{ref}</article>""")
        sections.append(f'<section><h2>{escape(heading)}</h2><div class="reference-grid">{"".join(boxes)}</div></section>')
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
