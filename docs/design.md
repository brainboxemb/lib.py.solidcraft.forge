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

During staged migration, older models keep their existing
`scripts/model_verify.py` + procedural `verify_model.py` path. Each model is
switched explicitly to `scripts/model_verify_declarative.py` in its own
migration change. New generic verification behavior must not be implemented in
Forge.


## Staged item participation

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

During the current staged proof, the `scpf` item remains active and exactly
five model-verification items participate: `simple-box`,
`anchor-topology-mutation`, `attach-angle`, `four-corner-l` and
`xz-anchor`. All other historical model items remain present but are excluded
with `process: false`. Reference items remain independently selectable where
their own changed paths/dependencies require them.


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

## Staged CI selection and evidence

The staged proof separates repository participation, Git selection and build
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

The active model proof set contains the five staged models. Independent
reference items remain independently selected by released CAD-CI; model and
reference execution are not collapsed into one consumer-owned scheduler.

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
reference. The migration must preserve the current Examples/Qualification
split, qualification cases, visible status semantics and main evidence
presentation unless a separately justified change is made.


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


## Example and Pages source flow

The stable site source boundary is:

```text
examples/<slug>/model.yml
  human title/description/concepts/test explanation
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
`EXAMPLES` catalog duplicating their titles/descriptions/concepts.

The example metadata loader validates one stable schema before rendering.
Verification prose is deliberately qualitative. Numeric truth is not parsed
back out of prose; the renderer uses the declarative verification definition
and durable evidence where technical details are required.

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
        |
        v
ci/site-source
  -> metadata schema test
  -> source-only site generation test
```

It has no dependency on either CAD runtime batch.

`model.yml` is deliberately absent from `forge-model-declarative` and
`model-verification-batch` execution inputs. This prevents title,
description, concept or verification-explanation edits from invalidating native
model evidence.
