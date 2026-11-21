"""Render Verification coverage/results and legacy route compatibility.

This module composes view rows from source-owned coverage declarations and the
current normalized stable evidence. Human page copy remains in site templates.
"""

from __future__ import annotations

from collections import defaultdict

from api_coverage import CAPABILITY_COVERAGE, EXPORT_COVERAGE, coverage_rank
from capability_map import CAPABILITY_GROUPS, SOLIDCRAFT_CAPABILITIES
from html_writer import escape, render_template


def _public_term(value):
    """Normalize historical internal wording for the public Verification UI."""
    text = str(value)
    for old, new in (
        ("Qualification", "Verification"),
        ("qualification", "verification"),
        ("Qualified", "Verified"),
        ("qualified", "verified"),
    ):
        text = text.replace(old, new)
    return text


def _status_badge(label):
    css = label.lower().replace(" ", "-")
    return (
        f'<span class="coverage-status {escape(css)}">'
        f"{escape(label)}</span>"
    )


def _case_links(cases, case_slugs):
    links = []
    for slug in cases:
        if slug not in case_slugs:
            raise ValueError(
                f"Verification coverage references unknown case: {slug}"
            )
        links.append(f'<a href="../{escape(slug)}/">{escape(slug)}</a>')
    return ", ".join(links) if links else "—"


def coverage_content(case_slugs, evidence_note):
    """Render current source-owned capability coverage."""
    case_slugs = set(case_slugs)

    forge_status_counts = {"Supported": 0, "Partial": 0, "Missing": 0}
    group_titles = dict(CAPABILITY_GROUPS)
    group_status_counts = {
        key: {"Supported": 0, "Partial": 0, "Missing": 0}
        for key, _title in CAPABILITY_GROUPS
    }
    primitive_names = {"Box", "Cylinder", "Sphere", "Cone", "Torus"}
    primitive_counts = {"Supported": 0, "Partial": 0, "Missing": 0}
    solidcraft_rows = []

    for (
        group,
        capability,
        solidcraft,
        status,
        forge,
        need,
        _references,
        _note,
    ) in SOLIDCRAFT_CAPABILITIES:
        if status not in forge_status_counts:
            raise ValueError(f"Unknown Forge support status: {status}")
        if group not in group_status_counts:
            raise ValueError(f"Unknown capability group: {group}")
        forge_status_counts[status] += 1
        group_status_counts[group][status] += 1
        if capability in primitive_names:
            primitive_counts[status] += 1
        solidcraft_rows.append(
            f"<tr><td>{escape(group_titles[group])}</td>"
            f"<td><strong>{escape(capability)}</strong></td>"
            f"<td>{escape(_public_term(solidcraft))}</td>"
            f"<td>{_status_badge(status)}</td>"
            f"<td>{escape(_public_term(forge))}</td>"
            f"<td>{escape(_public_term(need))}</td></tr>"
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
        if current == "GAP" and cases:
            raise ValueError(f"{api_name}: GAP cannot cite Verification cases")
        if (
            coverage_rank(current) is not None
            and coverage_rank(current) >= 3
            and not cases
        ):
            raise ValueError(
                f"{api_name}: {current} requires a concrete Verification case"
            )
        export_rows.append(
            f"<tr><td><code>{escape(api_name)}</code></td>"
            f"<td>{escape(target)}</td>"
            f"<td><strong>{escape(current)}</strong></td>"
            f"<td>{_case_links(cases, case_slugs)}</td>"
            f"<td>{escape(_public_term(note))}</td></tr>"
        )

    verification_counts = {"At target": 0, "Below target": 0, "Gap": 0}
    verification_group_counts = defaultdict(
        lambda: {"At target": 0, "Below target": 0, "Gap": 0}
    )
    capability_rows = []
    for group, capability, target, current, cases, note in CAPABILITY_COVERAGE:
        if current == "GAP":
            if cases:
                raise ValueError(
                    f"{capability}: GAP cannot cite Verification cases"
                )
            status = "Gap"
        else:
            current_level = coverage_rank(current)
            target_level = coverage_rank(target)
            if current_level is None or target_level is None:
                raise ValueError(
                    f"{capability}: invalid coverage level {current!r}/{target!r}"
                )
            if current_level >= 3 and not cases:
                raise ValueError(
                    f"{capability}: {current} requires a concrete Verification case"
                )
            status = (
                "At target"
                if current_level >= target_level
                else "Below target"
            )
        verification_counts[status] += 1
        verification_group_counts[group][status] += 1
        capability_rows.append(
            f"<tr><td>{escape(group)}</td>"
            f"<td><code>{escape(capability)}</code></td>"
            f"<td>{escape(target)}</td>"
            f"<td><strong>{escape(current)}</strong></td>"
            f"<td>{_status_badge(status)}</td>"
            f"<td>{_case_links(cases, case_slugs)}</td>"
            f"<td>{escape(_public_term(note))}</td></tr>"
        )

    verification_summary_rows = []
    for group, counts in verification_group_counts.items():
        total = sum(counts.values())
        verification_summary_rows.append(
            f"<tr><td><strong>{escape(group)}</strong></td>"
            f"<td>{total}</td><td>{counts['At target']}</td>"
            f"<td>{counts['Below target']}</td><td>{counts['Gap']}</td></tr>"
        )

    gap_exports = sum(
        1 for row in EXPORT_COVERAGE.values() if row[1] == "GAP"
    )
    return render_template(
        "verification-coverage.html",
        evidence_note=evidence_note,
        capability_total=escape(len(SOLIDCRAFT_CAPABILITIES)),
        forge_supported=escape(forge_status_counts["Supported"]),
        forge_partial=escape(forge_status_counts["Partial"]),
        forge_missing=escape(forge_status_counts["Missing"]),
        primitive_total=escape(sum(primitive_counts.values())),
        primitive_supported=escape(primitive_counts["Supported"]),
        primitive_partial=escape(primitive_counts["Partial"]),
        primitive_missing=escape(primitive_counts["Missing"]),
        area_summary_rows="".join(area_summary_rows),
        verification_total=escape(sum(verification_counts.values())),
        verification_at_target=escape(verification_counts["At target"]),
        verification_below_target=escape(verification_counts["Below target"]),
        verification_gap=escape(verification_counts["Gap"]),
        verification_summary_rows="".join(verification_summary_rows),
        gap_exports=escape(gap_exports),
        gap_capabilities=escape(verification_counts["Gap"]),
        solidcraft_rows="".join(solidcraft_rows),
        export_rows="".join(export_rows),
        capability_rows="".join(capability_rows),
    )


def results_content(
    example_rows,
    stable_views,
    *,
    source_sha,
    build_commit,
    solidcraft_version,
    evidence_note,
):
    """Render the current 1-row-per-case Verification result table."""
    rows = []
    for info in example_rows:
        view = stable_views.get(info.slug)
        if view is None:
            status = _status_badge("Not run")
            accepted_source = "—"
            bodies = "—"
            parameters = "—"
            saved_designs = "—"
            references = "—"
        else:
            status = _status_badge(
                "Pass" if view["status"] == "pass" else view["status"].title()
            )
            accepted_source = escape(view["accepted_source_commit"][:12])
            bodies = escape(len(view["bodies"]))
            parameters = escape(len(view["parameters"]))
            saved_designs = escape(len(view["saved_designs"]))
            references = escape(
                sum(
                    1
                    for row in view["references"]
                    if row["status"] == "pass"
                )
            )
        rows.append(
            f'<tr><td><a href="../{escape(info.slug)}/">'
            f"{escape(info.title)}</a></td>"
            f"<td>{status}</td>"
            f"<td><code>{accepted_source}</code></td>"
            f"<td>{bodies}</td><td>{parameters}</td>"
            f"<td>{saved_designs}</td><td>{references}</td></tr>"
        )
    return render_template(
        "verification-results.html",
        source_sha=escape(source_sha),
        build_commit=escape(build_commit or "source-only"),
        solidcraft_version=escape(solidcraft_version),
        evidence_note=evidence_note,
        result_rows="".join(rows),
    )


def legacy_redirect(target):
    """Render one old public HTML route as a canonical Verification redirect."""
    return render_template(
        "legacy-redirect.html",
        target=escape(target),
    )
