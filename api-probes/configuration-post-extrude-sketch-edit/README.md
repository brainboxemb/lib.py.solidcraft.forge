# Post-Extrude Sketch edit probe

## Why this probe exists

The motivating clamp flow wants to author the Free clamp first and then apply one
later Installed geometry change that can be suppressed.

SolidCraft has `sketch.edit` and `sketch.move_points`, so this probe checks
what those commands actually mean in history after an Extrude already depends
on the Sketch.

## Question

After:

~~~text
FreeProfile Sketch
-> ClampExtrude
-> edit FreeProfile and move points
~~~

does SolidCraft retain a new later history feature for the edit, or does it
rewrite `FreeProfile` and rebuild `ClampExtrude`?

## Model

The probe:

1. creates a 20 x 20 mm rectangle Sketch named `FreeProfile`;
2. extrudes it 8 mm as `ClampExtrude`;
3. reopens `FreeProfile`;
4. moves the two right-hand points from X=10 to X=12;
5. finishes the Sketch;
6. inspects `FreeProfile` and `ClampExtrude`.

The generated saved design and command output are the evidence.

## What success proves

A successful replay proves that a source Sketch can be edited after downstream
geometry exists and that the dependent Extrude rebuilds.

It does **not** by itself prove a suppressible Installed step. The important
inspection is whether the saved timeline contains any new feature for the edit.

If the timeline still contains only the original Sketch plus Extrude, then
`sketch.move_points` is an in-place authoring edit and cannot truthfully be
wrapped as one later `feature("installed")`.

## Decision this informs

This decides whether Forge can model Installed as a semantic Sketch-edit feature
or must use a real post-Extrude direct-geometry history operation instead.
