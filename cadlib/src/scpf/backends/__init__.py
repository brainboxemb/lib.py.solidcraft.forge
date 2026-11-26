"""Internal native-backend registry for Forge lowering.

The public authoring surface remains in scpf.core/model objects. Backend
selection happens once, after model evaluation, through this adapter boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any


Compile = Callable[[Any, str], tuple[dict, frozenset[str]]]


@dataclass(frozen=True)
class BackendAdapter:
    """One native Forge lowering/execution contract."""

    id: str
    display_name: str
    compile_shape: Compile
    compile_assembly: Compile | None
    document_family: str
    executor: str
    capabilities: frozenset[str]
    experimental: bool = False

    @property
    def supports_assemblies(self) -> bool:
        return self.compile_assembly is not None


def _solidcraft_adapter() -> BackendAdapter:
    from ..assembly import _compile_assembly_with_dependencies
    from ..compiler import _compile_model_with_dependencies

    return BackendAdapter(
        id="solidcraft",
        display_name="SolidCraft",
        compile_shape=_compile_model_with_dependencies,
        compile_assembly=_compile_assembly_with_dependencies,
        document_family="solidcraft-command-or-scpf-replay",
        executor="solidcraft-cli",
        capabilities=frozenset(
            {
                "stable-forge-surface",
                "assemblies",
                "native-drawings",
                "native-topology",
            }
        ),
    )


def _mitcad_adapter() -> BackendAdapter:
    from .mitcad import compile_model_with_dependencies

    return BackendAdapter(
        id="mitcad",
        display_name="Mitcad",
        compile_shape=compile_model_with_dependencies,
        compile_assembly=None,
        document_family="scpf-mitcad",
        executor="mitcad-mcp",
        capabilities=frozenset(
            {
                "primitive.box",
                "sketch.circle",
                "feature.extrude.distance",
                "modify.chamfer.face-boundary",
                "native-topology",
            }
        ),
        experimental=True,
    )


_FACTORIES = {
    "solidcraft": _solidcraft_adapter,
    "mitcad": _mitcad_adapter,
}


def get_backend(name: str) -> BackendAdapter:
    """Return one registered backend without importing unused engines."""
    try:
        factory = _FACTORIES[name]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"unknown SCPF backend: {name!r}") from exc
    return factory()


def backend_ids() -> tuple[str, ...]:
    return tuple(_FACTORIES)


__all__ = ["BackendAdapter", "backend_ids", "get_backend"]
