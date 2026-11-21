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

## Verification package dependency

Library ownership and runtime packaging are separate concerns.

The released CAD runtime images must not embed `lib.py.cad.verification`.
Forge supplies the exact released verification package through the CAD-CI
dependency graph.

Requirements:

- one `cad-verification-package` item prepares exactly one wheel from the
  pinned released verification source;
- the wheel is built/prepared once per selected graph, not once per model;
- model verification depends on both `forge-package` and
  `cad-verification-package`;
- reference verification depends on `cad-verification-package`;
- both runtime containers mount the dependency wheel read-only and add it to
  `PYTHONPATH`;
- changing the verification-library pin must not require a Docker runtime
  release;
- changing model-local `verification/verify.py` must not require either a
  package or runtime release;
- Forge owns only the dependency pin and transport, never verification-library
  implementation.

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
2. locate the exact released verification dependency wheel;
3. compile/replay the Forge model into the initial native SolidCraft `.sc`
   model;
4. load the model-local `verification/verify.py`;
5. call released `run_solidcraft_verification()`.

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
- model verification items depend on `forge-package` and
  `cad-verification-package` only.

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

During the current staged five-model proof:

- exactly `simple-box`, `anchor-topology-mutation`, `attach-angle`,
  `four-corner-l` and `xz-anchor` have model verification enabled;
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

- Forge uses the exact externally accepted root action from
  `tool.cad.ci 0.15.0`;
- one caller-owned job and one hosted runner execute the complete main
  lifecycle;
- the action performs exactly one changed-path-selected `cad-ci run`; Forge
  does not use `full_run: true`;
- documentation/site-only selection may execute source checks but must not
  start SolidCraft/reference CAD runtimes merely because Pages is published;
- after the action, the same workspace and exact tool/library source stack are
  reused without another checkout, Python setup or BrainboxEmb package install;
- `cad-ci build fetch` materializes the current durable baseline;
- `cad-ci build update-main --base/--head` always reconciles that baseline
  with current processed membership, including deletion-only updates with no
  replacement candidate;
- `cad-ci publish build --scope main` publishes the prepared main scope while
  preserving PR scopes and returns the immutable generated build commit;
- Forge builds the site directly from that same `prepared-main` tree and the
  returned build commit; it does not re-fetch the just-published build;
- `cad-ci publish pages` publishes the complete Forge-owned site from the same
  runner.

There is no Actions artifact transport and no second/third publication runner
on the main path. Forge must not calculate or merge item sets itself. Base/head
selection, build-store membership/deletion, generated-branch freshness and
publication remain released CAD-CI responsibilities.


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
- the diagram result remains a separate CAD-CI item and must not execute Forge
  or SolidCraft models;
- CADCraft is supplied by the immutable released `cad-reference` runtime;
- Forge must not download, cache, checksum or install the CADCraft executable;
- diagram rendering shares the heavy reference container with independent
  reference CAD when the reference batch is active;
- each source renders a non-empty SVG and DXF;
- the item output retains the original source JSON, rendered artifacts and one
  provenance manifest containing tool version, archive checksum and artifact
  hashes;
- source/tool pin changes invalidate the diagram item through normal CAD-CI
  inputs;
- normal model changes do not select the diagram item.

Forge owns these diagram sources and CADCraft command invocation. The CADCraft
binary/version/archive lifecycle belongs to `docker.cad.solidcraft`. This work
does not belong in lib.py.cad.verification because it is
documentation/evidence generation, not generic model comparison.


## Semantic verification summary

F11 restores the semantic qualification result already used by the public
Qualification pages. It must not introduce a new public report vocabulary or a
new sixth visible qualification level.

For each case the public semantic checks remain:

- `integration`;
- `native_model`;
- `geometry`;
- `saved_design`;
- `visual`.

This is the existing schema-5 `qualification-result.json` meaning. The current
Pages presentation and status labels remain the compatibility target.

Independent PythonSCAD, pyBOSL2, CadQuery and build123d results remain separate
reference evidence. Their presence and success are qualification prerequisites,
but F11 must not add a new visible `reference` row to the public case status
summary merely because storage/CI is being migrated.

Forge composes the result only from already-produced CAD-CI, model-verification,
visual and reference evidence. The summary layer must not compile Forge models,
start SolidCraft, execute reference CAD, render/compare images, mutate designs,
or implement a second CAD-CI selector.

Released `lib.py.cad.verification` owns generic semantic status precedence and
composition. Forge owns only the mapping from Forge evidence to the existing
qualification fields.

`saved_design` is `not-required` when no saved-design check exists.

`visual` is `not-required` when the current durable model item has no
`model_verify/visual.json`. A presentation preview is never evidence for a
visual PASS. When `visual.json` exists, its current status and view evidence
remain required and are composed normally.

Independent-reference summary input is read only from the canonical
`examples/<slug>/<implementation>/` child items. Batch producer copies are not
additional public/reference summary inputs.

Missing/failed/error/review/blocked evidence must remain distinguishable.
Evidence references must be preserved.

The original staged F11 proof used five cases. Stable Pages now applies the
same adapter semantics to the complete active catalog using the resolved
durable evidence tree.

F11 code operates on a resolved evidence tree and is independent from producer
execution. Wiring a durable resolved tree into the collector belongs to
#366/#497, so F11 must not create a cold CAD-CI fan-in that rebuilds every
producer.


## Verification runtime batching

Logical verification items remain independently selectable and retain their own
durable output/evidence paths. Expensive CAD runtimes are not required to match
those logical item boundaries.

Forge verification therefore batches expensive runtime work:

- one SolidCraft runtime processes the current declarative model list;
- one reference runtime processes the current independent-reference list;
- build123d uses one isolated interpreter/import for its complete case list;
- CadQuery, PythonSCAD and pyBOSL2 process their complete lists in the shared
  reference process;
- CADCraft processes the complete diagram source list inside the same heavy
  reference runtime batch.

Per-case verification state remains isolated. Each model/reference has its own
input, output directory and structured result. A failure in one case must not
prevent later cases in the same batch from running. After the complete list is
processed, the batch returns failure when one or more cases failed.

CAD-CI continues to own logical selection, dependencies, SCons state, caching
and durable publication. Forge owns only the batch runtime invocation and the
mapping from batch results back to existing per-case outputs. No generic worker
pool or batch scheduler is added to lib.py.cad.ci.


## Example documentation preservation

The #548 migration is a source relocation, not a rewrite.

The last canonical pre-removal case documentation from
`qualification/cases.py` must be preserved verbatim per owning example. The
migration may change headings/formatting and file location, but it must not
summarize, reinterpret or silently omit the existing engineering statements.

The last canonical per-case geometry sufficiency rationale from
`qualification/geometry_contracts.py` must also be preserved verbatim. In
particular, the explanation of why outer bounds are or are not sufficient is
human engineering documentation, not a value to reconstruct later from machine
checks.

`model.yml` keeps only the agreed generic page metadata fields:
`section`, `priority`, `title`, `tagline`, `description`, `parameters`, and
`stages`. It is not a second verification contract.

Machine expectations, tolerances and saved-design checks remain solely in
`verification/verify.py`.

## Example-owned presentation metadata

Every current Forge verification example is self-describing for generated
documentation.

`examples/<slug>/model.yml` is the authoritative source for human-facing
example metadata. The required schema contains:

- `section`;
- positive integer `priority`;
- `title`;
- `tagline`;
- `description`;
- `parameters`;
- non-empty `stages`.

Verification explanation and historical engineering rationale live in the
example documentation, not in additional `model.yml` verification fields.

These fields describe the example for navigation/presentation. `priority` is presentation-only and controls ordering within the example's section; lower values render first. These fields must not become a second machine verification contract. Exact expected geometry, parameters, tolerances and saved-design
expectations remain in `verification/verify.py`.

Generated Pages obtain actual status, measurements and evidence links from the
accepted durable `build/main` item output. `model.yml` must never claim a
current PASS/FAIL result.

The site generator discovers examples from the filesystem and their local
metadata. It must not maintain a central model-name/page-content registry.

## Site source separation

HTML generation must be structurally separated from site data/orchestration.

- complete page layout belongs in external templates;
- reusable dynamic fragments should normally use external templates;
- when Python-generated markup is justified, it must live only in an explicitly
  named HTML-rendering module rather than in `site/build.py`, loaders or
  evidence code;
- prose-heavy guide content belongs in external Markdown or template content;
- CSS and browser JavaScript belong in static files;
- generated API facts continue to come from the public implementation/docstrings;
- example page metadata comes from local `model.yml`;
- preserved engineering explanation comes from local `README.md`;
- executable model facts come from source/verification files and durable evidence.

Source/evidence/orchestration modules may load, validate and normalize data,
construct view-models and write generated output. They must not mix that work
with page markup. HTML belongs to templates or to the dedicated HTML-rendering
module; guide chapters and model-specific SVG galleries remain external data.

The current site must not depend on retired `qualification.*` source modules.
The 32 current `examples/` directories and durable `build/main` are the
catalog/evidence sources.


### Presentation metadata selection boundary

`model.yml` is presentation/documentation metadata. Changing only
`examples/<slug>/model.yml` must not select or invalidate model compilation,
SolidCraft verification or independent CAD reference verification.

The lightweight site-source item owns `model.yml` and `README.md` validation
and generated documentation checks. CAD verification inputs are the model source,
verification contract, model-specific command/test data and shared runtime
helpers only.


## Stable Pages durable evidence contract

Stable Pages combines current source documentation with the accepted generic
`build/main` baseline. The stable site is never a source of verification
truth itself.

- canonical model evidence is read from
  `build/main/examples/<slug>/`;
- canonical independent reference evidence is read from the corresponding
  `build/main/examples/<slug>/<implementation>/` child item;
- batch producer outputs under `build/main/ci/*-batch/` are implementation
  detail, not a second public evidence namespace;
- `build/main/build.json` is authoritative for item membership and per-item
  source provenance;
- unchanged accepted items may have an older `source_commit` than the site
  source commit;
- root site `provenance.json` records both the site source commit and the
  immutable build-branch commit used for generation;
- current status/measurements/results shown by Pages must come from durable
  evidence, not from `model.yml`, README prose or historical Pages output;
- preserved human engineering text remains sourced from the local README and
  must not be regenerated from verification JSON.

The cut-over is a content migration, not a content reduction. The stable site
must retain or replace with equivalent current data the existing useful
example, native, reference, saved-design, visual, diagram and raw-evidence
information categories.

### Durable presentation previews

Every accepted model and independent reference item used by stable Pages must
provide one current deterministic ISO presentation image at:

```text
presentation/preview-iso.png
```

This artifact has presentation semantics only.

- it is derived from the accepted native model or the already-verified
  reference STL belonging to that item;
- it does not create a new verification check or status;
- its presence must never be rendered as `visual=PASS`;
- a model that already produced the current ISO visual-verification render
  reuses that render rather than taking a duplicate snapshot;
- a model without visual-verification policy receives one deterministic
  720×540 SolidCraft ISO snapshot from its accepted model and baseline measurements;
- reference items receive one deterministic ISO render of their verified STL;
- CAD rendering, view choice and camera policy remain Forge-owned consumer
  behavior, consistent with the released CAD verification library boundary;
- historical backup renders may be used only as migration references and must
  never be labelled as current evidence.

Keeping previews in accepted item output allows presentation-only site changes
to reuse current CAD evidence without rerunning model/reference verification.

### Stable Pages publication

Forge owns complete site generation and content. Released CAD-CI owns generated
branch publication.

The stable site is published only as one complete directory through
`cad-ci publish pages`. Forge must not reimplement Pages Git fetch, merge,
retry, race or push mechanics. #497 changes only the stable root; PR preview and
preview cleanup lifecycle remains outside this cut-over.


## Public verification Pages

The current public concept is **verification**, not qualification.

- navigation, headings, page titles and stable public URLs must use
  `Verification` / `verification/`;
- retired `Qualification` terminology may remain only in historical material or
  temporary internal implementation names during migration; it must not be
  presented as the current user-facing architecture;
- every verified model page must show the complete Forge Python model source
  inline;
- every available independent reference implementation (PythonSCAD, pyBOSL2,
  CadQuery and build123d) must show its complete Python source inline beside
  that implementation's current preview/result evidence;
- reference source visibility is source-owned and must not depend on durable evidence availability; source-only builds still show all four reference sources, while stable builds add current durable result evidence beside them;
- source links are supplementary; replacing inline source with links is a
  content regression;
- displayed source must come from the owning example source tree, while
  PASS/FAIL, measurements and generated CAD artifacts continue to come from the
  accepted durable build evidence;
- the verification index must group examples by the existing `section` field in
  each example's `model.yml`;
- grouping order must be deterministic, and no second central catalog of group
  membership may be introduced;
- each example declares a local integer `priority` in its `model.yml`; examples
  inside one section are sorted by that priority and then slug as a deterministic
  tie-breaker;
- section presentation configuration uses `priority`, not positional `order`;
- public section label/priority translation is presentation configuration under
  `site/content/verification-sections.yml`, not Python source;
- the six existing section slugs keep the preserved public labels and order:
  `fundamentals` → `1 · Basic geometry`, `features` →
  `2 · Parent/child features and faces`, `parameters` →
  `3 · Parameters and dependencies`, `components` →
  `4 · Components and occurrences`, `anchors` → `5 · Anchors and local frames`,
  and `associativity` → `6 · Associative relationships`.


## Verification cut-over compatibility

The canonical public terminology and route are `Verification` and
`/verification/`.

The stable site must also preserve the pre-cut-over public
`/qualification/` URLs as compatibility aliases:

- the old root redirects to `/verification/`;
- old case paths redirect to the corresponding current Verification case;
- `coverage/`, `results/` and `joint-anatomy/` redirect to current
  canonical special pages;
- the old `qualification/manifest.json` path serves the exact same current
  manifest bytes as `verification/manifest.json`;
- the six historical joint-anatomy CadCraft JSON paths remain available.

Compatibility output must not reintroduce Qualification as current navigation or
as a second authored content tree.

The canonical Verification site must preserve the standalone knowledge that
existed before cut-over:

- a current durable results table derived from normalized build/main evidence;
- a capability/API coverage page derived from source-owned coverage
  declarations and linked current Verification cases;
- the authored joint-origin/corner-bracket anatomy explanation, backed by the
  current six source-owned CadCraft plans and durable rendered diagrams.

Human explanatory copy belongs in templates/content. Python may validate,
compose rows, resolve evidence URLs and write compatibility aliases.
