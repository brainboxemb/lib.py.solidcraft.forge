# Installed single-row suppression probe

## Why this probe exists

The desired Installed control is direct feature suppression.

There must be no Free/Installed row pair and no Configuration Rule.

## Model

~~~text
FreeProfile
-> ClampExtrude
-> Installed        offset_face diagnostic
~~~

The configuration contains exactly one row and one feature suppression column:

~~~text
Configuration     Suppress: Installed
Normal                    [x]
~~~

The checkbox is the stored suppression value for the actual Installed history
feature.

## Expected meaning

~~~text
checked     -> feature suppressed -> Free
unchecked   -> feature active     -> Installed
~~~

SolidCraft's native configuration UI renders suppression cells as checkboxes.
No rule or drive effect is required.

## What success proves

A green probe proves:

- the design contains one real later Installed history feature;
- one normal row can target that feature directly;
- the saved table contains exactly one suppression cell for Installed;
- no config.rule or drive_suppression command is needed.

The diagnostic Offset Face is not the final HUB75 geometry operation.