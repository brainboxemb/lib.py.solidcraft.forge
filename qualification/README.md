# Forge qualification

Qualification proves the public Forge API and its lowering against the selected
SolidCraft version from `scpf.version.TESTED_SOLIDCRAFT_VERSION`.

## Ownership

Forge uses five explicit stages:

1. **`tool_build`** builds/packages the Python Forge tool.
2. **`tool_test`** runs the Forge/SCPF unit-test suite.
3. **`tool_verify`** runs an example and verifies the generated SolidCraft
   command contract.
4. **`model_verify`** executes that command contract in SolidCraft and verifies
   the resulting model.
5. **`tool_qualification`** records that the tool and every required model
   verification passed for this Forge/SolidCraft combination.

`tool.cad.ci` is generic. It does not understand these stage names; Forge owns
their meaning and commands.

## Tool item

The `scpf` CI item owns:

- `tool_build`: build one installable Forge wheel;
- `tool_test`: run the Forge unit tests.

The tool item output is reusable like any other generic CI item.

## Example item

Each supported `examples/<case>` folder owns one CI item with two ordered
steps:

- `tool_verify`: run the example-owned contract tests and compile the
  replayable SolidCraft command document;
- `model_verify`: execute the compiled document in SolidCraft, measure and
  inspect the model, run saved-design mutation when required, render expected
  views, and write the model result.

The final per-model result is:

`case/model_verify/<slug>/qualification-result.json`

Its semantic checks include:

- `tool_verify`
- `model_verify`
- `geometry`
- `saved_design`
- `visual`

## Tool qualification

`qualification/tool_qualification/ci.yml` depends on the Forge tool item and
all registered examples. Its `tool_qualification` step performs no CAD work.
It checks the completed dependency results and writes one aggregate
`tool-qualification.json`.

Therefore "qualified" means that the tool built, the unit tests passed, and all
required model verifications passed against the selected SolidCraft version.

## Saved-design checks

A saved-design check is required only when a case claims that a relationship
must recompute after editing the saved SolidCraft design. The case registry
records this as `saved_design_required`.

A required case has one reusable mutation in `qualification/native_cases.py`.
The model validator reports `saved_design: pass|fail`; a case that does not
need mutation reports `not-required`.

## Shared geometry proof

`qualification/geometry_contracts.py` owns the machine-readable geometry
target. Model validation, independent references and expected-shape rendering
consume the same target.

Bounds alone are used only when they prove the intended shape. Cases with
internal or ambiguous geometry add volume, surface-distance or other declared
checks. Visual regression is additional evidence, not a replacement for
geometric checks.

## Selection

`qualification/impact.py` maps changed paths to affected examples.
`scripts/forge_scope.py` then selects one target stage:

- `none`
- `tool_verify`
- `model_verify`
- `tool_qualification`

Unknown technical inputs fail safe to `tool_qualification`.

Reference and diagram verification are independent shared items. They are run
when their inputs change and as part of a complete qualification run.

## References

Every qualification case may have independent PythonSCAD, pyBOSL2, CadQuery and
build123d comparison implementations. These are comparison models, not Forge
specifications. The independent reference-suite is its own generic CI item.

A reference exception is allowed only for a documented technical mismatch.
Missing required reference evidence fails the relevant verification.

## Build and Pages

Technical item output is durable build data. Website rendering is Forge-owned
presentation. `tool.cad.ci` owns the generic build-store and generated-branch
publication mechanisms; it does not interpret Forge verification results.

Presentation-only changes may reuse the latest passing technical baseline.
Provenance must preserve the source commit and evidence commit separately.
