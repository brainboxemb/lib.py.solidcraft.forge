# Handoff

Continue in `brainboxemb/lib.py.solidcraft.forge.NEW`.

Read `AGENTS.md`, `docs/requirements.md`, `docs/design.md` and `docs/plan.md` first.

## Stable baseline

`main@2594ff03b5dbae0e558e8ee65ce0a558292add6f` is the accepted pre-model-owner bootstrap.

The public package is already migrated as `cadlib/src/scpf`. Historical Forge remains unchanged as the A/B reference.

## Active work

Issue #11 / branch `issue/11-model-owner-sync` aligns NEW with the corrected stable library template `template.cad.library@1d9cddfe975d508e2aaa03cb140cbf61e2fdff82`.

Required result:
- `models/` physical owner root;
- one simple-box owner with five standard engine implementations;
- owner-level selection/publication;
- durable model output only on `build`;
- Pages links build artifacts instead of duplicating them.

Only after #11 is promoted should issue #6 / draft PR #7 be reshaped from the old example-owner layout into `models/simple-box/`.

## Handoff message

> Continue `brainboxemb/lib.py.solidcraft.forge.NEW` from `docs/plan.md`. Finish issue #11 first: sync the corrected physical model-owner contract from `template.cad.library@1d9cddfe975d508e2aaa03cb140cbf61e2fdff82`. Preserve `cadlib/src/scpf` and Forge-specific docs. Qualify one owner with five implementations and durable `build/<scope>/models` output. Then rework issue #6 / draft PR #7 for the historical Forge simple-box and continue 1 -> 5 -> 10.
