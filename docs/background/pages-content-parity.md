# Stable Pages content-parity audit

This document records the #497 cut-over from the preserved pre-F11 Pages site
to the current source + durable `build/main` architecture.

The preserved comparison baseline is
`backup/gh-pages-before-f11-2026-11-20`.

## Rule

The cut-over preserves engineering information, not the retired execution
layout. Current machine claims must come from current durable evidence. Old
images or statuses are not relabelled as current merely to make the new site
look complete.

## Inventory

| Preserved Pages information | #497 current source | Disposition |
| --- | --- | --- |
| Example title, intent and explanation | `model.yml` + local `README.md` | Preserved |
| Forge API/model/lowering explanation | local `README.md` | Preserved verbatim from the canonical migration source |
| Forge model source | current source commit | Preserved inline on every Verification case, with source link |
| Generated SolidCraft commands | durable model item `solidcraft.json` | Preserved, immutable build link |
| Native SolidCraft model/result | durable `model_verify/native/**` | Preserved |
| Editable parameters and measured bodies | durable baseline `measurements.json` | Preserved |
| Geometry verification details | durable `verification.json` | Preserved as exact machine evidence |
| Saved-design mutation results | durable `saved_designs/**` | Preserved where required |
| Native page preview | durable presentation preview | Replaced by a deterministic current preview |
| Current visual actual/goal/overlay/diff | durable `visual.json` + images | Preserved where the current model owns `verification/visual.json` |
| PythonSCAD reference | current `examples/<slug>/pythonscad/model.py` + canonical durable child item | Preserved as inline source beside current result/preview |
| pyBOSL2 reference | current `examples/<slug>/pybosl2/model.py` + canonical durable child item | Preserved as inline source beside current result/preview |
| CadQuery reference | current `examples/<slug>/cadquery/model.py` + canonical durable child item | Preserved as inline source beside current result/preview |
| build123d reference | current `examples/<slug>/build123d/model.py` + canonical durable child item | Preserved as inline source beside current result/preview |
| Reference expected/measured result | child `verification.json` | Preserved as exact JSON evidence |
| Reference CAD artifact | child `model.stl` | Preserved |
| Reference render | child presentation preview | Replaced by a deterministic current render of the verified STL |
| Raw evidence links | immutable generated build commit | Preserved; no Actions-artifact links |
| CADCraft engineering/setup diagrams | durable verification-diagram item | Preserved and displayed from current SVG evidence |
| Per-item source provenance | `build/main/build.json` | Preserved |
| Site/build provenance | root `provenance.json` | Added explicitly |
| Public catalog terminology | site templates/routes | Current public concept is `Verification`; `Qualification` remains historical/internal only |
| Functional catalog grouping/order | `model.yml.section` + local `model.yml.priority` + `site/content/verification-sections.yml` | Preserved six learning groups and their historical learning order |

## Representative case heading mapping

The preserved `qualification/simple-box/` page was checked heading-by-heading
against the replacement Verification case composition:

| Preserved heading | Replacement presentation |
| --- | --- |
| What this example makes | Verification hero goal from local `README.md` |
| Forge code | Inline complete Forge source |
| API used | Engineering explanation → Forge API |
| Reference code / PythonSCAD / pyBOSL2 / CadQuery / build123d | Independent references, each with inline source beside current preview/result evidence |
| How Forge builds it in SolidCraft | Engineering explanation → lowering |
| SolidCraft result | Engineering explanation → SolidCraft result + current durable verification |
| Editable parameters | Current durable verification → editable parameters |
| Body size | Current durable verification → measured native bodies |
| Visual result / Iso / Front / Right | Current visual verification where owned; otherwise the deterministic current presentation preview |
| Integration tests | Current status line + exact verification checks |
| Geometry checks | Exact verification checks + preserved geometry rationale |
| Saved-design test | Preserved explanation + current saved-design evidence |
| Raw test files | Durable raw evidence links pinned to the immutable build commit |
| Reference documentation | Preserved local README reference notes |

This mapping is representative of the 32 cases because all case pages are
composed through the same templates and source/evidence adapters. Per-case
human text remains example-owned rather than reconstructed centrally.

Reference source rendering is independent from durable evidence. A source-only
build still shows the complete Forge source and all four independent reference
sources. Stable Pages adds the accepted result/preview/geometry evidence beside
those sources, including the accepted evidence-source commit/link.

## Intentional differences

### Historical visual verification is not presented as current evidence

The preserved site had visual-verification output for the historical catalog.
The current declarative catalog presently owns explicit visual policies for a
subset of models.

#497 does not copy the old PNGs forward and does not infer a current visual
PASS from a presentation preview.

For a model with current `model_verify/visual.json`, Pages shows current
actual/goal/overlay/diff evidence and its PASS/FAIL state.

For a model without current `visual.json`, Pages shows:

- its current durable model-verification status;
- a deterministic current presentation preview;
- visual verification as `not-required` for the current verification
  contract.

The historical visual files remain available on the preserved backup branch,
but they are not labelled as current verification.

### Reference presentation uses one canonical current view

The preserved site stored several presentation renders per independent
reference. Current reference verification truth is the verified STL plus exact
geometry evidence. #497 adds one deterministic isometric presentation preview
for each current verified STL.

This is an intentional presentation simplification, not a verification
reduction: the STL and expected-versus-measured geometry evidence remain
available through immutable durable links.

### Batch outputs are not a public evidence namespace

The model/reference batch items remain implementation/materialization
producers. Pages reads model and reference evidence from the canonical
source-path items under `build/main/examples/**`.

## Publication provenance

A stable site records:

- exact Forge source commit;
- exact immutable generated `build` commit;
- build-manifest source commit.

Public machine-evidence links pin the immutable generated build commit and a
path below `main/`. Temporary GitHub Actions artifacts are transport between
CI jobs only and are never linked by Pages.
