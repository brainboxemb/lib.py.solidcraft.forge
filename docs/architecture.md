# Forge architecture

Forge is the canonical implementation of the public `scpf` Python authoring
API for SolidCraft. It is an authoring/compiler layer, not a second CAD kernel.

## Ownership

- `cadlib/` owns the public `scpf` package and Forge-specific release
  metadata validation.
- `models/<id>/` is the physical CAD owner boundary. Multiple real engine
  implementations of the same physical owner stay inside that owner.
- `api-probes/<id>/` contains temporary executable API/design probes. Probes
  are not physical model owners and are not model-catalogue content.
- `modules/` owns generic repository capabilities such as CI, builders,
  verification and Pages projection. Generic builders do not import `scpf` or
  learn Forge-specific authoring semantics.
- `site/` owns public documentation/presentation sources.
- `build/<scope>/` owns generated CAD/evidence output.
- `gh-pages` owns rendered Pages output and never owns CAD source/evidence.

Do not duplicate a capability across these boundaries merely to make one
consumer convenient.

## Authoring and lowering

The public API expresses CAD intent with Python objects, parameters,
relationships and typed operations. Callers must not depend on SolidCraft
browser ids, command ids, replay variables or transport details.

Forge lowers supported intent to SolidCraft-native operations. When SolidCraft
can preserve an editable associative relationship, Forge should preserve that
relationship rather than baking coordinates or geometry for compiler
convenience.

Unsupported intent fails explicitly. Do not silently substitute Python variants,
numeric flags, duplicated bodies or approximate geometry when that changes the
public semantics.

The experimental `exp` line may advance a more generic engine-neutral IR and
independent backend lowerings. That work remains isolated until intentionally
integrated into `dev`; normal `dev` design documents must not pretend an
experimental IR capability is already released.

### IR completion and backend completion

IR completion and backend completion are separate dimensions.

An **IR-ready** semantic slice has a backend-neutral CAD contract, normalizes
public SCPF source into typed IR instead of `LegacyShapeIR`, has pure IR
boundary tests, preserves symbolic/history/topology dependencies, and retains
stable SolidCraft behavior through typed lowering. A backend that does not yet
support that typed node must fail closed.

A backend is tracked independently as unsupported, lowered, contract-tested or
native-qualified. Mitcad coverage may therefore lag the IR layer and catch up
in backend-focused batches. Native Mitcad qualification is not a prerequisite
for declaring a semantic slice IR-ready.

This separation is deliberate: backend transport must not pace or shape the
semantic compiler contract. The canonical migration inventory is
[ir-coverage.md](ir-coverage.md), which reports IR status separately from
SolidCraft and Mitcad status.

## Configuration and API design

Current cross-object API semantics live in `api.md`. New or changing public
API contracts are designed under `design/api/` and should be accompanied by
executable API probes when backend behavior must be observed.

A reusable component owns geometry and parameters. Application-level
configuration presentation belongs to the final model/document or higher-level
assembly unless the public API explicitly defines otherwise.

## Build and verification

Central CI schedules owners and runtime roles; builders execute one explicit
implementation source and verification checks already-built artifacts.

Forge uses the runtime roles declared in root `ci.yml`. At the current dev
baseline these are:

- `reference`: `ghcr.io/brainboxemb/cad-reference:v0.3.6`;
- `solidcraft`: `ghcr.io/brainboxemb/cad-solidcraft:v0.3.6`, SolidCraft
  `0.49.0`.

Treat `ci.yml` and `cadlib/src/scpf/version.py` as the machine-readable
sources when these pins change.

Pages only projects source metadata and retained build evidence. It does not
execute CAD and must not copy generated CAD artifacts into the site branch.

## Branches and governance

- `main` is stable integration and the release source.
- `dev` is normal product integration.
- `exp` is optional experimental integration and never a direct release
  source.
- short-lived issue/fix/feature/docs/chore branches integrate through the merge
  policy.
- canonical unfinished-work governance is `main:docs/plan.md`.

Exact merge/release execution rules are intentionally kept in `AGENTS.md` and
`release.md`, not duplicated here.
