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

Qualification cases are ordinary `unittest.TestCase` regressions plus native
evidence. The workflow/runner orchestrates them; it is not a separate test
framework.

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
exported STL/render evidence. PythonSCAD, pyBOSL2 and CadQuery are required by
default. A case may omit one only through a documented technical
`reference_exceptions` entry.

To run those comparison references locally after installing the pinned
comparison libraries:

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

Every case has a Forge model plus three independent comparison models:

```text
examples/<case>/scpf/model.py
examples/<case>/pythonscad/model.py
examples/<case>/pybosl2/model.py
examples/<case>/cadquery/model.py
```

The required set is defined once in `qualification/cases.py`. Missing
references fail qualification. `reference_exceptions` is reserved for a real
technical mismatch and must contain a human-readable reason; it is not a
migration or convenience mechanism.

Reference implementations are comparison models, not Forge specifications.
Start with `docs/agent/reference-libraries.md`; only consult upstream when
that local cache does not cover the needed operation.
