# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design belong in the normal documentation. Issues keep
detail and history; this plan states what is current and what follows.

## Current goal

Complete the Forge verification/publication chain with a controlled five-model
vertical proof before enabling the remaining model verifications.

The runtime ownership migration is complete:

- `docker.cad.solidcraft` owns and releases the reusable runtime;
- Forge consumes `ghcr.io/brainboxemb/cad-solidcraft:v0.1.0`;
- Forge owns no runtime Dockerfile or publication workflow.

The first declarative migration batch (#460) is also complete. Do not continue
with another broad batch yet.

## Required CAD-CI prerequisite

Forge is blocked on generic CAD-CI support for explicit item processing.

The released stack must first support:

```yaml
process: true
process: false
```

Forge uses that flag only for **model verification items**. It does not disable
the Forge tool/library build or tests.

The required release chain is:

1. implement/test/release `process` in `lib.py.cad.ci`;
2. update/test/release `tool.cad.ci`;
3. black-box accept the exact released stack in `tool.cad.ci.test`;
4. only then update Forge to consume it.

## Five-model vertical proof

Once the released CAD-CI stack supports `process`:

1. keep Forge tool build/test/release verification active;
2. set exactly these model-verification items to `process: true`:
   - simple-box;
   - anchor-topology-mutation;
   - attach-angle;
   - four-corner-l;
   - xz-anchor;
3. set every other model-verification item to `process: false`;
4. complete the entire remaining Forge verification/publication chain using
   only those five active model verifications;
5. a change to the shared thin model-verification wrapper may rerun all five
   active model verifications; that is expected;
6. only after the complete five-model chain is green and stable, enable the
   remaining model-verification items one at a time.

Do not reintroduce a ten-model migration batch before this vertical proof is
complete.

## Execution order

1. Wait for the released/accepted CAD-CI `process` stack.
2. Update Forge to that exact released `tool.cad.ci`.
3. Apply the five-model `process` selection above.
4. Complete #432/#430/#378/#366 as one controlled vertical chain with those
   five model verifications.
5. Keep generic verification mechanics in released
   `lib.py.cad.verfication`; add/release missing semantics there when needed.
6. Enable remaining model verification items one at a time, fixing model- or
   verification-library-specific gaps before enabling the next item.
7. Run the final ownership/publication audit.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #432 Use released declarative CAD verification in model verification | blocked | Resume with five-model vertical proof after released CAD-CI `process` support. |
| #430 Prove visual render, regression and expected-shape evidence with simple-box | blocked | Part of the five-model vertical chain. |
| #391 Extract reusable CAD verification library from Forge | blocked | Close after shared checker ownership is fully outside Forge. |
| #378 Use explicit Forge verification stages instead of integration/native gates | blocked | Continue inside the five-model vertical chain. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Finish inside the five-model vertical chain before enabling remaining models. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Independent Forge API defect. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | Independent CLI quality work. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Product/API work. |
| #354 Support standalone sketch extrusions as boolean operands | later | Product/API work. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to superseded qualification architecture. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Independent model/API investigation. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Predates the released Docker runtime and current CAD-CI design. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Independent product behavior. |
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Major Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:
`CAD-CI process release -> five-model Forge proof -> complete chain -> enable remaining models one by one`.
