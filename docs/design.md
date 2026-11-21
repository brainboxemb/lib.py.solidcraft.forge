# Forge design

This document summarizes repository-level responsibility boundaries. Historical/narrow test and verification design records are preserved under
`docs/background/design/`. Current repository-wide rules live here and in
`requirements.md`.

## Main execution path

Normal Forge CI is intentionally simple:

```text
GitHub workflow
  -> pull request: tool.cad.ci reusable-pr
     -> read cad-ci.yml
     -> execute selected SCons targets
     -> prepare/publish sparse PR output on the same runner
  -> main push: tool.cad.ci reusable-ci
     -> read cad-ci.yml
     -> execute selected SCons targets
```

The GitHub workflow does not understand runtime packaging or selected item
kinds.

## Runtime lifecycle

Runtime construction and release are external to Forge:

```text
docker.cad.solidcraft
  versions.env + Dockerfile
  -> build/test
  -> immutable release vX.Y.Z
  -> ghcr.io/brainboxemb/cad-solidcraft:vX.Y.Z
  -> ghcr.io/brainboxemb/cad-reference:vX.Y.Z

lib.py.solidcraft.forge
  cad-ci.yml
  -> selects both immutable runtime roles
  -> tool.cad.ci injects repository variables
  -> model commands use FORGE_RUNTIME_IMAGE
  -> reference commands use REFERENCE_RUNTIME_IMAGE
```

Forge contains no runtime build or publication path.

A runtime update is explicit:

1. release a new `docker.cad.solidcraft` version;
2. verify both immutable role images in the runtime repository;
3. update the corresponding Forge runtime role variable(s);
4. prove Forge CI against the new release.

## Version roles

`docker.cad.solidcraft` owns runtime SemVer and runtime dependency pins.

`scpf/scpf/version.py::TESTED_SOLIDCRAFT_VERSION` remains Forge's package-level
SolidCraft compatibility behavior.

`cad-ci.yml::variables.SOLIDCRAFT_VERSION` is the SolidCraft version Forge CI
expects from the selected released runtime.

Forge does not own a runtime content hash, timestamp version or Docker release
number.

## Runtime package composition

Runtime package composition belongs to `docker.cad.solidcraft`.

The runtime images contain CAD engines and stable runtime dependencies only.
They do not contain `lib.py.cad.verification`.

Forge supplies separately:

```text
exact built Forge wheel
exact released verification wheel
model source
model-specific verification data
```

to the selected external runtime.

The verification wheel is a CAD-CI dependency output. Updating its pin does not
change or rebuild the runtime image.

## Verification

Model commands consume `FORGE_RUNTIME_IMAGE`. Independent reference commands
consume `REFERENCE_RUNTIME_IMAGE`. Each command pulls and runs only its exact
immutable role image.

Verification behavior stays in released `lib.py.cad.verfication`, including
CAD-tool-specific adapters. Forge keeps Forge compilation and model-specific
expected data.

## Declarative model verification flow

The final model-verification path has one Forge producer step followed by the
released verification-library runner:

```text
examples/<model>/scpf/model.py
  -> scripts/model_verify_declarative.py
     -> exact built Forge wheel
     -> compile Forge model to command document
     -> replay command document to initial native model.sc
     -> load examples/<model>/verification/verify.py
     -> run_solidcraft_verification(model.sc, output, VERIFICATION)
        -> baseline evaluation/checks
        -> saved-design mutation/evaluation/checks
        -> inspections
        -> artifacts + verification.json
```

`scripts/model_verify_declarative.py` may know how Forge produces the initial
native SolidCraft model and how to locate a model-local verification file. It
must not know the SolidCraft measurement schema, implement numeric/body/timeline
comparisons, or duplicate mutation/evaluation verification logic.

Generated SolidCraft timeline names are not model-owned unless explicitly
checked. `SolidCraftTimelineExpectation` therefore uses the released partial
field contract.

All current historical model-verification cases use the declarative
`verification/verify.py` contract. The shared batch producer invokes
`scripts/model_verify_declarative.py` inside the released runtime for each
model. The former procedural `verify_model.py` migration path is historical;
new generic verification behavior must not be implemented in Forge.

## Model item participation

Forge uses released CAD-CI `process` only as declarative repository
configuration.

The flow is:

```text
Forge item ci.yml
  -> process: true|false
  -> released tool.cad.ci
  -> released lib.py.cad.ci planner/executor
```

Forge contains no helper that interprets `process`, no duplicate changed-path
selection and no second execution policy.

The staged proof is complete. All 36 current native model-verification items
now declare `process: true` and participate in normal CAD-CI selection. Reference
items remain independently selectable through their own changed paths and
dependencies.

The former five-model proof set and the activation history of the remaining
catalog are recorded in `background/example-history.md`.


## Forge package CI item graph

Forge uses the existing CAD-CI item dependency/output contract:

```text
forge-package
  output: dist/scpf-*.whl
      |
      +--> forge-tests
      |
      +--> forge-release
      |
      +--> selected model_verify items
```

`forge-package` remains configured by `scpf/ci.yml`. The independent package
checks live under `ci/forge-tests/ci.yml` and
`ci/forge-release/ci.yml`; root `cad-ci.yml` discovers those CI items
explicitly.

The consumer boundary is the generic `CAD_CI_DEPENDENCIES_JSON` mapping.

- `forge-package` exposes the exact Forge wheel;
- `cad-verification-package` exposes the exact released verification wheel.

`forge_example.dependency_wheel(...)` resolves a wheel from the dependency
item's output root.

Model verification mounts both wheels read-only into `cad-solidcraft` and
sets `PYTHONPATH` to those wheel paths. Reference verification mounts only the
verification wheel into `cad-reference` and adds it ahead of the source tree
on `PYTHONPATH`.

`tool_ci.py tool_build` writes only to its own `CAD_CI_OUTPUT`. Verification
package preparation likewise writes only to its own item output.

The item graph deliberately does not encode unit tests or release verification
as prerequisites of model verification. Those checks remain independent CAD-CI
targets and keep source watches that select them when Forge package
implementation changes.

SCons execution order/parallelism remains generic CAD-CI behavior; this Forge
change only makes the dependency graph semantically correct.

## CI selection and evidence

The current flow separates repository participation, Git selection and build
execution:

```text
examples/<model>/ci.yml
  -> process participation
  -> released CAD-CI changed-path/dependency selection
  -> SCons target graph
  -> consumer action
  -> build/<item>/.cad-ci evidence
```

Forge owns only the declarative repository configuration. It does not reproduce
the planner in Forge code or tests.

All 36 current native model-verification items are active. Independent reference
items remain independently selected by released CAD-CI; model and reference
execution are not collapsed into one consumer-owned scheduler.

Run interpretation uses structured CAD-CI evidence, not buffered console order.
Consumer output may be emitted late or grouped by SCons, so console timestamps
are not a reliable per-action timing source.

During CI stabilization, evidence must be inspectable after a representative
run. If the reusable workflow does not retain the generated `.cad-ci` evidence,
the retention mechanism must be added at the workflow/tool boundary rather than
by adding a Forge-local execution tracker.

### Cold-path timing diagnostics

For #484 the Forge-owned model launcher measures its own execution boundary
without changing CAD-CI or verification semantics:

```text
host
  compile Forge command document
  docker pull immutable SolidCraft role
  docker run
      |
      +--> container creation/start -> entry shell
      +--> Python interpreter + module bootstrap
      +--> import released verification library
      +--> produce native SolidCraft model
      +--> run released SolidCraft verification
```

The launcher prints explicit duration values and flushes them immediately.
Host-side phases use a monotonic timer. The container entry shell records the
first executable point inside the container, and the Python process reports the
bootstrap interval from that entry marker to the in-runtime Forge function.
CAD-CI structured action timing remains authoritative for the whole
`model_verify` step; these finer values are diagnostic decomposition inside
that Forge-owned action.

## Model verification contract-test stage

Each processed declarative model item exposes Q2 and native verification as
separate ordered CAD-CI steps:

```text
forge-package wheel + cad-verification-package wheel
  -> contract_test
     -> run model-owned examples/<model>/tests against the Forge wheel
  -> model_verify
     -> compile model to solidcraft.json with the Forge wheel
     -> start released SolidCraft runtime
     -> mount both dependency wheels
     -> replay native model
     -> run released cad-verification model checks
```

A thin Forge-owned model contract-test command resolves `CAD_CI_ITEM` and the
exact `forge-package` dependency wheel, then delegates execution mechanics to
`forge_example.run_contract_tests()`. It contains no model expectations.

Keeping Q2 as its own CAD-CI step makes its pass/fail and timing visible in
normal structured CAD-CI evidence instead of hiding it inside native
verification.

Each active model item watches its own `tests/**` directory. This keeps
CAD-CI/SCons responsible for invalidation and execution; Forge does not add a
second freshness mechanism.

## Durable PR build flow

Pull-request verification and durable publication use one externally accepted
reusable workflow and one runner:

```text
pull_request open/update
  -> tool.cad.ci reusable-pr
     -> checkout exact PR source
     -> execute changed-path-selected CAD-CI graph
     -> materialized build output exists?
        no  -> success
        yes -> prepare-pr --base PR_BASE --head PR_HEAD
             -> publish build --scope pr

pull_request closed
  -> same reusable-pr workflow
     -> no normal CAD-CI execution
     -> publish build-cleanup --pull-request PR_NUMBER
```

There is no intermediate build artifact transport and no second Forge-owned PR
publication runner. The same workspace containing verified `build/` output is
used directly by the released prepare/publish commands.

Forge owns only the GitHub event wiring and the exact accepted reusable workflow
revision. The generic library validates candidate evidence, creates the sparse
build manifest, preserves unrelated generated-branch scopes, checks source
freshness and retries generated-branch races.

Same-repository PRs may publish with the workflow's `contents: write`
permission. Fork PRs keep verification behavior but durable publication is
guarded by the released workflow.

## Stable main bootstrap flow

During the bootstrap, pull requests and main pushes intentionally use different
execution scopes:

```text
pull_request
  -> incremental reusable CAD-CI
  -> optional sparse PR publication

push main
  -> reusable CAD-CI full_run=true
  -> complete artifact for process:true items
  -> prepare-main
  -> publish build --scope main
```

The workflow splits PR and main reusable jobs so a PR does not pay for the
bootstrap full run.

The main publication job:

1. checks out the exact main source commit;
2. installs the exact accepted `tool.cad.ci` revision;
3. downloads the complete verified build artifact;
4. runs `cad-ci build prepare-main`;
5. runs `cad-ci publish build --scope main` with source-freshness checking.

Generic publication replaces the `main/` directory on the generated build
branch while preserving sibling `pr/` scopes.

This bootstrap does not establish the final steady-state main workflow. After
the baseline exists, #366 replaces the full-run bootstrap with incremental
candidate selection plus generic `update-main`.

## Steady-state build publication

Once the generic main baseline exists, the bootstrap full-run path is removed.

```text
PR open/update event
  -> one released reusable-pr job
  -> incremental CAD-CI
  -> build output exists?
     -> prepare-pr --base PR_BASE --head PR_HEAD
     -> publish build --scope pr

PR closed/merged event
  -> same released reusable-pr workflow
  -> no normal CAD-CI verification
  -> publish build-cleanup --pull-request PR_NUMBER
  -> remove only build/pr/PR_NUMBER

main push
  -> cad_ci_main (incremental)
  -> artifact exists?
     -> build fetch -> generated-build/
     -> update-main
          --main generated-build/main
          --base BEFORE
          --head HEAD
     -> publish build --scope main
```

The published item set is derived twice by the same released planner semantics:
once during execution and once when preparing durable output. Forge does not
maintain a parallel selected-item list.

For main updates, stored item rows that are not selected are copied forward
unchanged by the generic build-store. This preserves accepted durable output
without requiring a full model/reference rerun.

The publication jobs retain source freshness checks and generated-branch race
retry from `tool.cad.ci` / `lib.py.cad.ci`.

PR-scope lifecycle cleanup is also delegated to the released stack. Forge only
owns the GitHub event wiring and the PR number; it does not inspect or mutate
generated branch contents itself.


## Nested reference-item migration

Reference implementations are migrated from one catalog-wide command to
directory-owned CAD-CI items.

For the first pilot:

```text
examples/attach-angle/
  ci.yml
  verification/reference_geometry.json
  build123d/ci.yml
  cadquery/ci.yml
  pythonscad/ci.yml
  pybosl2/ci.yml
```

Root `cad-ci.yml` owns reusable Forge-specific templates. Templates contain
generic execution structure only; model names and expected geometry do not live
in them.

For this pilot each child `ci.yml` explicitly selects its root-owned reference
template. This matches the externally accepted consumer shape and keeps the
child configuration inspectable. A child may select a different template when
one implementation needs an extra implementation-specific helper.

The effective flow for a child source change is:

```text
Git base/head
  -> released CAD-CI watch matching
  -> one reference child selected
  -> one child SCons target graph
  -> Forge reference launcher
  -> released runtime
  -> existing reference implementation
  -> released geometry validation
  -> child-owned build output/evidence
```

The shared parent geometry contract participates in every reference child's
watch/input set. A contract change therefore selects all four children through
normal released CAD-CI path matching.

### Transitional aggregate

The old `verification/references` item is not removed until reference coverage
for the active proof set is preserved.

During the attach-angle pilot it becomes a compatibility aggregate for only:

- simple-box;
- anchor-topology-mutation;
- four-corner-l;
- xz-anchor.

It no longer watches or executes attach-angle references. Each later active
model migration removes that model from the aggregate in the same change. The
aggregate disappears after the last active model is split.

This is a migration bridge only. It is not a second planner and it must never
expand back to inactive/all-catalog verification.


## Visual verification flow

Visual evidence remains inside the normal model-verification item and its
existing SolidCraft runtime:

```text
model_verify
  -> replay native model.sc
  -> run_solidcraft_verification()
     -> baseline/measurements.json
  -> Forge visual adapter
     -> derive deterministic camera from baseline measurements
     -> solidcraft-cli snapshot model.sc
     -> camera JSON + actual PNG
  -> released verify_visual_view()
     -> normalize actual/baseline
     -> regression metrics + diff
     -> expected-shape goal
     -> expected-shape overlay
     -> VisualViewEvidence
  -> released compose_semantic_result()
     -> required view result
  -> visual.json evidence
```

There is no second visual CI item or runner for the simple-box proof.

### Camera conversion

For measured global body bounds:

- target is the center of the complete envelope;
- framing size is the largest XYZ span with a 1 mm minimum;
- SolidCraft camera distance is `size * 1.65`;
- SolidCraft front is yaw 0°, pitch 0°;
- right is yaw -90°, pitch 0°;
- top is yaw 0°, pitch +90°;
- iso is yaw -45°, pitch +32°;
- roll is zero and fov is zero.

The corresponding released-library `OrthographicCamera` receives:

- the same target;
- SolidCraft yaw converted to degrees;
- the negated SolidCraft pitch converted to degrees;
- `distance = 0.4 * SolidCraft distance`.

This preserves the established front/top image-axis conventions without
copying generic projection code into Forge.

### Simple-box proof

Issue #430 enables the visual path for `simple-box` only.

Its model-local policy requires front, right and iso regression views and one
expected box from (-20,-15,0) to (20,15,10). Approved historical baseline PNGs
remain model-local and are compared by the released visual API.

Other models are not enabled by this change. The proven path is applied to the
remaining staged proof models later under #378.


### Historical baseline payload migration

After the simple-box PNG proof, the remaining four staged models reuse their
already-approved historical regression pixels without transcode/reapproval.

Each migrated view stores a model-local JSON payload containing:

- `encoding: zlib`;
- normalized width/height 96 x 72;
- the exact historical compressed/base64 pixel payload;
- approval/source provenance.

The Forge visual adapter asks released `decode_baseline()` to materialize the
payload for `verify_visual_view()`. Forge does not implement zlib/base64/Pillow
decoding.

### Five-model staged proof

The active #378 proof set contains only:

- simple-box (already proven);
- anchor-topology-mutation;
- attach-angle;
- four-corner-l;
- xz-anchor.

All use front/right/iso regression views. The first three added models use their
model body expectations as expected boxes. `four-corner-l` retains the
historical arm-level expected-shape decomposition so a mirrored/rotated L corner
cannot pass merely because its outer bounding box is unchanged.

No other model is `process: true` during this staged proof.


## F10 diagram evidence flow

F10 is one independent CAD-CI item discovered through the existing `ci/*`
root pattern:

```text
verification/diagrams/sources/*.cadcraft.json
  -> ci/verification-diagrams
     -> reference-verification-batch
        -> released cad-reference runtime
        -> scripts/build_diagrams.py
           -> use cadcraft-cli already supplied by the runtime
           -> replay each source command list
           -> render SVG (DXF may remain as historical/internal CADCraft evidence)
           -> copy source JSON into output
           -> write provenance.json
     -> verification-diagrams materializes its diagram output
```

The historical sources are restored byte-identically from the last green
qualification. They remain data; the renderer contains no hard-coded geometry
for an individual diagram.

CADCraft 0.20.1 is owned and pinned by the released heavy reference runtime.
Forge keeps only the source-level `cadcraft_version` contract needed to reject
diagram sources for an incompatible runtime. Forge does not own the archive URL,
architecture, checksum, download or installation.

The diagram item does not depend on forge-package. Its expensive rendering is a
dependency output of the shared reference batch; the diagram item itself only
materializes that result.


## F11 semantic summary flow

F11 is an execution-free adapter from the new distributed evidence layout back
to the existing public qualification semantics.

```text
resolved evidence tree
  examples/<case>/.cad-ci/steps/contract_test.json
  examples/<case>/.cad-ci/steps/model_verify.json
  examples/<case>/solidcraft.json
  examples/<case>/model_verify/verification.json
  examples/<case>/model_verify/visual.json
  reference verification.json files
       |
       v
Forge qualification-summary adapter
       |
       +--> released cad_verification semantic composition
       |
       v
schema-5-compatible qualification case meaning
  integration
  native_model
  geometry
  saved_design
  visual
```

The old Qualification pages are the presentation compatibility target. F11
does not invent another public status level.

### Integration

The existing `integration` meaning is restored from the model-owned
`contract_test` CAD-CI step plus the generated non-empty `solidcraft.json`
command document. The command count remains evidence as before.

### Native model

`native_model` represents successful production of the editable native model,
not the correctness of its geometry. The adapter uses the model-verification
step/evidence and native artifacts only; geometry remains a separate check.

### Geometry and saved design

`model_verify/verification.json` is the released verification-library report.
Its `baseline` check supplies `geometry`. Checks whose IDs start with
`saved_design_` supply `saved_design`; no such checks means
`not-required`.

Generic status precedence is delegated to released
`lib.py.cad.verification`.

### Visual

`model_verify/visual.json` already contains released-library semantic visual
evidence. F11 maps it back to the existing public `visual` check and preserves
the regression/expected-shape detail needed by Pages. It never reopens images
or reruns comparison.

### References

Independent reference results stay separate evidence, matching the current
Qualification site. F11 verifies that the expected reference evidence is
present/acceptable for qualification, but does not add a new visible
`reference` status row to the public case result.

### Aggregate and Pages boundary

The staged proof contains the five current proof cases exactly once.

Do not implement F11 as a cold CAD-CI fan-in with every producer in `needs`.
On a fresh runner that would rebuild all producers. The collector consumes a
resolved evidence tree. F11 proves the adapter and result semantics; #366/#497
own durable evidence-tree materialization and Pages wiring.

The snapshot branch
`backup/gh-pages-before-f11-2026-11-20` is the presentation regression
reference. The preserved branch remains the presentation regression reference, but the
current public split is Examples/Verification. Qualification remains historical
terminology; visible status semantics and main evidence presentation are still
preserved unless a separately justified change is made.


## Verification batch execution

The performance boundary is a Forge-owned producer dependency, not a new
CAD-CI execution mode.

The model path is:

```text
selected examples/<case> item
        |
        v
ci/model-verification-batch
  -> compile current declarative model list
  -> pull SolidCraft runtime once
  -> start one container
  -> for each model:
       own input/output directory
       produce native model
       run released verification
       collect pass/fail
  -> batch result tree
        |
        v
selected examples/<case>/model_verify
  -> copy only that case result into the existing item output
```

The independent-reference path is equivalent:

```text
selected examples/<case>/<engine> item
        |
        v
ci/reference-verification-batch
  -> pull reference runtime once
  -> start one container
  -> one Python process handles PythonSCAD/pyBOSL2/CadQuery lists
  -> one isolated build123d interpreter handles the complete build123d list
  -> CADCraft renders the complete diagram list in the same container
  -> collect reference and diagram results before returning failure
        |
        v
selected reference child
  -> copy only its own result into the existing item output
```

Batch inputs include the case membership/configuration files and all source
files consumed by the batch. This prevents a selected child from observing a
stale batch result.

The batch output is an internal Forge verification dependency. Existing
per-case CAD-CI items remain the durable/public ownership boundary.

CADCraft retains one diagram CAD-CI item as its durable ownership boundary.
The heavy reference batch executes the renderer using `cadcraft-cli` from the
released runtime, processes the full source list, records each result and
reports accumulated failures only after all sources were attempted. The diagram
item then materializes only the already-produced diagram evidence.


## Example documentation provenance

The example directory is the ownership boundary for human model/test
documentation. During #548, the last canonical legacy case records are moved
into the corresponding example directories without rewriting their content.

The local documentation preserves the former case fields as readable sections:
goal, Forge API, Forge model, SolidCraft lowering/result, saved-design test and
reference notes. It also preserves the former per-case geometry sufficiency
rationale explaining whether bounds alone prove the intended geometry. These
texts are copied verbatim; provenance identifies the historical source commit.

This local documentation is explanatory only. `verification/verify.py`
remains the executable verification contract, and `model.yml` remains generic
model/page metadata.

## Example and Pages source flow

The stable site source boundary is:

```text
examples/<slug>/model.yml
  generic section/priority/title/description/parameters/stages
            |
examples/<slug>/README.md
  preserved human engineering explanation
            |
examples/<slug>/verification/verify.py
  machine expected verification contract
            |
build/main/examples/<slug>/
  accepted current evidence/status/artifacts
            |
            v
site loader/view-model
            |
external templates + static assets
            |
            v
generated Pages
```

The generator discovers the 32 example directories. There is no central
`EXAMPLES` catalog duplicating their local metadata or documentation.

The example metadata loader validates the agreed `model.yml` presentation schema. A separate documentation loader reads the local `README.md` and
preserves its engineering statements without inference. Numeric truth is not
parsed back out of prose; the renderer uses `verification/verify.py` and
durable evidence where technical details are required.

Site layout uses external templates under `site/templates/`. Shared browser
behavior uses external files under `site/static/`. Task-oriented guide prose
moves from Python modules to external content under `site/content/`.

Python retains only:
- source discovery;
- schema validation;
- API introspection;
- evidence resolution;
- view-model composition;
- template rendering.

Cheatsheet content is declarative site content. Its headings, descriptions,
snippets and linked example slugs live under `site/content/`; the build layer
only loads, validates and renders them. Verification section slug-to-label/order
translation follows the same rule.

HTML rendering is an explicit layer. `site/build.py` and source/evidence
loaders do not assemble markup. External templates own page and reusable
fragment structure by default. If dynamic markup is materially clearer in
Python, it is implemented only in an explicitly named HTML-rendering module;
that module behaves as a renderer and receives normalized/escaped view data.

Legacy `qualification.*` imports are removed rather than recreated. Their
historical presentation semantics may be used as a visual compatibility
reference, but they are not a source-code dependency.


### Documentation-only CI path

The selection boundary for example documentation is:

```text
examples/<slug>/model.yml
examples/<slug>/README.md
        |
        v
ci/site-source
  -> metadata schema test
  -> source-only site generation test
```

It has no dependency on either CAD runtime batch.

`model.yml` and `README.md` are deliberately absent from
`forge-model-declarative` and `model-verification-batch` execution inputs. This
prevents presentation/documentation edits from invalidating native model
evidence.


## Stable Pages evidence adapter

#497 adds one Forge-owned adapter between generic durable build storage and the
existing site view-model/template layer.

```text
source checkout
  examples/<slug>/model.yml
  examples/<slug>/README.md
  examples/<slug>/{scpf,build123d,cadquery,pybosl2,pythonscad}/model.py
          |
          +------------------------------+
                                         v
immutable build commit -> build/main/build.json
                         build/main/examples/<slug>/**
                                         |
                                         v
                              site/build_evidence.py
                                         |
                              normalized evidence rows
                                         |
                                         v
                                  site/build.py
                                         |
                              external HTML templates
                                         |
                                         v
                                complete site directory
```

`site/build_evidence.py` owns only evidence loading/validation/normalization.
It does not render HTML, run CAD or invent human explanation.

For stable generation it receives:

- the materialized `build/main` directory;
- the immutable build-branch commit SHA used for that materialization.

It validates:

- `build.json` uses generic build schema 1 and scope `main`;
- every current verified example has one `examples/<slug>` item row;
- each required reference implementation has its own child item row;
- item evidence is read from the source-path item directory, never from the
  batch producer directory;
- public status comes from item/verification evidence;
- artifact references stay below their owning item root;
- per-item `source_commit` is retained verbatim.

The normalized example evidence contains at least:

- model item status/provenance;
- generated `solidcraft.json`;
- baseline measurements;
- declarative `model_verify/verification.json`;
- saved-design evidence and artifact references;
- `model_verify/visual.json` plus its produced views when present;
- model presentation preview metadata;
- four independent reference verification rows, STL artifacts and presentation
  previews;
- applicable durable CADCraft diagram references.

The adapter does not require all item `source_commit` values to equal the site
source commit. Sparse durable main intentionally preserves previously accepted
unchanged items.

Stable `site/build.py` writes root `provenance.json` with:

- `source_commit`: the source checkout used to generate the site;
- `build_commit`: the immutable generated `build` branch commit;
- `build_scope`: `main`;
- the generic build manifest's `source_commit` for traceability.

This root record describes generation inputs; it does not replace per-item
provenance.

## Durable presentation preview production

Presentation previews are produced with accepted CAD item output so stable
Pages can remain a pure evidence consumer.

### Native SolidCraft preview

`scripts/model_verify_declarative.py` always leaves:

```text
model_verify/presentation/preview-iso.png
model_verify/presentation/preview.json
```

after successful baseline model production/verification.

`scripts/model_visual.py` owns the rendering helper because it already owns
Forge's SolidCraft camera conversion and snapshot invocation.

Rules:

1. Run normal declarative verification first.
2. If the model's visual policy produced `visual/iso/actual.png`, copy that
   exact current render to `presentation/preview-iso.png`; do not invoke a
   second snapshot.
3. Otherwise load the already-produced baseline measurements, compute the
   existing deterministic `iso` camera with `solidcraft_camera()`, and invoke
   one `solidcraft-cli snapshot` against the accepted native model.
4. Use one fixed presentation size of 720×540, matching the existing approved native visual renders, with no grid and no axes.
5. Write `preview.json` recording schema/version, `view: "iso"`, dimensions,
   the source native model path, camera values and whether the image was
   `reused-visual` or `solidcraft-snapshot`.

The presentation preview is not added to the semantic verification check list.
Existing `visual.json` remains the only visual-verification status source.

### Independent reference preview

Each verified reference output leaves:

```text
references/<slug>/<implementation>/model.stl
references/<slug>/<implementation>/verification.json
references/<slug>/<implementation>/presentation/preview-iso.png
references/<slug>/<implementation>/presentation/preview.json
```

Forge owns this renderer because the released CAD verification library
explicitly leaves CAD rendering, view selection and camera values to the
consumer.

A small Forge module under `verification/` renders the already-verified STL
headlessly with the dependencies already present in the reference runtime
(`trimesh` and Pillow). It must not open or execute the original reference
source again.

The renderer:

- loads the accepted STL without changing its geometry;
- derives target and framing only from mesh bounds;
- uses the same visible Forge ISO orientation as native previews: SolidCraft
  uses yaw −45° / pitch +32°, while the released verification projection
  convention represents that same view as yaw −45° / pitch −32°;
- uses a bounding-sphere-based orthographic fit with a fixed margin so geometry
  cannot be clipped by model aspect ratio;
- rasterizes depth-sorted mesh triangles deterministically to a 720×540 PNG;
- writes a neutral deterministic presentation image with no labels, grid or
  axes;
- writes `preview.json` with renderer schema/version, source STL path, camera,
  dimensions and mesh bounds.

Preview rendering failure makes the item output incomplete and therefore fails
the producing Forge step, but it does not change the semantic geometry result
inside `verification.json`.

The shared reference batch renders all previews in its existing runtime before
per-reference materialization, so no extra container is started per child item.

## Stable qualification summary on durable main

Stable Pages reuses `scripts/qualification_summary.py` as the public
five-check adapter. The adapter is execution-free and imports semantic
composition from the exact durable CAD-verification wheel stored in the same
`build/main` baseline.

Reference gates read only:

```text
examples/<slug>/<implementation>/
  references/<slug>/<implementation>/verification.json
```

They do not glob batch producer outputs.

Visual semantics follow current evidence ownership:

- durable `model_verify/visual.json` present: current visual verification is
  required and its actual/goal/overlay/diff evidence is shown;
- no durable `visual.json`: visual is `not-required` for the current
  contract;
- `presentation/preview-iso.png` is shown in both cases but never contributes
  a visual status.

This deliberately avoids carrying historical visual PASS forward without
current evidence.

## Stable Pages content composition

Stable case pages use the current Examples/Verification split and assemble
content from current sources:

- local README: preserved human goal/API/model/lowering/result/rationale/reference
  notes;
- local model/reference Python: editable source, rendered independently of durable evidence availability;
- durable model item: status, parameters, measurements, saved designs, current
  native preview and detailed visual evidence where produced;
- durable reference child items: result measurements, STL and current preview;
- durable diagram item: applicable CADCraft SVGs;
- immutable build links: raw machine evidence.

Presentation previews are visually useful current artifacts, not PASS badges.
Only structured verification evidence may create PASS/FAIL labels.

The preserved branch
`backup/gh-pages-before-f11-2026-11-20` is used only for content-category and
layout regression review. Its images/results are never copied into the new site
as current evidence.

## Stable Pages publication flow

Stable main publication uses one caller-owned runner with exact released
`tool.cad.ci 0.15.0`:

```text
push main
  -> tool.cad.ci root action
       -> exact source/base
       -> exact released tool + pinned library source
       -> one selected cad-ci run
  -> cad-ci build fetch
  -> cad-ci build update-main
  -> cad-ci publish build
       -> immutable build commit
  -> Forge site/build.py
       source = current Forge commit
       evidence = same prepared-main tree
       build commit = publication result
  -> cad-ci publish pages
  -> gh-pages stable root
```

The action leaves the exact CLI stack and materialized `build/` output in the
same workspace. Forge therefore does not transport an Actions artifact, start a
second publication runner, reinstall CAD-CI, or re-fetch the just-published main
scope before site generation.

Forge owns only the site generator, content interpretation and provenance
composition. Released CAD-CI owns selection, SCons execution, durable-store
membership/deletion, generated-branch publication, source freshness and retry.

The PR verification/publication path remains the released
`reusable-pr.yml` workflow. Stable-site PR validation remains a separate
read-only presentation check; #558 does not duplicate the generic PR lifecycle
inside Forge merely to combine that check.

#497 deliberately does not add PR Pages scopes. #366 owns the later generic
preview/cleanup lifecycle and live cut-over.


## Verification page source-comparison composition

The stable model page is primarily a source-and-result comparison page.

For one `examples/<slug>` model, the presentation flow is:

```text
examples/<slug>/scpf/model.py
  -> inline Forge source

examples/<slug>/{pythonscad,pybosl2,cadquery,build123d}/model.py
  -> inline independent reference source rows

build/main/examples/<slug>/**
  -> accepted status, measurements, previews and raw artifacts

README.md + model.yml
  -> preserved engineering explanation and generic page metadata
```

The page renderer joins these sources only for presentation. It does not copy
reference source into durable verification output and it does not infer
verification truth from Python source.

Each reference row therefore contains both halves of the comparison:

1. the complete reference Python source;
2. the accepted current result/preview/evidence for that reference child item.

The Forge source is shown as a first-class block before or alongside the
independent references. GitHub source links remain available but are not a
substitute for visible code.

Public routing and navigation call this area `Verification` and use
`verification/`. Historical `qualification` names are migration/internal
compatibility details only and are not part of the intended public information
architecture.


### Verification catalog grouping

The verification overview is not a flat alphabetical card list. The renderer
uses the existing `ExampleMetadata.section` value loaded from each
`examples/<slug>/model.yml` as the grouping key. Group membership therefore
stays owned by each example and remains part of the agreed presentation metadata
schema.

The renderer groups cards after discovery. Section order is determined by the
section configuration's `priority`; example order inside a section is determined
by each example's local `model.yml.priority`, with slug only as a deterministic
tie-breaker. No central section-membership or example-order registry is introduced.

The section slug-to-label/priority mapping is presentation metadata, not a model
membership registry. It lives as declarative configuration in
`site/content/verification-sections.yml`; Python only loads and validates that
configuration so all renderers use exactly the preserved labels:

```text
fundamentals  -> 1 · Basic geometry
features      -> 2 · Parent/child features and faces
parameters    -> 3 · Parameters and dependencies
components    -> 4 · Components and occurrences
anchors       -> 5 · Anchors and local frames
associativity -> 6 · Associative relationships
```


## Verification special pages and legacy route compatibility

The old published site contained three standalone Qualification pages that are
not ordinary model cases: results, capability coverage and joint anatomy.
They are retained as canonical Verification pages rather than discarded during
the route rename.

```text
site/api_coverage.py + site/capability_map.py
  -> site/verification_special.py row composition
  -> site/templates/verification-coverage.html
  -> verification/coverage/

normalized stable_view_by_slug
  -> site/verification_special.py result rows
  -> site/templates/verification-results.html
  -> verification/results/

authored historical joint explanation
  -> site/templates/verification-joint-anatomy.html
current verification/diagrams/sources/*.cadcraft.json
durable diagram evidence
  -> verification/joint-anatomy/
```

The joint-anatomy human explanation is restored from source commit
`51b79c223939c84980206593fe9b062f474ca220` and remains authored template
content. Its six CadCraft sources are already owned by the current
`verification/diagrams/sources/` tree; stable SVG/DXF URLs are pinned to the
immutable generated build commit.

The `qualification/` output tree is compatibility-only. It contains redirect
HTML, a byte-identical alias of the current Verification manifest, and the six
legacy local CadCraft JSON aliases. It is generated from current membership and
does not become an executable or human-authored catalog.
