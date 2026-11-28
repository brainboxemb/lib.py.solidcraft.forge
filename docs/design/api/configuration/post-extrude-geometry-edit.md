# Suppressible later-state verification

Status: Proposed  
Tracking: #669  
Motivating consumer: brainboxemb/2026-011-02.cad.solidcraft#281

## Scope

#669 verifies exactly two reusable CAD behaviors.

### Case 1 — clamp-like sketch geometry edit

Start with a four-arc open-ring sketch for a 9.6 mm bore, extrude it, then move
the six defining sketch references to the calculated 10.0 mm Installed
positions in one `sketch.move_points` operation.

Draw the 10.0 mm target independently and compare both resulting bodies.

This proves the geometry edit, not timeline suppression of the sketch edit.

### Case 2 — one suppressible compound transform

Create one body and author one later `solid.move` feature that contains both a
translation and a rotation. Suppressing that one feature must suppress both
transform parts together.

The final configuration is one ordinary row with one direct suppression cell:

~~~text
Configuration     Suppress: InstalledPosition
Normal                         [x]
~~~

No Free/Installed row pair, Configuration Rule or drive mechanism is involved.

## API consequence

After both probes are green, Forge may implement only the public surface needed
to express these already-proven operations:

1. an explicit sketch multi-point edit surface for the clamp-like geometry case;
2. one feature-producing body transform that lowers to one native `solid.move`
   with translation and rotation together;
3. the existing `feature(...)` and `.configure(...)` contracts remain unchanged.

Do not introduce a deformation solver or a clamp-specific API.