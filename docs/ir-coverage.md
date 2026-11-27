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
- complete: **17 / 20 (85%)**
- partial: **3 / 20 (15%)**
- legacy: **0 / 20 (0%)**
- families with at least some typed IR: **20 / 20 (100%)**
- physical SCPF owners on permanent `exp`: **61**
- owners with current end-to-end `scpf-mitcad` evidence: **10 / 61 (16.4%)**

The family percentages are intentionally unweighted. They show migration shape,
not effort or backend parity.

## CAD semantic families

| Semantic family | IR | SolidCraft typed | Mitcad | Native Mitcad | Main remaining gap |
| --- | --- | --- | --- | --- | --- |
| Values, parameters, scalar expressions | complete | partial | partial | qualified slices | #577 types the complete existing public scalar grammar: literals, Parameter refs, unary/arithmetic, fixed numeric power and cadmath min/max/sqrt/abs/round/floor/atan; use-site roles stay separate. Non-affine backend lowering remains backend catch-up. |
| Primitive solids: Box, Cylinder, Cone, Sphere | complete | yes | yes | qualified | Current public primitive meaning is typed. |
| Placement and transforms | partial | partial | partial | qualified slices | #544 types within-component absolute/anchored FeaturePlacementIR and #555 types symbolic occurrence Placement plus fixed occurrence rotation; arbitrary primitive/body transform composition remains. |
| Reference geometry: planes and axes | partial | partial | partial | qualified slices | PlaneIR plus principal/vector AxisLineIR are typed; broader datum/reference semantics remain. |
| Sketch entities, constraints, dimensions | complete | partial | partial | qualified slices | #560 completes current public Sketch entity/operation semantics by reusing #554 SketchChainIR and adding Text plus Sketch-local rectangular-pattern/mirror source identity; support/consumer composition is tracked separately. |
| 2D profiles | complete | yes | partial | qualified slices | #534 covers public Circle/Polygon/Rectangle/RoundedRectangle/Slot closed-profile constructors; text/open connected geometry remains in the broader Sketch-entity family. |
| Regions/profile membership | complete | yes | partial | qualified slices | #561 covers current public all-profile, exact-region and explicit Sketch-local selector intent; Mitcad support remains backend catch-up. |
| Extrude | complete | yes | partial | qualified slices | #561 covers current public standalone/attached finite positive/negative/symmetric and through-all cut semantics over typed Sketch graphs/regions; Mitcad support remains partial. |
| Revolve | complete | yes | partial | qualified slices | #586 reuses the complete Sketch graph for the current working standalone Revolve surface: Circle/Rectangle/RoundedRectangle/Polygon/closed connected profile, symmetric sweep and symbolic AxisLine/angle intent; Slot/Text/pattern remain outside the current Revolve compiler surface and Mitcad remains a qualified subset. |
| Boolean body operations | complete | partial | partial | qualified slices | #581 represents join/cut/intersect as recursive BodyIR × BodyIR composition in authored order. SolidCraft retains qualified primitive/Extrude/Revolve tool lowering; Mitcad remains a backend subset. |
| Topology/reference selectors | complete | yes | partial | qualified slices | #562 types the current public face-boundary, principal-parallel, cardinal direction-pair, named Polygon segment/vertex and explicit fixed-pick selector vocabulary; Mitcad support remains a backend subset. |
| Chamfer | complete | yes | partial | qualified slices | #562 types the complete public distance/distance2/flip contract over shared EdgeSelectionIR and typed BodyIR; backend support remains a separate dimension. |
| Fillet | complete | yes | partial | qualified slices | #562 types the complete public radius + EdgeSelectionIR contract over typed BodyIR; backend support remains a separate dimension. |
| Feature identity, suppression, configuration | partial | partial | partial | qualified slices | #555 adds definition-level ComponentFeatureRefIR for exported reusable-child identity; broader configuration/rule/feature composition remains. |
| Hole family | complete | yes | unsupported | no | #550 represents current public absolute/anchored Hole-family meaning through shared FeaturePlacementIR, with TOP/BOTTOM simple SolidCraft lowering and backend-unsupported anchored variants remaining typed/fail-closed. |
| Native feature patterns | complete | yes | unsupported | no | #533 covers current public rectangular/circular feature-pattern controls with semantic FeatureRefIR source identity; models still depend on their source features being typed. |
| Shell | complete | yes | unsupported | no | #532 covers the current public shell operation through ShellIR + cardinal FaceSetIR over typed body history; a legacy base is a dependency boundary, not missing Shell semantics. |
| Plastic features: Lip, SnapFit, Boss, Rest | complete | yes | unsupported | no | #544 types all current public Lip/SnapFit/Boss/Rest feature meaning plus absolute/anchored placement; unsupported backend/anchor forms remain backend limitations, not missing feature semantics. |
| Sheet metal | complete | yes | unsupported | no | #554 types the current public sheet rule, base/contour creation, fold, edge flange, hem, path flange and manufacturing perforation history; Mitcad remains a backend gap only. |
| Assemblies, occurrences, relationships | complete | yes | unsupported | no | #555 types reusable definitions, occurrences/pose/grouping, assembly anchors, definition-level exported feature identity and rigid/planar/revolute/as-built relationships; drawings/exploded presentation and configuration tables remain separate families/layers. |

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
Plastic feature family; #550 completes the current public Hole semantic family,
including BOTTOM placement and degree-typed countersink parameters. #554 then
completes current public Sheet metal semantics through SheetRuleIR,
SketchChainIR and typed sheet history. #555 then introduces AssemblyIR for
reusable definitions, occurrences, placement/grouping, anchors and relationships.
All 20 tracked semantic families now have typed IR and no family is fully
legacy. #560 then completes the support-independent public Sketch entity and
operation graph while reusing the same SketchChainIR. #561 composes that graph
with semantic Sketch support/frame intent, general RegionIR selector semantics
and the current public standalone/attached Extrude contract, moving Regions and
Extrude to complete. #562 then completes the shared public edge-selector
vocabulary and moves Topology/reference selectors, Chamfer and Fillet to complete.
#577 then completes Values/parameters/scalar expressions by typing fixed numeric
power and the existing public cadmath function grammar while keeping physical
roles at typed use sites. #581 then completes Boolean body-operation semantics
as recursive typed BodyIR composition while keeping backend lowering coverage
independent. #586 then completes the current working Revolve semantics by reusing the
completed Sketch graph for the supported standalone profile set, symmetric
sweep and symbolic AxisLine/angle intent without broadening Slot/Text/pattern
compiler behavior.
The migration therefore continues entirely as partial -> complete closure while
backend catch-up remains independent.
