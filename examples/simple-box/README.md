# Parameterized Box

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy group:** `fundamentals`

**Saved-design required:** `true`

## Goal

Establish the smallest model/parameter contract: three public Python fields create one editable native box.

## Forge API

class fields -> Parameter; Box(length, width, height); build()

## Forge model

One root Shape with symbolic length, width and height; no occurrence or assembly layer.

## How Forge builds it in SolidCraft

parameters.add for the public dimensions, followed directly by native solid.box; no sketch is synthesized.

## SolidCraft result

One rectangular solid with the requested 40 x 30 x 10 mm dimensions and an error-free timeline.

## Saved-design test

Required because this case explicitly claims an editable native Box. Change length from 40 to 50 mm in the saved .sc design; the Box must rebuild to 50 x 30 x 10 mm without rerunning Python.

## Geometry evidence

> Geometry-rationale provenance: copied verbatim from `qualification/geometry_contracts.py` at commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`.

**Bounds sufficient:** `true`

This case is one rectangular solid. Its body size fully describes the visible geometry. The saved SolidCraft model is checked separately to confirm that the dimensions remain editable parameters.

## Reference notes

- **OpenSCAD** — cube([40,30,10]) is the constructive-geometry baseline; Forge differs by preserving editable SolidCraft history.
