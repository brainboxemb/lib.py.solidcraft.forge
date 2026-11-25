# Forge NEW design

## Purpose

Forge NEW is a clean consumer of the corrected `template.cad.library` architecture.

```text
cadlib/                     public scpf package
models/                     physical CAD model owners
modules/
  ci/                       selection/runtime orchestration
  builder-*                 standard CAD adapters
  verification/             local generic cad_verification
  preview/                  deterministic presentation rendering
  build/                    durable generated-output publication
  release/                  stable release-evidence qualification
  pages/                    Hugo projection/publication
site/                       Hugo/Hextra source
docs/                       repository contract and migration record
```

## Physical model boundary

The model owner is the same concept used by `template.cad.model-project`.

```text
models/simple-box/
  ci.yml
  model.yml
  scpf/model.py
  cadquery/model.py
  build123d/model.py
  pythonscad/model.py
  pybosl2/model.py
  verification/geometry.json
```

CI selects `simple-box` once. Its `ci.yml` expands the implementations required by that model. The build branch groups all implementation evidence below `models/simple-box/`.

`model.yml.purpose` is a list-like policy field and may contain `example`, `verification`, or both.

## SCPF boundary

The template role `cadlib` is the actual `scpf` package. Forge-specific compilation is consumer-owned logic.

The intended Forge path is:

```text
models/<id>/scpf/model.py
        ↓ cadlib/scpf compiler
SolidCraft command JSON
        ↓ generic builder-solidcraft
model.sc + model.stl + native model.png
        ↓ reference verifier
owner-local geometry/semantic evidence
```

Reference implementations use the standard PythonSCAD, pyBOSL2, CadQuery and build123d builders directly inside the same physical owner.

Native feature inputs keep native identity where SolidCraft provides it. For
example, an associative sheet fold stores the finished one-line Sketch Shape in
the Forge feature tree. Lowering emits that Sketch as
`sketch.create -> sketch.line -> sketch.finish`, then emits
`sheet.fold {sketch, curve}`. The older fixed two-point form remains a
compatibility path and lowers to `sheet.fold.points`. This avoids baking a
symbolically driven bend line into coordinates that stop following later
parameter edits.

## Runtime graph

Reference implementations build and verify in one `reference` container batch. SCPF-generated SolidCraft commands execute in `solidcraft`; their STL then enters the `reference` verification role.

The scheduler understands capabilities and runtime dependencies, not Forge engine names.

## Durable output

```text
build/<scope>/models/<owner>/
  result.json
  source.json
  model.stl
  model.png
  scpf/
  cadquery/
  build123d/
  ...
```

Owner-level canonical artifacts come from the configured primary implementation. Each implementation retains its own result and verification evidence.

Pages reads the durable scope and links generated files on the build branch. Generated CAD artifacts are not copied into `gh-pages`.

Workflow roles follow `template.cad.library`: pull requests run only the central `ci` qualification job; permanent `dev`/`main` events run one `build` job that executes selected project work and publishes the durable scope. After publication that build dispatches the independent `pages.yml` workflow and finishes without waiting for Pages.

The schema-2 `build-plan.json` also records whether the independent `cadlib` owner was selected and qualified. Stable release qualification requires `library: true`, a full build, all active owners selected, and owner-local successful evidence whose source provenance matches the exact release commit.

## Pages projection

`models/<id>/` remains the single physical owner. Pages creates views from that owner according to `model.yml.purpose`:

- `example` → `/examples/<id>/`;
- `verification` → `/verification/<id>/`;
- `[example, verification]` → both routes.

The two routes are presentation views over the same owner and durable `build/<scope>/models/<id>/` evidence. They are not separate model owners and do not duplicate CAD artifacts into `gh-pages`.

The reusable Hextra model presentation is consumed from the accepted `template.cad.library` design: expected setup, featured native/primary result, primary source and generated commands, independent reference source/result pairs, image/check overviews and raw verification evidence.

Forge-specific documentation is projected separately:

```text
docs/guide/                         authored Guide chapters
docs/cheatsheet.yml                authored Cheatsheet data
docs/api-reference.json            retained rich public API reference contract
docs/api.md                        API design contract
docs/verification/                 coverage + joint-anatomy authored sources
docs/pages-parity.json             fixed historical route/content gate
        ↓ modules/pages
site/content/...                    temporary Hugo projection
        ↓ Hugo
rendered Pages
```

`api_reference.py` uses Python AST to validate the retained public reference contract against `cadlib/src/scpf` without importing the package. `verification_special.py` reads authored coverage/joint documentation and durable build evidence without executing CAD. The final Pages verifier consumes `docs/pages-parity.json` so route and identifying-content regressions fail CI before publication.

## Migration comparison

Before moving historical code, classify it as:
- **SCPF product behavior** → `cadlib/`;
- **physical-model expectation** → `models/<id>/`;
- **generic verification** → `modules/verification/`;
- **generic runtime/builder behavior** → standard module;
- **presentation** → Hugo/Pages;
- **obsolete orchestration/duplication** → remove after parity.

Expand migration only after accepted A/B evidence: 1 → 5 → 10 → remaining graph.

## Release boundary

Forge consumes the generic library release boundary from
`template.cad.library`.

`modules/release` is a pure stable-evidence reader. It validates the exact
requested `build/main` scope and never creates tags, releases or Pages output.

`.github/workflows/release.yml` is a thin issue-comment adapter. It uses the
released `tool.py.lib.ci v0.2.1` parser, checks the exact stable durable
evidence through `modules/release`, and then delegates annotated-tag and GitHub
Release publication to that released reusable workflow.

Forge-specific release metadata remains consumer-owned in
`cadlib/release.py`: package version, dated changelog section, active
release-blockers and `TESTED_SOLIDCRAFT_VERSION`. The validator emits release
notes but owns no generic build, tag or GitHub Release mechanics.

The checked-in package version `0.15.0` is the immutable historical migration
baseline. Forge NEW intentionally rejects release requests at or below that
version. A first actual NEW release requires an explicit version bump and dated
changelog section.

Pages and `gh-pages` are not release evidence.
