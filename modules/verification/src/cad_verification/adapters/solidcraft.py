"""SolidCraft-specific verification adapter.

The adapter understands SolidCraft result schemas and command-line inspection
operations. Model-specific expected values remain consumer-supplied data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
from numbers import Real
from pathlib import Path
import re
import runpy
from typing import Any, Mapping

from ..assertions import require_condition, require_equal
from ..comparison import (
    BodyEnvelope,
    compare_bounds,
    compare_scalar,
    compare_vector,
    match_body_envelopes,
)
from ..errors import (
    SolidCraftEvidenceError,
    VerificationConfigError,
)
from ..model import CheckOutcome, VerificationCheck, VerificationContext
from ..process import run_command
from ..verification import verify


def _config_number(value: Any, name: str) -> float:
    """Return one finite numeric expectation value."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise VerificationConfigError(f"{name} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise VerificationConfigError(f"{name} must be finite")
    return result


def _config_tolerance(value: Any, name: str) -> float:
    """Return one finite non-negative expectation tolerance."""

    result = _config_number(value, name)
    if result < 0:
        raise VerificationConfigError(f"{name} may not be negative")
    return result


def _config_text(value: Any, name: str) -> str:
    """Return one non-empty string from adapter configuration."""

    if not isinstance(value, str):
        raise VerificationConfigError(f"{name} must be a string")
    result = value.strip()
    if not result:
        raise VerificationConfigError(f"{name} may not be empty")
    return result


def _config_optional_text(value: Any, name: str) -> str | None:
    """Return one optional string from adapter configuration."""

    if value is None:
        return None
    if not isinstance(value, str):
        raise VerificationConfigError(f"{name} must be a string or None")
    return value


def _config_count(value: Any, name: str) -> int:
    """Return one non-negative integer expectation."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise VerificationConfigError(f"{name} must be an integer")
    if value < 0:
        raise VerificationConfigError(f"{name} may not be negative")
    return value


def _config_count_mapping(value: Any, name: str) -> dict[str, int]:
    """Return one non-empty normalized mapping of named counts."""

    if not isinstance(value, Mapping):
        raise VerificationConfigError(f"{name} must be a mapping")
    result: dict[str, int] = {}
    for raw_key, raw_count in value.items():
        key = _config_text(raw_key, f"{name} key")
        if key in result:
            raise VerificationConfigError(f"duplicate {name} key: {key}")
        result[key] = _config_count(raw_count, f"{name} {key}")
    if not result:
        raise VerificationConfigError(f"{name} may not be empty")
    return dict(sorted(result.items()))


def _evidence_mapping(value: Any, path: str) -> Mapping[str, Any]:
    """Return one SolidCraft object or raise a schema error."""

    if not isinstance(value, Mapping):
        raise SolidCraftEvidenceError(f"{path} must be an object")
    return value


def _evidence_list(value: Any, path: str) -> list[Any]:
    """Return one SolidCraft array or raise a schema error."""

    if not isinstance(value, list):
        raise SolidCraftEvidenceError(f"{path} must be an array")
    return value


def _evidence_number(value: Any, path: str) -> float:
    """Return one finite SolidCraft numeric value."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise SolidCraftEvidenceError(f"{path} must be a number")
    result = float(value)
    if not math.isfinite(result):
        raise SolidCraftEvidenceError(f"{path} must be finite")
    return result


def _evidence_bool(value: Any, path: str) -> bool:
    """Return one literal SolidCraft boolean value."""

    if not isinstance(value, bool):
        raise SolidCraftEvidenceError(f"{path} must be a boolean")
    return value


def _evidence_text(value: Any, path: str) -> str:
    """Return one non-empty SolidCraft text value."""

    if not isinstance(value, str):
        raise SolidCraftEvidenceError(f"{path} must be a string")
    result = value.strip()
    if not result:
        raise SolidCraftEvidenceError(f"{path} may not be empty")
    return result


def _evidence_optional_text(value: Any, path: str) -> str | None:
    """Return one optional SolidCraft text value."""

    if value is None:
        return None
    if not isinstance(value, str):
        raise SolidCraftEvidenceError(f"{path} must be a string or null")
    return value


@dataclass(frozen=True)
class SolidCraftBodyExpectation:
    """Model-specific expectations for exactly one selected SolidCraft body."""

    name_prefix: str | None = None
    minimum: tuple[float, float, float] | None = None
    maximum: tuple[float, float, float] | None = None
    bounds_tolerance: float = 0.0
    volume_mm3: float | None = None
    volume_tolerance: float = 0.0
    face_count: int | None = None
    face_type_counts: Mapping[str, int] | None = None
    center_of_mass: tuple[
        float | None,
        float | None,
        float | None,
    ] | None = None
    center_of_mass_tolerance: float = 0.0
    sheet_metal: bool | None = None
    closed: bool | None = None

    def __post_init__(self) -> None:
        if self.name_prefix is not None:
            object.__setattr__(
                self,
                "name_prefix",
                _config_text(self.name_prefix, "name_prefix"),
            )
        if (self.minimum is None) != (self.maximum is None):
            raise VerificationConfigError(
                "minimum and maximum must be supplied together"
            )
        if self.minimum is not None and self.maximum is not None:
            envelope = BodyEnvelope(self.minimum, self.maximum)
            object.__setattr__(self, "minimum", envelope.minimum)
            object.__setattr__(self, "maximum", envelope.maximum)

        object.__setattr__(
            self,
            "bounds_tolerance",
            _config_tolerance(self.bounds_tolerance, "bounds_tolerance"),
        )

        if self.volume_mm3 is not None:
            object.__setattr__(
                self,
                "volume_mm3",
                _config_number(self.volume_mm3, "volume_mm3"),
            )
        object.__setattr__(
            self,
            "volume_tolerance",
            _config_tolerance(self.volume_tolerance, "volume_tolerance"),
        )

        if self.face_count is not None:
            object.__setattr__(
                self,
                "face_count",
                _config_count(self.face_count, "face_count"),
            )

        if self.face_type_counts is not None:
            object.__setattr__(
                self,
                "face_type_counts",
                _config_count_mapping(
                    self.face_type_counts,
                    "face_type_counts",
                ),
            )

        if self.center_of_mass is not None:
            try:
                values = tuple(self.center_of_mass)
            except TypeError as exc:
                raise VerificationConfigError(
                    "center_of_mass must contain exactly three numbers"
                ) from exc
            if len(values) != 3:
                raise VerificationConfigError(
                    "center_of_mass must contain exactly three numbers"
                )
            normalized_center = tuple(
                None
                if value is None
                else _config_number(value, f"center_of_mass[{index}]")
                for index, value in enumerate(values)
            )
            if all(value is None for value in normalized_center):
                raise VerificationConfigError(
                    "center_of_mass must request at least one axis"
                )
            object.__setattr__(
                self,
                "center_of_mass",
                normalized_center,
            )
        object.__setattr__(
            self,
            "center_of_mass_tolerance",
            _config_tolerance(
                self.center_of_mass_tolerance,
                "center_of_mass_tolerance",
            ),
        )

        for name in ("sheet_metal", "closed"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, bool):
                raise VerificationConfigError(
                    f"{name} must be a boolean or None"
                )


@dataclass(frozen=True)
class SolidCraftBodyGroupExpectation:
    """Expect several SolidCraft bodies selected by one name prefix."""

    name_prefix: str
    count: int
    body_envelopes: tuple[BodyEnvelope, ...] | None = None
    bounds_tolerance: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "name_prefix",
            _config_text(self.name_prefix, "name_prefix"),
        )
        object.__setattr__(
            self,
            "count",
            _config_count(self.count, "count"),
        )
        object.__setattr__(
            self,
            "bounds_tolerance",
            _config_tolerance(self.bounds_tolerance, "bounds_tolerance"),
        )

        if self.body_envelopes is not None:
            envelopes = tuple(self.body_envelopes)
            if not all(isinstance(item, BodyEnvelope) for item in envelopes):
                raise VerificationConfigError(
                    "body_envelopes must contain BodyEnvelope values"
                )
            if len(envelopes) != self.count:
                raise VerificationConfigError(
                    "body_envelopes length must equal count"
                )
            object.__setattr__(self, "body_envelopes", envelopes)


@dataclass(frozen=True)
class SolidCraftTimelineExpectation:
    """One expected SolidCraft timeline row with explicit checked fields."""

    feature_type: str
    name: str | None = None
    check_name: bool = False
    error: str | None = None
    check_error: bool = True
    warning: str | None = None
    check_warning: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "feature_type",
            _config_text(self.feature_type, "feature_type"),
        )

        for flag_name in ("check_name", "check_error", "check_warning"):
            if not isinstance(getattr(self, flag_name), bool):
                raise VerificationConfigError(
                    f"{flag_name} must be a boolean"
                )

        for field_name, flag_name in (
            ("name", "check_name"),
            ("error", "check_error"),
            ("warning", "check_warning"),
        ):
            value = _config_optional_text(
                getattr(self, field_name),
                field_name,
            )
            if not getattr(self, flag_name) and value is not None:
                raise VerificationConfigError(
                    f"{field_name} may not be supplied when "
                    f"{flag_name}=False"
                )
            object.__setattr__(self, field_name, value)

    def evidence(self) -> dict[str, Any]:
        """Return only timeline fields that belong to the model contract."""

        result: dict[str, Any] = {"type": self.feature_type}
        if self.check_name:
            result["name"] = self.name
        if self.check_error:
            result["error"] = self.error
        if self.check_warning:
            result["warning"] = self.warning
        return result


@dataclass(frozen=True)
class SolidCraftSketchExpectation:
    """One expected SolidCraft sketch summary."""

    name: str
    profiles: int | None = None
    curves: int | None = None
    dof: int | None = None
    status: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _config_text(self.name, "name"))

        for field_name in ("profiles", "curves", "dof"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _config_count(value, field_name),
                )

        if self.status is not None:
            object.__setattr__(
                self,
                "status",
                _config_text(self.status, "status"),
            )

        if (
            self.profiles is None
            and self.curves is None
            and self.dof is None
            and self.status is None
        ):
            raise VerificationConfigError(
                "SolidCraftSketchExpectation requires at least one "
                "property check"
            )

    def evidence(self) -> dict[str, Any]:
        """Return deterministic expected sketch evidence."""

        result: dict[str, Any] = {"name": self.name}
        if self.profiles is not None:
            result["profiles"] = self.profiles
        if self.curves is not None:
            result["curves"] = self.curves
        if self.dof is not None:
            result["dof"] = self.dof
        if self.status is not None:
            result["status"] = self.status
        return result


@dataclass(frozen=True)
class SolidCraftModelExpectation:
    """Model-specific data consumed by the SolidCraft verification adapter."""

    body_count: int | None = None
    body_envelopes: tuple[BodyEnvelope, ...] | None = None
    bounds_tolerance: float = 0.0
    parameters: Mapping[str, float] | None = None
    parameter_match: str = "exact"
    named_bodies: tuple[SolidCraftBodyExpectation, ...] = ()
    body_groups: tuple[SolidCraftBodyGroupExpectation, ...] = ()
    timeline_type_counts: Mapping[str, int] | None = None
    timeline: tuple[SolidCraftTimelineExpectation, ...] | None = None
    sketch_count: int | None = None
    sketches: tuple[SolidCraftSketchExpectation, ...] = ()

    def __post_init__(self) -> None:
        if self.body_count is not None:
            object.__setattr__(
                self,
                "body_count",
                _config_count(self.body_count, "body_count"),
            )

        if self.body_envelopes is not None:
            envelopes = tuple(self.body_envelopes)
            if not all(isinstance(item, BodyEnvelope) for item in envelopes):
                raise VerificationConfigError(
                    "body_envelopes must contain BodyEnvelope values"
                )
            object.__setattr__(self, "body_envelopes", envelopes)

        object.__setattr__(
            self,
            "bounds_tolerance",
            _config_tolerance(self.bounds_tolerance, "bounds_tolerance"),
        )

        parameter_match = _config_text(
            self.parameter_match,
            "parameter_match",
        )
        if parameter_match not in {"exact", "subset"}:
            raise VerificationConfigError(
                "parameter_match must be 'exact' or 'subset'"
            )
        object.__setattr__(self, "parameter_match", parameter_match)

        if self.parameters is not None:
            if not isinstance(self.parameters, Mapping):
                raise VerificationConfigError("parameters must be a mapping")
            normalized_parameters: dict[str, float] = {}
            for key, value in self.parameters.items():
                name = _config_text(key, "parameter name")
                if name in normalized_parameters:
                    raise VerificationConfigError(
                        f"duplicate parameter expectation: {name}"
                    )
                normalized_parameters[name] = _config_number(
                    value,
                    f"parameter {name}",
                )
            object.__setattr__(
                self,
                "parameters",
                dict(sorted(normalized_parameters.items())),
            )

        if self.timeline_type_counts is not None:
            object.__setattr__(
                self,
                "timeline_type_counts",
                _config_count_mapping(
                    self.timeline_type_counts,
                    "timeline_type_counts",
                ),
            )

        if self.sketch_count is not None:
            object.__setattr__(
                self,
                "sketch_count",
                _config_count(self.sketch_count, "sketch_count"),
            )

        named_bodies = tuple(self.named_bodies)
        if not all(
            isinstance(item, SolidCraftBodyExpectation)
            for item in named_bodies
        ):
            raise VerificationConfigError(
                "named_bodies must contain SolidCraftBodyExpectation values"
            )
        object.__setattr__(self, "named_bodies", named_bodies)

        body_groups = tuple(self.body_groups)
        if not all(
            isinstance(item, SolidCraftBodyGroupExpectation)
            for item in body_groups
        ):
            raise VerificationConfigError(
                "body_groups must contain SolidCraftBodyGroupExpectation values"
            )
        object.__setattr__(self, "body_groups", body_groups)

        if self.timeline is not None:
            timeline = tuple(self.timeline)
            if not all(
                isinstance(item, SolidCraftTimelineExpectation)
                for item in timeline
            ):
                raise VerificationConfigError(
                    "timeline must contain SolidCraftTimelineExpectation values"
                )
            object.__setattr__(self, "timeline", timeline)

        sketches = tuple(self.sketches)
        if not all(
            isinstance(item, SolidCraftSketchExpectation)
            for item in sketches
        ):
            raise VerificationConfigError(
                "sketches must contain SolidCraftSketchExpectation values"
            )
        object.__setattr__(self, "sketches", sketches)

        if (
            self.body_count is None
            and self.body_envelopes is None
            and self.parameters is None
            and not self.named_bodies
            and not self.body_groups
            and self.timeline_type_counts is None
            and self.timeline is None
            and self.sketch_count is None
            and not self.sketches
        ):
            raise VerificationConfigError(
                "SolidCraftModelExpectation must request at least one check"
            )


def _load_json(path: Path, *, object_required: bool) -> Any:
    """Load one SolidCraft JSON evidence file."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SolidCraftEvidenceError(
            f"could not read SolidCraft JSON evidence: {path}"
        ) from exc

    if object_required and not isinstance(value, Mapping):
        raise SolidCraftEvidenceError(
            f"SolidCraft evidence must contain one object: {path}"
        )
    if not object_required and not isinstance(value, (Mapping, list)):
        raise SolidCraftEvidenceError(
            f"SolidCraft inspection evidence must be an object or array: {path}"
        )
    return value


def evaluate_solidcraft_model(
    model_path: Path,
    destination: Path,
) -> dict[str, Any]:
    """Evaluate one saved SolidCraft model and load its measurement object."""

    model = Path(model_path)
    output = Path(destination)
    run_command(
        [
            "solidcraft-cli",
            "eval",
            str(model),
            "--json-out",
            str(output),
        ]
    )
    value = _load_json(output, object_required=True)
    return dict(value)


def mutate_solidcraft_model(
    model_path: Path,
    command_path: Path,
    destination: Path,
) -> Path:
    """Apply one SolidCraft command document to an existing saved model."""

    model = Path(model_path)
    command = Path(command_path)
    output = Path(destination)
    run_command(
        [
            "solidcraft-cli",
            "run",
            str(command),
            "--in",
            str(model),
            "--param-check",
            "strict",
            "--save",
            str(output),
        ]
    )
    return output


def inspect_solidcraft_model(
    model_path: Path,
    command_path: Path,
    destination: Path,
) -> Any:
    """Execute one read-only SolidCraft inspection and load its JSON result."""

    model = Path(model_path)
    command = Path(command_path)
    output = Path(destination)
    run_command(
        [
            "solidcraft-cli",
            "run",
            str(command),
            "--in",
            str(model),
            "--param-check",
            "strict",
            "--results",
            "--json-out",
            str(output),
        ]
    )
    return _load_json(output, object_required=False)


def _body_rows(measurements: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Return validated SolidCraft body rows without skipping malformed rows."""

    if "bodies" not in measurements:
        raise SolidCraftEvidenceError("bodies is required")
    values = _evidence_list(measurements["bodies"], "bodies")
    result = []
    for index, value in enumerate(values):
        result.append(_evidence_mapping(value, f"bodies[{index}]"))
    return result


def _body_name(body: Mapping[str, Any], path: str) -> str:
    """Return one validated SolidCraft body name."""

    if "name" not in body:
        raise SolidCraftEvidenceError(f"{path}.name is required")
    return _evidence_text(body["name"], f"{path}.name")


def _body_envelope(
    body: Mapping[str, Any],
    path: str,
) -> BodyEnvelope:
    """Convert one SolidCraft body row to a generic body envelope."""

    if "bbox" not in body:
        raise SolidCraftEvidenceError(f"{path}.bbox is required")
    bbox = _evidence_mapping(body["bbox"], f"{path}.bbox")
    if "min" not in bbox or "max" not in bbox:
        raise SolidCraftEvidenceError(
            f"{path}.bbox must contain min and max"
        )

    label = None
    if "name" in body:
        raw_name = body["name"]
        if raw_name is not None:
            label = _evidence_text(raw_name, f"{path}.name")

    try:
        return BodyEnvelope(
            tuple(bbox["min"]),
            tuple(bbox["max"]),
            label=label,
        )
    except (TypeError, VerificationConfigError) as exc:
        raise SolidCraftEvidenceError(
            f"{path}.bbox is not a valid XYZ envelope"
        ) from exc


def _parameters(measurements: Mapping[str, Any]) -> dict[str, float]:
    """Normalize SolidCraft parameter rows to a stable name/value mapping."""

    if "params" not in measurements:
        raise SolidCraftEvidenceError("params is required")
    rows = _evidence_list(measurements["params"], "params")
    result: dict[str, float] = {}
    for index, value in enumerate(rows):
        path = f"params[{index}]"
        row = _evidence_mapping(value, path)
        if "name" not in row or "value" not in row:
            raise SolidCraftEvidenceError(
                f"{path} must contain name and value"
            )
        name = _evidence_text(row["name"], f"{path}.name")
        if name in result:
            raise SolidCraftEvidenceError(
                f"duplicate SolidCraft parameter: {name}"
            )
        result[name] = _evidence_number(row["value"], f"{path}.value")
    return dict(sorted(result.items()))


def _timeline_types(measurements: Mapping[str, Any]) -> list[str]:
    """Return only validated SolidCraft timeline type values."""

    if "timeline" not in measurements:
        raise SolidCraftEvidenceError("timeline is required")
    rows = _evidence_list(measurements["timeline"], "timeline")
    result = []
    for index, value in enumerate(rows):
        path = f"timeline[{index}]"
        row = _evidence_mapping(value, path)
        if "type" not in row:
            raise SolidCraftEvidenceError(f"{path}.type is required")
        result.append(_evidence_text(row["type"], f"{path}.type"))
    return result


def _timeline_rows(
    measurements: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Normalize the SolidCraft timeline schema used by expectations."""

    if "timeline" not in measurements:
        raise SolidCraftEvidenceError("timeline is required")
    rows = _evidence_list(measurements["timeline"], "timeline")
    result = []
    for index, value in enumerate(rows):
        path = f"timeline[{index}]"
        row = _evidence_mapping(value, path)
        if "type" not in row:
            raise SolidCraftEvidenceError(f"{path}.type is required")
        result.append(
            {
                "type": _evidence_text(row["type"], f"{path}.type"),
                "name": _evidence_optional_text(
                    row.get("name"),
                    f"{path}.name",
                ),
                "error": _evidence_optional_text(
                    row.get("error"),
                    f"{path}.error",
                ),
                "warning": _evidence_optional_text(
                    row.get("warning"),
                    f"{path}.warning",
                ),
            }
        )
    return result


def _sketch_rows(
    measurements: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    """Return validated SolidCraft sketch rows."""

    if "sketches" not in measurements:
        raise SolidCraftEvidenceError("sketches is required")
    rows = _evidence_list(measurements["sketches"], "sketches")
    return [
        _evidence_mapping(value, f"sketches[{index}]")
        for index, value in enumerate(rows)
    ]


def _actual_count(value: Any, path: str) -> int:
    """Return one non-negative integer from SolidCraft evidence."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise SolidCraftEvidenceError(f"{path} must be an integer")
    if value < 0:
        raise SolidCraftEvidenceError(f"{path} may not be negative")
    return value


def verify_solidcraft_measurements(
    measurements: Mapping[str, Any],
    expectation: SolidCraftModelExpectation,
) -> dict[str, Any]:
    """Apply model-specific expectation data to SolidCraft measurements."""

    if not isinstance(measurements, Mapping):
        raise SolidCraftEvidenceError(
            "SolidCraft measurements must be an object"
        )
    if not isinstance(expectation, SolidCraftModelExpectation):
        raise VerificationConfigError(
            "expectation must be a SolidCraftModelExpectation"
        )

    evidence: dict[str, Any] = {}
    bodies: list[Mapping[str, Any]] | None = None

    def body_rows() -> list[Mapping[str, Any]]:
        nonlocal bodies
        if bodies is None:
            bodies = _body_rows(measurements)
        return bodies

    if expectation.body_count is not None:
        if "body_count" not in measurements:
            raise SolidCraftEvidenceError("body_count is required")
        actual_count = _actual_count(
            measurements["body_count"],
            "body_count",
        )
        evidence["body_count"] = require_equal(
            expectation.body_count,
            actual_count,
            label="SolidCraft body count",
        )

    if expectation.body_envelopes is not None:
        actual_envelopes = tuple(
            _body_envelope(row, f"bodies[{index}]")
            for index, row in enumerate(body_rows())
        )
        evidence["body_envelopes"] = match_body_envelopes(
            expectation.body_envelopes,
            actual_envelopes,
            expectation.bounds_tolerance,
        )

    if expectation.parameters is not None:
        actual_parameters = _parameters(measurements)
        if expectation.parameter_match == "subset":
            actual_parameters = {
                name: actual_parameters[name]
                for name in expectation.parameters
                if name in actual_parameters
            }
        evidence["parameters"] = require_equal(
            dict(expectation.parameters),
            actual_parameters,
            label="SolidCraft parameters",
        )

    if expectation.named_bodies:
        named_evidence = []
        rows = body_rows()
        names: list[str] | None = None
        for expected in expectation.named_bodies:
            if expected.name_prefix is None:
                require_equal(
                    1,
                    len(rows),
                    label="sole body count",
                )
                index, body = 0, rows[0]
                selector_label = "sole body"
                item_evidence: dict[str, Any] = {
                    "selector": "sole",
                }
            else:
                if names is None:
                    names = [
                        _body_name(row, f"bodies[{index}]")
                        for index, row in enumerate(rows)
                    ]
                matches = [
                    (index, row, names[index])
                    for index, row in enumerate(rows)
                    if names[index].startswith(expected.name_prefix)
                ]
                require_equal(
                    1,
                    len(matches),
                    label=f"{expected.name_prefix} body count",
                )
                index, body, body_name = matches[0]
                selector_label = expected.name_prefix
                item_evidence = {
                    "name_prefix": expected.name_prefix,
                    "body_name": body_name,
                }
            path = f"bodies[{index}]"

            if expected.minimum is not None and expected.maximum is not None:
                actual = _body_envelope(body, path)
                item_evidence["bounds"] = compare_bounds(
                    expected.minimum,
                    expected.maximum,
                    actual.minimum,
                    actual.maximum,
                    expected.bounds_tolerance,
                    label=f"{selector_label} bounds",
                )

            if expected.volume_mm3 is not None:
                if "volume_mm3" not in body:
                    raise SolidCraftEvidenceError(
                        f"{path}.volume_mm3 is required"
                    )
                item_evidence["volume"] = compare_scalar(
                    expected.volume_mm3,
                    _evidence_number(
                        body["volume_mm3"],
                        f"{path}.volume_mm3",
                    ),
                    expected.volume_tolerance,
                    label=f"{selector_label} volume",
                )

            if expected.face_count is not None:
                if "faces" not in body:
                    raise SolidCraftEvidenceError(
                        f"{path}.faces is required"
                    )
                item_evidence["face_count"] = require_equal(
                    expected.face_count,
                    _actual_count(body["faces"], f"{path}.faces"),
                    label=f"{selector_label} face count",
                )

            if expected.face_type_counts is not None:
                if "face_types" not in body:
                    raise SolidCraftEvidenceError(
                        f"{path}.face_types is required"
                    )
                raw_face_types = _evidence_mapping(
                    body["face_types"],
                    f"{path}.face_types",
                )
                actual_face_types = {}
                for face_type in expected.face_type_counts:
                    if face_type in raw_face_types:
                        actual_face_types[face_type] = _actual_count(
                            raw_face_types[face_type],
                            f"{path}.face_types.{face_type}",
                        )
                    else:
                        actual_face_types[face_type] = 0
                item_evidence["face_type_counts"] = require_equal(
                    dict(expected.face_type_counts),
                    actual_face_types,
                    label=f"{selector_label} face type counts",
                )

            if expected.center_of_mass is not None:
                if "center_of_mass" not in body:
                    raise SolidCraftEvidenceError(
                        f"{path}.center_of_mass is required"
                    )
                raw_center = _evidence_list(
                    body["center_of_mass"],
                    f"{path}.center_of_mass",
                )
                if len(raw_center) != 3:
                    raise SolidCraftEvidenceError(
                        f"{path}.center_of_mass must contain exactly "
                        "three values"
                    )

                if all(
                    value is not None
                    for value in expected.center_of_mass
                ):
                    actual_center = [
                        _evidence_number(
                            value,
                            f"{path}.center_of_mass[{index}]",
                        )
                        for index, value in enumerate(raw_center)
                    ]
                    item_evidence["center_of_mass"] = compare_vector(
                        expected.center_of_mass,
                        actual_center,
                        expected.center_of_mass_tolerance,
                        label=f"{selector_label} center of mass",
                    )
                else:
                    components = {}
                    for index, axis in enumerate(("x", "y", "z")):
                        expected_value = expected.center_of_mass[index]
                        if expected_value is None:
                            continue
                        components[axis] = compare_scalar(
                            expected_value,
                            _evidence_number(
                                raw_center[index],
                                f"{path}.center_of_mass[{index}]",
                            ),
                            expected.center_of_mass_tolerance,
                            label=(
                                f"{selector_label} center of mass {axis}"
                            ),
                        )
                    item_evidence["center_of_mass"] = {
                        "components": components,
                    }

            if expected.sheet_metal is not None:
                if "sheet_metal" not in body:
                    raise SolidCraftEvidenceError(
                        f"{path}.sheet_metal is required"
                    )
                item_evidence["sheet_metal"] = require_equal(
                    expected.sheet_metal,
                    _evidence_bool(
                        body["sheet_metal"],
                        f"{path}.sheet_metal",
                    ),
                    label=f"{selector_label} sheet_metal",
                )

            if expected.closed is not None:
                if "closed" not in body:
                    raise SolidCraftEvidenceError(
                        f"{path}.closed is required"
                    )
                item_evidence["closed"] = require_equal(
                    expected.closed,
                    _evidence_bool(body["closed"], f"{path}.closed"),
                    label=f"{selector_label} closed",
                )

            named_evidence.append(item_evidence)
        evidence["named_bodies"] = named_evidence

    if expectation.body_groups:
        group_evidence = []
        rows = body_rows()
        names = [
            _body_name(row, f"bodies[{index}]")
            for index, row in enumerate(rows)
        ]
        for expected in expectation.body_groups:
            matches = [
                (index, row, names[index])
                for index, row in enumerate(rows)
                if names[index].startswith(expected.name_prefix)
            ]
            item_evidence: dict[str, Any] = {
                "name_prefix": expected.name_prefix,
                "matched_names": [name for _, _, name in matches],
                "count": require_equal(
                    expected.count,
                    len(matches),
                    label=f"{expected.name_prefix} body group count",
                ),
            }
            if expected.body_envelopes is not None:
                actual_envelopes = tuple(
                    _body_envelope(row, f"bodies[{index}]")
                    for index, row, _ in matches
                )
                item_evidence["body_envelopes"] = match_body_envelopes(
                    expected.body_envelopes,
                    actual_envelopes,
                    expected.bounds_tolerance,
                )
            group_evidence.append(item_evidence)
        evidence["body_groups"] = group_evidence

    if expectation.timeline_type_counts is not None:
        actual_counts = {
            feature_type: 0
            for feature_type in expectation.timeline_type_counts
        }
        for feature_type in _timeline_types(measurements):
            if feature_type in actual_counts:
                actual_counts[feature_type] += 1
        evidence["timeline_type_counts"] = require_equal(
            dict(expectation.timeline_type_counts),
            actual_counts,
            label="SolidCraft timeline type counts",
        )

    if expectation.timeline is not None:
        expected_timeline = [
            item.evidence()
            for item in expectation.timeline
        ]
        actual_rows = _timeline_rows(measurements)
        require_equal(
            len(expected_timeline),
            len(actual_rows),
            label="SolidCraft timeline row count",
        )
        projected_actual = [
            {
                key: actual[key]
                for key in expected
            }
            for expected, actual in zip(
                expected_timeline,
                actual_rows,
            )
        ]
        evidence["timeline"] = require_equal(
            expected_timeline,
            projected_actual,
            label="SolidCraft timeline",
        )

    if expectation.sketch_count is not None:
        if "sketches" not in measurements:
            raise SolidCraftEvidenceError("sketches is required")
        evidence["sketch_count"] = require_equal(
            expectation.sketch_count,
            len(_evidence_list(measurements["sketches"], "sketches")),
            label="SolidCraft sketch count",
        )

    if expectation.sketches:
        rows = _sketch_rows(measurements)
        normalized_names = []
        for index, row in enumerate(rows):
            if "name" not in row:
                raise SolidCraftEvidenceError(
                    f"sketches[{index}].name is required"
                )
            normalized_names.append(
                _evidence_text(row["name"], f"sketches[{index}].name")
            )

        sketch_evidence = []
        for expected in expectation.sketches:
            matches = [
                (index, row)
                for index, row in enumerate(rows)
                if normalized_names[index] == expected.name
            ]
            require_equal(
                1,
                len(matches),
                label=f"{expected.name} sketch count",
            )
            index, row = matches[0]
            path = f"sketches[{index}]"

            expected_evidence = expected.evidence()
            actual: dict[str, Any] = {"name": expected.name}
            for field_name in expected_evidence:
                if field_name == "name":
                    continue
                if field_name not in row:
                    raise SolidCraftEvidenceError(
                        f"{path}.{field_name} is required"
                    )
                if field_name in {"profiles", "curves", "dof"}:
                    actual[field_name] = _actual_count(
                        row[field_name],
                        f"{path}.{field_name}",
                    )
                else:
                    actual[field_name] = _evidence_text(
                        row[field_name],
                        f"{path}.{field_name}",
                    )

            sketch_evidence.append(
                require_equal(
                    expected_evidence,
                    actual,
                    label=f"{expected.name} sketch",
                )
            )
        evidence["sketches"] = sketch_evidence

    return evidence


_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
_NO_INSPECTION_EXPECTATION = object()


def _identifier(value: Any, name: str) -> str:
    """Return one stable lowercase engineering identifier."""

    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise VerificationConfigError(
            f"{name} must match {_IDENTIFIER.pattern}"
        )
    return value


def _config_json_key(value: Any, name: str) -> str:
    """Return one non-empty JSON object key without rewriting it."""

    if not isinstance(value, str) or not value:
        raise VerificationConfigError(f"{name} must be a non-empty string")
    return value


def _config_json_scalar(value: Any, name: str) -> Any:
    """Return one finite JSON scalar used by an inspection selector."""

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise VerificationConfigError(f"{name} must be finite")
        return value
    raise VerificationConfigError(f"{name} must be a JSON scalar")


def _config_json_value(value: Any, name: str) -> Any:
    """Normalize one JSON-compatible configuration value."""

    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise VerificationConfigError(
            f"{name} must be JSON-compatible"
        ) from exc
    return json.loads(encoded)


def _config_tolerant_inspection_value(value: Any, name: str) -> Any:
    """Normalize one numeric scalar or flat numeric vector expectation."""

    if isinstance(value, Real) and not isinstance(value, bool):
        return _config_number(value, name)

    if isinstance(value, list) and value:
        return [
            _config_number(item, f"{name}[{index}]")
            for index, item in enumerate(value)
        ]

    raise VerificationConfigError(
        f"{name} with tolerance must be a numeric scalar "
        "or non-empty numeric array"
    )


@dataclass(frozen=True)
class SolidCraftInspectionSelect:
    """Select exactly one object from a JSON list by field/value."""

    field: str
    value: Any

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "field",
            _config_json_key(self.field, "inspection selector field"),
        )
        object.__setattr__(
            self,
            "value",
            _config_json_scalar(self.value, "inspection selector value"),
        )


@dataclass(frozen=True)
class SolidCraftInspectionCheck:
    """One data-only projected inspection comparison."""

    id: str
    path: tuple[Any, ...] = ()
    expected: Any = field(
        default=_NO_INSPECTION_EXPECTATION,
        repr=False,
    )
    tolerance: float | None = None
    count: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _identifier(self.id, "inspection check id"))

        if isinstance(self.path, (str, bytes)):
            raise VerificationConfigError(
                "inspection check path must be a sequence of path segments"
            )
        try:
            raw_path = tuple(self.path)
        except TypeError as exc:
            raise VerificationConfigError(
                "inspection check path must be a sequence of path segments"
            ) from exc

        normalized_path = []
        for index, segment in enumerate(raw_path):
            if isinstance(segment, str):
                normalized_path.append(
                    _config_json_key(
                        segment,
                        f"inspection path[{index}]",
                    )
                )
            elif isinstance(segment, int) and not isinstance(segment, bool):
                if segment < 0:
                    raise VerificationConfigError(
                        "inspection list indexes may not be negative"
                    )
                normalized_path.append(segment)
            elif isinstance(segment, SolidCraftInspectionSelect):
                normalized_path.append(segment)
            else:
                raise VerificationConfigError(
                    "inspection path segments must be object keys, "
                    "non-negative indexes or SolidCraftInspectionSelect values"
                )
        object.__setattr__(self, "path", tuple(normalized_path))

        has_expected = self.expected is not _NO_INSPECTION_EXPECTATION
        has_count = self.count is not None
        if has_expected == has_count:
            raise VerificationConfigError(
                "inspection check requires exactly one of expected or count"
            )

        if has_count:
            object.__setattr__(
                self,
                "count",
                _config_count(self.count, "inspection count"),
            )
            if self.tolerance is not None:
                raise VerificationConfigError(
                    "inspection count may not define tolerance"
                )
            return

        expected = _config_json_value(
            self.expected,
            "inspection check expected",
        )
        if self.tolerance is not None:
            tolerance = _config_tolerance(
                self.tolerance,
                "inspection tolerance",
            )
            expected = _config_tolerant_inspection_value(
                expected,
                "inspection check expected",
            )
            object.__setattr__(self, "tolerance", tolerance)
        object.__setattr__(self, "expected", expected)


@dataclass(frozen=True)
class SolidCraftMeasurementChangeExpectation:
    """One numeric baseline-to-mutated SolidCraft measurement relation."""

    id: str
    path: tuple[str | int, ...]
    minimum_absolute_delta: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _identifier(self.id, "change id"))
        try:
            raw_path = tuple(self.path)
        except TypeError as exc:
            raise VerificationConfigError(
                "change path must be a sequence of path segments"
            ) from exc
        if not raw_path:
            raise VerificationConfigError("change path may not be empty")

        normalized = []
        for index, segment in enumerate(raw_path):
            if isinstance(segment, str):
                normalized.append(
                    _config_json_key(segment, f"change path[{index}]")
                )
            elif isinstance(segment, int) and not isinstance(segment, bool):
                if segment < 0:
                    raise VerificationConfigError(
                        "change path indexes may not be negative"
                    )
                normalized.append(segment)
            else:
                raise VerificationConfigError(
                    "change path segments must be object keys or "
                    "non-negative indexes"
                )
        object.__setattr__(self, "path", tuple(normalized))
        object.__setattr__(
            self,
            "minimum_absolute_delta",
            _config_tolerance(
                self.minimum_absolute_delta,
                "minimum_absolute_delta",
            ),
        )


@dataclass(frozen=True)
class SolidCraftSavedDesign:
    """One saved-design mutation and its expected SolidCraft result."""

    id: str
    command_path: Path
    expectation: SolidCraftModelExpectation
    changes: tuple[SolidCraftMeasurementChangeExpectation, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _identifier(self.id, "saved design id"))
        object.__setattr__(self, "command_path", Path(self.command_path))
        if not isinstance(self.expectation, SolidCraftModelExpectation):
            raise VerificationConfigError(
                "saved design expectation must be a "
                "SolidCraftModelExpectation"
            )

        changes = tuple(self.changes)
        if not all(
            isinstance(item, SolidCraftMeasurementChangeExpectation)
            for item in changes
        ):
            raise VerificationConfigError(
                "saved design changes must contain "
                "SolidCraftMeasurementChangeExpectation values"
            )
        _require_unique_definition_ids(
            (item.id for item in changes),
            "saved design change",
        )
        object.__setattr__(self, "changes", changes)


@dataclass(frozen=True)
class SolidCraftInspection:
    """One read-only SolidCraft inspection owned by a model definition."""

    id: str
    command_path: Path
    expected: Any = field(
        default=_NO_INSPECTION_EXPECTATION,
        repr=False,
    )
    checks: tuple[SolidCraftInspectionCheck, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _identifier(self.id, "inspection id"))
        object.__setattr__(self, "command_path", Path(self.command_path))

        has_expected = self.expected is not _NO_INSPECTION_EXPECTATION
        if has_expected:
            try:
                json.dumps(self.expected, sort_keys=True)
            except (TypeError, ValueError) as exc:
                raise VerificationConfigError(
                    "inspection expected result must be JSON-compatible"
                ) from exc

        checks = tuple(self.checks)
        if not all(isinstance(item, SolidCraftInspectionCheck) for item in checks):
            raise VerificationConfigError(
                "inspection checks must contain SolidCraftInspectionCheck values"
            )
        if has_expected and checks:
            raise VerificationConfigError(
                "inspection expected and checks are mutually exclusive"
            )
        _require_unique_definition_ids(
            (item.id for item in checks),
            "inspection check",
        )
        object.__setattr__(self, "checks", checks)


@dataclass(frozen=True)
class SolidCraftVerification:
    """Declarative verification definition for one native SolidCraft model."""

    verification_id: str
    baseline: SolidCraftModelExpectation
    saved_designs: tuple[SolidCraftSavedDesign, ...] = ()
    inspections: tuple[SolidCraftInspection, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "verification_id",
            _identifier(self.verification_id, "verification id"),
        )
        if not isinstance(self.baseline, SolidCraftModelExpectation):
            raise VerificationConfigError(
                "baseline must be a SolidCraftModelExpectation"
            )

        saved_designs = tuple(self.saved_designs)
        if not all(
            isinstance(item, SolidCraftSavedDesign)
            for item in saved_designs
        ):
            raise VerificationConfigError(
                "saved_designs must contain SolidCraftSavedDesign values"
            )
        _require_unique_definition_ids(
            (item.id for item in saved_designs),
            "saved design",
        )
        object.__setattr__(self, "saved_designs", saved_designs)

        inspections = tuple(self.inspections)
        if not all(
            isinstance(item, SolidCraftInspection)
            for item in inspections
        ):
            raise VerificationConfigError(
                "inspections must contain SolidCraftInspection values"
            )
        _require_unique_definition_ids(
            (item.id for item in inspections),
            "inspection",
        )
        object.__setattr__(self, "inspections", inspections)

        if not isinstance(self.metadata, Mapping):
            raise VerificationConfigError("metadata must be a mapping")
        metadata = dict(self.metadata)
        try:
            json.dumps(metadata, sort_keys=True)
        except (TypeError, ValueError) as exc:
            raise VerificationConfigError(
                "metadata must be JSON-compatible"
            ) from exc
        object.__setattr__(self, "metadata", metadata)


def _require_unique_definition_ids(
    values,
    kind: str,
) -> None:
    """Reject duplicate IDs inside one declarative definition namespace."""

    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise VerificationConfigError(
                f"duplicate {kind} id: {value}"
            )
        seen.add(value)


def _baseline_check(
    model_path: Path,
    expectation: SolidCraftModelExpectation,
):
    """Build the baseline check without exposing procedural work to consumers."""

    def run(ctx: VerificationContext) -> CheckOutcome:
        destination = ctx.output_dir / "baseline" / "measurements.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        measurements = evaluate_solidcraft_model(
            model_path,
            destination,
        )
        evidence = verify_solidcraft_measurements(
            measurements,
            expectation,
        )
        return CheckOutcome.passed(
            evidence=evidence,
            artifacts=(destination,),
        )

    return run


def _resolve_measurement_change_path(
    result: Any,
    path: tuple[str | int, ...],
    change_id: str,
) -> float:
    """Resolve one numeric SolidCraft measurement path."""

    current = result
    label = "$"
    for segment in path:
        if isinstance(segment, str):
            mapping = _evidence_mapping(current, label)
            if segment not in mapping:
                raise SolidCraftEvidenceError(
                    f"{label}.{segment} is required"
                )
            current = mapping[segment]
            label = f"{label}.{segment}"
        else:
            values = _evidence_list(current, label)
            if segment >= len(values):
                raise SolidCraftEvidenceError(
                    f"{label}[{segment}] is out of range"
                )
            current = values[segment]
            label = f"{label}[{segment}]"

    return _evidence_number(
        current,
        f"saved design change {change_id} {label}",
    )


def _measurement_change_evidence(
    baseline: Mapping[str, Any],
    mutated: Mapping[str, Any],
    definition: SolidCraftMeasurementChangeExpectation,
) -> dict[str, Any]:
    """Compare one numeric measurement before and after a saved design."""

    baseline_value = _resolve_measurement_change_path(
        baseline,
        definition.path,
        definition.id,
    )
    mutated_value = _resolve_measurement_change_path(
        mutated,
        definition.path,
        definition.id,
    )
    absolute_delta = abs(mutated_value - baseline_value)
    comparison = require_condition(
        absolute_delta > definition.minimum_absolute_delta,
        expected={
            "absolute_delta_gt": definition.minimum_absolute_delta,
        },
        actual={
            "baseline": baseline_value,
            "mutated": mutated_value,
            "absolute_delta": absolute_delta,
        },
        label=f"SolidCraft saved design change {definition.id}",
    )
    return {
        "id": definition.id,
        "path": list(definition.path),
        "comparison": comparison,
    }


def _saved_design_check(
    model_path: Path,
    definition: SolidCraftSavedDesign,
):
    """Build one independent saved-design verification check."""

    def run(ctx: VerificationContext) -> CheckOutcome:
        root = ctx.output_dir / "saved_designs" / definition.id
        root.mkdir(parents=True, exist_ok=True)
        changed_model = root / "model.sc"
        measurements_path = root / "measurements.json"

        mutate_solidcraft_model(
            model_path,
            definition.command_path,
            changed_model,
        )
        measurements = evaluate_solidcraft_model(
            changed_model,
            measurements_path,
        )
        evidence = verify_solidcraft_measurements(
            measurements,
            definition.expectation,
        )
        if definition.changes:
            baseline_path = (
                ctx.output_dir / "baseline" / "measurements.json"
            )
            baseline = _load_json(
                baseline_path,
                object_required=True,
            )
            evidence = dict(evidence)
            evidence["changes"] = [
                _measurement_change_evidence(
                    baseline,
                    measurements,
                    change,
                )
                for change in definition.changes
            ]
        return CheckOutcome.passed(
            evidence=evidence,
            artifacts=(changed_model, measurements_path),
        )

    return run


def _inspection_path_evidence(path: tuple[Any, ...]) -> list[Any]:
    """Return a JSON-compatible deterministic inspection path."""

    result = []
    for segment in path:
        if isinstance(segment, SolidCraftInspectionSelect):
            result.append(
                {
                    "select": {
                        "field": segment.field,
                        "value": segment.value,
                    }
                }
            )
        else:
            result.append(segment)
    return result


def _evidence_json_scalar(value: Any, path: str) -> Any:
    """Return one finite JSON scalar from inspection evidence."""

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SolidCraftEvidenceError(f"{path} must be finite")
        return value
    raise SolidCraftEvidenceError(f"{path} must be a JSON scalar")


def _resolve_inspection_path(
    result: Any,
    path: tuple[Any, ...],
    check_id: str,
) -> Any:
    """Resolve one explicit inspection JSON path."""

    current = result
    label = "$"
    for segment in path:
        if isinstance(segment, str):
            mapping = _evidence_mapping(current, label)
            if segment not in mapping:
                raise SolidCraftEvidenceError(
                    f"{label}.{segment} is required"
                )
            current = mapping[segment]
            label = f"{label}.{segment}"
            continue

        if isinstance(segment, int):
            values = _evidence_list(current, label)
            if segment >= len(values):
                raise SolidCraftEvidenceError(
                    f"{label}[{segment}] is out of range"
                )
            current = values[segment]
            label = f"{label}[{segment}]"
            continue

        values = _evidence_list(current, label)
        matches = []
        for index, value in enumerate(values):
            row_path = f"{label}[{index}]"
            row = _evidence_mapping(value, row_path)
            if segment.field not in row:
                raise SolidCraftEvidenceError(
                    f"{row_path}.{segment.field} is required"
                )
            selector_value = _evidence_json_scalar(
                row[segment.field],
                f"{row_path}.{segment.field}",
            )
            if selector_value == segment.value:
                matches.append(row)

        require_equal(
            1,
            len(matches),
            label=(
                f"SolidCraft inspection {check_id} selector "
                f"{segment.field}={segment.value!r}"
            ),
        )
        current = matches[0]
        label = (
            f"{label}[{segment.field}={segment.value!r}]"
        )

    return current


def _compare_inspection_numeric(
    expected: Any,
    actual: Any,
    tolerance: float,
    label: str,
) -> dict[str, Any]:
    """Compare one numeric scalar or flat vector with tolerance."""

    if isinstance(expected, float):
        return compare_scalar(
            expected,
            _evidence_number(actual, label),
            tolerance,
            label=label,
        )

    values = _evidence_list(actual, label)
    require_equal(
        len(expected),
        len(values),
        label=f"{label} vector length",
    )
    actual_values = [
        _evidence_number(value, f"{label}[{index}]")
        for index, value in enumerate(values)
    ]
    differences = [
        abs(actual_value - expected_value)
        for expected_value, actual_value in zip(expected, actual_values)
    ]
    maximum = max(differences, default=0.0)
    return require_condition(
        maximum <= tolerance,
        expected={
            "value": expected,
            "tolerance": tolerance,
        },
        actual={
            "value": actual_values,
            "max_difference": maximum,
        },
        label=label,
    )


def _projected_inspection_evidence(
    result: Any,
    checks: tuple[SolidCraftInspectionCheck, ...],
) -> dict[str, Any]:
    """Apply data-only projected inspection checks."""

    rows = []
    for check in checks:
        actual = _resolve_inspection_path(result, check.path, check.id)
        label = f"SolidCraft inspection check {check.id}"

        if check.count is not None:
            if isinstance(actual, Mapping):
                actual_count = len(actual)
            elif isinstance(actual, list):
                actual_count = len(actual)
            else:
                raise SolidCraftEvidenceError(
                    f"{label} count target must be an array or object"
                )
            comparison = require_equal(
                check.count,
                actual_count,
                label=label,
            )
        elif check.tolerance is not None:
            comparison = _compare_inspection_numeric(
                check.expected,
                actual,
                check.tolerance,
                label,
            )
        else:
            comparison = require_equal(
                check.expected,
                actual,
                label=label,
            )

        rows.append(
            {
                "id": check.id,
                "path": _inspection_path_evidence(check.path),
                "comparison": comparison,
            }
        )

    return {"checks": rows}


def _inspection_check(
    model_path: Path,
    definition: SolidCraftInspection,
):
    """Build one read-only SolidCraft inspection check."""

    def run(ctx: VerificationContext) -> CheckOutcome:
        root = ctx.output_dir / "inspections" / definition.id
        root.mkdir(parents=True, exist_ok=True)
        result_path = root / "results.json"
        result = inspect_solidcraft_model(
            model_path,
            definition.command_path,
            result_path,
        )

        evidence: Any = {"result": result}
        if definition.expected is not _NO_INSPECTION_EXPECTATION:
            evidence = require_equal(
                definition.expected,
                result,
                label=f"SolidCraft inspection {definition.id}",
            )
        elif definition.checks:
            evidence = _projected_inspection_evidence(
                result,
                definition.checks,
            )

        return CheckOutcome.passed(
            evidence=evidence,
            artifacts=(result_path,),
        )

    return run


def run_solidcraft_verification(
    model_path: Path,
    output_dir: Path,
    definition: SolidCraftVerification,
) -> dict[str, Any]:
    """Run one declarative verification for an existing SolidCraft model."""

    if not isinstance(definition, SolidCraftVerification):
        raise VerificationConfigError(
            "definition must be a SolidCraftVerification"
        )

    model = Path(model_path).resolve()
    output = Path(output_dir).resolve()

    checks = [
        VerificationCheck(
            "baseline",
            _baseline_check(model, definition.baseline),
        )
    ]
    checks.extend(
        VerificationCheck(
            f"saved_design_{item.id}",
            _saved_design_check(model, item),
        )
        for item in definition.saved_designs
    )
    checks.extend(
        VerificationCheck(
            f"inspection_{item.id}",
            _inspection_check(model, item),
        )
        for item in definition.inspections
    )

    context = VerificationContext(
        verification_id=definition.verification_id,
        input_path=model,
        output_dir=output,
        metadata=definition.metadata,
    )
    return verify(context, checks)


def load_solidcraft_verification(path: Path) -> SolidCraftVerification:
    """Load one model-local Python verification definition."""

    source = Path(path)
    try:
        namespace = runpy.run_path(str(source))
    except FileNotFoundError as exc:
        raise VerificationConfigError(
            f"SolidCraft verification definition does not exist: {source}"
        ) from exc
    except VerificationConfigError:
        raise
    except Exception as exc:
        raise VerificationConfigError(
            f"could not load SolidCraft verification definition: {source}: {exc}"
        ) from exc

    definition = namespace.get("VERIFICATION")
    if not isinstance(definition, SolidCraftVerification):
        raise VerificationConfigError(
            "SolidCraft verification definition must export "
            f"VERIFICATION = SolidCraftVerification(...): {source}"
        )
    return definition


def run_solidcraft_verification_file(
    model_path: Path,
    output_dir: Path,
    definition_path: Path,
) -> dict[str, Any]:
    """Load one model definition and run the existing SolidCraft verifier."""

    return run_solidcraft_verification(
        model_path,
        output_dir,
        load_solidcraft_verification(definition_path),
    )

