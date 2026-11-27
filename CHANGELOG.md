# Changelog

All notable changes to SolidCraft Python Forge (SCPF) are recorded here.

The project follows semantic versioning. Forge compatibility with the native
SolidCraft engine is qualified separately; the tested engine version is defined
by `scpf.version.TESTED_SOLIDCRAFT_VERSION`.

## [Unreleased]

## [0.25.0] - 2026-11-27

### Changed

- Replace wrapper-style configuration authoring with final-model
  `model.configure(active=..., columns=..., rows=...)`.
- Accept existing `Parameter` and authored Shape/component-feature handles
  directly as configuration targets.

### Removed

- Remove the public `Configure(...)`, `Param(...)`, `Suppress(...)`,
  `ConfigRule(...)`, `Always()`, `DriveParameter(...)` and
  `Configure(..., rules=...)` surface.
- Remove the obsolete rule-based `configuration-installed-state`
  qualification model; direct feature suppression is the active Installed
  configuration pattern.


## [0.24.0] - 2026-11-27

### Added

- Add explicit reusable-component feature exports through
  `Shape.export_feature(name)` and definition-level
  `Occurrence.feature(name)` references.
- Allow a parent/root `Configure(...)` table to use
  `Suppress(child.feature(name))` for one authored feature inside a reusable
  child definition without exposing SolidCraft or replay feature ids.

### Qualification

- Add the Forge-owned `configuration-child-feature` case proving two
  separately constructed child occurrences share one parent-driven parameter,
  Small/Medium suppress the exported child cut and Large enables the same real
  native history after save/reopen without rerunning Forge Python.
- Add approved front/right/isometric visual regression baselines and
  expected-shape evidence for the seven visible-geometry owners identified by
  the verification audit while retaining their existing native/history/topology
  checks.

## [0.23.0] - 2026-11-26

### Added

- Add typed native Configuration Rules to final-design configuration authoring
  through `Configure(..., rules=...)`, `ConfigRule(...)`, `Always()` and
  `DriveParameter(...)`.
- Allow one independently enabled native rule to drive an existing
  `Param(...)` target from a Forge Parameter/Expression without requiring
  consumer-authored SolidCraft rule JSON or native ids.

### Changed

- Keep physical Installed state orthogonal to ordinary Small / Medium / Large
  configuration rows: disabling the rule restores the active row's stored
  Free/base expression instead of expanding size and state into Cartesian rows.
- Qualify Configuration Rules through saved-design switching after reopen,
  including reusable child occurrences sharing one parent-owned parameter and
  independent persistence of row activation and rule enabled state.
- Retain the pinned SolidCraft 0.49 typed `config.rule` contract as Forge-owned
  evidence before exposing the new public authoring surface.

## [0.22.1] - 2026-11-26

### Qualification

- Qualify parent `Configure(...)` tables driving a deliberately published
  parameter from a reusable child component through ordinary `Param(...)`
  composition.
- Prove multiple child occurrences share that one native parameter and that
  switching configuration rows in the saved SolidCraft design recomputes child
  geometry without rerunning Forge Python.
- This patch adds qualification evidence only; it does not change the public
  Forge API or runtime behavior from v0.22.0.

## [0.22.0] - 2026-11-26

### Added

- Add multiple closed profiles to standalone `Sketch.extrude(...)`, preserving
  one native Sketch and one native ExtrudeFeature for nested-loop regions such
  as annular Ø10/Ø8 hollow-tube profiles while keeping single-profile
  authoring source-compatible.
- Add native two-distance chamfer authoring through
  `Shape.chamfer(distance, distance2=..., flip=..., edges=...)`, reusing the
  existing semantic edge-selection vocabulary and preserving the exact
  equal-distance command shape when asymmetric options are omitted.

### Changed

- Apply the completed verification-evidence contract to newly added visible
  geometry: both multi-profile extrusion and asymmetric chamfer retain native
  saved-design checks, mesh geometry checks and approved SolidCraft visual
  baselines.
- Grow the normal Forge catalogue from 57 to 59 physical model owners with the
  focused multi-profile extrusion and asymmetric-chamfer qualification owners.


## [0.21.0] - 2026-11-26

### Added

- Add public symbolic CAD math through `scpf.cadmath.min()`,
  `max()`, `sqrt()`, `abs()`, `round()`, `floor()` and `atan()`,
  preserving parameter dependencies in SolidCraft expressions for
  configuration-driven geometry.
- Add typed `AxisLine(...)` support for shifted/custom
  `Sketch.revolve(...)` axes, including parameter-driven origins, while
  keeping the resulting revolve one feature that can be used by
  `Suppress(feature)`.
- Add `title_block_style="compact"` to component and Assembly drawing
  authoring, selecting SolidCraft's compact 49 mm title block while preserving
  the existing built-in title block as the default.

### Changed

- Qualify sheet perforation from SolidCraft flat-pattern/DXF manufacturing
  output with deterministic review evidence instead of fabricating perforations
  in display geometry.
- Qualify compact technical-drawing presentation with replayed 49 mm title-block
  geometry and a separate approved sheet-image baseline while retaining the
  existing full Sample Plate drawing qualification.
- Clarify configuration-position verification intent and place the
  owner-authored engineering explanation before generated command/evidence
  details on verification pages.

### Fixed

- Replace stale public `repeat_linear(...)` documentation with the released
  `rectangular_pattern(...)` feature-history pattern contract.

## [0.20.0] - 2026-11-26

### Added

- Add public native SolidCraft configuration-table authoring through
  `Configure(design, active=..., columns=..., rows=...)`, with
  `Param(...)` parameter columns and `Suppress(feature)` feature-suppression
  columns.
- Allow configuration intent around a final Shape, component occurrence or
  Assembly, including associative occurrence Placement driven by ordinary model
  parameters.

### Changed

- Keep generated configuration tables editable in saved SolidCraft `.sc`
  designs, bind suppression to replay-returned native feature identity and bind
  deterministic name-stable Forge row references to SolidCraft-owned native row
  ids.
- Qualify configuration behavior with Forge-owned cases for dimensional and
  suppression variants, complete Assembly Front/Below/Service positions, and
  flexible-fit `Free` / `Installed` physical states.
- Define `Free` as the uninstalled manufacturing/print state and `Installed`
  as the mounted working state while keeping render/display presentation
  separate from physical configuration state.

## [0.19.0] - 2026-11-25

### Added

- Add consumer-grade native drawing authoring with explicit standard-view
  placement and scale, per-view visual style, linear/face/radial dimensions
  and callouts, notes, drawing properties, title-block overrides and revision
  rows.
- Add bounded native revolute relationships through
  `Occurrence.attach(..., kind="revolute", value=..., limits=..., name=...)`,
  reusing the existing Anchor/AnchorFrame attachment model while preserving
  native joint identity and driveable saved-design behavior.
- Add `Shape.with_appearance("#RRGGBB")` for display-only body color without
  changing physical material, density or BOM semantics.

### Changed

- Qualify native A4/A3 drawing sheets in landscape orientation and publish each
  drawing as vector PDF, native static PNG and retained final
  `drawing.inspect` evidence. Pages uses the static preview and opens or
  downloads the PDF only on explicit user action.
- Qualify shaded isometric drawing presentation independently from orthographic
  line views through per-view visual style.

### Fixed

- Classify metadata-only stable `workflow_dispatch` release commits the same
  as the existing release-only push path: select release + library and zero
  model owners, while product/merge-commit deltas still fail closed to full
  qualification.
- Preserve the previously accepted full stable `build/main` product baseline
  when publishing a release-only metadata commit.

## [0.18.0] - 2026-11-25

### Added

- Add `Edges.from_faces(...)` for selecting the complete native boundary of
  one or more named cardinal faces without caller-supplied XYZ edge picks.

### Changed

- Use one world-cardinal `Faces` vocabulary across feature placement, shelling
  and face-boundary edge selection: TOP/BOTTOM = +/-Z, LEFT/RIGHT = -/+X and
  FRONT/BACK = -/+Y.
- Resolve named faces and their boundary edges through native SolidCraft
  `model.faces` / `model.edges` replay queries, then pass SolidCraft-returned
  `{body, index}` edge references to fillet/chamfer instead of predicting
  topology ids.
- Preserve existing edge selectors source-compatibly while qualifying native
  one-face Box and two-face XZ extrusion perimeter chamfers; XZ broad extrusion
  faces are FRONT/BACK because extrusion is along world Y.

## [0.17.0] - 2026-11-25

### Added

- Add native technical drawings for component occurrences through
  `Occurrence.with_drawing(...)` and `Assembly.with_drawing(...)`, with
  SolidCraft-owned front, top, right and isometric standard views.
- Publish every declared native drawing as a vector PDF build artifact below
  `drawings/`, using SolidCraft `drawing.export` rather than screenshots or
  a Forge-side PDF renderer.

### Changed

- Default component drawings to SolidCraft's ISO A4 part template while
  retaining explicit `template="iso-a3-part"` support for larger or more
  complex drawings.
- Restore open drawing editor context across headless replay phase boundaries,
  matching the existing active-component and active-Sketch transport behavior.
- Document the drawing ownership boundary, A4/A3 workflow and public
  `with_drawing` API in the Guide and generated API Reference.

## [0.16.0] - 2026-11-25

### Added

- Add `Sketch.line(...)` as a reusable authored native straight-line Sketch
  reference and allow `Shape.fold(line=...)` to bind that Sketch curve, so
  parameter-driven fold lines remain associative through saved-design edits.
- Restore canonical SolidCraft command-registry capture and exact immutable
  runtime verification under `modules/solidcraft-reference`.

### Changed

- Publish Forge from the canonical migrated repository while preserving the
  public `scpf` distribution/import contract and the accepted physical model
  owner architecture.
- Adopt immutable `docker.cad.solidcraft v0.3.6` and qualify Forge against
  SolidCraft **0.49.0**.
- Capture the canonical SolidCraft 0.49.0 registry from
  `cad-solidcraft:v0.3.6`: 886 commands, 20 command IDs added versus 0.48.1
  and none removed.
- Preserve the historical pre-migration repository as archived
  `brainboxemb/lib.py.solidcraft.forge.OLD`; the migrated repository now owns
  the canonical `brainboxemb/lib.py.solidcraft.forge` identity.


## [0.15.0] - 2026-11-24

### Fixed

- Restore active component context across headless replay phases before
  continuing component-local native features; this prevents joined feature/tool
  geometry from remaining visible in root/world space after save/reopen (#753).

### Changed

- Generalized native feature-pattern sources so rectangular/circular patterns
  accept already-applied Hole and native primitive Shapes as well as named
  Sketch extrusions, while keeping SolidCraft history names internal (#347).

### Added

- Added native exploded assembly views with automatic scale or explicit
  occurrence translations plus explicit exploded/assembled presentation
  selection, without mutating normal occurrence placements (#751).
- Added native whole-sheet `Shape.perforate(...)` fields with parameterized
  diameter, pitch and optional margin plus staggered/square layout. Forge keeps
  perforations as SolidCraft flat-pattern/DXF/measurement semantics instead of
  approximating them with repeated B-rep holes (#779).

## [0.14.0] - 2026-11-24

### Changed

- Adopt immutable `docker.cad.solidcraft v0.3.5` and qualify Forge against
  SolidCraft **0.48.1**. The retained #753 component-local joined-Cylinder
  occurrence regression is green on that runtime; Forge now checks the exact
  0.48.1 command registry and no longer consumes runtime v0.3.4 / SolidCraft
  0.45.0 for current development (#823).
- Canonical `model.yml` metadata now includes explicit `purpose`
  classification for Example and Verification membership, allowing the curated
  teaching catalog and the broader capability catalog to evolve independently
  without moving model source directories (#785).

### Documentation

- Added a first-class Sheet metal API Guide chapter and complete generated
  Reference/Cheatsheet coverage for `Sketch.sheet_metal()`,
  `Shape.fold()`, `Shape.flange()`, `Shape.contour_flange()`,
  `Shape.hem()` and `Shape.path_flange()` (#786).


## [0.13.2] - 2026-11-23

### Hotfix context

v0.13.2 is the consumer hotfix for the symbolic placed-primitive regression
found while the product-CAD repository adopted v0.13.1.

v0.13.1 remains a valid immutable release, but an existing parametrically
placed `Cylinder` could fail during Forge command generation when its placement
coordinate had already become a native expression while its height was still a
Forge `Expression`. The detailed `hub75-panel` model exposed this as:

```text
TypeError: can only concatenate str (not "Expression") to str
```

v0.13.2 keeps symbolic placement/dimension values typed until Box, Cylinder or
Cone anchor arithmetic is complete and converts them to native SolidCraft
expressions only when the final primitive command is emitted.

For Cylinder axial anchors, BOTTOM/LEFT/FRONT now also keep the native base
directly on the placed coordinate instead of creating a synthetic
`+height/2 -height/2` dependency.

This patch adds no new public modelling API beyond v0.13.1. Downstream users
adopting the v0.13.x capability batch should use **v0.13.2 or newer**.

### Fixed

- Preserve symbolic primitive placement through anchor arithmetic (#796),
  including the HUB75-style symbolic Cylinder boolean join and the equivalent
  Box/Cone lowering boundary.

## [0.13.1] - 2026-11-23

### Release clarification

v0.13.1 is a patch release that corrects Forge release documentation and
version guidance. It does **not** add new modelling behavior beyond v0.13.0.

The important release boundary is:

- v0.12.0 is a valid, immutable release, but it was published before the later
  `dev-cad` model-unblocking batch reached stable `main`;
- v0.13.0 is the first release that actually contains that post-v0.12 CAD
  batch;
- v0.13.1 republishes the same modelling baseline with corrected release notes
  so downstream users are not told to upgrade only to v0.12.0 for fixes that
  are absent from that tag.

The post-v0.12 fixes first available in v0.13.0 are:

- #746 Cone participation in native Boolean feature compilation;
- #747 `Polygon2D` in explicit and face-attached Sketches;
- #749 model-local Python import isolation;
- #750 rotated standalone Sketch cutters.

The original `Cone` primitive already existed before v0.12.0. The missing
Cone change was specifically #746's native Boolean feature support.

v0.13.0 also introduced the next native sheet-metal API slices:

- #773 `Shape.hem(...)` on existing sheet bodies;
- #776 `Shape.path_flange(...)` using reusable open Sketch-chain history.

Downstream models that depend on #746, #747, #749 or #750 require
**v0.13.0 or newer**. v0.13.1 is the recommended patch level because its
release metadata now states that boundary explicitly.

### Changed

- Corrected the release documentation and version guidance for the v0.12.0 to
  v0.13.x transition (#789).

## [0.13.0] - 2026-11-23

### Added

- Added native `Shape.hem(...)` sheet-metal history on existing sheet bodies.
  Hem length and optional gap remain parameterized in mm while the active sheet
  rule owns thickness, K-factor and bend radius (#773).

- Added native `Shape.path_flange(...)` on existing sheet bodies using the
  reusable open connected Sketch-chain replay identity. The qualified initial
  contract is line-only with an optional parameterized bend-radius override
  (#776).

### Fixed

- Cone primitives now participate in native feature-compiler Boolean
  join/cut/intersect operations instead of being limited to the primitive-only
  CSG route (#746).

- `Polygon2D` now lowers correctly inside explicit and face-attached Sketches,
  including attached through-all cutter workflows (#747).

- `run_script()` isolates model-local Python modules between independent model
  roots so one CAD model cannot reuse another model's local import accidentally
  (#749).

- Standalone extruded Sketch cutters preserve an explicit rotated local Sketch
  frame before normal Boolean CSG, enabling rotated cutter Shapes without a
  consumer-local workaround (#750).


## [0.12.0] - 2026-11-23

### Added

- Standalone `Sketch(...).extrude(...)` results can be used directly as
  Boolean join/cut/intersect operands without an attached Sketch or temporary
  cutter body (#354).

- `Sketch.profile(...)` supports connected mixed straight-line and circular-arc
  closed profiles with native connectivity and parameter-preserving lowering
  (#567).

- Sheet bodies support native SolidCraft edge flanges with explicit edge
  selection and rule-owned material properties (#682).

- `Sketch.chain(...)` supports reusable open connected chains, including the
  qualified line-to-tangent-arc path needed by sheet-metal consumers (#683).

- Open Sketch chains can create native SolidCraft contour flanges without
  extrude/fuse approximations (#684).

### Changed

- Forge owns one canonical reusable `model.yml` contract in
  `scpf.model_metadata`, with an exact seven-field template and shared mapping
  validator for Forge and CAD consumers (#703).

- Assembly lowering gives component-local Sketch features deterministic
  document-global native identities, so independent reusable component
  definitions and variants may reuse authored names such as `Profile` (#679).

- Forge CAD-CI now consumes the externally accepted owner stack
  `tool.cad.ci v0.35.0`, `lib.py.cad.ci v0.18.2` and
  `lib.py.cad.verification v0.16.0`. PR/durable workflows, generic build
  storage/Page publication, built-in CadQuery/build123d reference execution and
  reusable verification mechanics are owner-layer capabilities; Forge keeps
  only repository-owned builders and Forge-specific expectations
  (#261, #661, #662, #740).

- Merge governance supports history-preserving permanent-lane promotion and
  stable-to-lane synchronization, plus the reviewed `/merge-resolved`
  conflict-recovery path through the released shared policy (#718, #743).

### Fixed

- Release result reporting and post-release reconciliation distinguish source
  metadata from actual immutable tag/GitHub Release evidence (#655).
## [0.11.0] - 2026-11-22

### Added

- Native `Slot*2D` profiles now keep editable SolidCraft 0.45 dimensions:
  all five Slot creators accept parameterized width, while the three straight
  Slot creators support parameterized horizontal/vertical length and position
  through native dimensioned-sketch constraints. The `slot-family`
  verification mutates width, straight length and position in the saved
  SolidCraft design without rerunning Forge Python (issue #355).

- Added the first native sheet-metal workflow: `Sketch.sheet_metal(...)`
  creates a rule-backed flat sheet from one closed XY Sketch and
  `Shape.fold(...)` bends existing sheet material with native
  `sheet.fold` history. The `sheet-fold` verification proves the formed
  geometry and recovered 80 × 40 × 2 mm flat pattern with its Ø6 cutout
  (issue #305).

- Added `Cone(d=..., top_d=..., h=...)` as a native `solid.cone`
  primitive. `top_d=0` creates a cone and a non-zero top diameter creates a
  tapered cylinder/frustum, with the same principal-axis and axial-anchor
  conventions as the other Forge primitives (PR #310).

- Added `python -m scpf --version`, concise default CLI errors with source
  locations, and `--debug` for the original traceback plus exact checkout
  identity when available. Package identity remains separate from the tested
  SolidCraft version (issue #356, PR #601).

### Changed

- Forge is now qualified against SolidCraft 0.45.0 from immutable
  `docker.cad.solidcraft v0.3.4`. The checked-in SolidCraft 0.45 command
  reference is captured from that immutable runtime rather than maintained as a
  hand-authored subset.

- Verification and publication now use the released generic CAD-CI and
  verification layers, with exact `tool.cad.ci 0.17.0` /
  `lib.py.cad.ci 0.9.3`, explicit `jobs=2`, immutable runtime-role images,
  durable `main`/`dev-cad`/`dev-ci` build scopes and matching generated
  Pages. Forge no longer owns a second generic CI, verification or runtime
  packaging implementation.

- Forge release publication is explicit rather than an automatic consequence
  of a green CI run. A release candidate must have matching durable main build,
  `forge-release` verification and stable Pages evidence before its annotated
  tag and GitHub Release can be created.

### Removed

- Removed the obsolete `Shape.repeat_linear()` / `linear_repeat` Forge-side
  repetition path. Repeated history features use native rectangular or circular
  patterns instead. The `anchored-holes` verification proves one
  face-attached source cut plus one native rectangular pattern (issue #256).

- Removed the remaining legacy Qualification orchestration and duplicate
  runtime/verification ownership after the migration to declarative model
  verification and released owner-layer dependencies.

### Fixed

- `Sketch.add(slot)` and automatic Slot registration now preserve the authored
  sketch-local coordinates of all five native Slot profile kinds instead of
  applying an implicit semantic-center anchor (issue #357, PR #597).

- Presentation-only main changes reuse the existing complete `build/main`
  technical baseline without recalculating every model/reference input.
  Technical changes still require the normal verification and promotion path
  (issue #320).


## [0.10.0] - 2026-11-18

### Added

- Add explicit native `Hole`, `CounterboreHole`, `CountersinkHole` and
  `ThreadedHole` features with shared body × feature contract tests and a
  dedicated `hole-family` qualification (issue #302).

### Changed

- Remove countersink-specific optional arguments from `Hole`; countersink,
  counterbore and thread intent now use their dedicated constructors.


## [0.9.1] - 2026-11-18

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

