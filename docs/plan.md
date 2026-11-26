# Forge plan

This file contains unfinished work only.

## Accepted baseline

The Forge migration is complete and the current public product baseline is
released as **v0.19.0**.

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
- the adapter-boundary regression found by the permanent 52-owner gate is fixed: SolidCraft compiler/assembly imports occur during package initialization so public `scpf.assembly` remains the callable decorator; permanent `build/exp` at `4e2a6a7feb0de7f750efe1d073852208f1a25b5a` passed with library=true and 52/52 owners, followed by successful `/exp/` Pages publication.

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

### Experimental: #218 add the SCPF-to-Mitcad builder capability

The backend semantics are accepted on `exp`. The next boundary is ordinary
Forge build integration, without yet attaching Mitcad to model owners:

- add `builder-scpf-mitcad` with runtime role `mitcad`;
- feed the same owner-local SCPF source through
  `run_script(..., backend="mitcad")`;
- execute through the qualified Mitcad headless boundary and emit
  `model.mitcad`, `model.stl` and normal `build.json`;
- unit-test the builder without downloading a runtime binary;
- do not add root `runtimes.mitcad` or owner `scpf-mitcad` implementations
  until an immutable runtime image is available.

### Queued: #162 / #163 verification evidence cleanup

After the permanent `exp` line is stable:
- #162 fixes the concrete `sheet-perforate` case where native perforation
  metadata passes but the published model preview does not visibly show the
  perforations, and adds an explicit approved visual expectation;
- #163 audits every verification owner against the current evidence contract
  so visually meaningful owners cannot remain green on metadata/native checks
  alone.

## Later

1. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
2. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
