#!/usr/bin/env python3
"""Build a *library* API site from self-contained, regression-tested SCPF samples.

The complete mechanical CAD catalog belongs to 2026-011-02.cad.solidcraft.
This site deliberately contains only tiny fixtures and the SCPF cheatsheet.
"""
import argparse
import html
import json
from pathlib import Path
import re
import shutil
from string import Template
import sys

ROOT = Path(__file__).resolve().parents[1]

from scpf.runner import run_script
from scpf.version import TESTED_SOLIDCRAFT_VERSION
from guides import GUIDES
from api_coverage import EXPORT_COVERAGE, CAPABILITY_COVERAGE
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

sys.path.insert(0, str(ROOT))
try:
    from qualification.cases import (
        QUALIFICATION_CASES,
        QUALIFICATION_LEVELS,
        QUALIFICATION_GROUPS,
        REFERENCE_URLS,
    )
    from qualification.expectations import EXPECTED_VISUAL_BOXES
finally:
    sys.path.pop(0)

LIBRARY_URL = "https://github.com/brainboxemb/lib.py.solidcraft.forge"
CAD_SITE = "https://brainboxemb.github.io/2026-011-02.cad.solidcraft/"

# Keep the public catalog deliberately small; advanced tests remain in the repo.
EXAMPLES = {
    "simple-box": {
        "title": "1 · Simple box",
        "description": "A plain Python class with three dimensions and one Box.",
        "concepts": ["Box", "build()", "parameters"],
    },
    "anchored-holes": {
        "title": "2 · Two holes",
        "description": "An explicit rectangle Sketch extrusion and two patterned through-holes.",
        "concepts": ["Sketch", "Rectangle2D", "extrude", "Hole", "pattern", "attach"],
    },
    "components": {
        "title": "3 · Reuse a component",
        "description": "Two instances of one Block definition, placed relative to meaningful component references.",
        "concepts": ["component", "occurrence", "Anchor", "attach"],
    },
    "corner-anchor": {
        "title": "4 · Associative corner anchor",
        "description": "Attach one reusable component to a named corner that follows parent size changes.",
        "concepts": ["Anchor", "attach", "corner", "associative placement"],
    },
    "custom-anchor": {
        "title": "5 · Named attachment frame",
        "description": "Expose a named local AnchorFrame from a component when the datum belongs to that reusable part.",
        "concepts": ["AnchorFrame", "anchors()", "attach", "named datum"],
    },
}

CHEATSHEET = [
    ("Model classes", [
        ("class Example: ... build(self)", "Write a Python model. No main() or show() is required.",
         "class SimpleBox:\n    def build(self):\n        return Box(40, 30, 10)", "simple-box"),
        ("Model parameters", "Numeric model fields become named SolidCraft parameters.",
         "length = 40.0\nBox(self.length, 30, 10)", "simple-box"),
    ]),
    ("Shapes and sketches", [
        ("Box(length, width, height)", "Solid, centered in XY; its bottom is at Z=0.",
         "Box(40, 30, 10)", "simple-box"),
        ("Rectangle2D(width, depth)", "Planar XY profile authored inside a Sketch.",
         "with Sketch(plane='XY') as sketch:\n    Rectangle2D(100, 60)", "anchored-holes"),
        ("Circle2D(d=...)", "A round 2D profile authored inside a Sketch.",
         "with Sketch(plane='XY') as sketch:\n    Circle2D(d=8)", None),
        ("Polygon2D(points, plane=...)", "A closed profile on XY, XZ or YZ.",
         "Polygon2D([(0,0), (40,0), (0,30)], plane='XZ')", None),
        ("Cylinder(d=..., h=..., axis=...)", "Direct native cylinder on Axis.X, Axis.Y or Axis.Z, with its base at the placement point.",
         "Cylinder(d=24, h=14, axis=Axis.X).at(-7, 0, 0)", None),
    ]),
    ("Features and placement", [
        ("sketch.extrude(distance)", "Extrude an explicitly authored Sketch into editable native solid history.",
         "with Sketch(plane='XY') as sketch:\n    Rectangle2D(80, 50)\nplate = sketch.extrude(8)", "anchored-holes"),
        ("Hole(d=..., depth=...)", "A native hole. THROUGH_ALL follows the target body.",
         "Hole(d=8, depth=Depth.THROUGH_ALL)", "anchored-holes"),
        ("shape.at(target, anchor=..., child=...)", "Place a direct CSG shape anchor on another shape anchor; CENTER-to-CENTER is supported first.",
         "Cylinder(d=8, h=50, axis=Axis.X).at(body)", "primitive-csg"),
        ("shape.on(target, face=...)", "Place a feature on a selected face of another shape.",
         "Hole(d=8, depth=Depth.THROUGH_ALL).on(plate, face=Faces.TOP)", "anchored-holes"),
        ("shape.pattern(...)", "Repeat a supported feature before placing it on its parent shape.",
         "Hole(d=8, depth=Depth.THROUGH_ALL).pattern(count=2, spacing=40, axis=Axis.Y)", "anchored-holes"),
        ("TOP + LEFT / BOTTOM + RIGHT", "Combine cardinal directions to identify one edge of an axis-aligned rectangular solid.",
         "body.fillet(2, edges=[BOTTOM + LEFT, BOTTOM + RIGHT])", None),
        ("Box(...).at(..., anchor=...)", "Place a native Box by a face, edge or corner anchor without creating a Sketch.",
         "Box(80, 50, 12).at(0, 0, 0, anchor=FRONT + BOTTOM)", None),
        ("shape.fillet(...)", "Round selected edges of a feature-based body.",
         "body.fillet(2, edges=Edges.VERTICAL)", None),
        ("shape.shell(...)", "Create an open-sided shell (supported feature trees only).",
         "Box(80, 50, 30).shell(2, open=Faces.TOP)", None),
        ("a + b / a - b / a & b", "Join, cut or intersect supported shapes; operation support depends on the shape types.",
         "body + Hole(d=8).at(0, 0, 10)", None),
    ]),
    ("Reusable components", [
        ("model.copy().move(x=...)", "Copy an occurrence of one definition; preserve editable feature history.",
         "second = first.copy().move(x=40)", "components"),
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
        ("model.rotate(axis=..., degrees=...)", "Orient a native occurrence; rotation does not alter the shared component.",
         "second = first.copy().move(x=40).rotate(axis=(0,0,1), degrees=180)", None),
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


# A deliberately simple, labelled fallback for local/offline site builds.
# Production GitHub Pages uses real native SolidCraft snapshots from CI.
SCHEMATICS = {
  "simple-box": "<path d=\"M95 76 231 30 368 81 232 129Z\" fill=\"#bad8f2\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<path d=\"M95 76 232 129 V222 L95 168Z\" fill=\"#729eca\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<path d=\"M232 129 368 81 V169 L232 222Z\" fill=\"#91badf\" stroke=\"#31577c\" stroke-width=\"4\"/>",
  "anchored-holes": "<path d=\"M68 116 286 42 430 104 207 189Z\" fill=\"#bbd9f1\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<path d=\"M68 116 V143 L207 216 V189Z\" fill=\"#6f9fc9\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<path d=\"M207 189 430 104 V131 L207 216Z\" fill=\"#8bb8dc\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<ellipse cx=\"175\" cy=\"111\" rx=\"18\" ry=\"10\" fill=\"#f6faff\" stroke=\"#31577c\" stroke-width=\"3\"/>\n<ellipse cx=\"321\" cy=\"117\" rx=\"18\" ry=\"10\" fill=\"#f6faff\" stroke=\"#31577c\" stroke-width=\"3\"/>",
  "components": "<path d=\"M50 113 137 83 223 113 136 143Z\" fill=\"#bad8f2\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<path d=\"M50 113 V183 L136 212 V143Z\" fill=\"#729eca\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<path d=\"M136 143 223 113 V183 L136 212Z\" fill=\"#91badf\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<path d=\"M238 113 325 83 412 113 325 143Z\" fill=\"#b9d6f2\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<path d=\"M238 113 V183 L325 212 V143Z\" fill=\"#729eca\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<path d=\"M325 143 412 113 V183 L325 212Z\" fill=\"#91badf\" stroke=\"#31577c\" stroke-width=\"4\"/>",
  "corner-anchor": "<path d=\"M78 142 250 84 410 142 238 204Z\" fill=\"#bad8f2\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<path d=\"M78 142 V190 L238 246 V204Z\" fill=\"#729eca\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<path d=\"M238 204 410 142 V190 L238 246Z\" fill=\"#91badf\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<path d=\"M380 90 425 75 462 88 417 104Z\" fill=\"#d9e7f5\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<circle cx=\"410\" cy=\"142\" r=\"8\" fill=\"#ffffff\" stroke=\"#31577c\" stroke-width=\"3\"/>",
  "custom-anchor": "<path d=\"M210 35 245 47 245 215 210 203Z\" fill=\"#91badf\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<path d=\"M210 35 280 12 315 24 245 47Z\" fill=\"#bad8f2\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<path d=\"M245 47 315 24 315 192 245 215Z\" fill=\"#729eca\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<path d=\"M196 210 225 200 254 210 225 220Z\" fill=\"#d9e7f5\" stroke=\"#31577c\" stroke-width=\"4\"/>\n<circle cx=\"225\" cy=\"200\" r=\"7\" fill=\"#fff\" stroke=\"#31577c\" stroke-width=\"3\"/>"
}


def schematic(slug):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 260" '
        'role="img" aria-label="Schematic preview; not a SolidCraft render">'
        + SCHEMATICS[slug] + '</svg>'
    )


def expected_setup_schematic(slug):
    bodies = EXPECTED_VISUAL_BOXES.get(slug, [])
    if not bodies:
        return ""

    x_min = min(float(body["min"][0]) for body in bodies)
    x_max = max(float(body["max"][0]) for body in bodies)
    z_min = min(float(body["min"][2]) for body in bodies)
    z_max = max(float(body["max"][2]) for body in bodies)

    x_span = max(x_max - x_min, 1.0)
    z_span = max(z_max - z_min, 1.0)
    pad = 42.0
    width = 640.0
    height = 360.0
    scale = min((width - 2 * pad) / x_span, (height - 2 * pad) / z_span)

    def sx(value):
        return pad + (float(value) - x_min) * scale

    def sy(value):
        return height - pad - (float(value) - z_min) * scale

    shapes = []
    for index, body in enumerate(bodies):
        x0 = sx(body["min"][0])
        x1 = sx(body["max"][0])
        y0 = sy(body["max"][2])
        y1 = sy(body["min"][2])
        fill = "#dce8f5" if index % 2 == 0 else "#e5f2ea"
        stroke = "#46627f" if index % 2 == 0 else "#47715d"
        shapes.append(
            f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1-x0:.1f}" height="{y1-y0:.1f}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
        )
        label = escape(body.get("label", f"body {index + 1}"))
        shapes.append(
            f'<text x="{x0 + 5:.1f}" y="{max(y0 + 17, 20):.1f}" '
            f'font-family="system-ui,sans-serif" font-size="13" fill="#26394f">{label}</text>'
        )

    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 360" '
        'role="img" aria-label="Expected setup schematic; not a SolidCraft render">'
        '<rect width="640" height="360" fill="#f8fafc"/>'
        '<text x="24" y="28" font-family="system-ui,sans-serif" font-size="16" '
        'font-weight="700" fill="#20344d">Expected setup — front projection</text>'
        '<text x="24" y="50" font-family="system-ui,sans-serif" font-size="12" '
        'fill="#60738a">Conceptual geometry only; verification renders appear later.</text>'
        + "".join(shapes)
        + '</svg>'
    )


def escape(value):
    return html.escape(str(value), quote=True)


def _format_vector(values):
    return "[" + ", ".join(f"{float(value):g}" for value in values) + "]"


def _qualification_status(result):
    labels = {
        "pass": "PASS",
        "fail": "FAIL",
        "review": "REVIEW",
        "incomplete": "INCOMPLETE",
        "missing": "MISSING",
        "not-required": "N/R",
    }
    details = []
    for name in ("q1", "q2", "q3", "q4", "q5", "q6"):
        state = result.get("levels", {}).get(name, {}).get("status", "missing")
        q = name.upper()
        if state == "pass":
            details.append(q)
        elif state == "not-required":
            details.append(f"{q} N/R")
        else:
            details.append(f"{q} {labels.get(state, state.upper())}")
    overall_state = result.get("status", "incomplete")
    return labels.get(overall_state, overall_state.upper()), " · ".join(details)


def _qualification_status_html(overall, detail):
    status_class = {
        "PASS": "pass",
        "FAIL": "fail",
        "REVIEW": "review",
        "INCOMPLETE": "incomplete",
        "NOT RUN": "not-run",
    }.get(overall, "incomplete")
    return (
        '<div class="qualification-status-line">'
        f'<span class="qualification-status {status_class}">{escape(overall)}</span>'
        f'<span class="qualification-levels">{escape(detail)}</span>'
        '</div>'
    )


def _image_sort_key(name):
    if name == "model.png":
        return (0, "", 0)
    for view_index, view in enumerate(("front", "right", "iso"), 1):
        order = {
            f"model-{view}.png": 0,
            f"goal-{view}.png": 1,
            f"overlay-{view}.png": 2,
            f"visual-diff-{view}.png": 3,
        }
        if name in order:
            return (view_index, view, order[name])
    return (10, name, 0)


def _visual_view_html(case, view, native_images):
    names = [
        (f"model-{view}.png", "Actual", f"Current SolidCraft {view} view"),
        (f"goal-{view}.png", "Goal", f"Expected geometry in the same {view} view"),
        (f"overlay-{view}.png", "Overlay", f"Expected geometry over the actual {view} view"),
    ]
    figures = []
    for name, label, caption in names:
        if name not in native_images:
            continue
        figures.append(
            '<figure class="qualification-visual-item">'
            f'<a href="{escape(name)}" class="qualification-image-link" target="_blank" rel="noopener" '
            f'title="Open full-size {escape(label)} image">'
            f'<img src="{escape(name)}" '
            f'alt="{escape(case["title"])} {escape(view)} {escape(label)}" loading="lazy">'
            '</a>'
            f'<figcaption><strong>{escape(label)}</strong><br>{escape(caption)}</figcaption>'
            '</figure>'
        )
    if not figures:
        return ""
    return (
        f'<section class="qualification-view" data-view="{escape(view)}">'
        f'<h3>{escape(view.title())}</h3>'
        '<div class="qualification-view-grid">'
        + "".join(figures)
        + '</div></section>'
    )


def _render_visual_evidence(case, native_images):
    iso = _visual_view_html(case, "iso", native_images)
    additional = "".join(
        _visual_view_html(case, view, native_images)
        for view in ("front", "right")
    )
    if not iso and not additional:
        return ""
    extra = (
        '<details class="qualification-extra-views">'
        '<summary>Additional front/right views</summary>'
        + additional
        + '</details>'
        if additional else ""
    )
    return (
        '<section class="panel qualification-visual-check">'
        '<h2>5. Visual verification</h2>'
        '<p class="meta">Actual is the current SolidCraft result. Goal is the independent expected geometry. '
        'Overlay shows both together. Click any image for the full-size PNG.</p>'
        + iso + extra +
        '</section>'
    )


def _image_caption(name):
    if name == "model.png":
        return "Native baseline render."
    for view in ("front", "right", "iso"):
        if name == f"model-{view}.png":
            return f"Actual SolidCraft {view} view."
        if name == f"goal-{view}.png":
            return f"Expected/goal geometry in the same {view} camera."
        if name == f"overlay-{view}.png":
            return f"Actual {view} render with expected geometry overlaid."
        if name == f"visual-diff-{view}.png":
            return f"Visual regression diff for the {view} view."
    return f"Additional native evidence: {name}."


def _render_validation_checks(native_case):
    path = native_case / "validation.json"
    if not path.is_file():
        return ""
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for check in data.get("checks", []):
        status = check.get("status", "missing").upper()
        cls = "pass" if status == "PASS" else "fail"
        expected = json.dumps(check.get("expected"), ensure_ascii=False)
        actual = json.dumps(check.get("actual"), ensure_ascii=False)
        rows.append(
            "<tr>"
            f"<td><span class=\"qualification-status {cls}\">{escape(status)}</span></td>"
            f"<td>{escape(check.get('level', '').upper())}</td>"
            f"<td>{escape(check.get('name'))}</td>"
            f"<td><code>{escape(expected)}</code></td>"
            f"<td><code>{escape(actual)}</code></td>"
            "</tr>"
        )
    if not rows:
        return ""
    return (
        '<h3>Semantic validation</h3>'
        '<table class="qualification-checks"><thead><tr>'
        '<th>Status</th><th>Level</th><th>Check</th><th>Expected</th><th>Actual</th>'
        '</tr></thead><tbody>' + "".join(rows) + "</tbody></table>"
    )


def _render_native_results(native_case, solidcraft_version):
    measurement_files = sorted(native_case.glob("measurements*.json"))
    if not measurement_files:
        return (
            '<section class="panel"><h2>4. Machine verification</h2>'
            '<p>No measurement JSON was produced.</p></section>',
            None,
            None,
        )

    sections = []
    baseline_body_count = None
    baseline_parameter_count = None

    for measurement in measurement_files:
        data = json.loads(measurement.read_text(encoding="utf-8"))
        label = (
            "Baseline"
            if measurement.name == "measurements.json"
            else measurement.stem.replace("measurements-", "").replace("-", " ")
        )

        bodies = data.get("bodies", [])
        params = data.get("params", [])
        if measurement.name == "measurements.json":
            baseline_body_count = data.get("body_count", len(bodies))
            baseline_parameter_count = len(params)

        parameter_rows = "".join(
            f"<tr><td><code>{escape(row.get('name'))}</code></td>"
            f"<td>{escape(row.get('value'))}</td></tr>"
            for row in params
        )
        parameter_table = (
            '<h4>Parameters</h4><table><thead><tr><th>Name</th><th>Value</th>'
            f'</tr></thead><tbody>{parameter_rows}</tbody></table>'
            if parameter_rows else "<p>No editable parameters in this result.</p>"
        )

        body_rows = "".join(
            f"<tr><td>{escape(body.get('name'))}</td>"
            f"<td><code>{escape(_format_vector(body['bbox']['min']))}</code></td>"
            f"<td><code>{escape(_format_vector(body['bbox']['max']))}</code></td></tr>"
            for body in bodies
            if body.get("bbox")
        )
        body_table = (
            '<h4>Bodies</h4><table><thead><tr><th>Body</th><th>BBox min</th>'
            f'<th>BBox max</th></tr></thead><tbody>{body_rows}</tbody></table>'
            if body_rows else "<p>No body measurements in this result.</p>"
        )

        sections.append(
            f'<details{" open" if measurement.name == "measurements.json" else ""}>'
            f'<summary><strong>{escape(label)}</strong> · '
            f'{escape(data.get("body_count", len(bodies)))} bodies · '
            f'<a href="{escape(measurement.name)}">{escape(measurement.name)}</a>'
            f'</summary>{parameter_table}{body_table}</details>'
        )

    return (
        '<section class="panel"><h2>4. Machine verification</h2>'
        f'<p class="meta">Native runtime: <strong>SolidCraft '
        f'{escape(solidcraft_version)}</strong>. These values come from the '
        'saved native design, not from Python-side estimates.</p>'
        + "".join(sections)
        + _render_validation_checks(native_case)
        + "</section>",
        baseline_body_count,
        baseline_parameter_count,
    )


COPY_SCRIPT = r"""(() => {
  const copyIcon = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="11" height="11" rx="2"></rect><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"></path></svg>';
  const doneIcon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6"></path></svg>';

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const helper = document.createElement('textarea');
    helper.value = text;
    helper.setAttribute('readonly', '');
    helper.style.position = 'fixed';
    helper.style.opacity = '0';
    document.body.appendChild(helper);
    helper.select();
    document.execCommand('copy');
    helper.remove();
  }

  document.querySelectorAll('pre > code').forEach((code) => {
    const pre = code.parentElement;
    if (!pre || pre.parentElement?.classList.contains('code-block')) return;

    const wrapper = document.createElement('div');
    wrapper.className = 'code-block';
    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(pre);

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'code-copy';
    button.title = 'Copy code';
    button.setAttribute('aria-label', 'Copy code');
    button.innerHTML = copyIcon;
    wrapper.appendChild(button);

    button.addEventListener('click', async () => {
      try {
        await copyText(code.textContent);
        button.innerHTML = doneIcon;
        button.classList.add('copied');
        button.title = 'Copied';
        button.setAttribute('aria-label', 'Copied');
        window.setTimeout(() => {
          button.innerHTML = copyIcon;
          button.classList.remove('copied');
          button.title = 'Copy code';
          button.setAttribute('aria-label', 'Copy code');
        }, 1400);
      } catch (_error) {
        button.title = 'Copy failed';
        button.setAttribute('aria-label', 'Copy failed');
      }
    });
  });
})();
"""


def page(title, body, *, stylesheet, home, cheatsheet):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>{escape(title)} · SCPF Python library</title>
<link rel="stylesheet" href="{escape(stylesheet)}"></head>
<body><header class="top"><div class="wrap nav">
<a class="brand" href="{escape(home)}">SCPF <span>Python library</span></a>
<nav aria-label="Main"><a href="{escape(home)}">Examples</a><a href="{escape(home)}guide/">API Guide</a><a href="{escape(home)}reference/">API Reference</a><a href="{escape(home)}qualification/">Qualification</a><a href="{escape(cheatsheet)}">Cheatsheet</a>\n<a href="{LIBRARY_URL}">Source</a></nav></div></header>
<div class="development-banner" role="status"><div class="wrap">
<strong>Development version.</strong> Forge is under active development and testing. APIs, behaviour, coverage and qualification results may be incomplete or change without notice; published PASS results are not a support guarantee or production-readiness claim.
</div></div>
{body}
<footer><div class="wrap"><strong>SCPF</strong> generates commands; native SolidCraft creates the geometry.
<a href="{CAD_SITE}">Full SolidCraft CAD projects →</a></div></footer>
<script>{COPY_SCRIPT}</script>
</body></html>"""


def text(path):
    return path.read_text(encoding="utf-8")


def render_template(name, **values):
    template_path = ROOT / "qualification" / "templates" / name
    return Template(text(template_path)).substitute(values)


def build(out, sha, native_root=None, diagram_root=None, reference_evidence_root=None):
    """Compile the public examples and attach verified native screenshots if available.

    A .png is accepted only when the native verification file identifies the
    exact source SHA and the expected SolidCraft runtime. Outside native CI,
    emit plainly labelled SVG schematics rather than pretending a render.
    """
    verified = False
    metadata = {}
    if native_root is not None:
        meta_file = native_root / "verification.json"
        if not meta_file.is_file():
            raise ValueError("Native directory is missing verification.json")
        metadata = json.loads(meta_file.read_text(encoding="utf-8"))
        verified = (metadata.get("source_commit") == sha
                    and metadata.get("verified") is True
                    and metadata.get("solidcraft_version") == TESTED_SOLIDCRAFT_VERSION)
        if not verified:
            raise ValueError("Native screenshots do not match this source commit")

    reference_verified = False
    reference_summary = {}
    if reference_evidence_root is not None:
        summary_file = reference_evidence_root / "summary.json"
        if not summary_file.is_file():
            raise ValueError("Reference directory is missing summary.json")
        reference_summary = json.loads(summary_file.read_text(encoding="utf-8"))
        reference_verified = reference_summary.get("source_commit") == sha
        if not reference_verified:
            raise ValueError("Reference renders do not match this source commit")

    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "site" / "style.css", out / "style.css")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    cards = []
    manifest = {"library_commit": sha, "qualifier": "command-generation", "examples": {}}
    for slug, info in EXAMPLES.items():
        source_path = ROOT / "examples" / slug / "scpf" / "model.py"
        commands = run_script(source_path)
        assert commands.get("commands"), f"{slug}: empty command list"
        dest = out / "examples" / slug
        dest.mkdir(parents=True, exist_ok=True)
        source = text(source_path)
        (dest / "model.py").write_text(source, encoding="utf-8")
        (dest / "commands.json").write_text(json.dumps(commands, indent=2) + "\n", encoding="utf-8")
        count = len(commands["commands"])
        screenshot = native_root / slug / "model.png" if verified else None
        if screenshot is not None:
            if not screenshot.is_file() or screenshot.stat().st_size == 0:
                raise ValueError(f"Native screenshot missing or empty: {screenshot}")
            shutil.copyfile(screenshot, dest / "preview.png")
            preview_path = "preview.png"
            preview_kind = "native-snapshot"
            preview_caption = (
                f"Native SolidCraft {TESTED_SOLIDCRAFT_VERSION} render, "
                "verified against this source commit."
            )
        else:
            (dest / "preview.svg").write_text(schematic(slug), encoding="utf-8")
            preview_path = "preview.svg"
            preview_kind = "schematic"
            preview_caption = "Schematic illustration only; run the native CI job for a SolidCraft render."
        manifest["examples"][slug] = {"source": f"examples/{slug}/model.py",
                                      "commands": f"examples/{slug}/commands.json",
                                      "command_count": count,
                                      "preview": f"examples/{slug}/{preview_path}",
                                      "preview_kind": preview_kind}
        kinds = [row["command"] for row in commands["commands"]]
        timeline = "".join(f"<li><code>{escape(kind)}</code></li>" for kind in kinds)
        source_url = f"{LIBRARY_URL}/blob/main/examples/{slug}/scpf/model.py"
        body = f"""<main class="wrap"><div class="crumb"><a href="../../">← Examples</a> / {escape(info['title'])}</div>
<section class="hero small"><p class="eyebrow">Small API regression fixture</p>
<h1>{escape(info['title'])}</h1><p>{escape(info['description'])}</p>
<p class="meta"><span>Compiled: {count} native commands</span><span>{escape(preview_caption)}</span></p></section>
<figure class="example-image"><img src="{preview_path}" alt="{escape(info['title'])}: {escape(preview_caption)}" loading="lazy">
<figcaption>{escape(preview_caption)}</figcaption></figure>
<div class="twocol"><section class="panel"><h2>Python source</h2><pre><code>{escape(source)}</code></pre>
<a href="{escape(source_url)}">Open the editable source in GitHub →</a></section>
<section class="panel"><h2>Generated command sequence</h2><ol class="commands">{timeline}</ol>
<p><a class="button" href="commands.json">View command JSON →</a></p></section></div>
<section class="notice">The generated JSON is automatically rebuilt and checked by CI for every relevant change.
These examples are API smoke tests, not substitutes for a full mechanical CAD project or a native geometry certification.</section>
<p><a href="../../cheatsheet/">Related SCPF syntax in the cheatsheet →</a></p></main>"""
        (dest / "index.html").write_text(
            page(info["title"], body, stylesheet="../../style.css", home="../../", cheatsheet="../../cheatsheet/"),
            encoding="utf-8")
        tags = "".join(f'<span class="tag">{escape(x)}</span>' for x in info["concepts"])
        cards.append(f"""<article class="card"><a href="examples/{slug}/" class="card-image" aria-label="View {escape(info['title'])}"><img src="examples/{slug}/{preview_path}" alt="{escape(info['title'])} preview" loading="lazy"></a><div class="card-content"><p class="eyebrow">Regression example</p>
<h2><a href="examples/{slug}/">{escape(info['title'])}</a></h2>
<p>{escape(info['description'])}</p><div class="tags">{tags}</div>
<p class="meta">{count} generated SolidCraft commands</p>
<a class="button" href="examples/{slug}/">View source and command steps →</a></div></article>""")

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
            "<tr>"
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

    contract_source = (ROOT / "docs" / "05-cad-api-design.md").read_text(encoding="utf-8")
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

    # Qualification pages explain the full contract for each native fixture:
    # public API -> Forge model -> SolidCraft commands -> native evidence.
    qualification_root = out / "qualification"
    qualification_root.mkdir(exist_ok=True)
    qualification_cards = {key: [] for key, _, _ in QUALIFICATION_GROUPS}
    qualification_manifest = {}

    for case in QUALIFICATION_CASES:
        slug = case["slug"]
        source_path = ROOT / "examples" / slug / "scpf" / "model.py"
        commands = run_script(source_path)
        case_dir = qualification_root / slug
        case_dir.mkdir(exist_ok=True)
        source = text(source_path)
        (case_dir / "model.py").write_text(source, encoding="utf-8")

        reference_sources = {}
        for reference_name in ("pythonscad", "pybosl2"):
            reference_path = (
                ROOT / "examples" / slug / reference_name / "model.py"
            )
            if not reference_path.is_file():
                raise ValueError(
                    f"Qualification reference missing: {reference_path}"
                )
            reference_source = text(reference_path)
            try:
                compile(reference_source, str(reference_path), "exec")
            except SyntaxError as exc:
                raise ValueError(
                    f"Invalid {reference_name} reference syntax: {reference_path}"
                ) from exc
            reference_sources[reference_name] = reference_source
            (case_dir / f"reference-{reference_name}.py").write_text(
                reference_source,
                encoding="utf-8",
            )

        reference_evidence_html = (
            '<div class="notice">Executable reference renders were not supplied '
            'to this site build. The source comparisons remain available.</div>'
        )
        reference_evidence_files = []
        if reference_verified:
            reference_render_cards = []
            for reference_name in ("pythonscad", "pybosl2"):
                result_path = (
                    reference_evidence_root / slug / reference_name / "result.json"
                )
                if not result_path.is_file():
                    raise ValueError(f"Reference result missing: {result_path}")
                result = json.loads(result_path.read_text(encoding="utf-8"))
                if result.get("status") != "pass":
                    raise ValueError(
                        f"Reference result is not PASS: {slug}/{reference_name}"
                    )
                dest = case_dir / f"reference-{reference_name}"
                dest.mkdir(exist_ok=True)
                source_dir = result_path.parent
                for name in (
                    "result.json",
                    "model.stl",
                    "model-front.png",
                    "model-right.png",
                    "model-iso.png",
                ):
                    source_file = source_dir / name
                    if not source_file.is_file() or source_file.stat().st_size == 0:
                        raise ValueError(
                            f"Reference evidence missing or empty: {source_file}"
                        )
                    shutil.copyfile(source_file, dest / name)
                    reference_evidence_files.append(
                        f"reference-{reference_name}/{name}"
                    )
                label = "PythonSCAD" if reference_name == "pythonscad" else "pyBOSL2"
                reference_render_cards.append(
                    '<figure class="qualification-reference-preview">'
                    f'<a href="reference-{reference_name}/model-iso.png" '
                    'class="qualification-image-link" target="_blank" rel="noopener">'
                    f'<img src="reference-{reference_name}/model-iso.png" '
                    f'alt="{escape(case["title"])} {label} reference render">'
                    '</a>'
                    f'<figcaption><strong>{label}</strong> · independently exported STL · '
                    f'max bounds delta {escape(result.get("max_delta_mm"))} mm</figcaption>'
                    '</figure>'
                )
            reference_evidence_html = (
                '<div class="twocol qualification-reference-renders">'
                + "".join(reference_render_cards)
                + '</div>'
            )

        diagram_html = ""
        diagram_name = case.get("diagram")
        plan_name = None
        dxf_name = None
        if diagram_name:
            diagram_source = (
                diagram_root / diagram_name
                if diagram_root is not None
                else ROOT / "qualification" / "diagrams" / diagram_name
            )
            if not diagram_source.is_file():
                raise ValueError(f"Qualification diagram missing: {diagram_source}")
            shutil.copyfile(diagram_source, case_dir / diagram_name)
            dxf_source = diagram_source.with_suffix(".dxf")
            if dxf_source.is_file():
                dxf_name = dxf_source.name
                shutil.copyfile(dxf_source, case_dir / dxf_name)
            plan_source = ROOT / "qualification" / "diagrams" / f"{slug}.cadcraft.json"
            if plan_source.is_file():
                plan_name = plan_source.name
                shutil.copyfile(plan_source, case_dir / plan_name)
        else:
            diagram_name = "setup.svg"
            setup_svg = expected_setup_schematic(slug)
            if setup_svg:
                (case_dir / diagram_name).write_text(setup_svg, encoding="utf-8")
            else:
                diagram_name = None

        if diagram_name:
            if plan_name:
                source_links = (
                    f' <a href="{escape(plan_name)}">CadCraft source</a>'
                    + (f' · <a href="{escape(dxf_name)}">DXF</a>' if dxf_name else "")
                )
                caption = (
                    "Expected setup — technical drawing generated from the committed "
                    "CadCraft command source; not verification output."
                    + source_links
                )
            else:
                caption = (
                    "Expected setup — conceptual diagram, not verification output. "
                    "Click for the full-size image."
                )
            diagram_html = (
                '<figure class="qualification-setup-diagram">'
                f'<a href="{escape(diagram_name)}" class="qualification-image-link" '
                'target="_blank" rel="noopener" title="Open full-size setup diagram">'
                f'<img src="{escape(diagram_name)}" alt="{escape(case["title"])} expected setup diagram">'
                '</a>'
                f'<figcaption>{caption}</figcaption>'
                '</figure>'
            )
        (case_dir / "commands.json").write_text(
            json.dumps(commands, indent=2) + "\n",
            encoding="utf-8",
        )

        joint_commands = [
            command for command in commands["commands"]
            if command["command"].startswith("joint.")
        ]
        lowering_detail = (
            json.dumps(joint_commands, indent=2)
            if joint_commands
            else "\n".join(command["command"] for command in commands["commands"])
        )

        native_case = native_root / slug if verified else None
        native_files = []
        native_images = []
        qualification_result = None
        body_count = None
        parameter_count = None
        results_html = (
            '<section class="panel"><h2>3. Results</h2>'
            '<div class="notice">Native result data was not supplied to this '
            'site build. Run the native qualification for measured results.</div>'
            '</section>'
        )
        preview_html = (
            '<div class="notice">No source-matched native verification was supplied '
            'to this site build. The case sheet and command contract are still shown.</div>'
        )
        case_preview_html = ""
        status = "NOT RUN"
        status_detail = "Q1 Q2 documented"
        if native_case is not None and native_case.is_dir():
            result_file = native_case / "qualification-result.json"
            if not result_file.is_file():
                raise ValueError(f"Structured qualification result missing: {result_file}")
            qualification_result = json.loads(result_file.read_text(encoding="utf-8"))
            if (
                qualification_result.get("source_commit") != sha
                or qualification_result.get("solidcraft_version") != metadata.get("solidcraft_version")
            ):
                raise ValueError(f"Qualification result does not match this build: {result_file}")
            snapshot = native_case / "model.png"
            if not snapshot.is_file() or snapshot.stat().st_size == 0:
                raise ValueError(f"Qualification snapshot missing or empty: {snapshot}")

            image_paths = sorted(
                native_case.glob("*.png"),
                key=lambda path: _image_sort_key(path.name),
            )
            for image in image_paths:
                if image.stat().st_size == 0:
                    raise ValueError(f"Qualification snapshot empty: {image}")
                shutil.copyfile(image, case_dir / image.name)
                native_images.append(image.name)

            for pattern in (
                "results*.json",
                "measurements*.json",
                "change-*.json",
                "parameters*.json",
                "joint-*.json",
                "model.json",
                "model*.sc",
                "model*.step",
                "export-*.json",
                "qualification-result.json",
                "validation.json",
                "visual-validation.json",
                "camera-*.json",
            ):
                for evidence in sorted(native_case.glob(pattern)):
                    shutil.copyfile(evidence, case_dir / evidence.name)
                    native_files.append(evidence.name)
            preview_html = _render_visual_evidence(case, native_images)
            case_preview = (
                "model-iso.png" if "model-iso.png" in native_images
                else "model.png" if "model.png" in native_images
                else None
            )
            if case_preview:
                case_preview_html = (
                    '<figure class="qualification-case-preview">'
                    f'<a href="{escape(case_preview)}" class="qualification-image-link" '
                    'target="_blank" rel="noopener" title="Open full-size native preview">'
                    f'<img src="{escape(case_preview)}" '
                    f'alt="{escape(case["title"])} native SolidCraft preview">'
                    '</a>'
                    '<figcaption>Native SolidCraft preview — the same render used on the '
                    'qualification overview page.</figcaption>'
                    '</figure>'
                )
            status, status_detail = _qualification_status(qualification_result)
            results_html, body_count, parameter_count = _render_native_results(
                native_case,
                metadata["solidcraft_version"],
            )

        reference_items = []
        for label, description in case["references"]:
            url = REFERENCE_URLS.get(label)
            label_html = (
                f'<a href="{escape(url)}">{escape(label)}</a>'
                if url else escape(label)
            )
            reference_items.append(
                f"<li><strong>{label_html}:</strong> {escape(description)}</li>"
            )

        evidence_items = [
            '<li><a href="model.py">Forge fixture source</a></li>',
            '<li><a href="reference-pythonscad.py">PythonSCAD reference source</a></li>',
            '<li><a href="reference-pybosl2.py">pyBOSL2 reference source</a></li>',
            '<li><a href="commands.json">Generated command JSON</a></li>',
        ]
        evidence_items.extend(
            f'<li><a href="{escape(name)}">{escape(name)}</a></li>'
            for name in native_files
        )
        if native_images:
            evidence_items.extend(
                f'<li><a href="{escape(name)}">Native snapshot: {escape(name)}</a></li>'
                for name in native_images
            )
        evidence_items.extend(
            f'<li><a href="{escape(name)}">Reference evidence: {escape(name)}</a></li>'
            for name in reference_evidence_files
        )

        case_body = render_template(
            "case.html",
            title=escape(case["title"]),
            status_badge=_qualification_status_html(status, status_detail),
            case_preview=case_preview_html,
            setup_diagram=diagram_html,
            intent=escape(case["intent"]),
            gallery=preview_html,
            forge_api=escape(case["forge_api"]),
            forge_model=escape(case["forge_model"]),
            lowering=escape(case["lowering"]),
            native_expectation=escape(case["native_expectation"]),
            mutation_criterion=(
                '<h3>Mutation criterion</h3><p>' + escape(case["mutation"]) + '</p>'
                if case.get("q5_required") else ""
            ),
            mutation=escape(case["mutation"]),
            evidence_items="".join(evidence_items),
            results=results_html,
            lowering_detail=escape(lowering_detail),
            reference_items="".join(reference_items),
            source=escape(source),
            pythonscad_source=escape(reference_sources["pythonscad"]),
            pybosl2_source=escape(reference_sources["pybosl2"]),
            reference_evidence=reference_evidence_html,
        )
        (case_dir / "index.html").write_text(
            page(
                f"Qualification · {case['title']}",
                case_body,
                stylesheet="../../style.css",
                home="../../",
                cheatsheet="../../cheatsheet/",
            ),
            encoding="utf-8",
        )

        qualification_manifest[slug] = {
            "title": case["title"],
            "status": status,
            "status_detail": status_detail,
            "command_count": len(commands["commands"]),
            "reference_sources": [
                "reference-pythonscad.py",
                "reference-pybosl2.py",
            ],
            "native_evidence": native_files,
            "native_images": native_images,
            "reference_evidence": reference_evidence_files,
            "qualification_status": (
                qualification_result.get("status") if qualification_result else None
            ),
            "levels": (
                qualification_result.get("levels") if qualification_result else {}
            ),
            "solidcraft_version": (
                metadata.get("solidcraft_version") if verified else None
            ),
            "body_count": body_count,
            "parameter_count": parameter_count,
        }
        card_preview = (
            "model-iso.png" if "model-iso.png" in native_images
            else "model.png" if "model.png" in native_images
            else None
        )
        card_image = (
            f'<a href="{escape(slug)}/" class="qualification-card-image">'
            f'<img src="{escape(slug)}/{escape(card_preview)}" '
            f'alt="{escape(case["title"])} native isometric preview" loading="lazy"></a>'
            if card_preview else ""
        )
        qualification_cards[case["group"]].append(
            f'<article class="reference qualification-card">{card_image}'
            f'<div class="qualification-card-content">'
            + _qualification_status_html(status, status_detail)
            + f'<h2><a href="{escape(slug)}/">{escape(case["title"])}</a></h2>'
            f'<p>{escape(case["intent"])}</p>'
            f'<p><code>{escape(case["forge_api"])}</code></p>'
            + (
                f'<p class="meta">SolidCraft {escape(metadata.get("solidcraft_version"))}'
                f' · {escape(body_count)} bodies · {escape(parameter_count)} parameters</p>'
                if verified and body_count is not None else ""
            )
            + f'<a class="button" href="{escape(slug)}/">Open case sheet →</a></div></article>'
        )

    results_root = qualification_root / "results"
    results_root.mkdir(exist_ok=True)
    result_rows = []
    for case in QUALIFICATION_CASES:
        row = qualification_manifest[case["slug"]]
        result_rows.append(
            f"<tr><td><a href=\"../{escape(case['slug'])}/\">"
            f"{escape(case['title'])}</a></td>"
            f"<td>{_qualification_status_html(row['status'], row.get('status_detail', ''))}</td>"
            f"<td>{escape(row.get('solidcraft_version') or '—')}</td>"
            f"<td>{escape(row.get('body_count') if row.get('body_count') is not None else '—')}</td>"
            f"<td>{escape(row.get('parameter_count') if row.get('parameter_count') is not None else '—')}</td>"
            f"<td>{escape(len(row.get('native_evidence', [])))}</td></tr>"
        )
    results_body = render_template(
        "results.html",
        source_sha=escape(sha),
        solidcraft_version=escape(
            metadata.get("solidcraft_version") if verified else TESTED_SOLIDCRAFT_VERSION
        ),
        result_rows="".join(result_rows),
    )
    (results_root / "index.html").write_text(
        page(
            "Qualification results",
            results_body,
            stylesheet="../../style.css",
            home="../../",
            cheatsheet="../../cheatsheet/",
        ),
        encoding="utf-8",
    )

    level_rows = "".join(
        f"<tr><td><strong>{escape(level)}</strong></td><td>{escape(title)}</td>"
        f"<td>{escape(description)}</td></tr>"
        for level, title, description in QUALIFICATION_LEVELS
    )
    group_sections = "".join(
        f'<section class="section-heading"><h2>{escape(title)}</h2><p>{escape(description)}</p></section>'
        f'<div class="reference-grid qualification-grid">{"".join(qualification_cards[key])}</div>'
        for key, title, description in QUALIFICATION_GROUPS
        if qualification_cards[key]
    )
    qualification_index = render_template(
        "index.html",
        source_sha=escape(sha),
        solidcraft_version=escape(TESTED_SOLIDCRAFT_VERSION),
        level_rows=level_rows,
        group_sections=group_sections,
    )
    coverage_root = qualification_root / "coverage"
    coverage_root.mkdir(exist_ok=True)
    case_slugs = {case["slug"] for case in QUALIFICATION_CASES}

    def coverage_case_links(cases):
        links = []
        for name in cases:
            if name in case_slugs:
                links.append(f'<a href="../{escape(name)}/">{escape(name)}</a>')
            else:
                links.append(escape(name))
        return ", ".join(links) if links else "—"

    def coverage_status_badge(label):
        css = label.lower().replace(" ", "-")
        return (
            f'<span class="coverage-status {escape(css)}">'
            f'{escape(label)}</span>'
        )

    solidcraft_rows = []
    forge_status_counts = {"Supported": 0, "Partial": 0, "Missing": 0}
    group_titles = dict(CAPABILITY_GROUPS)
    group_status_counts = {
        key: {"Supported": 0, "Partial": 0, "Missing": 0}
        for key, _ in CAPABILITY_GROUPS
    }
    primitive_names = {"Box", "Cylinder", "Sphere", "Cone", "Torus"}
    primitive_counts = {"Supported": 0, "Partial": 0, "Missing": 0}

    for group, capability, solidcraft, status, forge, need, references, note in SOLIDCRAFT_CAPABILITIES:
        if status not in forge_status_counts:
            raise ValueError(f"Unknown Forge support status: {status}")
        forge_status_counts[status] += 1
        group_status_counts[group][status] += 1
        if capability in primitive_names:
            primitive_counts[status] += 1
        solidcraft_rows.append(
            f"<tr><td>{escape(group_titles.get(group, group))}</td>"
            f"<td><strong>{escape(capability)}</strong></td>"
            f"<td>{escape(solidcraft)}</td>"
            f"<td>{coverage_status_badge(status)}</td>"
            f"<td>{escape(forge)}</td><td>{escape(need)}</td></tr>"
        )

    area_summary_rows = []
    for group, title in CAPABILITY_GROUPS:
        counts = group_status_counts[group]
        total = sum(counts.values())
        area_summary_rows.append(
            f"<tr><td><strong>{escape(title)}</strong></td>"
            f"<td>{total}</td><td>{counts['Supported']}</td>"
            f"<td>{counts['Partial']}</td><td>{counts['Missing']}</td></tr>"
        )

    export_rows = []
    for api_name, (target, current, cases, note) in EXPORT_COVERAGE.items():
        export_rows.append(
            f"<tr><td><code>{escape(api_name)}</code></td>"
            f"<td>{escape(target)}</td><td><strong>{escape(current)}</strong></td>"
            f"<td>{coverage_case_links(cases)}</td><td>{escape(note)}</td></tr>"
        )

    def qualification_number(value):
        if value.startswith("Q") and value[1:].isdigit():
            return int(value[1:])
        return None

    capability_rows = []
    qualification_counts = {"At target": 0, "Below target": 0, "Gap": 0}
    qualification_group_counts = {}
    for group, capability, target, current, cases, note in CAPABILITY_COVERAGE:
        target_level = qualification_number(target)
        current_level = qualification_number(current)
        if current == "GAP":
            qualification_status = "Gap"
        elif current_level is not None and target_level is not None and current_level >= target_level:
            qualification_status = "At target"
        else:
            qualification_status = "Below target"

        qualification_counts[qualification_status] += 1
        group_counts = qualification_group_counts.setdefault(
            group, {"At target": 0, "Below target": 0, "Gap": 0}
        )
        group_counts[qualification_status] += 1

        capability_rows.append(
            f"<tr><td>{escape(group)}</td><td><code>{escape(capability)}</code></td>"
            f"<td>{escape(target)}</td><td><strong>{escape(current)}</strong></td>"
            f"<td>{coverage_status_badge(qualification_status)}</td>"
            f"<td>{coverage_case_links(cases)}</td><td>{escape(note)}</td></tr>"
        )

    qualification_summary_rows = []
    for group, counts in qualification_group_counts.items():
        total = sum(counts.values())
        qualification_summary_rows.append(
            f"<tr><td><strong>{escape(group)}</strong></td>"
            f"<td>{total}</td><td>{counts['At target']}</td>"
            f"<td>{counts['Below target']}</td><td>{counts['Gap']}</td></tr>"
        )

    gap_exports = sum(1 for row in EXPORT_COVERAGE.values() if row[1] == "GAP")
    gap_capabilities = qualification_counts["Gap"]
    coverage_body = render_template(
        "coverage.html",
        capability_total=escape(len(SOLIDCRAFT_CAPABILITIES)),
        forge_supported=escape(forge_status_counts["Supported"]),
        forge_partial=escape(forge_status_counts["Partial"]),
        forge_missing=escape(forge_status_counts["Missing"]),
        primitive_total=escape(sum(primitive_counts.values())),
        primitive_supported=escape(primitive_counts["Supported"]),
        primitive_partial=escape(primitive_counts["Partial"]),
        primitive_missing=escape(primitive_counts["Missing"]),
        area_summary_rows="".join(area_summary_rows),
        qualification_total=escape(sum(qualification_counts.values())),
        qualification_at_target=escape(qualification_counts["At target"]),
        qualification_below_target=escape(qualification_counts["Below target"]),
        qualification_gap=escape(qualification_counts["Gap"]),
        qualification_summary_rows="".join(qualification_summary_rows),
        gap_exports=escape(gap_exports),
        gap_capabilities=escape(gap_capabilities),
        solidcraft_rows="".join(solidcraft_rows),
        export_rows="".join(export_rows),
        capability_rows="".join(capability_rows),
    )
    (coverage_root / "index.html").write_text(
        page(
            "Qualification coverage",
            coverage_body,
            stylesheet="../../style.css",
            home="../../",
            cheatsheet="../../cheatsheet/",
        ),
        encoding="utf-8",
    )

    joint_anatomy_root = qualification_root / "joint-anatomy"
    joint_anatomy_root.mkdir(exist_ok=True)
    joint_diagrams = (
        "solidcraft-joint-anatomy",
        "solidcraft-joint-references",
        "corner-bracket-goal",
        "corner-bracket-depth",
        "corner-bracket-local-axes",
        "corner-bracket-front-corners",
    )
    for diagram in joint_diagrams:
        for suffix in (".svg", ".dxf"):
            source = (
                diagram_root / f"{diagram}{suffix}"
                if diagram_root is not None else None
            )
            if source is None or not source.is_file():
                raise ValueError(
                    f"Generated SolidCraft joint concept drawing missing: {diagram}{suffix}"
                )
            shutil.copyfile(source, joint_anatomy_root / source.name)
        plan = ROOT / "qualification" / "diagrams" / f"{diagram}.cadcraft.json"
        if not plan.is_file():
            raise ValueError(f"CadCraft concept source missing: {plan}")
        shutil.copyfile(plan, joint_anatomy_root / plan.name)

    joint_anatomy_body = render_template(
        "joint-anatomy.html",
        source_sha=escape(sha),
        solidcraft_version=escape(TESTED_SOLIDCRAFT_VERSION),
    )
    (joint_anatomy_root / "index.html").write_text(
        page(
            "SolidCraft joint anatomy",
            joint_anatomy_body,
            stylesheet="../../style.css",
            home="../../",
            cheatsheet="../../cheatsheet/",
        ),
        encoding="utf-8",
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
                "solidcraft_version": TESTED_SOLIDCRAFT_VERSION,
                "native_verified": verified,
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
                   if linked in EXAMPLES else "")
            boxes.append(f"""<article class="reference"><h3><code>{escape(title)}</code></h3>
<p>{escape(description)}</p><pre><code>{escape(snippet)}</code></pre>{ref}</article>""")
        sections.append(f'<section><h2>{escape(heading)}</h2><div class="reference-grid">{"".join(boxes)}</div></section>')
    cheat = f"""<main class="wrap"><div class="crumb"><a href="../">← Library</a> / Cheatsheet</div>
<section class="hero small"><p class="eyebrow">SCPF reference</p><h1>Cheatsheet</h1><p>SolidCraft version: <strong>{TESTED_SOLIDCRAFT_VERSION} tested</strong>; older versions are refused and newer versions trigger a compatibility warning.</p>
<p>Common SCPF syntax alongside tiny examples that CI compiles. For explanations, examples and limitations, read the
<a href="../guide/">full API Guide</a>.</p></section>
<div class="notice"><strong>What is verified?</strong> The linked examples and API unit tests run in GitHub Actions.
Cheatsheet fragments describe API calls; a fragment alone is not a complete runnable model.</div>
{"".join(sections)}</main>"""
    (out / "cheatsheet").mkdir(exist_ok=True)
    (out / "cheatsheet" / "index.html").write_text(
        page("Cheatsheet", cheat, stylesheet="../style.css", home="../", cheatsheet="./"),
        encoding="utf-8")

    home = f"""<main class="wrap"><section class="hero"><p class="eyebrow">lib.py.solidcraft.forge / Python Forge</p>
<h1>SCPF examples & API cheatsheet</h1><p class="meta">Tested SolidCraft version: {TESTED_SOLIDCRAFT_VERSION} · older releases rejected, newer releases warned</p><p>Small, readable Python examples to verify the SCPF command compiler.
This is <strong>not</strong> the SolidCraft CAD model gallery.</p>
<div class="actions"><a class="button primary" href="guide/">Read the API Guide →</a>\n<a class="button" href="reference/">API Reference →</a>\n<a class="button" href="qualification/">Qualification →</a>\n<a class="button" href="cheatsheet/">Quick cheatsheet →</a>\n<a class="button" href="{CAD_SITE}">See real CAD models →</a></div></section>
<section class="section-heading"><h2>Small public examples</h2><p>Each source produces its own native-command JSON.
Source and commands are regenerated together by CI.</p></section>
<div class="cards">{"".join(cards)}</div>
<div class="twocol"><section class="panel"><h2>Developing the library</h2>
<pre><code>python -m pip install -e ./scpf
python -m unittest discover -s scpf/tests -v
python -m scpf examples/simple-box/scpf/model.py --out output/box.json</code></pre>
<p>API and command tests stay here; mechanical assembly and render qualification live in the CAD project.</p></section>
<section class="panel"><h2>Continue with the real CAD project</h2><p>Corner Bracket, HUB75, enclosures and native
STEP/SC/PNG renders are maintained independently in <strong>2026-011-02.cad.solidcraft</strong>,
using the library as a pinned external dependency.</p><p><a href="{CAD_SITE}">Open the CAD project website →</a></p></section></div>
<p class="source-stamp">Library source commit: <code>{escape(sha)}</code></p></main>"""
    (out / "index.html").write_text(
        page("Examples & cheatsheet", home, stylesheet="style.css", home="./", cheatsheet="cheatsheet/"),
        encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "output" / "site")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--native", type=Path, help="Source-matched native screenshot directory")
    parser.add_argument("--diagram-root", type=Path, help="Generated qualification setup diagrams")
    parser.add_argument("--references", type=Path, help="Source-matched PythonSCAD/pyBOSL2 evidence")
    options = parser.parse_args()
    build(
        options.out,
        options.source_sha,
        native_root=options.native,
        diagram_root=options.diagram_root,
        reference_evidence_root=options.references,
    )
    print(f"Built independent SCPF library site: {options.out}")
