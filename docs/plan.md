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
- public symbolic CAD math through `scpf.cadmath.min()`, `max()`,
  `sqrt()`, `abs()`, `round()`, `floor()` and `atan()`, preserving
  source parameter dependencies in SolidCraft expressions;
- typed shifted/custom `AxisLine(...)` support for `Sketch.revolve(...)`,
  including parameter-driven origins while retaining one suppressible native
  revolve feature;
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

Release evidence for v0.21.0:
- promoted full product baseline:
  `fe1c6fd699e7df872e962fdee31ea002747b88f5`;
- full durable `build/main` evidence: `full=true`, `library=true` and
  57/57 active owners;
- release metadata commit:
  `5a176ab1a5c1eb04e920b896f6df382ac85888e6`;
- annotated tag `v0.21.0` points exactly to that release commit and the
  GitHub Release is published;
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

### Release checkpoint: #299 Forge v0.22.0

The consumer-driven v0.22 product line is accepted on permanent `dev`.

Accepted development work:
- #163 established the repository-wide verification evidence contract and
  future-owner minimum;
- #267 added multiple closed profiles in one standalone Sketch extrusion,
  required by CAD catalog #198;
- #294 added approved native visual evidence for that new visible-geometry
  owner;
- #271 added native two-distance/asymmetric chamfer authoring, required by CAD
  catalog #200, with direct native definition inspection, saved-design
  mutation, geometry and approved visual evidence;
- the development catalogue now contains 59 physical owners and 38 ordinary
  SolidCraft visual policies.

Permanent development evidence:
- exact product head:
  `79332ba55a52f205c0b469707bac1911a4cd3b6c`;
- permanent dev build run `45840231474`: success;
- selected project graph: success;
- durable `build/dev` publication: success;
- independent Pages dispatch: success.

Next:
1. promote the exact qualified `dev -> main` product through repository-local
   `/merge`;
2. require the permanent stable full product build to succeed;
3. prepare metadata-only `release/v0.22.0` from qualified stable `main`;
4. publish v0.22.0 through the explicit `/release` workflow;
5. synchronize stable-only release metadata back with `main -> dev`;
6. reconcile the plan after publication.

Do not start #255/#256/#257 before this release checkpoint unless a new
demonstrated consumer blocker supersedes the release.

### Experimental lane

The permanent `exp` branch remains isolated from normal product development.
Its branch-local `docs/plan.md` owns the current experimental work order;
normal `dev` must not duplicate that queue because it progresses
independently. Re-read the current `exp` plan before doing experimental work,
and integrate `exp -> dev` only through a separately qualified issue/PR when
an experiment is explicitly accepted for the product.

## Later

1. After v0.22.0 publication and stable -> dev synchronization, execute the
   concrete verification-evidence follow-ups #255, #256 and #257 in the order
   justified by the accepted audit unless a newer consumer blocker takes
   priority.
2. Continue the migrated Forge product/research backlog (#59-#72) according to
   demonstrated consumer value and dependencies rather than treating the whole
   historical backlog as release-blocking.
3. Retire duplicated historical orchestration only after all real consumers and
   public documentation have equivalent coverage.
