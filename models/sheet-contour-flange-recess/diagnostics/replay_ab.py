"""Owner-local A/B harness for Forge #73 live/headless replay.

This diagnostic does not change model geometry or Forge replay semantics. It
runs the exact replay document produced by the verification fixture through:

1. normal phased headless replay (save/reopen between replay chunks);
2. one fully resolved native script in a single SolidCraft CLI process;
3. optionally, the unchanged replay document in one running SolidCraft GUI.

The live case is opt-in because it replaces the active GUI design with a new
blank design before replay. Save unrelated GUI work first.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from scpf.headless import HeadlessReplayError, run_document
from scpf.live import LiveError, new_design, send_document
from scpf.replay import replay_chunks
from scpf.runner import run_script


ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / "models/sheet-contour-flange-recess/scpf/model.py"


def resolved_document(log: dict) -> dict:
    """Convert one replay log into the exact resolved native command stream."""
    commands = log.get("commands")
    if not isinstance(commands, list) or not commands:
        raise RuntimeError("replay log has no commands")
    return {
        "commands": [
            {
                "command": row["command"],
                "params": row["resolved_params"],
            }
            for row in commands
        ]
    }


def run_native(cli: str, document: dict, output: Path) -> dict:
    """Run one resolved command document in a single SolidCraft CLI process."""
    script = output / "single-process.json"
    results = output / "single-process-results.json"
    save = output / "single-process.sc"
    script.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    command = [
        cli,
        "run",
        str(script),
        "--param-check",
        "strict",
        "--results",
        "--json-out",
        str(results),
        "--save",
        str(save),
    ]
    completed = subprocess.run(command, text=True, capture_output=True)
    return {
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "saved": save.exists(),
    }


def _run_cli_document(
    cli: str,
    commands: list[dict],
    script: Path,
    save: Path,
    *,
    input_design: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run one already-resolved native command segment."""
    script.write_text(
        json.dumps({"commands": commands}, indent=2) + "\n",
        encoding="utf-8",
    )
    argv = [
        cli,
        "run",
        str(script),
        "--param-check",
        "strict",
        "--save",
        str(save),
    ]
    if input_design is not None:
        argv.extend(["--in", str(input_design)])
    return subprocess.run(argv, text=True, capture_output=True)


def run_reopen_boundaries(
    cli: str,
    document: dict,
    replay_log_data: dict,
    output: Path,
) -> dict:
    """Test one save/reopen after each native replay-chunk boundary.

    The normal phased replay saves after every replay chunk. This matrix keeps
    every other chunk in one process and inserts exactly one save/reopen, so it
    identifies the first semantic boundary that changes SolidCraft's result.
    Transport-only context restore commands are injected only at the start of
    the reopened suffix.
    """
    authored_chunks = replay_chunks(document["commands"])
    resolved = resolved_document(replay_log_data)["commands"]

    native_chunks = []
    offset = 0
    for chunk in authored_chunks:
        end = offset + len(chunk)
        native_chunks.append(resolved[offset:end])
        offset = end
    if offset != len(resolved):
        raise RuntimeError("replay chunk lengths do not match resolved log")

    phase_dir = output / "phases"
    transports = []
    for phase_number, native_chunk in enumerate(native_chunks, start=1):
        phase = json.loads(
            (phase_dir / f"phase-{phase_number}.json").read_text(
                encoding="utf-8"
            )
        )
        phase_commands = phase["commands"]
        transport_count = len(phase_commands) - len(native_chunk)
        if transport_count < 0:
            raise RuntimeError(
                f"phase {phase_number} is shorter than its authored chunk"
            )
        transports.append(phase_commands[:transport_count])

    boundary_root = output / "reopen-boundaries"
    boundary_root.mkdir(parents=True, exist_ok=True)
    results = {}

    for boundary in range(1, len(native_chunks)):
        case = boundary_root / f"after-phase-{boundary}"
        case.mkdir(parents=True, exist_ok=True)
        checkpoint = case / "checkpoint.sc"
        final = case / "final.sc"

        prefix_commands = [
            command
            for chunk in native_chunks[:boundary]
            for command in chunk
        ]
        suffix_commands = [
            *transports[boundary],
            *[
                command
                for chunk in native_chunks[boundary:]
                for command in chunk
            ],
        ]

        prefix = _run_cli_document(
            cli,
            prefix_commands,
            case / "prefix.json",
            checkpoint,
        )
        if prefix.returncode != 0:
            results[str(boundary)] = {
                "status": "prefix-fail",
                "after_phase": boundary,
                "stderr": prefix.stderr,
            }
            continue

        suffix = _run_cli_document(
            cli,
            suffix_commands,
            case / "suffix.json",
            final,
            input_design=checkpoint,
        )
        results[str(boundary)] = {
            "status": "pass" if suffix.returncode == 0 else "fail",
            "after_phase": boundary,
            "transport": [
                command["command"] for command in transports[boundary]
            ],
            "stderr": suffix.stderr,
            "saved": final.exists(),
        }

    # Phase 6 contains both the contour-flange creation and the read-only
    # model.faces query. Split once inside that phase to prove whether reopening
    # the freshly created sheet body itself is sufficient.
    if (
        len(native_chunks) >= 7
        and len(native_chunks[5]) == 2
        and native_chunks[5][0]["command"] == "sheet.flange"
        and native_chunks[5][1]["command"] == "model.faces"
    ):
        case = boundary_root / "after-sheet-flange"
        case.mkdir(parents=True, exist_ok=True)
        checkpoint = case / "checkpoint.sc"
        final = case / "final.sc"
        prefix_commands = [
            *[
                command
                for chunk in native_chunks[:5]
                for command in chunk
            ],
            native_chunks[5][0],
        ]
        suffix_commands = [
            native_chunks[5][1],
            *[
                command
                for chunk in native_chunks[6:]
                for command in chunk
            ],
        ]
        prefix = _run_cli_document(
            cli,
            prefix_commands,
            case / "prefix.json",
            checkpoint,
        )
        if prefix.returncode != 0:
            results["after_sheet_flange"] = {
                "status": "prefix-fail",
                "stderr": prefix.stderr,
            }
        else:
            suffix = _run_cli_document(
                cli,
                suffix_commands,
                case / "suffix.json",
                final,
                input_design=checkpoint,
            )
            results["after_sheet_flange"] = {
                "status": "pass" if suffix.returncode == 0 else "fail",
                "stderr": suffix.stderr,
                "saved": final.exists(),
            }

    return results


def run_live(document: dict, connect: str) -> dict:
    """Replay the unchanged document in a fresh design in the running GUI."""
    try:
        new_design(name="Forge #73 contour flange recess", connect=connect)
        result = send_document(document, connect=connect)
    except LiveError as exc:
        return {
            "status": "fail",
            "error": str(exc),
        }

    return {
        "status": "pass",
        "completed": result["completed"],
        "variables": result["variables"],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solidcraft-cli", default="solidcraft-cli")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("diagnostic-73"),
    )
    parser.add_argument(
        "--connect",
        help=(
            "Also run live replay through the running SolidCraft GUI. "
            "Use 'auto' or a control port/address. This creates a new GUI design."
        ),
    )
    args = parser.parse_args(argv)

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    document = run_script(MODEL)
    (output / "replay.json").write_text(
        json.dumps(document, indent=2) + "\n",
        encoding="utf-8",
    )

    phased_log = output / "phased-replay-log.json"
    summary = {
        "fixture": "sheet-contour-flange-recess",
        "phased_headless": {},
        "single_process_headless": {},
        "reopen_boundaries": {},
        "live": {"status": "not-run"},
    }

    try:
        phased = run_document(
            document,
            save=output / "phased.sc",
            results_out=output / "phased-results.json",
            replay_log_out=phased_log,
            executable=args.solidcraft_cli,
            work_dir=output / "phases",
        )
    except HeadlessReplayError as exc:
        summary["phased_headless"] = {
            "status": "fail",
            "error": str(exc),
        }
        (output / "summary.json").write_text(
            json.dumps(summary, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(summary, indent=2))
        return 1

    summary["phased_headless"] = {
        "status": "pass",
        "completed": phased["completed"],
        "variables": phased["variables"],
    }

    log = json.loads(phased_log.read_text(encoding="utf-8"))
    native = resolved_document(log)
    single = run_native(args.solidcraft_cli, native, output)
    summary["single_process_headless"] = {
        "status": "pass" if single["returncode"] == 0 else "fail",
        **single,
    }
    summary["reopen_boundaries"] = run_reopen_boundaries(
        args.solidcraft_cli,
        document,
        log,
        output,
    )

    if args.connect is not None:
        summary["live"] = run_live(document, args.connect)

    (output / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))

    required = [
        summary["phased_headless"]["status"],
        summary["single_process_headless"]["status"],
    ]
    if args.connect is not None:
        required.append(summary["live"]["status"])
    return 0 if all(status == "pass" for status in required) else 1


if __name__ == "__main__":
    raise SystemExit(main())
