# Imported @assembly subassembly

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `components`

## Goal

Verify the public @assembly decorator on an imported reusable subassembly, independently of anchor or feature complexity.

## Forge API

@component class Post; @assembly class PostPair; root model imports and returns PostPair()

## Forge model

One reusable Post component definition plus two occurrences produced inside an imported @assembly factory. The root model treats the returned subassembly as ordinary assembly geometry.

## How Forge builds it in SolidCraft

The Python-only @assembly wrapper disappears during lowering: Forge emits one Post component definition and one copied occurrence placed directly by occurrence.copy; no occurrence.move is needed.

## SolidCraft result

Two identical 10 x 10 x 20 mm posts remain at X=-15 and X=+15 while the imported @assembly result builds from a replay-safe component/copy command plan.

## Saved-design test

No saved-design mutation in this fixture; it isolates imported @assembly construction and native lowering.

## Reference notes

- **PythonSCAD** — The public Python object/decorator layer should remain natural while still producing reusable native CAD structure.
- **SolidCraft** — The resulting assembly must lower to native component/occurrence commands and build without special runtime handling.
