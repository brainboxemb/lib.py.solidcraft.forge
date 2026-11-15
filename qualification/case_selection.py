"""Case selection helpers shared by local and CI qualification runners."""

from __future__ import annotations

import re

from qualification.cases import QUALIFICATION_CASES


CASE_SLUGS = tuple(case["slug"] for case in QUALIFICATION_CASES)
CASE_BY_SLUG = {case["slug"]: case for case in QUALIFICATION_CASES}
GROUP_NAMES = tuple(dict.fromkeys(case["group"] for case in QUALIFICATION_CASES))


def parse_case_selection(value: str | None) -> tuple[str, ...]:
    """Expand comma/space separated case names, group:<name> tokens, or all.

    Selection order follows the qualification case registry so output and timing
    reports remain stable regardless of the order in which tokens are supplied.
    """
    if value is None or not value.strip() or value.strip().lower() == "all":
        return CASE_SLUGS

    requested: set[str] = set()
    tokens = tuple(
        token
        for token in re.split(r"[\s,]+", value.strip())
        if token
    )
    for token in tokens:
        if token.lower() == "all":
            requested.update(CASE_SLUGS)
            continue

        if token.startswith("group:"):
            group = token.split(":", 1)[1]
            if group not in GROUP_NAMES:
                raise ValueError(
                    f"unknown qualification group {group!r}; "
                    f"choose from {', '.join(GROUP_NAMES)}"
                )
            requested.update(
                case["slug"]
                for case in QUALIFICATION_CASES
                if case["group"] == group
            )
            continue

        if token not in CASE_BY_SLUG:
            raise ValueError(
                f"unknown qualification case {token!r}; "
                f"choose a case slug, group:<name>, or all"
            )
        requested.add(token)

    return tuple(slug for slug in CASE_SLUGS if slug in requested)


def format_selection_help() -> str:
    return (
        "case slugs: " + ", ".join(CASE_SLUGS)
        + "\ngroups: " + ", ".join(f"group:{name}" for name in GROUP_NAMES)
    )
