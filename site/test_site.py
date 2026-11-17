#!/usr/bin/env python3
"""Validate that the library Pages site is not a duplicate CAD model gallery."""
import html
import inspect
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "site"))
from build import (
    EXAMPLES,
    QUALIFICATION_CASES,
    QUALIFICATION_GROUPS,
    REFERENCE_IMPLEMENTATION_LABELS,
    reference_implementations_for,
)
from api_coverage import EXPORT_COVERAGE, CAPABILITY_COVERAGE
from capability_map import CAPABILITY_GROUPS, SOLIDCRAFT_CAPABILITIES
import scpf
from scpf.version import TESTED_SOLIDCRAFT_VERSION


def check(
    site: Path,
    sha: str,
    require_native: bool = False,
    require_references: bool = False,
):
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

    documented_constructor_groups = {
        "geometry-constructors",
        "sketch-slot-constructors",
        "feature-constructors",
    }
    for spec in GROUP_REFERENCES:
        if spec["slug"] not in documented_constructor_groups:
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
        "Placement",
        "occurrence.move",
        "placement=Placement",
        "rotation=(Z, 180)",
    ):
        assert term in transformations, term
    for removed in ("copy().move(", "copy().rotate(", "copy().at(", "Position"):
        assert removed not in transformations, removed
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
    assert "Native joint.as_built preserves an already translated and rotated child pose" in coverage_page
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
        for suffix in (".svg", ".dxf", ".cadcraft.json"):
            artifact = site / "qualification" / "joint-anatomy" / f"{diagram}{suffix}"
            assert artifact.is_file() and artifact.stat().st_size > 0, artifact
        assert f'src="{diagram}.svg"' in joint_anatomy_page
        assert f'href="{diagram}.cadcraft.json"' in joint_anatomy_page
    assert "Q1" in qualification_index and "Q6" in qualification_index
    assert 'class="reference-grid qualification-grid"' in qualification_index
    assert qualification_manifest["library_commit"] == sha
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
            "1. Test setup",
            "Test goal",
            "Pass criteria",
            "2. Implementation under test",
            "Public Forge API used",
            "Forge model represented by this fixture",
            "Reference implementations",
            "PythonSCAD",
            "pyBOSL2",
            "CadQuery",
            "build123d",
            "3. Generated SolidCraft relationship",
            "6. Evidence and references",
        ):
            assert heading in page_text, (slug, heading)
        assert case["title"] in page_text
        setup_name = case.get("diagram", "setup.svg")
        setup_image = site / "qualification" / slug / setup_name
        assert setup_image.is_file() and setup_image.stat().st_size > 0, slug
        assert 'class="qualification-setup-diagram"' in page_text, slug
        assert f'href="{setup_name}"' in page_text, slug
        assert 'target="_blank"' in page_text, slug

        setup_pos = page_text.index("<h2>1. Test setup</h2>")
        implementation_pos = page_text.index("<h2>2. Implementation under test</h2>")
        command_pos = page_text.index("<h2>3. Generated SolidCraft relationship</h2>")
        assert setup_pos < implementation_pos < command_pos, slug

        for placeholder in (
            "$title",
            "$status",
            "$gallery",
            "$results",
            "$source",
            "$reference_rows",
        ):
            assert placeholder not in page_text, (slug, placeholder)
        assert (site / "qualification" / slug / "model.py").is_file()
        reference_names = reference_implementations_for(case)
        for implementation in reference_names:
            source_name = f"reference-{implementation}.py"
            assert (site / "qualification" / slug / source_name).is_file()
            assert f'href="{source_name}"' in page_text
            assert REFERENCE_IMPLEMENTATION_LABELS[implementation] in page_text
        assert "Rendered comparison" in page_text
        assert "qualification-reference-list" in page_text
        assert page_text.count("qualification-reference-row") == len(reference_names)
        assert (site / "qualification" / slug / "commands.json").is_file()
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
                    assert artifact.is_file() and artifact.stat().st_size > 0, artifact
                result = json.loads(
                    (site / "qualification" / slug / prefix / "result.json")
                    .read_text(encoding="utf-8")
                )
                assert result["status"] == "pass", (slug, implementation)
                assert f'src="{prefix}/model-iso.png"' in page_text, (
                    slug,
                    implementation,
                )
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
            manifest_case = qualification_manifest["cases"][slug]
            result_path = site / "qualification" / slug / "qualification-result.json"
            assert result_path.is_file(), slug
            structured_result = json.loads(result_path.read_text(encoding="utf-8"))
            if case.get("blocked_reason"):
                assert structured_result["status"] == "blocked", slug
                assert structured_result["blocked_reason"] == case["blocked_reason"], slug
                assert manifest_case["qualification_status"] == "blocked", slug
                assert ">BLOCKED</span>" in page_text, slug
                assert case["blocked_reason"] in page_text, slug
                assert not (site / "qualification" / slug / "model.png").exists(), slug
                continue

            assert structured_result["status"] in {
                "pass", "fail", "review", "incomplete"
            }, slug
            assert manifest_case["qualification_status"] == structured_result["status"], slug

            badge = {
                "pass": "PASS",
                "fail": "FAIL",
                "review": "REVIEW",
                "incomplete": "INCOMPLETE",
            }[structured_result["status"]]
            assert f">{badge}</span>" in page_text, slug

            assert structured_result["source_commit"] == sha, slug
            assert structured_result["forge_version"] == qualification_manifest["forge_version"], slug
            assert structured_result["solidcraft_version"] == TESTED_SOLIDCRAFT_VERSION, slug
            assert structured_result["qualified_at"] == qualification_manifest["qualified_at"], slug
            assert manifest_case["levels"] == structured_result["levels"], slug
            assert "Native runtime:" in page_text, slug
            assert f"SolidCraft {TESTED_SOLIDCRAFT_VERSION}" in page_text, slug

            image = site / "qualification" / slug / "model.png"
            assert image.is_file() and image.stat().st_size > 0, slug
            assert image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
            native_images = qualification_manifest["cases"][slug]["native_images"]
            for required_image in (
                "model.png",
                "model-front.png",
                "model-right.png",
                "model-iso.png",
            ):
                assert required_image in native_images, (slug, required_image)

            assert "<h2>1. Test setup</h2>" in page_text, slug
            assert "<h3>Test goal</h3>" in page_text, slug
            assert "<h3>Pass criteria</h3>" in page_text, slug
            assert "<h2>2. Implementation under test</h2>" in page_text, slug
            assert "<h2>4. Machine verification</h2>" in page_text, slug
            assert "<h2>5. Visual verification</h2>" in page_text, slug
            machine_pos = page_text.index("<h2>4. Machine verification</h2>")
            visual_pos = page_text.index("<h2>5. Visual verification</h2>")
            evidence_pos = page_text.index("<h2>6. Evidence and references</h2>")
            assert command_pos < machine_pos < visual_pos < evidence_pos, slug
            assert 'class="panel qualification-visual-check"' in page_text, slug
            assert 'class="qualification-image-link"' in page_text, slug
            assert 'href="model-iso.png"' in page_text, slug
            assert 'href="goal-iso.png"' in page_text, slug
            assert 'href="overlay-iso.png"' in page_text, slug
            assert f'src="{slug}/model-iso.png"' in qualification_index, slug
            assert 'class="qualification-case-preview"' in page_text, slug
            assert 'href="model-iso.png"' in page_text, slug
            assert 'src="model-iso.png"' in page_text, slug
            preview_pos = page_text.index('class="qualification-case-preview"')
            setup_pos = page_text.index("<h2>1. Test setup</h2>")
            assert preview_pos < setup_pos, slug
            native_evidence = qualification_manifest["cases"][slug]["native_evidence"]
            assert "measurements.json" in native_evidence, slug
            assert "results.json" in native_evidence, slug
            assert "validation.json" in native_evidence, slug
            assert "visual-validation.json" in native_evidence, slug

            # Qualification status is data, not a hard-coded historical
            # expectation.  The site must render whatever status the current
            # structured result reports (PASS/FAIL/REVIEW/INCOMPLETE).
            status = structured_result["status"]
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
    for concept in ("Box(", "Rectangle2D(", "Hole(", "copy()", "rotate(", "python -m scpf"):
        assert concept in cheatsheet, concept
    # The library page has only tiny fixtures. CAD models and native renders
    # MUST NOT be copied into this independent site.
    assert not (site / "models").exists()
    assert not (site / "previews").exists()
    assert not list(site.rglob("native.png"))
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
    check(
        Path(sys.argv[1]),
        sys.argv[2],
        require_native="--require-native" in sys.argv[3:],
        require_references="--require-references" in sys.argv[3:],
    )
