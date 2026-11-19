"""SolidCraft measurement-schema adapters for Forge verification.

This module knows the SolidCraft measurement JSON shape only. Numeric and
geometry comparison behavior remains in lib.py.cad.verfication.
"""

from __future__ import annotations

from typing import Any, Mapping

from cad_verification import BodyEnvelope


def measured_body_envelopes(
    data: Mapping[str, Any],
) -> tuple[BodyEnvelope, ...]:
    """Convert measured SolidCraft body bounds to generic library envelopes."""

    result = []
    bodies = data.get("bodies", [])
    if not isinstance(bodies, list):
        return ()

    for body in bodies:
        if not isinstance(body, Mapping):
            continue
        bbox = body.get("bbox")
        if not isinstance(bbox, Mapping):
            continue
        minimum = bbox.get("min")
        maximum = bbox.get("max")
        if minimum is None or maximum is None:
            continue
        name = str(body.get("name", "")).strip() or None
        result.append(
            BodyEnvelope(
                minimum=tuple(minimum),
                maximum=tuple(maximum),
                label=name,
            )
        )
    return tuple(result)
