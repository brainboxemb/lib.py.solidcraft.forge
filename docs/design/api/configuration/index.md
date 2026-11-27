# Configuration API design

Status: v0.25 consumer-acceptance repair in progress  
Tracking: #444, #506, #584

Forge configuration belongs to the **final model**.

The public operation is deliberately small:

~~~python
model.configure(
    active="Small",
    columns=(...),
    rows={...},
)
~~~

There is no public configuration wrapper object.

## Configuration target types

A configuration column is an existing semantic handle:

- a root/parent `Parameter` means a parameter-value column;
- an authored Shape/feature handle means native feature suppression.

Do not turn a parameter-driven consumer state into a synthetic suppression
feature, and do not replace a real history toggle with a fake boolean parameter.

### Parameter values

A parameter configuration column selects concrete values for an existing
root/parent `Parameter`:

~~~python
model.configure(
    active="Medium",
    columns=(self.width,),
    rows={
        "Small": ("60 mm",),
        "Medium": ("80 mm",),
        "Large": ("100 mm",),
    },
)
~~~

Configuration rows do **not** author a second parameter-dependency graph.
Relationships between parameters belong in normal Forge model expressions.
Therefore cells such as `"width/2"`, `"tube_d"` or
`"tube_d-clamp_interference"` are not supported configuration values.

The split-ring Free/Installed experiments used this kind of parameter coupling
while exploring SolidCraft configuration behavior. That probe is not a public
consumer contract and must not be copied into product models.

### Named history feature

When the consumer really owns one history operation that rows must suppress,
name that operation directly:

~~~python
with feature("panel_pin", suppressed=True):
    body = body - Hole(d=5).at(0, 0, self.HEIGHT)

return body
~~~

For a reusable component, the scope name becomes component-definition identity.
The final model refers to it with:

~~~python
coupler.feature("panel_pin")
~~~

and configures it normally:

~~~python
model.configure(
    active="Medium",
    columns=(
        self.coupler_width,
        right.feature("panel_pin"),
    ),
    rows={
        "Small": ("30 mm", True),
        "Medium": ("40 mm", True),
        "Large": ("40 mm", False),
    },
)
~~~

The boolean cells are suppression values: `True` suppresses the feature and
`False` enables it.

## `feature(...)` scope contract

`feature(name, suppressed=False)` gives exactly **one authored CAD history
operation** stable Forge identity.

Rules:

- helper Sketch/profile construction belongs outside the scope;
- the scope must finish with exactly one terminal Shape;
- that result must represent exactly one CAD history operation;
- scopes do not nest;
- `suppressed=True` sets the initial native history state;
- `suppressed=False` leaves the newly authored feature active;
- a reusable component automatically exposes the scoped name through
  `occurrence.feature(name)`;
- the name is Forge identity, not a SolidCraft history id or browser label.

For a direct final Shape, the context handle may itself be used as the
configuration column:

~~~python
with feature("panel_pin_pass_through") as pass_through:
    model = panel - profile.revolve(axis=axis)

model.configure(
    active="Cut",
    columns=(pass_through,),
    rows={
        "Cut": (False,),
        "Suppressed": (True,),
    },
)
~~~

`Shape.export_feature(name)` remains the lower-level compatibility path for an
already-authored feature Shape. New consumer code that needs a named initial
history state should prefer the scoped `feature(...)` contract.

## Final-model ownership

Configuration is attached only after the model has been composed. A reusable
component owns its geometry, parameters and named history features; it does not
own application/document row selection.

This keeps reusable geometry separate from final-model presentation and state.

## Removed configuration vocabulary

The v0.25 API does not expose:

~~~text
Configure(...)
Param(...)
Suppress(...)
ConfigRule(...)
Always()
DriveParameter(...)
State(...)
Toggle(...)
Bind(...)
~~~

Backend-native mechanisms may still exist internally, but they are not public
Forge authoring vocabulary.

## Evidence boundary

Backend probes and consumer probes are different evidence.

A small probe may intentionally use synthetic geometry to isolate native
suppression, replay binding or saved-row behavior. That probe proves only that
mechanism. The motivating public API is not accepted until a consumer-faithful
case proves the actual semantic use.

For #506:

- `configuration-installed-feature` remains focused backend evidence;
- `configuration-child-feature` proves reusable child feature identity;
- `shifted-axis-revolve` proves one real stepped panel-pin-style history cut;
- the split-ring parameter-coupling experiment is historical/backend evidence,
  not supported consumer authoring;
- the current HUB75 tube-clamp source must be migrated away from that probe
  pattern rather than used to justify it.

## Compiler boundary

The normal `dev` API remains semantic and backend-neutral. Experimental typed
IR evolution stays on `exp`; SolidCraft command vocabulary does not become
public Forge API merely because the normal backend uses it internally.
