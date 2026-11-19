# Forge repository plan

Status: current repository plan.

This is the single current implementation plan for the Forge repository.
The active work is the CAD-CI migration described below. Historical issues,
pull requests and old qualification documents remain useful history, but they
do not replace this plan.

## Current work: CAD-CI migration

### Responsibilities

The generic CI implementation lives outside Forge:

- `tool.cad.ci` owns planning, SCons execution, dependency traversal, caching
  and reusable build state.
- `lib.py.cad.verfication` owns reusable CAD/model verification helpers.
- Forge owns only Forge-specific build, release verification and model
  verification commands.

Forge must not add a second runner, scheduler, cache engine or generic result
layer.

### Forge release verification

Forge itself has one release-verification chain:

```text
tool_build -> tool_test -> tool_verify
```

### tool_build

Build the distributable SCPF/Forge Python package.

### tool_test

Run the reusable Forge unit-test suite from `scpf/tests/`.

### tool_verify

Verify the **built Forge package** with the fixed representative example set.

The representative Forge examples are:

1. `simple-box`
2. `anchored-holes`
3. `components`
4. `corner-anchor`
5. `custom-anchor`

These are release verification for Forge. They prove that the built tool can
execute representative Python models and emit the expected SolidCraft command
structure.

`tool_verify` is **not** a per-model verification stage. The historical model
catalog must not be added to `tool_verify` merely because those models once had
integration tests.

The five-example set is explicit. Do not infer or expand it from the model
catalog.

### Model verification

`model_verify` verifies one CAD model in SolidCraft.

The source set for this migration is the historical qualification catalog from
Forge commit:

`be40b09e7454a90e87d83768a9e7453c52ba5d76`

That catalog contains 32 model-verification cases.

For each migrated model, `model_verify` owns the checks required by that
model's historical contract, including where applicable:

- native SolidCraft model creation;
- geometry and feature-history checks;
- saved-design parameter or relationship mutation;
- model-specific post-build inspections;
- other current executable evidence required for that model.

A model does not need `tool_verify` in order to be a model-verification item.
If one of the five Forge release examples is also present in the historical
model catalog, the same source model may participate in both responsibilities,
but the two verification responsibilities remain independent.

### Model metadata

Migrated models use a local `model.yml` with exactly these generic English
fields:

- `section`
- `title`
- `tagline`
- `description`
- `parameters`
- `stages`

Technical expectations, geometry assertions, mutations and SolidCraft commands
do not belong in `model.yml`.

### Migration order

The migration is completed in small reviewable PRs:

1. Forge tool build and unit-test path.
2. Forge `tool_verify` with the five representative release examples.
3. One complete model-verification path: `simple-box`.
4. The next ten historical qualification models (#395):
   - `anchored-holes`
   - `hole-family`
   - `sheet-fold`
   - `top-sketch-after-chamfer`
   - `parameter-scope`
   - `parent-derived-child-size`
   - `components`
   - `repeated-parent-attachments`
   - `assembly-decorator`
   - `group-hierarchy`
5. The remaining historical qualification models.
6. Durable build output and Pages publication (#366).
7. Final repository audit and full CI verification.

Each logical migration step uses its own branch and pull request.

### Historical integration tests

The pre-cut-over repository had example-owned integration tests under
`examples/<case>/tests/`.

Those tests remain useful evidence for Forge command behaviour, but the old
label `integration` does not decide the new CI ownership automatically.

- reusable Forge behaviour belongs in `tool_test`;
- the fixed representative release examples belong in `tool_verify`;
- per-model SolidCraft behaviour belongs in `model_verify`.

Do not recreate the old qualification runner or its gate terminology.

### Runtime and execution boundaries

- SolidCraft model verification uses the immutable `solidcraft_runtime`.
- The runtime contains SolidCraft and the pinned reusable verification library,
  but no model-specific contracts.
- Model expectations remain local to the Forge repository/model.
- Runtime preparation is driven from the CAD-CI plan, not hardcoded to one
  model name.
- A second unchanged CI run must leave reusable targets CURRENT.
- Unrelated model targets must remain CURRENT when one model changes.

### Publication boundary

Build-output storage and GitHub Pages publication are a later migration step
tracked by #366.

Publication must consume already produced build/verification evidence. It must
not rerun Forge or model verification merely to build the website.
