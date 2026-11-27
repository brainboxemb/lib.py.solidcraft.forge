# Free / Installed configuration

Status: consumer contract correction under #506  
Tracking: #444, #506

`Free` and `Installed` are useful physical-state row names, but they do not
imply one particular implementation mechanism.

Choose the configuration target from the model's real CAD intent.

## Parameter state

The retained HUB75 tube clamp is parameter-driven:

~~~text
Free       clamp_bore = tube_d - clamp_interference
Installed  clamp_bore = tube_d
~~~

The public authoring remains an ordinary Parameter column:

~~~python
clamp.configure(
    active="Free",
    columns=(self.clamp_bore,),
    rows={
        "Free": ("tube_d-clamp_interference",),
        "Installed": ("tube_d",),
    },
)
~~~

This is not a reason to add a Forge flex/deformation API. The consumer owns its
parametric geometry.

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

The standalone HUB75 tube clamp remains the separate parameter-driven consumer
described above.
