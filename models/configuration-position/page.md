This case verifies that **one saved native SolidCraft configuration table can
move an occurrence inside a complete assembly through ordinary associative
placement parameters**.

The assembly has two occurrences:

- **screen** stays fixed at the origin in every configuration;
- **front_plate** is the only occurrence that moves.

The configuration table owns two parameter columns, `plate_y` and `plate_z`,
which are also the Y/Z values of the front plate's `Placement`.

| Configuration | plate_y | plate_z | Expected physical state |
| --- | ---: | ---: | --- |
| **Front** | 8 mm | 0 mm | Front plate sits directly in front of the fixed screen. |
| **Below** | 0 mm | -55 mm | Front plate moves below the screen. |
| **Service** | 25 mm | 0 mm | Front plate moves +25 mm on Y while the screen remains fixed. |

The verification first saves the design with **Front** active. It then reopens
that saved `.sc` and activates **Below** and **Service** natively. For each
state it checks both the SolidCraft parameter values and the measured body
envelopes.

The important contract is that switching rows happens in the saved SolidCraft
document. Forge does **not** rebuild the Python assembly to create the alternate
positions.

This case does not test feature suppression, camera/render state or alternate
assembly topology; those are separate configuration/presentation concerns.
