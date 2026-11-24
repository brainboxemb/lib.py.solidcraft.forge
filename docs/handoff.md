# Handoff

Continue in `brainboxemb/lib.py.solidcraft.forge.NEW`.

Read `AGENTS.md`, `docs/requirements.md`, `docs/design.md` and `docs/plan.md` first.

## Stable baseline

`main@cf8bd232065279fad69e711ce46787612fa62ad7` is the accepted corrected physical model-owner baseline.

The public package is migrated as `cadlib/src/scpf`. The historical Forge repository remains unchanged as the A/B reference.

## Active work

Issue #6 / draft PR #7 owns the first real historical model migration.

`models/simple-box` is the single physical Parameterized Box owner:
- SCPF is the primary implementation;
- historical CadQuery/build123d/PythonSCAD/pyBOSL2 sources are reference implementations;
- `builder-scpf` compiles local SCPF and delegates native execution to generic `builder-solidcraft`;
- geometry verification runs for all five implementations in `reference`;
- native saved-design/timeline verification runs only for SCPF in `solidcraft`.

The branch consumes the generic staged-verification contract from `template.cad.library#25`; do not replace it with Forge-local scheduler logic.

OLD machine evidence is retained on `brainboxemb/lib.py.solidcraft.forge:build` under `dev-cad/examples/simple-box/`. Compare NEW native baseline and `length_50` evidence directly against those files.

## Handoff message

> Continue `brainboxemb/lib.py.solidcraft.forge.NEW` from `docs/plan.md`. Finish issue #6 only. Qualify the staged native + geometry run for the one `models/simple-box` owner. Compare NEW baseline parameters/timeline/bounds and the saved `length=50` mutation directly with OLD `build/dev-cad/examples/simple-box` machine evidence. Then merge #7 to dev, verify durable `build/dev/models/simple-box` and Hugo projection, and only then start the five-model migration.
