"""Experimental compiler-history controls for SCPF.

This module deliberately keeps policy separate from geometry. A behavior()
scope influences how semantic objects created inside that scope are lowered
to SolidCraft history.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from enum import Enum


class History(str, Enum):
    """Choose how supported semantic features are lowered to native history.

    Use when:
        Select AUTO for normal Forge behaviour, or deliberately request one of
        the supported native/sketch history policies inside behavior().

    Limits:
        This is a compiler-history policy, not a geometry operation. Exact
        effects depend on the feature being compiled.
    """
    AUTO = "auto"
    NATIVE = "native"
    SKETCH = "sketch"


_history = ContextVar("scpf_history_policy", default=History.AUTO)


def active_history():
    return _history.get()


@contextmanager
def behavior(*, history=History.AUTO):
    """Temporarily select a History policy for objects created in the scope.

    Use when:
        A model intentionally needs to compare or request a particular supported
        lowering strategy without changing the geometry API.

    Limits:
        The policy applies only inside the context and only to features that
        inspect the active history setting.
    """
    try:
        history = History(history)
    except ValueError as exc:
        raise ValueError("history must be History.AUTO, NATIVE or SKETCH") from exc
    token = _history.set(history)
    try:
        yield
    finally:
        _history.reset(token)
