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

## Active work — #29

The twenty-owner candidate is technically accepted:
- candidate source: `553033bdd2ccf0e5612e8f12d2a95c51a51ec462`;
- CI run: **45456265226**;
- qualification artifact: **14950656646**;
- evidence: `docs/acceptance/twenty-owner-gate.md`.

PR #30 adds the ten remaining owners from historical Basic geometry and Parent/child features and faces. The migration also restores the historical public `Sketch.revolve()` SCPF contract in `cadlib/scpf`; do not replace this with a model workaround.

Remaining #29 work:
- squash PR #30 to `dev`;
- verify all twenty durable owners and the purpose-driven Pages projection;
- promote `dev -> main` only after the full promotion gate passes;
- use a merge commit for that promotion;
- close #29 only after stable post-merge CI/build/Pages/deployment pass.

## Handoff message

> Continue `brainboxemb/lib.py.solidcraft.forge.NEW` from issue #29 / PR #30. The twenty-owner candidate is qualified at `553033bdd2ccf0e5612e8f12d2a95c51a51ec462` by CI `45456265226`; see `docs/acceptance/twenty-owner-gate.md`. Finish the integration gate: squash PR #30 to dev, verify `build/dev/models` has all twenty owners and Pages has exactly three Examples plus all twenty Verification entries, then run the full dev-to-main promotion and merge it with a merge commit. Close #29 only after stable post-merge CI/build/Pages/deployment pass.
