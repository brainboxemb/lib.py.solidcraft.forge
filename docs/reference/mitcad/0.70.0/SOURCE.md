# Mitcad 0.70.0 reference snapshot

This directory pins the exact upstream command reference used by the first
Forge multi-backend feasibility work.

- Mitcad release: `v0.70.0`
- Upstream commit: `806a4210126ab977ba678708dd476496ddbd2968`
- Upstream command-reference blob: `40240776bc6885e228bf2fbd8e2534875aa61b85`
- Runtime catalog: not captured in this source-only snapshot

## Evidence

- `commands.md` is byte-for-byte the upstream
  `core/model-api/src/commands.md` Git blob from `v0.70.0`.
- It is the source included by Mitcad MCP as the basis of
  `mitcad://reference/commands`; the server filters only entries its
  vocabulary does not permit.
- `modules/mitcad-reference` can additionally capture the live
  `model_reference` catalog into `commands.json` and require the live
  command-resource text to retain this exact Git-blob identity.

This initial snapshot intentionally does not invent a machine catalog when a
v0.70.0 `mitcad-cli` binary is not available in Forge CI. Add
`commands.json` only by running the capture command against that exact CLI.
