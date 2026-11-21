"""SCPF: compile Python CAD models or replay command JSON in SolidCraft."""
import argparse
import json
from pathlib import Path
import sys
import warnings

from .live import LiveError, new_design, send_document
from .replay import validate_replay_document
from .runner import run_script
from .version import (
    TESTED_SOLIDCRAFT_VERSION,
    check_cli_version,
    forge_revision,
    package_version,
)


_PACKAGE_ROOT = Path(__file__).resolve().parent


def _source_location(exc, fallback):
    """Return the best user-source location represented by one exception."""

    if isinstance(exc, SyntaxError):
        filename = getattr(exc, "filename", None)
        lineno = getattr(exc, "lineno", None)
        if filename:
            return Path(filename), lineno

    location = None
    traceback = exc.__traceback__
    while traceback is not None:
        filename = Path(traceback.tb_frame.f_code.co_filename).resolve()
        if filename != _PACKAGE_ROOT and _PACKAGE_ROOT not in filename.parents:
            location = (filename, traceback.tb_lineno)
        traceback = traceback.tb_next

    if location is not None:
        return location
    return Path(fallback).resolve(), None


def _debug_identity():
    """Write diagnostic package identity without changing the exception."""

    print(f"SCPF {package_version()}", file=sys.stderr)
    revision = forge_revision()
    if revision is not None:
        print(f"Forge revision: {revision}", file=sys.stderr)
    print(
        f"Tested SolidCraft: {TESTED_SOLIDCRAFT_VERSION}",
        file=sys.stderr,
    )


def _exit_model_error(parser, exc, script):
    """Exit with a compact model/build/compiler error."""

    path, line = _source_location(exc, script)
    location = f"{path}:{line}" if line is not None else str(path)
    parser.exit(
        1,
        (
            f"SCPF {package_version()} error\n"
            f"{location}\n\n"
            f"{type(exc).__name__}: {exc}\n\n"
            "Run again with --debug for the full Python traceback.\n"
        ),
    )


def read_command_file(path):
    """Load an existing SolidCraft command document without translating it."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read SolidCraft JSON {path}: {exc}") from exc
    return validate_replay_document(document)


def _check_model(argv):
    """Build and compile one model without starting SolidCraft."""
    parser = argparse.ArgumentParser(
        prog="scpf check",
        description="Build and compile an SCPF model without native SolidCraft.",
    )
    parser.add_argument("script", type=Path)
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show the full Python traceback for model/build failures",
    )
    args = parser.parse_args(argv)

    failure = None
    document = None
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            document = run_script(args.script)
        except Exception as exc:  # CLI boundary: report model/build/compile failures cleanly.
            failure = exc

    for item in caught:
        print(f"SCPF check warning: {item.message}", file=sys.stderr)

    if failure is not None:
        if args.debug:
            _debug_identity()
            raise failure
        _exit_model_error(parser, failure, args.script)

    print(
        f"SCPF check PASS: {args.script}: "
        f"{len(document['commands'])} SolidCraft commands"
    )
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and argv[0] == "check":
        return _check_model(argv[1:])

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version",
        action="version",
        version=f"SCPF {package_version()}",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show the full Python traceback for model/build failures",
    )
    parser.add_argument(
        "script", type=Path,
        help="SCPF model.py, or 'replay' followed by an existing SolidCraft JSON file",
    )
    parser.add_argument("replay_file", nargs="?", type=Path)
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--out", type=Path, help="Write compiled SolidCraft command JSON")
    output.add_argument(
        "--connect", nargs="?", const="auto", metavar="PORT",
        help="Send commands to open SolidCraft; optional 127.0.0.1:PORT",
    )
    parser.add_argument(
        "--new", action="store_true",
        help="Replace the active SolidCraft design with a new empty design before --connect",
    )
    parser.add_argument(
        "--replay-log", type=Path,
        help="Write the concrete runtime variable bindings used by this execution",
    )
    args = parser.parse_args(argv)

    if args.new and args.connect is None:
        parser.error("--new requires --connect")

    replay = str(args.script) == "replay"
    if replay:
        if args.new:
            parser.error("--new is for model scripts, not replay")
        if args.replay_file is None:
            parser.error("replay requires a SolidCraft .json file")
        if args.out is not None:
            parser.error("replay directly executes existing JSON; --out is not applicable")
        try:
            document = read_command_file(args.replay_file)
        except ValueError as exc:
            parser.error(str(exc))
    else:
        if args.replay_file is not None:
            parser.error("unexpected second file; use 'replay <file.json>'")
        if args.out is None and args.connect is None:
            parser.error("model scripts require --out or --connect")
        try:
            document = run_script(args.script)
        except Exception as exc:
            if args.debug:
                _debug_identity()
                raise
            _exit_model_error(parser, exc, args.script)

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        print(f"{args.out}: {len(document['commands'])} SolidCraft commands")
        return 0

    # Replay defaults to the active GUI. Model runs may explicitly request a
    # clean design with --new; replay never does so implicitly because a replay
    # can intentionally depend on parameters/features already in the document.
    try:
        check_cli_version(require_cli=False)
    except RuntimeError as exc:
        parser.exit(1, f"SCPF native version: {exc}\\n")
    try:
        if args.new:
            fresh = new_design(connect=args.connect or "auto")
            print(f"Live SolidCraft: new empty design {fresh['name']!r}")
        result = send_document(
            document, connect=args.connect or "auto"
        )
    except LiveError as exc:
        parser.exit(1, f"SCPF live: {exc}\n")
    if args.replay_log is not None:
        args.replay_log.parent.mkdir(parents=True, exist_ok=True)
        args.replay_log.write_text(
            json.dumps(result["replay_log"], indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Replay log: {args.replay_log}")
    print(f"Live SolidCraft: {result['completed']} commands applied to the open design")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
