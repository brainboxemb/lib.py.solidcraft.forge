# Forge NEW requirements

## Repository

1. Preserve the public SCPF Python API and import name `scpf`.
2. Use the corrected CAD library architecture rather than reproducing historical Forge-local orchestration.
3. Keep source ownership explicit: library, physical models, generic modules, documentation and generated evidence are separate roles.
4. Use `main` as stable and `dev` as development integration.
5. Generated CAD output is owned by `build`; Pages presentation is owned by `gh-pages`. Pages must not duplicate generated CAD artifacts.

## Models

1. `models/<id>/` is the physical selection/publication owner.
2. One owner may declare multiple CAD-engine implementations.
3. Engine implementations are local to the owner and must not become sibling model owners.
4. `model.yml.purpose` may contain `example`, `verification`, or both.
5. Owner-local verification expectations apply independently to every declared implementation unless a future real model demonstrates a justified override.
6. Physical model dependencies name owner ids and downstream dependents must be selected transitively.

## CAD execution

1. Reuse only the released `reference` and `solidcraft` runtime roles from `docker.cad.solidcraft v0.3.5` until a separately qualified upgrade exists.
2. Standard reference builders are PythonSCAD, pyBOSL2, CadQuery and build123d.
3. SCPF compilation is consumer-owned and feeds the generic SolidCraft command builder; do not teach generic builders Forge semantics.
4. SolidCraft executes in its lightweight runtime; generic mesh verification executes in the reference runtime.
5. CI batches compatible implementation work and does not start one Docker container per model implementation.

## Verification

1. Generic `cad_verification` source is local under `modules/verification/`.
2. Model-specific expectations remain with the physical model owner.
3. A migration slice is accepted only with retained evidence equivalent to the historical Forge baseline for the behavior under migration.
4. Verification-only model owners must not appear in the public catalogue.

## Migration

1. The historical Forge repository remains the known-good comparison source until parity is demonstrated.
2. Migrate one physical model end-to-end, then five, then ten, before enabling the remaining graph.
3. Do not delete the historical external verification repository until all real consumers have migrated.
4. Do not copy historical scripts, builders or site code merely because they exist. Re-home only behavior with a real owner.
5. Release behavior remains separate from early model migration.

## Documentation

1. Keep `docs/plan.md` as the source of truth for unfinished work.
2. Keep `docs/handoff.md` usable as a standalone continuation message.
3. Use Hugo/Hextra; Pages never runs CAD.
4. API, guide and reference content becomes normal documentation while CAD models use the shared model presentation.
