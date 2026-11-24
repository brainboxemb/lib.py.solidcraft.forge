# Explicit component parameters and shared dependencies

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Legacy group:** `parameters`

**Saved-design required:** `true`

## Goal

Verify that reusable component defaults stay fixed unless explicitly included, while selected defaults become native parameters and parent Parameters/Expressions are reused rather than duplicated in the child.

## Forge API

@component(include=('width',)) class Panel; Panel(width=self.shared_width); Panel(width=half(self.shared_width))

## Forge model

Only explicitly included width defaults become component-local Parameters. The lower-case depth default remains fixed. Inherited Parameter/Expression inputs become external bindings to the existing parent dependency.

## How Forge builds it in SolidCraft

Explicitly included component parameters are namespaced with the internal definition number plus readable component name (for example d1_Panel_width); unincluded child defaults stay fixed; inherited names such as shared_width remain unprefixed and are emitted once even when several child definitions use them.

## SolidCraft result

The saved SolidCraft design exposes d1_Panel_width, d2_Panel_2_width and shared_width; changing shared_width updates both directly-bound children and the derived half-width child without rerunning Python.

## Saved-design test

Change shared_width from 80 to 100 mm in the saved native design; widths must change from [40,40,60,80,80] to [40,50,60,100,100].

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `true`

The body sizes and positions describe the visible result. The saved SolidCraft model is checked separately to confirm that shared parameters are reused instead of duplicated.

## Reference notes

- **PythonSCAD** — Reference geometry remains ordinary Python; Forge adds explicit native parameter publication because that is persistence/editability intent rather than geometry syntax.
- **SolidCraft** — Native parameters and expressions are the source of truth for saved-design editability and rebuild behaviour.
