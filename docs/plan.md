# Forge repository plan

This file contains only current unfinished repository work.

Completed work is removed from this plan after it is merged. Permanent design
decisions belong in the normal repository documentation; Git history and closed
issues preserve the history.

## Current work: finish the CAD-CI migration

### 1. Migrate the next 10 historical qualification models — #395

Add `model_verify` for:

1. `anchored-holes`
2. `hole-family`
3. `sheet-fold`
4. `top-sketch-after-chamfer`
5. `parameter-scope`
6. `parent-derived-child-size`
7. `components`
8. `repeated-parent-attachments`
9. `assembly-decorator`
10. `group-hierarchy`

Use historical Forge commit
`be40b09e7454a90e87d83768a9e7453c52ba5d76` as the migration reference for
model expectations, mutations and inspections.

When #395 is merged, remove this section from the plan.

### 2. Migrate the remaining historical qualification models

Continue in the historical qualification registry order until every required
model has a `model_verify` path.

Use one reviewable migration PR per agreed batch.

Remove this section when the model catalog migration is complete.

### 3. Finish durable build output and Pages publication — #366

Move the remaining build-output and GitHub Pages publication work onto the
released generic CAD-CI infrastructure.

Publication consumes existing build/verification evidence and must not rerun
Forge or model verification merely to build the site.

Remove this section when #366 is merged.

### 4. Final migration audit

After the previous sections are complete:

- confirm no obsolete qualification/CI architecture remains active;
- run the complete intended CI verification;
- confirm unchanged targets are reusable/CURRENT where expected;
- confirm the active documentation matches the final implementation.

When this audit passes, remove this section. If no other work is planned,
`docs/plan.md` may then contain only the next repository work or be removed.
