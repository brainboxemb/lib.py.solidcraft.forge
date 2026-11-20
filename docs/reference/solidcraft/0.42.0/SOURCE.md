# SolidCraft 0.42.0 reference snapshot

This directory is the immutable, version-pinned SolidCraft 0.42.0 engineering
reference used for Forge compatibility and qualification.

- SolidCraft release: `v0.42.0`
- Upstream repository: `tangency-labs/solidcraft`
- Upstream commit: `1b1e940cc48e4d1d5d01971a4be20e2e55647066`

## Checked-in reference material

This qualified version tree contains:

- `commands.md` — the human-readable SolidCraft command catalog snapshot;
- `contract-gaps.md` — known typed-contract gaps relevant to Forge;
- `joint-occurrence-references.md` — qualified joint/occurrence reference behavior;
- `occurrence-identity.md` — qualified occurrence identity behavior;
- `rectangular-feature-patterns.md` — version-specific rectangular-pattern notes;
- `sketch-slot-family.md` — version-specific native slot notes.

An earlier qualification implementation also generated machine-readable
`runtime/manifest.json`, `runtime/commands.json` and
`runtime/contracts/<command-id>.json` snapshots. Those generated files and the
snapshot generator were removed during the later CI/runtime cleanup and are not
part of the current repository tree. Do not rely on the stale historical path.
The retained files above are the current checked-in 0.42.0 reference evidence.

## Upgrade rule

Keep all 0.42.0 evidence unchanged once qualified. When Forge targets a later
SolidCraft release, add a new sibling version directory first, record its exact
upstream provenance and capture the new version-specific reference material
before compatibility work begins.

See [../README.md](../README.md) and
[../../../development.md](../../../development.md) for the current procedure.
