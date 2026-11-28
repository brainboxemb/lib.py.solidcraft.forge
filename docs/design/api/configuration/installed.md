# Free / Installed configuration

Status: correction under #669  
Tracking: #444, #506, #669

Free/Installed is a physical state switch. It is **not** a configuration-row
axis.

The configuration table keeps its ordinary row axis, for example:

~~~text
Normal
~~~

or, when the consumer already has dimensional variants:

~~~text
Small
Medium
Large
~~~

Installed remains independent from those rows.

## Authored geometry

The base model is the physical Free geometry.

One later real CAD history feature represents the Installed adjustment:

~~~python
with feature("installed", suppressed=True):
    body = body.<generic_post_extrude_edit>(...)
~~~

That history feature is suppressed in the normal/base row.

## Installed control

The native SolidCraft presentation is one independent Configuration Rule
checkbox named `Installed`.

Conceptually:

~~~text
row: Normal
    Installed feature suppressed = true

rule: Installed
    enabled = false
    always
    drive suppression(Installed) = false
~~~

Therefore:

~~~text
Installed [ ]  -> base row wins -> feature suppressed -> Free
Installed [x]  -> rule wins     -> feature active     -> Installed
~~~

The checkbox remains orthogonal to row selection. If the table has
Small/Medium/Large rows, Installed does not create six Cartesian rows.

## Forge contract

The earlier two-row form is incorrect:

~~~text
Free
Installed
~~~

Do not represent this state by switching rows.

Forge needs a semantic independent feature-state control that targets the
authored feature handle and lowers to SolidCraft's native rule checkbox without
exposing native feature ids.

The exact public spelling is being resolved in #669.

## Backend evidence

The earlier parameter-driven Installed rule proved the native checkbox behavior,
but changed `clamp_bore` and was not a correct flexible-clamp model.

The #669 feature-rule probe instead targets a real authored post-Extrude feature
with native `drive_suppression`. That is the required configuration mechanism.

The geometry operation itself remains a separate #669 question: the positive
`offset_face` probe proves history/suppression mechanics only and is not the
final HUB75 clamp operation.
