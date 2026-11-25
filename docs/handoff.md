# Forge handoff

Repository: `brainboxemb/lib.py.solidcraft.forge`.

This document is the easy-to-find handoff entrypoint for a new work session.
It contains one copyable handoff message below.

The handoff message is deliberately an entrypoint, not a second repository
plan. Current work must always be derived from live GitHub state and
`docs/plan.md`.

Shared SolidCraft/CAD documentation conventions live in
`brainboxemb/meta.cad.solidcraft`. Use `templates/docs/plan.md` and
`templates/docs/handoff.md` there as structural references.

## Handoff message

Copy the complete text block below into a new chat.

~~~text
You are continuing work on brainboxemb/lib.py.solidcraft.forge.

Repository role:

- this repository is the canonical Forge repository and owns the public
  `scpf` package under `cadlib/`;
- `models/<id>/` is the single physical CAD owner boundary, with multiple
  engine implementations kept inside that owner when historically real;
- generic CAD-CI, verification, runtime/container and product-model concerns
  remain in their owning repositories rather than being reimplemented here.

Use this handoff only as the entrypoint. Do not treat copied handoff text as
fresher than GitHub or the repository plan.

Start by:

1. inspecting the current issues, pull requests and branches;
2. reading AGENTS.md;
3. reading docs/plan.md;
4. treating docs/plan.md as the source of truth for unfinished work;
5. reading docs/requirements.md and docs/design.md before changing behavior or
   architecture;
6. following the current work order from the plan rather than from old handoff
   text;
7. creating an issue before implementation when the logical change has none;
8. keeping one logical change to one issue, branch and PR;
9. updating requirements/design documentation when behavior or architecture
   changes;
10. reconciling the plan after merge or release.

Durable working rules:

- preserve the public `scpf` import/package contract and fix lost Forge API
  behavior in `cadlib/scpf` rather than with model-local workarounds;
- keep one physical owner per model and use `model.yml.purpose` only as a
  presentation projection for `example`, `verification`, or both;
- generated CAD artifacts remain on `build/<scope>/models/**`; Pages reads
  durable evidence and must not duplicate generated CAD artifacts into
  `gh-pages`;
- use `main` for stable integration and `dev` for normal integration;
  squash normal short-lived work branches into `dev`, promote explicit
  product stabilization `dev -> main` with a merge commit, and prepare
  metadata-only releases on `release/vX.Y.Z` branches created from stable
  `main` and squashed directly to `main`; after publication synchronize
  the stable-only release commit back with `main -> dev` and never rebase
  the shared permanent branch;
- execute every source-branch integration by posting `/merge` on the pull
  request and letting `.github/workflows/merge-policy.yml` choose the merge
  method; never use direct merge API, auto-merge or manual merge fallback;
- repeated `/merge` after a pull request is already merged is an idempotent
  successful no-op; a closed but unmerged pull request remains an error;
- preserve the two released CAD runtime roles, `reference` and `solidcraft`,
  unless a separately qualified change updates that contract;
- use the archived `brainboxemb/lib.py.solidcraft.forge.OLD` repository only as
  historical A/B or provenance evidence when needed;
- do not copy retired historical orchestration or site machinery when the
  corrected template/module architecture already owns that responsibility.

Shared document structures live in brainboxemb/meta.cad.solidcraft:
templates/docs/plan.md and templates/docs/handoff.md.

Do not copy exact current SHAs, runtime/release pins, active issue/PR status,
temporary migration phases or a short-lived "next actions" list into this
handoff. Those facts belong in GitHub and docs/plan.md.
~~~

## Maintenance guidance

The text block above is the actual handoff message.

Everything outside that block only explains how to use or maintain the
document. Keep repository-specific durable role and ownership guidance in the
block when it helps route work correctly. Do not turn the handoff into a status
snapshot.
