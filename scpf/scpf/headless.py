"""Headless execution of SCPF replay documents through solidcraft-cli."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

from .replay import (
    apply_bindings,
    is_replay_document,
    replay_chunks,
    replay_log,
    resolved_command,
    validate_replay_document,
)


class HeadlessReplayError(RuntimeError):
    """A replay could not be completed by solidcraft-cli."""


def run_document(
    document,
    *,
    save,
    export=None,
    results_out=None,
    replay_log_out=None,
    executable="solidcraft-cli",
    env=None,
    work_dir=None,
):
    """Execute one replay document in fresh solidcraft-cli processes.

    Intermediate .sc files are private checkpoints between replay phases. The
    final save path is written only by the last successful phase.
    """
    try:
        validate_replay_document(document)
        chunks = (
            replay_chunks(document["commands"])
            if is_replay_document(document)
            else [document["commands"]]
        )
    except ValueError as exc:
        raise HeadlessReplayError(str(exc)) from exc

    save = Path(save)
    save.parent.mkdir(parents=True, exist_ok=True)
    if export is not None:
        export = Path(export)
        export.parent.mkdir(parents=True, exist_ok=True)
    if results_out is not None:
        results_out = Path(results_out)
        results_out.parent.mkdir(parents=True, exist_ok=True)
    if replay_log_out is not None:
        replay_log_out = Path(replay_log_out)
        replay_log_out.parent.mkdir(parents=True, exist_ok=True)

    variables = {}
    entries = []
    all_results = []

    owned_tmp = None
    if work_dir is None:
        owned_tmp = tempfile.TemporaryDirectory(prefix="scpf-replay-")
        work = Path(owned_tmp.name)
    else:
        work = Path(work_dir)
        work.mkdir(parents=True, exist_ok=True)

    previous = None
    command_index = 0
    try:
        for phase_index, chunk in enumerate(chunks, start=1):
            native = [
                resolved_command(item, variables)
                if is_replay_document(document)
                else {
                    "command": item["command"],
                    "params": item.get("params", {}),
                }
                for item in chunk
            ]
            script = work / f"phase-{phase_index}.json"
            result_path = work / f"phase-{phase_index}-results.json"
            last = phase_index == len(chunks)
            phase_save = save if last else work / f"phase-{phase_index}.sc"
            script.write_text(
                json.dumps({"commands": native}, indent=2) + "\n",
                encoding="utf-8",
            )

            command = [
                executable,
                "run",
                str(script),
                "--param-check",
                "strict",
                "--results",
                "--json-out",
                str(result_path),
                "--save",
                str(phase_save),
            ]
            if previous is not None:
                command.extend(["--in", str(previous)])
            if last and export is not None:
                command.extend(["--out", str(export)])

            try:
                completed = subprocess.run(
                    command,
                    check=True,
                    text=True,
                    capture_output=True,
                    env=env if env is not None else os.environ.copy(),
                )
            except (OSError, subprocess.CalledProcessError) as exc:
                stderr = getattr(exc, "stderr", "") or ""
                raise HeadlessReplayError(
                    f"solidcraft-cli replay phase {phase_index} failed: "
                    f"{stderr.strip() or exc}"
                ) from exc

            try:
                results = json.loads(result_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise HeadlessReplayError(
                    f"cannot read replay results for phase {phase_index}"
                ) from exc
            if not isinstance(results, list):
                raise HeadlessReplayError(
                    f"replay phase {phase_index} did not return a result list"
                )

            if is_replay_document(document):
                try:
                    bindings = apply_bindings(
                        chunk,
                        results,
                        variables,
                    )
                except ValueError as exc:
                    raise HeadlessReplayError(str(exc)) from exc
            else:
                if len(results) != len(chunk):
                    raise HeadlessReplayError(
                        "SolidCraft did not return one result per command"
                    )
                bindings = [{} for _ in chunk]

            for item, native_item, bound in zip(
                chunk,
                native,
                bindings,
            ):
                entry = {
                    "index": command_index,
                    "command": item["command"],
                    "resolved_params": native_item["params"],
                }
                if bound:
                    entry["bindings"] = bound
                entries.append(entry)
                command_index += 1

            all_results.extend(results)
            previous = phase_save

        log = replay_log(document, variables, entries)
        if results_out is not None:
            results_out.write_text(
                json.dumps(all_results, indent=2) + "\n",
                encoding="utf-8",
            )
        if replay_log_out is not None:
            replay_log_out.write_text(
                json.dumps(log, indent=2) + "\n",
                encoding="utf-8",
            )
        return {
            "completed": len(entries),
            "variables": dict(variables),
            "results": all_results,
            "replay_log": log,
        }
    finally:
        if owned_tmp is not None:
            owned_tmp.cleanup()
