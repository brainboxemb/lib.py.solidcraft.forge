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

It may preinstall frequently reused released libraries and stable dependencies,
including the CAD verification library, for execution efficiency.

Forge does not duplicate those pins. It only supplies:

```text
exact built Forge wheel
model source
model-specific verification data
```

to the selected external runtime.

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

During the current one-model proof, the `scpf` item remains active and only
`simple-box` participates as a model-verification item. All other historical
model items remain present but are excluded with `process: false`. Reference
items remain independently selectable where their own changed
paths/dependencies require them.


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
`forge_example.dependency_wheel("forge-package")` resolves the exact wheel
from the dependency item's output root.

`tool_ci.py tool_build` writes only to its own `CAD_CI_OUTPUT`.
`tool_ci.py tool_test`, `tool_verify.py` and model verification read the
wheel only from the `forge-package` dependency.

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

The active model proof set contains only `simple-box`. Independent reference
items are not part of the model runtime measurement and remain independently
selected by released CAD-CI. A run that also contains reference verification is
therefore not a simple-box-only runtime measurement.

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
forge-package wheel
  -> contract_test
     -> run model-owned examples/<model>/tests against that exact wheel
  -> model_verify
     -> compile model to solidcraft.json with that exact wheel
     -> start released SolidCraft runtime
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

The next #378 step enables only:

- simple-box (already proven);
- anchor-topology-mutation;
- attach-angle;
- four-corner-l;
- xz-anchor.

All use front/right/iso regression views. The first three added models use their
model body expectations as expected boxes. `four-corner-l` retains the
historical arm-level expected-shape decomposition so a mirrored/rotated L corner
cannot pass merely because its outer bounding box is unchanged.

No other model becomes `process: true` in this step.
