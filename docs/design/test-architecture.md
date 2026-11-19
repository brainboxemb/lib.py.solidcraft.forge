# Forge test architecture

Status: current after the CAD-CI cut-over.

## Forge unit tests

Location: `scpf/tests/`.

These tests cover reusable Forge behaviour such as API validation,
parameter/expression handling, primitive lowering, component identity,
placement, attachments and general geometry-feature rules.

## Example command-contract tests

Location: `examples/<example>/tests/`.

These tests cover the exact SolidCraft command document produced by one example.
They run as part of the example's `tool_verify` step.

Typical assertions include command types, expressions, ordering required by
SolidCraft and example-specific component/occurrence operations.

## Native model verification

Location: `examples/<example>/verification/`.

These checks consume the generated `solidcraft.json` and run in the immutable
SolidCraft runtime.

They are used for facts that require the real native engine, such as:

- body count and bounds;
- editable native feature history;
- saved parameter changes;
- topology-sensitive attachments;
- native patterns;
- rebuild behaviour after a mutation.

The generic wrapper is `scripts/model_verify.py`. Model-specific expectations
remain in the example's `verify_model.py`.

## Visual evidence

Renders may supplement executable native assertions when orientation or spatial
errors are easier to understand visually.

## External comparison libraries

PythonSCAD, pyBOSL2, CadQuery and build123d may be used to express comparable
modelling intent. Their local notes are in
`docs/agent/reference-libraries.md`.

These references do not define Forge behaviour and do not prove SolidCraft
saved-history behaviour.

## CAD-CI ownership

`tool.cad.ci` provides the generic item planner/executor.

Forge-specific verification behaviour is defined by local `ci.yml` files,
example tests, example verification code and the `solidcraft_runtime`.

The old central qualification runner is no longer part of the active test
architecture.
