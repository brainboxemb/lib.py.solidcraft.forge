# Handoff

Continue work in `brainboxemb/lib.py.solidcraft.forge.NEW`.

Read `AGENTS.md`, `docs/requirements.md`, `docs/design.md` and `docs/plan.md` first.

## Current intent

This is the clean Forge migration target built on `template.cad.library`. Preserve the public package/import name `scpf`. The historical `brainboxemb/lib.py.solidcraft.forge` repository is the known-good A/B reference and must not be modified as part of this migration unless explicitly requested separately.

Bootstrap issue: #1.

The technical template baseline is `template.cad.library@f73c3e76066b16751d4bd1eb7f1c221e0f3fc3fe`. SCPF begins from the released 0.15.0 package. Runtime remains `docker.cad.solidcraft v0.3.5` / SolidCraft 0.48.1.

## Repository model

- `cadlib/src/scpf/`: Forge/SCPF product source.
- `cadlib/tests/`: package-owner tests.
- `modules/`: generic CI/builders/verification/preview/build/Pages.
- `examples/`: template qualification fixtures now; real Forge examples migrate later.
- `site/`: Hugo/Hextra.

Use normal NEW branch policy: short-lived branch -> squash to `dev`; `dev -> main` merge promotion.

## Immediate next action

Finish qualifying bootstrap issue #1. Fix only true migration/layout failures. Do not pull old Forge CI/site scripts across to make tests green.

After bootstrap is accepted, create the one-example migration issue. Choose a small real Forge example that has SCPF source, reference implementations and a geometry contract. Migrate that example end-to-end and compare OLD vs NEW. Then expand 1 -> 5 -> 10 -> remaining graph.

## Handoff message

> Continue `brainboxemb/lib.py.solidcraft.forge.NEW` from `docs/plan.md`. This is a clean migration onto `template.cad.library`, not an in-place Forge refactor. Keep `scpf` as the public package. Do not modify the old Forge repo; use it as the A/B baseline. Finish the current bootstrap/qualification first. Then migrate one real Forge example end-to-end and compare source semantics, SolidCraft commands, native/STL geometry, verification, preview and Hugo output before expanding to 5 and 10 examples.
