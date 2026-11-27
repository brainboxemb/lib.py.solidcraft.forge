# CAD builder and model-owner contract

Forge NEW uses the corrected `template.cad.library` ownership model.

A physical directory under `models/<id>/` is selected and published once. Its `ci.yml` may declare multiple implementations. Standard engine implementations remain local details of the owner.

The template qualification owner is `models/simple-box`. It runs CadQuery, build123d, PythonSCAD, pyBOSL2 and SolidCraft against one shared geometry expectation.

Forge-specific migrated owners add an SCPF implementation whose consumer-owned compiler produces a SolidCraft command document. That document then enters the unchanged generic SolidCraft builder. Generic builder modules never import `scpf`.

Reference implementations run in the shared reference role. SolidCraft command execution runs first in the lightweight SolidCraft role and its STL is then verified in reference.

Durable evidence is grouped by physical owner:

```text
build/<scope>/models/<owner>/
  result.json
  source.json
  model.stl
  model.png
  <implementation>/
    build.json
    result.json
    model.stl
    verification/
```

The configured primary implementation supplies the canonical owner-level preview/STL. Every declared implementation must pass before the owner passes.

Pages may read the durable build plan and link generated artifacts from the build branch. Generated CAD artifacts are never copied into `gh-pages`.
