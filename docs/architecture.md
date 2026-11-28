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

Forge v0.27.0 evaluates the public SCPF frontend into typed engine-neutral
semantic IR before backend lowering. SolidCraft and Mitcad consume that same
semantic contract independently; unsupported backend paths fail closed rather
than interpreting frontend objects or private Shape payloads.

Semantic IR has explicit physical ownership below `cadlib/src/scpf/ir/`:

- `base.py`: parameters, primitive geometry and placement nodes;
- `sketch.py`: profiles, sketch relations/entities and regions;
- `operations.py`: extrude/revolve, topology selectors and modifiers;
- `features.py`: holes, plastic features and feature patterns;
- `sheet_metal.py`: sheet rules and sheet history nodes;
- `body.py`: generic body-history composition and legacy boundary;
- `configuration.py`: semantic feature identity, configurations and model IR;
- `normalizers/`: matching frontend-to-IR normalization domains;
- `normalize.py`: top-level model/shape dispatch only;
- `__init__.py`: stable `scpf.ir` compatibility exports.

These modules are ownership boundaries, not additional public APIs. External
callers and backends continue to import the stable `scpf.ir` façade. Do not
recreate a second frontend or duplicate semantic definitions in backend code.

The semantic test suite mirrors these domains under `cadlib/tests/ir/`.
Backend-specific qualification remains in its backend test modules.

## Configuration and API design

Current cross-object API semantics live in `api.md`. New or changing public
API contracts are designed under `design/api/` and should be accompanied by
executable API probes when backend behavior must be observed.

A reusable component owns geometry and parameters. Application-level
configuration presentation belongs to the final model/document or higher-level
assembly unless the public API explicitly defines otherwise.

The current v0.27 configuration API attaches one ordered table to the final
Shape, ModelInstance or Assembly through `.configure(...)`. Semantic IR keeps
that table as `ConfigurationIR`; retired wrapper/rule authoring is not a
second frontend contract. Scoped `feature(name, suppressed=...)` authoring
adds stable semantic identity/state to one existing history operation and is
represented separately as `NamedFeatureIR(name, FeatureRefIR, suppressed)`
rather than as backend-native browser identity or as a new geometry node.

Normal and experimental lanes must periodically reconcile the current public
frontend before experimental integration. A completed IR inventory is only
meaningful against the current released/public API; backend coverage may lag
and must fail closed rather than preserve an obsolete frontend privately.

## Build and verification

Central CI schedules owners and runtime roles; builders execute one explicit
implementation source and verification checks already-built artifacts.

Forge uses the runtime roles declared in root `ci.yml`. At the current dev
baseline these are:

- `reference`: `ghcr.io/brainboxemb/cad-reference:v0.3.8`;
- `solidcraft`: `ghcr.io/brainboxemb/cad-solidcraft:v0.3.8`, SolidCraft
  `0.50.0`.

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
