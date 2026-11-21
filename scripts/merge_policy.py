#!/usr/bin/env python3
"""Repository merge-policy decision helper.

This module contains no GitHub API calls. It only maps a pull-request base/head
pair to the repository's merge and branch-lifecycle policy.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json


LONG_LIVED_LANES = frozenset({"dev-cad", "dev-ci"})
DURABLE_SOURCE_REFS = frozenset({"main", *LONG_LIVED_LANES})
PERMANENT_REFS = frozenset(
    {
        "main",
        "dev-cad",
        "dev-ci",
        "build",
        "gh-pages",
    }
)
TEMPORARY_PREFIXES = (
    "issue/",
    "fix/",
    "feature/",
    "accept/",
    "promote/",
    "docs/",
    "chore/",
)


@dataclass(frozen=True)
class MergePolicy:
    """Resolved merge/lifecycle policy for one pull request."""

    merge_method: str
    direct_lane_promotion: bool
    cleanup_head: bool
    integrate_base: bool


def is_direct_lane_promotion(*, base: str, head: str) -> bool:
    """Return whether this is a long-lived development lane promoted to main."""

    return base == "main" and head in LONG_LIVED_LANES


def is_cleanup_eligible(head: str) -> bool:
    """Return whether a merged short-lived source branch may be deleted."""

    if head in PERMANENT_REFS:
        return False
    if head.startswith("backup/"):
        return False
    return head.startswith(TEMPORARY_PREFIXES)


def evaluate(*, base: str, head: str) -> MergePolicy:
    """Resolve the repository's one merge-policy decision."""

    promotion = is_direct_lane_promotion(base=base, head=head)
    return MergePolicy(
        merge_method="merge" if promotion else "squash",
        direct_lane_promotion=promotion,
        cleanup_head=(not promotion and is_cleanup_eligible(head)),
        integrate_base=base in DURABLE_SOURCE_REFS,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    print(json.dumps(asdict(evaluate(base=args.base, head=args.head)), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
