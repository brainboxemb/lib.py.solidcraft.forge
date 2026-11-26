# Forge requirements

## Repository

1. Preserve the public SCPF Python API and import name `scpf`.
2. Use the corrected CAD library architecture rather than reproducing historical Forge-local orchestration.
3. Keep source ownership explicit: library, physical models, generic modules, documentation and generated evidence are separate roles.
4. Use `main` as stable, `dev` as normal development integration and optional permanent `exp` as isolated experimental integration. `exp` is not a release source and may not promote directly to `main`.
5. Generated CAD output is owned by `build`; Pages presentation is owned by `gh-pages`. Permanent `main`, `dev` and optional `exp` outputs must remain isolated by source scope. Pages must not duplicate generated CAD artifacts.

## Models

1. `models/<id>/` is the physical selection/publication owner.
2. One owner may declare multiple CAD-engine implementations.
3. Engine implementations are local to the owner and must not become sibling model owners.
4. `model.yml.purpose` may contain `example`, `verification`, or both.
5. Owner-local verification expectations apply independently to every declared implementation unless a future real model demonstrates a justified override.
6. Physical model dependencies name owner ids and downstream dependents must be selected transitively.

## CAD execution

1. Reuse only the released `reference` and `solidcraft` runtime roles from `docker.cad.solidcraft v0.3.6` until a separately qualified upgrade exists.
2. Standard reference builders are PythonSCAD, pyBOSL2, CadQuery and build123d.
3. SCPF compilation is consumer-owned and feeds the generic SolidCraft command builder; do not teach generic builders Forge semantics.
4. SolidCraft executes in its lightweight runtime; generic mesh verification executes in the reference runtime.
5. CI batches compatible implementation work and does not start one Docker container per model implementation.

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
8. Flexible-fit physical states use the conventional row names `Free` for uninstalled manufacturing/print geometry and `Installed` for mounted working geometry. These are model configurations, not render/display-state labels.
9. Configuration-driven derived geometry must remain native when it uses public symbolic CAD math. The public API must cover min/max, sqrt, abs, round, floor and atan without exposing raw SolidCraft expression strings or private expression helpers.
10. Symbolic multiplication, division and numeric powers must preserve all source Parameter dependencies so native configuration changes recompute the resulting feature inputs.
11. Native Sketch revolve must accept a typed shifted/custom AxisLine whose origin can remain parameter-driven. The resulting revolve must remain one exact Forge feature Shape usable by Suppress(feature).
12. A shifted revolve axis and its standalone Sketch plane must remain explicitly coplanar; Forge must reject mismatched axis/plane intent instead of silently transforming or baking coordinates.

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
