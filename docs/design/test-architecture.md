# Forge test rules

Status: updated after the 2026-11 code audit

Use the same words as the code. A test should make clear:

- which Forge object or function it checks;
- which SolidCraft command should be generated;
- whether it checks generated JSON or a real SolidCraft model;
- whether a saved parameter change is expected to keep working.

## 1. Forge object tests

Check Forge before SolidCraft commands are generated.

Examples:

- a component keeps its `Placement`;
- `.copy()` creates a separate occurrence;
- copies may reuse the same component definition;
- the same occurrence object cannot be inserted twice;
- grouping does not break an attachment;
- a bad attachment target is rejected;
- parameter conflicts are reported.

Do not depend on SolidCraft names such as `Panel:1` or `Panel:2`.

## 2. Generated SolidCraft command tests

Keep these tests beside the model under `examples/<case>/tests/`. Do not put
model-specific command contracts in one central qualification test directory.

Check the JSON Forge generates.

These tests may check:

- `component.create`;
- `occurrence.copy`;
- `occurrence.move`;
- `joint.create`;
- `joint.origin`;
- parameter expressions;
- command order when SolidCraft 0.42 requires it.

For ordinary positioning, check that `Placement` is put directly into
`component.create` or `occurrence.copy` when SolidCraft supports it.

Do not accept guessed SolidCraft occurrence names as the way Forge finds an
occurrence.

If Forge cannot safely generate a replayable command for a case, expect a clear
error.

## 3. Live and replay tests

`scpf/tests/test_live.py` checks the existing live connection and replay of a
static command document.

Keep tests for:

- one strict `engine.batch`;
- rollback on failure;
- replay of the same static document;
- connection and authentication errors.

Runtime result binding is not part of the normal Forge route.

## 4. Native SolidCraft tests

These tests run the generated commands in SolidCraft 0.42.

### Initial model check

Check:

- bodies and bounds;
- occurrence transforms;
- joints when the case uses a real joint;
- group hierarchy when grouping is the feature being tested.

### Saved parameter change

Use this when Forge claims that a relationship stays linked after changing a
parameter.

Change the parameter in the saved SolidCraft design without rerunning Python.

This is required for things such as:

- parameter-driven component size;
- parameter-driven Placement;
- attachment gap or offset;
- topology-backed anchors;
- feature placement that claims to remain associative.

An initial correct render is not enough to prove this.

## 5. Visual checks

Use screenshots/renders for mistakes that are hard to catch from numbers alone,
such as wrong orientation or a bracket on the wrong side.

Visual checks support the other tests; they do not replace them.

## 6. PythonSCAD, pyBOSL2 and CadQuery references

These show the same modelling intent in another library.

They compare the visible model and the way the model is expressed. They do not
prove SolidCraft joints, saved parameters or SolidCraft occurrence handling.

## 7. Existing test cleanup

### `scpf/tests/test_assembly.py`

Keep tests for Forge behaviour, but remove assertions that make
`Component:N` numbering part of the Forge contract.

Move exact SolidCraft-command checks into focused command tests where useful.

### `scpf/tests/test_live.py`

Keep transport, batch rollback and replay tests here.

### `qualification/tests/*NativeTests`

These classes are currently skipped in CI while
`qualification/native_validation.py` does the real native checks.

Move any unique useful check into the central validator, then remove the
duplicate skipped test.

## 8. Qualification tooling tests

Keep discovery, selection, reporting and publication-rule tests under
`qualification/tests/`. The qualification test runner itself must have unit
tests there. CI should call the runner rather than reimplement test discovery.

## 9. Review rule

Reject a new test when it:

- depends on a generated SolidCraft browser name;
- treats one correct initial render as proof that a saved parameter relationship
  works;
- duplicates an existing native check;
- keeps an old SolidCraft workaround without naming the version/case that needs
  it;
- checks command order that neither Forge nor SolidCraft requires.
