# CRITICAL FORGE PRODUCT CONSTRAINTS — READ BEFORE CODING

**FORGE IS REPLAY-FIRST. THE NORMAL FORGE OUTPUT IS A STATIC, REPLAYABLE
SOLIDCRAFT COMMAND DOCUMENT.**

**DO NOT INTRODUCE RUNTIME RESULT HANDLES, `$ref` BINDINGS, PHASED EXECUTION,
OR A FORGE-MANAGED LIVE EXECUTION PLAN AS THE NORMAL COMPILER PATH.**

**DO NOT PREDICT SOLIDCRAFT-GENERATED OCCURRENCE NAMES SUCH AS
`Component:1`, `Component:2`, ETC.**

**PLACEMENT IS THE NORMAL WAY TO POSITION OCCURRENCES. LOWER PLACEMENT DIRECTLY
IN `component.create` / `occurrence.copy` WHERE SOLIDCRAFT CAN EXPRESS IT.**

**ANCHORS / ATTACHMENTS / JOINTS ARE ONLY FOR REAL SEMANTIC RELATIONSHIPS.
NEVER ADD A JOINT OR ANCHOR FRAME MERELY TO MAKE ORDINARY PLACEMENT WORK.**

**IF A REQUESTED CAPABILITY CANNOT CURRENTLY BE EXPRESSED RELIABLY IN THE
REPLAY-FIRST MODEL, REMOVE OR REJECT THE IMPLEMENTATION THAT DEPENDS ON THE
UNRELIABLE BEHAVIOUR. DO NOT PATCH OVER IT WITH A NEW INFERENCE, STAGING
TRICK, HEURISTIC, GENERATED NAME, OR OTHER INDIRECT WORKAROUND.**

**ONLY IMPLEMENT A REPLACEMENT WHEN THE SOLIDCRAFT REFERENCE MECHANISM IS
EXPLICIT, REPLAY-SAFE, AND QUALIFIED FOR THAT EXACT COMMAND. IF A PROPOSED
REPLACEMENT IS NOT CLEARLY 100% RELIABLE, STOP AND DISCUSS IT WITH THE USER
BEFORE IMPLEMENTING IT.**

Historical runtime-result-handle work (including PRs #166/#167) is design
evidence only. It is **not** the approved normal Forge architecture.

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
| PythonSCAD / pyBOSL2 / CadQuery qualification reference | `docs/agent/reference-libraries.md` |

Only read additional files when the first source is insufficient. The compact
`docs/agent/forge-api.json` snapshot is generated from the same public Python
objects/docstrings as the human API reference. It is intentionally a first-read
index rather than a full manual: use its exact signature/value and short summary,
then read the linked local guide or relevant implementation/docstring only when
more semantics are needed. Do not edit the snapshot by hand.
For SolidCraft, use the version-pinned local vendor snapshot or local CLI
introspection before any website lookup. Only consult upstream/external
PythonSCAD, pyBOSL2 or CadQuery documentation when the local agent reference
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

Forge describes CAD intent and lowers it to SolidCraft commands. SolidCraft is
the BRep/feature-history engine; do not add a competing geometry or mating
engine to Forge.

## Qualification references

Every qualification case contains:

- `examples/<case>/scpf/model.py`
- `examples/<case>/pythonscad/model.py`
- `examples/<case>/pybosl2/model.py`
- `examples/<case>/cadquery/model.py`

PythonSCAD, pyBOSL2 and CadQuery express the same modelling intent from
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

When changing a qualification model, update its regression/native checks and
all required reference implementations.


## Release discipline

Keep user-visible changes under `[Unreleased]` in `CHANGELOG.md` during
normal development. Do not create or move release tags manually. For a release,
follow `docs/10-release-process.md`: use a `qualification/**` release branch,
bump only `scpf/pyproject.toml`, date the changelog section, require full Q1-Q6
on the release head and main head, then let the generic release workflow create
the annotated tag and GitHub Release.
