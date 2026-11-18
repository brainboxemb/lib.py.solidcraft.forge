#!/usr/bin/env python3
"""Retrying compare-and-swap publisher for generated branches.

Correctness does not depend on GitHub Actions concurrency queues. Every attempt
starts from the latest remote branch head, applies one pure namespace mutation,
and performs a normal non-force push. Push races are retried.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]


class StaleSource(RuntimeError):
    pass


def _run(
    args: list[str],
    *,
    cwd: Path = ROOT,
    check: bool = True,
    capture: bool = False,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def _output(args: list[str], *, cwd: Path = ROOT) -> str:
    return _run(args, cwd=cwd, capture=True).stdout.strip()


def remote_ref(remote: str, ref: str, *, cwd: Path = ROOT) -> str | None:
    completed = _run(
        ["git", "ls-remote", remote, f"refs/heads/{ref}"],
        cwd=cwd,
        capture=True,
    )
    line = completed.stdout.strip()
    return line.split()[0] if line else None


def assert_fresh(
    remote: str,
    source_ref: str | None,
    expected_source: str | None,
    *,
    cwd: Path = ROOT,
) -> None:
    if not source_ref or not expected_source:
        return
    actual = remote_ref(remote, source_ref, cwd=cwd)
    if actual != expected_source:
        raise StaleSource(
            f"stale source: {source_ref} is {actual or 'missing'}, "
            f"candidate is {expected_source}"
        )


def _clean_except(root: Path, keep: set[str]) -> None:
    for path in root.iterdir():
        if path.name in {".git", *keep}:
            continue
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()


def _copy_tree(source: Path, target: Path) -> None:
    source = Path(source)
    target = Path(target)
    if not source.is_dir():
        raise RuntimeError(f"publish source is not a directory: {source}")
    target.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if ".git" in relative.parts:
            continue
        destination = target / relative
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)


def apply_mutation(
    worktree: Path,
    operation: str,
    source: Path | None,
    destination: str | None,
) -> None:
    if operation == "replace-dir":
        if source is None or not destination:
            raise ValueError("replace-dir requires source and destination")
        target = worktree / destination
        if target.exists():
            shutil.rmtree(target)
        _copy_tree(source, target)
        return

    if operation == "remove-dir":
        if not destination:
            raise ValueError("remove-dir requires destination")
        target = worktree / destination
        if target.exists():
            shutil.rmtree(target)
        parent = target.parent
        if parent != worktree and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
        return

    if operation == "replace-stable-pages":
        if source is None:
            raise ValueError("replace-stable-pages requires source")
        _clean_except(worktree, {"previews"})
        _copy_tree(source, worktree)
        return

    raise ValueError(f"unknown mutation: {operation}")


def publish(
    *,
    branch: str,
    operation: str,
    source: Path | None = None,
    destination: str | None = None,
    remote: str = "origin",
    source_ref: str | None = None,
    expected_source: str | None = None,
    message: str,
    retries: int = 5,
    cwd: Path = ROOT,
) -> str:
    if retries < 1:
        raise ValueError("retries must be positive")

    for attempt in range(1, retries + 1):
        assert_fresh(remote, source_ref, expected_source, cwd=cwd)
        _run(["git", "fetch", "--no-tags", remote, branch], cwd=cwd)
        base = remote_ref(remote, branch, cwd=cwd)
        if not base:
            raise RuntimeError(
                f"generated branch {branch!r} does not exist; bootstrap it explicitly"
            )

        with tempfile.TemporaryDirectory(prefix="generated-publish-") as tmp:
            worktree = Path(tmp) / "tree"
            _run(["git", "worktree", "add", "--detach", str(worktree), base], cwd=cwd)
            try:
                apply_mutation(worktree, operation, source, destination)
                status = _output(["git", "status", "--porcelain"], cwd=worktree)
                if not status:
                    return base

                _run(["git", "config", "user.name", "github-actions[bot]"], cwd=worktree)
                _run(
                    [
                        "git",
                        "config",
                        "user.email",
                        "41898282+github-actions[bot]@users.noreply.github.com",
                    ],
                    cwd=worktree,
                )
                _run(["git", "add", "-A"], cwd=worktree)
                _run(["git", "commit", "-m", message], cwd=worktree)
                candidate = _output(["git", "rev-parse", "HEAD"], cwd=worktree)

                # Re-check immediately before the write. This rejects an old
                # verification run even when it spent a long time building.
                assert_fresh(remote, source_ref, expected_source, cwd=cwd)
                pushed = _run(
                    ["git", "push", remote, f"HEAD:refs/heads/{branch}"],
                    cwd=worktree,
                    check=False,
                    capture=True,
                )
                if pushed.returncode == 0:
                    return candidate
            finally:
                _run(
                    ["git", "worktree", "remove", "--force", str(worktree)],
                    cwd=cwd,
                    check=False,
                )

        if attempt == retries:
            raise RuntimeError(
                f"could not publish {branch}/{destination or '<root>'} "
                f"after {retries} compare-and-swap attempts"
            )
        time.sleep(min(0.25 * attempt, 1.0))

    raise AssertionError("unreachable")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation",
        choices=("replace-dir", "remove-dir", "replace-stable-pages"),
    )
    parser.add_argument("--branch", required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--destination")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--source-ref")
    parser.add_argument("--expected-source")
    parser.add_argument("--message", required=True)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    commit = publish(
        branch=args.branch,
        operation=args.operation,
        source=args.source,
        destination=args.destination,
        remote=args.remote,
        source_ref=args.source_ref,
        expected_source=args.expected_source,
        message=args.message,
        retries=args.retries,
    )
    print(f"Published {args.branch} at {commit}")
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as handle:
            handle.write(f"commit={commit}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
