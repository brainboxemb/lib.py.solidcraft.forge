# SolidCraft qualification protocol for Forge

This protocol defines how Forge qualifies a new SolidCraft release. It stops at
the Forge boundary: the CAD repository is upgraded only after Forge itself is
fully qualified.

## One version source

Forge has exactly one operational SolidCraft version setting:

```python
# scpf/scpf/version.py
TESTED_SOLIDCRAFT_VERSION = "0.42.0"
```

Everything else reads this value automatically:

- `scpf.version.check_cli_version()` uses it for the runtime compatibility
  check;
- the Forge qualification workflow reads it to download the matching official
  SolidCraft release;
- the generated library and qualification pages show it as the tested version;
- source-matched native verification accepts evidence only for this exact
  version.

A workflow, site builder or qualification script must not contain a second
SolidCraft version literal.

## Qualification branch

Create the candidate from current Forge `main`:

```text
qualify/solidcraft-<major>.<minor>
```

Example:

```text
qualify/solidcraft-0.42
```

`main` remains on the previously qualified version until the candidate has
passed this complete protocol.

## 1. Verify the baseline

Before changing the version:

1. Confirm Forge `main` qualification is green.
2. Record the Forge `main` commit SHA.
3. Create the qualification branch from that exact SHA.

Existing failures are fixed before an engine upgrade starts.

## 2. Change only the version first

Change only `TESTED_SOLIDCRAFT_VERSION`.

Do not initially change:

- Forge compiler behaviour;
- generated SolidCraft command structures;
- qualification models;
- expected geometry.

Run the complete Forge qualification suite. This first run answers:

> Does the existing Forge API and command contract work unchanged on the new
> SolidCraft release?

Only a demonstrated incompatibility justifies a Forge code change.

## 3. Run Forge's own qualification projects

The candidate is tested only with Forge's self-contained examples and
qualification cases. The downstream CAD repository is not part of this stage.

All levels must pass:

- Q1 — Python API contract;
- Q2 — generated SolidCraft command contract;
- Q3 — native SolidCraft build;
- Q4 — native semantic and measurement validation;
- Q5 — saved-design parametric mutation;
- Q6 — native visual regression.

Additionally:

- native timelines contain no unexplained errors;
- saved `.sc` files and STEP exports are produced;
- parameter mutations remain associative;
- joints and occurrence placement retain their intended semantics;
- visual differences are understood rather than silently accepted.

Command acceptance alone is not qualification.

## 4. Visible review result

Every successful `qualify/**` workflow publishes its generated site to a
separate GitHub Pages preview:

```text
/previews/<qualification-branch>/
```

For example:

```text
/previews/solidcraft-0.42/
```

The workflow summary prints direct links to:

- the full preview;
- `qualification/results/`.

The review page must visibly contain:

- the exact Forge source commit;
- the SolidCraft version from `TESTED_SOLIDCRAFT_VERSION`;
- the per-case qualification status;
- native measurements and evidence links;
- generated visual evidence.

The Actions artifact remains the complete retained evidence archive. The Pages
preview is the human review surface.

A candidate is not promoted solely because the workflow icon is green; the
published qualification results are reviewed as part of the protocol.

## 5. Investigate a failure

When the candidate fails:

1. Find the smallest failing qualification case.
2. Determine whether the cause is a SolidCraft API change, changed semantics, a
   Forge compiler assumption, an obsolete workaround, or an engine regression.
3. Change Forge only after the cause is understood.
4. Add or update regression coverage for every required compatibility change.
5. Run the complete qualification suite again.

Do not weaken assertions merely to make a newer release pass.

## 6. Forge acceptance criteria

Forge is qualified only when:

- Q1 through Q6 pass;
- all Forge qualification projects build natively;
- saved-design mutations pass;
- no unexplained native errors or warnings remain;
- geometry/visual evidence is reviewed;
- required compatibility changes have regression coverage;
- the published preview identifies the correct source commit and SolidCraft
  version.

At this point the branch is a qualified Forge candidate.

## 7. Promote Forge

1. Merge the qualified branch to Forge `main`.
2. Run the complete Forge qualification once more on the resulting `main`
   commit.
3. Review the normal published Forge qualification site.
4. Record the final Forge `main` SHA and successful workflow run.

Only that final qualified Forge `main` SHA is handed to the separate CAD
upgrade protocol.

## Abort

If the candidate cannot be qualified, abandon the qualification branch.
`main` was never changed, so no production rollback is necessary.

## Qualification record

Keep in Git history and CI:

- SolidCraft release number;
- qualification branch/PR;
- compatibility changes and their tests;
- final qualified Forge commit SHA;
- Q1–Q6 workflow evidence;
- published preview/result page.

The CAD upgrade begins only after this Forge record is complete.
