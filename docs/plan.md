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
released as **v0.24.0**.

The accepted baseline now includes:
- 60 physical model owners, with SCPF primary per owner and historically real
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

Release evidence for v0.24.0:
- #255 / PR #376 completed the first verification-audit visual follow-up for
  seven visible-geometry owners while preserving their existing
  native/history/topology checks; permanent dev run 45876667570 is green;
- #380 / PR #392 added `Shape.export_feature(name)` plus definition-level
  `Occurrence.feature(name)` and the Forge-owned
  `configuration-child-feature` saved-design qualification; final PR CI
  45908830410 is green and permanent dev run 45909235443 is green on
  `d23bc22e7a7af253664fae057d881c8170acd401`;
- #398 / PR #399 stabilized that qualified product through the permanent
  `dev -> main` merge-commit path as
  `ba4c655f552fb9c75a7fb9825e52ee5d3b185f45`; permanent stable full
  qualification/build run 45910580497 is green on that product head;
- #400 / PR #402 landed metadata-only v0.24.0 release state as
  `61aef227ac6723b4fba526912749dc28bf474741`; stable release-only run
  45911068181 is green, selected release + library and zero model owners, and
  retained the existing full `build/main` product baseline;
- annotated tag `v0.24.0` resolves through tag object
  `fdfa92dd0437f78f7f03a0c102a7740f130e4aba` exactly to
  `61aef227ac6723b4fba526912749dc28bf474741`, and the GitHub Release is
  published;
- PR #403 synchronized released `main -> dev` through the permanent merge
  policy as `682f42d73aa91f66daab3a9dead4724537989966`; permanent dev
  qualification/build/publication run 45911643864 is green.
- downstream CAD #189 may now adopt the released v0.24.0 capability instead of
  depending on an unreleased Forge branch.

Normal-lane verification evidence after v0.24.0:
- #256 / PR #410 added deterministic SolidCraft visual-state evidence for the
  five currently capturable owners: RGB appearance, Installed / Free
  configuration state, Front / Service configuration placement, 60 / 120
  degree revolute pose and cut / suppressed revolve geometry;
- the shared `solidcraft-visual` adapter now materializes persistent
  saved-design state before measurement/snapshot and supports explicit RGB
  regression without weakening the existing geometry policies;
- all nine approved baselines come from SolidCraft 0.49.0 capture run
  45916016779; exact-head PR CI 45965420591 is green;
- PR #410 landed on permanent `dev` as
  `3537cdeb4682f4ef4b49f5a4dab96ed996346941`; permanent dev
  CI/build/publication run 45965985416 and Pages run 45966386680 are green;
- #256 remains open only for `exploded-views`: #415 proves that
  SolidCraft 0.49.0 `explode.show` is transient presentation state and
  save/reopen snapshotting cannot capture it deterministically. Forge does not
  add sleep/polling or Python substitute geometry for that gap;
- #257 / PR #422 added folded-result front/right/isometric visual geometry
  evidence for `sheet-contour-flange`, `sheet-edge-flange`, `sheet-hem`
  and `sheet-path-flange` while retaining each owner's saved-design,
  flat-pattern and SolidCraft-history checks;
- reviewed SolidCraft 0.49.0 capture run 45967875286 supplied the twelve
  approved folded-result views and all twelve expected-shape envelope checks
  passed; final exact-head PR CI 45969116610 is green;
- PR #422 landed on permanent `dev` as
  `cf428d46d3683aa74155aed70c5e946f149f64f7`; permanent dev
  CI/build/publication run 45969693260 and Pages run 45970148895 are green.

Experimental compiler evidence after the v0.23.0 cross-lane checkpoint:
- #343 / PR #347 qualified recursive typed `BooleanIR` plus bounded `SphereIR` through native Mitcad join/cut/intersect;
- #351 / PR #355 qualified parameter-independent `PolygonProfileIR -> RegionIR -> symmetric ExtrudeIR -> ChamferIR` composition from unchanged public SCPF source;
- #358 / PR #373 synchronized the finalized normal v0.23 baseline into permanent `exp` through reviewed conflict recovery as `e0180edf02b0ff50f1fda8732aa4da5262730599`, with exact parent order prior exp + finalized dev and reviewed tree `1c601d2b30741c4d48e76b5edab71840e40d3b63`;
- permanent exp CI/build run 45875143593, Pages run 45875575429 and deployment 45875703312 are green;
- #381 / PR #386 then qualified parameterized `PolygonProfileIR -> RegionIR -> RevolveIR` from the unchanged public `native-revolve` source, preserving `radius`, `length` and angle-valued `sweep` while lowering the same IR to native SolidCraft Revolve and native Mitcad Revolve;
- Mitcad's native angular-value contract is handled only at lowering: degree-valued `ParameterIR` becomes a unit-bearing expression such as `360 deg`, so engine storage units do not leak into semantic IR;
- #387 / PR #388 repaired the focused-owner CI inventory expectation exposed by the first full post-merge run without changing SCPF, IR, backend or model behavior;
- #389 / PR #395 generalized Revolve reference geometry through typed `AxisLineIR` and preserved subtractive Revolve as one semantic feature with cut/target intent;
- #408 / PR #409 synchronized released v0.24 normal `dev` with the experimental compiler line through reviewed permanent conflict recovery;
- #417 / PR #423 generalized standalone Sketch support through typed `PlaneIR(orientation, origin)`, keeping Mitcad construction-plane features backend-only;
- #424 / PR #429 added engine-neutral `FeatureRefIR` plus the first suppression-only `ConfigurationIR`, and qualified saved native Mitcad row switching on the unchanged `shifted-axis-revolve` owner without rerunning Forge Python;
- the simple-concave PolygonProfile/Region prerequisite discovered during #424 is also qualified generically in that same permanent merge: symbolic points remain semantic IR while evaluated geometry is used only for validation and deterministic native region transport; #430 is therefore completed without duplicate implementation and the obsolete #431 ordering was closed;
- #433 / PR #437 generalized `FeatureRefIR` through typed `BooleanIR.target/tool` semantic history paths, keeping authored identity engine-neutral while SolidCraft and Mitcad independently bind their actual native feature results;
- the existing `primitive-csg` owner proves nested saved-state identity end to end: `Clipped -> Unclipped -> Clipped` suppresses/restores the exact final clip feature without rerunning Forge authoring, while a deeper bore reference is resolved in backend-independent tests;
- current permanent exp `2cddd4e29916a2bb72dc38849983d6733963f2bc` has final PR qualification 45982446290, permanent CI/build/publication 45982819170, Pages 45983317799 and deployment 45983462551 green;
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
- **v0.24.0 is released** and synchronized back to permanent `dev`; #255,
  #380, the capturable #256 visual-state slice and #257 folded sheet-metal
  visual evidence are part of the current development baseline;
- downstream CAD #189 may adopt v0.24.0 for parent/root suppression of an
  explicitly exported feature inside a reusable child component;
- **#256 remains open but blocked only on #415** for deterministic headless
  capture of transient `exploded-views` presentation; do not implement a
  Forge-local timing/polling or substitute-geometry workaround;
- **#73 investigation is complete on the Forge side**: PR #436 retained one
  owner-local A/B diagnostic on permanent `dev` as
  `72f19f177a89d2468de6f7058c17dffede172798`; exact-head PR CI
  45977349093 is green;
- #73 reproduces identically on SolidCraft 0.49.0 and 0.50.0: phased headless
  replay passes, while fully resolved single-process CLI replay and live GUI
  replay both reject the same broad-face cut as reaching bend `F2/l3`;
- boundary minimization proves that save/reopen before the contour flange does
  not help, while save/reopen immediately after `sheet.flange` makes the
  unchanged cut succeed; `model.faces`, replay-variable binding and live
  `edit.checkpoint` are therefore not the cause;
- keep #73 open only as tracking for this external SolidCraft in-memory
  sheet-state divergence; do not add a Forge save/reopen, `plane.fixed`,
  physical-hole or other model-local workaround;
- SolidCraft 0.50 adoption is separate runtime-baseline work: 0.50 does not fix
  #73, but #73 by itself is not a reason to block an otherwise qualified 0.50
  baseline;
- with #73 isolated and #256 blocked on #415, do not invent another verification
  issue merely to keep the normal lane busy; select further normal work from
  existing consumer demand and the migrated backlog;
- return to the remaining #256 exploded visual acceptance when #415 has a
  supported deterministic SolidCraft capture route;
- keep normal verification work independent from experimental Mitcad/IR work.

Experimental `exp` lane:
- #393 remains the compiler control gate: SCPF is one frontend, typed engine-neutral Forge CAD IR is the compiler contract, and SolidCraft/Mitcad are independent lowerings rather than source interpreters;
- #389, #417, #424, #433, #440, #447, #451, #456, #461 and #469 are complete architecture checkpoints: typed reference geometry includes symbolic `AxisLineIR` and `PlaneIR`; authored Revolve operation/target intent remains semantic; final design state carries bounded `ConfigurationIR`; `FeatureRefIR` traverses typed nested Boolean history; `SketchIR` carries explicit entity/constraint/dimension semantics; the same relation graph is qualified across Revolve and Extrude; `RegionIR` describes selected concentric-circle regions independently of unrelated Sketch profiles; standalone anchored/translated Sphere placement reuses generic `PlacementIR(SphereIR)`; and `ParameterIR` now owns semantic use roles instead of one global physical unit;
- #469 / PR #470 is permanently qualified on `exp` as `744c49c6600ed557b4d15f871d41935975398fd0`: heavy PR CI 46011497993 is green including exact pinned Mitcad v0.70.0 mixed-role Revolve smoke, while permanent exp CI 46011956045 reused that evidence, skipped duplicate project/native execution and published durable provenance;
- current typed/accepted core: role-aware `ParameterIR`; Box/Cylinder/Sphere + `PlacementIR`; `AxisLineIR` and `PlaneIR`; `SketchIR` with Circle/simple Polygon profiles, `RegionIR`, semantic points/straight-line connectivity, H/V constraints, symbolic line dimensions and `SketchCoordinateDimensionIR`; bounded `ExtrudeIR`, recursive `BooleanIR`, face-boundary `ChamferIR`, `RevolveIR` with principal/shifted axis plus new-body/cut operation intent; and bounded semantic feature/history/configuration references;
- the next compiler checkpoint is the explicit shifted/anchored Sphere-in-CSG boundary recorded by `test_shifted_or_anchored_sphere_csg_remains_outside_bounded_slice`;
- this is a backend lowering/history problem rather than new Sphere semantics: standalone shifted/anchored Sphere already normalizes to `PlacementIR(SphereIR)`, and `BooleanIR` plus `FeatureRefIR` already own semantic primitive history;
- one semantic backend feature may require zero or more private helper commands plus one native semantic feature command. Mitcad needs this for the offset construction plane supporting a non-origin Sphere; SolidCraft does not. Helper commands remain backend transport only and must not enter Forge IR or semantic feature paths;
- replace the assumption that semantic Boolean feature index equals raw native command index. Lowering must preserve a semantic feature-to-native-command map so root/target/tool `FeatureRefIR` paths and configuration suppression bind the actual Sphere/Boolean feature rather than a helper construction plane;
- allow already-qualified Sphere placement inside the bounded primitive `BooleanIR` slice while preserving existing Box/Cylinder/origin-Sphere command spelling;
- exact Mitcad qualification must prove a shifted Sphere tool inside a Box CSG operation, including deterministic geometry and correct feature binding when suppression/configuration targets that Sphere;
- keep the checkpoint bounded: private support geometry for Sphere CSG only. General helper-feature IR, rotated primitive frames, mixed-role expression dimensional typing, asymmetric Chamfer and Cone migration remain later work;
- follow the fixed compiler order: generic semantic contract -> pure normalization/history tests -> independent backend lowering -> backend contract tests -> exact native runtime qualification -> permanent `exp` merge;
- permanent `exp` must reuse the heavy green PR qualification when the reviewed PR-merge tree equals the permanent tree; Pages remains asynchronous publication evidence and is not an IR/compiler closure gate;
- `LegacyShapeIR` remains a visible migration boundary for stable SolidCraft compatibility, never a second interpreter; experimental backends continue to fail closed on unmigrated semantics;
- do not perform `exp -> dev` as part of this checkpoint.

## Later

1. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
2. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
