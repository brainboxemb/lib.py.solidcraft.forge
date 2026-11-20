# Named native subassembly group

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `components`

## Goal

Verify that group(name) creates a real nested native component rather than a Python-only label.

## Forge API

(left + right).group('PanelGroup'); group + Frame()

## Forge model

Two Panel occurrences share one definition under a named PanelGroup component, while Frame remains a direct root child.

## How Forge builds it in SolidCraft

Forge emits component.create(name='PanelGroup'), creates Panel with parent='PanelGroup', copies its occurrence, and creates Frame at the design root.

## SolidCraft result

Two 10 x 2 x 20 mm panels remain nested under PanelGroup and one 35 x 10 x 40 mm frame remains at root; native BOM inspection must preserve that hierarchy.

## Saved-design test

No saved-design mutation in this fixture; it isolates persisted native grouping and hierarchy.

## Reference notes

- **SolidCraft** — Native components form a tree; top-level BOM inspection exposes direct children while flat BOM inspection expands subassemblies.
- **PythonSCAD** — Python-side composition should lower to inspectable native CAD structure rather than remain a transient wrapper.
