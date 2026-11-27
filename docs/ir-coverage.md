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
- complete: **1 / 20 (5%)**
- partial: **13 / 20 (65%)**
- legacy: **6 / 20 (30%)**
- families with at least some typed IR: **14 / 20 (70%)**
- physical SCPF owners on permanent `exp`: **61**
- owners with current end-to-end `scpf-mitcad` evidence: **10 / 61 (16.4%)**

The family percentages are intentionally unweighted. They show migration shape,
not effort or backend parity.

## CAD semantic families

| Semantic family | IR | SolidCraft typed | Mitcad | Native Mitcad | Main remaining gap |
| --- | --- | --- | --- | --- | --- |
| Values, parameters, scalar expressions | partial | partial | partial | qualified slices | Broader symbolic/cadmath dimensional expression semantics. |
| Primitive solids: Box, Cylinder, Cone, Sphere | complete | yes | yes | qualified | Current public primitive meaning is typed. |
| Placement and transforms | partial | partial | partial | qualified slices | Rotated primitive frames and broader transform composition. |
| Reference geometry: planes and axes | partial | partial | partial | qualified slices | Broader datum/reference semantics. |
| Sketch entities, constraints, dimensions | partial | partial | partial | qualified slices | Full public Sketch surface. |
| 2D profiles | partial | partial | partial | qualified slices | Rectangle/RoundedRectangle/Slot families are not fully generic profile IR. |
| Regions/profile membership | partial | partial | partial | qualified slices | General region composition. |
| Extrude | partial | partial | partial | qualified slices | Attached/rotated/broader profile and operation forms. |
| Revolve | partial | partial | partial | qualified slices | Broader profile/operation/reference forms. |
| Boolean body operations | partial | partial | partial | qualified slices | General feature/body operands. |
| Topology/reference selectors | partial | partial | partial | qualified slices | Profile/vertex/explicit and broader directional selectors. |
| Chamfer | partial | partial | partial | qualified slices | Broader bases/selectors/orientations. |
| Fillet | partial | partial | partial | qualified slices | Broader bases/selectors/variable forms. |
| Feature identity, suppression, configuration | partial | partial | partial | qualified slices | General feature/config composition. |
| Hole family | legacy | legacy stable | unsupported | no | #519 migrates explicit `.at(...)` Hole/Counterbore/Countersink/Threaded intent; attached/on/pattern/config composition remains. |
| Native feature patterns | legacy | legacy stable | unsupported | no | Semantic source-feature and pattern IR. |
| Shell | legacy | legacy stable | unsupported | no | Semantic shell feature/history node. |
| Plastic features: Lip, SnapFit, Boss, Rest | legacy | legacy stable | unsupported | no | Generic mechanical feature/history semantics. |
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
backend-focused batch with backend tests and native qualification. The immediate
IR queue begins with the coherent explicit Hole-family #519 `HoleIR` batch.
