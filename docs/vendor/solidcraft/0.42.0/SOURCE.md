# SolidCraft 0.42.0 reference snapshot

This directory is a local, version-pinned reference for Forge qualification.

- SolidCraft release: `v0.42.0`
- Upstream repository: `tangency-labs/solidcraft`
- Upstream commit: `1b1e940cc48e4d1d5d01971a4be20e2e55647066`

## Runtime command snapshot

The authoritative Forge-used command snapshot is:

```text
runtime/manifest.json
runtime/commands.json
runtime/contracts/<command-id>.json
```

It is generated from the checksum-verified official SolidCraft 0.42.0 CLI:

```text
solidcraft-cli commands
solidcraft-cli exec engine.describe '{"command":"<id>"}'
```

The MCP tools `list_commands` and `describe_command` expose the same command
registry and command descriptions. The checked-in runtime snapshot therefore
stores the machine-readable API surface Forge compiles against rather than
reconstructing it from SolidCraft implementation source.

At the time of this snapshot Forge references 39 SolidCraft commands. SolidCraft
0.42 reports typed input/output schemas for 35 of them. Four commands expose
parameter prose but still return null typed schemas:

```text
solid.hole
solid.loft
solid.pattern.rectangular
solid.shell
```

Those gaps are retained explicitly in `runtime/manifest.json`.

## Human-readable catalog

The older `commands.md` snapshot comes from SolidCraft's generated
`docs/features.md` command catalog. It remains useful for browsing commands
outside the Forge-used subset.

Keep all 0.42.0 evidence unchanged once qualified. When Forge targets a later
SolidCraft release, add a sibling version directory and generate its runtime
snapshot before compatibility work begins.
