# Forge test architecture

Status: current after the CAD-CI cut-over.

## Forge unit tests

Location: `scpf/tests/`.

These tests cover reusable Forge behaviour such as API validation,
parameter/expression handling, primitive lowering, component identity,
placement, attachments and general geometry-feature rules.

They run in the Forge `tool_test` release step.

## Forge release examples

`tool_verify` belongs to the Forge tool item, not to every model item.

The fixed release set is:

- `simple-box`
- `anchored-holes`
- `components`
- `corner-anchor`
- `custom-anchor`

Supported release examples run their command-contract tests from
`examples/<example>/tests/` and compile with the built Forge wheel.
`custom-anchor` is an intentional negative contract that must be rejected
with the expected model error.

This small set verifies the packaged Forge tool without turning the complete
historical model catalog into a tool-release test suite.

## Native model verification

Location: `examples/<model>/verification/`.

A migrated model item runs only `model_verify`. The shared wrapper
`scripts/model_verify.py` obtains the exact built Forge wheel, compiles the
model to `solidcraft.json`, and runs the model-owned verifier in the immutable
SolidCraft runtime.

Native checks are used for facts that require the real engine, such as:

- body count and bounds;
- editable native feature history;
- saved parameter changes;
- topology-sensitive attachments;
- native patterns;
- rebuild behaviour after a mutation.

Model-specific expectations remain in `verification/verify_model.py`.

## Shared example mechanics

`scripts/forge_example.py` contains only mechanics shared by release examples
and model verification: locating the built wheel, running contract tests,
compiling one example, and writing the command document.

It does not decide CI scope or verification policy.

## External comparison libraries

PythonSCAD, pyBOSL2, CadQuery and build123d may express comparable modelling
intent. They do not define Forge behaviour and do not prove SolidCraft saved
history.

## CAD-CI ownership

`tool.cad.ci` provides the generic item planner/executor.

Forge owns its tool-release checks, model verification code and immutable
SolidCraft runtime. The old central qualification runner is not part of the
active architecture.


## Independent reference verification

`verification/references/ci.yml` is a separate reusable CAD-CI item. Its
`verify_references` step executes the existing PythonSCAD, pyBOSL2, CadQuery
and build123d sources. The first migration proof selects `simple-box`; the next
#378 step expands the same item to every current model item. Exported geometry
is checked against `verification/geometry_contracts.py`.

This layer is independent evidence. It does not import Forge geometry
implementation to calculate expected bounds or detailed surface probes.
