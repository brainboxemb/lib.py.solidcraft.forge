"""Internal native-backend registry for Forge lowering.

The public authoring surface remains in scpf.core/model objects. Backend
selection happens once, after model evaluation, through this adapter boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any

# These imports intentionally happen while scpf.runner itself is being imported.
# Importing scpf.assembly lazily after package initialization would overwrite the
# public scpf.assembly decorator with Python's submodule attribute.
from ..assembly import _compile_assembly_with_dependencies as _solidcraft_compile_assembly
from .solidcraft import compile_ir_with_dependencies as _solidcraft_compile_ir


Compile = Callable[[Any, str], tuple[dict, frozenset[str]]]


@dataclass(frozen=True)
class BackendAdapter:
    """One native Forge lowering/execution contract."""

    id: str
    display_name: str
    compile_ir: Compile
    compile_assembly: Compile | None
    document_family: str
    executor: str
    capabilities: frozenset[str]
    experimental: bool = False

    @property
    def supports_assemblies(self) -> bool:
        return self.compile_assembly is not None

    @property
    def compile_shape(self) -> Compile:
        """Compatibility alias while internal callers migrate to compile_ir."""
        return self.compile_ir


def _solidcraft_adapter() -> BackendAdapter:
    return BackendAdapter(
        id="solidcraft",
        display_name="SolidCraft",
        compile_ir=_solidcraft_compile_ir,
        compile_assembly=_solidcraft_compile_assembly,
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
    from .mitcad import compile_ir_with_dependencies

    return BackendAdapter(
        id="mitcad",
        display_name="Mitcad",
        compile_ir=compile_ir_with_dependencies,
        compile_assembly=None,
        document_family="scpf-mitcad",
        executor="mitcad-mcp",
        capabilities=frozenset(
            {
                "primitive.box",
                "primitive.cylinder",
                "primitive.sphere",
                "boolean.subtract",
                "boolean.join",
                "boolean.intersect",
                "placement.primitive",
                "sketch.circle",
                "sketch.polygon",
                "profile.region",
                "feature.extrude.distance",
                "feature.extrude.symmetric",
                "feature.revolve.angle",
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
    """Return one registered backend without importing unused experimental engines."""
    try:
        factory = _FACTORIES[name]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"unknown SCPF backend: {name!r}") from exc
    return factory()


def backend_ids() -> tuple[str, ...]:
    return tuple(_FACTORIES)


__all__ = ["BackendAdapter", "backend_ids", "get_backend"]
