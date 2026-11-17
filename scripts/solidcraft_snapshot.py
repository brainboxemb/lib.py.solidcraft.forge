"""Generate and audit a version-pinned SolidCraft command-contract snapshot.

The SolidCraft runtime registry is the primary source of truth. Forge source is
scanned for command ids and every Forge-used command is captured with
engine.describe.

The pinned audit does not need SolidCraft installed. It proves that the checked
in snapshot still covers the commands referenced by the current Forge source.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORGE_SOURCE = ROOT / "scpf" / "scpf"
VERSION_SOURCE = FORGE_SOURCE / "version.py"
COMMAND_ID = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+$")


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


def tested_version() -> str:
    text = VERSION_SOURCE.read_text(encoding="utf-8")
    match = re.search(
        r'^TESTED_SOLIDCRAFT_VERSION = "([^"]+)"$',
        text,
        re.MULTILINE,
    )
    if match is None:
        raise ValueError("cannot read TESTED_SOLIDCRAFT_VERSION")
    return match.group(1)


def source_string_literals() -> set[str]:
    found: set[str] = set()
    for path in sorted(FORGE_SOURCE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                found.add(node.value)
    return found


def command_ids_from_source(known_ids: set[str]) -> list[str]:
    return sorted(source_string_literals() & known_ids)


def unknown_command_like_ids(known_ids: set[str]) -> list[str]:
    """Find command-looking Forge strings in known SolidCraft namespaces."""
    prefixes = {command_id.split(".", 1)[0] for command_id in known_ids}
    return sorted(
        value
        for value in source_string_literals()
        if COMMAND_ID.fullmatch(value)
        and value.split(".", 1)[0] in prefixes
        and value not in known_ids
    )


def gaps_from_contracts(snapshot: Path, command_ids: list[str]) -> list[dict]:
    gaps = []
    for command_id in command_ids:
        path = snapshot / "contracts" / f"{command_id}.json"
        if not path.is_file():
            raise ValueError(f"missing SolidCraft contract snapshot: {path}")
        contract = json.loads(path.read_text(encoding="utf-8"))
        if contract.get("id") != command_id:
            raise ValueError(
                f"{path}: expected id {command_id!r}, found {contract.get('id')!r}"
            )
        missing = [
            key for key in ("input", "output")
            if contract.get(key) is None
        ]
        if missing:
            gaps.append({"command": command_id, "missing": missing})
    return gaps


def check_pinned(snapshot: Path) -> int:
    manifest_path = snapshot / "manifest.json"
    catalog_path = snapshot / "commands.json"
    if not manifest_path.is_file() or not catalog_path.is_file():
        raise SystemExit(
            f"{snapshot}: expected manifest.json and commands.json"
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    catalog_raw = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog = catalog_commands(catalog_raw)
    known_ids = {
        entry["id"]
        for entry in catalog
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }

    expected_version = tested_version()
    if manifest.get("solidcraft_version") != expected_version:
        raise SystemExit(
            "SolidCraft snapshot version mismatch: "
            f"Forge targets {expected_version}, snapshot has "
            f"{manifest.get('solidcraft_version')!r}"
        )

    actual = command_ids_from_source(known_ids)
    recorded = manifest.get("commands")
    if recorded != actual:
        missing = sorted(set(actual) - set(recorded or []))
        stale = sorted(set(recorded or []) - set(actual))
        raise SystemExit(
            "SolidCraft snapshot does not match Forge source; "
            f"missing={missing}, stale={stale}"
        )

    contract_files = {
        path.stem
        for path in (snapshot / "contracts").glob("*.json")
    }
    if contract_files != set(actual):
        raise SystemExit(
            "SolidCraft contract-file set does not match Forge source; "
            f"missing={sorted(set(actual) - contract_files)}, "
            f"stale={sorted(contract_files - set(actual))}"
        )

    actual_gaps = gaps_from_contracts(snapshot, actual)
    if manifest.get("contract_gaps", []) != actual_gaps:
        raise SystemExit(
            "SolidCraft typed-contract gap list is stale; "
            f"expected {actual_gaps}, recorded {manifest.get('contract_gaps', [])}"
        )

    print(
        f"SolidCraft {expected_version}: pinned snapshot covers "
        f"{len(actual)} Forge-used commands"
    )
    for gap in actual_gaps:
        print(
            f"TYPED GAP {gap['command']}: "
            + ", ".join(gap["missing"])
        )
    return 0


def generate(out: Path, version: str, source_ref: str, strict: bool) -> int:
    catalog_raw = run_json("solidcraft-cli", "commands")
    catalog = catalog_commands(catalog_raw)
    known_ids = {
        entry["id"]
        for entry in catalog
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }

    used = command_ids_from_source(known_ids)
    if not used:
        raise SystemExit("no SolidCraft command ids found in Forge runtime source")

    if out.exists():
        shutil.rmtree(out)
    contracts_dir = out / "contracts"
    contracts_dir.mkdir(parents=True)

    gaps: list[dict[str, object]] = []
    for command_id in used:
        description = run_json(
            "solidcraft-cli",
            "exec",
            "engine.describe",
            json.dumps({"command": command_id}, separators=(",", ":")),
        )
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
        "solidcraft_version": version,
        "source_ref": source_ref or None,
        "generator": "solidcraft-cli commands + engine.describe",
        "forge_source": "scpf/scpf/**/*.py",
        "command_count": len(used),
        "commands": used,
        "contract_gaps": gaps,
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (out / "commands.json").write_text(
        json.dumps(catalog_raw, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    index_lines = [
        f"# SolidCraft {version} command contracts",
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
    (out / "README.md").write_text(
        "\n".join(index_lines),
        encoding="utf-8",
    )

    print(
        f"SolidCraft {version}: captured {len(used)} Forge-referenced "
        f"command contracts; typed-contract gaps: {len(gaps)}"
    )
    for gap in gaps:
        print(f"GAP {gap['command']}: {', '.join(gap['missing'])}")

    if strict and gaps:
        raise SystemExit(
            f"{len(gaps)} Forge-referenced SolidCraft command(s) lack a complete "
            "typed input/output contract"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--out", type=Path)
    mode.add_argument("--check-pinned", type=Path)
    parser.add_argument("--version")
    parser.add_argument("--source-ref", default="")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="fail generation when a Forge-used command has no typed input/output contract",
    )
    args = parser.parse_args()

    if args.check_pinned is not None:
        return check_pinned(args.check_pinned)

    if not args.version:
        parser.error("--version is required with --out")
    return generate(args.out, args.version, args.source_ref, args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
