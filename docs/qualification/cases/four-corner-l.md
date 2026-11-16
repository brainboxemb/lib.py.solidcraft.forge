# Four centred vertical L-profiles

## Use scenario

One neutral vertical L-profile is reused on the four rounded side corners of a
rectangular frame. The assembly calculates the four poses from
`frame_width`, `frame_depth` and `frame_height`.

## Forge API

Each profile is a normal occurrence with `Placement`:

```python
profile.copy(
    placement=Placement(
        x=...,
        y=...,
        z=...,
        rotation=(Z, ...),
    ),
)
```

There is no `attach()` and no joint between the frame and the profiles.

## Expected behaviour

At 120 × 80 × 60 mm the four profiles are centred vertically at Z=22..38 and
wrap the four side corners. After changing the saved frame width/depth to
160 × 120 mm, all four positions must follow the changed parameters without
rerunning Python.

## Current backend status

This case is currently `BLOCKED` by ordinary Placement support from change
0009. SolidCraft 0.42 `component.create` cannot give the first occurrence its
non-identity pose, while `occurrence.copy` only accepts numeric translation
and has no rotation input.

That is a Placement backend limitation. It is not an attachment-reference
problem from change 0010.
