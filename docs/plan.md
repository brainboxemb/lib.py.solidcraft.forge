# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

The central CAD-CI, durable `build/main` store and generated `gh-pages`
publication path are implemented and green.

The first live Pages cut-over exposed presentation regressions. PR #566 and
PR #569 repaired the generic Verification case-sheet layout, restored all 36
conceptual setup diagrams and removed the misplaced engineering-diagram gallery
from the Verification catalog root.

A second live cut-over then exposed a deeper verification-semantic regression:
many current pages report `Visual N/R` even though the preserved Qualification
site had approved visual verification for those same cases.

The live Pages source has therefore been rolled back again to
`backup/gh-pages-before-f11-2026-11-20`. GitHub Pages rollback run
`44890618855` completed successfully from backup commit
`127adb3900cdc9ca6194edb1102ea7d505316295`.

Issue #378 is reopened because its F7-F9/F11 full-catalog visual contract was
never completed:

- 36 active Verification cases exist;
- all 36 have model-local declarative `verification/verify.py`;
- all 36 have current `verification/reference_geometry.json`;
- the preserved legacy visual baseline manifest contains approved baselines for
  all 36 current cases;
- only 5/36 current cases have model-local `verification/visual.json`;
- #430 proved the visual path for the first five models only;
- #432 completed procedural-to-declarative model verification but did not finish
  F7-F9 for the remaining catalog;
- #497 later intentionally mapped absent visual policies to `Visual N/R`.
  Live review rejects that semantic downgrade.

#366 remains open but is blocked on #378.

## Current goal

Complete the original #378 visual-verification contract for every active
Verification model without recreating the retired Qualification runner.

For all 36 active cases:

1. preserve/migrate the approved model-local visual baseline;
2. declare the historically required views;
3. retain current SolidCraft render and camera evidence;
4. run released `lib.py.cad.verification` image regression;
5. produce expected-shape goal and overlay evidence from model-local expected
   geometry;
6. require visual PASS in semantic verification;
7. keep presentation previews separate from verification truth.

The existing visual implementation is the architecture. Do not introduce a new
visual engine or central cross-model baseline registry.

Historical baseline pixels may be migrated byte-for-byte into model-local
encoded baseline payloads, as already proven by the existing four migrated
payload-based models. Generic decode/image/projection mechanics remain in the
released verification library.

The old central `qualification/geometry_contracts.py` is migration evidence,
not a source to restore. Required views, expected boxes/features and baseline
provenance must end up model-local under each
`examples/<slug>/verification/` directory.

## Verification parity audit

Current hard findings:

- legacy approved visual baselines for current cases: 36/36;
- current `visual.json` policies: 5/36;
- missing current visual policies: 31;
- current reference-geometry contracts: 36/36;
- cases declaring `bounds_sufficient: false`: 18/36;
- cases retaining explicit surface-distance probes for independent reference
  geometry: 14/36.

The surface-distance probes were primarily reference-mesh verification evidence
in the old runner and remain present in current `reference_geometry.json`.
The immediate semantic regression is the missing native visual verification,
not loss of those reference probes.

Representative failure:

`anchored-holes` currently reports
`Integration PASS · Native model PASS · Geometry PASS · Saved design N/R · Visual N/R`,
while the preserved site had required Top/Right/Iso visual verification with
Actual/Goal/Overlay evidence.

## Execution order

1. [#378, now] Correct requirements/design so every active Verification model
   requires a model-local visual policy and semantic visual PASS.
2. [#378] Migrate the 31 missing approved legacy baseline/view policies into
   model-local verification data without re-encoding approved baseline pixels.
3. [#378] Restore model-local expected-shape boxes/features and historically
   required view overrides.
4. [#378] Run the complete 36-model visual verification path and fix any real
   render regressions rather than weakening thresholds or silently reapproving
   baselines.
5. [#378] Prove the semantic summary requires visual PASS for all 36 active
   cases and publish a complete durable `build/main` baseline.
6. [#366, blocked] Regenerate and inspect `gh-pages` from that complete
   verification baseline.
7. [#366] Only then retry the live Pages cut-over and verify public routes.
8. [#481, next] Remove stale development branches after #366 is proven live.

## Open issue assessment — 2026-11-21

| Issue | Status | Assessment |
| --- | --- | --- |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Reopened. F7-F9/F11 were completed only for the five-model proof, not the full catalog. Restore visual verification for all 36 active cases. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Durable publication and page presentation are repaired, but live review exposed missing visual-verification semantics. Backup Pages stays live until #378 is complete. |
| #481 Remove stale Forge development branches | next | Wait until #378/#366 are proven; preserve active/generated/rollback branches meanwhile. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by released runtime images, batching and later one-runner timing work. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to the superseded Qualification architecture and old reuse strategy. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Independent Forge API defect. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | Independent CLI quality work. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Independent product/API work. |
| #354 Support standalone sketch extrusions as boolean operands | later | Independent product/API work. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Independent model/API investigation. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Independent product behavior. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | `custom-anchor` remains the expected-rejection fixture until this capability exists. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Major Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:

`#378 full-catalog visual verification -> #366 generated-site review/live cut-over -> #481 branch cleanup`.
