# Free / Installed feature state

Status: correction under #669  
Tracking: #444, #506, #669

For a real later Installed CAD operation, Free/Installed is represented by
direct suppression of that authored feature.

It is not a two-row configuration axis and it does not use a Configuration
Rule or drive mechanism.

## Native table

The minimal table is:

~~~text
Configuration     Suppress: Installed
Normal                    [x]
~~~

The checkbox is the feature suppression cell itself:

~~~text
[x] -> Installed suppressed -> Free
[ ] -> Installed active     -> Installed
~~~

If a model also has Small / Medium / Large rows, those rows keep the same
suppression column. Forge does not create Free/Installed row pairs.

## Forge authoring

~~~python
with feature("installed", suppressed=True) as installed:
    body = body.<one later CAD history operation>(...)

body.configure(
    active="Normal",
    columns=(installed,),
    rows={
        "Normal": (True,),
    },
)
~~~

The boolean is direct native suppression data. No State, Toggle, ConfigRule or
drive_suppression abstraction is involved.

## HUB75 qualification boundary

Issue #669 qualifies two concrete behaviors:

1. moving the defining points of the four-arc clamp profile from its 9.6 mm
   Free geometry to an independently drawn 10.0 mm target;
2. one later rigid transform containing translation and rotation together,
   suppressible as one history feature.

The first behavior is a Sketch edit and therefore rewrites the Sketch; it does
not become a separate timeline feature in SolidCraft 0.50. The second behavior
is a real later history feature and proves compound state changes can be
suppressed together.

Forge must preserve that distinction rather than disguise an upstream Sketch
edit as a later suppressible feature.
