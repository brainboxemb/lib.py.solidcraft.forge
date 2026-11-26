This case verifies that configuration rows can drive **derived native CAD
expressions**, not only direct dimensions.

The model has one configured source parameter, `size`. Its box dimensions are
derived from ordinary Forge symbolic values:

- length: `sqrt(min(size, limit)^2 - offset^2)`;
- width: `round(size / grid) * grid`;
- height: `floor(size / pitch) * step + max(wall, abs(bias))`.

The active **Medium** row uses `size = 70 mm`. The saved SolidCraft design is
then reopened and switched to **Small** and **Large**. The body envelopes must
change to the dimensions recomputed by SolidCraft from those expressions.

Forge never calls `pv()` for these relationships and never substitutes the
current Python result into the feature command. The native feature inputs retain
the source parameter names, so configuration changes remain geometry-driving.
