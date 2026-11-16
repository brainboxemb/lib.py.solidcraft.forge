# Change 0016 — Diagnose actual native parameter dependencies

Status: implementation  
SolidCraft target: **0.42.0**

## Problem

Forge currently checks whether a declared model parameter appears in a
`parameters.add` command when deciding whether the parameter stayed native.

That is not enough. `parameters.add` only publishes a parameter. It does not
prove that any SolidCraft geometry, placement or relationship still depends on
that parameter.

Forge also needs to distinguish an intentional Python-side value read through
`pv()` from its own internal numeric validation and native topology pick
coordinates.

Finally, root `@assembly` classes do not currently run the same model
parameter warning as root model classes.

## Rule

A declared model parameter counts as native only when an emitted native
expression actually depends on it.

Forge reports a `ModelParameterWarning` when:

- a public model parameter has no emitted native dependency; or
- the parameter has a native dependency but user model code also consumes its
  current value through `pv()`, making the model only partly associative.

A `parameters.add` command by itself is not dependency evidence.

## Typed expression dependencies

The internal native expression value introduced by change 0015 also records
the parameter names used by that expression.

For example:

```text
NativeExpression("width / 2", parameters=("width",))
```

Component namespacing renames both the expression text and its dependency
names. External/shared parameter names remain unchanged.

The final replay JSON still contains ordinary strings only.

## `pv()` classification

Public `pv()` is an explicit escape from a symbolic CAD value to its current
Python number. While Forge executes user `build()` code it records which of
that model's own Parameter objects were read through public `pv()`.

Forge's internal validation uses a separate non-recording numeric helper.
Internal checks, initial topology pick coordinates and compiler bookkeeping
therefore do not pretend that user code called `pv()`.

Nested component builds only count as a parent dependency loss when they read
the actual parent Parameter object passed into them.

## Root assemblies

A root `@assembly` is built through the same root-design path as a normal
model class. Its declared parameters and explicit `pv()` reads are retained
until after assembly compilation, so the same warning rules apply.

Imported/nested `@assembly` behaviour is unchanged.

## Non-goals

- no change to the public Parameter/Expression arithmetic API;
- no new replay metadata;
- no change to SolidCraft expression syntax;
- no warning merely because Forge uses a numeric authoring pick internally;
- no transform/attachment changes from remediation Phase 7.

## Qualification

This change must prove:

- a parameter used by native geometry has an emitted dependency and does not
  warn;
- a published parameter with no emitted dependency still warns;
- a parameter used natively and also read through public `pv()` warns that
  only part of the model remains native;
- Forge internal numeric validation does not create a false `pv()` warning;
- root model and root `@assembly` use the same dependency-loss warning;
- component namespacing keeps dependency names aligned with expression names;
- final replay JSON remains unchanged apart from intended model commands.

## Exit condition

> Parameter warnings are based on actual typed native dependencies and explicit
> user `pv()` reads, not on arbitrary strings or parameter publication.
