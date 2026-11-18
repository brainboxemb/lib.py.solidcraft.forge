# Changelog

All notable changes to SolidCraft Python Forge (SCPF) are recorded here.

The project follows semantic versioning. Forge compatibility with the native
SolidCraft engine is qualified separately; the tested engine version is defined
by `scpf.version.TESTED_SOLIDCRAFT_VERSION`.

## [Unreleased]

### Fixed

- Primitive CSG route selection no longer depends on which primitive is on the
  left side of a join, cut or intersection. Pure primitive trees use the CSG
  compiler consistently, while ordered features can be applied after an
  already-built primitive CSG body.
- Explicitly placed native `Hole` features can therefore be added to
  Cylinder-, Sphere- and derived primitive bodies instead of only body shapes
  that happened to enter the feature compiler first (issue #297).

### Testing

- Rebuilt the SCPF unit-test layout around reusable geometry contracts.
  Primitive creation, placement, parameters, all primitive-pair CSG operations
  and compatible body × feature combinations now use generated matrices.
  Direct and derived join/cut/intersection bodies share the same feature
  contracts, and compiler primitive support is checked against the test
  registry (issue #299).

## [0.9.0] - 2026-11-17

### Added

- `Shape.circular_pattern(...)` now lowers an already-applied
  `Sketch.extrude()` feature to one native `solid.pattern.circular` history
  feature. It supports principal/fixed XYZ axes, an optional axis origin,
  dimensionless count Parameters, optional degree-angle Parameters and native
  alignment/reversal settings (issue #293).

### Fixed

- Attached explicit Sketch compilation no longer requires rectangular-body
  metadata when using `Anchor.TOP` face lookup or an explicit
  `plane=..., origin=(...)`. BOTTOM/CENTER relative attachment keeps its
  existing rectangular-base requirement (issue #295).

## [0.8.1] - 2026-11-17

### Fixed

- TOP-attached Sketch replay now compares numeric vector selector values with
  a small absolute tolerance instead of exact list equality. Planar top faces
  therefore remain selectable after native feature operations such as chamfer
  even when SolidCraft returns tiny floating-point noise in `plane_normal`
  (issue #278).

- Reusable component compilation now preserves command-level replay metadata
  such as `bind`, namespaces component-local replay variables per definition,
  and rewrites their uses in command params and binding selectors. Attached
  Sketches that rely on `model.faces` therefore keep valid replay bindings
  when the component is embedded in an assembly (issues #279/#288, PR #289).


## [0.8.0] - 2026-11-17

### Added

- `Sketch.extrude(..., profiles=[(x, y), ...], exact_regions=True)` can now
  select closed Sketch regions by fixed sketch-local points. Forge lowers the
  selection directly to SolidCraft `solid.extrude profiles` data without
  exposing native profile indices or curve ids (issue #282).

### Fixed

- Fillet and chamfer now use one edge-selection API. Both accept
  `Edges.VERTICAL`, supported two-direction Box edge selectors, named
  profile/vertex selectors and explicit XYZ picks; `chamfer()` now defaults
  to `Edges.VERTICAL` like `fillet()`. Shared unit tests cover the selector
  variants and compiler edge picks (issue #280).

### Documentation

- Added normal API Reference, Guide, Cheatsheet and search documentation for
  `Sketch.rectangular_pattern(...)` and `Sketch.mirror(...)`, including
  supported sources, parameters, returned Sketch results, Circle/Slot examples
  and current limits (issue #277).

## [0.7.0] - 2026-11-17

### Added

- Added generic associative Sketch profile handles with
  `Sketch.rectangular_pattern(...)` and `Sketch.mirror(...)`. Circle and
  native Slot profiles can now seed native SolidCraft sketch patterns/mirrors
  without exposing generated curve ids. Pattern and mirror results can feed
  later Sketch operations, while pattern counts and spacing remain editable
  native parameters (issue #272).

### Changed

- Replay documents now use version 2 only. Replay bindings may carry any
  SolidCraft-returned runtime value needed by a later command; replay-v1 files
  are intentionally no longer supported.


## [0.6.3] - 2026-11-17

### Changed

- TOP-attached `Sketch(on=..., parent=Anchor.TOP)` now uses SolidCraft's
  native face lookup and face-attached `sketch.create` instead of the
  Forge-owned XY offset/face-centre workaround from 0.6.2. Replay v2 can select
  fields from one returned list record while replay v1 files remain supported
  (issue #266).

### Added

- Added a version-pinned SolidCraft runtime command-contract snapshot generated
  from the official command registry and `engine.describe`. CI now detects
  Forge commands missing from the saved snapshot and records incomplete typed
  contracts explicitly, so a future SolidCraft upgrade such as 0.44 starts by
  creating a new preserved command-API snapshot (issue #268).

## [0.6.2] - 2026-11-17

### Fixed

- Fixed native `Slot*2D` lowering on parametrically sized attached Sketches.
  A fixed sketch-local Slot position now stays numeric when the selected
  rectangular face centre is fixed, instead of inheriting cancelling
  width/depth expressions from the parent Box (issue #266).

## [0.6.1] - 2026-11-17

### Changed

- Qualification case pages now read as model examples for users: what the
  example makes, Forge code, independent reference code, SolidCraft result,
  and technical test details. Forge and reference implementations are shown
  next to each other for direct comparison.
- The API Guide now introduces positioning and orientation directly after
  model objects and explains when to use `at()`, `on()`,
  `Shape.attach()`, `Placement` and `Occurrence.attach()`.
- Presentation-only Pages changes can reuse the latest compatible successful
  qualification evidence instead of rerunning the full native/reference
  qualification. The site records the page-build commit separately from the
  qualification-evidence commit.


### Qualification

- Added a focused repeated-parent attachment qualification for the foundational
  case where two occurrences of one Parent definition each own one rigidly
  attached child. Saved-design mutation must move both children when the shared
  parent height changes; exactly two authored attachment joints are allowed.

- Renewed the SCPF v0.6.0 qualification under the corrected audit gates. All
  24 supported cases pass Q1-Q4 and Q6; all 14 Q5-required cases pass saved-
  design mutation. Post-tag package-source changes are documentation strings
  only, so no corrective Forge runtime release is required by this audit. The
  downstream CAD repository now pins the exact v0.6.0 tag commit and passes its
  model/site and native SolidCraft gates after the documented 0.6.0 API
  migration.

### Changed

- Q6 now separates independently declared expected-shape evidence from native
  render regression. Qualification cases declare required visual views; hole
  and Slot cases add 3D through-cut feature outlines and top views, while the
  existing front/right/isometric baselines remain the regression layer. Q6
  passes only when both evidence layers pass.

### Changed

- Q1 and Q2 qualification status is now case-specific. Every supported case
  declares concrete proving unittest targets, CI runs them per case, structured
  results retain the test targets and logs, and the qualification site links to
  the exact tests on the qualified commit. Global suite success no longer
  assigns Q1/Q2 PASS to every case.

### Changed

- Q5 applicability is now explicit for every qualification case. The editable
  simple-box baseline now proves a saved dimension change, while native
  rectangular-pattern qualification mutates saved pattern `columns` and
  `pitch` parameters without rerunning Python and verifies the rebuilt cut
  count, positions, source sketch and single native pattern feature.

### Changed

- Every qualification case now publishes one shared machine-readable proof
  contract. Native Q4 baseline checks, independent references and Q6 goal
  rendering use the same geometry declarations, while SolidCraft-only history,
  relationship and mutation checks remain separate.


### Changed

- Qualification coverage now validates every evidence slug against the real
  qualification catalog, rejects Q5 claims backed by non-mutation cases, and
  checks published current Q claims against native PASS results when full
  qualification evidence is available. Stale `custom-anchor`,
  `parametric-move`, `as-built-attach` and pseudo-case references were
  corrected, and SolidCraft version text now uses the tested-version constant.


### Fixed

- Repeated parent attachments now preserve the computed child seed Placement
  before `joint.create`. Seed moves use replay-bound occurrence ids and retain
  symbolic parent-dimension, gap and offset dependencies; parent/child topology
  picks are evaluated at their current world positions. This lets a second
  floating rigid-joint graph start at the authored pose and continue following
  saved parameter changes without generated placement joints or browser-name
  identity guesses.

- Attached `Sketch(..., on=body)` through-all cuts now emit the native
  `solid.extrude` direction explicitly. TOP support faces use `negative`
  and BOTTOM support faces use `positive`, preventing an error-free no-op
  cut when SolidCraft's positive default points away from the target body.

- External reference geometry qualification now welds duplicate STL triangle
  vertices before watertightness checks, uses mesh-volume tolerances that match
  the pinned PythonSCAD/pyBOSL2 tessellation while retaining per-feature 3D
  probes, and uses build123d 0.12.0 `SlotArc` instead of the unavailable
  later `SlotCurve` API.


### Added

- Site-wide client-side documentation search indexes public API symbols,
  signatures, parameter descriptions, enum members, Guide sections and
  Cheatsheet entries. Exact symbols rank first and results link directly to
  generated Reference/Guide/Cheatsheet sections.

### Changed

- Generated API Reference pages now derive argument descriptions, units,
  constraints and examples from the public Python docstrings. The API Guide
  links to the detailed parameter reference, and site tests compare documented
  argument names with the current Python signatures so new API arguments cannot
  silently appear without documentation.


## [0.6.0] - 2026-11-16

### Added

- Native rectangular history-feature patterns through
  `Shape.rectangular_pattern(...)`, lowering directly to
  `solid.pattern.rectangular`.
- Native SolidCraft sketch Slot profiles: `SlotCenterToCenter2D`,
  `SlotOverall2D`, `SlotCenterPoint2D`, `SlotArcThreePoint2D` and
  `SlotArcCenter2D`, each lowering directly to its matching
  `sketch.slot.*` command.
- `python -m scpf check model.py` builds and compiles a model without starting
  SolidCraft so model/API/compiler failures can be found before native testing.
- build123d 0.12.0 is the fourth required, independently executed and
  rendered qualification reference for each supported case, beside
  PythonSCAD, pyBOSL2 and CadQuery (issue #196).

### Changed

- The old Hole/Cylinder `.pattern()` pre-lowering helper is renamed to
  `.repeat_linear()`. Pattern terminology is now reserved for native
  SolidCraft Pattern features.
- Native pattern counts publish direct model Parameters as dimensionless
  SolidCraft parameters instead of millimetre dimensions.
- Common model-authoring mistakes now fail with direct guidance: editable CAD
  parameters used as Python counts explain the naming convention, `Shape.group`
  points to component/assembly grouping, and material-assigned Shapes cannot be
  combined as if separate physical parts were one Shape.
- `Sketch.extrude(distance, *, sym=False)` now uses the sign of `distance`
  for positive/negative extrusion and `sym=True` for a symmetric extrusion;
  the public Extrude `Direction` enum/argument is removed.
- build123d qualification sources now prefer its native Builder API
  (`BuildPart`, `Locations`, `Mode`) and may use reusable custom part
  objects when that makes component structure clearer.

## [0.5.0] - 2026-11-16

### Added

- `Box(..., anchor=...)`, `Cylinder(..., anchor=...)` and
  `Sphere(..., anchor=...)` select deliberate world-cardinal primitive
  datums with the existing Anchor vocabulary.

### Changed

- Box, Cylinder and Sphere now use their geometric CENTER at XYZ=0 by default.
  Models that require a bottom/base/tangent datum state it explicitly through
  `anchor=`.
- Native feature-history and Boolean CSG lowering now share the same primitive
  datum calculations. Box emits native center/corner data, Cylinder derives its
  native base from axis and anchor, and Sphere derives its native center.
- `Box.taper()` measures `from_z` from the actual Box bottom face regardless
  of the constructor anchor.

## [0.4.2] - 2026-11-16

### Fixed

- Reusable component definition identity now accepts Forge's own immutable
  cardinal, profile-edge, axis and fixed bound-offset selector values. This
  restores valid build-only inputs such as
  `fillet=(BOTTOM + LEFT, BOTTOM + RIGHT)` without weakening rejection of
  arbitrary mutable/opaque Python objects.

## [0.4.1] - 2026-11-16

### Fixed

- Restore `Sketch.add(Text2D(...), offset=(u, v))` after the 0.4.0 semantic
  centering change. An omitted sketch-profile anchor now chooses the profile's
  natural default: dimension-defined profiles still use CENTER, while Text2D
  and Polygon2D keep their coordinate-defined placement. Explicit CENTER
  remains unsupported for Text2D/Polygon2D.

## [0.4.0] - 2026-11-16

### Added

- `Sketch.add(..., anchor=Anchor.CENTER)` now defines semantic centering for
  dimension-defined sketch profiles; `CENTER` is exported as the short public
  form of `Anchor.CENTER`.
- Qualification evidence now records the Forge version, SolidCraft version,
  source commit and qualification time in structured results and published
  Pages output.
- Release validation now reads `docs/design/release-blockers.txt` and refuses
  a release while an active foundational blocker is listed.

### Changed

- Rectangle2D, Circle2D and RoundedRectangle2D are centred on the Sketch origin
  by default; `offset=(u, v)` is reserved for deliberate sketch-local
  displacement. Polygon2D authored coordinates and Text2D insertion coordinates
  remain explicit.
- Native parameter expressions remain typed internally until component
  namespacing is complete. Ordinary text, material names, feature names and enum
  strings are opaque and are never rewritten as parameter expressions.
- Model-parameter warnings now use actual emitted native dependencies rather
  than treating `parameters.add` as proof of associativity. Explicit user
  `pv()` reads are diagnosed separately from Forge's internal numeric checks,
  and root models and root `@assembly` classes use the same rule.
- Normal attachments with rotated parent or child Placement are rejected before
  lowering until complete Anchor/AnchorFrame/AnchorTopology transforms are
  qualified. Ordinary rotated Placement and rotated as-built relationships
  remain supported.
- Native Q4/Q5 expectations now live only in
  `qualification/native_validation.py`; duplicate conditionally skipped native
  unittest classes were removed.

### Fixed

- Reusable component definition identity now includes inherited parent-parameter
  defaults and supported fixed non-numeric build inputs, so definitions that
  can build different geometry are not silently merged.
- Unsupported mutable/arbitrary build inputs are rejected for reusable physical
  components instead of being omitted from definition identity.
- Compiler-local parameter names now include a stable definition number, so
  different component definitions cannot collide after readable names are
  normalized to the same identifier.
- Component-local parameter namespace rewriting now changes only typed native
  expressions, preventing literal strings equal to parameter names from being
  corrupted.

### Qualification

- Qualification and documentation use
  `scpf.version.TESTED_SOLIDCRAFT_VERSION` as the single SolidCraft-version
  source instead of copied engine-version assertions.
- Qualification documentation now describes the actual three-layer test
  structure and the required PythonSCAD, pyBOSL2 and CadQuery comparison set.


## [0.3.4] - 2026-11-16

### Fixed

- Keep a physical root occurrence ungrounded when its Placement position uses
  Parameters or Expressions. SolidCraft 0.42 otherwise evaluates the initial
  `move_grounded` correctly but freezes that grounded placement when the
  parameter later changes in the saved design.
- Fixed the HUB75-style case where copied occurrences followed a changed
  opening height but the first occurrence stayed at its original position.

## [0.3.3] - 2026-11-16

### Changed

- Occurrence replay no longer depends on predicted SolidCraft browser names
  such as `Block:2`. `component.create` and `occurrence.copy` bind their
  returned occurrence ids to explicit replay variables such as `$block_2`.
- Numeric unrotated copies still put their translation directly in
  `occurrence.copy(..., translate=...)`. Symbolic Placement, rotated copies,
  and a non-identity first occurrence use a later `occurrence.move` addressed
  by the bound runtime id.
- Copied occurrences can now be used as attachment/as-built endpoints without
  guessing their SolidCraft occurrence name.
- The same replay-variable resolver is used for the live GUI connection,
  saved replay files and headless SolidCraft qualification.
- Replay executions can write a separate replay log containing the concrete
  SolidCraft ids and resolved command parameters for that run. The replay file
  itself remains deterministic and contains no temporary native ids.
- The `components`, `four-corner-l`, `eight-corner-brackets` and
  `eight-flightcase-corners` qualification cases now model ordinary
  assembly-owned `Placement` instead of artificial attachment workarounds.
- `.group(...)` changes SolidCraft hierarchy only. Forge creates group
  components with `grounded=false`; grouping a physical root occurrence no
  longer moves the grounding decision onto the empty group.
- Ordinary copies of one reusable definition may be placed under different
  groups by using SolidCraft 0.42 `occurrence.copy(parent=...)`.
- `Assembly.group()` remaps direct attachment targets to the grouped
  occurrence objects, not only to matching Forge occurrence ids.
- Rotated relationship Placement and chained attachments remain unsupported
  until their relationship semantics are qualified separately.

### Added

- Versioned `scpf-replay` JSON documents with explicit named runtime-id
  bindings and `scpf-replay-log` execution logs.
- Stable internal Forge occurrence ids are used to track physical occurrences
  across copy/group/attach transformations.

## [0.3.2] - 2026-11-15

Restore the explicit reusable-component parameter publication contract from the
original Forge component API.

### Fixed

- Reusable child-component defaults are fixed by default again instead of
  automatically polluting the top-level SolidCraft parameter list.
- Restored `component(..., include=(...))`, `include="*"` and explicit alias
  mappings for deliberate child-default publication.
- Parent Parameter/Expression inputs continue to reuse the existing parent
  dependency regardless of child publication settings.
- Strengthened parameter-scope qualification with an unincluded lower-case child
  default that must remain fixed in native SolidCraft output.

### Documentation

- Added change 0003 with the original source commit, the later conflicting
  implementation change, and the process failure that allowed current
  implementation/tests/docs to be mistaken for the normative API decision.

### Compatibility

- SCPF package version: **0.3.2**
- Qualified SolidCraft version: **0.42.0**
- Python: **3.10+**

## [0.3.1] - 2026-11-15

Correct native lowering for copied occurrences that combine translation and
rotation.

### Fixed

- A concrete copied `Placement` with rotation is now copied at native identity
  and receives its full XYZ translation and axis-angle orientation in one
  `occurrence.move`. SCPF 0.3.0 could pre-translate the copy and then rotate
  that translation, changing the declared parent-frame position.
- Added native qualification for a non-square rotated copy so this failure is
  measured in SolidCraft 0.42 rather than covered only by command-plan tests.

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

