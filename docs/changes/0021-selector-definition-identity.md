# Change 0021 — Forge selectors in reusable definition identity

**Status:** implementation  
**SolidCraft target:** 0.42.0  
**Extends:** change 0012

## Problem

Change 0012 made reusable component definition identity reject arbitrary mutable
or opaque Python objects. That prevents two physically different component
builds from silently sharing one native definition.

The safe-value list was incomplete for Forge's own immutable selector objects.

A valid reusable component such as:

```python
@component
class Board:
    fillet = None

    def build(self):
        body = Box(40, 20, 5)
        if self.fillet:
            body = body.fillet(2, edges=self.fillet)
        return body

bottom = Board(
    fillet=(BOTTOM + LEFT, BOTTOM + RIGHT),
)
```

failed before build with:

```text
_DirectionSelector cannot be used in reusable component definition identity
```

The downstream HUB75 wood-frame model exposed this while validating SCPF 0.4.1.

## Contract

Forge's own immutable selector values are valid fixed reusable-component inputs
when they can be reduced to stable primitive identity data.

Supported selector identity values are:

- cardinal `_DirectionSelector` -> its three-value direction vector;
- `_ProfileEdgeSelection` -> patterns, sides and selection kind;
- public axis token `X` / `Y` / `Z` -> a typed axis-token value;
- `_BoundOffset` -> axis, reference and a recursively safe fixed delta.

The internal class names remain private. Users continue to write the public
objects such as `BOTTOM + LEFT`, `Edges.from_profile(...)` and
`X.MIN + 10`.

A plain string `"X"` and the public axis token `X` intentionally have
different identity values because they can drive different build behaviour.

Unsupported arbitrary/mutable objects remain rejected.

A `_BoundOffset` whose delta is not itself a safe fixed identity value remains
rejected rather than silently hashing a runtime Python object.

## Lowering

This change affects definition deduplication only.

It does not alter the selector passed to `build()`, SolidCraft command
lowering, replay variables or public CAD geometry semantics.

Two occurrences with the same component class and same selector input share one
native definition. Different selector inputs produce different definitions.

## Qualification

Required regressions:

- equal `BOTTOM + LEFT` selector values produce equal definition identity;
- different cardinal selectors produce different identity;
- Board-style tuples of cardinal fillet selectors are accepted and deduplicate;
- different `Edges.from_profile(...)` selections differ;
- axis token `X` does not collide with plain string `"X"`;
- different fixed `X.MIN + n` values differ;
- arbitrary mutable/object inputs remain rejected;
- full Q1-Q6 qualification remains green.

## Exit condition

> Forge rejects unknown object identity, but accepts its own immutable
> build-affecting selector values through deterministic primitive identity data.
