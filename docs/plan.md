# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Complete #438: remove the released `lib.py.cad.verfication` package itself
from the immutable SolidCraft runtime while preserving efficient repeated
verification.

Stable heavy dependencies remain in the runtime. The exact released
verification wheel is built once by CAD-CI and reused by all model/reference
verification items.

PR #441 updated the embedded library to 0.10.0 but did not fix this ownership
boundary. PR #447 is the current correction.

## Execution order

1. Complete #438:
   - remove verification-library version/commit from `runtime.json`;
   - remove the verification package from the Dockerfile;
   - keep Pillow/trimesh/scipy preinstalled as stable shared dependencies;
   - build released verification 0.10.0 once as a reusable CAD-CI dependency;
   - use that package from all model/reference verification;
   - prove the new immutable runtime and complete Forge CI.
2. Complete #444 if any post-merge runtime-image availability work remains.
3. Complete #440 with **simple-box only**:
   - keep only model-specific expectation/mutation data in the model;
   - keep Forge compilation/replay in the shared Forge producer path;
   - let released `run_solidcraft_verification()` own verification;
   - remove simple-box's procedural `verify_model.py`;
   - change no other model verifier in that proof PR.
4. Continue umbrella issue #432 only after #440 is green, using small reviewable
   model batches.
5. Resolve verification-library #44/#45 before models that need the missing
   partial parameter/sketch contracts. Do not work around those gaps in Forge.
6. Complete #446 independently; GitHub Actions build-cache policy is not part
   of the verification-library ownership change.
7. Resume #430 visual verification after the model-verification path is stable.
8. Complete #378 diagrams/final verification summary, then #366.
9. Run the final ownership audit and close/rewrite obsolete historical issues.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #438 Remove verification-library code from the SolidCraft runtime | now | Correct the runtime/package boundary; PR #441 did not remove the package from Docker. |
| #444 Keep published immutable SolidCraft runtime image available after merge | next | Verify post-merge availability after #438 selects the corrected immutable image. |
| #446 Remove GitHub Actions cache from SolidCraft runtime build | later | Separate runtime-build/cache policy; not required to define library ownership. |
| #440 Prove declarative SolidCraft verification with simple-box | blocked | Starts after #438; exactly one model. |
| #432 Use released declarative CAD verification in model verification | blocked | Continue only after #440 proves the one-model structure. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Resume after model verification ownership is stable. |
| #391 Extract reusable CAD verification library from Forge | blocked | Library is released; close after remaining shared checker code leaves Forge. |
| #378 Use explicit Forge verification stages instead of integration/native gates | now | Umbrella migration; current path is #438 then #440/#432. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | next | Starts after #378 verification output is complete. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Independent Forge API defect. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | Independent CLI quality work. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Product/API work. |
| #354 Support standalone sketch extrusions as boolean operands | later | Product/API work. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to superseded qualification architecture. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Independent model/API investigation. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Predates the current reusable runtime/CAD-CI design. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Independent product behavior. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:
`#438 -> #444 check -> #440 simple-box -> #432 batches -> #430 -> #378 -> #366`.
