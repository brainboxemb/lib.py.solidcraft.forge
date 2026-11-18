# 0039 — Simple main qualification trigger

**Tracks:** issue #343  
**Scope:** operational recovery of `main -> build/main -> Pages`.

## Use case

The repository needs one simple way to rebuild the published state from the
current `main`:

`main -> qualification -> build/main -> Pages`

This is an operational recovery action. It is not a release action and it does
not require a temporary qualification branch.

## Decision

Keep the existing qualification implementation in
`.github/workflows/scpf.yml`, but make that workflow reusable through
`workflow_call`.

Add a small entry workflow named **Qualify main**. It can be started in two
simple ways:

- a normal commit that changes `.github/workflows/qualify-main.trigger` on `main`;
- the parameterless GitHub **Run workflow** button on `main`.

The entry workflow calls the existing qualification workflow against the exact
current `main` SHA. The existing main-only steps then:

1. build and verify the complete technical baseline;
2. replace `build/main`;
3. build and test the stable site from that baseline;
4. replace stable Pages.

The entry workflow has its own workflow name. It is therefore separate from the
release workflow trigger, which listens to the direct
`SCPF full safety qualification` workflow.

## Trigger file

`.github/workflows/qualify-main.trigger` is an operational marker only. Updating its
single value is enough to request a new main qualification through a normal
repository commit.

No source or model code is encoded in the marker.

## Verification

Contract tests prove that:

- the existing qualification workflow supports `workflow_call`;
- `Qualify main` runs only for `main`;
- changing only `.github/workflows/qualify-main.trigger` is sufficient to start it;
- the wrapper calls the existing qualification workflow instead of duplicating
  qualification steps;
- the release workflow does not listen to `Qualify main`.
