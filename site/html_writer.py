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
