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

Keep the existing qualification and release workflows unchanged.

Add one operational workflow named **Qualify main**. It uses the same existing
qualification scripts, immutable qualification image and publication commands,
but has its own workflow name so it cannot be mistaken for a release run.

It can be started in two simple ways:

- a normal commit that changes `.github/workflows/qualify-main.trigger` on `main`;
- the parameterless GitHub **Run workflow** button on `main`.

The workflow runs against the exact current `main` SHA and then:

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

A preflight-only PR that introduces or edits this recovery path may encounter an
already incomplete `build/main`. In that situation the PR still runs repository
preflight and contract tests, but skips the optional PR website preview instead
of failing on the stale baseline. Technical PRs remain strict.

## Verification

Contract tests prove that:

- `Qualify main` runs only for `main`;
- changing only `.github/workflows/qualify-main.trigger` is sufficient to start it;
- the workflow uses the existing immutable qualification image,
  verification gate and publication commands;
- the existing full-safety and release workflows remain unchanged;
- the release workflow does not listen to `Qualify main`.
