# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

The declarative verification path and runtime batching are proven.

- #537 migrated the previous ten Qualification cases.
- #484/#541 removed per-case CAD runtime startup.
- Forge now uses one light SolidCraft batch runtime and one heavy reference
  runtime containing PythonSCAD, pyBOSL2, CadQuery, build123d and CADCraft.
- runtime `v0.3.2` is immutable and green;
- the representative batched Forge run is green;
- `lib.py.cad.verification 0.13.1` is released at
  `3600fa6145f11d05d6f27a342df0c24e075905eb` and provides the remaining
  generic face-count, center-of-mass and sketch-DOF expectation fields.

Current source inventory before #542:

- 21 declarative Qualification cases;
- 11 procedural `verification/verify_model.py` cases.

The current public Pages state remains preserved on
`backup/gh-pages-before-f11-2026-11-20`. Do not cut Pages over until current
durable evidence again covers the 32-case public Qualification catalog.

## Current goal

Complete #542: migrate the next ten procedural Qualification cases to the
released declarative verification path.

Batch #542 contains exactly:

1. bracket;
2. circle-negative-extrude;
3. circular-feature-pattern;
4. eight-flightcase-corners;
5. primitive-csg;
6. rectangular-pattern;
7. round-top-sketch;
8. rounded-rectangle-sketch;
9. selective-profile-extrude;
10. slot-family.

After this batch only `sketch-pattern-mirror` remains procedural. It is kept
separate because its saved-design contract contains a true baseline-to-mutation
relationship check rather than an absolute expected value.

## Required proof for #542

- all ten cases use data-only/declarative `verification/verify.py`;
- no `verification/verify_model.py` remains for those ten;
- all existing geometry, parameter, sketch, timeline and saved-design contract
  semantics are preserved;
- all ten use `template: forge-model-declarative` and `process: true`;
- all ten have four nested independent reference child configs;
- the shared SolidCraft/reference verification batches remain the runtime
  boundary;
- all ten model verifications and all forty reference results pass;
- durable main output gains current evidence for the ten migrated cases;
- inventory after merge is 31 declarative and one procedural case;
- Pages remains unchanged.

## Execution order

1. Pin released `lib.py.cad.verification 0.13.1`.
2. Replace the ten procedural verifiers with declarative model data.
3. Add the forty nested reference child configs and enable processing.
4. Run one PR proof for the complete ten-case batch using the shared runtime
   batches.
5. Correct only demonstrated contract/data errors; do not add Forge-local
   verification mechanics.
6. Merge, prove durable main output, then migrate the final
   `sketch-pattern-mirror` case separately.
7. Only after all 32 cases have current durable evidence continue #497/#366
   Pages work.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #542 Migrate next ten Qualification cases to declarative verification | now | Current migration batch; released verification 0.13.1 supplies all generic absolute-value checks needed by these ten. |
| #432 Use released declarative CAD verification in model verification | now | Parent migration issue; #542 leaves only sketch-pattern-mirror procedural. |
| #497 Publish stable Pages from the generic build/main baseline | blocked | Wait until all 32 current Qualification cases have durable current evidence. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Final Pages lifecycle follows #497. |
| #391 Extract reusable CAD verification library from Forge | effectively complete but still open | Generic verification ownership is external; only consumer migration remains. |
| #481 Remove stale Forge development branches | blocked | Current connected tooling cannot safely delete stale refs. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by released runtime batching and measured #484 work. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to superseded qualification architecture. |
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
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Major Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:

`#542 -> final sketch-pattern-mirror migration -> #497 stable 32-case Pages -> #366 final Pages lifecycle`.
