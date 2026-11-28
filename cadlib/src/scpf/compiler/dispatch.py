"""Backend-neutral compiler orchestration over Forge semantic IR."""
from ..core import Shape
from .legacy import compile_shape_legacy_with_dependencies


def compile_model_with_dependencies(shape: Shape, name: str):
    """Compile current public Shape intent through the SolidCraft boundary."""
    if getattr(shape, "_configuration", None) is not None:
        return compile_shape_legacy_with_dependencies(shape, name)

    from ..backends.solidcraft import compile_ir_with_dependencies
    from ..ir import normalize_shape
    return compile_ir_with_dependencies(normalize_shape(shape), name)


_compile_model_with_dependencies = compile_model_with_dependencies
