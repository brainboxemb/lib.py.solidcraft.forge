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
7. Run Q1/Q2 first and only affected native cases while iterating.
8. Run full Q1-Q6 before promotion/release.

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

Generated site output has three separate states. Do not mix them.

1. **Source branch** — editable Forge code and documentation.
2. **Preview/staging output** — build output owned by one PR or branch.
3. **Stable output** — the last fully qualified `main` build.

Rules:

- A branch or PR may only replace its own preview output.
- Preview output must never overwrite stable output.
- Preview Pages live under a branch/PR-specific path such as
  `previews/pr-123/`.
- Only a fully successful `main` Q1-Q6 qualification may replace stable
  output.
- Stable publishable output lives on the generated `qualified-output`
  branch. Treat that branch as generated data, not source code.
- `gh-pages` is only a serving branch. Do not rebuild Forge or qualification
  data there.
- Promote already-built output to Pages; do not independently rebuild the site
  during publication.
- Replacing the stable Pages root must preserve the `previews/` subtree.
- Updating one preview must not touch the stable root or another preview.
- Every generated preview/stable output must contain `provenance.json` with
  at least the source branch/PR, source commit, Forge version, SolidCraft
  version when applicable, workflow run id, qualification status/level and
  generation time.
- Verify provenance before promotion. The source commit in stable output must
  match the successful `main` qualification commit.
- Keep heavy qualification evidence such as STEP files, complete native build
  trees and large render sets as CI artifacts. Generated Git branches contain
  only publishable output plus provenance.
- Generated output is latest-only. Do not build an ever-growing Git history of
  generated site files.
- Changes under `site/**` are product changes and must trigger the same
  qualification needed before stable publication.
- Site capability/coverage data must be checked against the real public API.
  Removed methods must not remain published as stale documentation.

The intended flow is:

`source branch -> branch-owned build -> preview page`

and, only after full qualification:

`main -> qualified-output -> stable gh-pages root`.

Do not publish a failing or partially qualified build as stable merely because
the site renderer itself succeeded.

## Release discipline

Keep user-visible changes under `[Unreleased]` in `CHANGELOG.md` during
normal development. Do not create or move release tags manually. For a release,
follow `docs/10-release-process.md`: use a `qualification/**` release branch,
bump only `scpf/pyproject.toml`, date the changelog section, require full Q1-Q6
on the release head and main head, then let the generic release workflow create
the annotated tag and GitHub Release.
