"""Pure cleanup eligibility rules."""

from __future__ import annotations

from .config import CleanupConfig


def is_temporary(branch: str, config: CleanupConfig) -> bool:
    if branch in config.permanent:
        return False
    return branch.startswith(config.temporary_prefixes)


def merge_target(branch: str, config: CleanupConfig) -> str:
    """Return the primary integration target (release branches target stable)."""

    if branch.startswith("release/"):
        return config.stable
    return config.development


def merge_targets(branch: str, config: CleanupConfig) -> tuple[str, ...]:
    primary = merge_target(branch, config)
    return (primary,) if branch.startswith("release/") else (primary, "exp")


def eligible_post_merge(
    *,
    head: str,
    base: str,
    same_repository: bool,
    merged: bool,
    config: CleanupConfig,
) -> bool:
    return (
        merged
        and same_repository
        and is_temporary(head, config)
        and base in merge_targets(head, config)
    )


def eligible_sweep(
    *,
    branch: str,
    has_open_pr: bool,
    has_merged_pr_to_target: bool,
    config: CleanupConfig,
) -> bool:
    return (
        is_temporary(branch, config)
        and not has_open_pr
        and has_merged_pr_to_target
    )
