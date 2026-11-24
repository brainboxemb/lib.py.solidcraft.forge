"""Generic comparison helpers for consumer-supplied measurements."""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
from typing import Any, Iterable

from .errors import VerificationConfigError, VerificationFailure


def _number(value: Any, name: str) -> float:
    """Return one finite real number."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise VerificationConfigError(f"{name} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise VerificationConfigError(f"{name} must be finite")
    return result


def _tolerance(value: Any) -> float:
    """Return one finite non-negative tolerance."""

    result = _number(value, "tolerance")
    if result < 0:
        raise VerificationConfigError("tolerance may not be negative")
    return result


def _vector(value: Iterable[Any], name: str) -> tuple[float, ...]:
    """Normalize one non-empty numeric vector."""

    try:
        values = tuple(value)
    except TypeError as exc:
        raise VerificationConfigError(
            f"{name} must be a non-empty numeric vector"
        ) from exc
    if not values:
        raise VerificationConfigError(
            f"{name} must be a non-empty numeric vector"
        )
    return tuple(
        _number(item, f"{name}[{index}]")
        for index, item in enumerate(values)
    )


def _xyz(value: Iterable[Any], name: str) -> tuple[float, float, float]:
    """Normalize one XYZ vector."""

    values = _vector(value, name)
    if len(values) != 3:
        raise VerificationConfigError(
            f"{name} must contain exactly three numbers"
        )
    return values[0], values[1], values[2]


def _label(value: Any, name: str = "label") -> str | None:
    """Normalize an optional non-empty label."""

    if value is None:
        return None
    if not isinstance(value, str):
        raise VerificationConfigError(f"{name} must be a string or None")
    result = value.strip()
    if not result:
        raise VerificationConfigError(f"{name} may not be empty")
    return result


def _bounds(
    minimum: Iterable[Any],
    maximum: Iterable[Any],
    name: str,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Normalize one non-inverted XYZ envelope."""

    low = _xyz(minimum, f"{name}_min")
    high = _xyz(maximum, f"{name}_max")
    for axis, (lower, upper) in enumerate(zip(low, high)):
        if upper < lower:
            raise VerificationConfigError(
                f"{name}_max[{axis}] may not be below {name}_min[{axis}]"
            )
    return low, high


def _finish(evidence: dict[str, Any]) -> dict[str, Any]:
    """Return passing evidence or raise one expected verification failure."""

    if evidence["pass"]:
        return evidence
    raise VerificationFailure(
        "comparison does not satisfy the expected tolerance",
        evidence=evidence,
    )


def compare_scalar(
    expected: Any,
    actual: Any,
    tolerance: Any,
    *,
    label: str | None = None,
) -> dict[str, Any]:
    """Compare one scalar value and return deterministic evidence."""

    expected_value = _number(expected, "expected")
    actual_value = _number(actual, "actual")
    tolerance_value = _tolerance(tolerance)
    label_value = _label(label)
    delta = abs(actual_value - expected_value)
    evidence = {
        "kind": "scalar",
        "label": label_value,
        "expected": expected_value,
        "actual": actual_value,
        "delta": delta,
        "tolerance": tolerance_value,
        "pass": bool(delta <= tolerance_value),
    }
    return _finish(evidence)


def compare_vector(
    expected: Iterable[Any],
    actual: Iterable[Any],
    tolerance: Any,
    *,
    label: str | None = None,
) -> dict[str, Any]:
    """Compare equally-sized non-empty numeric vectors."""

    expected_values = _vector(expected, "expected")
    actual_values = _vector(actual, "actual")
    if len(expected_values) != len(actual_values):
        raise VerificationConfigError(
            "expected and actual vectors must have equal length"
        )
    tolerance_value = _tolerance(tolerance)
    label_value = _label(label)
    deltas = tuple(
        abs(actual_value - expected_value)
        for expected_value, actual_value in zip(
            expected_values,
            actual_values,
        )
    )
    maximum_delta = max(deltas)
    evidence = {
        "kind": "vector",
        "label": label_value,
        "expected": list(expected_values),
        "actual": list(actual_values),
        "deltas": list(deltas),
        "max_delta": maximum_delta,
        "tolerance": tolerance_value,
        "pass": bool(maximum_delta <= tolerance_value),
    }
    return _finish(evidence)


def compare_bounds(
    expected_min: Iterable[Any],
    expected_max: Iterable[Any],
    actual_min: Iterable[Any],
    actual_max: Iterable[Any],
    tolerance: Any,
    *,
    label: str | None = None,
) -> dict[str, Any]:
    """Compare expected and actual XYZ bounds."""

    expected_low, expected_high = _bounds(
        expected_min,
        expected_max,
        "expected",
    )
    actual_low, actual_high = _bounds(
        actual_min,
        actual_max,
        "actual",
    )
    tolerance_value = _tolerance(tolerance)
    label_value = _label(label)
    deltas = tuple(
        abs(actual_value - expected_value)
        for expected_value, actual_value in zip(
            expected_low + expected_high,
            actual_low + actual_high,
        )
    )
    maximum_delta = max(deltas)
    evidence = {
        "kind": "bounds",
        "label": label_value,
        "expected_min": list(expected_low),
        "expected_max": list(expected_high),
        "actual_min": list(actual_low),
        "actual_max": list(actual_high),
        "deltas": list(deltas),
        "max_delta": maximum_delta,
        "tolerance": tolerance_value,
        "pass": bool(maximum_delta <= tolerance_value),
    }
    return _finish(evidence)


@dataclass(frozen=True)
class BodyEnvelope:
    """One already-measured body envelope."""

    minimum: tuple[float, float, float]
    maximum: tuple[float, float, float]
    label: str | None = None

    def __post_init__(self) -> None:
        minimum, maximum = _bounds(
            self.minimum,
            self.maximum,
            "body",
        )
        object.__setattr__(self, "minimum", minimum)
        object.__setattr__(self, "maximum", maximum)
        object.__setattr__(self, "label", _label(self.label))

    def evidence(self) -> dict[str, Any]:
        """Return deterministic JSON-compatible evidence."""

        return {
            "label": self.label,
            "min": list(self.minimum),
            "max": list(self.maximum),
        }


def _envelope_delta(expected: BodyEnvelope, actual: BodyEnvelope) -> float:
    """Return the maximum absolute bounds delta for two envelopes."""

    return max(
        abs(actual_value - expected_value)
        for expected_value, actual_value in zip(
            expected.minimum + expected.maximum,
            actual.minimum + actual.maximum,
        )
    )


def _canonical_envelope_key(
    envelope: BodyEnvelope,
) -> tuple[str, tuple[float, ...]]:
    """Return a stable order key independent of caller list order."""

    return (
        envelope.label or "",
        envelope.minimum + envelope.maximum,
    )


def _envelopes(
    values: Iterable[BodyEnvelope],
    name: str,
) -> tuple[BodyEnvelope, ...]:
    """Validate one body-envelope collection."""

    try:
        result = tuple(values)
    except TypeError as exc:
        raise VerificationConfigError(
            f"{name} must contain BodyEnvelope values"
        ) from exc
    for item in result:
        if not isinstance(item, BodyEnvelope):
            raise VerificationConfigError(
                f"{name} must contain BodyEnvelope values"
            )
    return result


def match_body_envelopes(
    expected: Iterable[BodyEnvelope],
    actual: Iterable[BodyEnvelope],
    tolerance: Any,
) -> dict[str, Any]:
    """Match body envelopes one-to-one without depending on input order."""

    expected_values = _envelopes(expected, "expected")
    actual_values = _envelopes(actual, "actual")
    tolerance_value = _tolerance(tolerance)

    available = list(sorted(actual_values, key=_canonical_envelope_key))
    matched_pairs: list[dict[str, Any]] = []
    unmatched_expected: list[dict[str, Any]] = []

    for expected_envelope in expected_values:
        candidates = []
        for index, actual_envelope in enumerate(available):
            delta = _envelope_delta(expected_envelope, actual_envelope)
            if delta <= tolerance_value:
                candidates.append(
                    (
                        delta,
                        _canonical_envelope_key(actual_envelope),
                        index,
                        actual_envelope,
                    )
                )

        if not candidates:
            unmatched_expected.append(expected_envelope.evidence())
            continue

        delta, _key, index, actual_envelope = min(candidates)
        available.pop(index)
        matched_pairs.append(
            {
                "expected": expected_envelope.evidence(),
                "actual": actual_envelope.evidence(),
                "max_delta": delta,
            }
        )

    evidence = {
        "kind": "body_envelopes",
        "expected_count": len(expected_values),
        "actual_count": len(actual_values),
        "matched_pairs": matched_pairs,
        "unmatched_expected": unmatched_expected,
        "unmatched_actual": [
            envelope.evidence()
            for envelope in sorted(available, key=_canonical_envelope_key)
        ],
        "tolerance": tolerance_value,
        "pass": bool(not unmatched_expected and not available),
    }
    return _finish(evidence)
