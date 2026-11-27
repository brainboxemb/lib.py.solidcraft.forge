# Forge requirements

## Repository

1. Preserve the public SCPF Python API and import name `scpf`.
2. Use the corrected CAD library architecture rather than reproducing historical Forge-local orchestration.
3. Keep source ownership explicit: library, physical models, generic modules, documentation and generated evidence are separate roles.
4. Use `main` as stable, `dev` as normal development integration and optional permanent `exp` as isolated experimental integration. `exp` is not a release source and may not promote directly to `main`.
5. Generated CAD output is owned by `build`; Pages presentation is owned by `gh-pages`. Permanent `main`, `dev` and optional `exp` outputs must remain isolated by source scope. Pages must not duplicate generated CAD artifacts.
6. Every source-branch integration remains merge-policy owned. Normal integration uses `/merge`. A genuinely conflicted direct permanent merge (`dev -> main`, `main -> dev`, `dev -> exp` or `exp -> dev`) may use reviewed `/merge-resolved` only with a separate green same-repository `resolve/*` PR that binds the exact combined tree; the resulting permanent commit must have parents exactly `[base, head]` and the base ref must advance non-force.
7. Temporary, release and main-governance PRs must never use permanent conflict recovery; do not replace a conflicted permanent merge with squash, rebase or direct/manual ref mutation.

## Models

1. `models/<id>/` is the physical selection/publication owner.
2. One owner may declare multiple CAD-engine implementations.
3. Engine implementations are local to the owner and must not become sibling model owners.
4. `model.yml.purpose` may contain `example`, `verification`, or both.
5. Owner-local verification expectations apply independently to every declared implementation unless a future real model demonstrates a justified override.
6. Physical model dependencies name owner ids and downstream dependents must be selected transitively.

## CAD execution

1. Stable Forge execution continues to use the released `reference` and `solidcraft` roles from `docker.cad.solidcraft v0.3.6`; the experimental `exp` line additionally pins the isolated `mitcad` role from released `docker.cad.solidcraft v0.3.7`. This does not imply `dev` or `main` adoption.
2. Standard reference builders are PythonSCAD, pyBOSL2, CadQuery and build123d.
3. SCPF compilation is consumer-owned and feeds the generic SolidCraft command builder; do not teach generic builders Forge semantics.
4. SolidCraft executes in its lightweight runtime; generic mesh verification executes in the reference runtime.
5. CI batches compatible implementation work and does not start one Docker container per model implementation.
6. The experimental `builder-scpf-mitcad` capability lowers the same trusted SCPF source through `run_script(..., backend="mitcad")` and must retain both the native `model.mitcad` document and exported `model.stl`.
7. The Mitcad builder must not download or install a CAD runtime. Its runtime contract is an already-qualified `mitcad-cli` executable on `PATH`, optionally supplied through `CAD_LIBRARY_MITCAD_EXECUTABLE`.
8. Root `runtimes.mitcad` must use the immutable released `cad-mitcad:v0.3.7` role. Experimental `scpf-mitcad` implementations stay inside their existing physical owner, reuse the same SCPF source, keep SolidCraft `scpf` primary and must satisfy that owner's applicable verification contract.
9. The owner-integrated Mitcad set expands only through separately qualified backend capability and owner evidence inside an existing physical model owner; experimental work must not create duplicate model owners merely to add a backend.
10. Every published `scpf-mitcad` build must retain the validated pre-execution Forge-to-Mitcad command document as `mitcad.json` alongside `model.mitcad` and `model.stl`. Pages may project that durable command document but must not reconstruct it.
11. Experimental Pages must present a Mitcad result from the actual exported `model.stl`, label it as an STL-derived Mitcad result rather than a native screenshot, and expose the saved `model.mitcad` document.
12. When multiple backends consume the same owner-local SCPF source, Pages shows that source once and presents the secondary backend as an alternate result, not as independent reference code.
13. Trusted SCPF model source is evaluated once into Forge model objects; final Shape intent is normalized into an engine-neutral typed `ModelIR` before native backend lowering.
14. Portable Forge IR must express CAD semantics and selection intent only. It must not contain SolidCraft command names, Mitcad native ids, engine-owned BRep entities or backend transport details.
15. Native shape backends consume `ModelIR`. New multi-backend features must be introduced once in Forge IR and then lowered independently by each backend; they must not add parallel raw `Shape.data` interpreters.
16. `LegacyShapeIR` is a temporary SolidCraft-only compatibility node for stable surface not yet migrated to typed IR. Experimental backends must fail closed when they receive it.
17. Portable primitive CSG is represented once as typed `BooleanIR` with semantic `join`, `cut` or `intersect` operations. Its target may recursively contain another qualified `BooleanIR`; its current bounded tool is one `PlacementIR` primitive. The former special-case `BooleanSubtractIR(BoxIR, CylinderIR)` must not remain as a parallel representation.
18. Qualified primitive geometry includes `BoxIR`, `CylinderIR` and bounded `SphereIR`. `SphereIR` owns Forge radius semantics; a backend that uses diameter derives it only during lowering.
19. Native backend lowering may choose different engine instructions for the same `BooleanIR`. SolidCraft preserves its existing CSG primitive command sequence while Mitcad uses each primitive feature's native `new_body`, `join`, `cut` or `intersect` operation; both preserve one Forge semantic tree.
20. Mitcad primitive-CSG lowering must not predict native body ids. The bounded left-associated slice emits exactly one initial new body and then native primitive tools with empty participants, letting Mitcad apply each operation to the existing component body set and fail natively when an operation cannot be applied.
21. Qualified primitive placement is represented once by typed `PlacementIR`, which owns the world-space point of a semantic anchor independently from `BoxIR`, `CylinderIR` or `SphereIR` geometry. Native backends must not re-interpret raw `placed_box`, `placed3d` or translation payloads for this migrated slice.
22. SolidCraft lowering must preserve the existing native command/replay output of migrated primitive placement and CSG, including symbolic placement expressions. Mitcad preserves symbolic primitive-plane coordinates; Cylinder axial placement remains on its origin plane, while a centered Box may lower one-sided when its semantic bottom face lies exactly on that plane. Other axial offsets remain fail-closed rather than being baked or approximated.
23. Qualified standalone sketch extrusion must use separate typed `SketchIR`, profile, `RegionIR` and `ExtrudeIR` semantics rather than a fused shape-specific sketch/extrude node.
24. `RegionIR` identifies semantic profile membership with compiler-local profile indexes only. It must not contain SolidCraft curve ids, Mitcad region ids, BRep identities or native coordinate-pick transport.
25. The split Sketch/Extrude boundary qualifies both one centered `CircleProfileIR` without holes and the #320 two-concentric-circle annulus from the existing public exact-region authoring contract. The annulus must normalize to two `CircleProfileIR` nodes plus one `RegionIR` whose hole membership uses compiler-local profile indexes only.
26. A backend coordinate used to bind a native circle region must be derived from semantic circle geometry at lowering time and must not be stored in `RegionIR`. Non-concentric/nonnested circle membership and more than two circle profiles remain outside that qualified slice; other profile families require their own separately qualified semantic IR contract.
27. A bounded closed straight-segment profile is represented by typed `PolygonProfileIR` using Sketch-local semantic coordinates and optional authored segment ids. A qualified fixed polygon may be convex or concave when it is finite, simple, non-self-intersecting and encloses non-zero area. Parameterized polygon coordinates may enter typed profile IR only through a separately qualified consumer feature whose lowering preserves those dependencies; degenerate, self-intersecting or otherwise unqualified polygons remain `LegacyShapeIR` and fail closed on Mitcad.
28. `ExtrudeIR(direction="symmetric")` preserves the public `Sketch.extrude(distance, sym=True)` contract as one **total full length** split across both sides of the sketch plane. A backend-specific half/full-length flag is lowering transport and must not change this semantic.
29. `ChamferIR` may compose over a qualified typed body-producing feature such as `ExtrudeIR`; backends lower that typed base before resolving semantic `FaceBoundaryIR` topology. They must not re-read the original raw Shape payload to recover the base feature.
30. A multi-face `FaceBoundaryIR` remains one semantic edge selection. Mitcad replay may combine native boundary edges from multiple cardinal face queries into one deduplicated binding, but those native face/edge identities and query mechanics remain backend transport rather than Forge IR.
31. Portable Sketch Revolve is represented by typed `RevolveIR` over one `SketchIR`, one qualified simple `PolygonProfileIR` and one `RegionIR`. It preserves axis, angle-valued sweep, feature operation and target intent semantically; native ids, region keys and coordinate picks are lowering transport only.
32. Parameterized polygon coordinates remain symbolic in `PolygonProfileIR`. Current numeric values may be used only to validate a finite simple non-self-intersecting region and derive a deterministic interior selector required by a backend; they must not replace authored parameter/expression dependencies in IR.
33. Parameterized Revolve rectangle relations belong to typed Sketch semantics rather than to one backend. The qualified simple non-rectangular parameterized Polygon path may still use backend-owned point-coordinate transport until that broader Sketch relation graph is separately migrated; parameterized Polygon Extrude remains outside the accepted slice until separately qualified.
34. Angle-valued Revolve parameters use degree units in `ParameterIR`. A parameterized 360-degree sweep remains an angle-driven native feature so later edits to 180 degrees are preserved; lowering must not collapse that parameter dependency into an unconditional full-revolution flag.

35. Revolve axes are semantic reference geometry. Principal world axes and the bounded shifted principal-axis form must normalize through one typed `AxisLineIR(direction, origin)`; backend-native axis strings, sketch curve ids and construction helpers are not IR.
36. `AxisLineIR.origin` may retain Forge Parameters/Expressions. Backends may derive transport geometry from current values, but the authored dependency remains symbolic and must drive the native axis after parameter changes.
37. An authored subtractive Sketch Revolve over a qualified typed target must remain one `RevolveIR(operation="cut", target=...)` feature. Forge must not replace that identity with a new-body Revolve plus an unrelated generic Boolean when the semantic feature itself owns the cut.
38. SolidCraft lowering of the bounded Revolve-cut slice must remain behaviorally equivalent to the existing one-feature native `solid.revolve(operation="cut")` contract. Mitcad may express the same `AxisLineIR` as backend-only construction geometry and must bind the existing target body at runtime rather than storing native ids in IR.
39. The #389 shifted Mitcad `AxisLineIR` slice began with a principal X/Y direction in an unshifted XY Sketch and one Box target. Shifted Sketch-plane support must expand through typed `PlaneIR`, not by baking a plane coordinate into AxisLine transport; non-principal directions and portable configuration/suppression remain later semantic gaps.
40. Standalone Sketch support is semantic reference geometry. Qualified `SketchIR` must reference one typed `PlaneIR(orientation, origin)` rather than storing an engine-shaped plane string.
41. The first `PlaneIR` slice is bounded to principal XY/XZ/YZ orientation. Its XYZ origin may retain Forge Parameters/Expressions; a standalone offset plane varies only on that orientation's normal axis while in-plane origin coordinates remain zero.
42. Existing world-origin Sketch/Extrude/Revolve IR must use the same `PlaneIR` representation as a symbolic shifted plane. A parallel legacy plane-string representation is not permitted inside typed IR.
43. `PlaneIR` and `AxisLineIR` coplanarity must be checked from authored semantic dimensions. Current numeric values may validate fixed coordinates but must not replace a symbolic plane/axis dependency.
44. SolidCraft may lower a principal `PlaneIR` directly to its native Sketch plane/offset form. Mitcad may create a native construction-plane feature for a non-zero or symbolic offset and bind the Sketch to its returned uid; that helper feature, uid and reference are backend transport only.
45. The first shifted-plane runtime qualification is one typed Revolve cut on a symbolic XY plane offset. Rotated frames, arbitrary plane orientations and attached/on-face Sketches remain explicit later semantic gaps and fail closed on experimental backends.

46. Portable authored feature identity is represented by engine-neutral `FeatureRefIR`. Its semantic path must identify a feature in the normalized Forge model and must never contain a SolidCraft feature id, Mitcad uid, replay variable, native command index or retained Python object id.
47. The first portable configuration slice is `ModelIR.configuration = ConfigurationIR(...)` with one exact suppression column, named rows, an explicit active row and boolean cells. Parameter columns, rules, child-definition references, assembly configuration and appearance/visibility configuration remain outside this bounded slice.
48. `Suppress(feature)` is resolved from the original authored Shape identity during normalization. The first accepted reference is the exact root `RevolveIR(operation="cut", target=...)`; a non-member, ambiguous or otherwise unsupported feature reference must fail before backend lowering.
49. SolidCraft lowering of this typed configuration slice must remain behaviorally equivalent to the stable native configuration-table contract and bind the actual native Revolve feature identity returned by replay rather than placing a SolidCraft id in IR.
50. Mitcad lowering may introduce a backend-private suppression driver parameter because native configuration rows drive parameters. That driver and the returned Revolve uid are lowering transport only: the native Revolve result must be bound from the command result, rows must retain their authored names and suppression must follow the private expression without exposing that parameter in Forge IR or public SCPF parameters.
51. Exact Mitcad qualification for the suppression slice must save the configured design, reopen that same native `.mitcad` document, apply the `Suppressed` row without rerunning Forge Python, prove the exact Revolve feature is suppressed and geometry becomes the uncut target, then apply `Cut` again and prove the cut returns.
52. Stable SolidCraft configuration forms outside this portable slice may continue through the existing compatibility path while migration is incomplete; experimental backends must fail closed rather than interpret those broader forms independently.
53. `FeatureRefIR` may reference authored features below the root when the normalized typed feature tree exposes stable semantic roles. The first nested-history slice uses `BooleanIR.target` / `BooleanIR.tool` path segments; command emission order is not semantic identity.
54. Nested feature-reference normalization must walk the authored Shape tree and normalized IR together while Python object identity is still available, then retain only the semantic path. A non-member, malformed or unsupported path must fail before backend lowering.
55. SolidCraft and Mitcad may map the same nested semantic path to different native command/result positions, but that mapping is backend-owned. Native feature ids, replay names and command indexes must not be added to `FeatureRefIR`.
56. Native qualification of a nested suppression reference must save the configured design, reopen it without rerunning Forge authoring, suppress the exact referenced feature, prove geometry changes in a way that distinguishes that feature from neighboring history, then restore the authored active row and prove the original state returns.
57. The first nested-history runtime owner remains bounded to one suppression column over the existing typed `primitive-csg` Boolean tree. Multiple columns, parameter/rule ConfigurationIR, reusable-child feature references, assemblies and generalized topology references remain separate compiler layers.
58. A qualified Sketch may carry `SketchRelationsIR` beside profile/region intent. The first relation graph contains semantic `SketchPointIR`, `SketchLineIR`, horizontal/vertical `SketchOrientationConstraintIR` and symbolic `SketchLengthDimensionIR`; tuple positions are Sketch-local semantic references, never engine ids or backend command indexes.
59. The first Sketch-relations slice is the existing origin-based axis-aligned four-edge parameterized rectangle used by `native-revolve`. `length` and `radius` remain their authored Parameter/Expression values in point and dimension intent; current numeric values may validate the bounded rectangle but must not replace those dependencies.
60. `PolygonProfileIR` and `RegionIR` continue to own closed-profile and region membership semantics. `SketchRelationsIR` is a complementary entity/constraint/dimension layer and must not replace profile/region intent with backend-shaped sketch commands.
61. Independent backends may choose different efficient native spellings for the same Sketch relation graph. SolidCraft may coalesce the qualified graph to its symbolic closed-polyline form when that preserves all semantic dependencies; Mitcad may emit native points, lines, horizontal/vertical constraints and length dimensions. This difference is lowering transport, not divergent CAD meaning.
62. Once a Sketch relation slice is typed, a backend must consume that relation graph and must not rediscover its horizontal/vertical or dimensional semantics by inspecting `PolygonProfileIR` coordinates. Native point/curve/constraint ids and solver anchoring remain backend-private transport.
63. The #440 runtime qualification reuses the unchanged dual-backend `native-revolve` owner. SolidCraft must retain its existing saved-design radius/sweep mutation, Mitcad must retain native geometry/runtime evidence, and no duplicate model owner or public constraint-authoring syntax is introduced.
64. General parameterized simple-Polygon Revolve must normalize point-coordinate intent into `SketchRelationsIR` rather than leaving Mitcad to reconstruct it from `PolygonProfileIR`.
65. `SketchCoordinateDimensionIR(point, axis, value)` represents one signed X/Y coordinate of a semantic Sketch point relative to the Sketch origin. The point reference is Sketch-local; native origin entities, p/c/k ids, replay names and command indexes are forbidden in this IR.
66. The generic parameterized Polygon relation graph contains all authored semantic points, cyclic straight-line connectivity and one X plus one Y coordinate dimension per point. The exact authored Parameter/Expression values remain the dimension values; evaluated numbers are validation/solver seeds only.
67. The stronger #440 rectangle graph remains H/V plus edge-length based. Generic coordinate dimensions are a complementary fallback for already-qualified parameterized simple polygons, not a reason to weaken the rectangle semantics.
68. SolidCraft may coalesce a complete coordinate-dimension graph to its symbolic closed `sketch.line` form after validating that every point coordinate is represented. Mitcad may create one fixed native origin point and native signed horizontal/vertical distance dimensions, but those are lowering transport derived from the typed graph.
69. Once coordinate dimensions are typed, Mitcad must not keep or reintroduce a backend-private `_parameterized_polygon_sketch(...)` semantic reconstruction path. The exact pinned native runtime must execute a non-rectangular parameterized Revolve through the typed relation graph.
70. Parameterized simple-Polygon symmetric new-body Extrude must use the same typed `SketchRelationsIR` contract as other qualified profile-driven features; parameterized coordinates alone must not force this bounded feature back to `LegacyShapeIR`.
71. Polygon Extrude normalization must retain `PolygonProfileIR` / `RegionIR` and attach the strongest already-qualified relation graph available: the #440 origin-based rectangle graph when applicable, otherwise the #447 coordinate-dimension graph.
72. SolidCraft and Mitcad must consume the attached Sketch relation graph for a parameterized Polygon Extrude. Direct backend reconstruction of parameter dependencies from `PolygonProfileIR` is forbidden once relations are present.
73. Fixed-coordinate Polygon Extrude remains valid without a relation graph. The #451 checkpoint does not broaden direction/operation/region scope beyond the existing symmetric single-region new-body contract.
74. Exact pinned Mitcad runtime qualification must execute a parameterized rectangle Extrude, preserve its native parameter-driven Sketch dimension and prove deterministic solid geometry.
75. For a qualified multi-profile Circle Sketch, `RegionIR` describes only the boundary profiles of the selected connected region; unrelated profiles present in `SketchIR.profiles` are not implicitly region holes or members.
76. The first 3+ profile exact-region slice is bounded to distinct, origin-centered concentric `CircleProfileIR` loops and one authored exact-region pick. Current finite positive radii may resolve the pick interval, but `RegionIR` retains only semantic profile indexes.
77. For concentric circles, the immediate enclosing profile is the selected region outer boundary and the immediate smaller profile, when present, is its single hole. A pick on a profile boundary or outside every profile is invalid for this typed slice.
78. `RegionIR` validation must be independent of total Sketch profile count. Extra concentric profiles may exist strictly inside the selected hole or strictly outside the selected outer boundary, but no unreferenced profile may divide the interval between a region outer boundary and its hole.
79. SolidCraft and Mitcad must lower the same typed multi-profile `RegionIR` without rediscovering outer/hole membership. Native selector points and curve/profile ids remain backend transport only.
80. Exact pinned Mitcad runtime qualification must execute the three-circle exact annulus while retaining all three native Circle entities and extruding only the typed selected region.
81. Standalone Sphere anchors and world placement must normalize through the existing `PlacementIR(SphereIR)` contract; Forge must not introduce a Sphere-specific placement node or native-plane identity into semantic IR.
82. `PlacementIR.point` remains the world-space point of the selected Sphere anchor. The actual Sphere centre is derived from radius, point and anchor while retaining authored Parameter/Expression dependencies.
83. SolidCraft and Mitcad may spell the same Sphere placement differently. SolidCraft may emit its native 3D centre directly; Mitcad may derive an XY support plane plus plane-local centre. This is backend transport, not divergent placement meaning.
84. For a qualified standalone Sphere whose semantic centre has non-zero or symbolic Z, Mitcad must lower one backend-owned offset XY construction plane and reference it from the Sphere feature. The construction-plane uid/binding must not enter Forge IR.
85. The #461 checkpoint does not broaden primitive Boolean CSG: shifted or non-center-anchor Sphere operands remain outside the qualified recursive CSG slice even though the same standalone PlacementIR is now representable.
86. Exact pinned Mitcad runtime qualification must execute a parameterized top-anchor Sphere placement, retain radius/world-Z dependencies in the native support-plane/Sphere definitions and prove deterministic geometry.
87. `ParameterIR` must retain semantic use roles rather than assigning one global physical unit to every authored Forge `Parameter`; the first qualified roles are `length` and `angle` in canonical order.
88. Existing single-role length and angle parameters must retain their current native spelling and editability. A direct authored parameter used in both roles must remain one semantic parameter with one current numeric value.
89. Mixed-role lowering must publish one editable native source parameter, not independent length/angle aliases. SolidCraft and Mitcad may represent that source as unitless/Number and apply explicit `mm` or `deg` context at the typed use site.
90. Typed use-site coercion belongs to semantic fields: Sketch coordinates/dimensions are length-valued and Revolve extent is angle-valued. Backends must not infer the role from command names or native parameter metadata.
91. The #469 slice qualifies only direct `Parameter` reuse across length and angle slots. If a mixed-role source is nested inside an arbitrary authored `Expression`, the model remains outside portable IR until dimensional expression typing exists.
92. Exact pinned Mitcad runtime qualification must execute the mixed-role Revolve using one unitless native source parameter, explicit length/angle use expressions and deterministic solid geometry.
93. Backend lowering may use private helper commands for one semantic feature without adding those helpers to Forge IR. The first qualified case is the Mitcad offset construction plane required by a shifted/anchored Sphere inside `BooleanIR`.
94. A backend command group for one semantic CSG primitive contains zero or more helper commands plus exactly one native command representing the semantic feature. Helper bindings and command indexes remain backend transport only.
95. `FeatureRefIR` path meaning must remain independent of native command layout. Root/target/tool and nested history paths must bind the native semantic feature command even when helper commands precede it.
96. Configuration suppression of a Sphere CSG tool must bind the Sphere operation command, never its support construction plane; existing Box/Cylinder/origin-Sphere feature mapping must remain unchanged.
97. The #473 normalization slice may reuse the already-qualified standalone `PlacementIR(SphereIR)` anchor/world-point semantics inside primitive Boolean CSG. It does not introduce new Sphere placement meaning or rotated primitive frames.
98. Exact pinned Mitcad runtime qualification must execute a Box cut by an internal shifted Sphere, retain the private support-plane reference and prove deterministic volume/bounds.
99. Standalone and placed public Cone/frustum intent must normalize to typed `ConeIR(height, diameter, top_diameter, axis)` under the existing generic `PlacementIR`; Forge must not add a Cone-specific placement node or backend plane identity to semantic IR.
100. `PlacementIR.point` remains the world-space point of the selected Cone axial anchor. The backend derives the Cone base from height, principal axis, point and anchor using the same semantic helper as the stable SolidCraft surface.
101. SolidCraft typed Cone lowering must preserve the accepted `solid.cone` command contract: height, diameter, top_diameter, derived base, principal axis, operation and body name.
102. Mitcad Cone lowering must use its native principal support plane, plane-local centre, radius, top_radius and height. When the semantic Cone base is off the origin plane, a private offset construction plane may be emitted; that helper remains backend transport only.
103. The #477 bounded slice covers standalone/placed/translated Cone on principal X/Y/Z axes. Cone inside `BooleanIR`, Fillet composition and rotated primitive frames remain outside the qualified slice.
104. Exact pinned Mitcad runtime qualification must execute a placed Ø18→Ø10 × 8 frustum with BOTTOM at world Z=18 and prove volume `1208π/3` plus Z bounds [18, 26].
105. Authored `Expression` values may retain an engine-neutral scalar arithmetic tree separately from their compatibility/debug expression text; Forge normalization and native backends must never recover semantic arithmetic by parsing that text.
106. The first scalar-expression IR consists of finite numeric literals, semantic parameter references, unary negation and binary add/subtract/multiply/divide nodes; the immutable tree must be inspectable before backend lowering.
107. Existing three-argument `Expression(value, expression, parameters)` construction remains source compatible. Expressions without scalar-tree metadata remain valid for existing single-role lowering but do not gain new mixed-role portability.
108. Physical length/angle meaning belongs to the typed semantic use site, not to the scalar-expression node. The same scalar tree may therefore be rendered under different qualified physical roles without changing its authored arithmetic identity.
109. A mixed-role source remains one role-aware `ParameterIR` and one editable unitless native source parameter. A mixed parameter leaf used as length lowers with explicit `mm` context and the same leaf used as angle lowers with explicit `deg` context; single-role paths retain their existing spelling.
110. The #481 portable arithmetic subset is affine: add/subtract, unary negation, multiplication by a numeric literal and division by a non-zero numeric literal. Parameter×parameter, parameter÷parameter, numeric÷parameter, powers, text-only expressions and general derived-unit algebra remain fail-closed.
111. The #481 mixed-role Revolve proof must normalize `shared + 1` as a typed Sketch length while direct `shared` remains the Revolve angle; SolidCraft and Mitcad must lower the same semantic scalar tree independently through their central role-aware value boundary.
112. Exact pinned Mitcad v0.70.0 runtime qualification must execute that expression-bearing mixed-role Revolve with `shared=4`, radial height 5, X span 0..10 and angle 4 degrees, proving volume `25π/9` and X bounds [0, 10].
113. Public two-distance Chamfer must remain one semantic `ChamferIR`; Forge must not introduce a separate asymmetric feature node for the same authored operation.
114. `ChamferIR` may carry optional `distance2` and `flip`; `flip` is valid only when a second distance exists, while equal-distance Chamfer retains its existing IR and native spelling.
115. The first portable asymmetric slice is bounded to `PlacementIR(BoxIR)` plus exactly `FaceBoundaryIR(("top",))`. Other asymmetric face orientations and Extrude-based asymmetric Chamfer remain fail-closed until separately qualified.
116. SolidCraft typed asymmetric lowering must reproduce the accepted stable `solid.chamfer` command spelling with `distance`, optional `distance2` and authored `flip` while retaining the same semantic topology selection.
117. Mitcad v0.70.0 two-distance lowering must use native `ChamferSetDef` transport with `size.type=two_distances`, two independent distances, the selected native TOP face as private `reference_face`, and authored `flip`.
118. The native reference-face identity is backend replay transport derived from `FaceBoundaryIR`; it must never enter semantic Forge IR. Equal-distance replay must not require this additional binding.
119. Parameterized primary and secondary chamfer distances must remain separate editable length dependencies in both native backends.
120. Exact pinned Mitcad v0.70.0 runtime qualification must execute a 60×40×12 BOTTOM Box with TOP-boundary distances 0.18/0.65, prove unchanged bounds and volume 28788.32808 mm³, and retain saved native design/STL evidence.
121. A qualified primitive geometry/placement IR must compose through the existing recursive `BooleanIR` rather than requiring primitive-specific Boolean node types; the #496 slice adds `PlacementIR(ConeIR)` to the bounded primitive operand set.
122. Cone participation in `BooleanIR` must retain existing source-order `join`, `cut` and `intersect` semantics plus unchanged `FeatureRefIR` path meaning. No Cone-specific history vocabulary may enter semantic IR.
123. SolidCraft Cone Boolean lowering must reuse the already-qualified typed `solid.cone` command with the Boolean operation and target spelling used by stable Forge CSG.
124. Mitcad v0.70.0 Cone Boolean lowering must reuse the existing principal/offset support-plane transport. A private construction plane may precede the native Cone command, but semantic feature/history references must bind the Cone command rather than the helper.
125. Backend contract qualification must prove both an offset Cone cut and Cone join through the same `BooleanIR`; suppression/configuration lookup of `FeatureRefIR(("root", "tool"))` must resolve to the Cone feature when a helper plane precedes it.
126. Exact pinned Mitcad v0.70.0 runtime qualification must cut a d10→0 × 20 Cone whose BOTTOM is at world Z=5 from a 30×30×30 BOTTOM Box, retaining bounds [-15,-15,0]..[15,15,30], remaining volume `27000 - 500π/3`, and saved native design/STL evidence.
127. Public `Edges.VERTICAL` intent must normalize to an inspectable engine-neutral principal-edge selector; the first qualified form is `ParallelEdgeSetIR("Z")` and contains no SolidCraft XYZ picks or Mitcad topology names.
128. The first `FilletIR` contract is one positive constant radius over `PlacementIR(BoxIR)` plus `ParallelEdgeSetIR("Z")`. Other Fillet base/selector/radius modes remain fail-closed.
129. SolidCraft FilletIR lowering must derive the same four stable Box edge pick points from typed Box placement/dimensions and reproduce the accepted `solid.fillet` command spelling.
130. Mitcad FilletIR lowering must keep semantic edge intent out of native ids. Replay must query native edges with `geometry=true`, retain only straight line edges parallel to the selected principal axis, require exactly the expected set and bind their names privately before the native Fillet command executes.
131. Missing, malformed, duplicate-name or incomplete principal-edge topology must fail closed rather than selecting an arbitrary native edge subset.
132. A qualified `FilletIR` body result may feed the existing `BooleanIR` as target for the bounded Cone join proof; Forge must not introduce a Fillet-specific Boolean operation or history vocabulary.
133. The Fillet→Cone composition must preserve semantic source order `Box -> Fillet -> Cone`. Any Cone support construction plane and Mitcad edge-query/bindings remain backend transport and must not enter semantic history.
134. Exact pinned Mitcad v0.70.0 runtime qualification must execute a 50×40×20 BOTTOM Box with R2 Fillet over all four Z-parallel edges joined to an Ø18→Ø10 × 8 Cone whose BOTTOM is at world Z=18, proving bounds [-25,-20,0]..[25,20,26], volume `39680 + 338π`, exactly four bound parallel edges and retained saved native design/STL evidence.
135. `FilletIR.edges` may additionally reuse `FaceBoundaryIR` only for the first bounded `("top",)` Box selector; other face orientations, multiple faces and non-Box bases remain fail-closed.
136. SolidCraft TOP face-boundary Fillet lowering must reuse the typed face-boundary topology query/binding path and reproduce the stable `solid.fillet` command behavior for unchanged public SCPF source.
137. Mitcad TOP face-boundary Fillet lowering must reuse replay `bind_face_boundary_edges`, not principal-edge reconstruction; native face/edge names remain private transport and no Chamfer-style `reference_face` enters Fillet semantics.
138. The first face-boundary Fillet slice remains standalone. Existing Fillet→Cone `BooleanIR` composition remains qualified only for `ParallelEdgeSetIR("Z")`; face-boundary Fillet composition must fail closed.
139. Exact pinned Mitcad v0.70.0 runtime qualification must execute a 60×40×12 BOTTOM Box with R2 TOP-boundary Fillet, retain one watertight solid and saved native design/STL evidence, prove bounds [-30,-20,0]..[30,20,12], and preserve the first accepted native volume 28631.38638124875 mm³ as the regression value.
140. IR completion and backend completion are separate experimental states. A semantic slice may be IR-ready without Mitcad support when the generic CAD contract, typed normalization, pure IR boundary tests and stable typed SolidCraft lowering are complete.
141. A backend that does not support an IR-ready node must fail closed on that typed node. It may not fall back to raw `Shape.data`, reinterpret source authoring or force the semantic node back to `LegacyShapeIR` merely because that backend lags.
142. Mitcad lowering, Mitcad backend-contract tests and exact native Mitcad runtime qualification are independent backend milestones and may be completed in later backend-focused batches.
143. `docs/ir-coverage.md` is the permanent-`exp` compiler migration inventory. It must report semantic-family IR status separately from SolidCraft typed lowering, Mitcad lowering and native Mitcad qualification.
144. IR migration should prefer coherent family completion over one backend-qualified micro-slice per issue when the generic semantic contract can be widened safely and tested independently.
145. The first #525-policy batch is #519: explicitly positioned `Hole`, `CounterboreHole`, `CountersinkHole` and `ThreadedHole` over the bounded typed target migrate together to semantic `HoleIR`; Mitcad Hole support is not a #519 merge gate.
146. `HoleIR` must preserve authored Hole feature/history meaning directly; Forge must not replace it in semantic IR with an anonymous Cylinder Boolean merely because one backend may later implement Hole using cut geometry.
147. The #519 typed Hole contract carries a qualified Box/Hole target history, semantic entry point, through-all or positive finite depth, automatic-inward or fixed numeric non-zero direction, and the existing simple/counterbore/countersink/thread variant metadata.
148. Repeated explicitly positioned Hole-family features may form a recursive `HoleIR.target` history chain so source feature order remains semantic without requiring a generic Boolean node between Hole features.
149. Length-valued Hole dimensions retain authored Parameter/Expression dependencies. Countersink angle and direction remain fixed numeric intent in #519; parameter-driven widening must be separately typed rather than misclassified as length.
150. SolidCraft typed Hole lowering must reproduce the existing one-feature `solid.hole` behavior and command document for unchanged public source, including omitted through-all depth, omitted automatic-inward direction, recess fields and thread metadata.
151. Mitcad may remain unsupported for `HoleIR` after #519 and must fail closed on that typed node. Absence of Mitcad Hole lowering must not force valid #519 source back to `LegacyShapeIR`.
152. Topology-relative `Hole.on(...)`, attached Hole construction, feature-pattern/configuration composition and parameter-driven direction/countersink-angle semantics remain outside #519.
153. Typed body-producing semantic nodes must share one engine-neutral `BodyIR` result/history contract so downstream features can target the current typed body without pair-specific feature unions or backend body ids.
154. `BodyIR` is a semantic marker only; adding a node to that contract must not silently widen that node's own normalization or selector boundaries.
155. `ShellIR` must preserve one typed BodyIR base, one positive symbolic wall thickness and one non-empty `FaceSetIR` of cardinal open faces. `FaceSetIR` selects faces themselves and must remain distinct from edge-boundary `FaceBoundaryIR`.
156. SolidCraft ShellIR lowering must lower the typed body history first, resolve the requested current faces through native topology, then reproduce stable `solid.shell` command behavior without putting native face names in IR.
157. Typed SolidCraft body-history lowering must be shared by downstream feature consumers rather than duplicating a new target-pair lowering path for every composition.
158. `HoleIR.target` may reference any already-typed BodyIR result after #532; explicit Hole semantics remain unchanged and legacy/untyped targets still fail to normalize.
159. Nested topology queries in typed SolidCraft history must allocate deterministic non-conflicting replay variables from prior typed commands so stable source order remains observable.
160. Mitcad may remain unsupported for ShellIR and newly widened HoleIR histories and must fail closed rather than reinterpret source Shape payloads.
161. #532 does not itself widen vertical Fillet selector semantics or the existing Chamfer/Revolve/Boolean normalization boundaries merely because those result nodes implement BodyIR.
162. Native feature rectangular/circular patterns must be semantic BodyIR history nodes whose source features are engine-neutral `FeatureRefIR` paths into the typed pre-pattern body; native feature names/ordinals must not enter IR.
163. Pattern normalization may proceed only when every requested authored source feature resolves to typed semantic body history. A still-legacy source feature keeps the containing model legacy rather than manufacturing a native name in frontend normalization.
164. `ParameterIR` must distinguish the unitless semantic `count` role from length and angle, preserving direct symbolic pattern counts without assigning them millimetres or degrees.
165. Rectangular PatternIR must preserve one or two fixed direction vectors, positive integer/direct-Parameter counts, positive symbolic spacings, both alignments and both reversal flags.
166. Circular PatternIR must preserve one `AxisLineIR`, positive integer/direct-Parameter count, optional fixed/direct-Parameter sweep angle, alignment and reversal.
167. Generic `AxisLineIR` may represent either a principal X/Y/Z direction or one fixed finite non-zero XYZ vector with symbolic origin; existing Revolve normalization remains bounded to its separately qualified principal/in-plane semantics.
168. SolidCraft PatternIR lowering must derive native source-feature identity privately from the referenced typed history prefix and reproduce the stable `solid.pattern.rectangular` / `solid.pattern.circular` command document.
169. Mitcad may remain unsupported for PatternIR after #533 and must fail closed on those typed nodes.
170. Sketch-level rectangular pattern and mirror remain separate Sketch/Profile IR work and are not part of the native feature Pattern family.
171. Pattern-family completeness is judged on its own public controls once represented in IR; missing typed semantics in an unrelated source-feature dependency do not make PatternIR itself partial.
172. The public basic closed-profile constructor family must have explicit semantic IR for Circle, Polygon, Rectangle, RoundedRectangle and all five public Slot construction methods; native sketch command names must not define those IR nodes.
173. `RectangleProfileIR` and `RoundedRectangleProfileIR` must retain symbolic dimensions and semantic sketch-local centre/offset; RoundedRectangle additionally retains one positive radius below half the shorter side.
174. `SlotProfileIR` must retain the authored construction method, semantic points, positive symbolic width, optional fixed arc sweep and sketch-local offset rather than approximating the Slot as a PolygonProfileIR.
175. Public Sketch offsets for Circle and Polygon profiles must remain symbolic in typed IR; offset support must not numerically bake Parameter/Expression dependencies.
176. One typed standalone closed profile may feed positive, negative or symmetric ExtrudeIR. General attached/support-face Extrude and general multi-region composition remain separately bounded and must not be implied by profile-family completion.
177. Typed SolidCraft profile lowering must reproduce stable native rectangle/rounded-rectangle/Slot commands from semantic IR only. Parameterized straight Slots must preserve the stable dimension/constraint strategy without reading frontend Shape.data.
178. Existing concentric-Circle exact-region multi-profile behavior remains separately qualified; #534 must not broaden arbitrary multi-profile region selection merely to declare basic profile constructors complete.
179. Mitcad may remain unsupported for the new ProfileIR variants after #534 and must fail closed on those typed profiles.
180. Text and connected/open profile authoring belong to the broader Sketch entity family, not the basic closed-profile constructor family used for #534 completeness.
181. Within-component native feature placement must be semantic compiler data. `FeaturePlacementIR` distinguishes absolute XYZ placement from anchored placement and anchored placement retains parent anchor, child anchor and X/Y offset intent without native topology ids.
182. Public `X.MIN/CENTER/MAX` and `Y.MIN/CENTER/MAX` feature offsets normalize to `BoundOffsetIR(axis, reference, delta)`; the authored symbolic delta remains a length dependency and native coordinates are derived only during backend lowering.
183. HoleIR uses the generic feature-placement contract. Existing explicit `.at(...)` Hole semantics remain absolute placement, while the stable simple non-directional TOP/BOTTOM `.attach()` / `.on()` route becomes anchored typed Hole history over its typed BodyIR target.
184. SolidCraft anchored Hole lowering must reproduce the existing editable Sketch-circle plus cut-Extrude history rather than silently changing that stable path to `solid.hole`. Unsupported side-face or broader anchored Hole variants remain fail-closed.
185. `PlasticFeatureIR` represents one authored plastic/mechanical history feature over typed BodyIR plus generic FeaturePlacementIR. Its typed specifications are Lip, SnapFit, Boss and Rest; Forge must not rewrite them as anonymous primitive CSG.
186. Plastic feature dimensions and placement offsets retain authored Parameter/Expression dependencies in IR. Hook, direction and along vectors in #544 remain fixed finite non-zero semantic vectors; parameter-driven vector widening is not implied.
187. SolidCraft resolves TOP/BOTTOM/INNER_BOTTOM plastic placement only after lowering typed body history. INNER_BOTTOM wall position must come from typed ShellIR semantics; the backend must not inspect legacy Shape.data to recover shell thickness.
188. SolidCraft typed PlasticFeatureIR lowering must reproduce the existing `plastic.lip`, `plastic.snap_fit`, `plastic.boss` and `plastic.rest` command contracts for accepted public source.
189. Mitcad may remain unsupported for FeaturePlacementIR consumers after #544 and must fail closed on HoleIR/PlasticFeatureIR forms it cannot lower. Mitcad support is not an IR-ready merge gate.
190. General side-face feature placement, attached Cylinder placement, assembly occurrence placement and rotated component frames remain separate semantic layers; #544 does not conflate within-component feature placement with assembly attachment.
191. Hole semantic normalization is independent from backend anchor/variant support. Current public Hole-family `.at(...)` and `.on()/attach()` authoring over a typed target must produce `HoleIR` when its dimensions and fixed direction are otherwise valid.
192. Anchored HoleIR retains the generic FeaturePlacementIR parent/child anchor and offset intent. SolidCraft capability errors for side-face, directional or non-simple anchored forms must occur during lowering rather than by reverting the model to LegacyShapeIR.
193. SolidCraft must lower simple non-directional anchored Hole on both TOP and BOTTOM rectangular support faces. TOP retains the stable editable Sketch-circle + cut-Extrude spelling; BOTTOM finite depth drills in the positive body-normal direction from the bottom entry face.
194. Through-all TOP/BOTTOM simple anchored Hole remains one full body-thickness cut whose semantic result is independent of which supported entry face authored the request.
195. `countersink_angle` is an angle-valued Hole use site. Direct Parameters in that field remain semantic ParameterIR with role `angle` and lower to native degree units; Forge must not classify them as millimetre dimensions.
196. The stable SolidCraft compatibility classifier must use the same degree role for countersink-angle Parameters so typed and compatibility lowering agree on editable native units.
197. Fixed non-zero Hole direction vectors remain engine-neutral orientation intent. #550 does not introduce parameter-driven vector components as a new editable direction contract.
198. Patterning, configuration/suppression and backend-native Hole implementation are separate semantic/backend families; their remaining gaps do not make the Hole feature family itself incomplete once current Hole meaning and placement intent are represented.
199. Public Sketch entity authoring must normalize independently from Sketch support and solid consumers into one support-independent `SketchEntityGraphIR`.
200. Closed `Sketch.profile(...)` line/arc geometry uses `ConnectedProfileIR` plus semantic line, three-point-arc and center-point-arc segments; open `Sketch.chain()/line()` uses `OpenChainIR` plus line/tangent-arc segments. Native curve ids and command names are forbidden from these nodes.
201. `Text2D` inside a Sketch is semantic `TextEntityIR(text, height, font, position)`; its authored height and insertion coordinates retain length dependencies.
202. Sketch pattern/mirror source identity is represented by Sketch-local `SketchEntityRefIR(kind, index)`, resolved while authored Python identity is still available. Backend curve ids, replay names and command indexes are not semantic source identity.
203. `SketchRectangularPatternIR` retains authored count/spacing/directions/alignment/reversal semantics and `SketchMirrorIR` retains local X/Y mirror-axis intent. Sketch pattern counts are unitless/count Parameters; spacings remain length-valued.
204. SolidCraft may translate semantic Sketch entity refs to private `$sketch_*` bindings during lowering. Existing backend limitations, including connected-profile pattern/mirror input, fail closed without invalidating the typed Sketch graph.
205. #560 completes the current public Sketch entity/operation semantic surface only. Sketch support/reference frames, RegionIR composition and consuming Extrude/Revolve/Sheet Metal features remain separate layers owned by later batches.

## SCPF native associativity

1. When SolidCraft exposes a durable native reference for editable intent, Forge
   must preserve that relationship instead of snapshotting it to fixed
   coordinates merely for compilation convenience.
2. `Shape.fold()` supports both the historical fixed-point form and an
   associative straight line returned by `Sketch.line(...)`.
3. The associative fold form must lower to native `sheet.fold`
   `sketch` + `curve` references and retain symbolic endpoint dependencies.
4. Native qualification must prove that changing a driving parameter in a saved
   SolidCraft design rebuilds the fold successfully.

## SCPF standalone Sketch regions

1. A standalone `Sketch` may contain one or more supported closed profiles;
   Forge must lower all authored loops into one native SolidCraft Sketch rather
   than split them into unrelated sketches/features.
2. `Sketch.extrude(..., profiles=..., exact_regions=True)` is the public
   region-selection contract for nested or otherwise ambiguous closed loops.
   User code selects with fixed sketch-local points and never names native
   profile/curve ids.
3. Nested closed loops must preserve SolidCraft region semantics so an inner
   loop may become a hole in the explicitly selected outer region.
4. Existing one-profile standalone Sketch extrusion remains source- and
   command-compatible.
5. Multi-profile extrusion does not broaden other features implicitly:
   `Sketch.revolve()` remains limited to exactly one closed profile until a
   separately qualified contract changes it.
6. Native qualification must prove one Sketch contains both loops, one native
   extrusion consumes the intended annular region, and saved-design parameter
   changes preserve that region association.

## SCPF configuration tables

1. Author one native editable configuration table around a finished Shape, component occurrence or Assembly, with named rows and an explicit active row.
2. Parameter columns refer to existing native parameters; suppression columns refer to exact Forge feature identities, never caller-supplied native IDs.
3. Resolve suppression columns from actual replay-returned native feature identity; callers never supply SolidCraft feature ids. The saved design must retain SolidCraft's native feature-id references.
4. Preserve stable authored row identity and verify deterministic native row behavior across a clean rebuild.
5. Parameter columns must remain generic native dependencies: dimensions, assembly occurrence placement and other associative uses all switch through the same Param contract.
6. A parameter published by a reusable child component must remain addressable by a root `Configure(...)` table around that component occurrence or an Assembly; multiple occurrences sharing the same published parent parameter must not create unrelated native parameters.
7. Verify all authored cells, active-row state and row switching on a reopened saved design, including parameter, placement and suppression changes. Unsupported configuration intent must fail explicitly rather than be emulated with Python variants.
8. When flexible-fit state is the table's only configuration axis, use the conventional row names `Free` for uninstalled manufacturing/print geometry and `Installed` for mounted working geometry. When a parent already owns an independent row axis such as Small / Medium / Large, a native Configuration Rule named `Installed` may drive the same configured fit parameter; disabling that rule restores the active row's Free/base expression. Do not create a Cartesian row table merely to combine those axes.
9. Configuration-driven derived geometry must remain native when it uses public symbolic CAD math. The public API must cover min/max, sqrt, abs, round, floor and atan without exposing raw SolidCraft expression strings or private expression helpers.
10. Symbolic multiplication, division and numeric powers must preserve all source Parameter dependencies so native configuration changes recompute the resulting feature inputs.
11. Native Sketch revolve must accept a typed shifted/custom AxisLine whose origin can remain parameter-driven. The resulting revolve must remain one exact Forge feature Shape usable by Suppress(feature).
12. A shifted revolve axis and its standalone Sketch plane must remain explicitly coplanar; Forge must reject mismatched axis/plane intent instead of silently transforming or baking coordinates.
13. `Configure(...)` may author ordered native Configuration Rules in addition to rows. The initial typed rule contract is `ConfigRule(..., condition=Always(), effect=DriveParameter(...))`; callers never write raw SolidCraft rule JSON.
14. A `DriveParameter` target must also be an explicit `Param(...)` column of the same table. Rule enablement uses SolidCraft's native `enabled` checkbox and must not be emulated as a boolean/numeric model parameter.
15. Rule enablement and row activation are orthogonal native state. Saved-design qualification must prove that disabling a drive restores the active row value and that switching rows does not silently change the rule's enabled state.
16. A rule may drive a shared parent parameter published into reusable child components, so one Assembly rule can update every occurrence using that same native dependency without duplicating bodies or Python histories.
17. A reusable component may explicitly publish one already-authored suppressible feature with `Shape.export_feature(name)`; the export name is component-local Forge identity and must never be treated as a SolidCraft history id.
18. `ModelInstance.feature(name)` returns a definition-level Forge reference. A parent/root `Suppress(...)` must resolve that reference against the canonical compiled reusable definition, so separately constructed or copied occurrences of the same definition share one suppression target deterministically.
19. Component feature references must fail explicitly when the export is missing or the referenced definition is not part of the configured design. Saved-design qualification must prove Small/Medium suppression and Large presence after reopen while ordinary parent-driven child parameters continue to recompute natively.

## SCPF revolute relationships

1. `ModelInstance.attach(...)` must preserve its existing automatic rigid/planar behavior when no explicit relationship kind is requested.
2. An explicit `kind="revolute"` relationship must lower to SolidCraft's native `joint.create(type="revolute")`; Forge must not replace it with a fixed occurrence rotation.
3. Revolute authoring supports a fixed initial angle in degrees, optional finite minimum/maximum angular limits, native joint-origin flip and an optional native joint name.
4. Parent and child references reuse the existing `Anchor`, `AnchorFrame` and `AnchorTopology` attachment model; Forge must not introduce a second joint-origin vocabulary.
5. Native qualification must inspect the stored joint type/value/limits and drive the saved design to a second angle so motion is proven, not only command generation.
6. Additional moving joint types remain consumer-driven future work.

## SCPF display appearance

1. `Shape.with_appearance(color)` assigns one display-only color to the final body.
2. The initial public color contract accepts a fixed `#RRGGBB` value.
3. Appearance authoring must lower to native SolidCraft `appearance.assign`.
4. Appearance authoring must not create or mutate physical material, density or BOM metadata.
5. Native qualification must inspect the saved appearance chain after replay.
6. The first contract remains body-wide and opaque; face-level/PBR appearance work is consumer-driven future scope.

## SCPF native chamfer

1. Existing `Shape.chamfer(distance, edges=...)` remains the equal-distance,
   source-compatible public form and must keep its existing native command
   shape when no asymmetric options are requested.
2. A consumer may supply `distance2=` to author SolidCraft's native
   two-distance chamfer as one history feature; Forge must not approximate the
   taper with cutters, lofts or multiple chamfers.
3. `flip=True` selects the opposite adjacent-face ordering for the two native
   distances and is only valid when `distance2` is supplied.
4. Both distances may retain normal Forge Parameter/Expression dependencies and
   must remain editable in the saved SolidCraft design.
5. Equal- and two-distance chamfers use the same existing edge-selection
   vocabulary, including replay-resolved face boundaries and named
   Polygon2D profile edges.
6. Native qualification must prove one ChamferFeature, both driving
   parameters, saved-design recomputation and geometry that differs from the
   corresponding equal-distance chamfer.

## SCPF topology selection

1. `Faces.TOP/BOTTOM/LEFT/RIGHT/FRONT/BACK` is the shared world-cardinal
   surface vocabulary for within-component feature intent.
2. `Edges.from_faces(...)` selects the complete boundary of one or more named
   planar faces without caller-supplied XYZ edge picks.
3. Native lowering must query SolidCraft topology and consume returned face and
   edge identity; Forge must not predict browser names or topology ids.
4. TOP/BOTTOM map to +/-Z, LEFT/RIGHT to -/+X and FRONT/BACK to -/+Y. Therefore
   the broad end faces of an XZ profile extruded along Y are FRONT/BACK.
5. Existing edge selectors remain source-compatible.
6. A public face intent may be accepted even when a particular consumer's
   lowering is not yet qualified; that failure must identify the native
   placement/topology limitation rather than invent a second selector model.
7. Native qualification must cover one-face Box boundary chamfer, two-face XZ
   extrusion boundary chamfer and interoperability with existing shell/on
   consumers.

## Native component drawings

1. A technical drawing is final design presentation state; it must not become part
   of a reusable component definition or be duplicated implicitly by
   `.copy()`.
2. `ModelInstance.with_drawing(...)` may create a one-component design drawing;
   `Assembly.with_drawing(target, ...)` selects one occurrence already owned by
   the completed Assembly.
3. Forge must lower drawing intent to SolidCraft's native drawing commands.
   SolidCraft owns sheet/view/dimension/note/title-block representation; Forge
   may expose generic consumer controls for native standard-view placement,
   scale, qualified display style, annotations and metadata but must not draw
   replacement graphics.
4. Drawing lowering must address components, occurrences, sheets, sources and
   views through replay-bound SolidCraft result ids; browser names and predicted
   ids are forbidden.
5. Component drawings default to SolidCraft's native ISO A4 part template and
   explicitly set the first sheet to landscape. Callers may select the native
   ISO A3 part template; Forge preserves that paper size and landscape policy.
6. The public drawing authoring contract must support native `title_block_style="compact"` selection in addition to the normal built-in title block, while preserving existing template behavior.
7. The public drawing authoring contract must support explicit standard-view
   placement/scale, a qualified per-view shaded presentation, drawing
   properties, title-block overrides, one revision row, sheet notes and native
   dimensions needed by a Wall-Hook-class part drawing.
8. Omitting a view style keeps SolidCraft's normal line presentation.
   `DrawingView(visual_style="shaded")` is the qualified override for a
   pictorial/isometric consumer view; Forge must not invent its own shaded
   renderer.
9. Dimension authoring must remain native and topology-resolved. Forge may expose
   model-space picks for SolidCraft linear, parallel-face and radial dimensions;
   it must not convert dimensions into free lines/text. Stable face-to-face
   dimensions are the preferred overall-size form where fillets remove corners.
10. Every declared drawing is retained in the native `.sc` design and the SCPF
   builder exports a vector PDF, a native static PNG of the exact replay-bound
   sheet and the final native `drawing.inspect` JSON below the implementation's
   `drawings/` output directory.
11. Build filesystem paths are builder-owned. Model/compiler intent may declare
    safe relative drawing artifact names and replay-bound ids, but must not embed
    repository/build-root paths.
12. The SCPF builder must validate the fully-authored native drawing inspection
    against the compiled drawing intent before publishing PDF/PNG evidence:
    orientation, view count, dimension count, note count, properties, revision,
    authored title-block values and requested compact title-block geometry must
    survive native replay.
13. Drawing qualification must also include an approved visual baseline of the
    generated native sheet. Image comparison is generic verification behavior,
    not a drawing renderer; it consumes the already-generated sheet PNG.
14. Native qualification must execute drawing creation/export against the pinned
    SolidCraft runtime, not only compare generated JSON.
15. Centre marks/centre lines remain unavailable until the pinned SolidCraft
    command registry exposes native authoring for them. Balloons and parts lists
    remain later consumer requirements; Forge must not fake them.
16. Guide, Cheatsheet and API Reference must be sufficient for an external CAD
    repository to reproduce the qualified drawing workflow without reading Forge
    internals.
17. One physical owner with purpose `[example, verification]` demonstrates the
    complete flow. Pages must not embed/auto-open drawing PDFs; it may load the
    durable static PNG sheet preview and expose explicit PDF actions.

## SolidCraft reference evidence

1. Every tested SolidCraft version must have one canonical command-registry
   snapshot under `docs/reference/solidcraft/<version>/`.
2. The snapshot must be captured from the exact immutable runtime image
   qualified by Forge, never from a hand-selected command subset or an
   unpinned local installation.
3. Canonical capture and runtime comparison are owned by
   `modules/solidcraft-reference/`; retired top-level script/orchestration
   layouts must not be reintroduced.
4. The checked `commands.json`, generated `commands.md` and `SOURCE.md`
   provenance must remain deterministic and mutually consistent.
5. Forge CI must compare the checked registry with the root-pinned immutable
   SolidCraft runtime whenever the reference module/reference tree is selected.
6. When a typed native command contract gates Forge API design, retain the exact
   targeted `engine.describe` result below
   `docs/reference/solidcraft/<version>/describe/`; do not infer missing
   condition/effect schemas from the short command-registry description.
7. Targeted describe evidence must be captured from and compared back to the
   same root-pinned immutable runtime as the command registry. A checked schema
   may not be hand-authored from guessed SolidCraft parameter or effect names.

## Manufacturing visual verification

1. Native manufacturing-only features must be visually qualified from their authoritative manufacturing output rather than fabricated B-rep geometry.
2. SolidCraft sheet perforation fields use native flat-pattern/DXF semantics; Forge must not replace them with repeated solid holes solely to make a 3D preview look perforated.
3. Manufacturing visual evidence must retain the native exported artifact plus deterministic Actual/Goal/Overlay review images and a model-owned approved geometry contract.

## Verification

1. Generic `cad_verification` source is local under `modules/verification/`.
2. Model-specific expectations remain with the physical model owner.
3. A migration slice is accepted only with retained evidence equivalent to the historical Forge baseline for the behavior under migration.
4. Every model owner whose `model.yml.purpose` contains `verification` must appear in the public Verification catalogue. Every owner whose purpose contains `example` must appear in Examples. An owner with both purposes appears in both views while remaining one physical owner.
5. Verification detail pages must state the human verification intent before implementation detail. Durable measurement/check evidence remains available but may be collapsed by default; owner-local explanatory content stays source-owned and Pages must not execute CAD to produce it.
6. Every verification owner must state the contract it proves and retain the minimum evidence capable of catching a meaningful regression in that contract; successful command generation, replay or model build is not sufficient by itself when visible or structural output could still be wrong.
7. Visibly meaningful geometry or state must have deterministic review views and an approved expected visual baseline, with structural/geometry checks where topology or shape is part of the contract; Pages must make retained expected-vs-actual evidence reviewable rather than generating it.
8. Native feature/history contracts require saved-design mutation or inspection as appropriate. Manufacturing-only geometry must be checked from its authoritative manufacturing representation, and negative/runtime contracts must record an explicit expected failure or cross-runtime result rather than treating a missing artifact as evidence.

## Migration

1. The historical Forge repository remains the known-good comparison source until parity is demonstrated.
2. Migrate one physical model end-to-end, then five, then ten, before enabling the remaining graph.
3. Do not delete the historical external verification repository until all real consumers have migrated.
4. Do not copy historical scripts, builders or site code merely because they exist. Re-home only behavior with a real owner.
5. Release behavior remains separate from model migration and Pages.
6. Product-changing stable commits require full `build/main` evidence with explicit library qualification, all active model owners selected and matching successful model provenance.
7. A metadata-only release may reuse that retained full product evidence only when the requested release SHA is on its linear first-parent history and every intervening commit changes only `CHANGELOG.md` and `cadlib/pyproject.toml:project.version`.
8. Release branches must be created from stable `main`, target `main` directly, select only the library plus release capability, and fail closed on any product/source/model/dependency/build-config change.
9. Release publication is explicit and owner-issued through `/release vX.Y.Z <40-character-main-sha>`; the requested SHA must still be exact current stable `main`.
10. Generic release publication is delegated to released `tool.py.lib.ci`; Forge owns only package/changelog/blocker/SolidCraft metadata validation.
11. After a stable-only release commit, synchronize `main -> dev` through merge policy and never rebase the shared development branch.
12. The migrated `0.15.0` package version is not a canonical release. Every published Forge version must be newer than `0.15.0`.

## Documentation

1. Keep `docs/plan.md` as the source of truth for unfinished work.
2. Keep `docs/handoff.md` usable as a standalone continuation message.
3. Use Hugo/Hextra; Pages never runs CAD.
4. API, guide and reference content becomes normal documentation. CAD owners are projected into the Examples and/or Verification sections according to `model.yml.purpose` without duplicating source or generated CAD artifacts.
5. Pages must project the public SCPF API Reference without importing or executing `scpf`; retained authored reference metadata is statically validated against `cadlib/src/scpf`.
6. Historical public API symbol routes remain case-sensitive during migration parity (for example `/reference/Faces/` and `/reference/Shape.at/`).
7. Verification `coverage`, `results` and `joint-anatomy` pages are source/evidence projections: coverage and authored explanations live in `docs/`, while current result status comes only from durable `build/<scope>/models/**` evidence.
8. The reusable model catalogue/detail presentation is adopted from `template.cad.library`; Forge owns only consumer-specific Guide, API Reference, Cheatsheet and Verification explanatory content.
9. A fixed OLD-vs-NEW Pages parity manifest must verify the retained historical routes and identifying content before the migration is accepted.
10. The public Verification catalogue must group verification owners by the source-owned `docs/verification/sections.yml` taxonomy and order both sections and model cards by their declared priorities; unknown or missing verification sections fail closed.
