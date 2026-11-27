# Free / Installed configuration

Status: consumer contract correction under #506  
Tracking: #444, #506, #584

`Free` and `Installed` are useful physical-state row names, but they do not
imply one particular implementation mechanism.

Choose the configuration target from the model's real CAD intent.

## Parameter rows

Configuration tables may set an existing parameter to concrete row values.
They do not define relationships between parameters.

The earlier split-ring probe used:

~~~python
rows={
    "Free": ("tube_d-clamp_interference",),
    "Installed": ("tube_d",),
}
~~~

That is configuration-time parameter coupling and is no longer supported
public Forge authoring. It was backend/API exploration, not a HUB75 consumer
contract.

Normal parameter relationships still belong in the model itself, where Forge
retains typed `Parameter` / `Expression` dependencies. Configuration rows may
then select concrete values such as `"9.6 mm"` or `"10 mm"` when that is the
actual consumer intent.

## Feature state

Use feature suppression only when the model genuinely has one history operation
whose presence changes by configuration.

Author that operation with stable semantic identity:

~~~python
with feature("installed", suppressed=True):
    body = body - installed_cut
~~~

A reusable occurrence then exposes the same definition-level identity:

~~~python
clamp.feature("installed")
~~~

and the final model may use it directly:

~~~python
model.configure(
    active="Free",
    columns=(clamp.feature("installed"),),
    rows={
        "Free": (True,),
        "Installed": (False,),
    },
)
~~~

The boolean is native suppression data:

~~~text
True   -> feature suppressed
False  -> feature active
~~~

No public Configuration Rule or synthetic boolean State object is required.

## Consumer proof versus backend proof

The synthetic `configuration-installed-feature` probe deliberately uses a
simple extra cut. It proves native identity, initial suppression and saved-row
switching only.

It is not a mechanical model of a flexible clamp and must not be cited as one.

The consumer-level named-feature proof is the real stepped shifted-axis
panel-pin pass-through used by the HUB75 frame-coupler family: one revolve
history feature, Small/Medium suppressed, Large enabled.

The current standalone HUB75 tube-clamp source still contains the old split-ring
coupling pattern and must be corrected downstream. It is not evidence that the
pattern belongs in the Forge API.
