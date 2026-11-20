# 0036 — native circular feature patterns

Status: **implementation in qualification**  
Issue: **#293**  
SolidCraft target: **0.42.0**

## Problem

Forge already exposed SolidCraft's native rectangular feature pattern through
`Shape.rectangular_pattern(...)`, but had no circular sibling. A bolt-circle
model therefore had to either expand repeated cuts in Python or bypass Forge,
even though SolidCraft owns a native `solid.pattern.circular` history feature.

## Public API

```python
flange = flange.circular_pattern(
    bolt_cut,
    count=bolts,
    axis=Axis.Z,
)
```

The source feature follows the same rules as `rectangular_pattern()`: it is a
`Sketch.extrude()` feature that has already been applied to the body.

Supported axis forms are:

- `Axis.X`, `Axis.Y` or `Axis.Z`;
- a fixed non-zero XYZ direction through the world origin;
- either form with `origin=(x, y, z)` for a shifted fixed axis.

Native construction-axis, edge-axis and face-axis selectors remain future API
extensions instead of being exposed as raw SolidCraft selector dictionaries.

`angle=None` intentionally omits the native angle field so SolidCraft uses its
own 360-degree default. A supplied fixed angle is expressed in degrees; a direct
Parameter is registered with native unit `deg`.

## Shared pattern rules

Rectangular and circular feature patterns now share source-feature validation.
Both accept one source feature or a non-empty sequence, require those features
to be part of the current Shape, and emit one native history pattern command.

Pattern count Parameters are dimensionless. Circular angle Parameters use
degrees. Reusing one Parameter in incompatible count/angle/length roles is
rejected instead of silently assigning the wrong native unit.

## Qualification

Unit tests cover source validation, principal and shifted fixed axes, full and
partial angles, count/angle parameter units, alignment/reversal and exact
native command lowering.

The focused native qualification uses one through-hole cut on a rectangular
plate and repeats it six times around the Z axis with one
`solid.pattern.circular` feature.
