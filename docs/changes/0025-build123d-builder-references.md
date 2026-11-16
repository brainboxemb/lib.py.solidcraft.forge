# 0025 — build123d qualification references use native Builder style

## Problem

The first build123d reference set used mostly Algebra-mode expressions. That
proved geometry, but hid an important part of build123d's normal Python API:
`BuildPart`, `Locations`, combination `Mode` values and reusable custom
part objects.

## Decision

Qualification references should use idiomatic build123d Builder syntax when it
makes the model clearer. They do not mimic Forge syntax.

Typical CSG comparison:

```python
with BuildPart() as model:
    Sphere(20)
    with Locations((18, 0, 10)):
        Box(30, 30, 20)
    with Locations(Rot(0, 90, 0)):
        Cylinder(4, 120, mode=Mode.SUBTRACT)
    with Locations((0, 0, 15)):
        Box(50, 50, 30, mode=Mode.INTERSECT)
```

Complex reusable geometry may use build123d custom objects based on
`BasePartObject`. The flightcase-corner qualification deliberately does this
so the reference shows one reusable corner object placed eight times.

Algebra mode remains acceptable where it is the clearer build123d expression.

## Runner contract

A reference still exposes `model`. When `model` is a `BuildPart` builder,
the exporter uses `model.part`. Final Shape/Part/Compound values remain
supported.

## Qualification

All existing qualification geometry and expected envelopes stay fixed. Only
the build123d source style and exporter acceptance are changed. Full reference
execution/rendering must pass for every registered case.
