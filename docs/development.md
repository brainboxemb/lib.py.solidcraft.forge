# Forge development

This is the primary guide for working on the Forge repository itself. It
describes repository development; user-facing modelling semantics belong in
[api.md](api.md).

## Local setup

Install the editable package from the repository root:

```powershell
python -m pip install -e ./scpf
```

Run the Forge unit suite:

```powershell
python -m unittest discover -s scpf/tests -v
```

Windows-specific setup detail lives in
[manual/windows-setup.md](manual/windows-setup.md).

## Repository layout

```text
scpf/scpf/          public Forge API and compiler implementation
scpf/tests/         reusable API/compiler unit tests
examples/           Forge fixtures and model-verification cases
scripts/            Forge-owned CI/verification launchers
site/               generated human/API documentation source
docs/               primary repository documents
docs/manual/        current task-oriented guidance
docs/background/    historical/narrow design and research records
docs/agent/         generated/machine-oriented API material
```

Product CAD models live in `2026-011-02.cad.solidcraft`, not in this library.

## Primary documentation contract

Keep the `docs/` root deliberately small:

- [api.md](api.md) — cross-object public API semantics;
- [design.md](design.md) — repository-wide architecture and responsibility
  boundaries;
- [development.md](development.md) — working on Forge itself;
- [plan.md](plan.md) — current unfinished work and issue ordering;
- [requirements.md](requirements.md) — stable repository requirements;
- [release.md](release.md) — package/release rules.

Current task-oriented detail goes under `docs/manual/`. Current version-pinned
external engineering references go under `docs/reference/`. Historical design
records, numbered changes, audits, migration notes and superseded research go
under `docs/background/`.

Do not create a second handwritten agent API manual. The generated
`docs/agent/forge-api.json` is derived from the public implementation and
docstrings.

## API documentation sources

Exact exported names, signatures, defaults and enum members come from the
Python implementation and public docstrings.

`docs/api.md` owns cross-object semantics that cannot sensibly live on one
Python object.

The site generator reads the primary API contract and generated implementation
metadata. Public API changes therefore require implementation/docstring updates,
the cross-object contract when relevant, tests, and regeneration of agent/site
output where required.

## Updating the SolidCraft target

Forge keeps current version-pinned SolidCraft engineering references under
`docs/reference/solidcraft/<version>/`. These references are part of the
active development inputs for compiler compatibility work, not background
history.

When Forge intentionally targets a newer SolidCraft release:

1. do not modify or replace an already qualified version directory;
2. add a new sibling `docs/reference/solidcraft/<new-version>/` directory;
3. record the exact upstream release and commit in its `SOURCE.md`;
4. capture the relevant command/reference material and known contract gaps for
   that exact version before changing Forge compatibility code;
5. update `scpf/scpf/version.py::TESTED_SOLIDCRAFT_VERSION` and the matching
   Forge CI/runtime expectation only as part of the deliberate compatibility
   change;
6. qualify the new target before treating it as the current supported version.

The index and current version notes are in
[reference/solidcraft/README.md](reference/solidcraft/README.md).

## Testing ownership

- `scpf/tests/` — reusable Forge API/compiler tests;
- fixed release-verification examples — Forge package release verification;
- `examples/<model>/verification/` — model-specific native verification data;
- released `lib.py.cad.verfication` — shared CAD verification behavior.

Detailed historical/narrow test-architecture material is preserved under
`docs/background/design/`; current ownership rules live in
[design.md](design.md) and [requirements.md](requirements.md).

## CI development

Forge CI delegates generic planning/execution to released `tool.cad.ci`.
Repository-specific items are declared in `cad-ci.yml`, `scpf/ci.yml` and
model `ci.yml` files.

Do not add Forge-local implementations of generic selection, caching,
concurrency or SCons behavior when that responsibility belongs in the central
CI repositories.

Before changing CI structure, read the current issues, PRs, branches,
`AGENTS.md` and [plan.md](plan.md).

## Parallel lane execution

Forge has two independent long-lived development lanes:

- `dev-cad` for Forge API/compiler/model/Verification/site-content work;
- `dev-ci` for Forge CI/infrastructure/publication work.

Independent work in those lanes should progress in parallel. A running workflow
blocks only work whose next step depends on that result. Shared dependency
releases and true architecture boundaries remain explicit gates.

Repository-wide governance/documentation that applies equally to both lanes may
use a short-lived branch directly against `main`.

Merge policy is explicit:

- feature/fix PRs into a dev lane: squash merge;
- PRs whose base is `main`: squash merge by default;
- only a PR whose head is literally the long-lived `dev-cad` or `dev-ci`
  branch may use a normal merge into `main`;
- temporary `promote/*` heads and governance PRs to `main` are squash-merged.

## Change discipline

For active repository work:

1. ensure the change has an issue;
2. update [plan.md](plan.md) before implementation;
3. update [requirements.md](requirements.md), [design.md](design.md) or
   [api.md](api.md) when the stable contract changes;
4. implement and test one coherent change;
5. merge/release only after the relevant current checks pass;
6. update the plan after completion.

## Release preparation

See [release.md](release.md). Package version changes are deliberate release
preparation, not routine development bookkeeping.


## Example documentation sources

Each `examples/<slug>/` directory owns the material needed to explain that
example.

- `model.yml` contains only the generic page/model metadata fields
  `section`, `title`, `tagline`, `description`, `parameters` and
  `stages`;
- `README.md` contains the human engineering explanation for the example,
  including goal, Forge API/model, SolidCraft lowering/result, saved-design
  explanation, geometry sufficiency rationale and reference notes;
- `scpf/model.py` is the implementation shown/executed;
- `verification/verify.py` is the exact machine-readable verification
  contract;
- reference implementation directories are executable independent comparisons;
- accepted current PASS/FAIL and measurement evidence comes from
  `build/main`.

Do not add example descriptions to a central Python registry. During source
migrations, preserve existing README engineering statements rather than
summarizing or reinterpreting them. Do not duplicate
verification bounds/volumes/tolerances into prose merely to render a page.

Site layout belongs in external templates/static assets. Prose-heavy site
content must not be embedded as complete HTML pages in Python modules.
