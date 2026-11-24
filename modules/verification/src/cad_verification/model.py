"""Immutable public data objects for CAD verification."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping


@dataclass(frozen=True)
class VerificationContext:
    """Inputs and owned output location for one verification request."""

    verification_id: str
    input_path: Path
    output_dir: Path
    work_dir: Path | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CheckOutcome:
    """Successful or explicitly skipped result returned by a consumer check."""

    status: str = "pass"
    reason: str | None = None
    evidence: Any = field(default_factory=dict)
    artifacts: tuple[Path, ...] = ()

    @classmethod
    def passed(
        cls,
        *,
        evidence: Any = None,
        artifacts: tuple[Path, ...] = (),
    ) -> "CheckOutcome":
        """Return a passing outcome."""

        return cls(
            status="pass",
            evidence={} if evidence is None else evidence,
            artifacts=artifacts,
        )

    @classmethod
    def skipped(
        cls,
        reason: str,
        *,
        evidence: Any = None,
        artifacts: tuple[Path, ...] = (),
    ) -> "CheckOutcome":
        """Return an explicitly skipped outcome with a required reason."""

        return cls(
            status="skipped",
            reason=reason,
            evidence={} if evidence is None else evidence,
            artifacts=artifacts,
        )


CheckCallable = Callable[[VerificationContext], CheckOutcome | None]


@dataclass(frozen=True)
class VerificationCheck:
    """One named consumer-owned verification operation."""

    id: str
    run: CheckCallable


@dataclass(frozen=True)
class CommandResult:
    """Captured result of one successful external command."""

    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
