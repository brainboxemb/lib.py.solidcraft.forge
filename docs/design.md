# Forge design

This document summarizes repository-level responsibility boundaries. Historical/narrow test and verification design records are preserved under
`docs/background/design/`. Current repository-wide rules live here and in
`requirements.md`.

## Main execution path

Normal Forge CI is intentionally simple:

```text
GitHub workflow
  -> tool.cad.ci reusable-ci
     -> read cad-ci.yml
     -> inject repository variables
     -> execute selected SCons targets
        -> Forge-owned commands
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

lib.py.solidcraft.forge
  cad-ci.yml
  -> selects one immutable released runtime
  -> tool.cad.ci injects FORGE_RUNTIME_IMAGE
  -> model/reference commands pull and run it
```

Forge contains no runtime build or publication path.

A runtime update is explicit:

1. release a new `docker.cad.solidcraft` version;
2. verify that immutable image in the runtime repository;
3. update Forge's `FORGE_RUNTIME_IMAGE`;
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

Model/reference commands consume `FORGE_RUNTIME_IMAGE` from their environment.
They pull and run that exact immutable release.

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

During the five-model proof, the `scpf` item remains active. Exactly five model
verification items participate; the other model verification items remain
present in the repository but are excluded by the released CAD-CI planner.
Shared/reference items remain active where required by existing dependencies.


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

The five active model items form one bounded proof set. The independent
`reference-verification` item is not part of that set and remains independently
selected by released CAD-CI. A run that includes reference verification is
therefore not automatically a five-model runtime measurement.

Run interpretation uses structured CAD-CI evidence, not buffered console order.
Consumer output may be emitted late or grouped by SCons, so console timestamps
are not a reliable per-action timing source.

During CI stabilization, evidence must be inspectable after a representative
run. If the reusable workflow does not retain the generated `.cad-ci` evidence,
the retention mechanism must be added at the workflow/tool boundary rather than
by adding a Forge-local execution tracker.

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

## Durable PR build proof

The first generated-output migration uses the existing reusable build artifact
as the boundary between verification and publication:

```text
cad_ci reusable job
  -> materialized build artifact
     build/examples/simple-box/...
       |
       v
PR publication job
  -> download artifact
  -> cad-ci build prepare-pr --items simple-box
  -> cad-ci publish build --scope pr
       |
       v
generated build branch
  pr/<number>/examples/simple-box/...
```

The publication job is intentionally thin. It checks out the Forge source
revision, installs the exact accepted `tool.cad.ci` revision, downloads the
artifact produced by the reusable CI job and invokes the generic CLI.

The generic library validates candidate evidence, creates the sparse build
manifest, preserves unrelated generated-branch scopes, checks publication
freshness and retries generated-branch races.

The PR proof does not create or update `build/main`. Stable main publication
is a later #366 step after the sparse PR path is proven.

The job runs only for same-repository pull requests, requires
`contents: write` only on that publication job, and never executes for fork
pull requests. Verification itself keeps read-only source permissions.

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
PR event
  -> cad_ci_pr (incremental)
  -> artifact exists?
     -> prepare-pr --base PR_BASE --head PR_HEAD
     -> publish build --scope pr

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
