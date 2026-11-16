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

## Replay lowering

The first profile occurrence is bound from `component.create`; each later
copy is bound from `occurrence.copy`. Parameter-driven XYZ position and the
three rotated copies are then addressed through those replay variables.

The replay file therefore remains deterministic and contains no guessed
`LProfile:N` names. Saved-design frame parameter changes continue to drive
the occurrence moves.
