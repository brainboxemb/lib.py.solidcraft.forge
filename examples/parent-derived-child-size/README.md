# Child dimensions derived from parent parameters

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `parameters`

**Saved-design required:** `true`

## Goal

Isolate one dependency contract: a reusable child receives width and depth expressions derived from parent parameters, and those child dimensions remain editable/associative in the saved SolidCraft design.

## Forge API

DerivedChild(width=self.base_width / 2, depth=self.base_depth / 2)

## Forge model

One ParentBlock and one DerivedChild. Only base_width and base_depth are published as document parameters; the child carries expressions that reference those existing parent parameters instead of receiving independent duplicated values.

## How Forge builds it in SolidCraft

The parent and child sketch dimensions preserve base_width/base_depth expressions. Forge must not flatten base_width / 2 or base_depth / 2 to numeric constants when compiling the child component.

## SolidCraft result

At 120x80 mm parent size, the child measures 60x40 mm. Its fixed height and fixed body layout are deliberately unrelated to this qualification.

## Saved-design test

Change base_width/base_depth from 120x80 to 160x120 mm in the saved .sc design; without rerunning Python the child must rebuild from 60x40 to 80x60 mm.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `true`

The geometry is two rectangular bodies whose declared sizes and positions are sufficient; the parent-to-child expression is proved by native mutation.

## Reference notes

- **SolidCraft** — Native parameters and expressions must preserve the parent-to-child dimensional dependency after the Python compiler has finished.
- **PythonSCAD** — The Python model expresses the dependency with ordinary arithmetic rather than a special application-specific sizing API.
