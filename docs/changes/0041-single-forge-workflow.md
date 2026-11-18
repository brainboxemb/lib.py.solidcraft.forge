# 0041 — Single Forge workflow

**Tracks:** issue #346  
**Supersedes operational entry points from:** changes 0038 and 0039  
**Scope:** GitHub Actions UX, risk orchestration, main promotion, recovery,
publication, image reuse, reconcile and release.

## Problem

Forge exposed implementation phases as separate GitHub Actions workflows:
preflight, PR verification, affected qualification, full safety, site deploy,
qualification smoke/image, contract snapshot, reconcile and release.

For a one-person repository this made normal operation depend on remembering
which Action represented the desired end result.

## Decision

Keep exactly one active workflow file:

```text
.github/workflows/forge.yml
name: Forge
```

`scripts/forge_scope.py` converts event metadata and changed paths into one
tested plan containing operation, risk, gate, affected cases, image need,
pipeline smoke, contract validation, site-only reuse and release eligibility.

The operator never selects Q1/Q2/Q6/full.

## Event contract

- active PR: risk-based gate plus preview;
- closed PR: remove only that PR's generated namespaces;
- main push: reuse complete `build/main` for presentation-only work, otherwise
  run the required technical gate and promote into `build/main`;
- manual Forge run on main: full exact-main recovery, never a release trigger;
- `.github/workflows/forge.trigger` change on main: same full recovery;
- weekly cron: full safety;
- daily cron: generated-output reconcile.

A package-version change on main is the explicit release signal. It requires
full Q1-Q6 and only after successful build/Pages publication may the release job
inside the same Forge run tag and publish the version.

## Stable build rule

`build/main` is always a native-qualified baseline. A PR may legitimately need
only Q1/Q2, but a corresponding stable main promotion upgrades that affected
case to Q1-Q6 before replacing its stable evidence.

Sparse verified main candidates use the same schema-v2 promotion logic as PR
overlays and preserve all unaffected cases byte-for-byte.

## Performance

The immutable qualification image remains the expensive reusable boundary.
Forge first pulls the content-addressed image. It builds, smoke-tests and pushes
the image only when that identity is absent.

Changes limited to CI/orchestration use repository preflight plus one complete
`simple-box` native case and one exact-stage rerun. They do not trigger a full
catalog qualification merely because workflow wiring changed.

Pinned SolidCraft contract validation runs in the same cached image.

## Workflow boundaries

The workflow may contain multiple jobs because cleanup, reconcile and release
have different event/security boundaries. They remain part of the same visible
**Forge** run.

Policy belongs in tested Python. YAML may wire Actions, environments and
repository commands but must not duplicate case selection, branch layout or
risk classification.

## Verification

Regression tests require:

- exactly one active `.yml` workflow file, `forge.yml`;
- planner coverage for PR/main/manual/trigger/schedules/cleanup/release;
- one-case pipeline smoke for orchestration changes;
- immutable image reuse before rebuild;
- sparse main promotion preserving unaffected cases;
- presentation reuse validating against `build.json.source_commit`;
- generated branch writes through the retrying publisher;
- no workflow-to-workflow dispatch.
