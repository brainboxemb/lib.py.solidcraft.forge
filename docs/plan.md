# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

The current 32-case Qualification catalog is fully declarative, active and
durable.

- all 32 examples use data-only `verification/verify.py`;
- all 32 are `process: true`;
- all 32 have four independent reference child items;
- main commit `b4f601173d4a5ffddb7b0e2321b9d9174cce5c30` is green;
- durable `build/main` contains 32/32 current `model_verify` outputs;
- #432 and #546 are complete.

The remaining stable-Pages source code is still legacy. In particular:

- `site/build.py` contains hard-coded example/page metadata, SVG and full HTML;
- `site/guides.py` contains complete guide pages as Python strings;
- site code still references retired `qualification.*` modules that are no
  longer present on current main;
- local `examples/<slug>/model.yml` metadata is not yet the authoritative
  page-content source.

The current public Pages state remains preserved on
`backup/gh-pages-before-f11-2026-11-20`.

## Current goal

Complete #548: make each example directory self-describing for Pages and remove
hand-authored webpage content from Python.

## Required proof for #548

- all 32 `model.yml` files expose one validated presentation schema including
  concepts and a human verification explanation;
- exact numeric verification contracts remain only in `verification/verify.py`;
- current PASS/FAIL and measured evidence remain sourced only from durable
  `build/main`;
- example pages need no central Python example registry;
- page layout lives in external templates;
- guide prose lives outside Python;
- `site/build.py` contains orchestration/view-model code, not page markup;
- page and reusable-fragment structure normally lives under `site/templates/`;
- any Python-generated HTML is confined to an explicitly named HTML-rendering
  module, so rendering logic is structurally separate from source/evidence logic;
- no site code imports retired `qualification.*`;
- tests reject missing/malformed example metadata and hard-coded legacy page
  sources.

## Execution order

1. Define and validate the example `model.yml` presentation schema.
2. Add the missing concepts/verification explanation to all 32 examples.
3. Move base/example page layout and static scripts out of Python.
4. Move guide page prose out of `site/guides.py`.
5. Replace the central `EXAMPLES` / `SCHEMATICS` catalogs with discovered
   example metadata and durable evidence.
6. Remove retired `qualification.*` site imports and update site tests.
7. Prove source/site generation independent of retired qualification files.
8. Continue #497 using the cleaned source structure and complete
   `build/main` baseline.
9. Finish generic Pages publication/lifecycle in #366.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #548 Move example Pages content out of Python and into example metadata/templates | now | Required source cleanup before stable Pages; fixes the current legacy/hard-coded site architecture. |
| #497 Publish stable Pages from the generic build/main baseline | blocked | Complete #548 first; then generate stable Pages from current source + 32-case build/main. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Final generic Pages publication lifecycle follows #497. |
| #391 Extract reusable CAD verification library from Forge | effectively complete but still open | Generic verification ownership and consumer migration are complete; cleanup/close separately. |
| #481 Remove stale Forge development branches | blocked | Current connected tooling cannot safely delete stale refs. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by v0.3.2 runtime batching and measured #484 work. |
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

`#548 example/site sources -> #497 stable Pages -> #366 final Pages lifecycle`.
