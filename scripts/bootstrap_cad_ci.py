#!/usr/bin/env python3
"""Check out the exact tool.cad.ci revision used by this Forge repository.

The tool is repository infrastructure, not part of the scpf Python package.
Keeping it under ext/cad-ci means local runs and GitHub Actions invoke the same
tracked tool revision without mixing its package into Forge's public API.
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def dependency(root: Path = ROOT) -> tuple[str, str]:
    """Return the configured tool Git URL and exact 40-character revision."""

    text = (root / "dependencies.repos").read_text(encoding="utf-8")
    section = re.search(
        r"(?ms)^  cad-ci:\s*\n(.*?)(?=^  [\w-]+:|\Z)",
        text,
    )
    if section is None:
        raise RuntimeError("dependencies.repos has no cad-ci entry")

    url = re.search(r"(?m)^    url:\s*(\S+)\s*$", section[1])
    sha = re.search(r"(?m)^    version:\s*([0-9a-f]{40})\s*$", section[1])
    if url is None or sha is None:
        raise RuntimeError("cad-ci requires a Git URL and exact commit SHA")
    return url[1], sha[1]


def _git(target: Path, *args: str, check: bool = True) -> str:
    """Run Git for the external checkout and return stripped stdout."""

    completed = subprocess.run(
        ["git", "-C", str(target), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise RuntimeError(message or "git command failed")
    return completed.stdout.strip()


def ensure_checkout(
    root: Path = ROOT,
    *,
    target: Path | None = None,
) -> str:
    """Make ext/cad-ci match the exact revision in dependencies.repos.

    Tracked local changes are never overwritten. An existing non-Git directory
    is also left untouched so bootstrap cannot silently delete user files.
    """

    url, wanted = dependency(root)
    target = target or (root / "ext" / "cad-ci")
    target.parent.mkdir(parents=True, exist_ok=True)

    if (target / ".git").is_dir():
        current = _git(target, "rev-parse", "HEAD")
        if current != wanted:
            dirty = _git(target, "status", "--porcelain", "--untracked-files=no")
            if dirty:
                raise RuntimeError(
                    "ext/cad-ci has tracked local changes; preserve them before updating"
                )
            _git(target, "remote", "set-url", "origin", url)
            _git(target, "fetch", "origin", wanted)
            _git(
                target,
                "-c",
                "advice.detachedHead=false",
                "checkout",
                "--detach",
                wanted,
            )
    else:
        if target.exists():
            raise RuntimeError(
                f"{target} exists but is not a Git checkout; move it aside first"
            )
        subprocess.run(
            ["git", "clone", "--quiet", "--no-checkout", "--", url, str(target)],
            check=True,
        )
        _git(
            target,
            "-c",
            "advice.detachedHead=false",
            "checkout",
            "--detach",
            wanted,
        )

    actual = _git(target, "rev-parse", "HEAD")
    if actual != wanted:
        raise RuntimeError(
            f"cad-ci revision mismatch: expected {wanted}, found {actual}"
        )
    return actual


def main() -> int:
    """Bootstrap the pinned tool and print the exact ready revision."""

    actual = ensure_checkout()
    print(f"Ready: cad-ci at {actual}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
