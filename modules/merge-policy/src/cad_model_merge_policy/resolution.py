"""Pure parsing and verification for reviewed permanent-merge recovery."""

from __future__ import annotations

from dataclasses import dataclass
import re


_SHA = re.compile(r"^[0-9a-f]{40}$")
_REF = re.compile(r"^[A-Za-z0-9._/-]+$")


@dataclass(frozen=True)
class ResolutionCommand:
    """Immutable owner-reviewed evidence for one conflicted permanent merge."""

    base_sha: str
    head_sha: str
    resolution_pr: int
    resolution_ref: str
    resolution_sha: str
    resolution_tree: str


def _sha(value: str, label: str) -> str:
    if not _SHA.fullmatch(value):
        raise ValueError(f"{label} must be an exact 40-character lowercase SHA")
    return value


def parse_resolution_command(
    command: str,
    resolution_prefix: str = "resolve/",
) -> ResolutionCommand:
    """Parse the exact multiline /merge-resolved owner command."""

    if not resolution_prefix or not _REF.fullmatch(resolution_prefix):
        raise ValueError("resolution_prefix must be a non-empty branch prefix")

    lines = [line.strip() for line in command.splitlines() if line.strip()]
    if len(lines) != 5 or lines[0] != "/merge-resolved":
        raise ValueError(
            "resolved command must contain /merge-resolved plus base, head, "
            "resolution-pr and resolution lines"
        )

    base = lines[1].split()
    head = lines[2].split()
    review = lines[3].split()
    resolution = lines[4].split()

    if len(base) != 2 or base[0] != "base":
        raise ValueError("resolved command requires: base <sha>")
    if len(head) != 2 or head[0] != "head":
        raise ValueError("resolved command requires: head <sha>")
    if len(review) != 2 or review[0] != "resolution-pr" or not review[1].isdigit():
        raise ValueError("resolved command requires: resolution-pr <number>")
    if len(resolution) != 4 or resolution[0] != "resolution":
        raise ValueError(
            "resolved command requires: "
            "resolution <ref> <commit-sha> <tree-sha>"
        )

    ref = resolution[1]
    if not _REF.fullmatch(ref) or ref.startswith("/") or ref.endswith("/"):
        raise ValueError("resolution ref has invalid syntax")
    if not ref.startswith(resolution_prefix):
        raise ValueError(
            f"resolution ref must start with configured prefix {resolution_prefix!r}"
        )

    number = int(review[1])
    if number < 1:
        raise ValueError("resolution-pr must be positive")

    return ResolutionCommand(
        base_sha=_sha(base[1], "base SHA"),
        head_sha=_sha(head[1], "head SHA"),
        resolution_pr=number,
        resolution_ref=ref,
        resolution_sha=_sha(resolution[2], "resolution commit SHA"),
        resolution_tree=_sha(resolution[3], "resolution tree SHA"),
    )


def verify_merge_object(
    payload: dict,
    *,
    expected_tree: str,
    expected_parents: tuple[str, str],
) -> str:
    """Return the merge SHA only for the exact reviewed tree and parent order."""

    sha = payload.get("sha")
    if not isinstance(sha, str) or not _SHA.fullmatch(sha):
        raise ValueError("created merge commit has no valid SHA")

    tree = (payload.get("tree") or {}).get("sha")
    if tree != expected_tree:
        raise ValueError(
            f"created merge commit tree mismatch: expected {expected_tree}, got {tree}"
        )

    parents = tuple(
        parent.get("sha")
        for parent in payload.get("parents", [])
        if isinstance(parent, dict)
    )
    if parents != expected_parents:
        raise ValueError(
            "created merge commit parents mismatch: "
            f"expected {expected_parents}, got {parents}"
        )
    return sha
