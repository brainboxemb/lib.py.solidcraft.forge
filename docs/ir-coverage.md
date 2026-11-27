# Forge IR coverage

This is the canonical migration ledger for the experimental engine-neutral CAD
IR. It answers a different question from backend/model qualification:

- **IR coverage**: how much public CAD meaning is represented by typed,
  backend-neutral Forge IR?
- **backend coverage**: which typed IR can a backend lower and qualify?
- **owner evidence**: which physical model owners have end-to-end evidence for
  more than one engine?

Do not use one number as a substitute for the others.

## Status definitions

- **complete**: the current public semantic family is represented by typed IR;
  remaining work is not a known public semantic variant in that family.
- **partial**: useful public slices are typed, but documented public semantics in
  the same family still fall through `LegacyShapeIR` or remain outside the
  typed contract.
- **legacy**: the family is still compiled through the stable SolidCraft legacy
  path and has no accepted semantic IR node.
- **out-of-scope**: public Forge functionality that is not CAD model semantics
  for this IR, for example drawing presentation or compiler execution helpers.

Backend cells are independent. “Qualified” means real native runtime evidence
exists for at least the typed slice named in the notes; it does not upgrade a
partial IR family to complete.

## Headline inventory

Current family-level inventory:

- IR-relevant semantic families: **20**
- complete: **1 / 20 (5%)**
- partial: **13 / 20 (65%)**
- legacy: **6 / 20 (30%)**
- families with at least some typed IR: **14 / 20 (70%)**
- physical SCPF model owners on permanent `exp`: **61**
- owners with current end-to-end `scpf-mitcad` evidence: **10 / 61 (16.4%)**

The family percentages are intentionally coarse and unweighted. They are useful
for migration direction, not for estimating implementation effort. A large
family such as assemblies is not equivalent in effort to one primitive family.

## CAD semantic families

| Semantic family | IR status | SolidCraft typed lowering | Mitcad lowering | Native Mitcad | Remaining semantic work |
| --- | --- | --- | --- | --- | --- |
| Values, parameters and scalar expressions | partial | partial | partial | qualified slices | Role-aware `ParameterIR` and affine scalar expressions exist; broader public symbolic/cadmath expression semantics are not all represented. |
| Primitive solids: Box, Cylinder, Cone, Sphere | complete | yes | yes | qualified | Current public primitive meaning is represented by `BoxIR`, `CylinderIR`, `ConeIR`, `SphereIR`. |
| Placement and transforms | partial | partial | partial | qualified slices | Principal placement is typed; rotated primitive frames and broader transform composition remain outside the accepted contract. |
| Reference geometry: planes and axes | partial | partial | partial | qualified slices | `PlaneIR` and `AxisLineIR` exist; broader datum/reference semantics remain. |
| Sketch planes, entities, constraints and dimensions | partial | partial | partial | qualified slices | Typed line/point/orientation/length/coordinate relations exist; the full public Sketch surface is larger. |
| 2D profiles | partial | partial | partial | qualified slices | Circle and Polygon semantic profiles exist; Rectangle/RoundedRectangle/Slot families are not fully represented as generic profile IR. |
| Regions/profile membership | partial | partial | partial | qualified slices | `RegionIR` covers qualified polygon/concentric-circle cases; general region composition remains. |
| Extrude | partial | partial | partial | qualified slices | Qualified circle/polygon standalone slices exist; attached/rotated/broader profile and operation forms remain. |
| Revolve | partial | partial | partial | qualified slices | Polygon/profile + typed axis and bounded new-body/cut forms exist; broader profile/operation/reference forms remain. |
| Boolean body operations | partial | partial | partial | qualified slices | Recursive typed CSG exists for bounded operands; general feature/body operands are not yet generic. |
| Topology/reference selectors | partial | partial | partial | qualified slices | `FaceBoundaryIR` and `ParallelEdgeSetIR` exist; profile/vertex/explicit and broader directional selectors remain. |
| Chamfer | partial | partial | partial | qualified slices | Equal/two-distance bounded `ChamferIR` exists; broader bases/selectors/orientations remain. |
| Fillet | partial | partial | partial | qualified slices | Vertical and TOP face-boundary bounded `FilletIR` exist; broader bases/selectors/variable forms remain. |
| Feature identity, suppression and configuration | partial | partial | partial | qualified slices | `FeatureRefIR` and bounded suppression/configuration IR exist; general feature/config composition is not complete. |
| Hole family | legacy | legacy stable | unsupported | no | #519 starts semantic simple through-all `HoleIR`; counterbore/countersink/threaded and wider depth/direction forms follow. |
| Native feature patterns | legacy | legacy stable | unsupported | no | Rectangular/circular history patterns need semantic source-feature/pattern IR after feature identity/Hole groundwork. |
| Shell | legacy | legacy stable | unsupported | no | Public shell intent still uses the legacy SolidCraft compiler path. |
| Plastic/mechanical feature intents: Lip, SnapFit, Boss, Rest | legacy | legacy stable | unsupported | no | Need generic feature/history semantics rather than SolidCraft command-shaped nodes. |
| Sheet metal | legacy | legacy stable | unsupported | no | Sheet rule/body creation/fold/flange/hem/path flange/perforation remain a separate large semantic layer. |
| Assemblies, occurrences and relationships | legacy | legacy stable | unsupported | no | Component/occurrence placement, grouping, anchors and rigid/revolute relationships require a coherent assembly IR layer. |

## Public Forge functionality outside the CAD-IR denominator

| Family | IR status | Reason |
| --- | --- | --- |
| Drawings and drawing annotations | out-of-scope | Paper/layout/annotation presentation is backend/product output, not solid-model CAD IR. |
| Appearance and exploded presentation | out-of-scope | Display/presentation state is not geometric/history semantics for the core CAD IR. |
| Execution API and diagnostics | out-of-scope | `compile_model`, `run_script`, errors and warnings are compiler/runtime interface concerns. |

## Migration policy

IR work should now move horizontally across this table rather than requiring a
new Mitcad proof for every semantic increment.

For an IR PR:

1. define the generic CAD contract;
2. normalize unchanged SCPF source to typed IR;
3. prove accepted/rejected boundaries with pure IR tests;
4. preserve stable behavior through typed SolidCraft lowering;
5. make unsupported backends fail closed;
6. update this ledger.

Mitcad work may then consume several newly IR-ready families in one
backend-focused batch, with backend contract tests and native qualification.

The immediate IR queue starts with #519 HoleIR. After that, choose coherent
families/batches from the remaining partial/legacy rows, with priority on
finishing a family rather than adding another narrow backend-qualified slice.
