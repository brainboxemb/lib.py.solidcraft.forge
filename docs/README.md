# Forge documentation

The active documentation set is intentionally small. Historical migration
material and obsolete documents live under `legacy/` and are not current
instructions.

## Repository work

Read in this order:

1. `../AGENTS.md` — agent/automation governance and merge policy.
2. the current **main** version of `plan.md` — canonical unfinished work.
3. `architecture.md` — repository and compiler ownership boundaries.
4. `requirements.md` — durable product invariants.
5. the relevant API/design document for the change.

`handoff.md` is only a session entrypoint. It routes work back to live GitHub
state and the current main plan.

## Active documents

- `architecture.md` — Forge architecture and ownership boundaries.
- `requirements.md` — stable invariants; feature details belong in API docs
  and executable tests.
- `api.md` — current cross-object public SCPF API contract.
- `design-api/` — API proposals under active design review. A proposal is not
  automatically released API.
- `development.md` — normal development, testing and API-probe workflow.
- `release.md` — current release preparation/publication boundary.
- `reference/` — versioned retained SolidCraft reference evidence.
- `plan.md` / `handoff.md` — governance/session entrypoints, with
  `plan.md` canonical on main.

## User/site sources

Public Guide, API Reference and Cheatsheet inputs are owned by `site/source/`.
The Guide is still stored there in its pre-Hugo HTML source format. The agreed
direction is Markdown/Hugo; that conversion is separate parked work. Do not add
new Guide chapters in the old HTML format.

## Legacy

`legacy/` contains migration gates, old broad design/requirements documents,
obsolete Forge NEW manuals and other historical context. These files are not
authoritative. Useful content must be moved into an active document before a
legacy file is removed.

## Placement rule

Before adding repository material, identify its owner:

- user-facing site content -> `site/`;
- active architecture or requirements -> this directory;
- public API proposal -> `design-api/`;
- versioned external evidence -> `reference/`;
- historical context -> `legacy/`;
- CI/Pages/runtime machine input -> the owning module or package, not `docs/`.
