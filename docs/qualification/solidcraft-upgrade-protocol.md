# SolidCraft upgrade protocol

This protocol defines how Forge and the downstream CAD project move to a new
SolidCraft release without changing production branches before compatibility is
proven.

## Single source of truth

The SolidCraft version is configured in exactly one operational place:

```python
# scpf/scpf/version.py
TESTED_SOLIDCRAFT_VERSION = "0.42.0"
```

No GitHub Actions workflow should contain its own SolidCraft version literal.

The Forge qualification workflow installs SCPF and reads
`TESTED_SOLIDCRAFT_VERSION`. The CAD workflow first restores its exact pinned
Forge revision and then reads the same value from the installed `scpf`
package.

The CAD repository therefore owns only the **Forge revision pin**. It does not
own a second SolidCraft version setting.

## Branch convention

Use the same candidate branch name in both repositories:

```text
qualify/solidcraft-<version>
```

Example:

```text
qualify/solidcraft-0.42
```

Never start an engine qualification by changing `main` directly.

## Phase 1 — establish the baseline

1. Confirm the current Forge `main` qualification is green.
2. Confirm the current CAD `main` native workflow is green.
3. Record the current Forge and CAD commit SHAs.
4. Create the Forge qualification branch from current `main`.

If the baseline is not green, fix the existing regression before testing a new
SolidCraft version.

## Phase 2 — change only the candidate version

On the Forge qualification branch:

1. Change only `TESTED_SOLIDCRAFT_VERSION` to the candidate release.
2. Do not initially change compiler behaviour, command JSON or model code.
3. Run the full Forge qualification against the candidate version.

This first run answers one question: **does the existing Forge command contract
still work unchanged?**

If it does, the upgrade is potentially a one-line engine-version change.
If it does not, compatibility changes are made only on the qualification
branch and each change must be explained by a failing qualification case or a
documented SolidCraft API change.

## Phase 3 — Forge qualification

The candidate must pass all existing qualification levels:

- Q1 — Python API contract;
- Q2 — generated SolidCraft command contract;
- Q3 — native SolidCraft build;
- Q4 — native measurement/semantic validation;
- Q5 — saved-design parametric mutation;
- Q6 — native visual regression.

In addition:

1. every native timeline must be free of errors;
2. STEP and saved `.sc` artifacts must still be produced;
3. joint, occurrence and parameter behaviour must remain associative;
4. command acceptance alone is not sufficient evidence;
5. unexpected warnings or geometry differences must be investigated rather
   than accepted automatically.

If Forge requires a compatibility change, add or update a regression test that
proves the required behaviour.

## Phase 4 — downstream CAD qualification

Only after a Forge candidate commit is available:

1. Create the matching CAD qualification branch.
2. Pin `dependencies.repos` to the exact Forge qualification commit SHA.
3. Let the CAD workflow read the SolidCraft version from that installed Forge.
4. Run the complete native CAD workflow against the candidate engine.

The CAD run must cover:

- every catalogued SCPF model;
- the SCPF/SCPC comparison models;
- native saved-design parameter changes;
- component occurrences and assembly joints;
- expected body counts and bounding boxes;
- generated snapshots and STEP output;
- the HUB75 wood-frame regression checks.

No project model is changed merely to make an engine upgrade appear green. A
model change is acceptable only when the old model relied on behaviour that is
demonstrably obsolete or incorrect in the new SolidCraft API.

## Phase 5 — review the evidence

Before promotion, review:

1. Forge qualification results;
2. CAD native workflow results;
3. command-plan differences where the compiler changed;
4. native feature-history differences where relevant;
5. visual snapshots for unexpected geometry changes;
6. saved-design parameter mutations;
7. SolidCraft warnings and timeline errors.

A green process exit without semantic/geometry evidence is not sufficient.

## Acceptance criteria

The candidate can be promoted only when all of the following are true:

- Forge Q1 through Q6 pass;
- the complete CAD native workflow passes;
- saved-design parameter mutations remain associative;
- all required native models are closed/valid as expected;
- SCPF/SCPC comparison cases still agree;
- there are no unexplained native warnings or geometry regressions;
- any required Forge compatibility changes have regression coverage.

## Phase 6 — promote to main

Promotion order is fixed:

1. Merge the qualified Forge branch to Forge `main`.
2. Record the resulting Forge `main` commit SHA.
3. Update the CAD qualification branch to pin that exact merged Forge SHA.
4. Run the CAD native workflow once more with the final Forge SHA.
5. Merge the CAD branch to CAD `main` only after that final run is green.

This prevents CAD `main` from ever pointing at an unqualified Forge revision.

## Failure and rollback

A failed candidate is not rolled back on `main`, because `main` was never
changed.

Either:

- fix the compatibility issue on the qualification branch and rerun the full
  protocol; or
- abandon/delete the qualification branches and keep the existing qualified
  SolidCraft version.

Do not weaken qualification assertions merely to make a new engine version
pass.

## Upgrade record

For each successful engine upgrade, retain in Git history:

- the qualification branch/PR;
- the SolidCraft version;
- the qualified Forge commit;
- the final CAD pin;
- any compatibility changes;
- the successful Forge and CAD workflow evidence.

That history is the compatibility record for future SolidCraft upgrades.
