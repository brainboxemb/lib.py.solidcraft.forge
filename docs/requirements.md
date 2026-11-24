# Forge NEW requirements

## Repository

1. Preserve the public SCPF Python API and import name `scpf` during migration.
2. Use the qualified CAD library repository architecture rather than reproducing the historical Forge-local CI stack.
3. Keep source ownership explicit: library, examples, generic modules, documentation and generated evidence are separate roles.
4. Use `main` as stable and `dev` as development integration.
5. Generated build and Pages output must live on `build` and `gh-pages`, never mixed into release evidence.

## CAD execution

1. Reuse only the released `reference` and `solidcraft` runtime roles from `docker.cad.solidcraft v0.3.5` until a separately qualified upgrade exists.
2. Standard reference builders are PythonSCAD, pyBOSL2, CadQuery and build123d.
3. SolidCraft executes in its lightweight runtime; generic mesh verification executes in the reference runtime.
4. CI must batch compatible work and must not start one Docker container per example.
5. Builder, verifier and preview behavior must remain module-owned and engine-neutral at the scheduler boundary.

## Verification

1. Generic `cad_verification` source is local under `modules/verification/`.
2. Model-specific expectations remain with the example.
3. A migration slice is accepted only with retained evidence that the new result is equivalent to the old Forge baseline for the behavior under migration.
4. Verification-only fixtures must not appear in the public example catalogue.

## Migration

1. The historical Forge repository remains the known-good comparison source until parity is demonstrated.
2. Migrate one example end-to-end, then five, then ten, before enabling the remaining graph.
3. Do not delete the external historical verification repository until all real consumers have migrated.
4. Do not copy historical scripts, builders or site code merely because they exist. Re-home Forge-specific behavior only when no template capability owns it.
5. Release behavior is out of the bootstrap slice; first establish package/build/verification/site parity.

## Documentation

1. Keep a current `docs/plan.md` as the source of truth for unfinished work.
2. Keep `docs/handoff.md` usable as a standalone continuation message.
3. Use Hugo/Hextra for the new site; Pages never runs CAD.
4. API, guide and reference content should become normal documentation pages while CAD examples use the established CAD presentation layout.
