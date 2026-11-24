"""Public error types for CAD verification."""

from __future__ import annotations

from typing import Any


class VerificationError(RuntimeError):
    """Base class for verification-library errors."""


class VerificationConfigError(VerificationError):
    """Raised when a verification request is invalid."""


class VerificationFailure(VerificationError):
    """Expected model verification mismatch.

    This means the verification mechanism ran successfully and proved that an
    expected model condition was not satisfied.
    """

    def __init__(self, message: str, *, evidence: Any = None):
        super().__init__(message)
        self.evidence = evidence


class SolidCraftEvidenceError(VerificationError):
    """Raised when SolidCraft verification evidence is malformed or unreadable."""


class MeshLoadError(VerificationError):
    """Raised when exported mesh data cannot be loaded or measured."""


class SemanticResultError(VerificationFailure):
    """Raised when a composed semantic result is not passing."""


class VisualEvidenceError(VerificationError):
    """Raised when visual evidence cannot be loaded or decoded."""


class ArtifactError(VerificationError):
    """Raised when declared verification output is missing or unsafe."""


class CommandError(VerificationError):
    """Base class for external command execution errors."""


class CommandFailed(CommandError):
    """Raised when an external command exits with a non-zero status."""

    def __init__(
        self,
        command: tuple[str, ...],
        returncode: int,
        stdout: str,
        stderr: str,
    ):
        super().__init__(
            f"command exited with status {returncode}: {' '.join(command)}"
        )
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class CommandTimedOut(CommandError):
    """Raised when an external command exceeds its explicit timeout."""

    def __init__(self, command: tuple[str, ...], timeout_seconds: float):
        super().__init__(
            f"command timed out after {timeout_seconds:g}s: "
            + " ".join(command)
        )
        self.command = command
        self.timeout_seconds = timeout_seconds
