# lib.py.solidcraft.forge.NEW

Clean migration target for SolidCraft Forge.

This repository rebuilds Forge on the corrected `template.cad.library` architecture while preserving the public Python package/import name `scpf`. The historical `brainboxemb/lib.py.solidcraft.forge` repository remains the known-good A/B reference until migration parity is proven.

## Repository roles

- `cadlib/` — the real SCPF consumer library (`scpf`).
- `models/` — physical model owners with SCPF/reference implementations and owner-local verification.
- `modules/` — repository-local CI, standard CAD builders, verification, preview, build publication and Pages capabilities.
- `site/` — Hugo/Hextra documentation and model presentation.
- `docs/` — requirements, architecture, migration plan, development/release guidance and handoff.

A model owner may contain multiple implementations:

```text
models/<id>/
  ci.yml
  model.yml
  scpf/model.py
  cadquery/model.py
  build123d/model.py
  pythonscad/model.py
  pybosl2/model.py
  verification/...
```

Not every model needs every implementation; the owner declares the implementations required for its qualification.

## Migration baseline

- corrected CAD library template: `brainboxemb/template.cad.library@1d9cddfe975d508e2aaa03cb140cbf61e2fdff82`;
- historical Forge source baseline: `brainboxemb/lib.py.solidcraft.forge@8ddcf7e6f58e8da12750d63a5d3604101c9c2824`;
- migrated package keeps the public name `scpf`;
- CAD runtime: `docker.cad.solidcraft v0.3.6` / SolidCraft 0.49.0.

The migration expands physical models deliberately: **1 → 5 → 10 → remaining graph**. The old Forge repository stays authoritative until equivalent package, CAD, verification and site evidence exists here.
