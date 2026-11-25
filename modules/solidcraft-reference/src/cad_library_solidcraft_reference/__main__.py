"""Capture or verify canonical SolidCraft command references."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import capture_snapshot, root_runtime_pin, verify_pinned_reference, verify_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    capture = subparsers.add_parser("capture")
    capture.add_argument("--image", required=True)
    capture.add_argument("--version", required=True)
    capture.add_argument("--upstream-commit", required=True)
    capture.add_argument("--runtime-release", required=True)
    capture.add_argument("--out", type=Path, required=True)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--repo-root", type=Path, default=Path("."))
    verify.add_argument("--image")
    verify.add_argument("--version")
    verify.add_argument("--snapshot", type=Path)

    args = parser.parse_args()
    if args.command == "capture":
        count = capture_snapshot(
            image=args.image,
            version=args.version,
            upstream_commit=args.upstream_commit,
            runtime_release=args.runtime_release,
            out=args.out,
        )
        print(
            f"Captured SolidCraft {args.version}: {count} commands "
            f"from {args.image}"
        )
        return 0

    explicit = (args.image, args.version, args.snapshot)
    if any(value is not None for value in explicit):
        if not all(value is not None for value in explicit):
            parser.error(
                "--image, --version and --snapshot must be supplied together"
            )
        count = verify_snapshot(
            image=args.image,
            version=args.version,
            snapshot=args.snapshot,
        )
        print(
            f"SolidCraft reference matches {args.image}: "
            f"{args.version}; {count} commands"
        )
        return 0

    repo = args.repo_root.resolve()
    count = verify_pinned_reference(repo)
    image, version = root_runtime_pin(repo)
    print(
        f"SolidCraft reference matches root pin {image}: "
        f"{version}; {count} commands"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
