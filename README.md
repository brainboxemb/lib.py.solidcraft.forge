# lib.py.solidcraft.forge

Canonical repository for SolidCraft Forge / SCPF.

Forge is the Python API/compiler for expressing SolidCraft CAD models while
preserving native SolidCraft features, parameters, assemblies and editable
history. The public Python package/import name remains `scpf`.

The historical pre-migration implementation is preserved read-only at
`brainboxemb/lib.py.solidcraft.forge.OLD` as A/B and provenance evidence.

## Repository roles

- `cadlib/` — the real SCPF consumer library (`scpf`).
- `models/` — physical model owners with SCPF/reference implementations and owner-local verification.
- `modules/` — repository-local CI, standard CAD builders, verification, preview, build publication and Pages capabilities.
- `site/` — Hugo/Hextra documentation and model presentation.
- `docs/` — requirements, architecture, plan, development/release guidance and handoff.

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

Not every model needs every implementation; the owner declares the
implementations required for its qualification.

## Current baseline and provenance

- corrected CAD library template:
  `brainboxemb/template.cad.library@1d9cddfe975d508e2aaa03cb140cbf61e2fdff82`;
- historical Forge source baseline:
  `brainboxemb/lib.py.solidcraft.forge.OLD@8ddcf7e6f58e8da12750d63a5d3604101c9c2824`;
- public Python package/import: `scpf`;
- CAD runtime: `docker.cad.solidcraft v0.3.6`;
- tested SolidCraft: `0.49.0`.

The OLD→NEW migration is complete. New product/API work belongs here; the
archived historical repository is no longer an integration target.
