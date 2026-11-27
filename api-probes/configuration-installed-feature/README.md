# Installed named-feature backend probe

## Why this probe exists

This is a focused backend/API-mechanism probe. It proves that one feature
authored with the public `feature(...)` scope can be initially suppressed,
exported through a reusable component definition and targeted by the final
model through `clamp.feature("installed")`.

It is **not** the consumer acceptance case for flexible-clamp mechanics.

## Model

The fixture intentionally uses a second cylindrical cut so the two native
states are easy to inspect:

- `Free` keeps the named `installed` cut suppressed;
- `Installed` activates that exact cut.

The simplified geometry isolates feature identity, initial suppression and
saved configuration switching. It does not claim that widening a bore is a
generic model of elastic deformation.

## What success proves

- `with feature("installed", suppressed=True): ...` identifies exactly one
  authored CAD history feature;
- initial suppression uses that exact native feature;
- a reusable definition exposes the same semantic identity through
  `occurrence.feature("installed")`;
- `model.configure(...)` stores normal row-owned suppression values;
- saved-design switching does not rerun Forge Python.

## Consumer evidence boundary

Consumer-level acceptance uses real model intent separately:

- HUB75 tube-clamp Free/Installed is parameter-driven through `clamp_bore`;
- HUB75 Edge/Right-Corner panel-pin pass-through is one real shifted-axis
  revolve whose Small/Medium/Large rows suppress or enable that feature.

A synthetic backend probe must never be cited as proof of richer consumer
semantics it does not contain.
