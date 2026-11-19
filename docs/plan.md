# Forge repository plan

This file contains only current unfinished repository work.

Completed work is removed from this plan after it is merged. Permanent design
decisions belong in the normal repository documentation; Git history and closed
issues preserve the history.

## Current work: finish the verification and CAD-CI migration

### 1. Release and extend the reusable CAD verification library

Forge currently consumes an unreleased source commit of
`brainboxemb/lib.py.cad.verfication`. That is not an acceptable final
dependency boundary.

Complete these verification-library issues first:

- `brainboxemb/lib.py.cad.verfication#3` — independently verify and release the library;
- `brainboxemb/lib.py.cad.verfication#4` — add the reusable cross-CAD geometry,
  mesh, visual and semantic-result mechanics required by Forge.

Forge must then pin the exact released revision and record the library
version/revision in verification evidence.

### 2. Restore the complete Forge model-verification contract — #410

The current 32 `model_verify` items already cover native replay, the baseline
native assertions, all 18 saved-design mutations and both historical post-build
inspections.

Complete the missing historical verification layers:

- each model's own command/integration contract;
- one model-owned geometry proof shared by native/reference/visual checks;
- deterministic native visual verification and expected-shape evidence;
- independent PythonSCAD, pyBOSL2, CadQuery and build123d reference checks;
- clear semantic model-level result evidence.

Do not expand Forge `tool_verify`; catalog models remain `model_verify`
items.

Remove this section when #410 is merged.

### 3. Finish durable build output and Pages publication — #366

Move the remaining build-output and GitHub Pages publication work onto the
released generic CAD-CI infrastructure only after the complete verification
evidence contract is authoritative.

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
