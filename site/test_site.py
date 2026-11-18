#!/usr/bin/env python3
"""Validate that the library Pages site is not a duplicate CAD model gallery."""
import html
import inspect
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "site"))
from build import (
    CHEATSHEET,
    EXAMPLES,
    QUALIFICATION_CASES,
    QUALIFICATION_GROUPS,
    REFERENCE_IMPLEMENTATION_LABELS,
    _cheatsheet_anchor,
    reference_implementations_for,
)
from api_coverage import (
    EXPORT_COVERAGE,
    CAPABILITY_COVERAGE,
    validate_coverage_cases,
    validate_coverage_results,
)
from capability_map import CAPABILITY_GROUPS, SOLIDCRAFT_CAPABILITIES
import scpf
from scpf.version import TESTED_SOLIDCRAFT_VERSION
from qualification.geometry_contracts import proof_contract
from qualification.case_evidence import evidence_for


def check(
    site: Path,
    sha: str,
    require_native: bool = False,
    require_references: bool = False,
    evidence_sha: str | None = None,
):
    evidence_sha = evidence_sha or sha
    template_dir = ROOT / "qualification" / "templates"
    for template_name in (
        "case.html",
        "index.html",
        "results.html",
        "coverage.html",
        "joint-anatomy.html",
        "report.md",
    ):
        template = template_dir / template_name
        assert template.is_file() and template.stat().st_size > 0, template_name

    home = (site / "index.html").read_text(encoding="utf-8")
    cheatsheet = (site / "cheatsheet" / "index.html").read_text(encoding="utf-8")
    from build import GUIDES
    guide_index = (site / "guide" / "index.html").read_text(encoding="utf-8")
    assert "API Guide" in home and "API Guide" in guide_index
    assert 'class="guide-sidebar"' in guide_index
    assert 'class="active" href="./">Overview</a>' in guide_index
    assert "Start here" in guide_index

    reference_index = (site / "reference" / "index.html").read_text(encoding="utf-8")
    assert "API Reference" in home and "API Reference" in reference_index
    assert 'class="reference-sidebar"' in reference_index
    assert 'class="active" href="./">Overview</a>' in reference_index
    for heading in (
        "Browse by task",
        "Selectors",
        "Components &amp; assemblies",
        "Shape &amp; sketch",
    ):
        assert heading in reference_index, heading
    from api_reference import (
        ENUM_REFERENCES,
        GROUP_REFERENCES,
        METHOD_REFERENCES,
        agent_manifest,
        api_manifest,
        enum_members,
        export_reference_targets,
        group_members,
        unmapped_public_exports,
    )
    for spec in ENUM_REFERENCES:
        page_text = (site / "reference" / spec["slug"] / "index.html").read_text(encoding="utf-8")
        assert spec["summary"] in page_text, spec["slug"]
        assert "reference-sidebar" in page_text and "reference-article" in page_text
        assert f'class="active" href="../{spec["slug"]}/"' in page_text
        for name, value in enum_members(spec):
            assert f"{spec['slug']}.{name}" in page_text, (spec["slug"], name)
            assert str(value) in page_text, (spec["slug"], value)
    anchor_page = (site / "reference" / "Anchor" / "index.html").read_text(encoding="utf-8")
    assert "Anchor.UP" in anchor_page and "Anchor.DOWN" in anchor_page
    for spec in METHOD_REFERENCES:
        page_text = (site / "reference" / spec["slug"] / "index.html").read_text(encoding="utf-8")
        assert "reference-sidebar" in page_text and "reference-article" in page_text
        assert f'class="active" href="../{spec["slug"]}/"' in page_text
        assert html.escape(spec["signature"]) in page_text, spec["slug"]
        assert spec["summary"] in page_text, spec["slug"]
        assert "Cross-object API design rules" in page_text, spec["slug"]

    for spec in GROUP_REFERENCES:
        page_text = (site / "reference" / spec["slug"] / "index.html").read_text(encoding="utf-8")
        assert "reference-sidebar" in page_text and "reference-article" in page_text
        assert f'class="active" href="../{spec["slug"]}/"' in page_text
        assert spec["title"] in page_text and spec["summary"] in page_text
        for member in group_members(spec):
            assert f'href="#{member["name"]}"' in page_text, (
                spec["slug"],
                member["name"],
            )
            assert f'id="{member["name"]}"' in page_text, (spec["slug"], member["name"])
            assert html.escape(member["summary"]) in page_text, (spec["slug"], member["name"])
            if member["kind"] == "callable" and member.get("signature"):
                assert html.escape(member["signature"]) in page_text
            elif member["kind"] == "enum":
                for row in member["members"]:
                    assert f'{member["name"]}.{row["name"]}' in page_text
            elif member["kind"] == "constant":
                assert member["value"] in page_text

    documented_callable_groups = {
        "geometry-constructors",
        "sketch-slot-constructors",
        "feature-constructors",
        "parameters-positioning",
        "attachment-references",
        "execution-api",
    }
    for spec in GROUP_REFERENCES:
        if spec["slug"] not in documented_callable_groups:
            continue
        page_text = (
            site / "reference" / spec["slug"] / "index.html"
        ).read_text(encoding="utf-8")
        for member in group_members(spec):
            if member["kind"] != "callable":
                continue
            signature = inspect.signature(member["object"])
            expected_parameters = {
                name
                for name, parameter in signature.parameters.items()
                if parameter.kind not in {
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                }
            }
            documented_parameters = {
                row["name"] for row in member["parameters"]
            }
            assert documented_parameters == expected_parameters, (
                member["name"],
                documented_parameters,
                expected_parameters,
            )
            assert member["example"], member["name"]
            assert f'id="{member["name"]}"' in page_text, member["name"]
            for parameter in expected_parameters:
                assert f"<code>{parameter}</code>" in page_text, (
                    member["name"],
                    parameter,
                )

    geometry_guide = (
        site / "guide" / "geometry" / "index.html"
    ).read_text(encoding="utf-8")
    assert "Detailed parameter reference" in geometry_guide
    for term in (
        "Sketch.rectangular_pattern",
        "Sketch.mirror",
        "Circle2D",
        "SlotCenterToCenter2D",
        "Per-instance pattern suppression is not supported",
        "Select profiles when extruding a Sketch",
        "profiles=[(x, y), ...]",
        "exact_regions=True",
    ):
        assert term in geometry_guide, term
    assert "Sketch.rectangular_pattern(...)" in cheatsheet
    assert "Sketch.mirror(...)" in cheatsheet
    assert "shape.rectangular_pattern(...)" in cheatsheet
    assert "shape.circular_pattern(...)" in cheatsheet
    assert "sketch.extrude(..., profiles=[...])" in cheatsheet
    assert "Sketch.sheet_metal(...)" in cheatsheet
    assert "Shape.fold(...)" in cheatsheet
    assert "shape.pattern(...)" not in cheatsheet

    for _group, title, _target, _current, _cases, _note in CAPABILITY_COVERAGE:
        match = re.match(r"^(Shape|Sketch)\.([A-Za-z_][A-Za-z0-9_]*)\(", title)
        if not match:
            continue
        owner_name, method_name = match.groups()
        owner = getattr(scpf, owner_name)
        assert hasattr(owner, method_name), (
            "stale capability method",
            title,
        )

    for _heading, items in CHEATSHEET:
        for title, _description, _snippet, _linked in items:
            match = re.match(
                r"^(shape|Shape|sketch|Sketch)\.([A-Za-z_][A-Za-z0-9_]*)",
                title,
            )
            if not match:
                continue
            owner_token, method_name = match.groups()
            owner = scpf.Shape if owner_token.lower() == "shape" else scpf.Sketch
            assert hasattr(owner, method_name), (
                "stale cheatsheet method",
                title,
            )

    for spec in METHOD_REFERENCES:
        signature = inspect.signature(spec["object"])
        expected_parameters = {
            name
            for name, parameter in signature.parameters.items()
            if name != "self"
            and parameter.kind not in {
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            }
        }
        documented_parameters = {
            row["name"] for row in spec["parameters"]
        }
        assert documented_parameters == expected_parameters, (
            spec["slug"],
            documented_parameters,
            expected_parameters,
        )
        assert spec["example"], spec["slug"]

    assert not unmapped_public_exports()
    assert set(export_reference_targets()) == set(scpf.__all__)

    generated_api = json.loads(
        (site / "reference" / "api.json").read_text(encoding="utf-8")
    )
    assert generated_api == api_manifest()

    search_index = json.loads(
        (site / "search-index.json").read_text(encoding="utf-8")
    )
    assert search_index["schema"] == 1
    search_entries = search_index["entries"]
    indexed_symbols = {
        entry.get("symbol")
        for entry in search_entries
        if entry.get("symbol")
    }
    assert set(scpf.__all__) <= indexed_symbols

    def search_matches(query):
        raw_query = query.lower().strip()
        folded_query = re.sub(r"[_.:/-]+", " ", raw_query)
        words = folded_query.split()
        matches = []
        for entry in search_entries:
            aliases = [alias.lower() for alias in entry.get("aliases", ())]
            raw_title = entry["title"].lower()
            haystack = " ".join((
                entry["title"],
                entry.get("summary", ""),
                entry.get("keywords", ""),
                " ".join(entry.get("aliases", ())),
            )).lower()
            folded_haystack = re.sub(r"[_.:/-]+", " ", haystack)
            if (
                raw_title == raw_query
                or raw_query in aliases
                or raw_query in haystack
                or (words and all(word in folded_haystack for word in words))
            ):
                matches.append(entry)
        return matches

    slot_exact = search_matches("SlotCenterToCenter2D")
    assert any(
        entry["kind"] == "API Reference"
        and entry["url"] == "reference/sketch-slot-constructors/#SlotCenterToCenter2D"
        for entry in slot_exact
    )
    for query in ("p0", "slot centre"):
        assert any(
            "sketch-slot-constructors/#" in entry["url"]
            for entry in search_matches(query)
        ), query

    faces_top = search_matches("Faces.TOP")
    assert any(
        entry["title"] == "Faces.TOP"
        and entry["url"] == "reference/Faces/#Faces.TOP"
        for entry in faces_top
    )
    faces_page = (
        site / "reference" / "Faces" / "index.html"
    ).read_text(encoding="utf-8")
    assert 'id="Faces.TOP"' in faces_page

    for symbol in ("Shape.rectangular_pattern", "Shape.circular_pattern"):
        pattern_matches = search_matches(symbol)
        assert any(
            entry["kind"] == "API Reference"
            and entry["title"] == symbol
            for entry in pattern_matches
        ), symbol
        assert any(
            entry["kind"] == "API Guide"
            and entry["title"] == f"{symbol} · API Guide"
            and entry["url"] == "guide/features/#feature-patterns"
            for entry in pattern_matches
        ), symbol
    extrude_matches = search_matches("Sketch.extrude profiles")
    assert any(
        entry["kind"] == "API Reference"
        and entry["title"] == "Sketch.extrude"
        and entry["url"] == "reference/Sketch.extrude/"
        for entry in extrude_matches
    )
    assert any(
        entry["kind"] == "API Guide"
        and entry["url"] == "guide/geometry/#profile-selection"
        for entry in extrude_matches
    )

    for symbol in ("Sketch.rectangular_pattern", "Sketch.mirror"):
        matches = search_matches(symbol)
        assert any(
            entry["kind"] == "API Reference"
            and entry["title"] == symbol
            and entry["url"] == f"reference/{symbol}/"
            for entry in matches
        ), symbol
        assert any(
            entry["kind"] == "API Guide"
            and entry["title"] == f"{symbol} · API Guide"
            and entry["url"] == "guide/geometry/#pattern-mirror"
            for entry in matches
        ), symbol

    for symbol in ("Shape.fillet", "Shape.chamfer"):
        matches = search_matches(symbol)
        assert any(
            entry["kind"] == "API Reference"
            and entry["title"] == symbol
            and entry["url"] == f"reference/{symbol}/"
            for entry in matches
        ), symbol
        assert any(
            entry["kind"] == "API Guide"
            and entry["url"] == "guide/features/#fillet"
            for entry in matches
        ), symbol

    for heading, items in CHEATSHEET:
        for title, _description, _snippet, _linked in items:
            anchor = _cheatsheet_anchor(heading, title)
            assert f'id="{anchor}"' in cheatsheet
            assert any(
                entry["kind"] == "Cheatsheet"
                and entry["url"] == f"cheatsheet/#{anchor}"
                for entry in search_entries
            )

    for page_text in (home, guide_index, reference_index, cheatsheet):
        assert 'class="site-search"' in page_text
        assert "search-index.json" in page_text
        assert "Search SCPF documentation" in page_text
    assert "event.key === '/'" in home
    assert "event.key.toLowerCase() === 'k'" in home
    local_agent_api = json.loads(
        (ROOT / "docs" / "agent" / "forge-api.json").read_text(encoding="utf-8")
    )
    expected_agent_api = agent_manifest()
    if local_agent_api != expected_agent_api:
        cached_symbols = local_agent_api["symbols"]
        expected_symbols = expected_agent_api["symbols"]
        changed = {
            name: {
                "cached": cached_symbols.get(name),
                "generated": expected_symbols.get(name),
            }
            for name in sorted(set(cached_symbols) | set(expected_symbols))
            if cached_symbols.get(name) != expected_symbols.get(name)
        }
        raise AssertionError(
            "docs/agent/forge-api.json is out of date for: "
            + ", ".join(changed)
            + "\\n"
            + json.dumps(changed, indent=2)
        )
    assert set(scpf.__all__) <= set(local_agent_api["symbols"])
    agent_source = (ROOT / "docs" / "agent" / "forge-api.json").read_text(encoding="utf-8")
    assert len(agent_source.encode("utf-8")) < 25000
    assert '"use_when"' not in agent_source
    assert '"limits"' not in agent_source
    assert 'class="development-banner"' in home
    assert "querySelectorAll('pre > code')" in home
    assert "navigator.clipboard.writeText" in home
    assert "setAttribute('aria-label', 'Copy code')" in home
    assert "Development version." in home
    assert "not a support guarantee" in home
    assert "full API Guide" in cheatsheet
    for chapter in GUIDES:
        page = (site / "guide" / chapter["slug"] / "index.html").read_text(encoding="utf-8")
        assert chapter["title"] in page
        assert "guide-sidebar" in page and "guide-article" in page
        assert f'class="active" href="../{chapter["slug"]}/"' in page
        if '<h2 id="' in chapter["body"]:
            assert 'class="guide-subnav"' in page, chapter["slug"]
        assert len(page) > 1400, chapter["slug"]
    features = (site / "guide" / "features" / "index.html").read_text(encoding="utf-8")
    assert 'href="../../reference/Faces/"' in features
    assert "API on this page" in features
    for term in (
        "Shape.fillet",
        "Shape.chamfer",
        "Edges.VERTICAL",
        "FRONT + LEFT",
        "use the same edge-selection",
    ):
        assert term in features, term
    css = (site / "style.css").read_text(encoding="utf-8")
    assert ".guide-api-grid{display:grid;grid-template-columns:1fr" in css
    assert ".code-block>pre{margin-top:0;padding-right:52px}" in css
    for face_name in ("TOP", "BOTTOM", "LEFT", "RIGHT", "FRONT", "BACK"):
        assert f"Faces.{face_name}" in features, face_name
    assert "Shape.on(self, target" in features
    assert (site / "api-design-contract.html").is_file()

    assembly_basics = (
        site / "guide" / "assembly-basics" / "index.html"
    ).read_text(encoding="utf-8")
    for term in (
        "From one component to an assembly",
        "one physical part",
        "Shape + Shape",
        "occurrence + occurrence",
        "Use @assembly when the composition itself is reusable",
        "Use attach() when the relationship is the intent",
        "A group is organisation, not a relationship",
        "SolidCraft own the native relationship",
        "API on this page",
        "Anchor.TOP",
        "Occurrence.attach",
        "Assembly.group",
    ):
        assert term in assembly_basics, term
    transformations = (site / "guide" / "transformations" / "index.html").read_text(encoding="utf-8")
    for term in (
        "Positioning and orientation",
        "Which one do I use?",
        "shape.at(...)",
        "feature.on(...)",
        "Shape.attach(...)",
        "Placement(...)",
        "Occurrence.attach(...)",
        "The important distinction",
        "Use at() to place or align geometry",
        "Use on() for a feature on a face",
        "Shape.attach() is lower-level within-part placement",
        "Use Placement for a component occurrence",
        "Use Occurrence.attach() for separate physical parts",
        "rotation=(Z, 180)",
    ):
        assert term in transformations, term
    for removed in (
        "copy().move(",
        "copy().rotate(",
        "copy().at(",
        "<code>Position</code>",
        "Shape.attach() and Occurrence.attach() are the same",
    ):
        assert removed not in transformations, removed

    guide_slugs = [chapter["slug"] for chapter in GUIDES]
    assert guide_slugs[:4] == [
        "getting-started",
        "model-objects",
        "transformations",
        "assembly-basics",
    ], guide_slugs
    components = (site / "guide" / "components" / "index.html").read_text(encoding="utf-8")
    for term in (
        "AnchorFrame",
        "point plus orientation",
        "child=mount",
        "anchors()",
        "joint.create",
        "direct <code>AnchorFrame</code>",
        "AnchorTopology",
        "follow an edge or corner",
        "Assembly-owned named anchors",
        "with_anchor()",
        "Associative in-plane attachment offset",
        "attach(offset=(u, v))",
        "front_top_left",
    ):
        assert term in components, term
    assert "AnchorFrame" in cheatsheet and "child=mount" in cheatsheet
    assert "AnchorTopology" in cheatsheet
    assert "assembly.with_anchor" in cheatsheet
    assert "attach(offset=(u, v))" in cheatsheet
    assert "copy(placement=Placement(...))" in cheatsheet
    assert "Placement(rotation=(axis, degrees))" in cheatsheet
    assert "copy().move(" not in cheatsheet
    assert "model.rotate(" not in cheatsheet
    qualification_index = (site / "qualification" / "index.html").read_text(encoding="utf-8")
    qualification_manifest = json.loads(
        (site / "qualification" / "manifest.json").read_text(encoding="utf-8")
    )
    coverage_page = (
        site / "qualification" / "coverage" / "index.html"
    ).read_text(encoding="utf-8")
    results_page = (
        site / "qualification" / "results" / "index.html"
    ).read_text(encoding="utf-8")
    assert "Qualification results" in results_page
    for page_text in (qualification_index, coverage_page, results_page):
        assert 'class="development-banner"' in page_text
        assert "Development version." in page_text
        assert "not a support guarantee" in page_text
    assert set(scpf.__all__) == set(EXPORT_COVERAGE), (
        "Every public scpf.__all__ symbol must have a declared qualification row"
    )
    validate_coverage_cases(QUALIFICATION_CASES)
    coverage_source = (ROOT / "site" / "api_coverage.py").read_text(encoding="utf-8")
    assert "0.30.1" not in coverage_source
    case_slugs = {case["slug"] for case in QUALIFICATION_CASES}
    for _name, (_target, _current, cases, _note) in EXPORT_COVERAGE.items():
        assert set(cases) <= case_slugs
        for slug in cases:
            assert f'href="../{slug}/"' in coverage_page
    for _group, _capability, _target, _current, cases, _note in CAPABILITY_COVERAGE:
        assert set(cases) <= case_slugs
        for slug in cases:
            assert f'href="../{slug}/"' in coverage_page
    assert "SolidCraft functionality coverage" in coverage_page
    for api_name in scpf.__all__:
        assert f"<code>{api_name}</code>" in coverage_page, api_name
    for _, capability, *_ in SOLIDCRAFT_CAPABILITIES:
        assert capability in coverage_page, capability
    statuses = {
        status
        for _, _, _, status, *_ in SOLIDCRAFT_CAPABILITIES
    }
    assert statuses <= {"Supported", "Partial", "Missing"}
    assert "Basic primitives:</strong> 3/5 supported" in coverage_page
    assert "Coverage by area" in coverage_page
    for _, title in CAPABILITY_GROUPS:
        assert title in coverage_page, title
    for group, capability, target, current, cases, note in CAPABILITY_COVERAGE:
        assert capability in coverage_page, capability
        assert target.startswith("Q")
        assert current == "GAP" or current.startswith("Q")
    assert "Functional qualification:</strong>" in coverage_page
    assert "Qualification by area" in coverage_page
    assert "At target" in coverage_page
    assert "Below target" in coverage_page
    assert "Basic vertical-edge fillet is command-, native- and visual-qualified" in coverage_page
    assert "no dedicated native qualification case currently proves Q3-Q6" in coverage_page
    assert "<code>Edges</code>" in coverage_page
    for status_class in (
        "coverage-status supported",
        "coverage-status partial",
        "coverage-status missing",
        "coverage-status at-target",
        "coverage-status below-target",
        "coverage-status gap",
    ):
        assert status_class in coverage_page, status_class

    assert "Qualification" in home and "Qualification" in qualification_index
    assert 'href="joint-anatomy/"' in qualification_index
    joint_anatomy_page = (
        site / "qualification" / "joint-anatomy" / "index.html"
    ).read_text(encoding="utf-8")
    for term in (
        "Placing a corner bracket with Forge",
        "Nederlands — eenvoudige uitleg",
        "English — simple explanation",
        "The real SolidCraft relationship remains explicit",
        "AnchorFrame(",
        "<code>Anchor.RIGHT</code>",
        "child joint origin",
        "4 brackets",
        "8 brackets",
        "No second orientation solver",
        "Anchor.FRONT_TOP_LEFT",
        "z=+Y, x=-Z",
        "Anchor.BACK_TOP_RIGHT",
    ):
        assert term in joint_anatomy_page, term
    for diagram in (
        "solidcraft-joint-anatomy",
        "solidcraft-joint-references",
        "corner-bracket-goal",
        "corner-bracket-depth",
        "corner-bracket-local-axes",
        "corner-bracket-front-corners",
    ):
        source = site / "qualification" / "joint-anatomy" / f"{diagram}.cadcraft.json"
        assert source.is_file() and source.stat().st_size > 0, source
        assert not (site / "qualification" / "joint-anatomy" / f"{diagram}.svg").exists()
        assert not (site / "qualification" / "joint-anatomy" / f"{diagram}.dxf").exists()
        assert f"/qualification/diagrams/{diagram}.svg" in joint_anatomy_page
        assert f"/qualification/diagrams/{diagram}.dxf" in joint_anatomy_page
        assert f'href="{diagram}.cadcraft.json"' in joint_anatomy_page
    assert "Q1" in qualification_index and "Q6" in qualification_index
    assert 'class="reference-grid qualification-grid"' in qualification_index
    assert qualification_manifest["library_commit"] == sha
    assert qualification_manifest["qualification_commit"] == evidence_sha
    assert qualification_manifest["forge_version"]
    assert qualification_manifest["solidcraft_version"] == TESTED_SOLIDCRAFT_VERSION
    assert qualification_manifest["qualified_at"]
    assert f"Forge {qualification_manifest['forge_version']}" in qualification_index
    assert f"Forge {qualification_manifest['forge_version']}" in results_page
    assert qualification_manifest["qualified_at"] in qualification_index
    assert qualification_manifest["qualified_at"] in results_page
    assert set(qualification_manifest["cases"]) == {
        case["slug"] for case in QUALIFICATION_CASES
    }
    group_keys = {key for key, _, _ in QUALIFICATION_GROUPS}
    assert all(case["group"] in group_keys for case in QUALIFICATION_CASES)
    for _, title, _ in QUALIFICATION_GROUPS:
        assert title in qualification_index
    assert not (site / "qualification" / "capabilities").exists()
    for case in QUALIFICATION_CASES:
        slug = case["slug"]
        page_text = (
            site / "qualification" / slug / "index.html"
        ).read_text(encoding="utf-8")
        for heading in (
            "What this example makes",
            "Forge code",
            "API used",
            "How Forge builds it in SolidCraft",
            "SolidCraft result",
            "Reference code",
            "Technical test details",
            "Q1 and Q2 tests",
            "Geometry checks",
            "Saved-design test",
            "Raw test files",
            "Reference documentation",
            "PythonSCAD",
            "pyBOSL2",
            "CadQuery",
            "build123d",
        ):
            assert heading in page_text, (slug, heading)
        for old_heading in (
            "Case-specific Q1/Q2 evidence",
            "Shared geometry contract",
            "SolidCraft-only checks",
            "Q5 applicability",
            "Pass criteria",
            "Implementation under test",
            "Generated SolidCraft relationship",
        ):
            assert old_heading not in page_text, (slug, old_heading)
        assert '<details class="panel qualification-technical-details">' in page_text, slug
        assert '<details class="panel qualification-technical-details" open>' not in page_text, slug
        assert case["title"] in page_text
        for level in ("q1", "q2"):
            for target in evidence_for(slug, level):
                assert target["file"] in page_text, (slug, level, target)
                assert target["test"] in page_text, (slug, level, target)
        assert case["mutation"] in html.unescape(page_text), slug
        saved_label = (
            "Checked in the saved model."
            if case.get("q5_required")
            else "No saved-model change is required."
        )
        assert saved_label in page_text, slug
        setup_name = case.get("diagram", "setup.svg")
        setup_image = site / "qualification" / slug / setup_name
        assert setup_image.is_file() and setup_image.stat().st_size > 0, slug
        assert 'class="qualification-setup-diagram"' in page_text, slug
        assert f'href="{setup_name}"' in page_text, slug
        assert 'target="_blank"' in page_text, slug

        model_pos = page_text.index("<h2>What this example makes</h2>")
        forge_pos = page_text.index("<h2>Forge code</h2>")
        solidcraft_pos = page_text.index("<h2>How Forge builds it in SolidCraft</h2>")
        result_pos = page_text.index("<h2>SolidCraft result</h2>")
        reference_pos = page_text.index("<h2>Reference code</h2>")
        technical_pos = page_text.index("Technical test details")
        assert model_pos < forge_pos < reference_pos < solidcraft_pos < result_pos < technical_pos, slug

        for placeholder in (
            "$title",
            "$status",
            "$gallery",
            "$results",
            "$case_test_evidence",
            "$source",
            "$reference_rows",
        ):
            assert placeholder not in page_text, (slug, placeholder)
        assert (site / "qualification" / slug / "model.py").is_file()
        proof_path = site / "qualification" / slug / "proof-contract.json"
        assert proof_path.is_file(), slug
        rendered_proof = json.loads(proof_path.read_text(encoding="utf-8"))
        assert rendered_proof == proof_contract(slug), slug
        assert qualification_manifest["cases"][slug]["proof_contract"] == rendered_proof
        assert "Geometry checks" in page_text, slug
        assert "Is the size check enough for this model?" in page_text, slug
        assert html.escape(rendered_proof["geometry"]["bounds_reason"]) in page_text, slug
        assert 'class="qualification-table-scroll"' in page_text, slug
        geometry = rendered_proof["geometry"]
        if geometry.get("visual_features") or geometry.get("surface_distance_probes"):
            assert "Show all geometry check points" in page_text, slug
            assert '<details class="qualification-detail-block qualification-proof-details">' in page_text, slug
        reference_names = reference_implementations_for(case)
        for implementation in reference_names:
            source_name = f"reference-{implementation}.py"
            assert (site / "qualification" / slug / source_name).is_file()
            assert f'href="{source_name}"' in page_text
            assert REFERENCE_IMPLEMENTATION_LABELS[implementation] in page_text
        assert "Reference code" in page_text
        assert "qualification-reference-list" in page_text
        assert page_text.count("qualification-reference-row") == len(reference_names)
        assert not (site / "qualification" / slug / "commands.json").exists()
        build_prefix = (
            "https://github.com/brainboxemb/lib.py.solidcraft.forge/blob/build/"
        )
        assert build_prefix in page_text, slug
        assert "/blob/build/main/examples/" in page_text, slug
        if require_references:
            manifest_case = qualification_manifest["cases"][slug]
            evidence = manifest_case["reference_evidence"]
            for implementation in reference_names:
                prefix = f"reference-{implementation}"
                for name in (
                    "result.json",
                    "model.stl",
                    "model-front.png",
                    "model-right.png",
                    "model-iso.png",
                ):
                    rel = f"{prefix}/{name}"
                    assert rel in evidence, (slug, rel)
                    artifact = site / "qualification" / slug / rel
                    assert not artifact.exists(), artifact
                assert (
                    f"/examples/{slug}/{implementation}/model-iso.png"
                    in page_text
                ), (slug, implementation)
                assert (
                    f"/examples/{slug}/{implementation}/result.json"
                    in page_text
                ), (slug, implementation)
                assert "Reference result checks" in page_text, (
                    slug,
                    implementation,
                )
                assert '<details class="qualification-reference-checks qualification-detail-block">' in page_text, (
                    slug,
                    implementation,
                )
                assert '<details class="qualification-reference-checks qualification-detail-block" open>' not in page_text, (
                    slug,
                    implementation,
                )
                assert "Reference result checks" in page_text, (
                    slug,
                    implementation,
                )
                if slug in {"anchored-holes", "rectangular-pattern", "slot-family"}:
                    assert "surface distance probes" in page_text.lower(), slug
            if reference_names:
                assert "independently exported stl" in page_text.lower(), slug
            else:
                exceptions = case.get("reference_exceptions", {})
                assert exceptions, (
                    slug,
                    "a case without executable references needs documented exceptions",
                )
                assert (
                    set(exceptions) == set(REFERENCE_IMPLEMENTATION_LABELS)
                ), (
                    slug,
                    "a fully excepted case must explain every default reference implementation",
                )
                assert "Documented reference exceptions" in page_text, slug
                assert not evidence, (
                    slug,
                    "a fully excepted case must not fabricate reference evidence",
                )
                for implementation, reason in exceptions.items():
                    assert REFERENCE_IMPLEMENTATION_LABELS[implementation] in page_text, (
                        slug,
                        implementation,
                    )
                    assert html.escape(reason) in page_text, (slug, implementation)
        if require_native:
            validate_coverage_results(qualification_manifest)
            manifest_case = qualification_manifest["cases"][slug]
            result_path = site / "qualification" / slug / "qualification-result.json"
            assert not result_path.exists(), slug
            status = manifest_case["qualification_status"]
            if case.get("blocked_reason"):
                assert status == "blocked", slug
                assert ">BLOCKED</span>" in page_text, slug
                assert case["blocked_reason"] in page_text, slug
                assert not (site / "qualification" / slug / "model.png").exists(), slug
                continue

            assert status in {"pass", "fail", "review", "incomplete"}, slug
            badge = {
                "pass": "PASS",
                "fail": "FAIL",
                "review": "REVIEW",
                "incomplete": "INCOMPLETE",
            }[status]
            assert f">{badge}</span>" in page_text, slug
            assert "<h2>SolidCraft result</h2>" in page_text, slug
            assert f"SolidCraft {TESTED_SOLIDCRAFT_VERSION}" in page_text, slug
            assert "Semantic validation" in page_text, slug
            assert '<details class="qualification-detail-block qualification-semantic-checks">' in page_text, slug

            image = site / "qualification" / slug / "model.png"
            assert not image.exists(), slug
            native_images = qualification_manifest["cases"][slug]["native_images"]
            for required_image in (
                "model.png",
                "model-front.png",
                "model-right.png",
                "model-iso.png",
            ):
                assert required_image in native_images, (slug, required_image)

            geometry = proof_contract(slug)["geometry"]
            for view in geometry["required_views"]:
                for prefix in ("model", "goal", "overlay"):
                    required_image = f"{prefix}-{view}.png"
                    assert required_image in native_images, (
                        slug,
                        required_image,
                    )
                    assert f"/examples/{slug}/scpf/{required_image}" in page_text, (
                        slug,
                        required_image,
                    )

            assert "<h2>Visual result</h2>" in page_text, slug
            assert "<h2>Reference code</h2>" in page_text, slug
            assert "<strong>Technical test details</strong>" in page_text, slug
            assert "<h3>Q1 and Q2 tests</h3>" in page_text, slug
            assert "<h3>Geometry checks</h3>" in page_text, slug
            assert "<h3>Saved-design test</h3>" in page_text, slug
            assert "q1-case-evidence.txt" in page_text, slug
            assert "q2-case-evidence.txt" in page_text, slug
            for level in ("q1", "q2"):
                level_result = manifest_case["levels"][level]
                assert level_result["status"] == "pass", (slug, level)
                assert level_result["tests"], (slug, level)
                assert level_result["evidence"], (slug, level)
                for target in level_result["tests"]:
                    assert target["file"] in page_text, (slug, level, target)
                    assert target["test"] in page_text, (slug, level, target)

            for removed_heading in (
                "1. Test setup",
                "Test goal",
                "Pass criteria",
                "Case-specific Q1/Q2 evidence",
                "Shared geometry contract",
                "SolidCraft-only checks",
                "Implementation under test",
                "Machine verification",
                "Visual verification",
                "Evidence and references",
            ):
                assert removed_heading not in page_text, (slug, removed_heading)

            visual_pos = page_text.index("<h2>Visual result</h2>")
            preview_pos = page_text.index('class="qualification-case-preview"')
            assert model_pos < preview_pos < forge_pos, slug
            assert result_pos < visual_pos < technical_pos, slug

            assert 'class="panel qualification-visual-check"' in page_text, slug
            assert 'class="qualification-image-link"' in page_text, slug
            assert f"/examples/{slug}/scpf/model-iso.png" in page_text, slug
            assert f"/examples/{slug}/scpf/goal-iso.png" in page_text, slug
            assert f"/examples/{slug}/scpf/overlay-iso.png" in page_text, slug
            assert f"/examples/{slug}/scpf/model-iso.png" in qualification_index, slug
            q6 = manifest_case["levels"]["q6"]
            visual_result_path = site / "qualification" / slug / "visual-validation.json"
            assert not visual_result_path.exists(), slug
            if manifest_case["qualification_status"] == "pass":
                assert q6["status"] == "pass", slug
                assert q6["regression_status"] == "pass", slug
                assert q6["expected_shape_status"] == "pass", slug
                assert q6["required_views"] == geometry["required_views"], slug
                assert "<strong>Image checks:</strong>" in page_text, slug
                assert "expected shape PASS" in page_text, slug
                assert "saved render PASS" in page_text, slug

            if slug in {
                "anchored-holes",
                "rectangular-pattern",
                "slot-family",
            }:
                assert "top" in geometry["required_views"], slug
                assert 'data-view="top"' in page_text, slug
                assert f"/examples/{slug}/scpf/model-top.png" in page_text, slug
                assert f"/examples/{slug}/scpf/goal-top.png" in page_text, slug
                assert f"/examples/{slug}/scpf/overlay-top.png" in page_text, slug
                assert "Internal features" in page_text, slug

            native_evidence = qualification_manifest["cases"][slug]["native_evidence"]
            assert "measurements.json" in native_evidence, slug
            assert "results.json" in native_evidence, slug
            assert "validation.json" in native_evidence, slug
            assert "visual-validation.json" in native_evidence, slug

            # Qualification status is data, not a hard-coded historical
            # expectation.  The site must render whatever status the current
            # structured result reports (PASS/FAIL/REVIEW/INCOMPLETE).
            status = manifest_case["qualification_status"]
            assert status in {"pass", "fail", "review", "incomplete"}, slug
            status_class = f'qualification-status {status}'
            assert status_class in page_text, (slug, status)



    manifest = json.loads((site / "manifest.json").read_text(encoding="utf-8"))
    assert (site / ".nojekyll").is_file()
    assert (site / "style.css").is_file()
    assert set(manifest["examples"]) == set(EXAMPLES)
    assert manifest["qualifier"] == "command-generation"
    assert manifest["library_commit"] == sha and sha in home
    assert "SolidCraft CAD projects" in home and "SCPF examples" in home
    assert "Full SolidCraft CAD projects" in home
    assert "Cheatsheet" in home and "Cheatsheet" in cheatsheet
    assert "Qualification" in home
    for concept in (
        "Box(",
        "Rectangle2D(",
        "Hole(",
        "copy(placement=Placement(",
        "Placement(rotation=",
        "python -m scpf",
    ):
        assert concept in cheatsheet, concept
    # The library page has only tiny fixtures. CAD models and native renders
    # MUST NOT be copied into this independent site.
    assert not (site / "models").exists()
    assert not (site / "previews").exists()
    assert not list(site.rglob("native.png"))
    for suffix in (".sc", ".step", ".stl"):
        assert not list((site / "qualification").rglob(f"*{suffix}")), suffix
    for name in (
        "commands.json",
        "measurements.json",
        "results.json",
        "qualification-result.json",
        "validation.json",
        "visual-validation.json",
    ):
        assert not list((site / "qualification").rglob(name)), name
    qualification_by_slug = {
        case["slug"]: case for case in QUALIFICATION_CASES
    }
    native_case_slugs = {
        case["slug"] for case in QUALIFICATION_CASES
        if not case.get("blocked_reason")
    }
    for slug, info in manifest["examples"].items():
        page = (site / "examples" / slug / "index.html").read_text(encoding="utf-8")
        src = (site / info["source"]).read_text(encoding="utf-8")
        commands = json.loads((site / info["commands"]).read_text(encoding="utf-8"))["commands"]
        assert src.strip()
        blocked_reason = (
            info.get("blocked_reason")
            or qualification_by_slug.get(slug, {}).get("blocked_reason")
        )
        if blocked_reason:
            assert info["command_count"] == 0, slug
            command_record = json.loads(
                (site / info["commands"]).read_text(encoding="utf-8")
            )
            assert command_record.get("blocked_reason") == blocked_reason, slug
            assert info.get("blocked_reason") == blocked_reason, slug
        else:
            assert len(commands) == info["command_count"] > 0
        image = site / info["preview"]
        assert image.is_file() and image.stat().st_size > 0
        assert info["preview_kind"] in ("native-snapshot", "schematic")
        assert f'src="{image.name}"' in page
        assert f'examples/{slug}/{image.name}' in home
        if require_native and slug in native_case_slugs:
            assert info["preview_kind"] == "native-snapshot", slug
        if info["preview_kind"] == "native-snapshot":
            assert image.suffix == ".png"
            assert image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
            assert f"Native SolidCraft {TESTED_SOLIDCRAFT_VERSION} render" in page
        else:
            assert image.suffix == ".svg"
            if blocked_reason:
                assert "BLOCKED" in page
                assert blocked_reason in page
            else:
                assert "Schematic illustration only" in page
        assert "commands.json" in page and "model.py" in page
    print(f"OK: {len(EXAMPLES)} compiled library examples, cheatsheet, no CAD duplicates")


if __name__ == "__main__":
    extra = sys.argv[3:]
    evidence_sha = next(
        (arg.split("=", 1)[1] for arg in extra if arg.startswith("--evidence-sha=")),
        None,
    )
    check(
        Path(sys.argv[1]),
        sys.argv[2],
        require_native="--require-native" in extra,
        require_references="--require-references" in extra,
        evidence_sha=evidence_sha,
    )
