# Installed single-feature configuration probe

## Why this probe exists

The desired assembly has one authored Installed feature that can affect several
parts of the model at once.

SolidCraft already exposes configured feature suppression directly as a checkbox
in the configuration table:

~~~text
Suppress: <feature name>
~~~

This probe checks that one real multi-body feature named `Installed` can be
used directly as such a configuration target, without Configuration Rules.

## Exact question

Can one native feature named `Installed`:

1. operate on two separate bodies in one history step;
2. be added directly as one configuration suppression column;
3. expose its suppression value per configuration row without any rule layer?

## Model

Two coupler bodies are created separately. One `solid.move` feature named
`Installed` moves both bodies in the same history operation.

The configuration contains:

~~~text
rows:
    Small
    Large

columns:
    spacing
    Suppress: Installed
~~~

There are no Configuration Rules.

## What success proves

A green probe proves that SolidCraft can represent:

~~~text
one real Installed history feature
        |
        +--> body A
        +--> body B
        |
        v
one direct configuration suppression column
~~~

The configuration itself owns the suppression values.

## What this probe does not prove

A suppression column is row-owned. Small and Large may store different
suppression values.

This probe therefore does not prove a separate global boolean dimension outside
the configuration rows.

It also does not define the eventual Forge scoped feature syntax.

## Decision informed

For the concrete feature/configuration use case, Forge should not insert
`ConfigRule`, `Always`, `DriveParameter` or `drive_suppression`.

The direct lowering is simply:

~~~text
authored Installed feature
    -> configured suppression target
~~~

Only a separate requirement for state that must remain independent while rows
change would justify investigating another mechanism.
