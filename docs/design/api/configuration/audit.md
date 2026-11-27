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

### `ConfigRule(...)`, `Always()`, `DriveParameter(...)`, `rules=`

These expose one SolidCraft mechanism rather than generic Forge CAD intent.

The old `configuration-installed-state` qualification model depended on this
surface and is removed rather than preserved as compatibility-driven design.

## Do not introduce

The current use case does not justify separate public:

~~~text
State
Toggle
Bind
FeatureGroup
~~~

Do not add another abstraction until a concrete CAD model demonstrates a
semantic requirement that direct parameters, feature identity and
`model.configure(...)` cannot express.

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
