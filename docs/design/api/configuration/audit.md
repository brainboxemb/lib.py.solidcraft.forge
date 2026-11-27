# Configuration API audit

Status: working design audit  
Tracking: #444

This audit reviews the current public Forge configuration API against the
intended generic CAD authoring model.

Existing release history is not sufficient reason to keep an API object. A
public object should remain only when it represents useful Forge/CAD semantics
rather than one SolidCraft implementation mechanism.

## Audit rule

Keep a public concept only when its meaning can be stated without referring to:

- a SolidCraft command name;
- a SolidCraft rule/effect shape;
- a native feature id;
- a replay variable;
- a backend-private driver parameter.

Backends may still use all of those internally.

## `Configure(...)`

**Semantic concept: keep.  
Current wrapper form: replace/review.**

A final model legitimately owns:

- named configuration rows;
- one active row;
- configurable parameter/feature targets;
- final-model configuration intent such as global Installed behavior.

The released form:

~~~python
Configure(model, ...)
~~~

makes configuration look like a model-producing wrapper.

The intended flow is clearer:

~~~python
model = ...
model.configure(...)
return model
~~~

Existing wrapper compatibility may remain temporarily while the new API is
developed, but the wrapper shape is not the target contract.

## `Param(parameter)`

**Parameter-target semantics: keep.  
Wrapper: review for removal.**

A model Parameter is a legitimate configuration target.

If the Parameter handle itself is already unambiguous:

~~~python
model.configure(
    columns=(self.width,),
    ...
)
~~~

then:

~~~python
Param(self.width)
~~~

may be redundant public ceremony.

Do not retain `Param` merely because SolidCraft calls a native column
`param:<name>`.

## `Suppress(feature)`

**Feature-suppression semantics: keep.  
Exact wrapper spelling: review.**

Feature suppression is normal parametric-CAD history behavior.

Forge needs stable authored feature identity so configuration can refer to a
real history transition without exposing backend ids.

The exact `Suppress(...)` helper may change if the eventual
`model.configure(...)` API can express the target more directly.

## Authored feature identity

**Keep and strengthen.**

The current component feature export path proves that a parent can refer to a
deliberately exported child-owned feature.

The desired component authoring is now closer to:

~~~python
with feature(
    "Installed",
    suppressed=not self._installed,
):
    model = installed_motion(model)
~~~

The exact syntax remains open, but these semantics are required:

- stable Forge-authored feature identity;
- explicit name;
- initial suppression;
- feature remains present in history;
- reusable component may expose the identity to the final model.

The `configuration-installed-group` probe additionally shows that a semantic
feature/group abstraction must not be assumed to map one-to-one to a SolidCraft
configuration feature target: SolidCraft timeline folders can group several
features but cannot themselves be configured.

## `ConfigRule(...)`

**Remove from the intended public API.**

This object is a typed wrapper around SolidCraft Configuration Rules.

Its original practical reason was the independent Installed checkbox. That
requirement remains valid, but the user should author Installed behavior, not a
SolidCraft-shaped rule object.

The backend may still lower global Installed intent through a native rule when
that is the available SolidCraft mechanism.

## `Always()`

**Remove with the public rule surface.**

There is no current independent Forge/CAD authoring requirement for an
`Always` condition object. It exists to construct the SolidCraft-shaped rule.

If Forge later needs a genuine generic rule/constraint language, design it from
those semantic requirements rather than retaining this helper.

## `DriveParameter(...)`

**Remove with the public rule surface.**

The working SolidCraft fan-out probe uses a native rule plus a private shared
driver parameter. That proves a backend transport pattern; it does not prove
that users should author `DriveParameter`.

A backend-created driver remains backend-private.

## `Configure(..., rules=...)`

**Remove from the intended public contract.**

This exposes native rule mechanics through the public configuration object.
Final-model Installed behavior should be described in Forge terms and lowered
to whatever mechanism each backend supports.

## `Shape.export_feature(name)` / `occurrence.feature(name)`

**Generic requirement: keep.  
Current naming/spelling: review.**

Reusable components need a deliberate way to expose authored feature identity
to a parent/final model.

Open details include:

- whether `with feature(...)` automatically creates/exportable identity;
- whether export remains explicit;
- how component-local names map to final-model references;
- how default suppression is represented.

## Current API conclusion

The smallest credible target surface is currently:

~~~text
normal model Parameters
authored named suppressible features
final model.configure(...)
stable feature references/exports
~~~

The following should not be used as foundations for new API work:

~~~text
ConfigRule
Always
DriveParameter
public rules=
first-class State/Toggle invented only for this use case
~~~

The global Installed requirement is real, but its final public spelling is
still open.

## Relationship to `exp`

The experimental lane owns typed engine-neutral IR development.

This audit supplies requirements to that work:

- parameter intent must remain semantic;
- feature identity must remain semantic;
- suppression/configuration intent must not contain native ids;
- SolidCraft-only rules/drivers must remain lowering details.

It does not prescribe a new IR node from `dev`.

## Immediate next work

Use the concrete HUB75-style example to settle only the missing public
authoring pieces:

1. scoped/named feature authoring with initial suppression;
2. reusable feature identity/export;
3. final `model.configure(...)` syntax;
4. one global Installed control affecting all participating Installed behavior;
5. removal/replacement of the released rule-shaped public surface.

Do not add another abstraction until the concrete example demonstrates why it
is necessary.
