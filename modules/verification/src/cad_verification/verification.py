"""Execute one explicit verification request and write structured evidence."""

from __future__ import annotations

import json
import re
from typing import Any, Iterable

from .errors import VerificationConfigError, VerificationFailure
from .evidence import artifact_record
from .model import CheckOutcome, VerificationCheck, VerificationContext


SCHEMA = "cad-verification"
SCHEMA_VERSION = 1
_ID = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _json_value(value: Any, *, label: str) -> Any:
    """Validate that consumer evidence can be serialized to stable JSON."""

    try:
        json.dumps(value, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise VerificationConfigError(
            f"{label} must be JSON-compatible"
        ) from exc
    return value


def _validate(
    context: VerificationContext,
    checks: tuple[VerificationCheck, ...],
) -> None:
    """Validate request identity and check configuration before execution."""

    if not _ID.fullmatch(context.verification_id):
        raise VerificationConfigError(
            f"invalid verification id: {context.verification_id!r}"
        )
    if not checks:
        raise VerificationConfigError(
            "verification requires at least one check"
        )
    _json_value(dict(context.metadata), label="metadata")

    seen: set[str] = set()
    for check in checks:
        if not _ID.fullmatch(check.id):
            raise VerificationConfigError(f"invalid check id: {check.id!r}")
        if check.id in seen:
            raise VerificationConfigError(f"duplicate check id: {check.id}")
        seen.add(check.id)


def _normal_outcome(value: CheckOutcome | None) -> CheckOutcome:
    """Normalize the shorthand None return to a plain passing result."""

    outcome = CheckOutcome.passed() if value is None else value
    if not isinstance(outcome, CheckOutcome):
        raise VerificationConfigError(
            "verification check must return CheckOutcome or None"
        )
    if outcome.status not in {"pass", "skipped"}:
        raise VerificationConfigError(
            f"consumer check returned unsupported status: {outcome.status!r}"
        )
    if outcome.status == "skipped" and not outcome.reason:
        raise VerificationConfigError("skipped check requires a reason")
    _json_value(outcome.evidence, label="check evidence")
    return outcome


def _report_path(context: VerificationContext):
    """Return the library-owned report path."""

    return context.output_dir.resolve() / "verification.json"


def _write_report(context: VerificationContext, report: dict[str, Any]) -> None:
    """Write deterministic JSON evidence for one verification request."""

    path = _report_path(context)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def verify(
    context: VerificationContext,
    checks: Iterable[VerificationCheck],
    *,
    raise_on_error: bool = False,
) -> dict[str, Any]:
    """Execute checks in order and return/write the structured report.

    Expected VerificationFailure exceptions become a model-level failure.
    Other exceptions become an infrastructure-level error.
    """

    configured = tuple(checks)
    _validate(context, configured)

    context.output_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "verification_id": context.verification_id,
        "status": "pass",
        "input": str(context.input_path),
        "metadata": dict(context.metadata),
        "checks": [],
    }

    for check in configured:
        row: dict[str, Any] = {
            "id": check.id,
            "status": "pass",
            "reason": None,
            "error": None,
            "evidence": {},
            "artifacts": [],
        }
        try:
            outcome = _normal_outcome(check.run(context))
            row["status"] = outcome.status
            row["reason"] = outcome.reason
            row["evidence"] = outcome.evidence
            row["artifacts"] = [
                artifact_record(path, context.output_dir)
                for path in outcome.artifacts
            ]
        except VerificationFailure as exc:
            row["status"] = "fail"
            row["error"] = str(exc)
            row["evidence"] = _json_value(
                exc.evidence,
                label="failure evidence",
            )
            report["checks"].append(row)
            report["status"] = "fail"
            _write_report(context, report)
            return report
        except Exception as exc:
            row["status"] = "error"
            row["error"] = f"{type(exc).__name__}: {exc}"
            report["checks"].append(row)
            report["status"] = "error"
            _write_report(context, report)
            if raise_on_error:
                raise
            return report

        report["checks"].append(row)

    _write_report(context, report)
    return report
