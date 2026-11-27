# Installed exported-feature probe

## Why this probe exists

This tests whether a reusable component can publish one real `installed`
feature and let the final design configure that feature through normal
suppression.

## Question

Can `Suppress(clamp.feature("installed"))` lower to a native SolidCraft
configuration feature target and survive saved-design replay?

## Model

The component exports one extra cutter as `installed`.

- `Free` suppresses that feature;
- `Installed` activates it.

The cutter only makes the two states visibly different. It is not intended as
the mechanical model of a flexible clamp.

## What success proves

Forge can address one explicitly exported child feature from the final design
and SolidCraft can store its suppression state per configuration row.

## Important finding

The Forge export name is component-local API identity. Current lowering resolves
the right SolidCraft history feature but does not propagate the export name to
its native display/history name, so retained evidence used a generated name
such as `Cylinder3`.

## Decision this probe informs

A real Free/Installed component interface can be based on exported feature
handles, but Forge still needs a deliberate rule for semantic feature naming in
the native backend.
