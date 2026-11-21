# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

The central CAD-CI and generated stable-Pages path is implemented.

PR #562 completed #558 and moved Forge main verification, durable build
publication and stable Pages generation onto one hosted runner through exact
externally accepted `tool.cad.ci 0.15.0`.

PR #563 completed the #366 cut-over-readiness repair. Main run #2173 /
`44885328702` is green and produced:

- Forge source: `2bd8a1cc08dc9cbee015211e506bbbc6ebf0a1ee`;
- generated build: `6cd32285db2f272d91136117813604873a39240e`;
- generated `gh-pages`: `9bc48876a189073a9a94fa25564c4165e0225a0f`;
- 36 native Verification cases and 144 independent reference items.

The generated replacement now contains the three restored canonical special
pages, legacy Qualification-route compatibility and representative old/new case
content parity.

The public GitHub Pages source is still deliberately pointed at
`backup/gh-pages-before-f11-2026-11-20`. Generated `gh-pages` is not live.

## Current goal

Finish #366 only after explicit approval of the live Pages-source switch.

There is no remaining parity/code repair before that switch. Until approval is
given, #366 is blocked at the live publication boundary and no Forge-local
workaround or alternate publication path should be introduced.

#391 is complete. Its closure review confirmed that reusable CAD verification
mechanics are owned by `lib.py.cad.verification`; Forge retains only
consumer/model policy, reference execution, presentation and publication
composition.

While #366 is blocked, the next repository work is #481: remove stale
development branches after confirming none represent active work.

## Live cut-over proof

The generated replacement already proves:

- all 36 current Verification cases are present;
- representative old/new case content parity is green;
- `verification/results/` is generated from durable `build/main` evidence;
- `verification/coverage/` links only to current model Verification cases;
- `verification/joint-anatomy/` preserves authored engineering explanation
  and all six current CadCraft sources;
- stable joint diagrams use immutable durable build URLs;
- old `qualification/<case>/` and special-page URLs have generated redirects;
- old and new manifest URLs contain identical current bytes;
- canonical templates contain no visible Qualification navigation;
- complete PR and main site generation are green.

Keep `backup/gh-pages-before-f11-2026-11-20` intact as rollback evidence until
the live site has been switched and verified.

## Execution order

1. [#366, blocked] Obtain explicit approval for the live Pages-source cut-over.
2. [#366] Repoint the public Pages source to generated `gh-pages`.
3. [#366] Verify the actual public root, Verification pages and old
   Qualification redirects.
4. [#366] Only after successful live verification decide preview/cleanup and
   backup-retention policy.
5. [#481, now while #366 is blocked] Remove stale development branches after
   confirming none represent active work.

## Open issue assessment — 2026-11-21

| Issue | Status | Assessment |
| --- | --- | --- |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Durable build/main, one-runner publication, page parity and legacy compatibility are complete. Only the explicitly approved live Pages-source switch, public verification and later retention/preview decisions remain. |
| #481 Remove stale Forge development branches | now | #391 is closed; clean stale refs from merged, abandoned or superseded work and preserve only active/generated/rollback branches. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by released runtime images, batching and later one-runner timing work. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to the superseded Qualification architecture and old reuse strategy. |
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
| #81 Support inline AnchorFrame references for rotated occurrences | later | Current `custom-anchor` intentionally proves the unsupported case rejects clearly; this issue blocks promotion of that fixture. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Major Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:

`#366 blocked on explicit live approval -> #481 branch cleanup`.
