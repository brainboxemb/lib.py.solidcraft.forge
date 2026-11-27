# Runnable Installed clamp probe

## Why this probe exists

This probe produces a real `.sc` file that can be opened interactively in
SolidCraft. It exists so the configuration UI and saved-design behavior can be
reviewed by hand, not only through replay evidence.

## Question

Does a named `Installed` suppression feature produce a usable native
Free/Installed configuration in an ordinary saved SolidCraft design?

## Model

The probe builds a simple split ring clamp and a native feature named
`Installed`.

- `Free` suppresses `Installed`;
- `Installed` activates it.

## Important limitation

The current probe widens the bore with an extra cylindrical cutter. That is
deliberately simple visual evidence and **not** a realistic flexible-clamp
mechanism.

A production example should instead model the actual installed transition, for
example by moving/deforming split clamp arms or halves while keeping the
mechanical intent intact.

## What success proves

The generated `model.sc` can be opened and the native configuration can switch
the named history feature between Free and Installed states.

## Decision this probe informs

Keep the native suppression mechanism as the baseline for real authored state
features, while improving the mechanical example separately from the API
mechanism.
