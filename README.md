# lib.py.solidcraft.forge.NEW

Clean migration target for SolidCraft Forge.

This repository rebuilds Forge on the qualified `template.cad.library` architecture while preserving the public Python package/import name `scpf`. The existing `brainboxemb/lib.py.solidcraft.forge` repository remains the known-good A/B reference until migration parity is proven.

## Repository roles

- `cadlib/` — the real SCPF consumer library (`scpf`).
- `examples/` — public examples and verification-only qualification fixtures.
- `modules/` — repository-local CI, standard CAD builders, verification, preview, build publication and Pages capabilities.
- `site/` — Hugo/Hextra documentation and generated example presentation.
- `docs/` — requirements, architecture, migration plan, manual and handoff.

## Migration baseline

- CAD library template: `brainboxemb/template.cad.library@f73c3e76066b16751d4bd1eb7f1c221e0f3fc3fe`.
- Forge source: `brainboxemb/lib.py.solidcraft.forge`; package source starts from released SCPF 0.15.0.
- CAD runtime: `docker.cad.solidcraft v0.3.5` / SolidCraft 0.48.1.

The migration expands examples deliberately: **1 → 5 → 10 → remaining graph**. The old Forge repository stays authoritative until equivalent package, CAD, verification and site evidence exists here.

Read `AGENTS.md`, `docs/requirements.md`, `docs/design.md`, `docs/development.md`, `docs/plan.md`, `docs/release.md` and `docs/handoff.md` before changing the repository.
