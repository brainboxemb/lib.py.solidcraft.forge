#!/usr/bin/env python3
"""Build Forge documentation from self-describing examples and API sources.

Human example intent comes from local model.yml files. Exact verification
contracts remain in verification/verify.py. Stable Pages attaches accepted
build/main evidence separately.
"""
import argparse
import importlib.util
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
from example_metadata import discover_example_metadata, section_presentation
from example_documentation import discover_example_documentation
from cheatsheet_content import load_cheatsheet
from build_evidence import IMPLEMENTATIONS, load_stable_build_evidence
from qualification_view import diagram_views, qualification_case_view
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
    qualification_card,
    qualification_current_evidence,
    qualification_reference_comparison,
    qualification_diagrams,
    reference_shell,
    render_template,
)
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
    for heading, items in load_cheatsheet():
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
                documentation[row.slug].geometry_reason,
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


def _stable_qualification_summary(stable, slugs):
    """Compose current public status using the verification wheel in build/main."""

    wheel = str(stable.verification_wheel_path)
    scripts = str(ROOT / "scripts")
    added = []
    for value in (wheel, scripts):
        if value not in sys.path:
            sys.path.insert(0, value)
            added.append(value)
    try:
        spec = importlib.util.spec_from_file_location(
            "stable_qualification_summary",
            ROOT / "scripts" / "qualification_summary.py",
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load qualification summary adapter")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result, gate = module.compose_cases(
            stable.root,
            tuple(slugs),
        )
    finally:
        for value in added:
            if value in sys.path:
                sys.path.remove(value)

    if gate.get("status") != "pass":
        raise ValueError(
            "stable Pages publication gate is not pass: "
            + str(gate.get("status"))
        )
    cases = result.get("cases")
    if not isinstance(cases, dict):
        raise ValueError("qualification summary has no case map")
    return cases


def build(
    out,
    sha,
    *,
    build_main=None,
    build_commit=None,
):
    """Compile the source-driven site, optionally with stable build evidence."""

    out = Path(out)
    if (build_main is None) != (build_commit is None):
        raise ValueError(
            "stable Pages requires both build_main and build_commit"
        )

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
    verification_cards_by_section = {}
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

    stable = None
    stable_by_slug = {}
    summary_by_slug = {}
    stable_view_by_slug = {}
    if build_main is not None:
        stable = load_stable_build_evidence(
            Path(build_main),
            build_commit,
            (row.slug for row in example_rows),
        )
        stable_by_slug = {row.slug: row for row in stable.examples}
        summary_by_slug = _stable_qualification_summary(
            stable,
            (row.slug for row in example_rows),
        )
        stable_view_by_slug = {
            row.slug: qualification_case_view(
                stable,
                stable_by_slug[row.slug],
                summary_by_slug[row.slug],
                site_source_commit=sha,
            )
            for row in example_rows
        }
        (out / "provenance.json").write_text(
            json.dumps(
                {
                    "schema": 1,
                    "source_commit": sha,
                    "build_commit": stable.build_commit,
                    "build_scope": "main",
                    "build_manifest_source_commit": (
                        stable.manifest_source_commit
                    ),
                },
                indent=2,
                sort_keys=True,
            ) + "\n",
            encoding="utf-8",
        )

    for info in example_rows:
        slug = info.slug
        _section_priority, section_label, _section_description = (
            section_presentation(info.section)
        )
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

        if stable is not None:
            stable_view = stable_view_by_slug[slug]
            page_preview = stable_view["preview_url"]
            card_preview = stable_view["preview_url"]
            qualification_preview = stable_view["preview_url"]
            preview_kind = "durable-presentation-preview"
            preview_caption = (
                "Current deterministic presentation preview from durable "
                f"build {stable.build_commit[:12]}."
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
            f"{LIBRARY_URL}/blob/{sha}/examples/{slug}/scpf/model.py"
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
            bounds_sufficient=escape(
                "yes" if documentation.bounds_sufficient else "no"
            ),
            geometry_reason=escape(documentation.geometry_reason),
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
        if stable is not None:
            verification_card = qualification_card(
                info,
                stable_view_by_slug[slug],
                f"{slug}/",
                section_label=section_label,
            )
        else:
            verification_card = render_template(
                "example-card.html",
                **{**card_values, "section": escape(section_label)},
                example_url=f"../examples/{escape(slug)}/",
                preview_url=escape(qualification_preview),
            )
        verification_cards_by_section.setdefault(info.section, []).append(
            (info.priority, info.slug, verification_card)
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

    # Verification pages are derived from the same local example metadata.
    # #497 attaches accepted build/main status and measurements.
    verification_root = out / "verification"
    verification_root.mkdir(exist_ok=True)
    verification_manifest = {}

    for info in example_rows:
        slug = info.slug
        _section_priority, section_label, _section_description = (
            section_presentation(info.section)
        )
        documentation = documentation_by_slug[slug]
        case_dir = verification_root / slug
        case_dir.mkdir(exist_ok=True)
        reference_notes_html = reference_notes(
            documentation.reference_notes
        )
        verification_url = (
            f"{LIBRARY_URL}/blob/{sha}/examples/{slug}/verification/verify.py"
        )
        reference_sources = {
            implementation: (
                ROOT / "examples" / slug / implementation / "model.py"
            ).read_text(encoding="utf-8")
            for implementation in IMPLEMENTATIONS
        }
        reference_source_urls = {
            implementation: (
                f"{LIBRARY_URL}/blob/{sha}/examples/{slug}/"
                f"{implementation}/model.py"
            )
            for implementation in IMPLEMENTATIONS
        }
        current_evidence = (
            qualification_current_evidence(
                stable_view_by_slug[slug],
                info.title,
            )
            if stable is not None
            else render_template("qualification-evidence-unavailable.html")
        )
        reference_comparison = qualification_reference_comparison(
            reference_sources,
            reference_source_urls,
            reference_rows=(
                stable_view_by_slug[slug]["references"]
                if stable is not None
                else ()
            ),
        )
        body = render_template(
            "qualification-case.html",
            slug=escape(slug),
            title=escape(info.title),
            section=escape(section_label),
            documentation_goal=escape(documentation.goal),
            forge_api=escape(documentation.forge_api),
            forge_model=escape(documentation.forge_model),
            lowering=escape(documentation.lowering),
            solidcraft_result=escape(documentation.solidcraft_result),
            saved_design_test=escape(documentation.saved_design_test),
            bounds_sufficient=escape(
                "yes" if documentation.bounds_sufficient else "no"
            ),
            geometry_reason=escape(documentation.geometry_reason),
            reference_notes=reference_notes_html,
            verification_url=escape(verification_url),
            forge_source=escape((ROOT / "examples" / slug / "scpf" / "model.py").read_text(encoding="utf-8")),
            forge_source_url=escape(f"{LIBRARY_URL}/blob/{sha}/examples/{slug}/scpf/model.py"),
            current_evidence=current_evidence,
            reference_comparison=reference_comparison,
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
        verification_manifest[slug] = {
            "title": info.title,
            "documentation_source": f"examples/{slug}/README.md",
            "verification_source": (
                f"examples/{slug}/verification/verify.py"
            ),
            "evidence_source": "build/main",
        }
        if stable is not None:
            verification_manifest[slug].update(
                {
                    "status": stable_view_by_slug[slug]["status"],
                    "accepted_source_commit": (
                        stable_view_by_slug[slug][
                            "accepted_source_commit"
                        ]
                    ),
                    "build_commit": stable.build_commit,
                }
            )

    if stable is not None:
        evidence_note = render_template(
            "qualification-evidence-note.html",
            build_commit=escape(stable.build_commit),
        )
        diagrams = qualification_diagrams(diagram_views(stable))
    else:
        evidence_note = render_template(
            "qualification-evidence-unavailable.html"
        )
        diagrams = ""

    verification_groups = "".join(
        render_template(
            "verification-group.html",
            section=escape(label),
            description=escape(description),
            cards="".join(
                card
                for _priority, _slug, card in sorted(
                    verification_cards_by_section[section],
                    key=lambda item: (item[0], item[1]),
                )
            ),
        )
        for section, (priority, label, description) in sorted(
            (
                (section, section_presentation(section))
                for section in verification_cards_by_section
            ),
            key=lambda item: (item[1][0], item[0]),
        )
    )
    verification_index = render_template(
        "qualification-index.html",
        example_count=len(example_rows),
        groups=verification_groups,
        evidence_note=evidence_note,
        diagrams=diagrams,
    )
    (verification_root / "index.html").write_text(
        page(
            "Verification",
            verification_index,
            stylesheet="../style.css",
            home="../",
            cheatsheet="../cheatsheet/",
        ),
        encoding="utf-8",
    )
    (verification_root / "manifest.json").write_text(
        json.dumps(
            {
                "library_commit": sha,
                "evidence_source": "build/main",
                "build_commit": (
                    stable.build_commit if stable is not None else None
                ),
                "cases": verification_manifest,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    sections = []
    example_slugs = {row.slug for row in example_rows}
    for heading, items in load_cheatsheet():
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
    if stable is not None:
        manifest["build_commit"] = stable.build_commit
        manifest["build_manifest_source_commit"] = (
            stable.manifest_source_commit
        )
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "output" / "site")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument(
        "--build-main",
        type=Path,
        help="Materialized durable generated-branch main/ scope",
    )
    parser.add_argument(
        "--build-commit",
        help="Full immutable generated build-branch commit SHA",
    )
    options = parser.parse_args()
    build(
        options.out,
        options.source_sha,
        build_main=options.build_main,
        build_commit=options.build_commit,
    )
    print(f"Built independent SCPF library site: {options.out}")
