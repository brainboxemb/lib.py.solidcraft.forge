# Forge plan

This file contains unfinished work only.

## Accepted baseline

The Forge migration is complete and the current public product baseline is
released as **v0.21.0**.

The accepted baseline now includes:
- 57 physical model owners, with SCPF primary per owner and historically real
  reference implementations kept inside the same physical owner;
- native, geometry, inspection and applicable visual verification with durable
  generated evidence below `build/<scope>/models/**`;
- public Examples and Verification projected from the same physical-owner
  declarations rather than duplicate model trees;
- the Guide, Cheatsheet and generated API Reference validated against the public
  `cadlib/scpf` surface;
- shared topology selection through `Edges.from_faces(...)`, one
  world-cardinal `Faces` vocabulary and replay-bound native
  `model.faces` / `model.edges` identity;
- consumer-grade native drawing authoring:
  - A4/A3 landscape sheets;
  - explicit front/top/right/isometric placement and scale;
  - per-view visual style, including qualified shaded isometric views;
  - linear, face-to-face and radial/diameter dimensions and callouts;
  - native notes, drawing properties, title-block overrides and revisions;
  - vector PDF, native PNG and retained final `drawing.inspect` JSON;
  - builder-side structural checks plus approved sheet-image regression;
- bounded native revolute relationships through
  `Occurrence.attach(..., kind="revolute", ...)`;
- display-only `Shape.with_appearance("#RRGGBB")` authoring without changing
  material/density/BOM semantics;
- native editable configuration-table authoring through
  `Configure(design, active=..., columns=..., rows=...)`, with
  `Param(...)` parameter columns and `Suppress(feature)` feature-suppression
  columns across Shape, component occurrence and Assembly results;
- Forge-owned Configurations verification for dimensional/suppression variants,
  complete Assembly Front/Below/Service positions and flexible-fit
  `Free` / `Installed` physical states, including native saved-design
  switching after replay;
- public symbolic CAD math through `scpf.cadmath`, preserving parameter
  dependencies in native expressions for configuration-driven geometry;
- typed `AxisLine(...)` support for shifted/custom native revolve axes,
  including parameter-driven origins and suppressible revolve history;
- native compact technical-drawing presentation through
  `title_block_style="compact"`, replay-qualified as SolidCraft's 49 mm
  title block while preserving the existing built-in block as the default;
- sheet perforation qualified from authoritative SolidCraft
  flat-pattern/DXF manufacturing output with deterministic review evidence
  rather than fabricated display geometry;
- policy-owned integration through PR comment `/merge`, including merge
  commits for permanent branch synchronization;
- the library workflow split: pull requests run central `ci`; permanent
  `dev` / `main` runs qualify and publish durable scopes; Pages is
  dispatched independently;
- release-only stable `workflow_dispatch` classification from #156 /
  `template.cad.library#67`: metadata-only stable commits select release +
  library + zero models, while product changes or merge commits fail closed to
  full qualification;
- release-only stable publication preserves the previous full `build/main`
  product baseline instead of rebuilding/replacing it;
- Forge-owned release metadata validation and explicit owner-issued
  `/release` publication through released `tool.py.lib.ci`;
- stable Pages quality and the canonical Pages deployment;
- policy-dispatched permanent `dev` / `main` / `exp` qualification resolves the current checked-out branch HEAD and uses that same SHA for history selection and durable publication, preventing stale `workflow_dispatch` event-SHA races while retaining fail-closed publisher freshness checks.

Release evidence for v0.21.0:
- promoted full product baseline:
  `fe1c6fd699e7df872e962fdee31ea002747b88f5`;
- full durable `build/main` evidence: library=true and 57/57 owners;
- release metadata commit:
  `5a176ab1a5c1eb04e920b896f6df382ac85888e6`;
- annotated tag `v0.21.0` points exactly to that release commit;
- the metadata-only permanent stable run selected release + library + zero
  models and retained the full product baseline;
- stable -> dev synchronization completed through merge commit
  `46f77cc9078adb7e63a0ddd2b1694bd1fbdf4662`.

The pinned SolidCraft 0.49 registry still has no native centre-mark or
centre-line drawing-authoring command; Forge deliberately does not emulate
those graphics.

The historical repository remains an archived A/B/provenance reference at
`brainboxemb/lib.py.solidcraft.forge.OLD`.

## Now

### Dev: consumer capability blockers

Consumer-driven Forge capability stays ahead of the broad verification audit.

1. **#267 — multiple closed profiles in standalone Sketch extrusion**
   - required by CAD catalog #198 for the reusable hollow Ø10/Ø8 tube;
   - support nested closed loops in one standalone Sketch;
   - select the annular extrusion region explicitly and deterministically;
   - preserve one native Sketch and one native extrusion history feature;
   - keep current single-profile behavior backwards compatible.

2. **#271 — native two-distance / asymmetric chamfer**
   - required by CAD catalog #200 for the HUB75 Edge/Corner coupler taper;
   - expose the native primary/secondary chamfer-distance intent directly;
   - preserve semantic edge selection and one native chamfer feature;
   - keep existing equal-distance `chamfer(distance)` source-compatible.

3. **#163 — verification evidence audit**
   - resume the repository-wide verification audit after #267 and #271;
   - use the already-created focused follow-ups #255, #256 and #257 rather
     than mixing verification cleanup into consumer feature work.

Experimental compiler/backend development remains isolated on permanent
`exp`. The `exp` branch plan is authoritative for that stream; normal dev
work must not absorb unfinished experimental IR/backend changes.

## Later

1. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
2. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
