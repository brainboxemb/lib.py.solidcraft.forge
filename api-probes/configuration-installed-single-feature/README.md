# Installed single-feature fan-out probe

## Why this probe exists

The desired assembly has one global Installed control. When it changes, every
part of the model that belongs to the Installed transition changes with it.

The previous group experiment proved that SolidCraft timeline folders can group
several history features, but Configuration does not accept a folder as a
feature target.

This probe tests the simpler native model suggested by an existing SolidCraft
configuration UI example: make Installed one real history feature, and let that
one feature act on several bodies.

## Exact question

Can one native feature named `Installed`:

1. operate on two separate bodies in one history step;
2. be configured as a suppression target;
3. be driven by one independent Configuration Rule checkbox while Small/Large
   remains the ordinary row axis?

## Model

Two coupler bodies are created separately. One `solid.move` feature named
`Installed` moves both bodies in the same history operation.

The configuration contains:

~~~text
rows:
    Small
    Large

configured feature:
    Installed

independent rule:
    Installed [off/on]
        -> drive suppression of feature Installed
~~~

Both rows store `Installed` suppressed. Enabling the independent rule drives
the one feature unsuppressed without changing the active row.

## What success proves

A green probe proves that SolidCraft can represent:

~~~text
one Installed checkbox
        |
        v
one real Installed history feature
        |
        +--> body A
        +--> body B
~~~

This is materially different from one checkbox trying to target several
separate features.

It means a global Forge Installed scope could potentially lower to one native
multi-object feature where the backend operation can truthfully represent the
whole transition as one history step.

## What this probe does not prove

It does not prove that every kind of Installed transition can be expressed as
one native SolidCraft feature. Some designs may need several different history
operations.

It also does not define the eventual Forge `with feature(...)` API.

## Decision informed

If this succeeds, the preferred SolidCraft lowering for a global Installed
transition is one real named feature whenever the participating CAD operation
can act on all required objects in one native history step.

Only cases that genuinely require several independent native history features
still need another composition strategy.
