# Forge repository plan

This file contains only current unfinished repository work.

Completed work is removed from this plan after it is merged. Permanent design
decisions belong in the normal repository documentation; Git history and closed
issues preserve the history.

## Current work: finish the CAD-CI migration

### 1. Release the reusable CAD verification library — lib.py.cad.verfication #5

Forge currently consumes `lib.py.cad.verfication` from an exact development
commit. Complete and formally release version 0.1.0 before treating the library
as the reusable released verification dependency.

After the release:
- record the released version and exact commit in Forge runtime metadata;
- rebuild/publish the immutable SolidCraft runtime with that released revision.

Remove this section when the library release is complete and Forge consumes it.

### 2. Complete the Forge verification contract — #378

The 32 historical model cases now have `model_verify`, but that is only the
native model layer.

Complete the already-agreed verification contract:

- keep the existing native geometry/history verification;
- keep saved-design mutations and post-build inspections;
- restore `verify_references`;
- restore independent PythonSCAD / pyBOSL2 / CadQuery / build123d reference
  execution and comparison where required;
- restore render/visual evidence and visual baseline regression;
- restore independent expected-shape/goal-overlay evidence;
- restore `build_diagrams`;
- add the final `verification-summary` / `collect_results` fan-in without
  rerunning model work.

Do not recreate the old qualification runner or Q-number vocabulary. Reuse
`tool.cad.ci` for execution and `lib.py.cad.verfication` for generic
verification mechanics.

Remove this section when #378 is complete.

### 3. Make accepted verification output durable on the build branch — #366

A verification result is complete only after its accepted item output has been
written durably to the `build` branch under the corresponding source item path.

Proceed incrementally:

1. prove one model end-to-end: `model_verify -> accepted item output -> build`;
2. extend the same mechanism to all required verification items;
3. confirm partial updates replace only affected item output;
4. confirm reused/CURRENT items retain their accepted durable output.

Do not use or recreate the old central `qualification/` build layout.

When durable build storage is complete, replace this section with the remaining
Pages work only.

### 4. Publish Pages from accepted durable build output — #366

After durable item output is authoritative:

- publish stable and preview Pages through `tool.cad.ci`;
- consume accepted build output instead of rerunning technical verification;
- keep Forge-owned site content and presentation in Forge;
- remove superseded Forge-owned branch publication code.

Remove this section when #366 is merged.

### 5. Final migration audit

After the previous sections are complete:

- confirm no obsolete qualification/CI architecture remains active;
- run the complete intended verification graph;
- confirm unchanged targets are reusable/CURRENT where expected;
- confirm accepted verification output is present on `build`;
- confirm the active documentation matches the final implementation.

When this audit passes, remove this section. If no other work is planned,
`docs/plan.md` may then contain only the next repository work or be removed.
