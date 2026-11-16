# Change 0020 — Profile-specific Sketch.add default anchor

**Status:** implementation  
**SolidCraft target:** 0.42.0  
**Corrects:** change 0018 / SCPF 0.4.0

## Problem

Change 0018 made semantic centering the default for dimension-defined profiles
by giving `Sketch.add()` this public default:

```python
sketch.add(profile, anchor=Anchor.CENTER, offset=(0, 0))
```

That is correct for Circle2D, Rectangle2D and RoundedRectangle2D, but it made an
existing Text2D use case impossible.

Text2D does not expose an insertion-point argument in its constructor. Its
sketch-local insertion point is supplied by `Sketch.add(..., offset=(u, v))`.
Because the default anchor was CENTER and Text2D deliberately rejects CENTER,
this valid model stopped compiling in SCPF 0.4.0:

```python
with Sketch(name="Label", on=body) as sketch:
    sketch.add(
        Text2D("Pi 4"),
        offset=(-9, 18),
    )
```

The CAD project exposed this regression while validating the 0.4.0 release.

## Contract

`Sketch.add()` becomes:

```python
sketch.add(profile, anchor=None, offset=(0, 0))
```

`anchor=None` means **use the natural default for this profile type**:

- Circle2D, Rectangle2D and RoundedRectangle2D -> Anchor.CENTER;
- Text2D and Polygon2D -> keep their own authored/insertion coordinates.

The visible behaviour for dimension-defined profiles therefore does not change:
they are still centred by default.

For Text2D, `offset=(u, v)` remains the supported way to set the native text
insertion point because Text2D has no separate coordinate argument.

Explicit `anchor=Anchor.CENTER` on Text2D or Polygon2D remains rejected until a
qualified semantic centre exists for those profile types.

Polygon2D keeps its existing compiler limits. This change does not add new
support for moving polygon vertices through a non-zero Sketch.add offset where
that lowering is not already supported.

## Lowering

No new SolidCraft command is introduced.

Text2D still lowers to:

```text
sketch.text(..., at=[u, v], ...)
```

Dimension-defined profiles still lower using their semantic centre plus any
deliberate local offset.

The change is only in how the omitted public `anchor` argument is resolved
before those existing lowering paths run.

## Qualification

Required evidence:

- `Sketch.add(Rectangle2D(...))` is still centred by default;
- `Sketch.add(Text2D(...), offset=(-9, 18))` emits text insertion
  `at=[-9, 18]`;
- explicit `anchor=CENTER` remains rejected for Text2D;
- explicit `anchor=CENTER` remains rejected for Polygon2D;
- automatic Text2D/Polygon2D capture keeps authored coordinates;
- full Q1-Q6 qualification remains green.

## Exit condition

> Omitting anchor chooses the profile's defined default; semantic CENTER is the
> default for dimension-defined profiles, while coordinate-defined profiles keep
> their own coordinate system.
