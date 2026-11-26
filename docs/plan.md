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
- policy-dispatched permanent `dev` / `main` / `exp` qualification resolves the current checked-out branch HEAD and uses that same SHA for history selection and durable publication, preventing stale `workflow_dispatch` event-SHA races while retaining fail-closed publisher freshness checks.

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

The pinned SolidCraft 0.49 registry still has no native centre-mark or
centre-line drawing-authoring command; Forge deliberately does not emulate
those graphics.

The historical repository remains an archived A/B/provenance reference at
`brainboxemb/lib.py.solidcraft.forge.OLD`.

## Now

### Post-release permanent-lane synchronization

The v0.23.0 product release and the current isolated compiler experiment are
both at qualified checkpoints. No new product or experimental capability is
selected until the accepted baseline has been synchronized across the
permanent lanes.

Normal/stable checkpoint:
- v0.23.0 is published at
  `bc6cdeb2190abbf6ec2edc24dfef1c5da4c37689`;
- #315's Small / Medium / Large row axis plus independent Installed rule is
  released public Forge behavior;
- the release-only stable path is green and did not replace the retained full
  stable CAD evidence.

Experimental checkpoint:
- #343 / PR #347 qualified recursive typed `BooleanIR` plus bounded
  `SphereIR` through native Mitcad primitive join/cut/intersect while keeping
  SolidCraft behavior compatible; permanent exp
  `6826ea2c6ca0dfefb054dd4791d4e0303489f413`, CI 45859528081 and Pages
  45860055299 are green;
- #351 / PR #355 then qualified typed
  `PolygonProfileIR -> RegionIR -> symmetric ExtrudeIR -> ChamferIR`
  composition from the unchanged public SCPF source; current permanent exp
  `d9bb05d71e58a3b2069dfbf802f40a09a5ca32df`, CI 45862418767 and Pages
  45862908963 are green;
- neither checkpoint changes the public SCPF API and neither is promoted
  `exp -> dev`.

Complete the cross-lane checkpoint in this order:

1. synchronize accepted stable `main` governance and v0.23.0 release metadata
   into permanent `dev` through a direct `main -> dev` PR and `/merge`;
2. require permanent `dev` qualification/publication green on that exact
   post-release synchronization head;
3. execute already-open #358 as the final synchronization of this experimental
   trajectory: direct `dev -> exp`, preserving all accepted experimental
   compiler/backend work and all finalized normal v0.23.0 history;
4. if that direct permanent merge conflicts, use only the qualified reviewed
   `/merge-resolved` flow; then require permanent `exp` CI, durable
   `build/exp` publication and Pages green.

Do not start a new experimental compiler capability before #358 is complete.

## Later

1. After the post-release permanent-lane synchronization checkpoint, execute
   verification-evidence follow-ups #255, #256 and #257 in the order justified
   by the completed #163 audit unless a newer demonstrated consumer blocker
   takes priority.
2. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
3. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
