"""Small external-process helper for CAD-engine commands."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
from typing import Mapping, Sequence

from .errors import CommandFailed, CommandTimedOut, VerificationConfigError
from .model import CommandResult


def run_command(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, object] | None = None,
    timeout_seconds: float | None = None,
) -> CommandResult:
    """Run one explicit argv command and capture its textual output."""

    argv = tuple(str(value) for value in command)
    if not argv:
        raise VerificationConfigError("command must not be empty")
    if timeout_seconds is not None and timeout_seconds <= 0:
        raise VerificationConfigError("timeout_seconds must be positive")

    process_env = dict(os.environ)
    if env:
        process_env.update(
            {str(key): str(value) for key, value in env.items()}
        )

    try:
        completed = subprocess.run(
            argv,
            cwd=None if cwd is None else str(cwd),
            env=process_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout_seconds,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CommandTimedOut(argv, float(timeout_seconds)) from exc

    if completed.returncode != 0:
        raise CommandFailed(
            argv,
            completed.returncode,
            completed.stdout,
            completed.stderr,
        )

    return CommandResult(
        command=argv,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
