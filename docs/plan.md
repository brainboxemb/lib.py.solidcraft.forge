# Forge repository plan

This file contains only current unfinished repository work.

Completed work is removed from this plan after it is merged. Permanent design
decisions belong in the normal repository documentation; Git history and closed
issues preserve the history.

## Current work: finish the CAD-CI migration

### 1. Complete the Forge verification contract — #378

The 32 historical model cases now have `model_verify`, but that is only the
native model layer.

Complete the already-agreed verification contract:

- keep the existing native geometry/history verification;
- keep saved-design mutations and post-build inspections;
- restore `verify_references`;
- restore independent PythonSCAD / pyBOSL2 / CadQuery / build123d reference
  execution and comparison where required;
- restore render/visual evidence and visual baseline regression;
- restore independent expected-shape/goal-overlay evidence;
- restore `build_diagrams`;
- add the final `verification-summary` / `collect_results` fan-in without
  rerunning model work.

Do not recreate the old qualification runner or Q-number vocabulary. Reuse
`tool.cad.ci` for execution and `lib.py.cad.verfication` for generic
verification mechanics.

Remove this section when #378 is complete.

### 2. Make accepted verification output durable on the build branch — #366

A verification result is complete only after its accepted item output has been
written durably to the `build` branch under the corresponding source item path.

Proceed incrementally:

1. prove one model end-to-end: `model_verify -> accepted item output -> build`;
2. extend the same mechanism to all required verification items;
3. confirm partial updates replace only affected item output;
4. confirm reused/CURRENT items retain their accepted durable output.

Do not use or recreate the old central `qualification/` build layout.

When durable build storage is complete, replace this section with the remaining
Pages work only.

### 3. Publish Pages from accepted durable build output — #366

After durable item output is authoritative:

- publish stable and preview Pages through `tool.cad.ci`;
- consume accepted build output instead of rerunning technical verification;
- keep Forge-owned site content and presentation in Forge;
- remove superseded Forge-owned branch publication code.

Remove this section when #366 is merged.

### 4. Final migration audit

After the previous sections are complete:

- confirm no obsolete qualification/CI architecture remains active;
- run the complete intended verification graph;
- confirm unchanged targets are reusable/CURRENT where expected;
- confirm accepted verification output is present on `build`;
- confirm the active documentation matches the final implementation.

When this audit passes, remove this section. If no other work is planned,
`docs/plan.md` may then contain only the next repository work or be removed.

## Open issue assessment — 2026-11-19

This snapshot determines priority; an open issue is not automatically current work.

| Issue | Status | Assessment |
| --- | --- | --- |
| #416 Make docs/plan.md the repository work source of truth | now | Repository-process housekeeping. Close after the plan/AGENTS rule is merged. |
| #391 Extract reusable CAD verification library from Forge | now / dependency | Required to complete #378 without rebuilding reusable verification logic inside Forge. The library itself must be completed independently first. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now / blocked | Main Forge completion task. Continue as soon as the required `lib.py.cad.verfication` capabilities are released. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Starts after #378 verification output is complete and accepted. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Forge API defect, not part of the immediate CI/verfication completion chain. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | Useful CLI quality work, but not a blocker for finishing verification migration. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Product/API work after the current verification/CI migration. |
| #354 Support standalone sketch extrusions as boolean operands | later | Product/API work after the current verification/CI migration. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Coverage backlog, not current migration work. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog; return after migration completion. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to the superseded qualification architecture. Reassess after #378/#366 and close or rewrite only if a real current need remains. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement, not required for the current minimum migration path. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Model/API investigation independent of the immediate CI/verfication completion chain. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete / reassess | The old qualification/runtime design has changed substantially. Reassess measured performance only after the final CAD-CI graph is active. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog after the generic verification path is restored. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Product behavior issue, independent of migration. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog, independent of migration. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate execution chain:
`lib.py.cad.verfication -> Forge #378 -> Forge #366 -> final migration audit`.

