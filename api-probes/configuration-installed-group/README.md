# Installed timeline-group configuration probe

## Why this probe exists

The desired model has one global Installed control. Every authored operation
that belongs to the Installed transition should follow that one control.

A reusable component may therefore contribute its own Installed feature, while
the final design should still expose only one Installed control.

This probe checks whether SolidCraft 0.49 can use one timeline feature folder as
that native fan-out target.

## Exact questions

1. Can one SolidCraft timeline folder named `Installed` contain several
   independently authored history features and suppress/unsuppress them
   together?
2. Can that same folder be targeted by one native Configuration Rule
   `drive_suppression` effect, giving the configuration one Installed
   checkbox for the entire folder?

## Model

The probe creates two bodies and two independent history moves:

~~~text
LeftInstalled
RightInstalled
~~~

Both moves are placed in one timeline folder:

~~~text
Installed
├── LeftInstalled
└── RightInstalled
~~~

`commands.json` is the permanent positive baseline. It suppresses the folder
through `timeline.suppress(groups=[...])` and inspects the folder.

`group-config-attempt.json` is the focused backend experiment. It additionally
tries to use the folder id as the target of one Configuration Rule
`drive_suppression` effect.

## What success of the baseline proves

It proves SolidCraft can treat a timeline folder as one manual suppression
boundary for several history features.

## What the configuration attempt proves

If accepted, SolidCraft can directly expose one Installed Configuration Rule
whose suppression effect controls the whole timeline folder.

If rejected, SolidCraft distinguishes a timeline folder id from a feature id
for Configuration Rule effects. In that case one global configuration checkbox
cannot directly suppress several independent features through a folder in the
0.49 native rule contract.

## What this probe does not prove

A positive folder result does not by itself define Forge public API. The Forge
authoring model may still use a scoped/named feature abstraction and lower it
differently per backend.

The probe does not touch the experimental IR.

## Decision informed

This decides whether the concrete HUB75-style design can lower a single global
Installed control directly to one SolidCraft group suppression target, or
whether SolidCraft needs a different backend mechanism.
