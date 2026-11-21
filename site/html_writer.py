"""Explicit HTML rendering layer for the generated Forge documentation.

Source discovery, evidence handling and build orchestration live elsewhere.
This module owns dynamic HTML composition that is not clearer as a static
template.
"""

from __future__ import annotations

import html
from pathlib import Path
import re
from string import Template

from api_reference import (
    ENUM_REFERENCES,
    GROUP_REFERENCES,
    METHOD_REFERENCES,
    anchor_aliases,
    enum_members,
    group_members,
    references_for_guide,
)
from guides import GUIDES


ROOT = Path(__file__).resolve().parents[1]
LIBRARY_URL = "https://github.com/brainboxemb/lib.py.solidcraft.forge"
CAD_SITE = "https://brainboxemb.github.io/2026-011-02.cad.solidcraft/"


def escape(value):
    return html.escape(str(value), quote=True)


def plain_text(value):
    """Return compact visible text from generated HTML or plain strings."""
    text = re.sub(r"<[^>]+>", " ", str(value))
    return " ".join(html.unescape(text).split())


_GUIDE_HEADING = re.compile(
    r'<h([23])\s+id="([^"]+)">(.*?)</h\1>',
    re.IGNORECASE | re.DOTALL,
)


def guide_sections(body):
    """Return visible heading/section text from rendered guide content."""
    headings = list(_GUIDE_HEADING.finditer(body))
    result = []
    for index, match in enumerate(headings):
        next_start = (
            headings[index + 1].start()
            if index + 1 < len(headings)
            else len(body)
        )
        result.append(
            (
                match.group(2),
                plain_text(match.group(3)),
                plain_text(body[match.end():next_start]),
            )
        )
    return result


def render_template(name, **values):
    """Render one external site template."""
    template_path = ROOT / "site" / "templates" / name
    template = Template(template_path.read_text(encoding="utf-8"))
    return template.substitute(values)


def page(title, body, *, stylesheet, home, cheatsheet):
    """Render the shared site shell from its external template."""
    return render_template(
        "page.html",
        title=escape(title),
        body=body,
        stylesheet=escape(stylesheet),
        home=escape(home),
        cheatsheet=escape(cheatsheet),
        library_url=escape(LIBRARY_URL),
        cad_site=escape(CAD_SITE),
    )


def list_items(values, *, code=False):
    if code:
        return "".join(
            f"<li><code>{escape(value)}</code></li>" for value in values
        )
    return "".join(f"<li>{escape(value)}</li>" for value in values)


def tags(values):
    return "".join(
        f'<span class="tag">{escape(value)}</span>' for value in values
    )


def saved_design(value):
    if not value:
        return ""
    return f"<h3>Saved design</h3><p>{escape(value)}</p>"


def reference_notes(items):
    """Render preserved reference-note pairs without changing their text."""
    return "".join(
        "<li><strong>"
        + escape(name)
        + "</strong> — "
        + escape(note)
        + "</li>"
        for name, note in items
    )


def cheatsheet_link(slug, known_slugs):
    if slug not in known_slugs:
        return ""
    return (
        f'<p class="tip"><a href="../examples/{escape(slug)}/">'
        "View working example →</a></p>"
    )


def guide_sidebar(*, active=None, prefix=""):
    active_chapter = next(
        (chapter for chapter in GUIDES if chapter["slug"] == active),
        None,
    )

    def nav_link(slug, title):
        cls = ' class="active"' if slug == active else ""
        link = (
            f'<a{cls} href="{escape(prefix + slug + "/")}">'
            f"{escape(title)}</a>"
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
                    + "</div>"
                )
        return link

    overview_cls = ' class="active"' if active == "overview" else ""
    return (
        '<aside class="guide-sidebar">'
        "<h2>API Guide</h2>"
        f'<a{overview_cls} href="{escape(prefix or "./")}">Overview</a>'
        + "".join(
            nav_link(chapter["slug"], chapter["title"])
            for chapter in GUIDES
        )
        + "</aside>"
    )


def guide_shell(content, *, active, prefix):
    return (
        '<main class="wrap guide-layout">'
        + guide_sidebar(active=active, prefix=prefix)
        + '<article class="guide-article">'
        + content
        + "</article></main>"
    )


def member_details(member, *, compact=False):
    if member["kind"] == "enum":
        return (
            '<div class="guide-api-members">'
            + " · ".join(
                f'<code>{escape(member["name"])}.{escape(row["name"])}</code>'
                for row in member["members"]
            )
            + "</div>"
        )
    if member["kind"] == "constant":
        return (
            f'<p><code>{escape(member["name"])} = '
            f'{escape(member["value"])}</code></p>'
        )
    if member.get("signature"):
        css = ' class="guide-api-signature"' if compact else ""
        return f'<pre{css}><code>{escape(member["signature"])}</code></pre>'
    return ""


def parameter_details(member, *, heading="Parameters"):
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
        '<table class="api-table"><thead><tr>'
        "<th>Argument</th><th>Meaning</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def example_details(member):
    example = member.get("example") or ""
    if not example:
        return ""
    return "<h3>Example</h3>" + f"<pre><code>{escape(example)}</code></pre>"


def guide_group_details(spec):
    rows = []
    for member in group_members(spec):
        rows.append(
            f'<div class="guide-api-group-member" id="api-{escape(member["name"])}">'
            f'<h4><code>{escape(member["name"])}</code></h4>'
            + member_details(member, compact=True)
            + (
                f'<p>{escape(member["summary"])}</p>'
                if member["summary"] else ""
            )
            + (
                f'<p><strong>Use when:</strong> '
                f'{escape(member["use_when"])}</p>'
                if member["use_when"] else ""
            )
            + (
                f'<p><strong>Current limits:</strong> '
                f'{escape(member["limits"])}</p>'
                if member["limits"] else ""
            )
            + (
                f'<p><a href="../../reference/{escape(spec["slug"])}/'
                f'#{escape(member["name"])}">'
                "Detailed parameter reference →</a></p>"
                if member.get("parameters") else ""
            )
            + "</div>"
        )
    return '<div class="guide-api-group-members">' + "".join(rows) + "</div>"


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
                + "</div>"
            )
        elif spec["kind"] == "group":
            details = guide_group_details(spec)
        else:
            details = (
                '<pre class="guide-api-signature"><code>'
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
                f'<p><strong>Current limits:</strong> '
                f'{escape(spec["limits"])}</p>'
                if spec.get("limits") else ""
            )
            + "</article>"
        )
    return (
        '<section class="guide-api-summary">'
        "<h2>API on this page</h2>"
        '<p class="guide-api-intro">These values and signatures are generated '
        "from the current Python API. They are shown here so the normal guide "
        "flow does not require opening the reference for every detail.</p>"
        '<div class="guide-api-grid">' + "".join(cards) + "</div></section>"
    )


def guide_chapter_content(chapter):
    return (
        f'<p class="crumb"><a href="../">API Guide</a> / '
        f'{escape(chapter["title"])}</p>'
        f'<h1>{escape(chapter["title"])}</h1>'
        f'<p class="guide-lead">{escape(chapter["summary"])}</p>'
        + chapter["body"]
        + guide_api_summary(chapter["slug"])
    )


def guide_overview_content():
    return render_template("guide-overview.html")


def reference_sidebar(*, active=None, prefix=""):
    def nav_link(slug, title):
        cls = ' class="active"' if slug == active else ""
        link = (
            f'<a{cls} href="{escape(prefix + slug + "/")}">'
            f"{escape(title)}</a>"
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
                    + "</div>"
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
        "<h2>API Reference</h2>"
        f'<a{overview_cls} href="{escape(prefix or "./")}">Overview</a>'
        "<h3>Browse by task</h3>"
        + "".join(
            nav_link(spec["slug"], spec["title"])
            for spec in GROUP_REFERENCES
        )
        + "<h3>Selectors</h3>"
        + "".join(
            nav_link(spec["slug"], spec["title"])
            for spec in ENUM_REFERENCES
        )
        + "<h3>Components &amp; assemblies</h3>"
        + "".join(
            nav_link(spec["slug"], spec["title"])
            for spec in component_methods
        )
        + "<h3>Shape &amp; sketch</h3>"
        + "".join(
            nav_link(spec["slug"], spec["title"])
            for spec in shape_methods
        )
        + "</aside>"
    )


def reference_shell(content, *, active, prefix):
    return (
        '<main class="wrap reference-layout">'
        + reference_sidebar(active=active, prefix=prefix)
        + '<article class="reference-article">'
        + content
        + "</article></main>"
    )


def reference_enum_content(spec):
    slug = spec["slug"]
    rows = "".join(
        f'<tr id="{escape(slug + "." + name)}">'
        f"<td><code>{escape(slug)}.{escape(name)}</code></td>"
        f"<td><code>{escape(str(value))}</code></td>"
        "</tr>"
        for name, value in enum_members(spec)
    )
    return (
        '<p class="crumb"><a href="../">API Reference</a> / '
        + escape(spec["title"]) + "</p>"
        + '<section class="hero small">'
        '<p class="eyebrow">Generated SCPF API reference</p>'
        + f'<h1>{escape(spec["title"])}</h1>'
        f'<p>{escape(spec["summary"])}</p></section>'
        + '<section class="panel">'
        + (
            f'<h2>When to use it</h2><p>{escape(spec["use_when"])}</p>'
            if spec["use_when"] else ""
        )
        + "<h2>Members</h2>"
        '<table class="api-table"><thead><tr>'
        "<th>Name</th><th>Value</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        + (
            "<h2>Convenience aliases</h2><p>"
            + " · ".join(
                f"<code>{escape(name)}</code>" for name in anchor_aliases()
            )
            + "</p>"
            if spec["slug"] == "Anchor" else ""
        )
        + parameter_details(spec, heading="Parameters")
        + example_details(spec)
        + (
            f'<h2>Current limits</h2><p>{escape(spec["limits"])}</p>'
            if spec["limits"] else ""
        )
        + f'<p><a href="../../guide/{escape(spec["guide"])}/'
        f'#{escape(spec["guide_anchor"])}">'
        "Worked usage in the guide →</a> · "
        '<a href="../../api-design-contract.html">'
        "Cross-object API design rules →</a></p>"
        + "</section>"
    )


def reference_method_content(spec):
    return (
        '<p class="crumb"><a href="../">API Reference</a> / '
        + escape(spec["title"]) + "</p>"
        + '<section class="hero small">'
        '<p class="eyebrow">Generated SCPF API reference</p>'
        + f'<h1>{escape(spec["title"])}</h1>'
        f'<p>{escape(spec["summary"])}</p></section>'
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
        + f'<p><a href="../../guide/{escape(spec["guide"])}/'
        f'#{escape(spec["guide_anchor"])}">'
        "Worked usage in the guide →</a> · "
        '<a href="../../api-design-contract.html">'
        "Cross-object API design rules →</a></p>"
        + "</section>"
    )


def reference_group_content(spec):
    member_sections = []
    for member in group_members(spec):
        member_sections.append(
            f'<section class="panel api-group-member" '
            f'id="{escape(member["name"])}">'
            f'<h2><code>{escape(member["name"])}</code></h2>'
            + member_details(member)
            + (
                f'<p>{escape(member["summary"])}</p>'
                if member["summary"] else ""
            )
            + (
                f'<h3>When to use it</h3><p>'
                f'{escape(member["use_when"])}</p>'
                if member["use_when"] else ""
            )
            + parameter_details(member)
            + example_details(member)
            + (
                f'<h3>Current limits</h3><p>'
                f'{escape(member["limits"])}</p>'
                if member["limits"] else ""
            )
            + "</section>"
        )

    guide_link = (
        f'<p><a href="../../guide/{escape(spec["guide"])}/'
        f'#{escape(spec["guide_anchor"])}">'
        "Worked usage in the guide →</a> · "
        '<a href="../../api-design-contract.html">'
        "Cross-object API design rules →</a></p>"
        if spec.get("guide")
        else '<p><a href="../../api-design-contract.html">'
             "Cross-object API design rules →</a></p>"
    )
    return (
        '<p class="crumb"><a href="../">API Reference</a> / '
        + escape(spec["title"]) + "</p>"
        + '<section class="hero small">'
        '<p class="eyebrow">Generated SCPF API reference</p>'
        + f'<h1>{escape(spec["title"])}</h1>'
        f'<p>{escape(spec["summary"])}</p>'
        + guide_link
        + "</section>"
        + "".join(member_sections)
    )


_STATUS_CLASS = {
    "pass": "pass",
    "fail": "fail",
    "error": "fail",
    "review": "review",
    "blocked": "blocked",
    "incomplete": "incomplete",
    "missing": "incomplete",
    "not-required": "not-run",
    "skipped": "not-run",
}


def qualification_status_badge(status, label=None):
    """Render one public qualification status badge."""
    value = str(status or "missing").lower()
    css = _STATUS_CLASS.get(value, "incomplete")
    visible = label or value.replace("-", " ").upper()
    return (
        f'<span class="qualification-status {css}">'
        f'{escape(visible)}</span>'
    )


def qualification_status_line(summary):
    """Render current public check statuses without recomputing semantics."""
    checks = summary.get("checks") or {}
    labels = (
        ("integration", "Integration"),
        ("native_model", "Native model"),
        ("geometry", "Geometry"),
        ("saved_design", "Saved design"),
        ("visual", "Visual"),
    )
    parts = []
    for key, label in labels:
        row = checks.get(key) or {}
        status = row.get("status", "missing")
        if status == "not-required":
            text = f"{label} N/R"
        else:
            text = f"{label} {str(status).upper()}"
        parts.append(escape(text))
    return (
        '<div class="qualification-status-line">'
        + qualification_status_badge(summary.get("status"))
        + '<span class="qualification-levels">'
        + " · ".join(parts)
        + "</span></div>"
    )



def qualification_case_preview(view, title):
    """Render the primary native preview in the historical overview position."""
    url = view.get("preview_url")
    if not url:
        return ""
    return (
        '<figure class="qualification-case-preview">'
        f'<a href="{escape(url)}" class="qualification-image-link" '
        'target="_blank" rel="noopener" title="Open full-size native preview">'
        f'<img src="{escape(url)}" '
        f'alt="{escape(title)} native SolidCraft preview" loading="lazy">'
        "</a>"
        "<figcaption>Native SolidCraft preview from the accepted durable "
        "build output.</figcaption>"
        "</figure>"
    )


def qualification_setup_svg(view, title):
    """Render the historical conceptual front projection from declared targets."""
    bodies = view.get("expected_bodies") or ()
    if not bodies:
        return ""

    try:
        x_min = min(float(body["minimum"][0]) for body in bodies)
        x_max = max(float(body["maximum"][0]) for body in bodies)
        z_min = min(float(body["minimum"][2]) for body in bodies)
        z_max = max(float(body["maximum"][2]) for body in bodies)
    except (KeyError, IndexError, TypeError, ValueError):
        return ""

    x_span = max(x_max - x_min, 1.0)
    z_span = max(z_max - z_min, 1.0)
    pad = 42.0
    width = 640.0
    height = 360.0
    scale = min(
        (width - 2 * pad) / x_span,
        (height - 2 * pad) / z_span,
    )

    def sx(value):
        return pad + (float(value) - x_min) * scale

    def sy(value):
        return height - pad - (float(value) - z_min) * scale

    shapes = []
    for index, body in enumerate(bodies):
        minimum = body["minimum"]
        maximum = body["maximum"]
        x0 = sx(minimum[0])
        x1 = sx(maximum[0])
        y0 = sy(maximum[2])
        y1 = sy(minimum[2])
        fill = "#dce8f5" if index % 2 == 0 else "#e5f2ea"
        stroke = "#46627f" if index % 2 == 0 else "#47715d"
        shapes.append(
            f'<rect x="{x0:.1f}" y="{y0:.1f}" '
            f'width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
        )
        label = escape(body.get("label") or f"body {index + 1}")
        shapes.append(
            f'<text x="{x0 + 5:.1f}" y="{max(y0 + 17, 20):.1f}" '
            'font-family="system-ui,sans-serif" font-size="13" '
            f'fill="#26394f">{label}</text>'
        )

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 360" '
        f'role="img" aria-label="{escape(title)} expected setup schematic">'
        '<rect width="640" height="360" fill="#f8fafc"/>'
        '<text x="24" y="28" font-family="system-ui,sans-serif" '
        'font-size="16" font-weight="700" fill="#20344d">'
        "Expected setup — front projection</text>"
        '<text x="24" y="50" font-family="system-ui,sans-serif" '
        'font-size="12" fill="#60738a">'
        "Conceptual geometry only; verification renders appear later.</text>"
        + "".join(shapes)
        + "</svg>"
    )


def qualification_setup_diagram(title):
    """Render the historical setup-diagram figure around generated setup.svg."""
    return (
        '<figure class="qualification-setup-diagram">'
        '<a href="setup.svg" class="qualification-image-link" '
        'target="_blank" rel="noopener" title="Open full-size setup diagram">'
        f'<img src="setup.svg" alt="{escape(title)} expected setup diagram">'
        "</a>"
        "<figcaption>Expected setup — conceptual diagram, not verification "
        "output. Click for the full-size image.</figcaption>"
        "</figure>"
    )

def _evidence_table(headers, rows):
    """Render a small exact-value evidence table."""
    if not rows:
        return '<p class="meta">No rows.</p>'
    head = "".join(f"<th>{escape(value)}</th>" for value in headers)
    body = []
    for row in rows:
        body.append(
            "<tr>"
            + "".join(f"<td>{escape(value)}</td>" for value in row)
            + "</tr>"
        )
    return (
        '<div class="qualification-table-scroll"><table class="api-table">'
        f"<thead><tr>{head}</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table></div>"
    )


def _evidence_link(url, label):
    if not url:
        return ""
    return (
        f'<a href="{escape(url)}" target="_blank" rel="noopener">'
        f"{escape(label)}</a>"
    )


def qualification_current_evidence(
    view,
    title,
    *,
    forge_model="",
    saved_design_test="",
    bounds_sufficient="",
    geometry_reason="",
    reference_notes="",
):
    """Render stable results in the historical case-sheet information order."""
    parameters = _evidence_table(
        ("Parameter", "Value", "Unit", "Expression"),
        tuple(
            (
                row.get("name"),
                row.get("value"),
                row.get("unit"),
                row.get("expression"),
            )
            for row in view["parameters"]
        ),
    )
    bodies = _evidence_table(
        (
            "Body",
            "Minimum",
            "Maximum",
            "Volume mm³",
            "Faces",
            "Edges",
            "Closed",
        ),
        tuple(
            (
                row.get("name"),
                row.get("minimum"),
                row.get("maximum"),
                row.get("volume_mm3"),
                row.get("faces"),
                row.get("edges"),
                row.get("closed"),
            )
            for row in view["bodies"]
        ),
    )
    baseline_details = (
        '<details class="qualification-detail-block">'
        f'<summary><strong>Original model</strong> · '
        f'{len(view["bodies"])} bodies</summary>'
        "<h4>Editable parameters</h4>"
        + parameters
        + "<h4>Body size</h4>"
        + bodies
        + "</details>"
    )

    check_fragments = []
    for row in view["verification_checks"]:
        reason = (
            f"<p>{escape(row['reason'])}</p>"
            if row.get("reason")
            else ""
        )
        check_fragments.append(
            render_template(
                "qualification-check.html",
                check_id=escape(row.get("id")),
                status=qualification_status_badge(row.get("status")),
                reason=reason,
                evidence_json=escape(row.get("evidence_json")),
            )
        )

    saved = ""
    if view["saved_designs"]:
        details = []
        for row in view["saved_designs"]:
            details.append(
                '<details class="qualification-detail-block">'
                f'<summary>{escape(row["name"])}</summary>'
                f'<p>{_evidence_link(row["measurements_url"], "Open durable measurements")}</p>'
                f'<pre><code>{escape(row["measurements_json"])}</code></pre>'
                "</details>"
            )
        saved = "<h3>Saved-design results</h3>" + "".join(details)

    visual_rows = []
    for row in view["visual_views"]:
        image_fragments = []
        for label, key in (
            ("Actual", "actual_url"),
            ("Goal", "goal_url"),
            ("Overlay", "overlay_url"),
            ("Diff", "diff_url"),
        ):
            url = row.get(key)
            if not url:
                continue
            image_fragments.append(
                render_template(
                    "qualification-visual-image.html",
                    url=escape(url),
                    view=escape(row.get("view")),
                    label=escape(label),
                )
            )
        visual_rows.append(
            render_template(
                "qualification-visual-view.html",
                view=escape(row.get("view")),
                status=qualification_status_badge(row.get("status")),
                baseline_status=escape(row.get("baseline_status")),
                expected_shape_status=escape(row.get("expected_shape_status")),
                images="".join(image_fragments),
                regression_json=escape(row.get("regression_json")),
            )
        )

    if visual_rows:
        visual_section = render_template(
            "qualification-visual-section.html",
            views="".join(visual_rows),
        )
    else:
        visual_section = render_template(
            "qualification-visual-not-required.html"
        )

    raw_links = " · ".join(
        value
        for value in (
            _evidence_link(view["commands_url"], "commands"),
            _evidence_link(view["verification_url"], "verification"),
            _evidence_link(view["measurements_url"], "measurements"),
            _evidence_link(view["native_model_url"], "native .sc"),
            _evidence_link(view["native_step_url"], "STEP"),
            _evidence_link(view["native_results_url"], "native results"),
            _evidence_link(view["preview_metadata_url"], "preview metadata"),
        )
        if value
    )

    return render_template(
        "qualification-current.html",
        baseline_details=baseline_details,
        status_line=qualification_status_line(view),
        site_source_commit=escape(view["site_source_commit"]),
        accepted_source_commit=escape(view["accepted_source_commit"]),
        build_commit=escape(view["build_commit"]),
        verification_checks="".join(check_fragments),
        saved_designs=saved,
        raw_links=raw_links,
        visual_section=visual_section,
        forge_model=escape(forge_model),
        saved_design_test=escape(saved_design_test),
        bounds_sufficient=escape(bounds_sufficient),
        geometry_reason=escape(geometry_reason),
        reference_notes=reference_notes,
    )

def qualification_reference_comparison(
    reference_sources,
    source_urls,
    *,
    reference_rows=(),
):
    """Render reference source always and durable result evidence when available."""

    rows_by_implementation = {
        str(row.get("implementation", "")).lower(): row
        for row in reference_rows
    }
    fragments = []
    for implementation, source_code in reference_sources.items():
        key = str(implementation).lower()
        row = rows_by_implementation.get(key)
        source_link = _evidence_link(
            source_urls.get(key),
            "Open current reference source",
        )
        if row is None:
            fragments.append(
                render_template(
                    "verification-reference-source-row.html",
                    implementation=escape(implementation),
                    source_link=source_link,
                    source_code=escape(source_code),
                )
            )
            continue

        artifact_links = " · ".join(
            value
            for value in (
                _evidence_link(row.get("stl_url"), "STL"),
                _evidence_link(
                    row.get("verification_url"),
                    "verification JSON",
                ),
                _evidence_link(
                    row.get("preview_metadata_url"),
                    "preview metadata",
                ),
            )
            if value
        )
        fragments.append(
            render_template(
                "qualification-reference-row.html",
                implementation=escape(row["implementation"]),
                status=qualification_status_badge(row.get("status")),
                accepted_source_commit=escape(
                    row["accepted_source_commit"]
                ),
                accepted_source_link=_evidence_link(
                    row.get("source_url"),
                    "Open accepted source",
                ),
                source_link=source_link,
                source_code=escape(source_code),
                geometry_json=escape(row["geometry_json"]),
                preview_url=escape(row["preview_url"]),
                artifact_links=artifact_links,
            )
        )

    description = (
        "Each source is shown from the current Forge tree. Stable result "
        "evidence is unavailable in this source-only build."
        if not rows_by_implementation
        else
        "Each source is shown from the current Forge tree beside the accepted "
        "durable result for that independent implementation."
    )
    return render_template(
        "verification-references.html",
        description=escape(description),
        references="".join(fragments),
    )


def qualification_diagrams(rows):
    """Render current durable CADCraft diagrams."""
    diagrams = []
    for row in rows:
        diagrams.append(
            render_template(
                "qualification-diagram.html",
                svg_url=escape(row["svg_url"]),
                title=escape(row["title"]),
                cadcraft_version=escape(row.get("cadcraft_version")),
                svg_evidence_url=escape(row["svg_evidence_url"]),
            )
        )
    if not diagrams:
        return ""
    return render_template(
        "qualification-diagrams.html",
        diagrams="".join(diagrams),
    )


def qualification_card(info, view, case_url, *, section_label):
    """Render one stable verification catalog card."""
    return render_template(
        "qualification-card.html",
        case_url=escape(case_url),
        preview_url=escape(view["preview_url"]),
        title=escape(info.title),
        section=escape(section_label),
        status_line=qualification_status_line(view),
        description=escape(info.description),
    )
