# Forge repository plan

This file contains only current unfinished repository work.

Completed work is removed from this plan after it is merged. Permanent design
decisions belong in the normal repository documentation; Git history and closed
issues preserve the history.

## Current work: finish the CAD-CI migration

### 1. Migrate the remaining historical qualification models

Continue in the historical qualification registry order until every required
model has a `model_verify` path.

Use one reviewable migration PR per agreed batch.

Remove this section when the model catalog migration is complete.

### 2. Finish durable build output and Pages publication — #366

Move the remaining build-output and GitHub Pages publication work onto the
released generic CAD-CI infrastructure.

Publication consumes existing build/verification evidence and must not rerun
Forge or model verification merely to build the site.

Remove this section when #366 is merged.

### 3. Final migration audit

After the previous sections are complete:

- confirm no obsolete qualification/CI architecture remains active;
- run the complete intended CI verification;
- confirm unchanged targets are reusable/CURRENT where expected;
- confirm the active documentation matches the final implementation.

When this audit passes, remove this section. If no other work is planned,
`docs/plan.md` may then contain only the next repository work or be removed.
