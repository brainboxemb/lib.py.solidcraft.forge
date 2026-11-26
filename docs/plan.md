# Forge plan

This file contains unfinished work only.

## Accepted baseline

The Forge migration is complete. The current public stable product baseline on
the normal main/dev line is **v0.21.0**. Permanent `exp` intentionally has not
yet synchronized the normal product changes after its earlier v0.19-derived
baseline; #297 owns that checkpoint before the next backend experiment.

The accepted baseline now includes:
- 52 physical model owners, with SCPF primary per owner and historically real
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
- policy-dispatched permanent `dev` / `main` / `exp` qualification resolves the current checked-out branch HEAD and uses that same SHA for history selection and durable publication, preventing stale `workflow_dispatch` event-SHA races while retaining fail-closed publisher freshness checks;
- the experimental `exp` line has a proven second native CAD backend boundary: Mitcad v0.70.0 reference/runtime identity is pinned, unchanged SCPF sources qualify native Box, Circle Sketch+Extrude and face-boundary Chamfer, native Mitcad topology remains engine-owned, retained Mitcad STL passes the existing geometry verifier, and the internal `BackendAdapter` centralizes backend selection while SolidCraft remains the stable default;
- the adapter-boundary regression found by the permanent 52-owner gate is fixed: SolidCraft compiler/assembly imports occur during package initialization so public `scpf.assembly` remains the callable decorator; permanent `build/exp` at `4e2a6a7feb0de7f750efe1d073852208f1a25b5a` passed with library=true and 52/52 owners, followed by successful `/exp/` Pages publication;
- the experimental builder/runtime boundary is complete: `builder-scpf-mitcad` compiles unchanged SCPF sources through the Mitcad adapter and retains `model.mitcad` + `model.stl`; `docker.cad.solidcraft v0.3.7` publishes the isolated immutable `cad-mitcad` role pinned to Mitcad 0.70.0; temporary Forge evidence PR #230 qualified the exact release candidate through normal CAD-CI with `simple-box` and `circle-negative-extrude` Mitcad geometry PASS and was closed unmerged;
- the first owner-integrated Mitcad slice stays inside the existing physical owners: `simple-box`, `circle-negative-extrude` and `topology-face-boundary-box` declare secondary `scpf-mitcad` implementations over the same SCPF source while SolidCraft remains primary; all three enter generic reference-runtime mesh verification, including an explicit two-edge chamfer geometry contract for the topology owner;
- experimental Pages now makes that second backend inspectable instead of merely green: `builder-scpf-mitcad` retains validated `mitcad.json`, durable output includes native `model.mitcad` plus Mitcad-exported `model.stl`/preview, shared SCPF source is shown once, and the published `/exp/` pages expose generated Mitcad commands and replay bindings alongside result/verification evidence; permanent exp build `45817979939` and Pages run `45818223238` passed after #243;
- the experimental compiler boundary is now explicit: trusted SCPF source is evaluated once, final Shape intent is normalized to engine-neutral `ModelIR`, and SolidCraft/Mitcad lower the same typed `BoxIR`, `CircleExtrudeIR`, `ChamferIR` and semantic face-boundary intent; not-yet-migrated stable SolidCraft surface is isolated behind SolidCraft-only `LegacyShapeIR`; permanent exp build `45824024029` passed with library=true and all 52 owners, followed by successful Pages run `45824616018`;
- the first capability added through that compiler boundary is qualified: `CylinderIR` and bounded `BooleanSubtractIR(BoxIR, CylinderIR)` are shared semantic nodes, SolidCraft preserves its existing CSG command contract, Mitcad lowers the same intent to native Box + Cylinder Cut without predicted body ids, and the focused `cylinder-subtract` owner extends only the experimental catalog to 53 owners; permanent exp build `45828904100` passed with both SolidCraft and Mitcad geometry evidence, followed by successful Pages run `45829424750`.
- primitive geometry and absolute placement are now separate semantic IR concepts: `PlacementIR` owns world-space point + semantic anchor around typed `BoxIR` / `CylinderIR`, qualified `.at(...)` and translations use that same boundary, and `BooleanSubtractIR` consumes placed solids; the off-centre `cylinder-subtract` proof keeps symbolic `bore_x` / `bore_y` through Mitcad native Cylinder Cut while unsupported axial offsets fail closed; permanent exp build `45832874520` passed with library=true and all 53 owners, followed by successful Pages run `45833401412`.
- standalone Sketch geometry, semantic region membership and extrusion are now separate compiler concepts: `CircleProfileIR` lives inside `SketchIR`, `RegionIR` owns compiler-local outer/hole profile membership and `ExtrudeIR` consumes regions without engine ids; the existing `circle-negative-extrude` source remains unchanged and both native backends lower the same semantic nodes; unqualified nested-loop regions fail closed; permanent exp build `45836358625` passed with library=true and all 53 owners, followed by successful Pages run `45836994007`.
- normal `dev` has independently advanced to the v0.21.0 product line and now includes #267 multi-profile standalone Sketch extrusion with 58 normal owners; that capability is not copied into `exp` and becomes available to the experiment only through the #297 dev→exp synchronization checkpoint.

Release evidence for v0.19.0:
- promoted full product baseline:
  `e19c362e3703ae0d62638d76728b29d3315320f0`;
- full durable `build/main` evidence: library=true and 52/52 owners;
- release metadata commit:
  `ce9cd4439efe51edc360b7bfffb77b950e218d32`;
- annotated tag `v0.19.0` points exactly to that release commit;
- the metadata-only permanent stable run selected release + library + zero
  models and retained the full product baseline;
- stable -> dev synchronization completed through merge commit
  `6e569782592ebd9d51fef991b032b6fb51eb7eb7`.

The pinned SolidCraft 0.49 registry still has no native centre-mark or
centre-line drawing-authoring command; Forge deliberately does not emulate
those graphics.

The historical repository remains an archived A/B/provenance reference at
`brainboxemb/lib.py.solidcraft.forge.OLD`.

## Now

### Experimental checkpoint: #297 sync current dev product baseline into exp

Bring the real normal Forge product back underneath the experimental compiler
line before adding another Mitcad capability:

- wait for current normal dev consumer blocker #271 to complete and for the
  resulting dev plan to be reconciled;
- synchronize permanent `dev -> exp` through a PR and the repository
  `/merge` policy; do not cherry-pick or reimplement normal product changes;
- preserve the accepted experimental IR/backend commits while bringing in the
  current v0.21-era normal product baseline, including #267 multi-profile
  standalone Sketch extrusion;
- require a full permanent `exp` library + owner qualification/publication
  after the synchronization;
- do not integrate `exp -> dev` in this checkpoint;
- only after the synchronized baseline is green, open the next experimental
  issue to qualify the already-public nested/multi-profile Sketch semantics
  through `RegionIR` on Mitcad without changing the public SCPF API.

Normal dev verification follow-ups (#255/#256/#257/#294) and consumer work
remain owned by the normal dev lane; do not duplicate them on `exp`.

## Later

1. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
2. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
