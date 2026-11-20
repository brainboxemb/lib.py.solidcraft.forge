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

During the current staged proof:

- `simple-box` remains enabled only as the representative pipeline/example fixture;
- the staged verification models are `anchor-topology-mutation`, `attach-angle`,
  `four-corner-l` and `xz-anchor`;
- every other historical model item remains explicit `process: false`;
- independent reference items remain separately selected by normal released
  CAD-CI changed-path/dependency semantics;
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

The staged proof is considered reliable only when representative active-model
changes can be explained from:

1. the repository configuration;
2. the released CAD-CI selected graph;
3. the resulting structured item/step evidence.

For #484, performance interpretation must additionally separate immutable
SolidCraft image acquisition from subsequent container/process/model work.

The Forge-owned model launcher may emit diagnostic duration lines for:

- Forge command compilation;
- immutable image pull;
- Docker container creation/start to the container entry shell;
- Python interpreter/module bootstrap from container entry to the Forge runtime
  function;
- total container/process execution;
- in-runtime verification-library import;
- native model production;
- released SolidCraft verification;
- total in-runtime work.

These durations are diagnostics only. They must not affect selection, execution,
pass/fail decisions or structured CAD-CI evidence. Verification semantics must
not be weakened to improve timing.

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

For pull requests Forge delegates the complete lifecycle to the exact externally
accepted `tool.cad.ci` reusable PR workflow:

- one reusable PR job performs changed-path-selected CAD-CI execution;
- if materialized `build/` output exists, the same runner invokes
  `cad-ci build prepare-pr --base/--head`;
- the same runner publishes the sparse PR scope with
  `cad-ci publish build --scope pr`;
- no GitHub artifact upload/download boundary exists between verification and
  PR publication;
- no second Forge-owned publication runner exists;
- on `pull_request.closed`, normal CAD-CI execution is skipped and the same
  reusable workflow invokes `cad-ci publish build-cleanup`;
- same-repository PR publication may use `contents: write`; fork PRs must not
  receive durable publication privileges;
- generated-branch validation, source freshness and retry behavior remain
  released CAD-CI responsibilities.

Forge must not install/build its own copy of the accepted CAD-CI stack inside a
second publication job and must not implement its own build-store copy,
manifest validation, generated-branch race retry or Git publication logic.

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

The main/push path keeps write permission confined to its separate publication
job. The PR path uses the accepted single-runner reusable PR workflow, which
owns the required PR publication permission and same-repository guard.

The bootstrap full run is transitional. Once a valid generic main baseline
exists, future #366 work must use partial main updates rather than requiring a
full run for every main change.

## Steady-state durable build updates

After the generic `build/main` baseline exists, normal durable publication is
incremental.

For pull requests:

- Forge calls the exact accepted `reusable-pr.yml` revision once;
- that single reusable job remains changed-path selected;
- `cad-ci build prepare-pr --base/--head` derives the sparse durable scope from
  the same released planner semantics on the same runner;
- the PR scope contains all affected processed top-level items, not a
  Forge-hard-coded model name;
- unrelated item output is absent;
- close-only events execute only released PR-scope cleanup and do not run normal
  CAD-CI verification;
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


## Visual model verification

Forge visual verification separates model/engine policy from generic image
mechanics.

Forge owns:

- which views a model requires;
- conversion from measured SolidCraft body bounds to the deterministic
  SolidCraft snapshot camera;
- the `solidcraft-cli snapshot` invocation;
- approved model-local baseline images or approved encoded baseline payloads;
- model-local expected geometry;
- the fact that visual verification is required for that model.

Released `lib.py.cad.verification` owns:

- normalization and image comparison;
- visual-regression metrics and diff creation;
- orthographic projection and expected box/hole/slot drawing;
- goal and overlay generation;
- one-view `VisualViewEvidence`;
- generic semantic result composition.

A visual-enabled model stores policy below its own verification directory:

```text
examples/<model>/verification/
  visual.json
  baselines/
    <view>.png | <view>.json
```

`visual.json` contains data only. It must not contain Python callbacks or a
second implementation of generic image/projection logic.

An approved encoded baseline payload may use the released verification-library
baseline schema (`encoding`, `width`, `height`, `data`) plus provenance fields.
Forge must delegate payload decoding to released `decode_baseline()`; it must
not copy base64/zlib/image decoding logic. A migrated historical payload is
preserved byte-for-byte in its encoded `data` field.

The historical render contract remains:

- SolidCraft snapshot: 720 x 540;
- normalized regression: 96 x 72;
- changed-pixel threshold: 12;
- maximum mean absolute difference: 6.0;
- maximum changed-pixel fraction: 0.08.

Approved baselines are versioned model data. A CI render must never replace or
approve its own baseline.

For each required view, normal model verification retains:

- actual PNG;
- SolidCraft camera JSON;
- regression diff PNG when a baseline exists;
- independent expected-shape goal PNG;
- overlay PNG;
- structured view evidence with pass/fail/missing state.

The visual stage reuses the baseline measurements already produced by
`run_solidcraft_verification()`. It must not reevaluate the native model only
to derive camera bounds.

The historical projection convention remains:

- front view: X right, Z up;
- top view: X right, Y up.

SolidCraft and the verification library share yaw direction. The equivalent
verification-library orthographic camera uses the negated SolidCraft pitch and
a half-height distance equal to `0.4 * SolidCraft distance`.


## Versioned verification diagrams

Forge retains the historical CADCraft verification/documentation diagrams as
versioned source evidence.

Requirements:

- diagram sources live below `verification/diagrams/sources/`;
- the required source set contains the historical joint/corner-bracket diagrams;
- every source declares the exact supported CADCraft version;
- the renderer is a separate CAD-CI item and must not execute Forge models,
  SolidCraft models or independent reference CAD;
- CADCraft 0.20.1 x86_64 is downloaded only from the pinned release URL and its
  archive SHA-256 is verified before extraction;
- each source renders a non-empty SVG and DXF;
- the item output retains the original source JSON, rendered artifacts and one
  provenance manifest containing tool version, archive checksum and artifact
  hashes;
- source/tool pin changes invalidate the diagram item through normal CAD-CI
  inputs;
- normal model changes do not select the diagram item.

Forge owns these diagram sources and CADCraft-specific invocation. This work
does not belong in lib.py.cad.verification because it is documentation/evidence
generation, not generic model comparison.


## Semantic verification summary

Forge composes final verification meaning only from evidence that has already
been produced by normal CAD-CI/model/reference work.

The summary layer must not:

- compile Forge models;
- start SolidCraft;
- execute PythonSCAD, pyBOSL2, CadQuery or build123d;
- render or compare images;
- mutate saved designs;
- implement a second CAD-CI selection or dependency engine.

Released `lib.py.cad.verification` owns generic semantic status validation,
precedence, evidence preservation and aggregate composition. Forge owns the
semantic names and the mapping from Forge evidence to those names.

For each staged model the required semantic checks are:

- `native_model` — the CAD-CI `model_verify` step completed successfully and
  produced its declared model output;
- `geometry` — the baseline `cad-verification` check is present and passing;
- `saved_design` — every `saved_design_*` verification check passes, or the
  semantic check is `not-required` when no such check exists;
- `visual` — the model-local visual semantic result is present and passing;
- `reference` — all four independent reference implementations for the model
  are present and passing.

The summary must preserve evidence references for every semantic check.

Missing required evidence maps to `missing`; explicit failed evidence maps to
`fail`; explicit review/blocked/error states remain distinguishable when
present. The summary must not convert an incomplete result into pass merely
because no producer was executed.

The staged verification aggregate contains exactly these four model IDs once each:

- `anchor-topology-mutation`;
- `attach-angle`;
- `four-corner-l`;
- `xz-anchor`.

`simple-box` is deliberately excluded from the verification aggregate. Its current verification scaffolding is representative infrastructure proof for the pipeline/example and must not make it appear as a verified project/model.

Summary composition must be executable against a resolved tree of existing
evidence. It must not require declaring all model/reference producers as direct
CAD-CI prerequisites merely to read their already accepted results, because on
a fresh hosted runner such a fan-in would cold-rerun every prerequisite.

Wiring the completed summary into durable build/Pages publication is subsequent
#366/#497 work. F11 proves the semantic consumer and its five-model result
without introducing publication logic into verification code.
