"""Classify allowed branch integrations."""

class MergePolicyError(RuntimeError):
    """Branch integration violates project policy."""


def merge_method(*, head: str, base: str) -> str:
    if (head, base) in {("dev", "exp"), ("exp", "dev")}:
        return "merge"
    if base in {"dev", "exp"} and head.startswith(("issue/", "fix/", "feature/", "docs/", "chore/")):
        return "squash"
    if base == "main" and head.startswith("release/"):
        return "squash"
    if (head, base) in {("dev", "main"), ("main", "dev")}:
        return "merge"
    raise MergePolicyError(f"unsupported branch integration: {head} -> {base}")
