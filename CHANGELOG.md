# Changelog

All notable changes to SolidCraft Python Forge (SCPF) are recorded here.

The project follows semantic versioning. Forge compatibility with the native
SolidCraft engine is qualified separately; the tested engine version is defined
by `scpf.version.TESTED_SOLIDCRAFT_VERSION`.

## [Unreleased]

### Added

- Nothing yet.

## [0.3.1] - 2026-11-15

Rotated-copy Placement lowering correction.

### Fixed

- Keep numeric translation and rotation from one copied `Placement` together
  in a single native `occurrence.move`. Forge no longer applies translation
  through `occurrence.copy` and then rotates that already-translated occurrence
  around the native origin.
- Added native qualification for a copied occurrence with both translation and
  rotation so downstream panel-style layouts catch this transform-order bug.

### Compatibility

- SCPF package version: **0.3.1**
- Qualified SolidCraft version: **0.42.0**
- Python: **3.10+**

## [0.3.0] - 2026-11-15

Replay-first placement cleanup and foundational API correction.

### Added

- Added public `Placement(x, y, z, rotation=...)` occurrence metadata for
  absolute, optionally symbolic pose at component construction/copy time.
- Concrete placement of additional occurrences lowers directly through
  `occurrence.copy(..., translate=...)` where SolidCraft supports it.
- Added per-case comparison-engine selection and a pinned CadQuery 2.8.0
  assembly/location reference for parametric occurrence positioning.

### Changed

- Component constructors accept reserved `placement=Placement(...)` metadata;
  it is consumed by Forge and never becomes a component model parameter.
- `copy(placement=..., name=...)` creates a new occurrence with the declared
  Placement while retaining the shared component definition.
- Runtime result-handle execution is deferred to roadmap issue #168 instead of
  becoming part of the normal replay compiler.

### Removed

- Removed occurrence `.move()`, `.rotate()` and `.at()` placement actions,
  plus the redundant public `Position` wrapper. Initial occurrence pose is
  constructor/copy metadata; backend `occurrence.move` remains a valid native
  lowering fallback where SolidCraft 0.42 cannot encode placement at creation.
- Removed the phased runtime-result-binding work from this release line; normal
  Forge output remains replay-first.

### Compatibility

- SCPF package version: **0.3.0**
- Qualified SolidCraft version: **0.42.0**
- Python: **3.10+**

## [0.2.0] - 2026-11-15 — WITHDRAWN

This release was published before Forge's foundational create/place/copy/attach
model, occurrence identity strategy and replay contract were fully designed and
qualified. It is retained in Git history but must not be used as a downstream
CAD baseline.

Breaking API cleanup plus native occurrence-placement correction.

### Fixed

- Lower symbolic occurrence `.move()` directly to SolidCraft 0.42.0
  `occurrence.move` expressions instead of generating hidden planar placement
  joints. Saved designs keep the placement expression associative when its
  parameter changes.

### Removed

- Removed the experimental public `History` enum and `behavior()` scope.
  Forge now uses native feature lowering by default; authored sketch history is
  expressed explicitly with `Sketch`.

### Compatibility

- SCPF package version: **0.2.0**
- Qualified SolidCraft version: **0.42.0**
- Python: **3.10+**

## [0.1.1] - 2026-11-15

Release-process patch. No public Forge modelling API changes from 0.1.0.

### Changed

- Replaced the one-off v0.1.0 publisher with a reusable release workflow.
- Releases are created only after the full main-branch SCPF qualification passes.
- Release metadata is validated against the single package version in
  `scpf/pyproject.toml`, the dated changelog section and the exact main commit.
- Release tags are annotated and downstream projects can pin the exact tagged
  commit while still recording the semantic release version.

## [0.1.0] - 2026-11-15

Initial qualified Forge release.

### Added

- Readable Python modelling API for native SolidCraft geometry, sketches,
  features, parameters, components and assemblies.
- Explicit 2D/3D constructors including `Box`, `Cylinder`, `Sphere`,
  `Rectangle2D`, `RoundedRectangle2D`, `Circle2D` and `Polygon2D`.
- Reusable `@component` and `@assembly` model definitions with occurrences,
  copies, native placement, grouping and associative attachment relationships.
- Standard `Anchor` references plus `AnchorFrame` and `AnchorTopology`
  for custom and topology-backed assembly datums.
- Native feature support including holes, fillets, chamfers, shells and
  explicit sketch/extrude workflows.
- SolidCraft 0.42.0 qualification with Q1-Q6 API, command, native,
  parametric-mutation and visual verification.
- Executable PythonSCAD and pyBOSL2 comparison implementations for every
  qualification case, with independent STL exports and renders.
- Generated API Guide, persistent-navigation API Reference, Cheatsheet and
  compact machine-readable agent API index.
- Version-pinned local SolidCraft and comparison-library reference material for
  low-token agent lookup.
- Affected-case qualification runner for faster local and CI iteration.

### Compatibility

- SCPF package version: **0.1.0**
- Qualified SolidCraft version: **0.42.0**
- Python: **3.10+**

