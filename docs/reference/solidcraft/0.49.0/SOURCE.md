# SolidCraft 0.49.0 canonical reference snapshot

This directory is generated from the command registry emitted by the qualified
immutable SolidCraft runtime. It is not a hand-authored Forge migration note.

- SolidCraft release: `v0.49.0`
- Upstream commit: `10e6242c3a94e942c8fc11e78965ef1cd21e4856`
- Qualified runtime release: `v0.3.6`
- Qualified runtime image: `ghcr.io/brainboxemb/cad-solidcraft:v0.3.6`
- Captured CLI version: `solidcraft-cli 0.49.0`
- Registered commands: `886`

## Canonical evidence

- `commands.json` is the exact normalized JSON registry captured from
  `solidcraft-cli commands`.
- `commands.md` is generated from `commands.json` for human review.
- `describe/*.json`, when present, are exact targeted read-only
  `engine.describe` results captured from the same immutable runtime.

Forge compatibility conclusions must be traceable to this captured registry,
the exact runtime behavior, or separately recorded upstream source evidence.
Do not replace this directory with a manually selected command subset.
