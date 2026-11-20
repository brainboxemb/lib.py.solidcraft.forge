# Forge requirements

This document records stable repository requirements. Cross-object API behavior is documented in `docs/api.md`; exact public
signatures/defaults remain implementation/docstring-owned.

## CI ownership

- `tool.cad.ci` is the only generic CAD-CI planner/executor.
- Forge workflows remain thin orchestration.
- Forge owns Forge compilation, model definitions and model-specific
  expectation data.
- Shared verification behavior comes from released
  `lib.py.cad.verfication`, including CAD-tool-specific adapters such as the
  SolidCraft adapter.

## SolidCraft runtime ownership

The reusable SolidCraft CAD runtime is owned by
`brainboxemb/docker.cad.solidcraft`.

Forge is a consumer only.

Therefore Forge must not own or duplicate:

- the runtime Dockerfile;
- runtime dependency/version pins;
- runtime image build/publication workflows;
- runtime release/version management.

Root `cad-ci.yml` declares the exact immutable released role images Forge
consumes:

```text
FORGE_RUNTIME_IMAGE=ghcr.io/brainboxemb/cad-solidcraft:v0.2.0
REFERENCE_RUNTIME_IMAGE=ghcr.io/brainboxemb/cad-reference:v0.2.0
```

Changing either runtime role is a two-repository operation:

1. change, test and release a new immutable version from
   `docker.cad.solidcraft`;
2. deliberately update Forge's corresponding immutable role image.

Forge never derives a runtime version from source hashes, timestamps or local
Docker files.

## Runtime consumption

Forge CAD-CI commands read the injected repository environment:

- `FORGE_RUNTIME_IMAGE` is the exact immutable released SolidCraft
  model/visual verification image;
- `REFERENCE_RUNTIME_IMAGE` is the exact immutable released independent
  reference-engine image;
- `SOLIDCRAFT_VERSION` is the SolidCraft version expected by Forge CI.

Model verification must not use the reference image. Independent reference
verification must not use the SolidCraft image.

Consumer commands do not parse `cad-ci.yml` themselves.

A missing released image is an error. Forge CI must not build or publish a
runtime implicitly.

## Forge package compatibility

The package keeps its own tested SolidCraft compatibility guard. CI must verify
that its declared `SOLIDCRAFT_VERSION` agrees with the package compatibility
contract.

## Shared runtime efficiency

Library ownership and runtime packaging are separate concerns.

The external runtime may preinstall exact released libraries used by nearly
every verification run, including `lib.py.cad.verfication`, together with
stable heavy dependencies.

Preinstallation:

- is an execution-efficiency choice;
- does not transfer code ownership to the runtime repository;
- must not cause Forge to copy or modify verification-library implementation;
- must not require Forge to duplicate those runtime dependency pins.

## Declarative model verification

A migrated Forge model owns only model-specific verification data.

For SolidCraft-backed model verification:

- the model may define a `SolidCraftVerification` value in
  `verification/verify.py`;
- body counts, expected bounds, parameter values, timeline expectations,
  mutation command paths and other model-specific expected values remain with
  the model;
- `verify.py` contains data only and must not contain checker callbacks;
- the model must not parse SolidCraft result JSON, invoke SolidCraft
  verification commands, construct verification checks or write
  `verification.json`.

The shared Forge launcher owns only the producer boundary required before
verification:

1. build/locate the exact Forge wheel;
2. compile/replay the Forge model into the initial native SolidCraft `.sc`
   model;
3. load the model-local `verification/verify.py`;
4. call released `run_solidcraft_verification()`.

Shared SolidCraft evaluation, mutation, inspection, schema interpretation,
comparison and report construction are responsibilities of released
`lib.py.cad.verfication`.

Model migrations are proven in reviewable batches after the representative
simple-box proof.


## Staged model participation

Forge may declare released CAD-CI item participation with the generic
`process` field.

- Forge does not parse, plan or execute `process` semantics itself.
- `tool.cad.ci` / `lib.py.cad.ci` remain the sole owners of those semantics.
- `scpf` tool/library build and tests must remain processed during staged model
  verification.
- A staged proof may explicitly mark selected model verification items
  `process: true` and other model verification items `process: false`.
- Shared/reference items remain processed where the current dependency graph
  requires them.
- Changing staged participation must not alter model verification ownership or
  verification-library boundaries.


## Forge package CI dependency boundary

Forge package creation, Forge unit tests and Forge release verification are
separate CAD-CI items.

- `forge-package` builds the SCPF wheel exactly once and publishes `dist/`
  as its item output.
- `forge-tests` depends on `forge-package`, installs that exact dependency
  wheel and runs the reusable Forge unit suite.
- `forge-release` depends on `forge-package`, uses that exact dependency
  wheel and runs the fixed release-verification example set.
- model verification items depend on `forge-package` only.

A model verification must not require `forge-tests` or `forge-release` to
complete before its own model check can execute.

The test and release-verification items must watch Forge package source as well
as their own test/example sources so a package implementation change still
selects both checks.

The package wheel must not be rebuilt independently by tests, release
verification or model items. All consumers use the output root supplied by the
generic CAD-CI dependency context.

This split changes dependency ownership only. It does not add Forge-local
selection, scheduling, caching or parallel-execution policy.

## CI reliability during staged verification

Forge CI must run only against an exact externally accepted `tool.cad.ci` /
`lib.py.cad.ci` release pair.

During the current one-model proof:

- `simple-box` is the only model verification item with `process: true`;
- every other historical model item remains explicit `process: false`;
- independent reference items remain separately selected by normal released
  CAD-CI changed-path/dependency semantics;
- reference execution is not part of the simple-box model runtime measurement;
- Forge must not add a second planner or consumer-side changed-path engine to
  enforce this staging.

Structured CAD-CI evidence is authoritative for what executed.

For every selected item/step that runs, the current CAD-CI evidence under the
item's `.cad-ci` namespace must be sufficient to determine:

- item and step identity;
- execution outcome;
- whether the consumer action executed;
- run start/finish;
- action start/finish and duration when an action executed.

Console text is diagnostic only and must not be the sole source used to decide
what CI actually executed.

The one-model proof is considered reliable only when representative
`simple-box` changes can be explained from:

1. the repository configuration;
2. the released CAD-CI selected graph;
3. the resulting structured item/step evidence.

For #484, performance interpretation must additionally separate immutable
SolidCraft image acquisition from subsequent container/process/model work.
Verification semantics must not be weakened to improve timing.

## Model command-contract coverage

The staged model-verification path preserves the former Q1/Q2 ownership split
without retaining the old qualification runner.

- Q1 is reusable Forge API/compiler evidence and is covered by the normal
  `forge-tests` unit suite.
- Q2 is model-owned command-contract evidence under
  `examples/<model>/tests/`.
- Every processed declarative model verification item must run its own
  command-contract tests against the exact `forge-package` wheel before
  native SolidCraft replay.
- A Q2 failure fails that model item before native verification starts.
- `verification/verify.py` remains data-only and does not contain Q1/Q2 test
  code.
- The fixed `forge-release` example set is release verification and is not a
  substitute for Q2 coverage of every processed model item.
- A processed model item's CAD-CI watch/step inputs must include its
  `examples/<model>/tests/**` files so changing the contract test invalidates
  and reruns that model verification.

This restores command-contract coverage without reintroducing the historical
qualification orchestration.

## Durable generated build output

Successful transient verification output becomes durable only through the
released CAD-CI build-store/publication commands.

For the first migration proof:

- the reusable Forge CAD-CI job remains the only producer of candidate
  `simple-box` verification output;
- a downstream publication job may consume the reusable workflow's materialized
  build artifact but must not rerun model verification;
- the candidate is validated by `cad-ci build prepare-pr`;
- the sparse PR candidate contains only the explicitly selected
  `simple-box` item path;
- the accepted candidate is published by `cad-ci publish build` below
  `build/pr/<pull-request>/examples/simple-box/`;
- the item-local public `.cad-ci` evidence is preserved;
- existing `build/main` and unrelated PR scopes are preserved;
- Forge must not implement its own build-store copy, manifest validation,
  generated-branch race retry or Git publication logic.

Publishing a PR build scope is permitted only after the reusable CAD-CI job
succeeds. Publication is a consumer of accepted verification output, not an
alternative verification path.

The first proof is intentionally limited to same-repository pull requests where
the workflow token can write the generated `build` branch. Fork PRs must not
gain write publication privileges.

## Stable build main bootstrap

The retired Forge-owned `build/main` format is not an input to the current
generic build store.

The first authoritative generic main baseline is created from a complete
accepted run of the current processed item set:

- PR verification remains incremental;
- the bootstrap main push runs all `process: true` items;
- staged `process: false` items do not participate and do not require output;
- the reusable CAD-CI artifact is the only candidate-output source;
- `cad-ci build prepare-main` validates and packages the complete processed
  candidate;
- `cad-ci publish build --scope main` replaces only the generated
  `build/main` scope;
- existing `build/pr/*` scopes are preserved;
- the retired main manifest is neither parsed nor translated;
- every stored item keeps its public `.cad-ci` evidence.

Only the publication job receives `contents: write`. Verification jobs remain
read-only consumers of source/packages.

The bootstrap full run is transitional. Once a valid generic main baseline
exists, future #366 work must use partial main updates rather than requiring a
full run for every main change.

## Steady-state durable build updates

After the generic `build/main` baseline exists, normal durable publication is
incremental.

For pull requests:

- the normal reusable CAD-CI run remains changed-path selected;
- `cad-ci build prepare-pr --base/--head` derives the sparse durable scope from
  the same released planner semantics;
- the PR scope contains all affected processed top-level items, not a
  Forge-hard-coded model name;
- unrelated item output is absent;
- when a pull request is closed or merged, Forge invokes released
  `cad-ci publish build-cleanup --pull-request <number>`;
- close-only events must not run normal CAD-CI verification;
- cleanup must preserve `build/main` and every unrelated PR scope;
- Forge must not implement generated-branch deletion logic itself.

For main pushes:

- the reusable CAD-CI run remains changed-path selected and must not use
  `full_run: true`;
- if no materialized build artifact exists, durable publication is skipped;
- otherwise the publication job fetches the current generated `build` branch;
- `cad-ci build update-main --base/--head` starts from the current
  `build/main` baseline and replaces only affected processed item paths;
- unchanged item output and manifest rows remain preserved;
- `cad-ci publish build --scope main` publishes the updated main scope while
  preserving all PR scopes.

Forge must not calculate or merge item sets itself. Base/head selection,
build-store validation and publication remain released CAD-CI responsibilities.


## Isolated reference items

Independent reference implementations for an active model are CAD-CI items in
their own source directories.

For a migrated model:

```text
examples/<model>/
  verification/reference_geometry.json
  build123d/
    ci.yml
    model.py
  cadquery/
    ci.yml
    model.py
  pythonscad/
    ci.yml
    model.py
  pybosl2/
    ci.yml
    model.py
```

Requirements:

- each reference implementation is independently selectable from Git changes;
- the directory containing the child `ci.yml` is its item root;
- child configuration uses released item-root and parent-relative path
  semantics; it must not repeat the full model repository path;
- a child source change selects that child only unless an explicit shared input
  also changed;
- the model-local `verification/reference_geometry.json` is a shared input of
  all four reference children, so changing it selects all four;
- reference children do not depend on the Forge model item merely to inherit
  selection state;
- model-specific geometry expectations remain only in the model-local contract;
- shared Forge scripts may derive model/reference identity from generic
  `CAD_CI_ITEM_PATH` context, but must not contain a model-name registry;
- released `lib.py.cad.verfication` remains the owner of generic geometry
  validation behavior.

During staged migration, a temporary aggregate reference item may cover active
models whose references have not yet been split. That aggregate:

- must exclude every model already migrated to isolated reference children;
- must not process `process: false` model references;
- is transitional and is removed when the active proof set is fully migrated;
- must not cause a child-only change in a migrated model to trigger
  all-catalog reference verification.

Forge must not add a second Git-diff selector or cache/fingerprint mechanism.
The exact released CAD-CI planner owns affected-item selection.
