# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

#558 is complete.

Forge main verification, durable build publication and stable Pages generation
now run on one hosted runner through externally accepted
`tool.cad.ci 0.15.0`.

The proven main run #2170 / `44884338160` produced:

- Forge source:
  `e658a44abb15773f7dac813afcf2fcfbf575f72a`;
- generated build:
  `fe1857e93cbe364460fa072d69c24d553db2ddc7`;
- generated `gh-pages`:
  `7b08be375258dc34b84dfcb33c378613a0ed773a`;
- 36 native Verification cases and 144 independent reference items;
- site generation in about one second after the one-runner CAD-CI/build path.

The public GitHub Pages source remains deliberately pointed at
`backup/gh-pages-before-f11-2026-11-20`. Generated `gh-pages` is not live.

A cut-over audit found that the normal 32 historical case pages have full
content parity in their new Verification pages, and the four restored cases are
additional current content. The audit also found three old standalone public
pages that were not yet source-owned by the replacement site:

- `qualification/results/`;
- `qualification/coverage/`;
- `qualification/joint-anatomy/`.

The latter two contain independent engineering knowledge, not merely old route
names. Existing `/qualification/.../` URLs would also 404 after a direct
branch cut-over.

## Current goal

Complete the #366 cut-over-readiness repair before changing the live Pages
source.

This change restores canonical:

- `verification/results/`;
- `verification/coverage/`;
- `verification/joint-anatomy/`;

and generates backward-compatible `qualification/` aliases for the root,
current case pages, the three special pages, the manifest and joint-anatomy
CadCraft source files.

Canonical navigation remains Verification-only.

## Required proof before live cut-over

- all 36 current Verification cases remain present;
- representative old/new case content parity remains green;
- current results page is generated from durable build/main evidence;
- coverage links only to current model Verification cases;
- joint-anatomy preserves the authored engineering explanation and all six
  current CadCraft sources;
- stable joint diagrams use immutable durable build URLs;
- old `qualification/<case>/` URLs redirect to canonical Verification pages;
- old special-page URLs redirect to canonical special pages;
- old and new manifest URLs contain identical current bytes;
- public canonical templates contain no visible Qualification navigation;
- complete PR and main site generation are green.

## Live boundary

Do **not** repoint the public Pages source during this parity repair.

After the generated replacement is reviewed and the above proof is green, the
remaining live cut-over is a separate explicit #366 action. Keep
`backup/gh-pages-before-f11-2026-11-20` intact as rollback evidence.

## Execution order

1. [#366] Restore the three source-owned Verification special pages.
2. [#366] Generate old-route compatibility aliases.
3. [#366] Prove source-only and complete durable stable-site generation.
4. [#366] Merge and review generated `gh-pages`.
5. [explicit approval] Repoint the live Pages source to the intended generated
   branch.
6. Verify the actual public site and old redirect URLs.
7. Only then decide later preview/cleanup and backup-retention policy.

## Open issue assessment — 2026-11-21

| Issue | Status | Assessment |
| --- | --- | --- |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | now | Durable build/main and one-runner gh-pages publication are complete; special-page parity, legacy URL compatibility and explicit live cut-over remain. |
| #391 Extract reusable CAD verification library from Forge | effectively complete but still open | Generic verification ownership and consumer migration are complete; remaining closure review is separate. |
| #481 Remove stale Forge development branches | later | Stale refs from closed work remain cleanup debt. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by released runtime batching and later timing work. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to superseded Qualification architecture. |
| #357 Fix Sketch.add() default handling for native Slot profiles | later | Independent Forge API defect. |
| #356 Improve CLI errors: show concise model errors instead of raw Python tracebacks | later | Independent CLI quality work. |
| #355 Support current SolidCraft parametric Slot API in Forge | later | Independent product/API work. |
| #354 Support standalone sketch extrusions as boolean operands | later | Independent product/API work. |
| #349 Coverage: expose the remaining SolidCraft SOLID › CREATE features in Forge | later | Feature-coverage backlog. |
| #347 Patterns should accept any applied Shape feature, not only Sketch.extrude | later | Forge feature backlog. |
| #335 Use build123d Sheet Metal for the sheet-fold qualification reference | later | Reference-quality improvement. |
| #325 Research: determine root cause of HUB75 AnchorFrame regression | later | Independent model/API investigation. |
| #175 Change 0005: qualify HUB75-like AnchorFrame orientation against known-good Placement poses | later | Domain verification backlog. |
| #82 Reconsider automatic hiding of the SolidCraft Joints folder | later | Independent product behavior. |
| #81 Support inline AnchorFrame references for rotated occurrences | later / blocks custom-anchor | Current `custom-anchor` intentionally proves the unsupported case rejects clearly. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Major Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:

`#366 parity/compatibility -> explicit live cut-over review`.
