# Handoff

Continue in `brainboxemb/lib.py.solidcraft.forge.NEW`.

Read `AGENTS.md`, `docs/requirements.md`, `docs/design.md` and `docs/plan.md` first.

## Accepted baseline

The corrected physical model-owner architecture is qualified.

`simple-box` is the first accepted historical Forge owner:
- SCPF primary;
- historical CadQuery/build123d/PythonSCAD/pyBOSL2 references;
- native SolidCraft baseline + saved-design verification in `solidcraft`;
- geometry verification for all implementations in `reference`;
- OLD/NEW command and measurement parity;
- durable owner-grouped build output;
- Pages shows named `native` and `geometry` evidence.

Issues #6 and #14 are closed. Do not reopen engine-specific sibling owners.

## Active work — #16

PR #19 has a fully green five-owner candidate at `5939c926957446b73e3669941acff9b9d44ecc63` (CI `45441165279`). `docs/acceptance/five-owner-gate.md` records OLD vs NEW command/native/saved-design/geometry evidence. The next action is integration: merge PR #19 to `dev`, verify durable `build/dev/models` for all five owners and confirm Pages exposes only `simple-box` and `anchored-holes` before opening the 10-owner gate.

Move from one accepted owner to five total:

1. `simple-box` — already accepted;
2. `primitive-csg`;
3. `anchored-holes`;
4. `assembly-decorator`;
5. `parametric-attach`.

The old repository `brainboxemb/lib.py.solidcraft.forge` remains the A/B authority. Use its source and generated `build` branch as machine evidence.

Preserve each historical `model.yml.purpose` exactly. Verification-only models stay out of public Pages; owners with `example` are public.

Do not add Forge-specific scheduling logic. Consumer-owned SCPF compilation may remain in `builder-scpf`; build/runtime/verification orchestration stays generic.

## Handoff message

> Continue `brainboxemb/lib.py.solidcraft.forge.NEW` from `docs/plan.md`, issue #16. The 1-owner gate is accepted. Migrate the four selected historical owners so the repository has five total: `primitive-csg`, `anchored-holes`, `assembly-decorator`, `parametric-attach`, plus accepted `simple-box`. Keep one physical owner per model, preserve historical purposes and reference implementations, migrate native/geometry/saved-design expectations from source, compare against retained OLD build evidence, and do not start the 10-owner gate until all five are accepted.
