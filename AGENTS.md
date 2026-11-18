# CRITICAL FORGE PRODUCT CONSTRAINTS — READ BEFORE CODING

**FORGE IS REPLAY-FIRST. THE NORMAL FORGE OUTPUT IS A STATIC, REPLAYABLE
SOLIDCRAFT COMMAND DOCUMENT.**

**NORMAL FORGE OUTPUT MUST REMAIN REPLAYABLE. WHEN A LATER SOLIDCRAFT COMMAND
NEEDS AN ID RETURNED BY AN EARLIER COMMAND, STORE AN EXPLICIT REPLAY VARIABLE
SUCH AS `$board_2` IN THE REPLAY DOCUMENT. BIND THAT VARIABLE TO THE RETURNED
FIELD DURING EVERY REPLAY. DO NOT STORE THE TEMPORARY SOLIDCRAFT ID IN THE
REPLAY DOCUMENT.**

**REPLAY VARIABLES HOLD VALUES RETURNED BY SOLIDCRAFT THAT A LATER SOLIDCRAFT
COMMAND NEEDS. RUNTIME IDS ARE THE MOST COMMON CASE, BUT THE MECHANISM IS NOT
LIMITED TO IDS. A VARIABLE IS EXECUTION DATA, NOT A SECOND PUBLIC MODELLING API.
LIVE EXECUTION AND FILE REPLAY MUST USE THE SAME REPLAY DOCUMENT AND THE SAME
VARIABLE RESOLUTION.**

**DO NOT PREDICT SOLIDCRAFT-GENERATED OCCURRENCE NAMES SUCH AS
`Component:1`, `Component:2`, ETC.**

**PLACEMENT IS THE NORMAL WAY TO POSITION OCCURRENCES. LOWER PLACEMENT DIRECTLY
IN `component.create` / `occurrence.copy` WHERE SOLIDCRAFT CAN EXPRESS IT.**

**ANCHORS / ATTACHMENTS / JOINTS ARE ONLY FOR REAL SEMANTIC RELATIONSHIPS.
NEVER ADD A JOINT OR ANCHOR FRAME MERELY TO MAKE ORDINARY PLACEMENT WORK.**

**IF AN IMPLEMENTATION DEPENDS ON UNRELIABLE SOLIDCRAFT BEHAVIOUR, DO NOT
HIDE THAT PROBLEM WITH ANOTHER TRICK. FIRST CHECK WHETHER THE REPLACEMENT IS A
NORMAL, DOCUMENTED SOLIDCRAFT WAY TO DO THE OPERATION. FOR EXAMPLE, A GEOMETRY
PICK MAY BE CORRECT WHEN SOLIDCRAFT ITSELF USES THAT PICK TO SELECT A FACE,
EDGE OR JOINT ORIGIN.**

**FOR A FOUNDATIONAL COMPILER CHANGE, WRITE DOWN WHAT SOLIDCRAFT DOES, WHY THE
NEW METHOD MATCHES THE INTENDED CAD OPERATION, AND WHAT CAN MAKE IT AMBIGUOUS
OR FAIL. QUALIFY THOSE CASES. IF THE METHOD IS STILL UNCLEAR OR DEPENDS ON AN
ASSUMPTION WE HAVE NOT PROVED, DISCUSS IT WITH THE USER BEFORE IMPLEMENTING
THE REPLACEMENT.**

Historical runtime-result-handle work (including PRs #166/#167) is design
evidence only. Change 0013 replaces that discarded design with explicit named
replay variables stored in the replay file.

## WRITE SIMPLY

Write like you are explaining the code to another engineer.

- Use short sentences.
- Use normal words.
- Use names that already exist in the code.
- Use SolidCraft command names when you mean a SolidCraft command.
- Avoid architecture jargon.
- Avoid management or academic wording.
- Do not invent new terms if the code already has a clear name.
- If a technical term is needed, explain it in one simple sentence.

Prefer:

> `compile_assembly()` builds the name `Board:2` itself and passes it to
> `joint.create`. Forge does not control that SolidCraft name, so this can
> point to the wrong occurrence.

Do not write:

> the native occurrence identity abstraction violates the replay-safe semantic
> contract.

The goal is simple: a technical reader should understand the sentence the first
time they read it.

Before implementing any foundational compiler change:

1. read these constraints first;
2. read `docs/05-cad-api-design.md`;
3. check the relevant current design/change record;
4. if an implementation would violate any rule above, stop the implementation
   and fix/clarify the design record first.

# SCPF repository instructions

## Read the minimum context

Do not browse external documentation by default. Start with the smallest local
source that answers the task:

| Task | Read first |
| --- | --- |
| Public Forge API lookup/semantics | `docs/agent/forge-api.json` |
| Exact Forge names/signatures/enums | relevant code in `scpf/scpf/` |
| Qualification rules | `qualification/README.md` |
| SolidCraft command/API lookup | `docs/agent/solidcraft.md` |
| SolidCraft version upgrade | `docs/qualification/solidcraft-upgrade-protocol.md` |
| SCPF version/release work | `docs/10-release-process.md` |
| PythonSCAD / pyBOSL2 / CadQuery / build123d qualification reference | `docs/agent/reference-libraries.md` |

Only read additional files when the first source is insufficient. The compact
`docs/agent/forge-api.json` snapshot is generated from the same public Python
objects/docstrings as the human API reference. It is intentionally a first-read
index rather than a full manual: use its exact signature/value and short summary,
then read the linked local guide or relevant implementation/docstring only when
more semantics are needed. Do not edit the snapshot by hand.
For SolidCraft, start with `docs/agent/solidcraft.md` and the generated
version-pinned `docs/vendor/solidcraft/<version>/runtime/` command contracts.
Use local CLI introspection only to regenerate or investigate an explicitly
recorded contract gap, before any website lookup. Only consult upstream/external
PythonSCAD, pyBOSL2, CadQuery or build123d documentation when the local agent reference
does not cover the required operation or when intentionally refreshing that reference.

## Public API source of truth

Read `docs/09-documentation-architecture.md` for the documentation/source-of-truth split.
Exact public names, signatures, defaults, enum members and object-local semantics live
with the Python implementation and its public docstrings. Cross-object design rules that
cannot sensibly live on one Python object remain in `docs/05-cad-api-design.md`.
Generated API/reference output, qualification fixtures, README/site examples and downstream
CAD models do not redefine either source.

If implementation and the API contract disagree, treat that as an
implementation bug or unresolved API decision. Never make a qualification pass
by adding a copied numeric offset when the API should express the relationship
semantically.

## Public API change procedure

1. Read `docs/05-cad-api-design.md`.
2. Decide whether the behaviour is already specified.
3. If specified: fix implementation + focused regression.
4. If not specified: update the API contract first.
5. Update the smallest proving qualification fixture.
6. Update derived user documentation/examples.
7. Keep a model's command-contract tests under `examples/<case>/tests/`.
   Keep only qualification-tooling tests under `qualification/tests/`.
8. Run Q1/Q2 first and only affected native cases while iterating.
9. Run full Q1-Q6 before promotion/release.

When sibling methods use the same public selector or option type, treat that as
one API. Put shared validation/resolution in one code path where practical and
cover every supported variant with unit tests for every applicable sibling
method. A product-specific model or native qualification case does not replace
that unit-test matrix.

Forge describes CAD intent and lowers it to SolidCraft commands. SolidCraft is
the BRep/feature-history engine; do not add a competing geometry or mating
engine to Forge.

## Qualification references

Every qualification case contains:

- `examples/<case>/scpf/model.py`
- `examples/<case>/pythonscad/model.py`
- `examples/<case>/pybosl2/model.py`
- `examples/<case>/cadquery/model.py`
- `examples/<case>/build123d/model.py`

PythonSCAD, pyBOSL2, CadQuery and build123d express the same modelling intent from
different library viewpoints. They are not alternative Forge specifications. Use
`docs/agent/reference-libraries.md` before looking upstream.

When another library lacks a SolidCraft-style associative relationship, compare
the visible geometry and state the semantic limitation in a short source
comment. Do not fake associativity with unexplained coordinates.

## Verification levels

Do not run every model after every edit. The changed paths and proving tests
define the scope.

`qualification/preview_scope.py` is the executable selector for PR work. It
must agree with these rules:

| Stage | When | What runs |
| --- | --- | --- |
| Preflight | Every relevant PR update | Compile all Python, validate workflow structure, run CI contract tests, build/test the website |
| Affected Q1/Q2 | Normal API/model development | All cheap Forge unit tests plus Q1/Q2 evidence and command compilation only for selected cases |
| Affected Q1-Q6 | Final check for native/geometry-sensitive work | `qualification/run_affected.py --cases <selected>` |
| Full Q1-Q6 | Foundational compiler/replay/runtime changes, SolidCraft promotion, release | Every registered case plus the normal full reference/native gate |

How cases are selected:

- A changed `examples/<case>/...` path selects that case.
- A changed Q1/Q2 test selects every case that names that test in
  `qualification/case_evidence.py`.
- Forge modules map to qualification cases through
  `qualification/impact.py`. Unknown or unmapped technical inputs fail safe
  to the full gate; do not silently classify them as presentation-only.
- Changes to the case registry/evidence registry select all cases because they
  change the mapping itself.
- Site/docs/workflow-only changes select no CAD case.
- Reference libraries run only when reference implementation or
  reference-validation code changed.

The selector also reports the required final gate. Work on a source branch with
cheap affected checks while implementing. Open a PR only when the implementation
is reviewable; the PR merge gate then runs the reported final gate on that exact
head/base pair. Do not create an early PR merely to use CI as the development
loop.

Site-only publication uses the same risk decision through
`scripts/reusable_qualification.py`. For a presentation-only source change it
may reuse a structurally valid, complete passing `build/main` baseline without
recalculating every case input hash. Any technical source change must use the
normal technical qualification/promotion flow. Actions-run history is not an
evidence database.

### Qualify main recovery path

When the current published state is out of sync, the operational recovery use
case is always:

`main -> qualification -> build/main -> Pages`

Use the **Qualify main** workflow for this. Do not create a temporary
`qualification/**` branch and do not involve the release workflow merely to
repair Pages or `build/main`.

The workflow qualifies the exact current `main` commit, replaces
`build/main` only after successful qualification, then builds/tests and
publishes stable Pages from that same baseline.

A normal commit that changes `.github/workflows/qualify-main.trigger` on `main` is the
repository-native way to request this recovery. The trigger file carries no
model/source semantics; it is only an explicit operational signal. The same
workflow may also expose a parameterless manual Run workflow action in GitHub.

Do not require an operator or agent to choose Q1/Q2/Q6/full for this recovery
entry point. The workflow owns the qualification policy. Release work remains a
separate process under `docs/10-release-process.md`.

`scripts/ci_preflight.py` is the first hard gate. Keep it cheap. It exists to
catch broken Python, malformed workflow structure, broken publication
contracts and a broken website before third-party CAD libraries or native
SolidCraft are started.

## Qualification performance

Keep the edit-check loop short:

- Q1/Q2 require no SolidCraft.
- Native qualification must support selected cases.
- Time compile/build/eval/snapshot/mutation steps before optimizing startup.
- Reuse a supported persistent native process only when measured useful and
  case isolation remains reliable.
- Full Q1-Q6 is mandatory for SolidCraft-version promotion and final
  main-branch qualification.

A qualification case is a fixed comparison target. Do not change its expected
geometry or its PythonSCAD, pyBOSL2, CadQuery or build123d reference code merely because
Forge changes its defaults or syntax. Migrate the Forge/SCPF fixture so it
continues to produce the established case. Change expected geometry and
external references only when the task explicitly changes that qualification
case itself.

When intentionally changing a qualification model, update its regression/native
checks and all required reference implementations.


## Unit-test geometry contracts

The unit-test layer is the first and cheapest place to prove a general Forge
geometry rule.

- Do not add one body-specific regression when the public rule applies to a
  family of bodies.
- Register supported primitives, body capabilities, CSG operations and general
  features in `scpf/tests/geometry_contracts.py`.
- A general feature must run through the shared body × feature matrix for every
  compatible direct and derived body.
- A new primitive must enter the canonical compiler primitive set and the test
  body registry; the registry-completeness test must fail until both agree.
- Derived join/cut/intersection body cases come from the same operation
  registry as the primitive-pair CSG tests. Do not maintain a second list.
- Keep a focused standalone regression only when the failure is genuinely
  specific and cannot be expressed as a shared API contract.
- When reorganising tests, preserve existing coverage and update qualification
  Q1 evidence paths in the same change.

See `scpf/tests/README.md` for the current test layout.

## Model authoring workflow

When writing or changing an SCPF model:

1. Find the smallest existing working example that uses the required features.
2. Decide which things are separate physical parts and which geometry belongs
   inside one part.
3. Classify numeric fields before coding: lower-case is an editable CAD
   parameter, UPPER_CASE is a fixed constant, and a leading underscore is a
   Forge/build-time input.
4. Use only current API constructs confirmed by the local API snapshot, source
   or a working example.
5. Run `python -m scpf check path/to/model.py`.
6. Compile the model to command JSON when reviewing the generated SolidCraft
   operations.
7. Do not describe a model as working at Q1/Q2 level until those checks pass.
8. Do not claim native SolidCraft behaviour unless the relevant Q3+ validation
   actually ran.

A downstream CAD model such as Simple MFT belongs in the CAD model repository.
Forge qualification models should stay small and abstract so a failure proves
one API rule rather than product-specific geometry.


## Runtime/tool capabilities

Treat stable runtime capabilities as repository knowledge, not as something to
rediscover on every task.

In the ChatGPT project runtime used for this repository, use the connected
GitHub connector as the normal GitHub interface. The connector already carries
the repository authentication; do not look for a local token or test GitHub CLI
authentication first.

Known connector operations used in this repository:

- read repository/branch/commit/PR data and arbitrary supported GitHub GET
  endpoints;
- read, create, update and delete repository files;
- create branches and commits;
- create, inspect and merge pull requests;
- compare commits/trees and read commit/check status;
- inspect workflow runs, jobs, steps and logs;
- list and download workflow artifacts;
- rerun failed workflow jobs/runs when the matching connector action exists.

Known limitation: the connector currently exposes no workflow-run cancel action
and no general workflow-dispatch mutation. The local ChatGPT runtime also has no
`gh` executable. Therefore do not repeatedly probe `gh`, `gh auth status`,
environment tokens or the connector catalog during normal work.

When an operation is needed:

1. use the known connector operation when it is listed above;
2. when it is not listed, check the connector catalog once for that operation;
3. if the connector does not expose it, record the limitation here when it is a
   recurring repository task and choose a repository/workflow design that does
   not depend on that missing operation;
4. re-check a recorded capability only after the runtime/tooling environment
   has explicitly changed.

GitHub Actions runners are a different environment. Repository workflows may
use tools installed/authenticated by GitHub Actions; do not infer runner
capabilities from the ChatGPT runtime, or vice versa.

## Git workflow

Treat one logical change as one branch/PR and finish that change before calling
the task complete. For a multi-file change, prepare the complete patch first
and push one logical commit; do not commit or push once per file. After CI has
run, collect the failures before making one bundled follow-up fix instead of
triggering a new workflow for every small edit.

Parallel work on another existing branch is fine while CI runs. Keep the topics
separate, and merge or otherwise finish the first PR as soon as its checks are
green.

## Generated build output and Pages publishing

`docs/11-generated-output.md` is the normative publication design. Read it
before changing build/Pages branches, previews, evidence links, publication
workflows or cleanup. If code/workflows disagree with that document, fix the
implementation or deliberately change the design first.


Generated output has two branches with different jobs. Do not mix them with
source branches.

1. `main` and PR branches contain editable source.
2. `build` contains generated technical build and qualification output.
3. `gh-pages` contains only the browseable website.

The `build` branch has exactly two scopes:

```text
main/
  examples/<case>/<implementation>/...
  qualification/...
  build.json
pr/<number>/
  examples/<case>/<implementation>/...
  qualification/...
  build.json
```

The item path mirrors the source path. For example,
`examples/simple-box/cadquery/model.py` produces technical output under
`examples/simple-box/cadquery/`; native Forge/SolidCraft output for
`examples/simple-box/scpf/model.py` lives under
`examples/simple-box/scpf/`. Do not create top-level `native/`,
`references/` or other producer-oriented trees on the `build` branch.
Only cross-case reports belong under `qualification/`.

Pages uses the matching scope model:

```text
/                         # stable main website
previews/pr-<number>/     # one website preview per open PR
```

Rules:

- A PR may replace only `build/pr/<number>/` and
  `gh-pages/previews/pr-<number>/`.
- Updating a PR replaces those same directories. Do not create `fast`,
  `full`, branch-name or staging variants.
- Closing a PR removes both generated PR directories. A merged technical PR
  promotes its verified overlay before cleanup.
- Normal technical merge promotion replaces only affected case/implementation
  directories in the complete `build/main/` baseline. A scheduled/manual full
  Q1-Q6 safety run may rebuild the complete baseline.
- Replacing the stable Pages root must preserve `previews/`.
- `preview-output` and `qualified-output` are not part of the architecture.
  Do not publish new data to them.
- The website never lives on `build`; technical build evidence never lives in
  the stable Pages root merely to stage publication.
- `gh-pages/qualification/` is the public readable qualification section.
  It contains HTML, documentation source and presentation-only material.
  Generated commands, native files, renders, measurements and reference
  evidence belong on `build`; public qualification pages link to that output.
- A presentation-only PR does not create `build/pr/<number>/`. Its Pages
  preview reuses the latest qualified `build/main/` evidence.
- Every generated build uses schema-v2 `build.json` with per-case and
  per-implementation source commit, input hash, build scope and achieved
  verification level. Mixed-age evidence must remain truthful.
- Every generated website has `provenance.json` and is verified before
  publication.
- Workflows orchestrate setup and publication. Path selection, build layout,
  cleanup and other repository rules belong in tested Python code, not inline
  shell/Python workflow logic.
- CI artifacts may retain additional heavy/intermediate evidence. They are not
  a third generated branch or an alternative source of truth.

The intended flow is:

`PR source -> required merge gate -> sparse build/pr/<number>/`

`resolved build/main + PR overlay -> gh-pages/previews/pr-<number>/`

and after a technical merge:

`verified PR overlay -> scoped promotion -> build/main/`

`build/main -> stable gh-pages root`.

All public technical links use the immutable generated-branch commit SHA.
Publication uses the retrying publisher in `scripts/publish_generated.py`;
normal workflows must not force-push generated branches.

Do not publish failing technical evidence as stable.

## Release discipline

Keep user-visible changes under `[Unreleased]` in `CHANGELOG.md` during
normal development. Do not create or move release tags manually. For a release,
follow `docs/10-release-process.md`: use a `qualification/**` release branch,
bump only `scpf/pyproject.toml`, date the changelog section, require full Q1-Q6
on the release head and main head, then let the generic release workflow create
the annotated tag and GitHub Release.
