# Current Installed rule baseline

## Why this probe exists

This records the released Forge/SolidCraft baseline for a standalone
Free/Installed control before deciding whether Installed should instead be a
real suppressible CAD feature.

## Question

Can the current public configuration-rule API present a global `Installed`
checkbox and drive a clamp parameter without introducing new public API?

## Model

The clamp has a configurable `clamp_bore` parameter.

- the `Free` row stores `tube_d - 0.4 mm`;
- one disabled-by-default rule named `Installed` drives `clamp_bore` to
  `tube_d` when enabled.

## What success proves

The current Forge API can create a native SolidCraft Configuration Rule with an
independent enabled checkbox that drives a configured parameter.

## What this probe does not prove

It does not prove that a rule is the right semantic model for Installed. The
rule's enabled state is a global rule switch, not a row-owned boolean cell and
not a named CAD history feature.

The clamp bore change is intentionally minimal API-test geometry, not a
realistic flexible-clamp mechanism.

## Decision this probe informs

Compare this baseline with the feature-suppression probes. Prefer the smaller
semantic model when Installed is truthfully an authored CAD feature/state.
