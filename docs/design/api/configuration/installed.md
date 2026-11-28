# Free / Installed feature state

Status: correction under #669  
Tracking: #444, #506, #669

Free/Installed is represented by direct suppression of one authored Installed
history feature.

It is not a two-row configuration and it is not a Configuration Rule.

## Native table

The minimal table is:

~~~text
Configuration     Suppress: Installed
Normal                    [x]
~~~

The checkbox is the feature suppression cell itself.

~~~text
[x] -> Installed suppressed -> Free
[ ] -> Installed active     -> Installed
~~~

No rule, condition, effect or drive operation sits between the checkbox and the
feature.

## Forge authoring

~~~python
with feature("installed", suppressed=True) as installed:
    body = body.<generic_post_extrude_edit>(...)

body.configure(
    active="Normal",
    columns=(installed,),
    rows={
        "Normal": (True,),
    },
)
~~~

If the model later has Small / Medium / Large rows, each row can hold the same
normal suppression column. Installed remains the same authored feature; Forge
does not create Free/Installed row pairs.

## Geometry boundary

The configuration mechanism is already sufficient.

Issue #669 only still needs to identify the generic post-Extrude solid-edit
operation that correctly changes the HUB75 clamp geometry while preserving its
physical intent.