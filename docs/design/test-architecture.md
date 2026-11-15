# Forge test and qualification architecture

Status: **draft from foundational audit 2026-11**

This document defines which layer each test is allowed to prove.

A test is not stronger merely because it compares more generated JSON. The
important question is whether it checks a Forge semantic contract, a
SolidCraft-adapter contract, or an actual native CAD result.

## 1. Layers

### T1 — Public/semantic model tests

Scope:

- public constructors and decorators;
- DefinitionId / OccurrenceId;
- copy semantics;
- Placement values;
- parameter/dependency classification;
- grouping graph;
- attachment graph;
- validation and early rejection.

These tests must not know:

- SolidCraft occurrence ids;
- SolidCraft browser names;
- command ordering caused only by the native adapter;
- the fact that SolidCraft creates one implicit first occurrence.

Examples after the IR migration:

```python
right = left.copy(placement=Placement(x=40))

assert right.occurrence_id != left.occurrence_id
assert right.definition_id == left.definition_id
assert right.placement.x == 40
```

### T2 — Native-adapter command contract tests

Scope:

- which SolidCraft 0.42 command represents one semantic operation;
- result bindings and logical references;
- parameter/native-expression lowering;
- SolidCraft-specific first-occurrence handling;
- command order when the 0.42 engine contract requires it.

These tests may know native command names and schema fields.

They must still not predict browser labels such as `Panel:2`.

Identity-dependent command tests should expect a logical result reference, for
example conceptually:

```json
{"occurrence": {"$ref": "occurrence:<forge-id>"}}
```

and a binding from the producing create/copy command.

### T3 — Execution-plan tests

Scope:

- binding validation;
- phase splitting;
- result capture;
- live/headless replay;
- atomic checkpoint/restore;
- fresh ids on replay.

These tests use fake transports for error cases and focused native 0.42 tests
for the actual result schema.

### T4 — Native Q4 geometric/relationship qualification

Scope:

- SolidCraft successfully builds and saves;
- native bodies/bounds;
- actual occurrence transforms;
- actual joint/relationship inspection;
- hierarchy where hierarchy itself is the capability.

A T4 test may inspect actual native ids/names as evidence, but it must not
promote a generated name into a Forge contract.

### T5 — Native Q5 saved-design mutation

Required whenever a public capability claims a persistent associative
dependency.

The mutation happens **without rerunning Python**.

Examples:

- parameter-dependent component size;
- parameter-dependent Placement;
- attachment gap/offset;
- topology-backed anchor;
- reference-backed feature placement.

T5 is the authoritative proof that a dependency survived lowering.

### T6 — Visual regression

Scope:

- orientation and gross assembly/layout errors that are difficult to infer from
  scalar bounds alone.

Visual evidence supplements semantic/native assertions; it does not replace
them.

### TR — Cross-library reference qualification

PythonSCAD, pyBOSL2 and CadQuery implement the same modelling intent
idiomatically.

They verify the expected geometry/modelling interpretation, not Forge native
identity.

## 2. Current test-suite classification

### `scpf/tests/test_assembly.py`

Current state: **mixed T1 + T2; must split**.

Keep as T1 after rewriting:

- `copy()` Placement semantics;
- distinct definition vs occurrence behaviour;
- parameter publication intent;
- authored name lookup;
- group graph validation;
- attachment intent;
- AnchorFrame/Topology value validation.

Move to T2:

- `component.create` / `occurrence.copy` decisions;
- `occurrence.move` expression fields;
- native joint frame structure;
- material command deduplication;
- custom joint-origin lowering;
- native browser visibility command.

Delete/replace accidental assertions:

- every literal `Block:1`, `Panel:2`, `Marker:1`, etc.;
- “all groups grounded” as an expected consequence of grouping.

### `scpf/tests/test_explicit_sketch_primitives.py`

Current state: mostly T1/T2.

Split semantic Sketch API tests from exact SolidCraft sketch/extrude command
tests. When semantic profile centring is implemented, tests must target
`anchor=CENTER` rather than preserve manual centring offsets.

### `scpf/tests/test_generic_geometry.py`

Current state: mostly T1/T2 and generally appropriate.

Keep polygon naming/validation semantic checks separate from exact sketch
command details.

### `scpf/tests/test_live.py`

Current state: T3 transport/execution tests.

This is the correct home for:

- single-batch atomic execution;
- result-binding phased execution;
- checkpoint rollback;
- replay;
- connection/authentication errors.

When Phase 1 restores result binding, reuse the proven historical PR #166 test
ideas rather than mixing these tests into assembly compilation.

### `scpf/tests/test_models.py`

Current state: broad T1/T2 integration suite.

Keep public API/validation tests in T1. Move exact native command-shape
assertions to focused adapter tests over time.

This file should not become the catch-all location for new compiler behaviour.

### `scpf/tests/test_version.py`

Current state: version policy tests; keep.

Version policy must derive from one source:
`TESTED_SOLIDCRAFT_VERSION`.

## 3. Current qualification tests

The `*CommandTests` classes under `qualification/tests/` are T2 fixture
contracts. Keep them only where they assert meaningful generated intent.

The `*NativeTests` classes guarded by `NATIVE_ROOT` are duplicate/stale
T4/T5 implementations and are not executed in the current CI path.

The actually authoritative native validation is:

```text
qualification/native_validation.py
qualification/visual_validation.py
```

### Migration rule

- move any unique assertion from skipped native unittest classes into the
  central validator;
- verify equivalence;
- delete the skipped native class;
- never keep two native truth sources.

## 4. Qualification utility tests

These remain normal Python tests:

- `test_case_selection.py`;
- `test_native_runtime_metadata.py`;
- `test_reference_models.py`;
- `test_report_template.py`;
- `test_visual_tools.py`.

They validate the qualification infrastructure itself, not CAD semantics.

## 5. Required new foundational tests

### Identity

- one physical occurrence -> one OccurrenceId;
- `.copy()` -> new OccurrenceId, same DefinitionId;
- duplicate insertion of one occurrence -> rejected;
- no generated SolidCraft label appears in semantic IR;
- native create/copy result id is bound and reused downstream;
- replay obtains fresh ids.

### Definition identity

- identical build inputs share one definition;
- different fixed numeric input separates definitions;
- conflicting inherited parameter values cannot be deduplicated away;
- bool/string/enum build variants separate definitions;
- namespace collision `Foo 2` vs `Foo_2` does not collide.

### Grouping

- grouping does not change relationship graph;
- grouping does not imply grounding;
- grouping an already attached assembly remaps both ends correctly;
- externally attached grouped child remains semantically equivalent.

### Parameters

- literal text equal to a parameter name remains unchanged;
- parameter publication alone does not count as dependency proof;
- root model and `@assembly` both detect lost dependencies.

### Rotation

For each supported attachment reference type:

- rotated parent;
- rotated child;
- initial build;
- native relationship inspection;
- saved mutation where associative.

Unsupported combinations must fail before command generation.

## 6. Architecture gate for tests

A new test must state which layer it belongs to.

A test should be rejected during review when it:

- uses a SolidCraft display name in a semantic assertion;
- treats one successful initial render as proof of associativity;
- duplicates an existing native truth source;
- encodes a workaround without naming the SolidCraft version/capability it is
  protecting;
- checks implementation ordering that is not required by either Forge
  semantics or the pinned native command contract.

## 7. Q1-Q6 interpretation after remediation

- **Q1**: public semantics / IR / validation;
- **Q2**: native adapter and execution-plan contract;
- **Q3**: pinned SolidCraft accepts and persists the plan;
- **Q4**: native initial geometry/relationships;
- **Q5**: native saved-design associativity;
- **Q6**: visual evidence.

A case can only be labelled fully qualified for a claimed associative
capability when Q5 is present and passes.
