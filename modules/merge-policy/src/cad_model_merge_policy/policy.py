"""Classify allowed branch integrations."""

class MergePolicyError(RuntimeError):
    """Branch integration violates project policy."""


def is_main_governance(*, head: str, base: str) -> bool:
    """Return whether this is the narrow main-owned governance-docs lane."""

    return base == "main" and head.startswith("docs/")


_PERMANENT_MERGES = frozenset({
    ("dev", "main"),
    ("main", "dev"),
    ("dev", "exp"),
    ("exp", "dev"),
})


def is_permanent_merge(*, head: str, base: str) -> bool:
    """Return whether this exact permanent direction requires a merge commit."""

    return (head, base) in _PERMANENT_MERGES


def merge_method(*, head: str, base: str) -> str:
    if is_permanent_merge(head=head, base=base):
        return "merge"
    if base in {"dev", "exp"} and head.startswith(
        ("issue/", "fix/", "feature/", "docs/", "chore/")
    ):
        return "squash"
    if is_main_governance(head=head, base=base):
        return "squash"
    if base == "main" and head.startswith("release/"):
        return "squash"
    raise MergePolicyError(f"unsupported branch integration: {head} -> {base}")
