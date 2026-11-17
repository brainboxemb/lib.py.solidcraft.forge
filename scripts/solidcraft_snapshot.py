"""Generate a version-pinned SolidCraft command-contract snapshot.

The SolidCraft command registry is the source of truth.  Forge source is scanned
for literal command ids that occur in that registry; every matching command is
then described through engine.describe.

This deliberately avoids maintaining a second handwritten list of commands.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORGE_SOURCE = ROOT / "scpf" / "scpf"


def run_json(*args: str):
    completed = subprocess.run(
        list(args),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return json.loads(completed.stdout)


def catalog_commands(value) -> list[dict]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict) and isinstance(value.get("commands"), list):
        return value["commands"]
    raise ValueError("unexpected SolidCraft command-catalog shape")


def command_ids_from_source(known_ids: set[str]) -> list[str]:
    """Return SolidCraft command ids literally referenced by Forge runtime code."""
    found: set[str] = set()
    for path in sorted(FORGE_SOURCE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node.value in known_ids:
                    found.add(node.value)
    return sorted(found)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--source-ref", default="")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="fail when a Forge-used command has no typed input/output contract",
    )
    args = parser.parse_args()

    catalog_raw = run_json("solidcraft-cli", "commands")
    catalog = catalog_commands(catalog_raw)
    by_id = {
        entry["id"]: entry
        for entry in catalog
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
    used = command_ids_from_source(set(by_id))
    if not used:
        raise SystemExit("no SolidCraft command ids found in Forge runtime source")

    contracts: dict[str, dict] = {}
    gaps: list[dict[str, object]] = []
    contracts_dir = args.out / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)

    for command_id in used:
        description = run_json(
            "solidcraft-cli",
            "exec",
            "engine.describe",
            json.dumps({"command": command_id}, separators=(",", ":")),
        )
        contracts[command_id] = description
        missing = [
            key for key in ("input", "output")
            if description.get(key) is None
        ]
        if missing:
            gaps.append({"command": command_id, "missing": missing})

        (contracts_dir / f"{command_id}.json").write_text(
            json.dumps(description, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    manifest = {
        "solidcraft_version": args.version,
        "source_ref": args.source_ref or None,
        "generator": "solidcraft-cli commands + engine.describe",
        "forge_source": "scpf/scpf/**/*.py",
        "command_count": len(used),
        "commands": used,
        "contract_gaps": gaps,
    }
    (args.out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.out / "commands.json").write_text(
        json.dumps(catalog_raw, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    index_lines = [
        f"# SolidCraft {args.version} command contracts",
        "",
        "Generated from the pinned SolidCraft runtime command registry.",
        "",
        f"Forge-referenced commands: **{len(used)}**",
        "",
    ]
    for command_id in used:
        gap = next((g for g in gaps if g["command"] == command_id), None)
        suffix = (
            " — MISSING TYPED " + ", ".join(str(x) for x in gap["missing"])
            if gap else ""
        )
        index_lines.append(
            f"- `{command_id}` → `contracts/{command_id}.json`{suffix}"
        )
    index_lines.append("")
    (args.out / "README.md").write_text(
        "\n".join(index_lines),
        encoding="utf-8",
    )

    print(
        f"SolidCraft {args.version}: captured {len(used)} Forge-referenced "
        f"command contracts; typed-contract gaps: {len(gaps)}"
    )
    for gap in gaps:
        print(f"GAP {gap['command']}: {', '.join(gap['missing'])}")

    if args.strict and gaps:
        raise SystemExit(
            f"{len(gaps)} Forge-referenced SolidCraft command(s) lack a complete "
            "typed input/output contract"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
