# Post-Extrude direct geometry suppression probe

## Why this probe exists

The existing `ServicePosition` probe proves a later `solid.move` can be a
saved suppressible state feature. The clamp needs the same history concept but
with a geometry-changing operation.

This probe checks a direct geometry modifier after Sketch + Extrude.

## Question

Can one native `solid.offset_face` authored after Extrude be named
`Installed` and used directly as a saved configuration suppression target?

## Model

The geometry is intentionally simple:

~~~text
FreeProfile Sketch
-> ClampExtrude
-> Installed: offset one side face by 4 mm
~~~

Rows:

| Row | Installed |
| --- | --- |
| Free | suppressed |
| Installed | active |

The script activates Installed and then returns to Free. Both row changes must
rebuild successfully.

## What success proves

A green probe proves:

- a direct post-Extrude geometry edit is normal native history;
- it can carry stable feature identity;
- the existing configuration mechanism can suppress/enable it;
- saved row switching does not need another state abstraction.

## What this does not prove

The rectangular face offset is not a flexible-clamp model.

It does not prove that `solid.offset_face` alone can open the HUB75 ring while
preserving wall thickness. It only proves the history/configuration pattern with
a true geometry modifier.

## Decision this informs

If this passes while the Sketch-edit probe shows no later feature, Forge should
keep configuration unchanged and focus the next API design on the smallest
generic post-Extrude geometry operation required by the clamp.
