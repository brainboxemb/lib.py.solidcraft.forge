# Forge repository plan

This file is the current source of truth for unfinished work in
`lib.py.solidcraft.forge`.

Permanent requirements/design/API/release contracts belong in the primary
documents in `docs/`. Issues keep detail and history.

## Current status

The 32-case verification catalog and its documentation sources are current,
declarative and durable.

- #548 and #554 are complete on current main;
- current main and the corresponding durable `build/main` update are green;
- `build/main` contains 32/32 model verification items, 128/128 reference
  child results and all 6 current CADCraft SVG diagrams;
- #548 is complete: all verified examples own preserved human engineering
  documentation in local `README.md` files, while `model.yml` remains the
  agreed generic presentation schema, now including local presentation `priority`;
- the historical case text and geometry-sufficiency rationale were migrated
  verbatim and audited 32/32 with zero mismatches;
- site layout, guide prose and browser scripts are no longer embedded as
  complete pages in `site/build.py`.
- remaining hand-authored site content/configuration, including cheatsheet content
  and verification section labels/priority, must live under `site/content/` rather
  than as Python literals.

The live public Pages site has been deliberately switched back to the preserved
pre-cut-over baseline after the failed #556 cut-over. The snapshot remains on
`backup/gh-pages-before-f11-2026-11-20`.

Do not publish the replacement site again until #497 content-parity, terminology,
grouping/source-comparison and stable-generation checks are green and the
replacement has been reviewed.

The #557 replacement renderer restores the content-parity regressions found
after #556:

- complete Forge source is visible inline on every Verification case page;
- PythonSCAD, pyBOSL2, CadQuery and build123d source is visible inline beside
  each current reference result/preview;
- public routing/navigation/labels use Verification;
- the catalog is grouped into the preserved six functional sections;
- section and example learning order is declarative through local priorities;
- section labels/descriptions and cheatsheet content live under `site/content/`,
  not as hand-authored Python presentation constants.

PR #557 has passed both the selected site-source CAD-CI graph and complete
stable-site generation against resolved durable `build/main` evidence. The live
site remains deliberately on the preserved backup until the replacement is
reviewed and deliberately republished.

The current durable evidence is complete for machine verification but not yet
for visual content parity:

- native visual-verification PNG evidence exists for 5/32 examples;
- the other 27 examples have no current visual-verification policy; #497 adds
  current presentation previews without treating those previews as visual PASS;
- all 128 independent references have current STL + structured verification
  evidence;
- none of those 128 reference outputs currently has a durable rendered image.

## Current goal

Complete #497: generate and publish stable Pages from current Forge source plus
the authoritative generic `build/main` baseline without reducing the useful
engineering information on the preserved public site.

## Required proof for #497

- stable site generation reads accepted evidence from
  `build/main/examples/<slug>/` and the corresponding reference child item
  paths, not from retired `qualification/**` output or batch producer paths;
- per-item `source_commit` provenance is preserved; a sparse durable baseline
  is not misrepresented as one uniform model source commit;
- root `provenance.json` records the site source commit and the immutable
  build-branch commit used for generation;
- all 32 verified examples are present;
- the public site uses `Verification` terminology and URL/navigation labels;
  retired `Qualification` terminology is not presented as the current public
  concept;
- every verification model page shows the complete Forge model source inline
  and shows each available PythonSCAD, pyBOSL2, CadQuery and build123d
  reference source inline beside its current result/preview;
- the verification index is grouped by each example's existing `model.yml.section`
  value; the generator must not replace that distributed metadata with a new
  central hand-authored grouping registry;
- preserved README engineering statements remain verbatim source material and
  are never reconstructed from machine evidence;
- current status, parameters, measurements, geometry checks, saved-design
  results, reference checks and raw evidence links come from durable evidence;
- the six current CADCraft diagrams are consumed from durable build output;
- old-vs-new content inventory covers every public information category before
  cut-over;
- missing native/reference visual presentation is resolved from current durable
  CAD evidence before cut-over; historical images must not be presented as
  current evidence;
- presentation-only source changes reuse accepted technical evidence and do not
  rerun model/reference verification merely to rebuild Pages;
- the complete site is published through released `cad-ci publish pages`;
- no PR Pages preview/cleanup behavior is added in #497; a PR-only complete
  site-generation validation is allowed and does not publish `gh-pages`;
- normal incremental Forge CI and durable build publication remain green after
  merge.

## Execution order

1. Freeze the old-vs-new content/source inventory and durable evidence mapping.
2. [complete in #557] Restore the source-comparison contract, Verification
   terminology and grouped/priority-driven catalog presentation.
3. [complete in #556] Keep verification truth separate from deterministic
   presentation preview derivation.
4. [complete in #556] Implement a Forge-owned durable-evidence loader for canonical
   `build/main/examples/<slug>/` item outputs and per-item provenance.
5. [complete in #556/#557] Render current model/reference/status/measurement/
   saved-design/diagram data through external templates.
6. [complete in #556] Produce deterministic current native/reference
   presentation previews from accepted durable CAD artifacts.
7. [complete in #557] Add regression tests for source visibility, Verification
   terminology, grouping, priorities and configuration separation.
8. [complete in PR #557 CI] Generate the complete stable site from PR source
   plus resolved durable build evidence.
9. Review the generated replacement against the preserved production baseline;
   only then republish the stable root through released `cad-ci publish pages`.
10. Continue #366 for final generic Pages preview/cleanup lifecycle work after
    stable publication is intentionally restored.

## Open issue assessment — 2026-11-20

| Issue | Status | Assessment |
| --- | --- | --- |
| #497 Publish stable Pages from the generic build/main baseline | now | #548 and the 32-case durable baseline are complete; stable Pages is the active migration. Visual parity is the remaining evidence gap before cut-over. |
| #366 Make verified item output durable on build, then cut Pages publication over to tool.cad.ci | blocked | Durable build storage is active; final generic Pages preview/cleanup lifecycle follows #497 stable publication. |
| #391 Extract reusable CAD verification library from Forge | effectively complete but still open | Generic verification ownership and consumer migration are complete; cleanup/close separately. |
| #481 Remove stale Forge development branches | blocked | Current connected tooling cannot safely delete stale refs. |
| #261 Reduce full qualification from minutes to seconds with a reusable CI image | probably obsolete | Superseded by v0.3.2 runtime batching and measured #484 work. |
| #340 Reuse full release qualification after identical squash merge | probably obsolete | Refers to superseded qualification architecture. |
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
| #81 Support inline AnchorFrame references for rotated occurrences | later | Forge API backlog. |
| #9 SCPF: first-class Sketch objects, constraints and face workplanes | later | Major Forge feature backlog. |
| #8 Add generic hollow primitives: Tube, RectTube and OvalTube | later | Major Forge feature backlog. |
| #5 SCPF: generic anchors and parametric constraints for native SolidCraft | later | Major Forge feature backlog. |

Immediate chain:

`#497 stable Pages -> #366 final Pages lifecycle`.
