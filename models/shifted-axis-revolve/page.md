This case verifies that a shifted revolve is still **one native SolidCraft
history feature**, so configuration suppression can target the complete cut.

The panel-pin pass-through is intentionally stepped:

- rear relief: Ø4.5 mm;
- core: Ø3.7 mm;
- front relief: Ø4.5 mm.

The profile is authored on an XY Sketch whose Z offset is the symbolic
`axis_z` parameter. The revolve uses:

```python
AxisLine(Axis.Y, origin=(self.axis_x, 0, self.axis_z))
```

Both the Sketch plane and revolve axis therefore follow the same native
parameter at Z, while the profile and axis X position follow `axis_x`.

The active **Cut** configuration keeps the revolve feature enabled. The saved
`.sc` is reopened and switched to **Suppressed**; SolidCraft suppresses the
single revolve feature and the body volume increases. Switching does not branch
Python and does not leave separate relief cylinders behind.
