# Configuration position suppression probe

## Why this probe exists

The configuration API design needs to distinguish two different kinds of
"position":

- moving model geometry as an authored CAD history step; and
- changing the placement of a reusable component occurrence in an assembly.

SolidCraft 0.49 exposes `solid.move` as a real history feature, while
`occurrence.move` stores an occurrence transform and does not return a history
feature. Native configuration suppression targets history features.

This probe tests the first case directly instead of assuming that every kind of
position can be configured through suppression.

## Question

Can a named `solid.move` feature represent a positional state and be selected
as a normal SolidCraft configuration suppression target?

## Model

The probe creates:

- a fixed base plate;
- a panel body in its normal position;
- one history feature named `ServicePosition` which moves the panel 30 mm;
- one configuration suppression target for that feature.

The rows are:

| Row | ServicePosition |
| --- | --- |
| Normal | suppressed |
| Service | active |

The saved design is left in `Normal`.

## What success proves

A green probe proves that a positional change authored as one real CAD history
feature can use the same configuration mechanism as any other suppressible
feature. In the SolidCraft UI the user can switch between the rows and the move
feature is suppressed or active.

## What this probe does not prove

This does **not** prove that an assembly `occurrence.move` can itself be
suppressed. SolidCraft 0.49 documents `occurrence.move` as an occurrence
transform operation whose reply contains `occurrence`, `transform` and
`pending`, not a timeline feature.

The existing `configuration-position` model therefore remains the qualified
route for true occurrence placement: configuration parameters are referenced by
`Placement` / `occurrence.move` expressions.

This distinction is intentional evidence for the Forge API design. Forge should
not pretend that body-history movement and occurrence placement are the same
backend capability.

## Decision this probe informs

If the user intent is naturally a real authored transition such as
`ServicePosition`, Forge may expose it as a named suppressible feature.

If the intent is the placement of a reusable occurrence, Forge needs a separate
placement binding/lowering path unless SolidCraft later exposes occurrence
moves as suppressible history features.
