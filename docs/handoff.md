# Handoff

Continue in `brainboxemb/lib.py.solidcraft.forge.NEW`.

Read `AGENTS.md`, `docs/requirements.md`, `docs/design.md` and `docs/plan.md` first.

## Accepted baseline

The ten-owner migration gate is accepted and promoted on `main@378b5051cc2accc98e4774af3189d377be52ab1c`.

Accepted physical owners:
- `simple-box`;
- `primitive-csg`;
- `anchored-holes`;
- `assembly-decorator`;
- `parametric-attach`;
- `corner-anchor`;
- `rectangular-pattern`;
- `rotated-sketch-cutter`;
- `slot-family`;
- `sheet-fold`.

All owner-local command contracts pass. All 10 native SCPF stages and all 45 applicable geometry stages pass. Historical saved-design/inspection behavior and SCPF multi-phase replay semantics are retained. A/B evidence is recorded in `docs/acceptance/five-owner-gate.md` and `docs/acceptance/ten-owner-gate.md`.

Permanent `build/main/models` and `build/dev/models` output exists for all ten owners.

Pages uses `model.yml.purpose` as a presentation projection, not as a visibility filter:
- Examples contains `simple-box`, `anchored-holes` and `corner-anchor`;
- Verification contains all ten owners;
- an owner with `[example, verification]` appears in both views while remaining one physical owner;
- generated CAD artifacts remain on `build`, not `gh-pages`.

## Active work

Continue with the remaining historical model graph.

Keep the established migration discipline:
- one physical owner;
- SCPF primary;
- only historical reference implementations that actually existed;
- preserve historical `model.yml.purpose`;
- preserve model-local source/compiler tests and native/saved-design/inspection expectations;
- use OLD durable build evidence as A/B authority;
- keep scheduler/builders/verification generic and do not add Forge-specific orchestration.

## Handoff message

> Continue `brainboxemb/lib.py.solidcraft.forge.NEW` from the accepted ten-owner baseline on `main@378b5051cc2accc98e4774af3189d377be52ab1c`; see `docs/acceptance/ten-owner-gate.md`. Classify and migrate the remaining historical physical owners in controlled groups. Preserve each owner's historical purpose, only existing reference implementations, model-local tests and native/saved-design/inspection evidence. Keep one physical owner across engines, SCPF primary, generic CI mechanics outside Forge-specific code, and compare against the OLD durable build evidence before accepting each group.
