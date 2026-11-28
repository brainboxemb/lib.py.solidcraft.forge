"""Top-level semantic normalization dispatch.

Domain normalization lives in :mod:`scpf.ir.normalizers`; this module keeps
only the stable model/shape entry points and portability query.
"""
from __future__ import annotations

from ..core import Shape
from .base import BodyIR
from .body import LegacyShapeIR
from .configuration import ConfiguredDesignIR, ModelIR
from .normalizers.body import _normalize_node
from .normalizers.configuration import _named_feature_ir, normalize_configured_design
from .normalizers.values import _parameter_ir

def normalize_model(value) -> ModelIR | ConfiguredDesignIR:
    """Normalize one current Forge result into backend-independent semantic IR."""
    from ..model_objects import Assembly, ModelInstance

    if isinstance(value, Shape):
        if getattr(value, "_configuration", None) is not None:
            return normalize_configured_design(value)
        root = _normalize_node(value)
        return ModelIR(
            root=root,
            parameters=_parameter_ir(value),
            named_features=(
                _named_feature_ir(value, root)
                if isinstance(root, BodyIR)
                else ()
            ),
        )
    if isinstance(value, (ModelInstance, Assembly)):
        if getattr(value, "_configuration", None) is not None:
            return normalize_configured_design(value)
    raise TypeError(
        "Forge IR normalization requires Shape or configured ModelInstance/Assembly"
    )

def normalize_shape(shape: Shape) -> ModelIR:
    """Normalize one Forge Shape into backend-independent semantic IR."""
    if not isinstance(shape, Shape):
        raise TypeError("Forge IR normalization requires a Shape")
    return normalize_model(shape)


def is_portable(model: ModelIR | ConfiguredDesignIR) -> bool:
    """Return whether one semantic design no longer depends on LegacyShapeIR."""
    if isinstance(model, ModelIR):
        return not isinstance(model.root, LegacyShapeIR)
    if isinstance(model, ConfiguredDesignIR):
        from ..assembly_ir import AssemblyIR

        if isinstance(model.design, ModelIR):
            return is_portable(model.design)
        if isinstance(model.design, AssemblyIR):
            return all(
                is_portable(definition.model)
                for definition in model.design.definitions
            )
    return False
