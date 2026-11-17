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


def _phase_commands(chunk, variables, active_sketch):
    """Resolve one replay phase and restore transient Sketch edit state.

    A saved .sc file preserves the Sketch feature but not the session's
    active-sketch flag. Headless replay starts a fresh CLI process for every
    runtime-binding phase, so an unfinished Sketch must be explicitly reopened
    before the next phase continues.
    """
    native = [resolved_command(item, variables) for item in chunk]
    if active_sketch is None:
        return native, 0
    return [
        {
            "command": "sketch.edit",
            "params": {"sketch": active_sketch},
        },
        *native,
    ], 1


def _active_sketch_after(items, results, active_sketch):
    """Track the transient Sketch edit state represented by replay commands."""
    if len(items) != len(results):
        raise HeadlessReplayError(
            "SolidCraft did not return one result per replay command"
        )

    active = active_sketch
    for item, result in zip(items, results):
        command = item["command"]
        if command == "sketch.create":
            sketch = result.get("sketch") if isinstance(result, dict) else None
            if not isinstance(sketch, int):
                raise HeadlessReplayError(
                    f"sketch.create did not return a sketch id: {result!r}"
                )
            active = sketch
        elif command == "sketch.edit":
            target = item.get("params", {}).get("sketch")
            if not isinstance(target, (int, str)):
                raise HeadlessReplayError(
                    f"sketch.edit has no usable sketch target: {target!r}"
                )
            active = target
        elif command in (
            "sketch.finish",
            "sketch.finish_auto_constrain",
            "sketch.cancel",
        ):
            active = None
        elif command == "file.new":
            active = None
    return active


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
    active_sketch = None

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
            if is_replay_document(document):
                native, transport_prefix = _phase_commands(
                    chunk,
                    variables,
                    active_sketch,
                )
                replay_native = native[transport_prefix:]
            else:
                native = [
                    {
                        "command": item["command"],
                        "params": item.get("params", {}),
                    }
                    for item in chunk
                ]
                transport_prefix = 0
                replay_native = native
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
            if len(results) != len(native):
                raise HeadlessReplayError(
                    "SolidCraft did not return one result per native phase command"
                )

            replay_results = results[transport_prefix:]
            if is_replay_document(document):
                try:
                    bindings = apply_bindings(
                        chunk,
                        replay_results,
                        variables,
                    )
                except ValueError as exc:
                    raise HeadlessReplayError(str(exc)) from exc
                active_sketch = _active_sketch_after(
                    replay_native,
                    replay_results,
                    active_sketch,
                )
            else:
                bindings = [{} for _ in chunk]

            for item, native_item, bound in zip(
                chunk,
                replay_native,
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

            all_results.extend(replay_results)
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



def main(argv=None):
    """Run an SCPF replay file through solidcraft-cli."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("replay", type=Path)
    parser.add_argument("--save", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--results", type=Path)
    parser.add_argument("--replay-log", type=Path)
    parser.add_argument("--solidcraft-cli", default="solidcraft-cli")
    args = parser.parse_args(argv)

    try:
        document = json.loads(args.replay.read_text(encoding="utf-8"))
        result = run_document(
            document,
            save=args.save,
            export=args.out,
            results_out=args.results,
            replay_log_out=args.replay_log,
            executable=args.solidcraft_cli,
        )
    except (OSError, json.JSONDecodeError, HeadlessReplayError) as exc:
        parser.exit(1, f"SCPF headless replay: {exc}\n")

    print(
        f"Headless SolidCraft: {result['completed']} commands applied; "
        f"{len(result['variables'])} replay variable(s) bound"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
