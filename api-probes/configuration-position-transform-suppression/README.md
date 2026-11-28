# Combined move + rotate suppression verification probe

## Consumer case

One later positional state may contain more than one transform at once.

The probe creates one body and authors exactly one native `solid.move` history
feature named `InstalledPosition` containing both:

- translation: +30, +20, +5 mm;
- rotation: 30 deg around world Z at the origin.

That one history feature is then suppressed and enabled again.

## Configuration

The final table has one row and one direct suppression checkbox:

~~~text
Configuration     Suppress: InstalledPosition
Normal                         [x]
~~~

There is no second row and no rule/drive layer.

## What this proves

- translation and rotation can be one authored CAD history feature;
- suppressing that one feature removes both transforms together;
- enabling it restores both transforms together;
- the same feature can be used directly as the one-row configuration
  suppression target.

This is the positional analogue of the clamp's later Installed step.