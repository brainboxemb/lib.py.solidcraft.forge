# Experimental Forge IR coverage

This is the permanent-`exp` migration inventory for the engine-neutral CAD IR.
It is evidence/status, not a competing work plan; canonical unfinished-work
ordering remains `main:docs/plan.md`.

Three different questions are reported separately:

- **IR coverage** — how much public CAD meaning is represented by typed,
  backend-neutral Forge IR?
- **backend coverage** — which typed IR can each backend lower and qualify?
- **owner evidence** — which physical owners currently have end-to-end evidence
  for more than one engine?

## Status definitions

- **complete** — the current public semantic family is represented by typed IR.
- **partial** — useful public slices are typed, but documented semantics in the
  same family still remain legacy or outside the typed contract.
- **legacy** — the family still relies on the stable SolidCraft compatibility
  path and has no accepted semantic IR node.
- **out-of-scope** — public Forge functionality that is not core CAD model
  semantics for this IR.

Backend status never upgrades an incomplete IR family.

## Headline inventory

Current conservative family-level inventory:

- IR-relevant semantic families: **20**
- complete: **7 / 20 (35%)**
- partial: **11 / 20 (55%)**
- legacy: **2 / 20 (10%)**
- families with at least some typed IR: **18 / 20 (90%)**
- physical SCPF owners on permanent `exp`: **61**
- owners with current end-to-end `scpf-mitcad` evidence: **10 / 61 (16.4%)**

The family percentages are intentionally unweighted. They show migration shape,
not effort or backend parity.

## CAD semantic families

| Semantic family | IR | SolidCraft typed | Mitcad | Native Mitcad | Main remaining gap |
| --- | --- | --- | --- | --- | --- |
| Values, parameters, scalar expressions | partial | partial | partial | qualified slices | Length/angle plus unitless count roles are typed; #550 adds Hole countersink-angle use-site typing and #560 applies count-vs-length roles to Sketch patterns; broader symbolic/cadmath dimensional expression semantics remain. |
| Primitive solids: Box, Cylinder, Cone, Sphere | complete | yes | yes | qualified | Current public primitive meaning is typed. |
| Placement and transforms | partial | partial | partial | qualified slices | #544 adds semantic absolute/anchored FeaturePlacementIR plus BoundOffsetIR for within-component features; rotated primitive/component frames and broader transforms remain. |
| Reference geometry: planes and axes | partial | partial | partial | qualified slices | PlaneIR plus principal/vector AxisLineIR are typed; broader datum/reference semantics remain. |
| Sketch entities, constraints, dimensions | complete | partial | partial | qualified slices | #560 types current public closed/open line/arc geometry, Text, Sketch-local source identity, rectangular pattern and mirror on top of existing point/line/constraint/dimension IR; support/consumer composition is tracked separately. |
| 2D profiles | complete | yes | partial | qualified slices | #534 covers public Circle/Polygon/Rectangle/RoundedRectangle/Slot closed-profile constructors; text/open connected geometry remains in the broader Sketch-entity family. |
| Regions/profile membership | partial | partial | partial | qualified slices | General region composition. |
| Extrude | partial | partial | partial | qualified slices | Attached/rotated/broader profile and operation forms. |
| Revolve | partial | partial | partial | qualified slices | Broader profile/operation/reference forms. |
| Boolean body operations | partial | partial | partial | qualified slices | General feature/body operands. |
| Topology/reference selectors | partial | partial | partial | qualified slices | Profile/vertex/explicit and broader directional selectors. |
| Chamfer | partial | partial | partial | qualified slices | Broader bases/selectors/orientations. |
| Fillet | partial | partial | partial | qualified slices | Broader bases/selectors/variable forms. |
| Feature identity, suppression, configuration | partial | partial | partial | qualified slices | General feature/config composition. |
| Hole family | complete | yes | unsupported | no | #550 represents current public absolute/anchored Hole-family meaning through shared FeaturePlacementIR, with TOP/BOTTOM simple SolidCraft lowering and backend-unsupported anchored variants remaining typed/fail-closed. |
| Native feature patterns | complete | yes | unsupported | no | #533 covers current public rectangular/circular feature-pattern controls with semantic FeatureRefIR source identity; models still depend on their source features being typed. |
| Shell | complete | yes | unsupported | no | #532 covers the current public shell operation through ShellIR + cardinal FaceSetIR over typed body history; a legacy base is a dependency boundary, not missing Shell semantics. |
| Plastic features: Lip, SnapFit, Boss, Rest | complete | yes | unsupported | no | #544 types all current public Lip/SnapFit/Boss/Rest feature meaning plus absolute/anchored placement; unsupported backend/anchor forms remain backend limitations, not missing feature semantics. |
| Sheet metal | legacy | legacy stable | unsupported | no | Sheet rule/body/features form a separate large semantic layer. |
| Assemblies, occurrences, relationships | legacy | legacy stable | unsupported | no | Coherent assembly/relationship IR. |

## Outside the core CAD-IR denominator

| Family | Status | Reason |
| --- | --- | --- |
| Drawings and annotations | out-of-scope | Paper/layout/annotation presentation. |
| Appearance and exploded presentation | out-of-scope | Display/presentation state. |
| Execution API and diagnostics | out-of-scope | Compiler/runtime interface concerns. |

## Migration rule

For an IR batch:

1. define generic CAD meaning;
2. normalize unchanged SCPF source into typed IR;
3. prove accepted/rejected boundaries with pure IR tests;
4. preserve stable behavior through typed SolidCraft lowering;
5. require unsupported backends to fail closed;
6. update this inventory.

Mitcad may consume several newly IR-ready capabilities later in one
backend-focused batch with backend tests and native qualification. #532 added generic BodyIR history and ShellIR; #533 completed native feature
PatternIR; #534 completes the public basic closed-profile constructor family;
#544 adds generic within-component FeaturePlacementIR and completes the public
Plastic feature family; #550 completes the current public Hole semantic family;
#560 completes the support-independent public Sketch entity/operation graph.
Remaining legacy families are Sheet metal and Assemblies; #561 next composes
that Sketch graph with support, RegionIR and Extrude semantics before backend
catch-up becomes the pacing item.
