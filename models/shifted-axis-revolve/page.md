This case verifies that a shifted revolve is still **one native SolidCraft
history feature**, and that Forge can give that feature stable semantic identity
without exposing a SolidCraft timeline name.

The panel-pin pass-through is intentionally stepped:

- rear relief: Ø4.5 mm;
- core: Ø3.7 mm;
- front relief: Ø4.5 mm.

The profile is authored first on an XY Sketch whose Z offset is the symbolic
`axis_z` parameter. Only the actual cut operation is inside the named feature
scope:

```python
with feature("panel_pin_pass_through") as pass_through:
    model = panel - profile.revolve(
        axis=AxisLine(
            Axis.Y,
            origin=(self.axis_x, 0, self.axis_z),
        ),
    )
```

The scope owns exactly one CAD history operation. Sketch/profile construction is
ordinary model code and is not hidden inside the feature identity.

The active **Cut** configuration keeps the feature enabled. The saved `.sc` is
reopened and switched to **Suppressed**; SolidCraft suppresses the same single
revolve feature and the body volume increases. Switching does not branch Python
and does not leave separate relief cylinders behind.
