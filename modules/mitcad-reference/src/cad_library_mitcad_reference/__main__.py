"""Capture or verify version-pinned Mitcad command references."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import capture_snapshot, verify_runtime_snapshot, verify_source_snapshot


VERSION = "0.70.0"
RELEASE_TAG = "v0.70.0"
UPSTREAM_COMMIT = "806a4210126ab977ba678708dd476496ddbd2968"
SOURCE_REFERENCE_BLOB = "40240776bc6885e228bf2fbd8e2534875aa61b85"
RUNTIME_REFERENCE_BLOB = "c839084ba223e814370a55c761644da362fabc93"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    capture = sub.add_parser("capture")
    capture.add_argument("--mitcad-cli", required=True)
    capture.add_argument(
        "--out",
        type=Path,
        default=Path("docs/reference/mitcad") / VERSION,
    )

    verify = sub.add_parser("verify")
    verify.add_argument("--mitcad-cli")
    verify.add_argument(
        "--snapshot",
        type=Path,
        default=Path("docs/reference/mitcad") / VERSION,
    )

    args = parser.parse_args()
    if args.command == "capture":
        count = capture_snapshot(
            executable=args.mitcad_cli,
            version=VERSION,
            upstream_commit=UPSTREAM_COMMIT,
            release_tag=RELEASE_TAG,
            source_reference_blob=SOURCE_REFERENCE_BLOB,
            runtime_reference_blob=RUNTIME_REFERENCE_BLOB,
            out=args.out,
        )
        print(f"Captured Mitcad {VERSION}: {count} model commands")
        return 0

    if args.mitcad_cli:
        count = verify_runtime_snapshot(
            executable=args.mitcad_cli,
            version=VERSION,
            snapshot=args.snapshot,
            source_reference_blob=SOURCE_REFERENCE_BLOB,
            runtime_reference_blob=RUNTIME_REFERENCE_BLOB,
        )
        print(f"Mitcad {VERSION} runtime reference matches: {count} commands")
    else:
        verify_source_snapshot(
            args.snapshot,
            reference_blob=SOURCE_REFERENCE_BLOB,
        )
        print(
            f"Mitcad {VERSION} source reference matches "
            f"{SOURCE_REFERENCE_BLOB}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
