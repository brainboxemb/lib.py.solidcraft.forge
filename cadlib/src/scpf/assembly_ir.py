"""Engine-neutral reusable-component and assembly semantic IR.

The authoring object layer in model_objects.py remains user-facing. This module
snapshots that layer into compiler semantics before any native backend chooses
component ids, occurrence ids, replay variables or joint transport.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

from .core import Anchor, AnchorFrame, AnchorTopology, parameters_in, _pv as pv
from .ir import ModelIR, normalize_shape
from .model_objects import (
    Assembly,
    AssemblyAnchor,
    Attachment,
    ModelDefinition,
    ModelInstance,
    Placement,
    _rectangular_bounds,
)


@dataclass(frozen=True)
class AnchorFrameIR:
    """One semantic local attachment frame."""

    origin: tuple[Any, Any, Any]
    z: tuple[float, float, float]
    x: tuple[float, float, float]


@dataclass(frozen=True)
class AnchorTopologyIR:
    """One semantic local topology-based attachment reference."""

    edge: tuple[Any, Any, Any]
    on: tuple[Any, Any, Any]
    corner: tuple[Any, Any, Any] | None = None
    z: tuple[float, float, float] | None = None
    x: tuple[float, float, float] | None = None


@dataclass(frozen=True)
class AnchorReferenceIR:
    """Engine-neutral occurrence attachment reference."""

    kind: str
    value: str | AnchorFrameIR | AnchorTopologyIR

    def __post_init__(self):
        if self.kind not in {"standard", "named", "frame", "topology"}:
            raise ValueError("AnchorReferenceIR kind is unsupported")
        if self.kind in {"standard", "named"}:
            if not isinstance(self.value, str) or not self.value:
                raise ValueError("named AnchorReferenceIR requires non-empty text")
        elif self.kind == "frame" and not isinstance(self.value, AnchorFrameIR):
            raise ValueError("frame AnchorReferenceIR requires AnchorFrameIR")
        elif self.kind == "topology" and not isinstance(
            self.value, AnchorTopologyIR
        ):
            raise ValueError(
                "topology AnchorReferenceIR requires AnchorTopologyIR"
            )


@dataclass(frozen=True)
class OccurrencePlacementIR:
    """Absolute semantic pose in the parent assembly coordinate frame."""

    position: tuple[Any, Any, Any]
    rotation_axis: tuple[float, float, float] | None = None
    rotation_angle: float | None = None

    def __post_init__(self):
        if (
            not isinstance(self.position, tuple)
            or len(self.position) != 3
            or any(
                isinstance(value, bool) or not isfinite(pv(value))
                for value in self.position
            )
        ):
            raise ValueError(
                "OccurrencePlacementIR position must contain finite CAD dimensions"
            )
        if (self.rotation_axis is None) != (self.rotation_angle is None):
            raise ValueError(
                "OccurrencePlacementIR rotation axis/angle must be supplied together"
            )
        if self.rotation_axis is not None:
            if (
                len(self.rotation_axis) != 3
                or any(not isfinite(value) for value in self.rotation_axis)
                or sum(value * value for value in self.rotation_axis) <= 0
                or not isfinite(self.rotation_angle)
            ):
                raise ValueError(
                    "OccurrencePlacementIR rotation must be finite and non-zero-axis"
                )


@dataclass(frozen=True)
class ComponentDefinitionIR:
    """Reusable physical component definition independent of native identity."""

    id: str
    class_name: str
    model: ModelIR
    parameters: tuple[tuple[str, float], ...]
    fixed_inputs: tuple[tuple[str, object], ...]
    external_parameters: tuple[tuple[str, float], ...]
    input_bindings: tuple[tuple[str, str], ...]
    anchors: tuple[tuple[str, AnchorFrameIR | AnchorTopologyIR], ...]
    exported_features: tuple[str, ...]
    bounds: tuple[
        tuple[Any, Any],
        tuple[Any, Any],
        tuple[Any, Any],
    ] | None = None

    def __post_init__(self):
        if not self.id.startswith("definition_"):
            raise ValueError("ComponentDefinitionIR id must be semantic")
        if not isinstance(self.model, ModelIR):
            raise ValueError("ComponentDefinitionIR model must be ModelIR")
        if len(set(self.exported_features)) != len(self.exported_features):
            raise ValueError("component exported feature names must be unique")


@dataclass(frozen=True)
class OccurrenceIR:
    """One semantic occurrence of a reusable definition."""

    id: str
    definition: str
    placement: OccurrencePlacementIR
    name: str | None = None
    group: str | None = None
    flattened_parameters: tuple[str, ...] = ()

    def __post_init__(self):
        if not self.id.startswith("occurrence_"):
            raise ValueError("OccurrenceIR id must be semantic")
        if not self.definition.startswith("definition_"):
            raise ValueError("OccurrenceIR definition must be semantic id")
        if not isinstance(self.placement, OccurrencePlacementIR):
            raise ValueError("OccurrenceIR placement must be OccurrencePlacementIR")


@dataclass(frozen=True)
class RelationshipIR:
    """One semantic relationship between two occurrences."""

    child: str
    parent: str
    kind: str
    parent_anchor: AnchorReferenceIR | None
    child_anchor: AnchorReferenceIR | None
    offset: tuple[Any, Any] = (0, 0)
    gap: Any = 0
    angle: float | None = None
    value: float | None = None
    limits: tuple[float, float] | None = None
    flip: bool = False
    name: str | None = None
    as_built: bool = False

    def __post_init__(self):
        if not self.child.startswith("occurrence_") or not self.parent.startswith(
            "occurrence_"
        ):
            raise ValueError("RelationshipIR occurrence references must be semantic")
        if self.kind not in {"rigid", "planar", "revolute"}:
            raise ValueError("RelationshipIR kind is unsupported")
        if self.as_built:
            if (
                self.kind != "rigid"
                or self.parent_anchor is not None
                or self.child_anchor is not None
            ):
                raise ValueError(
                    "as-built RelationshipIR is rigid and has no anchor references"
                )
        elif self.parent_anchor is None or self.child_anchor is None:
            raise ValueError("normal RelationshipIR requires both anchor references")
        if self.kind == "revolute":
            if self.value is None or not isfinite(self.value):
                raise ValueError("revolute RelationshipIR requires finite value")
            if self.limits is not None:
                low, high = self.limits
                if not all(isfinite(v) for v in (low, high)) or low > high:
                    raise ValueError("revolute RelationshipIR limits are invalid")
        elif self.value is not None or self.limits is not None or self.flip:
            raise ValueError(
                "RelationshipIR value/limits/flip require revolute kind"
            )


@dataclass(frozen=True)
class AssemblyAnchorIR:
    """Named assembly-owned datum pointing at one semantic occurrence."""

    name: str
    target: str
    reference: AnchorReferenceIR
    offset: tuple[Any, Any] = (0, 0)


@dataclass(frozen=True)
class AssemblyIR:
    """Core reusable-component/occurrence/relationship compiler contract."""

    definitions: tuple[ComponentDefinitionIR, ...]
    occurrences: tuple[OccurrenceIR, ...]
    relationships: tuple[RelationshipIR, ...] = ()
    anchors: tuple[AssemblyAnchorIR, ...] = ()

    def __post_init__(self):
        definition_ids = {item.id for item in self.definitions}
        occurrence_ids = {item.id for item in self.occurrences}
        if len(definition_ids) != len(self.definitions):
            raise ValueError("AssemblyIR definition ids must be unique")
        if len(occurrence_ids) != len(self.occurrences):
            raise ValueError("AssemblyIR occurrence ids must be unique")
        if not self.occurrences:
            raise ValueError("AssemblyIR requires at least one occurrence")
        if any(item.definition not in definition_ids for item in self.occurrences):
            raise ValueError("AssemblyIR occurrence references missing definition")
        if any(
            item.child not in occurrence_ids or item.parent not in occurrence_ids
            for item in self.relationships
        ):
            raise ValueError("AssemblyIR relationship references missing occurrence")
        if any(item.target not in occurrence_ids for item in self.anchors):
            raise ValueError("AssemblyIR anchor references missing occurrence")


def _frame_ir(value: AnchorFrame) -> AnchorFrameIR:
    return AnchorFrameIR(
        origin=tuple(value.origin),
        z=tuple(float(v) for v in value.z),
        x=tuple(float(v) for v in value.x),
    )


def _topology_ir(value: AnchorTopology) -> AnchorTopologyIR:
    return AnchorTopologyIR(
        edge=tuple(value.edge),
        on=tuple(value.on),
        corner=None if value.corner is None else tuple(value.corner),
        z=None if value.z is None else tuple(float(v) for v in value.z),
        x=None if value.x is None else tuple(float(v) for v in value.x),
    )


def _anchor_reference_ir(value) -> AnchorReferenceIR:
    if isinstance(value, Anchor):
        return AnchorReferenceIR("standard", value.value)
    if isinstance(value, str):
        return AnchorReferenceIR("named", value)
    if isinstance(value, AnchorFrame):
        return AnchorReferenceIR("frame", _frame_ir(value))
    if isinstance(value, AnchorTopology):
        return AnchorReferenceIR("topology", _topology_ir(value))
    raise TypeError("assembly anchor reference is outside semantic IR")


def _placement_ir(value: Placement) -> OccurrencePlacementIR:
    if value.rotation is None:
        return OccurrencePlacementIR(tuple(value.position))
    axis, angle = value.rotation
    return OccurrencePlacementIR(
        tuple(value.position),
        rotation_axis=tuple(float(v) for v in axis),
        rotation_angle=float(angle),
    )


def _definition_bounds(instance: ModelInstance):
    try:
        return tuple(tuple(pair) for pair in _rectangular_bounds(instance))
    except ValueError:
        return None


def normalize_assembly(value: ModelInstance | Assembly) -> AssemblyIR:
    """Normalize one authored reusable-component assembly into semantic IR."""
    assembly = Assembly((value,)) if isinstance(value, ModelInstance) else value
    if not isinstance(assembly, Assembly):
        raise TypeError("assembly normalization requires ModelInstance or Assembly")
    if not assembly.instances:
        raise ValueError("assembly normalization requires at least one occurrence")

    definition_ids = {}
    definitions = []
    occurrence_ids = {
        instance.occurrence_id: f"occurrence_{index}"
        for index, instance in enumerate(assembly.instances, start=1)
    }

    for instance in assembly.instances:
        key = instance.definition.key
        if key in definition_ids:
            continue
        definition_id = f"definition_{len(definition_ids) + 1}"
        definition_ids[key] = definition_id
        definition = instance.definition
        definitions.append(
            ComponentDefinitionIR(
                id=definition_id,
                class_name=definition.class_name,
                model=normalize_shape(definition.shape),
                parameters=definition.parameters,
                fixed_inputs=definition.fixed_inputs,
                external_parameters=definition.external_parameters,
                input_bindings=definition.input_bindings,
                anchors=tuple(
                    (
                        name,
                        _frame_ir(anchor)
                        if isinstance(anchor, AnchorFrame)
                        else _topology_ir(anchor),
                    )
                    for name, anchor in definition.anchors
                ),
                exported_features=tuple(name for name, _ in definition.features),
                bounds=_definition_bounds(instance),
            )
        )

    occurrences = tuple(
        OccurrenceIR(
            id=occurrence_ids[instance.occurrence_id],
            definition=definition_ids[instance.definition.key],
            placement=_placement_ir(instance.placement),
            name=instance.name,
            group=instance.group_name,
            flattened_parameters=instance.flattened_parameters,
        )
        for instance in assembly.instances
    )

    relationships = []
    for instance in assembly.instances:
        attachment = instance.attachment
        if attachment is None:
            continue
        child = occurrence_ids[instance.occurrence_id]
        try:
            parent = occurrence_ids[attachment.target.occurrence_id]
        except KeyError as exc:
            raise ValueError(
                "attachment target must belong to normalized Assembly"
            ) from exc
        if attachment.as_built:
            relationships.append(
                RelationshipIR(
                    child=child,
                    parent=parent,
                    kind="rigid",
                    parent_anchor=None,
                    child_anchor=None,
                    as_built=True,
                )
            )
            continue

        has_planar_offset = (
            any(pv(value) != 0 for value in attachment.offset)
            or bool(parameters_in(*attachment.offset))
        )
        kind = (
            attachment.kind
            if attachment.kind is not None
            else "planar" if has_planar_offset else "rigid"
        )
        relationships.append(
            RelationshipIR(
                child=child,
                parent=parent,
                kind=kind,
                parent_anchor=_anchor_reference_ir(attachment.parent),
                child_anchor=_anchor_reference_ir(attachment.child),
                offset=tuple(attachment.offset),
                gap=attachment.gap,
                angle=attachment.angle,
                value=attachment.value,
                limits=attachment.limits,
                flip=attachment.flip,
                name=attachment.name,
            )
        )

    anchors = tuple(
        AssemblyAnchorIR(
            name=name,
            target=occurrence_ids[anchor.target.occurrence_id],
            reference=_anchor_reference_ir(anchor.reference),
            offset=tuple(anchor.offset),
        )
        for name, anchor in assembly.anchors
    )

    return AssemblyIR(
        definitions=tuple(definitions),
        occurrences=occurrences,
        relationships=tuple(relationships),
        anchors=anchors,
    )


__all__ = [
    "AnchorFrameIR",
    "AnchorTopologyIR",
    "AnchorReferenceIR",
    "OccurrencePlacementIR",
    "ComponentDefinitionIR",
    "OccurrenceIR",
    "RelationshipIR",
    "AssemblyAnchorIR",
    "AssemblyIR",
    "normalize_assembly",
]
