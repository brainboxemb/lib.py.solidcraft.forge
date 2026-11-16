# Forge functional API qualification

Forge is documented and qualified from **use scenarios**, not from internal
implementation details. The normative public API definition is
[`docs/05-cad-api-design.md`](../05-cad-api-design.md).

Each case document is a functional proof of one API behaviour. The executable
fixture and native SolidCraft checks prove that Forge implements the normative
contract; they do not define that contract.

## Case structure

Every non-trivial case uses the same order:

1. **Use scenario** — what the model author is trying to achieve.
2. **Expected behaviour** — observable behaviour of the Forge API.
3. **Forge API** — the public Python expression used to describe it.
4. **Reference implementations** — PythonSCAD, pyBOSL2 and CadQuery versions
   of the same modelling intent.
5. **Forge model** — the semantic objects/relations Forge should represent.
6. **SolidCraft mapping** — how Forge lowers the intent to native commands.
7. **Acceptance criteria** — what must be true in the native model.
8. **Parametric change** — where relevant, what must happen after editing a
   saved SolidCraft parameter without rerunning Python.
9. **Verification evidence** — command JSON, native measurements and snapshots.

## Required reference layout

Every qualification case has these files:

```text
examples/<case>/
├── scpf/
│   └── model.py
├── pythonscad/
│   └── model.py
├── pybosl2/
│   └── model.py
└── cadquery/
    └── model.py
```

The three reference models must describe the same user-visible modelling
intent as the Forge fixture. They are comparison material, not executable proof
of SolidCraft behaviour and not alternative API specifications.

If PythonSCAD, pyBOSL2 or CadQuery cannot express an associative relationship
comparable to SolidCraft, the reference remains useful: build the equivalent
geometry and state the missing relationship semantics in a short source
comment. Do not fake associativity with unexplained copied coordinates.

A new qualification case without all three reference files is incomplete unless
the case has a documented technical `reference_exceptions` entry.

## Test implementation

Qualification uses three layers:

- `scpf/tests/` — Forge object/API/compiler behaviour;
- `qualification/tests/` — generated SolidCraft command contracts and
  qualification tooling;
- `qualification/native_validation.py` — Q4/Q5 native SolidCraft
  measurements, saved-design mutation and native-history checks.

`qualification/tests/` uses Python's standard `unittest` framework. Native
measurement expectations are not duplicated there and are not conditionally
skipped based on `SCPF_NATIVE_ROOT`.

Functional command/tooling assertions belong in `qualification/tests/`, not
in shell/JQ when they can reasonably be expressed in Python.

## Fast iteration versus full qualification

The edit-check loop has two modes.

**Fast / affected cases**

- run Q1;
- run Q2;
- compile only changed/selected cases;
- run native Q3-Q6 only for selected affected cases when native evidence is
  required;
- record timing per compile/build/eval/snapshot/mutation step.

**Full qualification**

- run every case;
- required for a SolidCraft version promotion;
- required for final qualification on the promoted `main` commit;
- produces the complete review artifact and Pages result set.

Tool startup must be measured before introducing a persistent process. A
long-lived SolidCraft session is an optimization only if it preserves
independent-case isolation and measurably reduces runtime.

## Published results

Native evidence is first written under `output/native/<case>/`. After a
source-matched qualification run, `site/build.py` publishes that evidence to
GitHub Pages.

Two views are available:

- `/qualification/results/` — compact overview of every case, status,
  SolidCraft version, body count, parameter count and evidence count;
- `/qualification/<case>/` — intent, Forge source, reference models,
  measurements, mutation evidence, snapshots and raw evidence links.

The CI artifact remains the complete archive; Pages is the review surface.

## Qualification levels

- Q1 — Python API contract
- Q2 — generated SolidCraft command contract
- Q3 — native SolidCraft build
- Q4 — native measurement
- Q5 — saved-design parametric mutation
- Q6 — native visual artifact

## SolidCraft upgrades

SolidCraft engine upgrades follow the documented
[SolidCraft upgrade protocol](solidcraft-upgrade-protocol.md). The protocol
keeps the candidate version on a qualification branch, uses one version source
in Forge, and requires native Forge and CAD evidence before promotion to
`main`.
