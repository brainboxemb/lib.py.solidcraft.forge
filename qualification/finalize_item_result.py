#!/usr/bin/env python3
"""Finalize one self-contained Forge example item.

The finalizer reads the command, stage and model-verification evidence already produced by
that item and writes one semantic qualification-result.json. It never reruns
SolidCraft.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from qualification.project_metadata import scpf_version
from qualification.results import collect as collect_results
from scpf.version import TESTED_SOLIDCRAFT_VERSION


def now() -> str:
    """Return the UTC timestamp format used by qualification results."""

    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def finalize(out: Path, slug: str, source_sha: str) -> dict:
    """Create and validate one structured result from existing item output."""

    result = collect_results(
        out,
        source_sha,
        scpf_version(),
        TESTED_SOLIDCRAFT_VERSION,
        now(),
        cases=(slug,),
    )
    case = result.get("cases", {}).get(slug)
    if not isinstance(case, dict) or case.get("status") != "pass":
        raise RuntimeError(f"{slug}: structured item result is not passing")
    target = out / "model_verify" / slug / "qualification-result.json"
    if not target.is_file() or target.stat().st_size == 0:
        raise RuntimeError(f"{slug}: qualification-result.json was not written")
    return case


def main() -> int:
    """Parse one item result finalization request."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    finalize(args.out.resolve(), args.slug, args.source_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
