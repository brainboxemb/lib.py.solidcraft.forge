# Forge repository plan

This file contains only current unfinished repository work.

Completed work is removed from this plan after it is merged. Permanent design
decisions belong in the normal repository documentation; Git history and closed
issues preserve the history.

## Current work: finish the CAD-CI migration

### 1. Separate SolidCraft runtime image lifecycle from Forge CI — #404

Move Docker runtime build/publication out of the normal Forge workflow.

- add a dedicated SolidCraft runtime workflow;
- keep `workflow_dispatch` so the runtime build can be triggered explicitly;
- also trigger on changes to runtime inputs on `main`;
- normal Forge CI only resolves and checks the immutable runtime image;
- normal Forge CI never builds or publishes Docker images.

When #404 is merged, remove this section from the plan.

### 2. Migrate the next 10 historical qualification models — #395

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

### 3. Migrate the remaining historical qualification models

Continue in the historical qualification registry order until every required
model has a `model_verify` path.

Use one reviewable migration PR per agreed batch.

Remove this section when the model catalog migration is complete.

### 4. Finish durable build output and Pages publication — #366

Move the remaining build-output and GitHub Pages publication work onto the
released generic CAD-CI infrastructure.

Publication consumes existing build/verification evidence and must not rerun
Forge or model verification merely to build the site.

Remove this section when #366 is merged.

### 5. Final migration audit

After the previous sections are complete:

- confirm no obsolete qualification/CI architecture remains active;
- run the complete intended CI verification;
- confirm unchanged targets are reusable/CURRENT where expected;
- confirm the active documentation matches the final implementation.

When this audit passes, remove this section. If no other work is planned,
`docs/plan.md` may then contain only the next repository work or be removed.
