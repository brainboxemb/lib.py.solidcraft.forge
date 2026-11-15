#!/usr/bin/env python3
"""Compare native AnchorFrame evidence with the explicit Placement baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TOL = 1e-3


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def body_map(data: dict) -> dict[str, dict]:
    return {
        row["name"]: row["bbox"]
        for row in data.get("bodies", [])
        if row.get("bbox") is not None
    }


def vector_delta(a, b) -> float:
    return max(abs(float(x) - float(y)) for x, y in zip(a, b))


def compare(anchor: dict, baseline: dict) -> dict:
    a = body_map(anchor)
    b = body_map(baseline)
    names = sorted(set(a) | set(b))
    rows = []
    ok = set(a) == set(b)

    for name in names:
        if name not in a or name not in b:
            rows.append({
                "name": name,
                "status": "missing",
                "anchorframe": a.get(name),
                "placement": b.get(name),
            })
            ok = False
            continue

        delta = max(
            vector_delta(a[name]["min"], b[name]["min"]),
            vector_delta(a[name]["max"], b[name]["max"]),
        )
        status = "pass" if delta <= TOL else "fail"
        rows.append({
            "name": name,
            "status": status,
            "max_delta_mm": delta,
            "anchorframe": a[name],
            "placement": b[name],
        })
        ok = ok and status == "pass"

    return {
        "status": "pass" if ok else "fail",
        "body_count": {"anchorframe": len(a), "placement": len(b)},
        "bodies": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anchor-initial", type=Path, required=True)
    parser.add_argument("--placement-initial", type=Path, required=True)
    parser.add_argument("--anchor-mutated", type=Path, required=True)
    parser.add_argument("--placement-mutated", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result = {
        "schema_version": 1,
        "tolerance_mm": TOL,
        "initial": compare(
            load(args.anchor_initial),
            load(args.placement_initial),
        ),
        "mutated": compare(
            load(args.anchor_mutated),
            load(args.placement_mutated),
        ),
    }
    result["status"] = (
        "pass"
        if result["initial"]["status"] == "pass"
        and result["mutated"]["status"] == "pass"
        else "fail"
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        "AnchorFrame vs Placement:",
        f"initial={result['initial']['status']}",
        f"mutated={result['mutated']['status']}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
