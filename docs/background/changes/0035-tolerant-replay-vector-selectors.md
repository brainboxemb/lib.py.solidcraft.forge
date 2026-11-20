# 0035 — tolerant numeric-vector replay selectors

Status: **implementation in qualification**  
Issue: **#278**  
SolidCraft target: **0.42.0**

## Problem

A TOP-attached Sketch selects its support face from `model.faces`. Forge asks
for the largest planar face whose outward normal points along +Z:

```text
where plane_normal = [0, 0, 1]
max area
```

Replay previously compared every `where` value with normal Python equality.
That made a numeric vector such as `[0, 0, 1]` require bit-for-bit equality
with the floating-point vector returned by the CAD kernel.

After native feature operations such as chamfer, an otherwise valid planar top
face can contain tiny floating-point noise in its reported unit normal. The
face is still geometrically the +Z face, but exact list equality rejects it and
the attached Sketch cannot be replayed.

## Fix

Replay selector matching now treats a pair of numeric vectors specially:

- lengths must match;
- every component must be a real number, not a bool;
- each component is compared with `abs_tol=1e-9` and no relative tolerance.

Other selector values keep exact equality. In particular, text, ids, indexes
and other scalar values do not become fuzzy.

## Unit tests

The replay tests prove both sides of the rule:

- a +Z normal with tiny kernel-style noise still matches `[0, 0, 1]`;
- a materially different direction such as `[0, 0, 0.999]` does not match.

Compiler tests also build the same TOP-attached Sketch after both a vertical
chamfer and a vertical fillet, proving both feature paths use the same
`model.faces` selector.

Native SolidCraft qualification uses the chamfer case because only the native
kernel can prove the actual returned face normal and saved face attachment.
