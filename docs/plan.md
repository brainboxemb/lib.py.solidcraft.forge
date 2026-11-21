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

PR #563 restored the special Verification pages, legacy Qualification routes
and source/reference content needed for cut-over testing. A live source switch
to generated `gh-pages` was then performed on 2026-11-21. GitHub Pages run
#818 / `44888168038` deployed `gh-pages`
`74f087afd3ec3477b014c96a54380241dd8f73ae` successfully.

Live review exposed a remaining presentation-parity regression on ordinary
case sheets. For example, `verification/circular-feature-pattern/` no longer
used the accepted historical information order: the conceptual setup diagram
and native preview were missing from the overview, the large durable
verification block appeared before the reference/explanation flow, and the
engineering explanation was moved to the bottom. The Verification index also
embedded a six-item joint/corner-bracket engineering gallery that did not
belong on the catalog overview.

The live Pages source was therefore rolled back to
`backup/gh-pages-before-f11-2026-11-20`. Pages run #819 /
`44888467498` completed successfully from backup commit
`127adb3900cdc9ca6194edb1102ea7d505316295`.

#366 is reopened and owns the parity repair. The current fix is developed on
`issue/366-verification-case-parity`.

## Current goal

Restore the accepted case-sheet information architecture without reintroducing
the old Qualification execution model or a second source of verification truth.

The target presentation order is:

1. status and case title;
2. "What this example makes";
3. conceptual setup diagram plus native preview;
4. Forge source and API used;
5. independent reference source/result comparison;
6. "How Forge builds it in SolidCraft";
7. SolidCraft result and visual evidence;
8. collapsed technical verification detail and provenance.

The conceptual setup diagram must be derived from the declared expected body
envelopes already present in verification evidence from `verify.py`; do not
restore the removed central `EXPECTED_VISUAL_BOXES` catalog.

The Verification index remains a grouped case catalog with links to the
standalone results, coverage and joint-anatomy pages. Joint/corner-bracket
engineering diagrams belong on `verification/joint-anatomy/`, not as a
gallery appended to the catalog root.

#391 is complete. Reusable CAD verification mechanics remain owned by
`lib.py.cad.verification`; Forge retains consumer/model policy, reference
execution, presentation and publication composition.

## Cut-over validation state

Already proven and retained:

- all 36 current Verification cases exist;
- `verification/results/`, `verification/coverage/` and
  `verification/joint-anatomy/` are generated;
- old `qualification/<case>/` and special-page routes have generated
  compatibility redirects;
- old and new manifest URLs contain identical current bytes;
- canonical navigation uses Verification terminology;
- durable Pages generation and publication from `build/main` are green.

Still required before another live switch:

- representative case sheets must match the accepted historical information
  architecture;
- setup diagrams and primary previews must appear in their original overview
  role;
- heavy machine evidence must be secondary/collapsed rather than defining the
  page layout;
- the Verification catalog root must not embed the joint engineering gallery;
- complete PR and main site generation must remain green after the repair.

Keep `backup/gh-pages-before-f11-2026-11-20` intact and live until the repaired
generated site is reviewed again.

## Execution order

1. [#366, now] Restore generic Verification case-sheet presentation parity.
2. [#366] Remove the misplaced engineering-diagram gallery from the catalog
   root while retaining the standalone joint-anatomy page.
3. [#366] Generate and inspect representative case pages, especially
   `circular-feature-pattern`, and run the complete site/CI checks.
4. [#366] Merge the repair and let main publish a fresh generated
   `gh-pages`.
5. [#366] Review the generated branch before switching the live Pages source.
6. [#366] Repoint live Pages to `gh-pages` only after that review, then verify
   the public root, representative Verification cases and old Qualification
   redirects.
7. [#481, next] Remove stale development branches after #366 is proven live.

## Open issue assessment — 2026-11-21

| Issue | Status | Assessment |
| --- | --- | --- |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | now | Live review found a case-sheet presentation-parity regression. Backup Pages is restored; repair the generic Verification layout, review generated gh-pages, then retry the live cut-over. |
| #481 Remove stale Forge development branches | next | #391 is closed, but branch cleanup waits until the #366 Pages repair is proven live; preserve active/generated/rollback branches meanwhile. |
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

`#366 case-page parity repair -> generated-site review -> live cut-over -> #481 branch cleanup`.
