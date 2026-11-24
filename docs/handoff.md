# Handoff

Continue in `brainboxemb/lib.py.solidcraft.forge.NEW`.

Read `AGENTS.md`, `docs/requirements.md`, `docs/design.md` and `docs/plan.md` first.

## Stable baseline

`main@cf8bd232065279fad69e711ce46787612fa62ad7` is the accepted corrected physical model-owner baseline.

The public package is migrated as `cadlib/src/scpf`. The historical Forge repository remains unchanged as the A/B reference.

## Active work

Issue #6 / draft PR #7 owns the first real historical model migration.

`models/simple-box` is the single physical Parameterized Box owner. It must contain:
- SCPF as primary implementation;
- the historical CadQuery/build123d/PythonSCAD/pyBOSL2 references;
- historical owner metadata and geometry expectations;
- Forge-specific command-lowering assertions only where their owner is clear.

Do not recreate engine-specific sibling owners.

The final missing contract is native SolidCraft saved-design/parameter/timeline verification. Upstream `brainboxemb/template.cad.library#25` provides the generic multi-stage runtime mechanism. Consume that after it is qualified rather than adding a local scheduler exception.

## Handoff message

> Continue `brainboxemb/lib.py.solidcraft.forge.NEW` from `docs/plan.md`. Finish issue #6 only. Keep `models/simple-box` as one physical owner with SCPF primary and four historical reference implementations. Consume staged verification from `template.cad.library#25` for the native saved-design check, then record explicit OLD vs NEW command/geometry evidence and qualify durable build/Pages. Do not expand to five models until this slice is accepted.
