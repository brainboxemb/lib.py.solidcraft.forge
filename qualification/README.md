# Forge qualification

Qualification proves the public Forge API and its lowering against native
SolidCraft. The qualified SolidCraft version comes from
`scpf.version.TESTED_SOLIDCRAFT_VERSION`.

## Ownership

The repository has three test layers:

1. `scpf/tests/` contains **library unit tests** for Forge API, validation and
   compiler behaviour.
2. `examples/<case>/tests/` contains **integration tests** for one concrete
   example and its generated SolidCraft command contract.
3. Native **qualification** proves the saved SolidCraft model, geometry,
   saved-design behaviour where applicable, and visual result.

Each supported `examples/<case>` folder is one `tool.cad.ci` item. The
generic CI tool does not understand any of the meanings above. Forge supplies
the commands and interprets their output.

## Example item

An example item has two ordered steps:

- `integration`: run the example-owned tests and compile the replayable
  SolidCraft command document;
- `native`: resume that same item at native replay in the immutable
  qualification image, then evaluate, inspect, render, mutate when required,
  validate, and gate the result.

The item keeps all output below its own mirrored build path. The final native
step writes:

`case/native/<slug>/qualification-result.json`

The result schema uses semantic checks:

- `integration`
- `native_model`
- `geometry`
- `saved_design`
- `visual`

There are no numbered qualification levels in the current result contract.

## Saved-design checks

A saved-design check is required only when the case claims that a relationship
must recompute after editing the saved native design. Examples include parameter
expressions, attachment values, topology-following relationships and native
feature parameters.

The case registry records this as `saved_design_required`. A required case
must have one reusable mutation in `qualification/native_cases.py`.
The native validator reports `saved_design: pass|fail`; a case that does not
need mutation reports `not-required`.

## Shared geometry proof

`qualification/geometry_contracts.py` owns the machine-readable geometry
target. Native validation, independent references and expected-shape rendering
consume the same target.

Bounds alone are used only when they prove the intended shape. Cases with
internal or ambiguous geometry add volume, surface-distance or other declared
checks. Visual regression is additional evidence, not a replacement for
geometric checks.

## Selection and gates

`qualification/impact.py` maps changed paths to affected example cases.
`scripts/forge_scope.py` chooses one semantic gate:

- `preflight`: no technical CAD item needs to run;
- `affected-integration`: selected examples run through integration only;
- `affected-native`: selected examples run through native qualification;
- `full-native`: all supported examples plus required shared evidence items.

Unknown technical inputs fail safe to `full-native`.

Library and integration checks are the normal edit loop. Native qualification is
run only when the change can affect native SolidCraft behaviour or when a full
safety/release gate is required.

## References

Every qualification case may have independent PythonSCAD, pyBOSL2, CadQuery and
build123d comparison implementations. These are comparison models, not Forge
specifications. The independent reference-suite is its own generic CI item and
runs only when Forge policy requires it.

A reference exception is allowed only for a documented technical mismatch.
Missing required reference evidence fails qualification.

## Build and Pages

Technical item output is durable build data. Website rendering is Forge-owned
presentation. `tool.cad.ci` owns the generic build-store and generated-branch
publication mechanisms; it does not interpret qualification results.

Presentation-only changes may reuse the latest passing technical baseline.
Provenance must preserve the source commit and evidence commit separately.
