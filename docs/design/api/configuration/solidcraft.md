# SolidCraft configuration lowering

Status: backend evidence for #444

This document records SolidCraft-specific facts. They do not define the public
Forge API.

## Direct configuration targets

SolidCraft 0.49 supports configuration targets for parameters and feature
suppression.

Forge can therefore lower:

~~~text
Parameter handle
    -> native parameter configuration column

authored feature handle
    -> native suppression configuration column
~~~

The UI labels feature-suppression columns as `Suppress: <feature name>`.

## Direct Installed result

The `configuration-installed-single-feature` probe creates two bodies and one
real native feature named `Installed` that acts on both bodies.

That feature is passed directly to `config.configure` and its suppression
value is stored in the normal configuration rows.

No `config.rule`, `drive_parameter` or `drive_suppression` is required.

The rule-free direct probe passed in CI run 971.

## Reusable component feature identity

Forge currently resolves an explicitly exported component feature to the exact
compiled history command, then binds the native feature name returned by
replay.

The public caller never supplies a SolidCraft feature id or predicts a generated
native name.

## Timeline folders are different

The `configuration-installed-group` experiment proves that SolidCraft timeline
folders can contain several contiguous history features and can be manually
suppressed as a group.

However, SolidCraft 0.49 rejects a timeline folder as
`config.configure(features=[...])` with `no feature 'Installed'`.

A folder is therefore not a configuration feature target.

Forge must not pretend those backend concepts are interchangeable.

## Configuration Rules

SolidCraft has a native Configuration Rule system, including parameter and
suppression effects.

Those capabilities may still be useful as backend capabilities in other
contexts, but the current Forge Installed/configuration API does not require
them and should not expose their command vocabulary publicly.

## Backend contract

SolidCraft lowering may use native names, ids and replay variables internally.

Public Forge authoring remains:

~~~text
semantic Parameter
semantic authored feature
final model configuration
~~~

Backend transport stays below that boundary.
