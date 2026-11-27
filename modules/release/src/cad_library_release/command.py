"""Parse owner release commands and publish through the local release module."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError

from .publish import publish_exact_release


_TAG = re.compile(r"^v([0-9]+\.[0-9]+\.[0-9]+)$")
_SHA = re.compile(r"^[0-9a-f]{40}$")


def parse_release_command(value: str) -> tuple[str, str]:
    """Return plain version and exact SHA from one strict /release command."""

    parts = value.strip().split()
    if len(parts) != 3 or parts[0] != "/release":
        raise ValueError("usage: /release vX.Y.Z <40-character-main-sha>")
    match = _TAG.fullmatch(parts[1])
    if match is None:
        raise ValueError("release tag must be vX.Y.Z")
    if _SHA.fullmatch(parts[2]) is None:
        raise ValueError(
            "release SHA must contain exactly 40 lowercase hex characters"
        )
    return match.group(1), parts[2]


def _write_output(path: Path, name: str, value: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{name}={value}\n")


def _parse(args) -> None:
    version, sha = parse_release_command(args.command)
    _write_output(args.github_output, "version", version)
    _write_output(args.github_output, "tag", f"v{version}")
    _write_output(args.github_output, "target_sha", sha)


def _publish(args) -> None:
    token = os.environ.get("GITHUB_TOKEN", "")
    notes = ""
    if args.notes_file and args.notes_file.is_file():
        notes = args.notes_file.read_text(encoding="utf-8")
    result = publish_exact_release(
        args.repository,
        args.version,
        args.target_sha,
        token,
        stable_ref=args.stable_ref,
        notes=notes,
    )
    _write_output(args.github_output, "tag", result.tag)
    _write_output(args.github_output, "target_sha", result.target_sha)
    _write_output(args.github_output, "release_url", result.url)
    _write_output(args.github_output, "created", str(result.created).lower())


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command_name", required=True)

    parse = sub.add_parser("parse")
    parse.add_argument("--command", required=True)
    parse.add_argument("--github-output", type=Path, required=True)
    parse.set_defaults(handler=_parse)

    publish = sub.add_parser("publish")
    publish.add_argument("--repository", required=True)
    publish.add_argument("--version", required=True)
    publish.add_argument("--target-sha", required=True)
    publish.add_argument("--stable-ref", default="main")
    publish.add_argument("--notes-file", type=Path)
    publish.add_argument("--github-output", type=Path, required=True)
    publish.set_defaults(handler=_publish)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        args.handler(args)
    except (ValueError, HTTPError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
