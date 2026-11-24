"""Compose already-produced verification evidence without executing work."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Iterable, Mapping, Sequence

from .errors import (
    SemanticResultError,
    VerificationConfigError,
)


_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_CHECK_STATUSES = {
    "pass",
    "fail",
    "error",
    "missing",
    "review",
    "blocked",
    "not-required",
    "skipped",
}
_RESULT_STATUSES = {
    "pass",
    "fail",
    "error",
    "incomplete",
    "review",
    "blocked",
}
_PRECEDENCE = (
    ("error", "error"),
    ("fail", "fail"),
    ("missing", "incomplete"),
    ("review", "review"),
    ("blocked", "blocked"),
)


def _json_value(value: Any, name: str) -> Any:
    """Validate one JSON-compatible value."""

    try:
        json.dumps(value, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise VerificationConfigError(
            f"{name} must be JSON-compatible"
        ) from exc
    return value


def _name(value: Any, name: str) -> str:
    """Validate one stable lowercase engineering identifier."""

    if not isinstance(value, str) or not _NAME.fullmatch(value):
        raise VerificationConfigError(f"invalid {name}: {value!r}")
    return value


@dataclass(frozen=True)
class SemanticCheck:
    """One consumer-supplied semantic result record."""

    name: str
    status: str
    required: bool = True
    reason: str | None = None
    evidence: Any = None

    def __post_init__(self) -> None:
        _name(self.name, "semantic check name")
        if self.status not in _CHECK_STATUSES:
            raise VerificationConfigError(
                f"invalid semantic check status: {self.status!r}"
            )
        if not isinstance(self.required, bool):
            raise VerificationConfigError(
                "semantic check required must be a bool"
            )
        if self.reason is not None and not isinstance(self.reason, str):
            raise VerificationConfigError(
                "semantic check reason must be a string or None"
            )
        _json_value(self.evidence, "semantic check evidence")

    def to_evidence(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible evidence."""

        return {
            "name": self.name,
            "status": self.status,
            "required": self.required,
            "reason": self.reason,
            "evidence": self.evidence,
        }


def _overall(checks: Sequence[SemanticCheck]) -> str:
    """Return the generic overall status for required checks."""

    required = tuple(check for check in checks if check.required)
    for check_status, result_status in _PRECEDENCE:
        if any(check.status == check_status for check in required):
            return result_status
    return "pass"


def compose_semantic_result(
    checks: Iterable[SemanticCheck],
) -> dict[str, Any]:
    """Compose ordered semantic checks into one deterministic result."""

    configured = tuple(checks)
    if not configured:
        raise VerificationConfigError(
            "semantic result requires at least one check"
        )
    for check in configured:
        if not isinstance(check, SemanticCheck):
            raise VerificationConfigError(
                "semantic result must contain SemanticCheck values"
            )
    names = [check.name for check in configured]
    if len(set(names)) != len(names):
        raise VerificationConfigError(
            "semantic check names must be unique"
        )
    return {
        "status": _overall(configured),
        "checks": [check.to_evidence() for check in configured],
    }


def _validate_result(result: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one already-composed semantic result."""

    if not isinstance(result, Mapping):
        raise VerificationConfigError(
            "semantic result must be an object"
        )
    status = result.get("status")
    checks = result.get("checks")
    if status not in _RESULT_STATUSES:
        raise VerificationConfigError(
            f"invalid semantic result status: {status!r}"
        )
    if not isinstance(checks, list):
        raise VerificationConfigError(
            "semantic result checks must be a list"
        )
    _json_value(dict(result), "semantic result")
    return dict(result)


def require_semantic_pass(
    result: Mapping[str, Any],
) -> dict[str, Any]:
    """Require a composed semantic result to be complete and passing."""

    validated = _validate_result(result)
    if validated["status"] != "pass":
        raise SemanticResultError(
            "semantic result is not complete and passing",
            evidence=validated,
        )
    return validated


def compose_item_results(
    items: Iterable[tuple[str, Mapping[str, Any]]],
) -> dict[str, Any]:
    """Compose ordered already-produced item results."""

    rows = []
    statuses = []
    seen = set()
    for item_id, result in tuple(items):
        item_id = _name(item_id, "item id")
        if item_id in seen:
            raise VerificationConfigError(
                f"duplicate item id: {item_id}"
            )
        seen.add(item_id)
        validated = _validate_result(result)
        statuses.append(validated["status"])
        rows.append({
            "item_id": item_id,
            "status": validated["status"],
            "result": validated,
        })

    if not rows:
        raise VerificationConfigError(
            "aggregate result requires at least one item"
        )

    overall = "pass"
    for candidate in (
        "error",
        "fail",
        "incomplete",
        "review",
        "blocked",
    ):
        if candidate in statuses:
            overall = candidate
            break
    return {
        "status": overall,
        "items": rows,
    }


def semantic_checks_from_report(
    report: Mapping[str, Any],
) -> tuple[SemanticCheck, ...]:
    """Adapt ordered checks from an existing verification report."""

    if not isinstance(report, Mapping):
        raise VerificationConfigError(
            "verification report must be an object"
        )
    if report.get("schema") != "cad-verification":
        raise VerificationConfigError(
            "unsupported verification report schema"
        )
    rows = report.get("checks")
    if not isinstance(rows, list):
        raise VerificationConfigError(
            "verification report checks must be a list"
        )

    allowed = {"pass", "fail", "error", "skipped"}
    result = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise VerificationConfigError(
                f"verification report check {index} must be an object"
            )
        check_id = _name(row.get("id"), "report check id")
        status = row.get("status")
        if status not in allowed:
            raise VerificationConfigError(
                f"unsupported report check status: {status!r}"
            )
        evidence = {
            "evidence": row.get("evidence"),
            "artifacts": row.get("artifacts", []),
            "error": row.get("error"),
        }
        _json_value(evidence, "adapted report evidence")
        result.append(
            SemanticCheck(
                name=check_id,
                status=status,
                required=True,
                reason=row.get("reason"),
                evidence=evidence,
            )
        )
    return tuple(result)
