# 0023 — build123d as fourth independent qualification reference

**Tracks:** issue #196  
**Scope:** qualification sources, runner, website and test infrastructure only.  
**Forge public API:** unchanged.  
**Pinned package:** `build123d==0.12.0`.

## Decision

Every supported qualification case normally has four independent, executable
Python references:

1. PythonSCAD — direct Python constructive solid geometry.
2. pyBOSL2 — anchors and attachment-oriented modelling.
3. CadQuery — assembly, workplane and object placement.
4. build123d — algebraic, parametric OpenCascade-based geometry.

For each `<implementation>`, the source is
`examples/<slug>/<implementation>/model.py`. It exposes `model` as final
geometry. The qualification runner executes the source, exports
`model.stl` using the reference's own export API, compares its bounds
against the independently maintained expected envelope, and produces
`model-front.png`, `model-right.png`, `model-iso.png`, and `result.json`.

The runner must fail on missing code, import errors, absent STL output,
incorrect bounds, or missing renders. The published qualification site
must show all four references and source/evidence links.

## Exceptions

A missing build123d reference is allowed only with a concrete, documented
`reference_exceptions["build123d"]` technical reason in that case's metadata.
The same rule already applies to the other three. 'Not implemented yet' is
not a technical exception. No baseline case gets an exception.

## Independence and geometry

Reference files import build123d directly, not Forge or CadQuery. Avoid
generating models by converting Forge commands or importing CAD output.
All four are independent geometric checks of the same visible intent.

Build123d STL does not prove persisted SolidCraft history, joint identity,
or parameter mutation. Native Q3–Q6 remain the evidence for those properties.

Build123d defaults to centered Box/Cylinder. Explicit `Align.MIN` in Z
reproduces a bottom-based design only when that design requires it. Cylinder
accepts radius, not diameter, and its export is the function
`export_stl(model, filename)` rather than a `model.export()` method.

## Reproducibility

Pin build123d 0.12.0 in a dedicated reference virtual environment in full and affected/preview CI. pyBOSL2 and build123d have incompatible `webcolors` requirements, so they must not share one Python environment.
Store common API syntax locally in `docs/agent/reference-libraries.md`;
routine qualification work should not need a new external code search.

This extends, rather than retroactively rewrites, change 0004's historical
three-library baseline. Existing qualification geometry and the three older
reference sources stay fixed unless a task explicitly changes that case.
