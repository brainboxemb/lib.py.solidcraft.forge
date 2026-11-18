# Forge qualification

Qualification proves the public Forge API and its lowering against native
SolidCraft. It is deliberately split into a fast edit-check loop and the full
release/version gate.

The qualified SolidCraft version comes from
`scpf.version.TESTED_SOLIDCRAFT_VERSION`. Do not copy a version literal into
qualification prose or scripts.

## Test layers and qualification result fields

The repository has three test layers:

1. `scpf/tests/` contains **library unit tests** for Forge API, validation and
   compiler behaviour.
2. `examples/<case>/tests/` contains **integration tests** for concrete
   examples and their generated SolidCraft command contracts.
3. Qualification adds the native SolidCraft, saved-design, semantic and visual
   proof required for a qualification item.

The current qualification result schema still uses historical Q1/Q2 field names
for focused evidence from the first two layers. They are compatibility labels in
the existing runner, not separate architectural layers. New tool.cad.ci work
must use the names library tests, integration tests and qualification.

| Existing result field | Current meaning |
| --- | --- |
| Q1 | Focused library-unit-test evidence |
| Q2 | Focused integration command-contract evidence |
| Q3 | Native SolidCraft build and saved editable design |
| Q4 | Native semantic/measurement validation |
| Q5 | Saved-design parametric mutation where required |
| Q6 | Fixed-camera visual regression |

Qualification uses explicit test ownership:

1. `scpf/tests/` checks Forge objects, public API and compiler behaviour.
2. `examples/<case>/tests/` checks the emitted SolidCraft commands for that
   example.
3. `qualification/tests/` checks the qualification tooling itself, including
   discovery, selection, reporting and publication rules.
4. `qualification/native_validation.py` is the single Q4/Q5 source for native
   geometry, saved-design mutation and native-history expectations.

`qualification/testsuite.py` discovers the central tooling tests and each
example-local test directory. CI calls that runner instead of duplicating test
directory knowledge in workflow YAML.

Do not copy native measurement expectations back into skipped unittest classes.
The workflow/runner orchestrates these layers; it is not a separate test
framework.

### Focused library and integration evidence (legacy Q1/Q2 fields)

A qualification case reports Q1 or Q2 PASS only when its explicit test targets
in `qualification/case_evidence.py` pass. Q1 targets point to focused API or
compiler tests under `scpf/tests/`; Q2 targets point to focused command-
contract tests under `examples/<case>/tests/`.

`qualification/run_case_evidence.py` executes those targets separately per
case and writes a per-case log plus `q1-case-evidence.tsv` or
`q2-case-evidence.tsv`. The complete Q1/Q2 unittest suites still run as
regression gates, but their global success does not assign PASS to individual
cases. Compiling JSON with a non-zero command count remains a useful fixture
check but is not Q2 evidence by itself.

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

### Q6 expected shape and render regression

Q6 has two separate evidence requirements. First, each case declares
`required_views` in its geometry contract. The goal/overlay renderer must
produce the independently declared expected shape in every required view.
Cases with internal cuts can also declare 3D `visual_features` such as
`through_hole` and `through_slot`; these include profile dimensions and
the Z range so a normal view and an orthogonal/isometric view can show both
placement and depth.

Second, the existing front/right/isometric renders are compared with approved
native render baselines. Baseline agreement alone is not Q6 proof. Q6 is PASS
only when both `expected_shape.status` and `regression.status` are PASS.
The native renderer creates the union of regression views and each case's
required expected-shape views, so internal-feature cases can add a top view
without weakening the existing regression history.

### Q5 applicability rule

Q5 is required when the behaviour claimed by a case depends on a value stored
in the saved native design that must recompute after `parameters.change`.
Examples are parameter expressions, attachment values, topology-following
relationships and native feature parameters such as rectangular-pattern count
or spacing.

Q5 is not automatically required merely because a model has parameters. A case
may stay Q4/Q6-only when its qualification claim is fixed baseline geometry and
saved-design recomputation is already outside that case's responsibility.

Every qualification case must explain its Q5 decision in its `mutation`
field. Cases marked `q5_required=True` must have a registered mutation in
`qualification/native_cases.py`; the runtime metadata check fails otherwise.
The published proof contract and structured results expose the decision and its
reason for both required and not-required cases.

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

The affected runner always runs focused library and integration evidence first (currently stored in the legacy Q1/Q2 result fields), then runs Q3-Q6 only for the selected native cases. Q5 is executed only for cases marked `q5_required`.

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
