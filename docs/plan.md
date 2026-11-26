# Forge plan

This file contains unfinished work only.

`docs/plan.md` is repository governance and is canonical on **main**. Work on
`dev` or `exp` must read the current main version even when that branch's
working-tree copy has not yet received the latest governance synchronization.
Plan reconciliation is authored from a short-lived docs branch created from
`main` and merged back to `main` through `/merge`; development lanes do not
maintain competing branch-local plans.

## Accepted baseline

The Forge migration is complete and the current public product baseline is
released as **v0.23.0**.

The accepted baseline now includes:
- 59 physical model owners, with SCPF primary per owner and historically real
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
- qualified configuration composition where a parent `Configure(...)` table
  drives a deliberately published reusable-child parameter, multiple child
  occurrences share that one native parameter, and saved-design row switching
  recomputes child geometry without rerunning Forge Python;
- typed native Configuration Rules through
  `Configure(..., rules=...)`, `ConfigRule(...)`, `Always()` and
  `DriveParameter(...)`, keeping Installed state independent from ordinary
  Small / Medium / Large rows while disabling the rule restores the active
  row's stored Free/base expression;
- public symbolic CAD math through `scpf.cadmath.min()`, `max()`,
  `sqrt()`, `abs()`, `round()`, `floor()` and `atan()`, preserving
  source parameter dependencies in SolidCraft expressions;
- typed shifted/custom `AxisLine(...)` support for `Sketch.revolve(...)`,
  including parameter-driven origins while retaining one suppressible native
  revolve feature;
- multiple closed profiles in one standalone `Sketch.extrude(...)`, including
  deterministic nested-loop/annular regions while preserving one native Sketch
  and one native ExtrudeFeature;
- native equal- or two-distance chamfer authoring through
  `Shape.chamfer(distance, distance2=..., flip=..., edges=...)`;
- manufacturing-output verification for `sheet-perforate` from authoritative
  SolidCraft flat-pattern/DXF evidence rather than fabricated display geometry;
- native compact technical-drawing title blocks through
  `title_block_style="compact"`, with replayed 49 mm geometry and a separate
  approved sheet-image baseline while the existing full title block remains the
  default;
- policy-owned integration through PR comment `/merge`, including merge
  commits for permanent branch synchronization;
- reviewed `/merge-resolved` recovery for genuinely conflicted direct
  permanent merges, using a separate green same-repository `resolve/*` PR,
  an exact reviewed tree and an exact two-parent `[base, head]` merge object
  before non-force base advancement;
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
- merge policy validates the newest PR-specific central CI run for an exact head SHA, so historical failed checks from superseded PRs cannot poison a later qualified replacement while a newest pending/failed run still blocks;
- the isolated `exp` compiler line evaluates SCPF once into typed engine-neutral semantic IR and lowers that same IR independently to SolidCraft and Mitcad, with accepted `PlacementIR`, Sketch/profile/Region/Extrude, recursive Boolean, Sphere, face-boundary Chamfer and parameterized `RevolveIR` slices rather than backend interpretation of raw `Shape.data`.

Release evidence for v0.23.0:
- #315 completed through native-contract PR #336 and public typed API PR #348,
  with permanent dev qualification/build run 45860020832 green;
- #353 / PR #354 stabilized that qualified product through the permanent
  `dev -> main` merge-commit path as
  `4095f1b377a088f7d2c9b5eba319ddcc2c84af90`;
- permanent stable full qualification/build run 45862411015 is green on that
  product head;
- release metadata landed through #356 / PR #357 as
  `bc6cdeb2190abbf6ec2edc24dfef1c5da4c37689`;
- stable release-only run 45863277563 is green, selected release + library and
  zero model owners, and retained the prior full `build/main` product
  baseline;
- annotated tag `v0.23.0` points exactly to
  `bc6cdeb2190abbf6ec2edc24dfef1c5da4c37689` and the GitHub Release is
  published.

Experimental compiler evidence after the v0.23.0 cross-lane checkpoint:
- #343 / PR #347 qualified recursive typed `BooleanIR` plus bounded `SphereIR` through native Mitcad join/cut/intersect;
- #351 / PR #355 qualified parameter-independent `PolygonProfileIR -> RegionIR -> symmetric ExtrudeIR -> ChamferIR` composition from unchanged public SCPF source;
- #358 / PR #373 synchronized the finalized normal v0.23 baseline into permanent `exp` through reviewed conflict recovery as `e0180edf02b0ff50f1fda8732aa4da5262730599`, with exact parent order prior exp + finalized dev and reviewed tree `1c601d2b30741c4d48e76b5edab71840e40d3b63`;
- permanent exp CI/build run 45875143593, Pages run 45875575429 and deployment 45875703312 are green;
- #381 / PR #386 then qualified parameterized `PolygonProfileIR -> RegionIR -> RevolveIR` from the unchanged public `native-revolve` source, preserving `radius`, `length` and angle-valued `sweep` while lowering the same IR to native SolidCraft Revolve and native Mitcad Revolve;
- Mitcad's native angular-value contract is handled only at lowering: degree-valued `ParameterIR` becomes a unit-bearing expression such as `360 deg`, so engine storage units do not leak into semantic IR;
- #387 / PR #388 repaired the focused-owner CI inventory expectation exposed by the first full post-merge run without changing SCPF, IR, backend or model behavior;
- current permanent exp `a5470e171e1455b54905a51390a25531af93bd47` has full CI/build/publication run 45879270985 green, Pages run 45879685758 green and deployment 45879775624 green;
- accepted experimental compiler/backend work remains isolated from `dev` until a separately qualified `exp -> dev` integration is explicitly selected.

The pinned SolidCraft 0.49 registry still has no native centre-mark or
centre-line drawing-authoring command; Forge deliberately does not emulate
those graphics.

The historical repository remains an archived A/B/provenance reference at
`brainboxemb/lib.py.solidcraft.forge.OLD`.

## Now

### Independent normal and experimental lanes

Normal consumer work and isolated compiler research may proceed independently; neither lane may use the other as an unqualified staging area.

Normal `dev` lane:
- #380 is the demonstrated CAD consumer blocker: let a parent/root `Configure(...)` target an exact authored suppressible feature owned by a reusable child component without exposing replay/native feature ids;
- keep its public authoring/replay qualification independent from experimental Mitcad work;
- #255 / PR #376 is complete on `dev`: seven audited visible-geometry owners now retain approved `front`, `right` and `iso` regression baselines plus expected-shape evidence while preserving their existing native/history/topology checks; final PR CI 45876080803, permanent dev build/publication 45876667570 and Pages 45877168765 are green;
- keep later verification-evidence follow-ups #256 and #257 separate from #380.

Experimental `exp` lane:
- #393 is the immediate architecture/control checkpoint before more backend capability code;
- treat Forge as a generic CAD compiler: SCPF is one frontend, typed engine-neutral Forge CAD IR is the compiler contract, and SolidCraft/Mitcad are independent lowerings rather than separate source interpreters;
- maintain an explicit IR inventory by semantic layer (values, reference geometry, sketches, profiles/regions, features/history, body operations, topology references, assemblies and configurations) and mark each layer accepted, bounded/partial or still legacy;
- current typed/accepted core: `ParameterIR`; Box/Cylinder/Sphere + `PlacementIR`; `SketchIR` with Circle/Polygon profiles and `RegionIR`; bounded `ExtrudeIR`, recursive `BooleanIR`, face-boundary `ChamferIR`, and the first principal-axis new-body `RevolveIR` slice;
- current generic gaps: no general reference-geometry IR (`AxisLineIR`/Plane/Point), no complete Sketch constraint/dimension IR, only partial feature/history and topology-reference identity, and no experimental assembly/occurrence or configuration/suppression IR yet;
- require every experimental capability to progress in this order: define generic CAD meaning -> pure normalization/IR tests -> backend lowering -> backend contract tests -> real native runtime qualification -> permanent `exp` merge;
- backend implementation details may never drive semantic IR fields: a Mitcad construction helper, native feature uid/curve id, SolidCraft command spelling or topology id remains backend transport only;
- symbolic Parameters/Expressions and authored feature identity must survive normalization; current evaluated values may validate semantics but may not replace them;
- a backend may lower a typed IR node or fail explicitly; it may not reinterpret raw `Shape.data`, silently approximate unsupported intent or create a second CAD interpreter;
- `LegacyShapeIR` remains a visible migration boundary for stable SolidCraft compatibility, not a second permanent compiler architecture; experimental backends continue to fail closed on it;
- #389 remains the first candidate capability after #393 because a generic `AxisLineIR` plus feature-operation/target semantics fills real gaps in the inventory; its Mitcad construction-line mechanics are secondary lowering detail and must not determine the IR shape;
- do not change #389 implementation until #393 is merged to canonical `main`; the existing #389 work branch remains a clean branch from permanent `exp`;
- keep parameter-driven Sketch-plane placement and portable configuration/suppression semantics as later generic IR gaps rather than hiding them in backend workarounds;
- do not perform `exp -> dev` as part of #393 or #389.

## Later

1. Continue verification-evidence follow-ups #256 and #257 after completed #255, in the order justified
   by the completed #163 audit unless a newer demonstrated consumer blocker
   takes priority.
2. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
3. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
