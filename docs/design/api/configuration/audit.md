# Configuration API audit

Status: active cleanup  
Tracking: #444

The configuration surface is being reduced to semantic CAD concepts only.

## Keep

### `model.configure(...)`

Configuration is legitimate final-model intent.

It owns:

- named rows;
- one active row;
- parameter-value targets;
- feature-suppression targets.

The model is composed first, configured second, and returned normally.

### `Parameter`

An existing `Parameter` is already an unambiguous parameter configuration
target. No `Param(...)` wrapper is needed.

### authored feature handles

A Shape that represents an already-applied history feature, a handle returned
by `feature(...)`, or a named reusable-component feature reference is already
an unambiguous suppression target. No `Suppress(...)` wrapper is needed.

### named feature authoring/reference

`feature(name, suppressed=False)` is the primary consumer authoring contract
when one real CAD history operation needs stable semantic identity or an
explicit initial suppressed state.

A reusable component automatically exposes that definition-level identity
through `occurrence.feature(name)`.

`Shape.export_feature(name)` remains the lower-level compatibility path for an
already-authored feature Shape.

## Remove

### `Configure(model, ...)`

The wrapper makes configuration appear to produce another model object.

Replace with:

~~~python
model.configure(...)
return model
~~~

### `Param(...)`

Redundant around an existing `Parameter` handle.

### `Suppress(...)`

Redundant when a feature handle is already typed by the object itself.

### broad rule authoring remains under review

The earlier audit treated all Configuration Rule authoring as unnecessary.
Issue #669 disproves that for one concrete semantic requirement: an independent
Installed checkbox must remain orthogonal to the configuration row axis while
driving suppression of one authored history feature.

SolidCraft 0.50 provides that behavior natively through a rule `enabled`
checkbox plus `drive_suppression`.

Do not restore the retired broad rule API blindly. The public Forge surface must
express the semantic independent feature-state switch without exposing native
feature ids or raw rule dictionaries. The exact spelling is decided by #669.

## Independent feature state

Issue #669 is the concrete CAD requirement that the earlier audit was missing.
A physical Installed state is independent of the row axis and therefore cannot
be represented truthfully by adding `Free` / `Installed` rows.

The required public concept is one independent switch over one semantic authored
feature. Its SolidCraft lowering may use a native Configuration Rule, but the
public API must not expose raw SolidCraft rule vocabulary merely for transport.

## Backend evidence

The direct `configuration-installed-single-feature` probe proves that
SolidCraft can configure one real feature through ordinary feature suppression
without a Configuration Rule. It is backend evidence only; a deliberately
synthetic probe cannot close a richer motivating consumer use case.

The `configuration-installed-group` experiment proves the opposite boundary:
a timeline folder may group/suppress multiple features manually, but SolidCraft
0.49 does not accept that folder as a configuration feature target.

That backend distinction must not leak into public Forge syntax.

## Target public surface

For configuration, the credible public surface is now:

~~~text
Parameter
feature(name, suppressed=...)
authored feature handle
occurrence.feature(name)
model.configure(...)
~~~

Everything else must justify itself independently.
