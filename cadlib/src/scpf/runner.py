"""Execute a trusted SCPF model and compile it through Forge semantic IR.

A script may end with an explicit model call such as Plate(). If the file
instead defines exactly one public class with build(), that class is used as
the root model automatically. This lets reusable component source files run
standalone without a launcher or duplicate model definition.

Within build() or a final model function, a last geometry expression acts as
an implicit return. No show() or main() is required.
"""
import ast
from contextlib import contextmanager
from dataclasses import dataclass, is_dataclass
from enum import Enum
import functools
import inspect
from pathlib import Path
import sys
import warnings

from . import core, cadmath
from .configurations import (
    Always,
    ConfigRule,
    Configure,
    DriveParameter,
    Param,
    Suppress,
    _ConfiguredDesign,
    _apply_configuration_document,
)
from .compiler import ModelError, _compile_model_with_dependencies
from .core import Expression, Parameter, Shape, command_value, parameters_in, _pv as pv
from .model_objects import (
    Assembly,
    DrawingDimension,
    DrawingNote,
    DrawingRevision,
    DrawingView,
    ModelDefinition,
    ModelInstance,
    Placement,
)
from .explicit_sketch import Sketch
from .backends import get_backend
from .ir import normalize_model, normalize_shape
from .assembly_ir import normalize_assembly


class ModelParameterWarning(UserWarning):
    """Warn that an editable model parameter lost a native CAD dependency.

    Use when:
        Tooling wants to detect parameters that became concrete Python values or
        are only partly associative in the generated SolidCraft model.

    Limits:
        This is a warning category, not an exception. The preferred fix is to
        preserve the symbolic relationship or mark an intentional build-time
        input with a leading underscore.
    """


@dataclass(frozen=True)
class _BuiltDesign:
    result: object
    parameters: tuple[tuple[str, float], ...]
    pv_parameters: tuple[str, ...] = ()


def _warn_missing_model_parameters(
    parameters,
    dependencies,
    *,
    context="model",
    pv_parameters=(),
    backend_name="SolidCraft",
):
    """Warn from actual emitted dependencies and explicit user pv() reads."""
    native = set(dependencies)
    concrete_reads = set(pv_parameters)

    for name, _ in parameters:
        if name in concrete_reads:
            if name in native:
                detail = (
                    "remains a native dependency, but pv() also consumes its "
                    f"current Python value. Changing the {backend_name} "
                    "parameter may therefore update only part of the model."
                )
            else:
                detail = (
                    f"has no native {backend_name} dependency and pv() "
                    "consumes its current Python value."
                )
            warnings.warn(
                f"{context} parameter {name!r} {detail} Preserve the symbolic "
                "value wherever native associativity is required, or rename "
                f"it to _{name} if it is intentionally Forge/build-time.",
                ModelParameterWarning,
                stacklevel=3,
            )
        elif name not in native:
            warnings.warn(
                f"{context} parameter {name!r} has no native {backend_name} "
                "dependency; publishing a parameter alone does not make model "
                "geometry or placement associative. Preserve the symbolic "
                f"value, or rename it to _{name} if it is intentionally "
                "Forge/build-time.",
                ModelParameterWarning,
                stacklevel=3,
            )


def _symbolic(value, name):
    """Promote numeric model inputs to named CAD parameters."""
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        return Parameter(name, value)
    return value


def _model_function(function):
    """Call a function-based model with named symbolic CAD dimensions."""
    signature = inspect.signature(function)

    @functools.wraps(function)
    def wrapped(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        for name, value in bound.arguments.items():
            bound.arguments[name] = _symbolic(value, name)
        return function(*bound.args, **bound.kwargs)

    return wrapped


def _plain_model_fields(cls):
    """Ordered numeric model/build fields, excluding UPPER_CASE constants.

    Naming is intentional:
      lower_case   -> editable native model parameter
      _lower_case  -> Forge/build-time input, never a native parameter
      UPPER_CASE   -> fixed class constant, not a model input
    """
    fields = {}
    # Base model dimensions come first; subclasses may override defaults
    # without reimplementing build(). Existing key order stays stable.
    for base in reversed(cls.__mro__):
        if base is object:
            continue
        for name, value in vars(base).items():
            if (name.startswith("__")
                    or name.isupper()
                    or not isinstance(value, (int, float))
                    or isinstance(value, bool)):
                continue
            fields[name] = value
    return list(fields.items())


def _plain_reference_fields(cls):
    """Ordered non-parametric object inputs declared with a None default.

    These values are passed through to build() unchanged. They are intended
    for assembly/component references such as an already-built WoodFrame and
    never become SolidCraft parameters.
    """
    fields = {}
    for base in reversed(cls.__mro__):
        if base is object:
            continue
        for name, value in vars(base).items():
            if (
                name.startswith("__")
                or name.isupper()
                or value is not None
            ):
                continue
            fields[name] = value
    return list(fields.items())


def _definition_identity_value(value, name):
    """Return one stable hashable value for a reusable component input."""
    if isinstance(value, core._DirectionSelector):
        return (
            "direction_selector",
            tuple(value.vector),
        )
    if isinstance(value, core._ProfileEdgeSelection):
        return (
            "profile_edge_selection",
            tuple(value.patterns),
            value.sides,
            value.kind,
        )
    if isinstance(value, core._AxisRef):
        return (
            "axis_ref",
            str(value),
        )
    if isinstance(value, core._BoundOffset):
        return (
            "bound_offset",
            value.axis,
            value.reference,
            _definition_identity_value(value.delta, name),
        )
    if isinstance(value, Enum):
        enum_type = type(value)
        return (
            "enum",
            enum_type.__module__,
            enum_type.__qualname__,
            value.name,
        )
    if value is None:
        return ("none",)
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, str):
        return ("str", value)
    if isinstance(value, (int, float)):
        return ("number", float(value))
    if isinstance(value, tuple):
        return (
            "tuple",
            tuple(
                _definition_identity_value(item, name)
                for item in value
            ),
        )
    raise TypeError(
        f"{name}: {type(value).__name__} cannot be used in reusable "
        "component definition identity; use a fixed immutable value "
        "(None, bool, number, str, Enum, Forge selector or tuple)"
    )


def _parameter_input(
    value,
    name,
    *,
    expose_local=True,
    alias=None,
    build_only=False,
):
    """Bind one input while preserving explicit parameter publication intent.

    Parent Parameter/Expression inputs always stay symbolic. Plain numeric
    child-component defaults become editable local CAD parameters only when
    explicitly exposed through component(include=...). Root-model fields call
    this path with expose_local=True. Private underscore inputs remain
    Forge/build-time inputs.
    """
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a numeric model parameter")

    if build_only:
        if isinstance(value, (Parameter, Expression)):
            external = tuple((p.name, p.value) for p in parameters_in(value))
            return pv(value), value, external, (name, command_value(value)), False
        if isinstance(value, (int, float)):
            concrete = float(value)
            return concrete, concrete, (), None, True
        raise TypeError(f"{name} must be a numeric Forge/build parameter")

    # An explicit parent dependency wins over component-local publication or
    # aliases. The child keeps using the parent's native parameter/expression.
    if isinstance(value, (Parameter, Expression)):
        external = tuple((p.name, p.value) for p in parameters_in(value))
        return pv(value), value, external, (name, command_value(value)), False

    if isinstance(value, (int, float)):
        concrete = float(value)
        if alias is not None:
            parameter = Parameter(alias, concrete)
            return (
                concrete,
                parameter,
                ((alias, concrete),),
                (name, alias),
                False,
            )
        if expose_local:
            return concrete, Parameter(name, concrete), (), None, False
        return concrete, concrete, (), None, True

    raise TypeError(f"{name} must be a numeric model parameter")


def _plain_model_data(
    cls,
    *args,
    _include=None,
    _aliases=None,
    _definition_identity=False,
    **kwargs,
):
    """Instantiate a plain model and classify public vs fixed inputs."""
    fields = _plain_model_fields(cls)
    references = _plain_reference_fields(cls)
    names = [name for name, _ in fields]
    reference_names = [name for name, _ in references]
    if len(args) > len(fields):
        raise TypeError(
            f"{cls.__name__}() takes at most {len(fields)} positional model arguments"
        )

    values = dict(fields)
    reference_values = dict(references)
    assigned = set()
    for (name, _), value in zip(fields, args):
        values[name] = value
        assigned.add(name)

    for name, value in kwargs.items():
        if name in reference_values:
            if name in assigned:
                raise TypeError(
                    f"{cls.__name__}() got multiple values for input {name!r}"
                )
            reference_values[name] = value
            assigned.add(name)
            continue
        if name not in values:
            raise TypeError(
                f"{cls.__name__}() got an unexpected model input {name!r}"
            )
        if name in assigned:
            raise TypeError(
                f"{cls.__name__}() got multiple values for parameter {name!r}"
            )
        values[name] = value
        assigned.add(name)

    instance = cls()
    for name in reference_names:
        object.__setattr__(instance, name, reference_values[name])

    aliases = {} if _aliases is None else dict(_aliases)
    concrete = []
    fixed = []
    if _definition_identity:
        for name in reference_names:
            fixed.append((
                name,
                _definition_identity_value(reference_values[name], name),
            ))
    external = {}
    bindings = []
    for name in names:
        build_only = name.startswith("_")
        alias = aliases.get(name)
        expose_local = (
            not build_only
            and alias is None
            and (_include is None or name in _include)
        )
        value, symbolic, inherited, binding, is_fixed = _parameter_input(
            values[name],
            name,
            expose_local=expose_local,
            alias=alias,
            build_only=build_only,
        )
        if binding is None:
            if is_fixed:
                fixed.append((name, value))
            else:
                concrete.append((name, value))
        else:
            bindings.append(binding)
            for parameter_name, parameter_value in inherited:
                previous = external.setdefault(parameter_name, parameter_value)
                if previous != parameter_value:
                    raise ValueError(
                        f"conflicting inherited parameter {parameter_name!r}"
                    )
        object.__setattr__(instance, name, symbolic)

    return (
        instance,
        tuple(concrete),
        tuple(fixed),
        tuple(external.items()),
        tuple(bindings),
    )


def _plain_model_instance(cls, *args, **kwargs):
    """Instantiate a plain SCPF model class without requiring @dataclass."""
    return _plain_model_data(cls, *args, **kwargs)[0]


def _parameterized_instance(
    cls,
    *args,
    _include=None,
    _aliases=None,
    _definition_identity=False,
    **kwargs,
):
    """Construct one model object and classify its reusable inputs."""
    if not is_dataclass(cls):
        return _plain_model_data(
            cls,
            *args,
            _include=_include,
            _aliases=_aliases,
            _definition_identity=_definition_identity,
            **kwargs,
        )

    instance = cls(*args, **kwargs)
    aliases = {} if _aliases is None else dict(_aliases)
    signature = inspect.signature(cls)
    bound = signature.bind(*args, **kwargs)
    bound.apply_defaults()
    concrete = []
    fixed = []
    external = {}
    bindings = []
    for name, value in bound.arguments.items():
        if name not in vars(instance):
            continue
        if isinstance(value, (int, float, Parameter, Expression)) and not isinstance(value, bool):
            build_only = name.startswith("_")
            alias = aliases.get(name)
            expose_local = (
                not build_only
                and alias is None
                and (_include is None or name in _include)
            )
            number, symbolic, inherited, binding, is_fixed = _parameter_input(
                value,
                name,
                expose_local=expose_local,
                alias=alias,
                build_only=build_only,
            )
            if binding is None:
                if is_fixed:
                    fixed.append((name, number))
                else:
                    concrete.append((name, number))
            else:
                bindings.append(binding)
                for parameter_name, parameter_value in inherited:
                    previous = external.setdefault(parameter_name, parameter_value)
                    if previous != parameter_value:
                        raise ValueError(
                            f"conflicting inherited parameter {parameter_name!r}"
                        )
            object.__setattr__(instance, name, symbolic)
            continue

        if _definition_identity:
            fixed.append((
                name,
                _definition_identity_value(value, name),
            ))
    return (
        instance,
        tuple(concrete),
        tuple(fixed),
        tuple(external.items()),
        tuple(bindings),
    )



def _component_anchor_frames(instance):
    """Read optional named local attachment frames from one component model."""
    provider = getattr(instance, "anchors", None)
    if provider is None:
        return ()
    value = provider() if callable(provider) else provider
    if not isinstance(value, dict):
        raise TypeError("component anchors must be returned as a dict")

    anchors = []
    standard_names = {anchor.value for anchor in core.Anchor}
    for name, frame in value.items():
        if not isinstance(name, str) or not name.isidentifier():
            raise ValueError(
                "component anchor names must be valid Python identifiers"
            )
        if name in standard_names:
            raise ValueError(
                f"component anchor {name!r} conflicts with a standard Anchor"
            )
        if not isinstance(frame, (core.AnchorFrame, core.AnchorTopology)):
            raise TypeError(
                f"component anchor {name!r} must be an AnchorFrame "
                "or AnchorTopology"
            )
        anchors.append((name, frame))
    return tuple(anchors)


def _build_object(
    cls,
    *args,
    _include=None,
    _aliases=None,
    _definition_identity=False,
    **kwargs,
):
    """Build one user model and return its classified reusable inputs."""
    instance, concrete, fixed, external, bindings = _parameterized_instance(
        cls,
        *args,
        _include=_include,
        _aliases=_aliases,
        _definition_identity=_definition_identity,
        **kwargs,
    )
    build = getattr(instance, "build", None)
    if not callable(build):
        raise TypeError(f"{cls.__name__} must define build()")

    tracked_parameters = []
    for parameter_name, _ in concrete:
        value = getattr(instance, parameter_name, None)
        if isinstance(value, Parameter):
            tracked_parameters.append(value)

    with core._track_pv_reads(tracked_parameters) as pv_parameters:
        result = build()
        anchors = _component_anchor_frames(instance)

    return (
        result,
        concrete,
        fixed,
        external,
        bindings,
        anchors,
        tuple(sorted(pv_parameters)),
    )


def _design_object(cls, *args, **kwargs):
    """Build the root model and retain its declared native parameters."""
    result, concrete, _, _, _, _, pv_parameters = _build_object(
        cls, *args, **kwargs
    )
    if not isinstance(result, (Shape, ModelInstance, Assembly, _ConfiguredDesign)):
        raise TypeError(
            f"{cls.__name__}.build() must finish with a Shape or assembly"
        )
    return _BuiltDesign(
        result=result,
        parameters=concrete,
        pv_parameters=pv_parameters,
    )


def _component_feature_exports(shape):
    """Collect explicitly exported Forge features from one component Shape tree."""
    exports = {}

    def visit(node):
        if isinstance(node, Shape):
            if node.kind == "exported_feature":
                _source, name = node.data
                previous = exports.get(name)
                if previous is not None and previous is not node:
                    raise ValueError(
                        f"duplicate exported component feature {name!r}"
                    )
                exports[name] = node
            visit(node.data)
            return
        if isinstance(node, (tuple, list)):
            for item in node:
                visit(item)

    visit(shape)
    return tuple(exports.items())


def _reusable_model_object(
    cls,
    *args,
    _include=(),
    _aliases=None,
    **kwargs,
):
    """Build a nested user model as a reusable component definition."""
    object_name = kwargs.pop("name", None)
    placement = kwargs.pop("placement", None)
    if placement is None:
        placement = Placement()
    elif not isinstance(placement, Placement):
        raise TypeError("component placement must be a Placement")
    if object_name is not None:
        if (
            not isinstance(object_name, str)
            or not object_name.isidentifier()
            or object_name.startswith("_")
        ):
            raise ValueError(
                "component object name must be a public Python identifier"
            )

    result, concrete, fixed, external, bindings, anchors, pv_parameters = _build_object(
        cls,
        *args,
        _include=_include,
        _aliases=_aliases,
        _definition_identity=True,
        **kwargs,
    )
    if not isinstance(result, Shape):
        raise TypeError(
            f"{cls.__name__}.build() must produce one Shape when reused as a component"
        )
    return ModelInstance(
        ModelDefinition(
            class_name=cls.__name__,
            parameters=concrete,
            shape=result,
            fixed_inputs=fixed,
            external_parameters=external,
            input_bindings=bindings,
            anchors=anchors,
            features=_component_feature_exports(result),
        ),
        placement=placement,
        name=object_name,
        flattened_parameters=pv_parameters,
    )


def _component_include(cls, include):
    """Return explicitly published local inputs and optional shared aliases."""
    fields = {name for name, _ in _plain_model_fields(cls)}
    public_fields = {name for name in fields if not name.startswith("_")}

    if include == "*":
        return frozenset(public_fields), {}

    if isinstance(include, dict):
        aliases = dict(include)
        unknown = set(aliases) - public_fields
        if unknown:
            raise ValueError(
                f"{cls.__name__}: unknown component parameter(s): "
                + ", ".join(sorted(unknown))
            )
        for local_name, model_name in aliases.items():
            if (
                not isinstance(model_name, str)
                or not model_name.isidentifier()
                or model_name.startswith("_")
                or model_name.isupper()
            ):
                raise ValueError(
                    f"{cls.__name__}.{local_name}: shared model parameter "
                    "name must be a public lower_case Python identifier"
                )
        return frozenset(), aliases

    if isinstance(include, str):
        include = (include,)
    try:
        names = tuple(include)
    except TypeError as exc:
        raise TypeError(
            "component include must be '*', parameter names, or a mapping"
        ) from exc
    if any(not isinstance(name, str) or not name for name in names):
        raise TypeError("component include names must be non-empty text")

    unknown = set(names) - public_fields
    if unknown:
        raise ValueError(
            f"{cls.__name__}: unknown component parameter(s): "
            + ", ".join(sorted(unknown))
        )
    return frozenset(names), {}


def _model_factory(cls, include=()):
    """Replace a nested class name with a transparent reusable-model factory."""
    included, aliases = _component_include(cls, include)

    @functools.wraps(cls)
    def factory(*args, **kwargs):
        return _reusable_model_object(
            cls,
            *args,
            _include=included,
            _aliases=aliases,
            **kwargs,
        )

    factory._scpf_component_class = cls
    return factory


def component(cls=None, *, include=()):
    """Declare one reusable physical component definition.

    Parameters:
        cls: Model class whose build() returns one physical part. Omit when using @component(...) as a decorator factory.
        include: Child default parameters to publish. Use names, "*", or a mapping for renamed shared parameters.

    Use when:
        Decorate a model class whose build() result represents one reusable
        physical part. Child defaults stay fixed unless explicitly published
        with include=. Parent Parameter/Expression inputs remain symbolic.

    Limits:
        build() must produce one Shape when reused as a component.

    Example:
        @component(include=("inside_corner_radius",))
        class CornerBracket:
            pass
    """
    def decorate(model_cls):
        if not isinstance(model_cls, type) or not callable(
            getattr(model_cls, "build", None)
        ):
            raise TypeError("component() expects a model class with build()")
        return _model_factory(model_cls, include=include)

    if cls is None:
        return decorate
    return decorate(cls)

def _reusable_assembly_object(cls, *args, **kwargs):
    """Build an imported assembly class without exposing build_* helpers."""
    result, _, _, _, _, _, _ = _build_object(cls, *args, **kwargs)
    if not isinstance(result, (ModelInstance, Assembly)):
        raise TypeError(
            f"{cls.__name__}.build() must produce a component or assembly"
        )
    return result


def _assembly_factory(cls):
    @functools.wraps(cls)
    def factory(*args, **kwargs):
        return _reusable_assembly_object(cls, *args, **kwargs)
    factory._scpf_assembly_class = cls
    return factory


def assembly(cls):
    """Declare a reusable class that composes component occurrences.

    Parameters:
        cls: Model class whose build() returns a component occurrence or Assembly.

    Use when:
        Decorate a class when the class itself represents a reusable assembly
        or subassembly built from component occurrences and their relationships.

    Limits:
        build() must return a component occurrence or Assembly. The decorator
        does not itself create grouping or attachment relationships; those come
        from the objects returned by build().

    Example:
        @assembly
        class Frame:
            pass
    """
    if not isinstance(cls, type) or not callable(getattr(cls, "build", None)):
        raise TypeError("assembly() expects a model class with build()")
    return _assembly_factory(cls)


def _implicit_shape(body):
    """Turn a trailing expression into an implicit return.

    This is a deliberate SCPF model convention; do not rewrite nested
    helper methods or unrelated Python functions. Explicit return stays
    valid. A last assignment alone is not treated as a CAD result.
    """
    if body and isinstance(body[-1], ast.Expr):
        body[-1] = ast.copy_location(ast.Return(value=body[-1].value), body[-1])


def _model_local_import_names(path: Path) -> set[str]:
    """Return top-level Python import names owned beside one model.py."""

    names: set[str] = set()
    for entry in path.parent.iterdir():
        if entry == path or entry.name == "__pycache__":
            continue
        if entry.is_file():
            if (
                entry.suffix == ".py"
                and entry.stem != "__init__"
                and entry.stem.isidentifier()
            ):
                names.add(entry.stem)
            continue
        if (
            entry.is_dir()
            and entry.name.isidentifier()
            and any(child.suffix == ".py" for child in entry.rglob("*.py"))
        ):
            names.add(entry.name)
    return names


def _model_local_modules(names: set[str]) -> dict[str, object]:
    """Return currently loaded modules shadowed by model-local import names."""

    return {
        name: module
        for name, module in tuple(sys.modules.items())
        if name.partition(".")[0] in names
    }


@contextmanager
def _model_import_context(path: Path):
    """Make project-local component imports available for a model script.

    A script in `<project>/models/<slug>/scpf/model.py` may import
    `models.components.*`. This must work whether the user runs SCPF from
    the repository root or from the script's own directory.

    Only the execution of this trusted script receives these import paths.
    Imports owned beside model.py are isolated for this execution so two model
    roots may use the same local package names. The broader project root stays
    shared for imports such as models.components.*. Restore sys.path and the
    caller's pre-existing local-name modules afterwards; do not require
    user-set PYTHONPATH.
    """
    local_root = path.parent
    roots = [local_root]
    for ancestor in path.parents:
        if ancestor.name == "models":
            roots.append(ancestor.parent)
            break

    local_names = _model_local_import_names(path)
    original_modules = _model_local_modules(local_names)
    for module_name in original_modules:
        sys.modules.pop(module_name, None)

    original = sys.path[:]
    original_dont_write_bytecode = sys.dont_write_bytecode
    try:
        # Model projects often split parts and assemblies over small Python
        # modules. Keep those source trees clean: imported model modules are
        # transient build input and do not need adjacent __pycache__ files.
        sys.dont_write_bytecode = True
        for root in reversed(roots):
            folder = str(root)
            if folder in sys.path:
                sys.path.remove(folder)
            sys.path.insert(0, folder)
        yield
    finally:
        # Imports owned beside model.py are private to this run. Remove modules
        # loaded from that local namespace, then restore anything the caller
        # had loaded under the same name before run_script().
        for module_name in tuple(sys.modules):
            if module_name.partition(".")[0] in local_names:
                sys.modules.pop(module_name, None)
        sys.modules.update(original_modules)
        sys.path[:] = original
        sys.dont_write_bytecode = original_dont_write_bytecode


def _compile_assembly_result(value, name, backend_adapter):
    """Normalize core assembly semantics before backend selection/lowering."""
    assembly = Assembly((value,)) if isinstance(value, ModelInstance) else value
    if not isinstance(assembly, Assembly):
        raise TypeError("assembly result must contain reusable model instances")

    model = normalize_assembly(assembly)
    if backend_adapter.compile_assembly is None:
        raise ModelError(
            f"{backend_adapter.display_name} backend does not support "
            "Forge AssemblyIR in its qualified capability set"
        )

    has_presentation = bool(
        assembly.drawings
        or assembly.exploded_views
        or assembly.exploded_display_set
    )
    if has_presentation:
        if backend_adapter.id != "solidcraft":
            raise ModelError(
                f"{backend_adapter.display_name} backend does not support "
                "Forge assembly presentation state"
            )
        # Drawings/exploded views are output presentation, explicitly outside
        # the core CAD-IR denominator. The SolidCraft compatibility layer
        # appends that presentation after validating the same AssemblyIR core.
        from .assembly import _compile_assembly_with_dependencies
        return _compile_assembly_with_dependencies(assembly, name)

    return backend_adapter.compile_assembly(model, name)


def run_script(path: str | Path, *, backend: str = "solidcraft") -> dict:
    """Execute a trusted SCPF model source file and return its command document.

    Parameters:
        path: Path to the trusted Python model source file.
        backend: Native lowering backend. Model evaluation and Forge IR
            normalization are backend-independent. "solidcraft" is the stable
            default; "mitcad" is experimental and intentionally incomplete.

    Use when:
        Programmatic tooling needs the same model-loading/root-selection and
        compilation behaviour as the SCPF CLI.

    Limits:
        The source is executed as trusted Python. A file must either end in an
        explicit root model call or define exactly one unambiguous public model
        class with build().

    Example:
        document = run_script("models/panel/scpf/model.py")
    """
    backend_adapter = get_backend(backend)

    path = Path(path).resolve()
    syntax = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    explicit_root = (
        bool(syntax.body)
        and isinstance(syntax.body[-1], ast.Expr)
        and isinstance(syntax.body[-1].value, ast.Call)
        and isinstance(syntax.body[-1].value.func, ast.Name)
    )

    if explicit_root:
        last = syntax.body.pop()
        name = last.value.func.id
    else:
        # A reusable component file should also be a valid standalone model.
        # Auto-select only when the choice is unambiguous: exactly one public
        # top-level class that defines build(). Never guess between models.
        candidates = []
        for item in syntax.body:
            if not isinstance(item, ast.ClassDef) or item.name.startswith("_"):
                continue
            if any(
                isinstance(member, ast.FunctionDef) and member.name == "build"
                for member in item.body
            ):
                candidates.append(item)

        if len(candidates) != 1:
            names = ", ".join(item.name for item in candidates) or "none"
            raise SyntaxError(
                "SCPF needs an explicit final model call unless the file "
                "defines exactly one public class with build(); "
                f"candidates: {names}"
            )

        name = candidates[0].name
        last = ast.Expr(
            value=ast.Call(
                func=ast.Name(id=name, ctx=ast.Load()),
                args=[],
                keywords=[],
            )
        )
        ast.fix_missing_locations(last)

    definitions = {
        item.name: item for item in syntax.body
        if isinstance(item, (ast.FunctionDef, ast.ClassDef))
    }
    definition = definitions.get(name)

    context = {
        "__name__": "__scpf_model__",
        "__file__": str(path.resolve()),
        "dataclass": dataclass,
        "Box": core.Box,
        "Cylinder": core.Cylinder,
        "Cone": core.Cone,
        "Hole": core.Hole,
        "CounterboreHole": core.CounterboreHole,
        "CountersinkHole": core.CountersinkHole,
        "ThreadedHole": core.ThreadedHole,
        "Lip": core.Lip,
        "SnapFit": core.SnapFit,
        "Boss": core.Boss,
        "Rest": core.Rest,
        "Depth": core.Depth,
        "Sphere": core.Sphere,
        "Polygon2D": core.Polygon2D,
        "Rectangle2D": core.Rectangle2D,
        "RoundedRectangle2D": core.RoundedRectangle2D,
        "Circle2D": core.Circle2D,
        "SlotCenterToCenter2D": core.SlotCenterToCenter2D,
        "SlotOverall2D": core.SlotOverall2D,
        "SlotCenterPoint2D": core.SlotCenterPoint2D,
        "SlotArcThreePoint2D": core.SlotArcThreePoint2D,
        "SlotArcCenter2D": core.SlotArcCenter2D,
        "Text2D": core.Text2D,
        "Edges": core.Edges,
        "Faces": core.Faces,
        "Anchor": core.Anchor,
        "AnchorFrame": core.AnchorFrame,
        "AnchorTopology": core.AnchorTopology,
        "Axis": core.Axis,
        "AxisLine": core.AxisLine,
        "Shape": core.Shape,
        "Parameter": core.Parameter,
        "cadmath": cadmath,
        "Configure": Configure,
        "Param": Param,
        "Suppress": Suppress,
        "ConfigRule": ConfigRule,
        "Always": Always,
        "DriveParameter": DriveParameter,
        "CENTER": core.CENTER,
        "TOP": core.TOP,
        "BOTTOM": core.BOTTOM,
        "LEFT": core.LEFT,
        "RIGHT": core.RIGHT,
        "FRONT": core.FRONT,
        "BACK": core.BACK,
        "Placement": Placement,
        "DrawingView": DrawingView,
        "DrawingNote": DrawingNote,
        "DrawingRevision": DrawingRevision,
        "DrawingDimension": DrawingDimension,
        "up": core.up,
        "down": core.down,
        "left": core.left,
        "right": core.right,
        "front": core.front,
        "back": core.back,
        "half": core.half,
        "midpoint": core.midpoint,
        "pv": core.pv,
        "X": core.X,
        "Y": core.Y,
        "Z": core.Z,
        "Sketch": Sketch,
        "component": component,
        "assembly": assembly,
    }
    if isinstance(definition, ast.FunctionDef):
        _implicit_shape(definition.body)

    model_classes = {}
    for item in syntax.body:
        if not isinstance(item, ast.ClassDef):
            continue
        build_method = next(
            (member for member in item.body
             if isinstance(member, ast.FunctionDef) and member.name == "build"),
            None,
        )
        if build_method is not None:
            _implicit_shape(build_method.body)
            model_classes[item.name] = item

    ast.fix_missing_locations(syntax)
    with _model_import_context(path):
        exec(compile(syntax, str(path), "exec"), context)

        root_object = context.get(name)
        root_component_class = getattr(
            root_object, "_scpf_component_class", None
        )
        root_assembly_class = getattr(
            root_object, "_scpf_assembly_class", None
        )
        root_is_class = isinstance(root_object, type)
        root_is_component = root_component_class is not None
        root_is_assembly = root_assembly_class is not None
        for class_name in model_classes:
            if class_name == name:
                continue
            model_object = context[class_name]
            if (
                getattr(model_object, "_scpf_component_class", None) is not None
                or getattr(model_object, "_scpf_assembly_class", None) is not None
            ):
                continue
            context[class_name] = _model_factory(model_object)

        if isinstance(definition, ast.FunctionDef):
            context[name] = _model_function(context[name])
            result = eval(
                compile(ast.Expression(body=last.value), str(path), "eval"), context
            )
        elif root_is_class or root_is_component:
            root_has_placement = any(
                keyword.arg == "placement"
                for keyword in last.value.keywords
            )
            if root_has_placement:
                raise ModelError(
                    "root component placement requires the identity-aware "
                    "occurrence executor; this foundational capability is not "
                    "qualified yet"
                )
            # A reusable @component source remains directly runnable as a
            # standalone design. Compile its original model class as the root
            # shape, while imported/nested uses keep the component factory.
            root_class = (
                root_object if root_is_class else root_component_class
            )
            constructor = ast.Call(
                func=ast.Name(id="_scpf_design_object", ctx=ast.Load()),
                args=[ast.Name(id="_scpf_root_class", ctx=ast.Load()), *last.value.args],
                keywords=last.value.keywords,
            )
            context["_scpf_design_object"] = _design_object
            context["_scpf_root_class"] = root_class
            ast.fix_missing_locations(constructor)
            built = eval(
                compile(ast.Expression(body=constructor), str(path), "eval"),
                context,
            )
            result = built.result
        elif root_is_assembly:
            constructor = ast.Call(
                func=ast.Name(id="_scpf_design_object", ctx=ast.Load()),
                args=[
                    ast.Name(id="_scpf_root_assembly_class", ctx=ast.Load()),
                    *last.value.args,
                ],
                keywords=last.value.keywords,
            )
            context["_scpf_design_object"] = _design_object
            context["_scpf_root_assembly_class"] = root_assembly_class
            ast.fix_missing_locations(constructor)
            built = eval(
                compile(ast.Expression(body=constructor), str(path), "eval"),
                context,
            )
            result = built.result
        else:
            raise SyntaxError(
                f"the last call must use a defined function/class or "
                f"an imported model/component/assembly: {name}"
            )

    if isinstance(result, _ConfiguredDesign):
        design = result.design
        if isinstance(design, Shape):
            try:
                model = normalize_model(result)
            except (TypeError, ValueError) as exc:
                if backend_adapter.id != "solidcraft":
                    raise ModelError(
                        f"{backend_adapter.display_name} backend does not support "
                        "Forge configurations in this qualified capability set: "
                        f"{exc}"
                    ) from exc
                # Stable SolidCraft owns the broad existing configuration
                # surface while semantic ConfigurationIR migrates slice by
                # slice. Unsupported portable forms keep that compatibility
                # path rather than being reinterpreted by another backend.
                document, dependencies = _compile_model_with_dependencies(
                    result, name
                )
            else:
                document, dependencies = backend_adapter.compile_ir(
                    model,
                    name,
                )
        elif isinstance(design, (ModelInstance, Assembly)):
            document, dependencies = _compile_assembly_result(
                design,
                name,
                backend_adapter,
            )
            if backend_adapter.id != "solidcraft":
                raise ModelError(
                    f"{backend_adapter.display_name} backend does not support "
                    "Forge configured AssemblyIR in its qualified capability set"
                )
            document = _apply_configuration_document(
                result, name, document
            )
        else:
            raise TypeError("Configure contains an unsupported design result")
    elif isinstance(result, Shape):
        model_ir = normalize_shape(result)
        document, dependencies = backend_adapter.compile_ir(model_ir, name)
    elif isinstance(result, (ModelInstance, Assembly)):
        document, dependencies = _compile_assembly_result(
            result,
            name,
            backend_adapter,
        )
    else:
        raise TypeError(f"{name}() must produce CAD geometry or an assembly")

    if root_is_class or root_is_component or root_is_assembly:
        _warn_missing_model_parameters(
            built.parameters,
            dependencies,
            context=name,
            pv_parameters=built.pv_parameters,
            backend_name=backend_adapter.display_name,
        )
    return document
