"""Load task-oriented guide metadata and external content."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"


def load_guides():
    """Load guide metadata plus externally stored rendered content."""

    manifest = json.loads(
        (CONTENT / "guides.json").read_text(encoding="utf-8")
    )
    if manifest.get("schema") != 1:
        raise ValueError("unsupported guide content schema")

    guides = []
    for row in manifest.get("guides", []):
        body_path = CONTENT / row["body"]
        guides.append(
            {
                "slug": row["slug"],
                "title": row["title"],
                "summary": row["summary"],
                "body": body_path.read_text(encoding="utf-8"),
            }
        )
    return guides


GUIDES = load_guides()
