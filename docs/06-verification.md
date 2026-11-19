# Verification

Forge currently uses three concrete verification layers.

## Forge package tests

From the repository root:

```powershell
python -m pip install -e ./scpf
python -m unittest discover -s scpf/tests -v
```

In CAD-CI these are `tool_build` and `tool_test` from `scpf/ci.yml`.

This layer covers reusable Forge API and compiler behaviour.

## Example command verification

Check one example without starting SolidCraft:

```powershell
python -m scpf check examples/simple-box/scpf/model.py
```

Compile the model when reviewing generated commands:

```powershell
python -m scpf examples/simple-box/scpf/model.py --out output/simple-box.json
```

The example's `tool_verify` step executes the Forge model and its
example-owned command-contract tests. Its generated command document is
`solidcraft.json` in the CAD-CI item output.

Example-specific command assertions live under
`examples/<example>/tests/`.

## Native model verification

Migrated examples also contain a `model_verify` step after `tool_verify`.

`scripts/model_verify.py` receives the exact Forge package produced by the
`forge-tool` dependency, pulls the immutable SolidCraft runtime image and
runs the example's `verification/verify_model.py`.

The runtime is defined by:

```text
docker/solidcraft_runtime/Dockerfile
docker/solidcraft_runtime/runtime.json
```

Native expectations remain under
`examples/<example>/verification/`.

At the current migration point, `simple-box` has `model_verify`. Issue #395
tracks the next ten examples.

## Layer meaning

| Layer | Proves |
| --- | --- |
| `tool_test` | reusable Forge Python/API/compiler rules |
| `tool_verify` | one example executes and produces the expected command contract |
| `model_verify` | that command document produces the expected SolidCraft model |

The removed repository-wide qualification runner and numbered qualification
levels are historical terminology, not current step names.
