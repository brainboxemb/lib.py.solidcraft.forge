# SolidCraft 0.50.0 canonical reference snapshot

This directory is generated from the command registry emitted by the qualified
immutable SolidCraft runtime. It is not a hand-authored Forge migration note.

- SolidCraft release: `v0.50.0`
- Upstream commit: `eeb366c2ff276987a15c043d63b9072b58274703`
- Qualified runtime release: `v0.3.8`
- Qualified runtime image: `ghcr.io/brainboxemb/cad-solidcraft:v0.3.8`
- Captured CLI version: `solidcraft-cli 0.50.0`
- Registered commands: `930`

## Canonical evidence

- `commands.json` is the exact normalized JSON registry captured from
  `solidcraft-cli commands`.
- `commands.md` is generated from `commands.json` for human review.
- `describe/*.json`, when present, are exact targeted read-only
  `engine.describe` results captured from the same immutable runtime.

Forge compatibility conclusions must be traceable to this captured registry,
the exact runtime behavior, or separately recorded upstream source evidence.
Do not replace this directory with a manually selected command subset.
