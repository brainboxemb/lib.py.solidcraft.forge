# CAD builder and model-owner contract

Forge NEW uses the corrected `template.cad.library` ownership model.

A physical directory under `models/<id>/` is selected and published once. Its `ci.yml` may declare multiple implementations. Standard engine implementations remain local details of the owner.

The template qualification owner is `models/simple-box`. It runs CadQuery, build123d, PythonSCAD, pyBOSL2 and SolidCraft against one shared geometry expectation.

Forge-specific migrated owners normally add an SCPF implementation whose consumer-owned compiler produces a SolidCraft command document. That document then enters the unchanged generic SolidCraft builder.

The experimental `builder-scpf-mitcad` is intentionally different: it is a Forge-owned SCPF backend adapter builder and therefore calls `run_script(..., backend="mitcad")` directly, then executes the resulting native Mitcad document through the already-qualified headless boundary. It retains `model.mitcad` and `model.stl`; the central runtime writes the normal implementation `build.json`. This capability is not attached to owners until an immutable `mitcad` runtime exists. Generic non-SCPF engine builders remain unaware of Forge semantics.

Reference implementations run in the shared reference role. SolidCraft command execution runs first in the lightweight SolidCraft role and its STL is then verified in reference. The experimental Mitcad builder declares runtime role `mitcad`, but that role is intentionally absent from root `ci.yml` until #221 provides an immutable image.

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
