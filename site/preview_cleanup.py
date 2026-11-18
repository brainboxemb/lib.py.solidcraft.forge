#!/usr/bin/env python3
"""Remove the hosted Pages preview that belongs to one pull request."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


def preview_path(pages_root: Path, pull_request: int) -> Path:
    """Return the only Pages directory owned by a pull request."""
    if pull_request <= 0:
        raise ValueError("pull request number must be positive")
    return Path(pages_root) / "previews" / f"pr-{pull_request}"


def remove_preview(pages_root: Path, pull_request: int) -> bool:
    """Remove one PR preview without touching other previews or stable Pages."""
    target = preview_path(Path(pages_root), pull_request)
    if not target.exists():
        return False
    if not target.is_dir():
        raise ValueError(f"preview path is not a directory: {target}")
    shutil.rmtree(target)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages-root", type=Path, required=True)
    parser.add_argument("--pull-request", type=int, required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    changed = remove_preview(args.pages_root, args.pull_request)
    if args.github_output is not None:
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(f"changed={'true' if changed else 'false'}\n")

    print(
        f"{'removed' if changed else 'no preview for'} "
        f"PR #{args.pull_request}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
