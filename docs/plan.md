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
- final-model configuration authoring through
  `model.configure(active=..., columns=..., rows=...)` on Shape, component
  occurrence and Assembly results;
- configuration columns use existing semantic handles directly: `Parameter`
  objects for parameter values and authored Shape/component-feature handles for
  feature suppression; the former `Configure(...)`, `Param(...)` and
  `Suppress(...)` wrappers are removed from the target API;
- Forge-owned Configurations verification for dimensional/suppression variants
  and complete Assembly Front/Below/Service positions, including native
  saved-design switching after replay;
- qualified configuration composition where a final model directly configures
  a deliberately published reusable-child parameter/feature, multiple child
  occurrences may reuse one component definition, and saved-design row
  switching recomputes child geometry without rerunning Forge Python;
- the former public `ConfigRule(...)`, `Always()`, `DriveParameter(...)`
  and `rules=` surface is removed; SolidCraft-specific rules remain backend
  evidence rather than Forge authoring vocabulary;
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

Normal-lane configuration API evidence after v0.24.0:
- #444 / PR #464 replaced wrapper/rule-shaped configuration authoring with
  final-model `model.configure(...)` using direct Parameter and authored
  feature handles; the obsolete rule-based `configuration-installed-state`
  owner was removed rather than preserved for compatibility;
- rule-free SolidCraft probe run 971 proves one real Installed feature may
  affect multiple bodies and be configured directly as a suppression column;
- exact-head PR CI 46022451428 (run 1008) is green; PR #464 merged to
  permanent `dev` as `a0570f6d11b9dea934cbff878955678ffad464e8`;
- permanent dev CI/build/publication 46023012718 (run 1009) is green on that
  exact product head;
- #488 / PR #489 owns stable `dev -> main` integration and the subsequent
  release checkpoint; downstream CAD must adopt the new API only from the
  published Forge tag, not from an unreleased branch.

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
- **v0.24.0 is released**; #444 / PR #464 is additionally qualified on
  permanent `dev` as `a0570f6d11b9dea934cbff878955678ffad464e8` with
  permanent build/publication run 46023012718 green;
- #488 / PR #489 is the immediate normal-lane checkpoint: stabilize that exact
  qualified product to `main`, then prepare a metadata-only Forge release
  from the exact qualified stable main head;
- do not migrate the downstream CAD model to the new `model.configure(...)`
  API until that Forge tag is published;
- #255, #380, the capturable #256 visual-state slice and #257 folded
  sheet-metal visual evidence remain part of the current development baseline;
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
- #389, #417, #424, #433, #440, #447, #451, #456, #461, #469, #473, #477, #481, #485, #496, #504 and #514 are complete architecture checkpoints: typed reference geometry includes symbolic `AxisLineIR` and `PlaneIR`; authored Revolve operation/target intent remains semantic; final design state carries bounded `ConfigurationIR`; `FeatureRefIR` traverses typed nested Boolean history; `SketchIR` carries explicit entity/constraint/dimension semantics; `RegionIR` describes exact region membership; Sphere/Cone reuse generic `PlacementIR`; role-aware `ParameterIR` and affine scalar-expression IR retain authored dependencies; equal/two-distance `ChamferIR` is typed; Cone composes through recursive `BooleanIR`; `Edges.VERTICAL` has engine-neutral `ParallelEdgeSetIR("Z")` feeding bounded constant-radius `FilletIR`; and that same `FilletIR` now reuses existing `FaceBoundaryIR(("top",))` topology semantics for the qualified Box/TOP slice;
- #510 / PR #511 completed the physical-owner checkpoint on permanent `exp`: PR CI 46033877961 built and verified both `cone-boolean` implementations from the exact same `scpf/model.py`, while permanent exp CI 46034222870 reused that qualification and skipped duplicate CAD execution;
- durable owner evidence remains green end-to-end: `cone-boolean--scpf` native/visual/geometry pass; `cone-boolean--scpf-mitcad` build/geometry/preview pass; shared mesh bounds are [-25,-20,0]..[25,20,26] with volume `39680 + 338π`; the Mitcad implementation retains the normal native document/STL/preview/build evidence through the catalogue path;
- #514 / PR #516 then completed TOP face-boundary Fillet on permanent `exp`: final PR CI 46036833118 is green and permanent exp CI 46037065727 reused the tree-identical PR qualification, skipped duplicate selected CAD execution, published the build scope and dispatched Pages;
- the #514 semantic contract is bounded to `PlacementIR(BoxIR)` plus one positive radius and exactly `FaceBoundaryIR(("top",))`; public `Edges.VERTICAL` remains `ParallelEdgeSetIR("Z")`;
- SolidCraft reuses the typed TOP-face `model.faces` / boundary `model.edges` path before stable `solid.fillet`; Mitcad reuses private `bind_face_boundary_edges` transport rather than principal-edge reconstruction, with no native face/edge identity entering semantic IR;
- exact pinned Mitcad v0.70.0 produced one watertight 60×40×12 BOTTOM Box with R2 TOP-boundary Fillet, bounds [-30,-20,0]..[30,20,12] and frozen native volume 28631.38638124875 mm³;
- TOP face-boundary Fillet remains standalone: the already-qualified Fillet→Cone `BooleanIR` path is still restricted to `ParallelEdgeSetIR("Z")`; FRONT/BACK/LEFT/RIGHT/BOTTOM face-boundary Fillet, multiple selected faces, directional-pair/explicit/vertex/profile selectors, Fillet over Extrude/Boolean bases, variable/chord/asymmetric/curvature Fillet, asymmetric non-TOP Chamfer, text-only/derived-unit mixed-role expressions, axial primitive support-plane widening, rotated primitive frames and new public unit syntax remain outside the qualified slices;
- #525 changes the pacing rule for the experimental compiler: IR completion and backend completion are separate dimensions. A semantic slice may become IR-ready on permanent `exp` after backend-neutral contract definition, typed normalization, pure IR boundary tests and stable typed SolidCraft compatibility; Mitcad may explicitly fail closed and catch up later;
- #525 also owns the experimental IR coverage ledger on `exp`, keeping complete/partial/legacy semantic status separate from SolidCraft/Mitcad backend status and physical-owner dual-backend evidence;
- #519 / PR #531 completed the first IR-first batch on permanent `exp`: explicit `Hole`, `CounterboreHole`, `CountersinkHole` and `ThreadedHole` now normalize to recursive semantic `HoleIR` over the bounded Box/Hole history; SolidCraft typed lowering remains legacy-document compatible while Mitcad intentionally fails closed;
- #519 PR CI 46042668913 is green (58 focused + 298 library tests), and permanent exp CI 46042807284 reused the tree-identical PR qualification instead of repeating selected execution; the coverage ledger therefore moves Hole from legacy to partial and reports 15/20 semantic families with at least some typed IR;
- #532 / PR #537 completed generic typed `BodyIR` history + `ShellIR`; #533 / PR #540 completed semantic native feature `PatternIR`; #534 / PR #542 completed the public basic closed-profile family with `RectangleProfileIR`, `RoundedRectangleProfileIR` and `SlotProfileIR`, plus Circle/Polygon offset and finite positive/negative/symmetric Extrude widening;
- final #534 PR CI 46046742176 is green (58 focused + 310 library tests), while permanent exp CI 46046851212 reused that tree-identical qualification and skipped duplicate selected execution; the experimental ledger now reports 4/20 semantic families complete and 17/20 with at least some typed IR;
- #544 / PR #547 completed semantic within-component placement on permanent `exp`: `FeaturePlacementIR` now owns absolute/anchored placement, `BoundOffsetIR` owns X/Y bound-relative offsets, `PlasticFeatureIR` completes Lip/SnapFit/Boss/Rest semantics, and the stable simple TOP anchored Hole route is typed without native topology ids in IR;
- final #544 PR CI 46048555351 is green (58 focused + 314 library tests), while permanent exp CI 46048695905 reused that tree-identical qualification and skipped duplicate selected execution; the ledger now reports 5/20 semantic families complete, 18/20 with typed IR and 2/20 fully legacy;
- #550 / PR #556 completed the current public Hole semantic family on permanent `exp`: absolute and anchored Hole intent remains typed independent from backend support, simple BOTTOM joins TOP as a typed SolidCraft lowering, countersink-angle Parameters are semantic degree-valued uses, and unsupported anchored variants remain typed/fail-closed; the ledger now reports 6/20 complete, 12 partial and 2 legacy families;
- #554 / PR #565 completed the current public Sheet metal semantic family on permanent `exp`, including shared `SketchChainIR`, typed sheet rules/history and manufacturing perforation semantics; #555 / PR #567 then completed reusable definitions, occurrences, symbolic pose/grouping, assembly anchors and rigid/planar/revolute/as-built relationships through `AssemblyIR`;
- #560 / PR #566 completed the current public support-independent Sketch entity/operation graph; #561 / PR #570 completed semantic Sketch support/frame intent, Regions/profile membership and current public Extrude semantics; #562 / PR #572 completed the shared public topology/reference-selector vocabulary;
- #574 / PR #575 reconciled the #562 semantic boundary against the actual public modifier API: current public Chamfer and Fillet are complete over typed `BodyIR` plus the shared typed edge-selection vocabulary; backend/body lowering limits remain backend coverage rather than missing modifier IR;
- #577 / PR #579 completes the current public Values/parameters/scalar-expressions family: literals, named parameters, unary/arithmetic, fixed numeric power and the existing `cadmath.min/max/sqrt/abs/round/floor/atan` grammar now retain typed backend-neutral scalar IR; physical roles remain use-site semantics and unsupported non-affine backend forms remain fail-closed;
- #581 / PR #583 completes the current public Boolean body-operation family: join/cut/intersect now compose recursive typed `BodyIR × BodyIR` histories in authored order, including semantic target/tool FeatureRefIR traversal; SolidCraft preserves qualified native CSG contracts while unsupported backend forms remain explicit backend gaps;
- #586 / PR #589 completes the current working standalone Revolve family: Circle/Rectangle/RoundedRectangle/Polygon/closed connected-profile Sketch results reuse the completed Sketch graph; symmetric sweep, coplanar principal/AxisLine intent and typed symbolic angles remain semantic IR; Slot/Text/pattern Revolve behavior is deliberately not invented because the current standalone compiler rejects those forms;
- permanent `exp` therefore reports 17/20 complete, 3/20 partial, 0 legacy and 20/20 families with typed IR. The remaining partial families are Placement/transforms, Reference geometry and Feature identity/suppression/configuration;
- #593 is the next partial-to-complete batch, as a semantic audit rather than assumed new IR. Reconcile the current public plane/axis vocabulary against `PlaneIR` and `AxisLineIR`: principal Sketch planes plus origin/offset, principal/fixed XYZ axes, shifted origins and public `AxisLine` are already typed across current consumers; construction-/edge-/face-/topology-selected axes are explicitly not exposed and must not be invented merely to fill the coverage row;
- if #593 confirms no current-public reference-geometry gap, mark that family complete and then select between Placement/transforms and Feature identity/suppression/configuration based on shared compiler/consumer value rather than backend parity or per-feature micro-slices;
- keep one issue/branch/PR per batch, but do not require Mitcad lowering/native qualification to advance to the next IR batch; unsupported backend paths remain fail-closed and Mitcad catches up separately;
- permanent `exp` must continue to reuse heavy green PR qualification when the reviewed PR-merge tree equals the permanent tree; Pages remains asynchronous publication evidence and is not an IR/compiler closure gate;
- `LegacyShapeIR` remains a visible migration boundary for stable SolidCraft compatibility, never a second interpreter; experimental backends continue to fail closed on unmigrated semantics;
- do not perform `exp -> dev` unless a separately qualified integration checkpoint explicitly selects it.

## Later

1. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
2. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
