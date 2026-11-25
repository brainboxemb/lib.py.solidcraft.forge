# Forge design

## Purpose

Forge is a clean consumer of the corrected `template.cad.library` architecture.

```text
cadlib/                     public scpf package
models/                     physical CAD model owners
modules/
  ci/                       selection/runtime orchestration
  builder-*                 standard CAD adapters
  solidcraft-reference/     canonical runtime command-registry evidence
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

## Native component drawing boundary

Component drawings are Assembly-owned presentation state. A component
definition remains geometry/feature intent and does not own a drawing, because
one definition may have many physical occurrences.

Forge lowers `with_drawing()` to native `drawing.create`,
`drawing.sheet.set`, `drawing.view.standard`, component-filtering
`drawing.view.edit` calls and `drawing.close`. SolidCraft owns the part
template, standard front/top/right/isometric layout and fitted scale. A4 is the
Forge default; A3 remains an explicit native template choice for larger or more
complex parts.

All component, occurrence, drawing, drawing-source, sheet and view identities
come from replay-bound SolidCraft command results. Forge never predicts browser
names or native ids.

The replay document may also declare a drawing PDF artifact by its safe
implementation-relative path, for example
`drawings/Block-drawing.pdf`. `builder-scpf` owns the actual build path:
after the native model replay succeeds it reopens `model.sc`, opens the
replay-bound drawing and calls SolidCraft `drawing.export` with
`format="pdf"`. The PDF is therefore a native vector drawing artifact, not a
screenshot and not a Python-rendered document.

For a component selected from a larger Assembly, SolidCraft currently computes
the standard view group's fitted scale before Forge narrows the base views to
that occurrence subtree. Projected top/right views inherit the main view
source. The result remains native and safe, but the scale can be conservative
for a small component inside a much larger Assembly.

## SolidCraft command-reference boundary

The canonical SolidCraft command registry is a Forge-owned engineering
reference, not a CAD model and not generated Pages content.

```text
root ci.yml immutable SolidCraft runtime pin
        ↓ modules/solidcraft-reference
solidcraft-cli --version + commands
        ↓
docs/reference/solidcraft/<version>/
  commands.json
  commands.md
  SOURCE.md
```

`modules/solidcraft-reference` validates registry completeness, captures and
normalizes the exact runtime registry, renders the human catalog/provenance, and
compares the checked snapshot back to the same immutable runtime. Its item watch
includes `docs/reference/solidcraft/**`, so reference changes select their
own verifier. Historical version directories remain immutable evidence.

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
  drawings/
    <drawing>.pdf
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

The Forge homepage follows the generated homepage contract established by
`template.cad.library#63`. Repository-owned `site/home.yml` declares the
ordered hero, flow, navigation and catalogue blocks. Pages validates that
source with `homepage.py`, resolves Forge-owned generated values from
`landing_metadata()`, and writes temporary `data/home.json`. Hugo then
renders that manifest with the Forge-specific presentation classes in
`site/layouts/home.html`. The layout owns structure and styling only; Forge
copy, routes and external destinations are not hardcoded there. The SolidCraft
model website is therefore one normal generated navigation destination rather
than a template exception.

Verification keeps its Forge-owned presentation taxonomy in `docs/verification/sections.yml`. During Pages preparation that declaration is validated, sorted by section priority and projected into a temporary Hugo resource catalogue. Every owner projected to Verification must name one known section through `model.yml.section`; the Verification list renders those sections in declared order and sorts the model cards inside each section by model priority. This is presentation metadata only and does not create additional model owners or CAD build scopes.

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

Forge consumes the generic stable-main release boundary from
`template.cad.library@e9fb95cd22cb574d615d0bf9a8115c30bbac7ddf`.

Product qualification and release metadata are deliberately separate. A
product-changing stable source still receives a normal full Forge qualification
and becomes the durable `build/main` product baseline. A later release commit
does not rebuild the 47 unchanged model owners merely because version/changelog
metadata changed.

The accepted release path is:

```text
qualified main product source
  -> release/vX.Y.Z from main
  -> CHANGELOG.md + cadlib/pyproject.toml:project.version only
  -> semantic delta preflight
  -> library + modules/release only; zero models
  -> squash to main through /merge
  -> release-only stable check, preserve prior build/main product evidence
  -> /release exact-main-sha
  -> main -> dev synchronization
```

CI records such candidates with `release_only: true`. Build publication
validates source freshness but deliberately does not replace the prior durable
full stable scope.

`modules/release` validates that retained product scope and then validates the
exact requested release source history. The full baseline must remain a
library + all-owner PASS. Every first-parent stable commit between that baseline
and the release target must be single-parent and may change only
`CHANGELOG.md` and the `project.version` value in
`cadlib/pyproject.toml`. Any product/source/model/dependency/build-config
change requires a new normal full stable qualification.

`.github/workflows/release.yml` checks out the exact requested source with
history, performs this repository/template-owned evidence validation, and then
delegates publication to released `tool.py.lib.ci v0.2.1`. The shared
publisher still requires the requested SHA to equal current `main` HEAD.

Forge-specific release metadata remains consumer-owned in
`cadlib/release.py`: package version, dated changelog section, active
release-blockers and `TESTED_SOLIDCRAFT_VERSION`. It emits release notes but
owns no generic build, tag or GitHub Release mechanics.

`release/*` is a first-class temporary branch whose valid integration target
is stable `main`; other temporary branches target `dev`. Branch cleanup uses
the same target mapping so cleanup cannot legitimize an invalid branch
integration.

Pages and `gh-pages` are not release evidence.
