# Handoff

Continue in `brainboxemb/lib.py.solidcraft.forge.NEW`.

Read `AGENTS.md`, `docs/requirements.md`, `docs/design.md` and `docs/plan.md` first.

## Accepted baseline

The five-owner gate is accepted on `dev@606f07588c8a41ee4f2ae18aef55ff25d1ceb2fc`.

Accepted owners:
- `simple-box`;
- `primitive-csg`;
- `anchored-holes`;
- `assembly-decorator`;
- `parametric-attach`.

All owner-local command contracts, native stages and applicable geometry stages pass. SCPF replay documents retain historical multi-phase semantics through `scpf.headless.run_document()`. The A/B evidence and historical bundle hashes are recorded in `docs/acceptance/five-owner-gate.md`.

Permanent `build/dev/models` output exists for all five owners. Pages semantics are purpose-driven: owners with `example` appear under Examples; owners with `verification` appear under Verification; owners with both appear in both views.

## Active work — #21

PR #24 is squash-merged to `dev@8f28cbb46acd894554a2152611aec5d161a9ab38`. Post-merge CI `45448096247` is green and `build/dev/models` contains all ten owners. A/B evidence is recorded in `docs/acceptance/ten-owner-gate.md`. The remaining blocker is the Pages migration: the current implementation incorrectly publishes only `example` owners. Fix the projection so Examples contains the three example owners and Verification contains all ten verification owners, then qualify Pages and promote the full ten-owner baseline to main.

Move from five accepted owners to ten total:

6. `corner-anchor`;
7. `rectangular-pattern`;
8. `rotated-sketch-cutter`;
9. `slot-family`;
10. `sheet-fold`.

Keep the same migration discipline:
- one physical owner;
- SCPF primary;
- only historical reference implementations that actually existed;
- historical model-local tests and verification definitions;
- OLD build evidence as A/B authority;
- no Forge-specific scheduler logic.

Before starting the owner migration, promote the accepted five-owner `dev` baseline to `main` with a full promotion run.

## Handoff message

> Continue `brainboxemb/lib.py.solidcraft.forge.NEW` from issue #21. The five-owner gate is accepted and durably published on `dev@606f07588c8a41ee4f2ae18aef55ff25d1ceb2fc`; see `docs/acceptance/five-owner-gate.md`. First promote this baseline from dev to main with a full run. Then migrate `corner-anchor`, `rectangular-pattern`, `rotated-sketch-cutter`, `slot-family` and `sheet-fold` as physical owners, preserving historical purposes, only existing reference implementations, model-local tests and native/saved-design/inspection evidence.
