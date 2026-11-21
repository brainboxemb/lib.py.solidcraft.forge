# Forge design

This document summarizes repository-level responsibility boundaries. Historical/narrow test and verification design records are preserved under
`docs/background/design/`. Current repository-wide rules live here and in
`requirements.md`.

## Main execution path

Forge uses the exact released CAD-CI root action on both review and long-lived
branch integration events:

```text
GitHub workflow
  -> pull request
     -> read cad-ci.yml
     -> execute selected SCons targets
     -> no durable generated-state write
  -> push main/dev-cad/dev-ci
     -> execute selected SCons targets
     -> reconcile/publish only that branch's complete build scope
     -> publish only that branch's Pages root/subtree
```

Promotion pull requests from `dev-cad` or `dev-ci` to `main` request a
complete processed run. The GitHub workflow does not understand runtime
packaging or selected item kinds.

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

## Development-lane CI flow

Forge uses one source-branch topology and one released CAD-CI stack:

```text
feature/fix PR
  -> dev-cad or dev-ci
  -> changed-path-selected verification only
  -> no generated-branch write

push main
  -> selected CAD-CI run
  -> fetch build branch
  -> update-main
  -> publish build/main
  -> build site from prepared-main
  -> publish stable Pages root, preserving dev-cad + dev-ci

push dev-cad
  -> selected CAD-CI run
  -> fetch build branch
  -> update-named dev-cad
  -> publish build/dev-cad
  -> build site from prepared-dev-cad
  -> publish Pages subtree dev-cad

push dev-ci
  -> same flow with dev-ci
```

The pull-request path keeps one `cad_ci_pr` required-check job. Before the
released root action is invoked, Forge may perform one repository-level cheap
classification based only on the changed filenames reported by the GitHub Pull
Request API.

For a normal PR whose base is `dev-cad` or `dev-ci`:

- if every changed filename is below `docs/`, the job reports
  `docs-only` and skips the released CAD-CI action entirely;
- otherwise it invokes the released root action exactly as before.

This classifier is deliberately narrower than CAD-CI item selection. It does
not calculate affected items, dependency closure or SCons targets and therefore
does not duplicate the generic planner.

Promotion PRs targeting `main` bypass the docs-only shortcut and always invoke
the released action with complete validation.

Forge does not call the reusable PR publication workflow and does not prepare,
publish or clean sparse PR scopes.

### Push bootstrap versus update

A development branch can exist before its generated complete scope.

For a normal push with an existing named scope, Forge reads the previous
accepted source commit from `build/<lane>/build.json` and uses that SHA as the
incremental selection/update base:

```text
build/<lane>/build.json.source_commit
  -> CAD-CI base SHA
  -> build fetch
  -> update-named --named generated-build/<lane>
  -> publish build --scope named --scope-name <lane>
```

This is deliberately not derived from `github.event.before`: a recreated
long-lived branch produces a branch-create push whose before SHA is all zeroes,
while the durable named scope still knows the exact previously accepted source
commit.

For the first publication of a lane, the push runs the complete processed graph
and then:

```text
prepare-named --name <lane>
  -> publish build --scope named --scope-name <lane>
```

The workflow decides only whether the named directory exists and which
long-lived source branch is running. It does not calculate item membership or
copy generated item trees.

Main already has a complete baseline and continues to use `update-main`.

### Site evidence scope

Forge's site generator accepts the exact prepared complete build directory plus
its logical scope name.

The evidence loader validates:

- stable scope `main` against a main manifest;
- development scope `dev-cad` or `dev-ci` against a named manifest with the
  same name.

Generated provenance and Verification metadata record the supplied scope.
Relative site links remain unchanged, so the same complete generated site can
be installed either at the Pages root or under one named top-level subtree.

### Pages isolation

Publication uses released CAD-CI mechanics:

```text
main
  -> publish pages
     --preserve-subtree dev-cad
     --preserve-subtree dev-ci

dev-cad
  -> publish pages --name dev-cad

dev-ci
  -> publish pages --name dev-ci
```

The generated branch is shared, but every mutation is scoped. CAD-CI retries a
publication race from the latest generated-branch head; Forge does not
serialize the three lanes through one global concurrency group.

### Promotion

Feature/fix PRs into either dev lane are squash-merged.

Promotion never uses the long-lived lane directly as the PR head. Create one
temporary promotion ref at the accepted lane head:

```text
dev-cad -> promote/dev-cad -> PR main
dev-ci  -> promote/dev-ci  -> PR main
```

The promotion PR requests complete validation and uses a normal merge commit.
Repository automatic head deletion may then remove the temporary promotion
branch without deleting `dev-cad` or `dev-ci`.

After promotion, main publishes stable output from main itself. Both
development lanes are then fast-forwarded/synchronized to the resulting main
head. A development preview is never promoted by copying its generated
build/Page scope into stable output.

If a long-lived lane has to be recreated, its first push still uses the prior
durable named-scope `source_commit` as base. This keeps synchronization
incremental and avoids treating branch recreation as a new full bootstrap.

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

### Historical simple-box proof

Issue #430 originally proved the visual path with `simple-box` first.

Its model-local policy requires front, right and iso regression views and one
expected box from (-20,-15,0) to (20,15,10). Approved historical baseline PNGs
remain model-local and are compared by the released visual API.

That staged proof is no longer the completion boundary. Reopened #378 applies
the same proven path to every active Verification model.


### Historical baseline payload migration

After the simple-box PNG proof, the remaining four staged models reuse their
already-approved historical regression pixels without transcode/reapproval.

Each migrated view stores a model-local JSON payload containing:

- `encoding: zlib`;
- normalized width/height 96 x 72;
- the exact historical decoded compressed/image payload bytes;
- the historical base64 text when canonical, or a provenance-recorded
  canonicalization when legacy padding is invalid;
- approval/source provenance.

The Forge visual adapter asks released `decode_baseline()` to materialize the
payload for `verify_visual_view()`. Forge does not implement zlib/base64/Pillow
decoding.

### Full-catalog visual verification

The former five-model proof established the implementation path but did not
complete #378. Every active Verification model now uses that same path.

Each model owns:

- its required view set;
- approved local baseline image/payload per required view;
- expected boxes;
- expected through-hole/through-slot features where the historical contract
  requires them;
- baseline provenance.

The default required views are front/right/iso. Model-local policy preserves the
historical overrides for cases whose internal geometry is best exposed by top,
front or right views.

Historical approved encoded baseline payloads preserve the decoded compressed
or image bytes exactly in the owning model directory. Canonical base64 text is
kept unchanged; invalid legacy padding may be normalized only when that
normalization is recorded in model-local provenance. There is no restored
central baseline registry.

The visual stage remains inside the existing model-verification item. Expanding
the catalog must not add a second CAD-CI item or duplicate generic image
mechanics.


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

Every active Verification model produces `model_verify/visual.json` containing
released-library semantic visual evidence. F11 maps it back to the existing
public `visual` check and preserves the regression/expected-shape detail needed
by Pages. It never reopens images or reruns comparison.

Absence of visual evidence for an active model is incomplete verification; it
is not mapped to `not-required`. Presentation previews remain separate and
cannot satisfy the visual check.

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

Visual semantics require current evidence for every active model:

- durable `model_verify/visual.json` must be present;
- every model-required view must have current render/regression/expected-shape
  evidence;
- the resulting visual status participates in the normal semantic result;
- `presentation/preview-iso.png` remains presentation evidence only and never
  contributes a visual status.

Historical approved baselines may be migrated as model-local payloads, but PASS
is always recomputed from the current render against that current model-local
policy.

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
`tool.cad.ci 0.16.1`:

```text
push main
  -> tool.cad.ci root action
       -> exact source/base
       -> exact released tool + pinned library source
       -> one selected cad-ci run
  -> cad-ci build fetch
  -> cad-ci build update-main
  -> cad-ci publish build --scope main
       -> immutable build commit
  -> Forge site/build.py
       source = current Forge commit
       evidence = same prepared complete scope
       scope = main
       build commit = publication result
  -> cad-ci publish pages
       --preserve-subtree dev-cad
       --preserve-subtree dev-ci
  -> gh-pages stable root
```

Development pushes use the same runner shape with `update-named` (or
`prepare-named` for first bootstrap), named build publication and named Pages
subtree publication.

The root action leaves the exact CLI stack and materialized `build/` output in
the same workspace. Forge therefore does not transport an Actions artifact,
start a second publication runner, reinstall CAD-CI, or re-fetch the
just-published complete scope before site generation.

Forge owns only source-branch event wiring, the site generator, content
interpretation and provenance composition. Released CAD-CI owns selection,
SCons execution, complete-scope membership/deletion, generated-branch
publication, source freshness and retry.

Pull requests are verification-only and use no reusable PR publication flow,
no sparse durable PR scope and no Pages preview. #366 remains responsible only
for the separate live GitHub Pages source cut-over.


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
