"""Generic exact-value and predicate verification helpers."""

from __future__ import annotations

import json
from typing import Any

from .errors import VerificationConfigError, VerificationFailure


def _json_value(value: Any, name: str) -> Any:
    """Validate one JSON-compatible evidence value."""

    try:
        json.dumps(value, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise VerificationConfigError(
            f"{name} must be JSON-compatible"
        ) from exc
    return value


def _label(value: Any) -> str | None:
    """Validate one optional descriptive label."""

    if value is not None and not isinstance(value, str):
        raise VerificationConfigError(
            "label must be a string or None"
        )
    return value


def _evidence(
    *,
    expected: Any,
    actual: Any,
    label: str | None,
    passed: bool,
) -> dict[str, Any]:
    """Build one deterministic expected/actual evidence object."""

    return {
        "label": _label(label),
        "expected": _json_value(expected, "expected"),
        "actual": _json_value(actual, "actual"),
        "pass": bool(passed),
    }


def require_equal(
    expected: Any,
    actual: Any,
    *,
    label: str | None = None,
) -> dict[str, Any]:
    """Require exact equality without numeric tolerance or coercion."""

    passed = actual == expected
    evidence = _evidence(
        expected=expected,
        actual=actual,
        label=label,
        passed=passed,
    )
    if not passed:
        raise VerificationFailure(
            (
                f"{label}: value does not match expected value"
                if label is not None
                else "value does not match expected value"
            ),
            evidence=evidence,
        )
    return evidence


def require_condition(
    condition: bool,
    *,
    expected: Any,
    actual: Any,
    label: str | None = None,
) -> dict[str, Any]:
    """Require one consumer-defined boolean condition."""

    if type(condition) is not bool:
        raise VerificationConfigError("condition must be a bool")

    evidence = _evidence(
        expected=expected,
        actual=actual,
        label=label,
        passed=condition,
    )
    if not condition:
        raise VerificationFailure(
            (
                f"{label}: required condition is not satisfied"
                if label is not None
                else "required condition is not satisfied"
            ),
            evidence=evidence,
        )
    return evidence
