# SolidCraft 0.43.0 reference snapshot

This directory is the immutable, version-pinned SolidCraft 0.43.0 engineering
reference used for Forge compatibility and qualification.

- SolidCraft release: `v0.43.0`
- Upstream repository: `tangency-labs/solidcraft`
- Upstream commit: `8ba46e9e2181396a9b5903b98031399aef61cf26`
- Forge runtime owner release: `docker.cad.solidcraft v0.3.3`

## Why Forge moved from 0.42.0

Forge #355 exposed upstream SolidCraft issue #15857 in the released 0.42.0
runtime: a native Slot `width` supplied as an expression was rejected with
`width must be positive`.

SolidCraft 0.43.0 contains the upstream fix. The runtime-owner repository
qualifies that release with a parameter-driven native Slot smoke before Forge
adopts it.

## Checked-in reference material

This version tree intentionally captures the contracts relevant to the 0.43.0
compatibility move:

- `commands.md` — focused native Slot command/dimension reference;
- `sketch-slot-family.md` — Forge-relevant Slot semantics and boundaries;
- `contract-gaps.md` — the remaining limitations Forge must not infer around.

The broader 0.42.0 reference tree remains unchanged. Unrelated 0.43.0 command
contracts are not copied merely because the runtime version changed.

See [../README.md](../README.md) and
[../../../development.md](../../../development.md) for the upgrade procedure.
