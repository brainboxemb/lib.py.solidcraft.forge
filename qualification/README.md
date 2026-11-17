# Forge qualification

Qualification proves the public Forge API and its lowering against native
SolidCraft. It is deliberately split into a fast edit-check loop and the full
release/version gate.

The qualified SolidCraft version comes from
`scpf.version.TESTED_SOLIDCRAFT_VERSION`. Do not copy a version literal into
qualification prose or scripts.

## Levels

| Level | Purpose |
| --- | --- |
| Q1 | Python API and symbolic/compiler invariants |
| Q2 | Generated SolidCraft command contract |
| Q3 | Native SolidCraft build and saved editable design |
| Q4 | Native semantic/measurement validation |
| Q5 | Saved-design parametric mutation where required |
| Q6 | Fixed-camera visual regression |

Qualification uses three explicit test layers:

1. `scpf/tests/` checks Forge objects, public API and compiler behaviour.
2. `qualification/tests/` checks emitted SolidCraft commands and qualification
   tooling.
3. `qualification/native_validation.py` is the single Q4/Q5 source for native
   geometry, saved-design mutation and native-history expectations.

Do not copy native measurement expectations back into skipped unittest classes.
The workflow/runner orchestrates these layers; it is not a separate test
framework.

## Shared proof contract

Every case has one machine-readable proof contract in
`qualification/geometry_contracts.py`. Its `geometry` section is independent
of SolidCraft and supplies baseline body bounds, Q6 visual boxes and any
stronger measurements needed when bounds do not prove the shape. Its
`solidcraft_only` section records native history/relationship expectations and
whether saved-design mutation is required.

Q4 baseline bounds, external reference validation and Q6 goal rendering all
read the same geometry contract. A case must state whether bounds are sufficient
for the geometry it is responsible for and explain why. If bounds are not
sufficient, the contract must declare volume and/or 3D surface-distance checks.

## Fast affected-case loop

Use this while changing one case or one API area:

```text
python qualification/run_affected.py --cases four-corner-l
```

Several cases can be supplied with commas or spaces:

```text
python qualification/run_affected.py --cases "components,parametric-attach"
```

For a generic subsystem change, select the relevant qualification group:

```text
python qualification/run_affected.py --cases group:anchors
```

Available groups come from `qualification/cases.py`. Use `--cases all` only
when you deliberately want every native case locally.

The affected runner always runs Q1 and Q2 first, then runs Q3-Q6 only for the
selected native cases. Q5 is executed only for cases marked `q5_required`.

It writes:

```text
output/affected/qualification/affected-timings.json
output/affected/qualification/affected-timings.tsv
output/affected/native/<case>/...
```

Timings record SolidCraft startup plus per-case compile, native build, eval,
snapshots and mutation. Use these measurements before considering a persistent
SolidCraft process; do not add daemon/process-reuse complexity without evidence
that startup is the bottleneck.

The same runner is available in GitHub Actions through
`SCPF affected-case qualification` (manual workflow dispatch). That workflow
also executes the configured comparison references and stores their independently
exported STL/render evidence. PythonSCAD, pyBOSL2, CadQuery and build123d are required by
default. A case may omit one only through a documented technical
`reference_exceptions` entry.

To run those comparison references locally, install the pinned comparison libraries. Keep build123d in a separate virtual environment from pyBOSL2 because their pinned webcolors requirements conflict, and set `BUILD123D_PYTHON` to that environment's Python:

```text
python qualification/reference_validation.py \
  --cases four-corner-l \
  --out output/references \
  --source-sha local
```

## Full gate

A SolidCraft version upgrade, Forge release or final promotion must run the
normal `SCPF Python package qualification` workflow. That workflow runs every
registered case through Q1-Q6 and enforces that every required result is PASS.

Affected-case success is iteration evidence, not a replacement for the full
gate.

## Reference models

Every case has a Forge model plus four independent comparison models:

```text
examples/<case>/scpf/model.py
examples/<case>/pythonscad/model.py
examples/<case>/pybosl2/model.py
examples/<case>/cadquery/model.py
examples/<case>/build123d/model.py
```

The required set is defined once in `qualification/cases.py`. Missing
references fail qualification. `reference_exceptions` is reserved for a real
technical mismatch and must contain a human-readable reason; it is not a
migration or convenience mechanism.

Reference implementations are comparison models, not Forge specifications.
They are measured against independent case expectations. Bounds remain one
check, but cases with internal holes/slots also require volume, watertightness
and declared 3D surface-distance probes; the generated case page publishes the
actual measurements used for PASS/FAIL.

Start with `docs/agent/reference-libraries.md`; only consult upstream when
that local cache does not cover the needed operation.
