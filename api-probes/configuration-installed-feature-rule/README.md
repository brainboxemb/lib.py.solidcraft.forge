# Installed feature rule checkbox probe

## Why this probe exists

Free/Installed is not a configuration-row axis.

The base configuration row owns the normal/free geometry. Installed is an
independent state switch that must remain orthogonal to whatever row axis the
model already has.

SolidCraft 0.50 provides exactly that UI through a native Configuration Rule:
the rule has its own `enabled` checkbox and may drive feature suppression.

## Question

Can one real named post-Extrude feature remain suppressed in the normal row,
while an independent native rule named `Installed` enables that feature by
driving its suppression to false?

## Model

The probe creates:

~~~text
FreeProfile
-> ClampExtrude
-> Installed        offset_face, initially/config-row suppressed
~~~

Configuration:

~~~text
row
  Normal:
    Suppress Installed = true

rule
  Installed:
    enabled = false
    condition = always
    effect = drive_suppression(Installed, false)
~~~

Expected UI meaning:

~~~text
Normal row + Installed unchecked -> Free
Normal row + Installed checked   -> Installed
~~~

The rule checkbox is independent of the row. A future Small/Medium/Large row
axis can therefore coexist with the same Installed switch without creating a
Cartesian row table.

## What success proves

A green probe proves that SolidCraft 0.50 can use the actual authored Installed
history feature with the desired one-row-plus-checkbox presentation.

It also proves that the earlier two-row Free/Installed proposal was the wrong
configuration model for this use case.

## Geometry boundary

The `offset_face` geometry is diagnostic only. This probe qualifies the
configuration-rule/suppression mechanism, not the final HUB75 clamp operation.
