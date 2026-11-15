"""Execute a Forge result-binding plan through solidcraft-cli.

This runner is used by native qualification and other headless workflows. It
uses the same ExecutionState phase resolver as live GUI execution. Intermediate
SolidCraft files stay in a temporary directory, so a failed later phase never
replaces the requested final output.
"""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from .plan import ExecutionState, validate_document


class HeadlessPlanError(RuntimeError):
    """A headless Forge execution plan could not complete."""


def _phase_results(path):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HeadlessPlanError(
            f"Cannot read SolidCraft phase results {path}: {exc}"
        ) from exc
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return payload["results"]
    raise HeadlessPlanError(
        f"Unexpected SolidCraft phase results in {path}: {payload!r}"
    )


def execute_document(
    document,
    *,
    save,
    input_path=None,
    export=None,
    json_out=None,
    cli="solidcraft-cli",
    param_check="strict",
):
    """Execute one Forge plan with runtime result binding through the CLI."""
    validate_document(document)
    state = ExecutionState(document)
    save = Path(save)
    input_path = Path(input_path) if input_path is not None else None
    export = Path(export) if export is not None else None
    json_out = Path(json_out) if json_out is not None else None

    with tempfile.TemporaryDirectory(prefix="scpf-plan-") as directory:
        temporary = Path(directory)
        current = input_path
        final_export = None
        phase_number = 0

        while not state.done:
            phase = state.next_phase()
            phase_file = temporary / f"phase-{phase_number}.json"
            phase_results = temporary / f"phase-{phase_number}-results.json"
            phase_model = temporary / f"phase-{phase_number}.sc"
            phase_file.write_text(
                json.dumps({"commands": phase}, indent=2) + "\n",
                encoding="utf-8",
            )

            command = [
                cli,
                "run",
                str(phase_file),
                "--param-check",
                param_check,
                "--results",
                "--json-out",
                str(phase_results),
                "--save",
                str(phase_model),
            ]
            if current is not None:
                command.extend(["--in", str(current)])
            if state.pending_is_final and export is not None:
                suffix = export.suffix or ".step"
                final_export = temporary / f"final{suffix}"
                command.extend(["--out", str(final_export)])

            try:
                subprocess.run(command, check=True)
            except (OSError, subprocess.CalledProcessError) as exc:
                raise HeadlessPlanError(
                    f"SolidCraft phase {phase_number} failed: {exc}"
                ) from exc

            try:
                state.record_results(_phase_results(phase_results))
            except ValueError as exc:
                raise HeadlessPlanError(str(exc)) from exc
            current = phase_model
            phase_number += 1

        save.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(current, save)

        if export is not None:
            if final_export is None or not final_export.is_file():
                raise HeadlessPlanError(
                    "SolidCraft did not produce the requested final export"
                )
            export.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(final_export, export)

        summary = state.summary()
        if json_out is not None:
            json_out.parent.mkdir(parents=True, exist_ok=True)
            json_out.write_text(
                json.dumps(summary["results"], indent=2) + "\n",
                encoding="utf-8",
            )
        return summary


def read_document(path):
    """Load and validate a Forge execution document."""
    path = Path(path)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HeadlessPlanError(f"Cannot read SCPF plan {path}: {exc}") from exc
    try:
        return validate_document(document)
    except ValueError as exc:
        raise HeadlessPlanError(str(exc)) from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--save", type=Path, required=True)
    parser.add_argument("--in", dest="input_path", type=Path)
    parser.add_argument("--out", dest="export", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--cli", default="solidcraft-cli")
    parser.add_argument("--param-check", default="strict")
    args = parser.parse_args(argv)

    document = read_document(args.plan)
    try:
        result = execute_document(
            document,
            save=args.save,
            input_path=args.input_path,
            export=args.export,
            json_out=args.json_out,
            cli=args.cli,
            param_check=args.param_check,
        )
    except HeadlessPlanError as exc:
        parser.exit(1, f"SCPF headless plan: {exc}\n")
    print(
        f"SCPF headless plan: {result['completed']} commands "
        f"in {result['phases']} phase(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
