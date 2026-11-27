# Native Installed feature-name probe

## Why this probe exists

The exported-feature probe showed that the correct native history feature was
configured but still had an implementation-generated name such as
`Cylinder3`.

This direct SolidCraft probe isolates naming from Forge lowering.

## Question

Can SolidCraft 0.49 rename that history feature to `Installed` before adding
it as a configuration suppression target?

## Model

The probe creates the same minimal clamp-state cutter, renames the native
history feature with `timeline.rename`, then configures
`suppress:Installed`.

## What success proves

SolidCraft already supports the desired human-readable native feature name.
The naming gap is therefore in Forge lowering, not in the SolidCraft
configuration backend.

## What this probe does not prove

It does not define the eventual Forge naming API. It only establishes backend
capability.

## Decision this probe informs

Forge may preserve semantic feature identity through lowering instead of
inventing a separate boolean configuration primitive merely to obtain a useful
checkbox label.
