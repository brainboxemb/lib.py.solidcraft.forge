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
released as **v0.22.0**.

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

Release evidence for v0.22.0:
- promoted full product baseline:
  `8fd34556bb85527e085dc59ae0b07cc0539080cc`;
- full durable `build/main` evidence retains that source with
  `full=true`, `library=true` and 59/59 active owners;
- release metadata commit:
  `bed61dd65fb2b2617f2f316cbc1cd7a7dd250988`;
- annotated tag `v0.22.0` points exactly to that release commit and the
  GitHub Release is published;
- the metadata-only stable release path succeeded and retained the full product
  baseline rather than replacing it.
- stable -> dev release-metadata synchronization completed through merge commit
  `a60114bceccc084f812bfd9435d364c80180e677`.

The pinned SolidCraft 0.49 registry still has no native centre-mark or
centre-line drawing-authoring command; Forge deliberately does not emulate
those graphics.

The historical repository remains an archived A/B/provenance reference at
`brainboxemb/lib.py.solidcraft.forge.OLD`.

## Now

### Stable governance checkpoint: #307

The #306 qualification-only product delta is already promoted to stable
`main` through #317 / PR #319 at
`4370cc398ac8913dacda1c02a57edc13ef8c58ba`.

Land #307 next on that updated stable product. This makes
`main:docs/plan.md` the single canonical repository plan and updates AGENTS
and the durable handoff accordingly. Require the permanent stable main
qualification after that governance merge before release preparation.

### Release checkpoint: #318 / v0.22.1

#306 proves the existing released configuration API covers the HUB75
parent/child composition without adding a new public API:

- a reusable child component publishes one native parameter through
  `component(..., include=...)`;
- the parent Assembly's Small / Medium / Large `Configure(...)` table targets
  that shared published child parameter through ordinary `Param(...)`;
- multiple child occurrences share the same native parameter;
- saved-design row switching recomputes child geometry without rerunning Forge
  Python;
- no boolean emulation, duplicate Installed body, Cartesian state table or raw
  SolidCraft ids are introduced.

Because this qualification completed after the immutable v0.22.0 publication,
publish a **v0.22.1 qualification-only patch**:

1. require the permanent stable build on the #306 promotion head;
2. merge #307 canonical-plan governance on that updated main;
3. require permanent stable qualification after the governance merge;
4. create metadata-only `release/v0.22.1` from that exact main;
5. publish through #318 with the explicit owner-issued `/release` workflow;
6. synchronize accepted governance plus stable patch metadata back with one
   `main -> dev` merge-policy PR;
7. reconcile this canonical main plan after publication.

The patch must not add a new public API.

### Conditional future configuration research: #315

Only if a demonstrated consumer requires Free / Installed to remain an
independent state axis inside the same Assembly while Small / Medium / Large
remains separate, investigate the native SolidCraft `config.rule` contract
through #315 before designing Forge API.

#315 is **not** a v0.22.1 prerequisite. Do not emulate a boolean with numeric
0/1 and do not force Cartesian configuration rows.

### Experimental lane

Permanent `exp` keeps the accepted Mitcad/semantic-IR work isolated from
normal development. Synchronize accepted normal product/governance state into
`exp` through #297 only after the stable/governance synchronization is
settled, then continue experiments without reimplementing normal product work.

## Later

1. After the v0.22.1 qualification patch, execute verification-evidence
   follow-ups #255, #256 and #257 in the order justified by the completed
   #163 audit unless a newer demonstrated consumer blocker takes priority.
2. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
3. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
