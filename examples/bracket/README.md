# Bracket — SCPF live CAD example

This small L bracket demonstrates a parameterized XZ sketch, extrusion,
fillet and two mounting holes, using SolidCraft's native CAD command API.

- [Python design](scpf/model.py): reusable `Bracket` dataclass, `build()`, no explicit `return` or `show()`.
- [SCPF command fixture](scpf/solidcraft.json): standalone command sequence.
- [Original SolidCraft commands](source/bracket.json): supplied reference; works with parameters already declared.
- [SCPF runner instructions](../../scpf/README.md#run-and-inspect-the-bracket): PowerShell examples for `--out`, `--connect`, and the CLI.
- [Results website](../../site/): generated automatically by GitHub Actions.

## Why the two JSON files start differently

The original reference starts with `parameters.change`: it expects
`width` and `thickness` to exist in the current document. SCPF uses
`parameters.add` to create them in an empty design. Beyond those first
two commands, the geometry operations must agree.

The XZ sketch's positive vertical coordinate maps to **negative world Z**.
The valid fillet point is `[40, -30, -6]` and the through-hole cut also
travels along negative Z.

## Run on Windows

From the repository root:

```powershell
$env:PYTHONPATH = "scpf"
python -m scpf examples/bracket/scpf/model.py --out output/examples/bracket/scpf/solidcraft.json
code output/examples/bracket/scpf/solidcraft.json
```

To replay the **original command JSON without translating it**:

```powershell
python -m scpf replay examples/bracket/source/bracket.json
```

The original file starts with `parameters.change`, so `width` and
`thickness` must already exist in the current design. In a new empty
design, replay the standalone SCPF file instead:

```powershell
python -m scpf replay examples/bracket/scpf/solidcraft.json
```

To send commands to an **already open SolidCraft** instance, first open a
new empty design and enable external Assistant control:

```powershell
python -m scpf examples/bracket/scpf/model.py --connect
```

A live batch does not write a file. The existing design may be modified.
If the build fails, the control request asks SolidCraft to roll back.

For native CLI evaluation without a GUI connection:

```powershell
solidcraft-cli run output/examples/bracket/scpf/solidcraft.json --param-check strict --save output/bracket.sc
```

Open `output/bracket.sc` in SolidCraft. Native execution of this particular
Bracket model must be verified independently from Python command-generation
tests.

---

## Preserved verification documentation

> Documentation provenance: the engineering text below is copied verbatim from the last canonical `qualification/cases.py` source before its removal, commit `be40b09e7454a90e87d83768a9e7453c52ba5d76`. Machine verification lives in [`verification/verify.py`](verification/verify.py).

**Legacy title:** `Minimal L-profile`

**Legacy group:** `fundamentals`

### Goal

Provide a deliberately simple reusable L-shaped reference component for later attachment/orientation qualification.

### Forge API

with Sketch(plane='XZ'): Polygon2D(..., plane='XZ'); sketch.extrude(width, direction=Direction.SYMMETRIC)

### Forge model

One symbolic L profile extruded symmetrically through its width; no holes, fillets, anchors or secondary features.

### How Forge builds it in SolidCraft

Native XZ sketch/polygon plus symmetric extrusion. No assembly commands are present yet.

### SolidCraft result

A clean 40 mm L profile with 12 mm arms and 24 mm symmetric extrusion width.

### Saved-design test

Not yet an attachment mutation case. This component is intentionally the geometry baseline for upcoming multi-orientation anchor tests.

### Reference notes

- **OpenSCAD** — Equivalent baseline is a 2D L polygon followed by linear_extrude(center=true).
- **BOSL2** — Later attachment cases can reuse this simple shape while testing anchor/orient semantics independently of bracket feature complexity.

