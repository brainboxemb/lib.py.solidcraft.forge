# SolidCraft 0.42 typed-contract gaps

The runtime snapshot is generated from `engine.describe`. SolidCraft 0.42
returns `input: null` and `output: null` for these Forge-used commands:

- `solid.hole`
- `solid.loft`
- `solid.pattern.rectangular`
- `solid.shell`

This is a limitation of the 0.42 command registry, not missing Forge snapshot
generation. Each corresponding file under `runtime/contracts/` still stores
the exact parameter documentation returned by the runtime.

Forge currently does not bind or consume result fields from these four commands.
Their emitted input fields are covered by Forge command-contract tests and
native qualification. If future Forge code needs a field or result that the
runtime description does not specify, that dependency must be recorded and
qualified explicitly; do not infer it from a different SolidCraft version.

A future SolidCraft snapshot should keep this file only for commands whose
runtime `engine.describe` still has an actual gap.
