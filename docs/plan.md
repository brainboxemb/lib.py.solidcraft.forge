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
released as **v0.22.1**.

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
- policy-dispatched permanent `dev` / `main` / `exp` qualification resolves the current checked-out branch HEAD and uses that same SHA for history selection and durable publication, preventing stale `workflow_dispatch` event-SHA races while retaining fail-closed publisher freshness checks.

Release evidence for v0.22.1:
- #306 qualification product head:
  `4370cc398ac8913dacda1c02a57edc13ef8c58ba`;
- permanent stable full qualification run 45845367923 is green on that product
  head;
- canonical-main governance landed through #307 / PR #308 as
  `5a982afe3bf7aa6ad07980df123ded50dfce98cf`, with permanent stable CI run
  45848533724 green;
- release metadata commit:
  `d09a8d0d47166c4ae375685d9c7ebc09a234fcd9`;
- annotated tag `v0.22.1` points exactly to that release commit and the
  GitHub Release is published;
- the metadata-only stable release path retained the prior full product evidence
  rather than replacing it;
- stable -> dev synchronization completed through #327 / PR #328 as merge
  commit `3c1c7e3f9986fb31d0567c57802855d57df7dfb7`, with permanent dev CI run
  45850246882 green.

The pinned SolidCraft 0.49 registry still has no native centre-mark or
centre-line drawing-authoring command; Forge deliberately does not emulate
those graphics.

The historical repository remains an archived A/B/provenance reference at
`brainboxemb/lib.py.solidcraft.forge.OLD`.

## Now

### Active consumer capability: #315 independent Free / Installed state

v0.22.1 is published; #315 is the active normal Forge consumer capability.

The HUB75 contract requires two independent axes in one Assembly:

- Small / Medium / Large remains the ordinary configuration row axis;
- Free / Installed is an independent physical-state checkbox, with Installed
  enabled by default for the assembled frame while standalone clamp output can
  remain Free for manufacturing/STL.

#306 proves reusable child parameters compose with a parent configuration
table, but it does not provide that independent state axis.

Before designing public Forge syntax, retain the exact SolidCraft 0.49
`config.rule` typed condition/effect schema in the repository. The retained
registry already advertises read-only `engine.describe`, which returns typed
input/output JSON Schemas when a command has a typed contract, while the
existing Forge reference module currently snapshots only `engine.commands`.
Extend that Forge-owned evidence path to retain
`engine.describe("config.rule")` from the pinned immutable runtime. The
current command row proves only the generic
`{id,name,enabled,condition,effect}` envelope and does not document a
`drive_parameter` effect. Forge must not guess the native schema or emulate
the state with numeric 0/1 parameters or Cartesian size/state rows.

If the pinned native contract supports the required rule semantics, #315 should
expose them through typed Forge intent and qualify save/reopen independence of
row selection and Installed state. A new public authoring API makes that a
minor-release capability.

#315 is not a v0.22.1 prerequisite because that patch only publishes the
already-stable #306 qualification.

### Experimental lane checkpoint

The isolated semantic-IR / Mitcad line is currently at a qualified checkpoint.

#297 synchronized the accepted v0.22.1 normal baseline into permanent `exp`
through reviewed conflict recovery. #320 then qualified the already-public
two-concentric-circle annular standalone Sketch extrusion through the same
engine-neutral compiler boundary:

- #320 / PR #342 merged to permanent `exp` as
  `95f70ef93eaaf86fece51b8e560aa895281ac7fe`;
- permanent exp CI run 45856878722 is green and durable `build/exp` names
  that exact source;
- one SCPF source now lowers through
  `SketchIR` / `CircleProfileIR` / `RegionIR` / `ExtrudeIR` to both
  SolidCraft and Mitcad;
- the annulus retains only semantic membership
  `RegionIR(outer=0, holes=(1,))`; backend coordinate picks and Mitcad native
  region ids remain lowering details rather than IR intent;
- the existing `multi-profile-extrude` owner retains native
  `model.mitcad`, `mitcad.json` and STL evidence;
- its Mitcad geometry verification passes the 10 mm OD / 8 mm ID / 30 mm
  length contract, including watertight mesh and inner-wall/volume checks;
- arbitrary profile types, non-concentric/nonnested membership and more than
  two profiles remain outside the qualified portable slice and fail closed on
  Mitcad.

No further experimental capability is selected by this plan. Keep `exp`
isolated at this qualified checkpoint until a demonstrated consumer need or a
separately scoped issue justifies the next compiler/backend expansion. Do not
promote `exp -> dev` merely because the experiment is green.

## Later

1. After the active #315 consumer capability, execute verification-evidence
   follow-ups #255, #256 and #257 in the order justified by the completed
   #163 audit unless a newer demonstrated consumer blocker takes priority.
2. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
3. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
