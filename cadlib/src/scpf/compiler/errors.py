"""Compiler validation errors and shared numeric guards."""
from math import isfinite

from ..core import _pv as pv


class ModelError(ValueError):
    """Report unsupported or invalid CAD model intent."""


def require_positive(value, label):
    num = pv(value)
    if not isfinite(num) or num <= 0:
        raise ModelError(f"{label} must be positive")
    return num


# Private compatibility name used by backend lowering.
_require_positive = require_positive
